import json
from dataclasses import replace
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient as BaseTestClient

def TestClient(*args, **kwargs):
    return BaseTestClient(*args, base_url="http://127.0.0.1", **kwargs)
from among_agents.app import create_app
from among_agents.config import ROOT, Settings
from among_agents.crew import demo_decision, ensure_budget
from among_agents.integrations import IntegrationError, discord_action, mcp_payload, parse_tick, writable_connection
from among_agents.models import AgentSummary, Decision, Tick


@pytest.fixture
def settings(tmp_path):
    return Settings(database=tmp_path / "runs.sqlite3")


@pytest.fixture
def outbreak():
    return Tick.model_validate(json.loads((ROOT / "fixtures/outbreak-level-5.json").read_text())["ticks"][0])


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    # These tests must never consume credits, advance the real feed, or send Discord messages.
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access is forbidden in worker tests")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


def test_demo_covers_all_sectors_and_control(settings):
    with TestClient(create_app(settings)) as client:
        outbreak = client.post("/run", json={"fixture": "outbreak"})
        assert outbreak.status_code == 200
        data = outbreak.json()
        assert data["mode"] == "demo"
        assert data["decision"]["action"] == "evacuate"
        assert len(data["tick"]["sector_reports"]) == 2
        assert len(data["decision"]["evidence"]) == 2
        assert client.get(f"/runs/{data['id']}").json()["id"] == data["id"]
        control = client.post("/run", json={"fixture": "control"}).json()
        assert control["decision"]["action"] == "observe"
        assert control["dispatch"]["status"] == "not_required"
        dispatched = client.post(f"/runs/{control['id']}/dispatch").json()
        assert dispatched["dispatch"]["status"] == "not_required"


def test_budget_refuses_zero_agents_or_credits(outbreak):
    with pytest.raises(IntegrationError):
        ensure_budget(outbreak.model_copy(update={"swarm_budget": outbreak.swarm_budget.model_copy(update={"max_active_agents": 0})}))
    with pytest.raises(IntegrationError):
        ensure_budget(outbreak.model_copy(update={"swarm_budget": outbreak.swarm_budget.model_copy(update={"api_credits_remaining": 0})}))


def test_secondary_sector_drives_decision(outbreak):
    # The breach is deliberately second; reasoning cannot assume sector_reports[0].
    reordered = outbreak.model_copy(update={"sector_reports": list(reversed(outbreak.sector_reports))})
    assert demo_decision(reordered)[0].action == "evacuate"


def test_auth_health_and_input_validation(settings):
    configured = replace(settings, worker_token="secret-test-token-very-long", parasail_key="do-not-expose")
    with TestClient(create_app(configured)) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert "do-not-expose" not in health.text
        assert "secret-test-token" not in health.text
        assert health.json()["safety_gates"] == {
            "SCENARIO_ALLOW_TICK": False, "SCENARIO_ALLOW_SUBMIT": False, "DISCORD_SEND_ENABLED": False,
        }
        assert client.post("/run", json={}).status_code == 401
        assert client.get("/scoreboard").status_code == 401
        assert client.get("/runs/missing").status_code == 401
        headers = {"Authorization": "Bearer " + configured.worker_token}
        assert client.post("/run", json={"fixture": "invented"}, headers=headers).status_code == 422
        assert client.post("/run", json={"fixture": "outbreak", "url": "https://bad.example"}, headers=headers).status_code == 422


def live_settings(settings):
    return replace(settings, mode="live", team="team-worker-test", parasail_key="fake-p", you_key="fake-y",
                   one_key="fake-o", one_connections="connection", worker_token="fake-worker-token-at-least-24-chars",
                   discord_channel="222222222222222222", discord_allowed_channels="222222222222222222",
                   discord_send_enabled=True, scenario_allow_tick=True, scenario_allow_submit=True)


class FakeIntegrations:
    def __init__(self, tick, failing=False):
        self.value = tick
        self.failing = failing
        self.submits = 0
        self.sends = 0
        self.ticks = 0

    async def tick(self):
        self.ticks += 1
        if self.failing:
            raise RuntimeError("secret-upstream-key")
        return self.value

    async def submit(self, run):
        self.submits += 1
        return {"score": 1}

    async def dispatch(self, run):
        self.sends += 1
        if self.failing:
            raise RuntimeError("secret-upstream-key")
        return {"message_id": "123456789012345678"}

    async def scoreboard(self):
        return {"teams": []}


def fake_decision(tick, settings, integrations):
    return Decision(action="evacuate", rationale="Mocked decision for isolated endpoint tests.",
        evidence=[f"tick:{tick.tick_id}:catering_coffee_bar"]), [AgentSummary(role="Mock", summary="No inference.")]


def test_live_missing_config_does_not_fetch_or_fallback(settings, outbreak):
    fake = FakeIntegrations(outbreak)
    config = replace(live_settings(settings), you_key="")
    with TestClient(create_app(config, fake, fake_decision)) as client:
        response = client.post("/run", json={}, headers={"Authorization": "Bearer " + config.worker_token})
        assert response.status_code == 503
        assert fake.ticks == 0
    with TestClient(create_app(replace(config, worker_token=""), fake, fake_decision)) as client:
        assert client.post("/run", json={}).status_code == 503


def test_live_failure_is_closed_and_secret_safe(settings, outbreak):
    config = live_settings(settings)
    fake = FakeIntegrations(outbreak, failing=True)
    with TestClient(create_app(config, fake, fake_decision)) as client:
        response = client.post("/run", json={}, headers={"Authorization": "Bearer " + config.worker_token})
        assert response.status_code == 502
        assert "secret-upstream" not in response.text
        assert "No demo fallback" in response.text
        assert fake.submits == fake.sends == 0


def test_effects_require_explicit_calls_and_are_deduplicated(settings, outbreak):
    config = live_settings(settings)
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        first = client.post("/run", json={}, headers=headers).json()
        assert fake.submits == fake.sends == 0
        for _ in range(2):
            assert client.post(f"/runs/{first['id']}/submit", headers=headers).json()["submission"]["status"] == "submitted"
            assert client.post(f"/runs/{first['id']}/dispatch", headers=headers).json()["dispatch"]["status"] == "dispatched"
        assert fake.submits == fake.sends == 1
        duplicate_tick = client.post("/run", json={}, headers=headers).json()
        for path, effect in (("submit", "submission"), ("dispatch", "dispatch")):
            result = client.post(f"/runs/{duplicate_tick['id']}/{path}", headers=headers).json()
            assert result[effect]["status"] == "duplicate"
        assert fake.submits == fake.sends == 1
    # The receipt survives process restart.
    with TestClient(create_app(config, fake, fake_decision)) as client:
        client.post(f"/runs/{first['id']}/dispatch", headers=headers)
        assert fake.sends == 1


def test_uncertain_send_is_not_retried(settings, outbreak):
    config = live_settings(settings)
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        run = client.post("/run", json={}, headers=headers).json()
        fake.failing = True
        for _ in range(2):
            result = client.post(f"/runs/{run['id']}/dispatch", headers=headers)
            assert result.json()["dispatch"]["status"] == "unknown"
            assert "secret-upstream" not in result.text
        assert fake.sends == 1


def test_mcp_structured_text_and_error_parsing(outbreak):
    value = outbreak.model_dump()
    structured = SimpleNamespace(isError=False, structuredContent={"tick": value}, content=[])
    assert parse_tick(mcp_payload(structured)).tick_id == 142
    text = SimpleNamespace(isError=False, structuredContent=None,
        content=[SimpleNamespace(type="text", text=json.dumps(value))])
    assert parse_tick(mcp_payload(text)).tick_id == 142
    with pytest.raises(IntegrationError):
        mcp_payload(SimpleNamespace(isError=True))
    with pytest.raises(IntegrationError):
        parse_tick({"tick_id": 142})


def test_one_requires_documented_exact_action_and_write_access():
    docs = "### Create Message · `POST /channels/{channelId}/messages` · actionId: `found-action`\nBody: content, allowed_mentions"
    assert discord_action(docs) == "found-action"
    assert discord_action(docs.replace("{channelId}", "{{channelId}}")) == "found-action"
    with pytest.raises(IntegrationError):
        discord_action(docs.replace("POST", "DELETE"))
    with pytest.raises(IntegrationError):
        discord_action(docs.replace("###", "-"))
    read_only = {"platform": "discord", "key": "readonly", "access": {"policy": "methods", "methods": ["GET"]}}
    writable = {"platform": "discord", "key": "writable", "access": {"policy": "full"}}
    assert writable_connection({"connections": [read_only, writable]}, "found-action", "") == "writable"
    with pytest.raises(IntegrationError):
        writable_connection({"connections": [read_only]}, "found-action", "")
    with pytest.raises(IntegrationError):
        writable_connection({"connections": [writable, {**writable, "key": "ambiguous"}]}, "found-action", "")
    assert writable_connection({"connections": [writable]}, "found-action", "writable") == "writable"
    with pytest.raises(IntegrationError):
        writable_connection({"connections": [writable]}, "found-action", "another")


def test_worker_rejects_browser_origin_and_nonlocal_host(settings):
    with TestClient(create_app(settings)) as client:
        assert client.post("/run", json={}, headers={"Origin": "https://evil.example"}).status_code == 403
        assert client.get("/health", headers={"Host": "evil.example"}).status_code == 400


def test_live_run_is_bound_to_original_configuration(settings, outbreak):
    config = live_settings(settings)
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        run = client.post("/run", json={}, headers=headers).json()
    for changed in (replace(config, team="another-team"), replace(config, discord_channel="999999999999999999"),
                    replace(config, scenario_name="control-tick")):
        with TestClient(create_app(changed, fake, fake_decision)) as client:
            assert client.post(f"/runs/{run['id']}/dispatch", headers=headers).status_code == 409
            assert client.post(f"/runs/{run['id']}/submit", headers=headers).status_code == 409
    assert fake.sends == fake.submits == 0


def test_inference_failure_preserves_tick_for_next_run(settings, outbreak):
    config = live_settings(settings)
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    def failing_runner(*args):
        raise IntegrationError("Mock inference unavailable")
    with TestClient(create_app(config, fake, failing_runner)) as client:
        assert client.post("/run", json={}, headers=headers).status_code == 502
    assert fake.ticks == 1
    with TestClient(create_app(config, fake, fake_decision)) as client:
        recovered = client.post("/run", json={}, headers=headers)
        assert recovered.status_code == 200
        assert recovered.json()["tick"]["tick_id"] == 142
        assert fake.ticks == 1


def test_actual_crewai_construction_without_inference(settings, outbreak, monkeypatch):
    # Exercise real installed CrewAI constructor / provider / task schemas, but replace execution.
    import os
    os.environ["CREWAI_TRACING_ENABLED"] = "false"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["DO_NOT_TRACK"] = "true"
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(settings.database.parent / "crewai-test"))
    from crewai_core.token_manager import TokenManager
    credentials = settings.database.parent / "crewai-credentials-test"
    credentials.mkdir()
    monkeypatch.setattr(TokenManager, "_get_secure_storage_path", staticmethod(lambda: credentials))
    from crewai import Crew
    from crewai.tasks.task_output import TaskOutput
    from among_agents.crew import live_decision
    decision = Decision(action="evacuate", rationale="A breach has trapped civilians; the mock crew cites both input sources.",
        evidence=["tick:142:catering_coffee_bar", "https://example.org/safety"])

    def kickoff(self):
        assert self.process.value == "sequential"
        assert len(self.agents) == 3
        assert all(agent.allow_delegation is False for agent in self.agents)
        assert self.agents[0].llm.model == "parasail-glm-53-flash"
        assert self.agents[0].llm.base_url == "https://api.parasail.io/v1"
        self.agents[0].tools[0].run()
        self.agents[1].tools[0].run()
        assert self.agents[2].tools == []
        for task in self.tasks:
            task.output = TaskOutput(description="Mocked output", raw="Mocked local agent output", agent=task.agent.role)
        return SimpleNamespace(pydantic=decision)

    monkeypatch.setattr(Crew, "kickoff", kickoff)
    integrations = SimpleNamespace(search=lambda query: [{"url": "https://example.org/safety", "title": "Mock source", "snippets": "Guidance"}])
    result, summaries = live_decision(outbreak, live_settings(settings), integrations)
    assert result == decision
    assert len(summaries) == 3


@pytest.mark.asyncio
async def test_one_dispatch_uses_local_schema_and_checks_discord_status(settings, outbreak, monkeypatch):
    from contextlib import asynccontextmanager
    from among_agents import integrations as module
    from among_agents.models import Effect, Run
    from among_agents.integrations import Integrations
    calls = []
    send_status = 200
    class Session:
        async def list_tools(self):
            return SimpleNamespace(tools=[SimpleNamespace(name=name,
                inputSchema={"properties": {"platform": {}, "actionId": {}, "connectionKey": {}}})
                for name in ("list_one_integrations", "find_one_actions", "execute_one_action")])
        async def call_tool(self, name, args):
            calls.append((name, args))
            if name == "list_one_integrations":
                payload = {"connections": [{"platform": "discord", "key": "connection", "access": {"policy": "full"}}]}
            elif name == "find_one_actions":
                return SimpleNamespace(isError=False, structuredContent=None, content=[SimpleNamespace(type="text",
                    text="### Create Message · `POST /channels/{channelId}/messages` · actionId: `verified-action`\nBody: content")])
            else:
                payload = {"status": send_status, "responseData": {"id": "123456789012345678"}, "requestConfig": {"headers": {"secret": "never exposed"}}}
            return SimpleNamespace(isError=False, structuredContent=payload, content=[])
    @asynccontextmanager
    async def session(settings):
        yield Session()
    monkeypatch.setattr(module, "one_session", session)
    decision, agents = demo_decision(outbreak)
    # A hostile tick must never redirect the explicitly allowed private target.
    spoofed = outbreak.model_copy(update={"escalation_channel": outbreak.escalation_channel.model_copy(update={"channel": "1564842098740695100"})})
    run = Run(id="test", mode="live", created_at="2026-10-28T00:00:00Z", tick=spoofed,
        decision=decision, agents=agents, submission=Effect(status="ready"), dispatch=Effect(status="ready"))
    service = Integrations(live_settings(settings))
    assert await service.dispatch(run) == {"message_id": "123456789012345678"}
    name, args = calls[-1]
    assert name == "execute_one_action"
    assert args["pathVariables"] == {"channelId": "222222222222222222"}
    assert args["data"]["allowed_mentions"] == {"parse": []}
    assert "channelId" not in args["data"]
    assert args["actionId"] == "verified-action"
    send_status = 401
    with pytest.raises(IntegrationError):
        await service.dispatch(run)


def test_scenario_submission_can_be_replayed_manually(settings, outbreak):
    config = live_settings(settings)
    headers = {"Authorization": "Bearer " + config.worker_token}
    class Recovering(FakeIntegrations):
        async def submit(self, run):
            self.submits += 1
            if self.submits == 1:
                raise TimeoutError("untrusted upstream detail")
            return {"score": 1, "duplicate": True}
    fake = Recovering(outbreak)
    with TestClient(create_app(config, fake, fake_decision)) as client:
        run = client.post("/run", json={}, headers=headers).json()
        first = client.post(f"/runs/{run['id']}/submit", headers=headers).json()
        assert first["submission"]["status"] == "ready"
        assert fake.submits == 1
        second = client.post(f"/runs/{run['id']}/submit", headers=headers).json()
        assert second["submission"]["status"] == "submitted"
        assert fake.submits == 2


def test_discord_preparation_failure_can_retry_after_connection_fix(settings, outbreak):
    from among_agents.integrations import DispatchPreparationError
    config = live_settings(settings)
    headers = {"Authorization": "Bearer " + config.worker_token}
    class Recovering(FakeIntegrations):
        attempts = 0
        async def dispatch(self, run):
            self.attempts += 1
            if self.attempts == 1:
                raise DispatchPreparationError("No write was attempted")
            self.sends += 1
            return {"message_id": "123456789012345678"}
    fake = Recovering(outbreak)
    with TestClient(create_app(config, fake, fake_decision)) as client:
        run = client.post("/run", json={}, headers=headers).json()
        first = client.post(f"/runs/{run['id']}/dispatch", headers=headers).json()
        assert first["dispatch"]["status"] == "ready"
        assert fake.sends == 0
        second = client.post(f"/runs/{run['id']}/dispatch", headers=headers).json()
        assert second["dispatch"]["status"] == "dispatched"
        assert fake.sends == 1


def test_live_mode_alone_never_consumes_tick(settings, outbreak):
    config = replace(live_settings(settings), scenario_allow_tick=False,
                     scenario_allow_submit=False, discord_send_enabled=False)
    fake = FakeIntegrations(outbreak)
    with TestClient(create_app(config, fake, fake_decision)) as client:
        result = client.post("/run", json={}, headers={"Authorization": "Bearer " + config.worker_token})
        assert result.status_code == 503
        assert "SCENARIO_ALLOW_TICK" in result.json()["detail"]
    assert fake.ticks == fake.submits == fake.sends == 0


@pytest.mark.parametrize("path,gate", [("submit", "scenario_allow_submit"), ("dispatch", "discord_send_enabled")])
def test_side_effect_gates_block_before_claim_or_integration(settings, outbreak, path, gate):
    config = replace(live_settings(settings), **{gate: False})
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        run = client.post("/run", json={}, headers=headers).json()
        # A browser/request body cannot override server-only gates.
        result = client.post(f"/runs/{run['id']}/{path}", headers=headers, json={gate: True})
        assert result.status_code == 503
        saved = client.get(f"/runs/{run['id']}", headers=headers).json()
        assert saved["submission" if path == "submit" else "dispatch"]["status"] == "ready"
    assert fake.submits == fake.sends == 0


@pytest.mark.parametrize("changes,tick_channel", [
    ({"discord_channel": ""}, "222222222222222222"),
    ({"discord_channel": "1564842098740695100", "discord_allowed_channels": "1564842098740695100"}, "1564842098740695100"),
    ({"discord_allowed_channels": ""}, "222222222222222222"),
    ({"one_connections": ""}, "222222222222222222"),
    ({"one_connections": " , "}, "222222222222222222"),
])
def test_private_dispatch_rejects_unsafe_targets_before_integration(settings, outbreak, changes, tick_channel):
    config = replace(live_settings(settings), **changes)
    tick = outbreak.model_copy(update={"escalation_channel": outbreak.escalation_channel.model_copy(update={"channel": tick_channel})})
    fake = FakeIntegrations(tick)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        result = client.post("/run", json={}, headers=headers)
        assert result.status_code == 200
        run = result.json()
        assert client.post(f"/runs/{run['id']}/dispatch", headers=headers).status_code == 503
    assert fake.sends == 0


@pytest.mark.asyncio
async def test_direct_integration_helpers_cannot_bypass_disabled_gates(settings, outbreak, monkeypatch):
    from among_agents.integrations import Integrations
    from among_agents.models import Effect, Run
    config = replace(live_settings(settings), scenario_allow_tick=False,
                     scenario_allow_submit=False, discord_send_enabled=False)
    service = Integrations(config)
    calls = []
    async def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("The integration transport must not be reached")
    # Public high-level methods must block even if their transport is replaced.
    monkeypatch.setattr(service, "scenario_call", forbidden)
    decision, agents = demo_decision(outbreak)
    run = Run(id="blocked-test", mode="live", created_at="2026-10-28T00:00:00Z", tick=outbreak,
              decision=decision, agents=agents, submission=Effect(status="ready"), dispatch=Effect(status="ready"))
    with pytest.raises(IntegrationError, match="SCENARIO_ALLOW_TICK"):
        await service.tick()
    with pytest.raises(IntegrationError, match="SCENARIO_ALLOW_SUBMIT"):
        await service.submit(run)
    with pytest.raises(IntegrationError, match="DISCORD_SEND_ENABLED"):
        await service.dispatch(run)
    assert calls == []
    # The unpatched low-level helper also enforces policy.
    service = Integrations(config)
    with pytest.raises(IntegrationError, match="SCENARIO_ALLOW_TICK"):
        await service.scenario_call("hack26-get-tick", {})
    with pytest.raises(IntegrationError, match="SCENARIO_ALLOW_SUBMIT"):
        await service.scenario_call("hack26-submit-containment", {})
    with pytest.raises(IntegrationError, match="Unsupported"):
        await service.scenario_call("invented-write-action", {})


@pytest.mark.asyncio
@pytest.mark.parametrize("changes", [
    {"discord_channel": ""},
    {"discord_allowed_channels": ""},
    {"one_connections": " , "},
    {"discord_channel": "1564842098740695100", "discord_allowed_channels": "1564842098740695100"},
])
async def test_direct_dispatch_rejects_unsafe_config_before_one_session(settings, outbreak, monkeypatch, changes):
    from among_agents import integrations as module
    from among_agents.integrations import Integrations
    from among_agents.models import Effect, Run
    def forbidden(*args, **kwargs):
        pytest.fail("No One session may start for an unsafe configured target")
    monkeypatch.setattr(module, "one_session", forbidden)
    tick = outbreak.model_copy(update={"escalation_channel": outbreak.escalation_channel.model_copy(update={"channel": "1564842098740695100"})})
    decision, agents = demo_decision(tick)
    run = Run(id="spoofed-target", mode="live", created_at="2026-10-28T00:00:00Z", tick=tick,
              decision=decision, agents=agents, submission=Effect(status="ready"), dispatch=Effect(status="ready"))
    with pytest.raises(IntegrationError):
        await Integrations(replace(live_settings(settings), **changes)).dispatch(run)


def test_one_and_channel_configuration_is_only_required_for_dispatch(settings, outbreak):
    config = replace(live_settings(settings), one_key="", one_connections="", discord_channel="",
                     discord_allowed_channels="", discord_send_enabled=False)
    fake = FakeIntegrations(outbreak)
    headers = {"Authorization": "Bearer " + config.worker_token}
    with TestClient(create_app(config, fake, fake_decision)) as client:
        result = client.post("/run", json={}, headers=headers)
        assert result.status_code == 200
        assert client.get("/scoreboard", headers=headers).status_code == 200
        assert client.post(f"/runs/{result.json()['id']}/submit", headers=headers).status_code == 200
    assert fake.submits == 1
    assert fake.sends == 0


def test_settings_default_gates_and_dotenv_isolation(monkeypatch):
    from among_agents import config as module
    for name in ("SCENARIO_ALLOW_TICK", "SCENARIO_ALLOW_SUBMIT", "DISCORD_SEND_ENABLED", "DISCORD_CHANNEL_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SKIP_DOTENV", "1")
    def forbidden(*args, **kwargs):
        pytest.fail("Isolated smoke must not read the user's dotenv")
    monkeypatch.setattr(module, "load_dotenv", forbidden)
    config = Settings.from_env()
    assert config.discord_channel == ""
    assert config.scenario_allow_tick is config.scenario_allow_submit is config.discord_send_enabled is False
    monkeypatch.setenv("SCENARIO_ALLOW_TICK", "yes")
    assert Settings.from_env().scenario_allow_tick is False
    monkeypatch.setenv("SCENARIO_ALLOW_TICK", "true")
    assert Settings.from_env().scenario_allow_tick is True


def test_doctor_offline_shows_presence_and_gates_without_values(settings, monkeypatch, capsys):
    from among_agents import doctor
    config = replace(settings, parasail_key="fake-never-show-me", team="private-team-name", discord_channel="222222222222222222")
    monkeypatch.setattr(doctor.Settings, "from_env", lambda: config)
    monkeypatch.setattr("sys.argv", ["doctor"])
    async def forbidden(*args, **kwargs):
        pytest.fail("Offline doctor must not invoke the network checker")
    monkeypatch.setattr(doctor, "network", forbidden)
    doctor.main()
    output = capsys.readouterr().out
    assert "SET: PARASAIL_API_KEY" in output
    assert "PENDING / DISABLED: DISCORD_SEND_ENABLED" in output
    assert "PENDING / DISABLED: SCENARIO_ALLOW_TICK" in output
    assert "OFFLINE:" in output
    for secret in (config.parasail_key, config.team, config.discord_channel):
        assert secret not in output


def test_doctor_rejects_invalid_mode_without_echoing_value(settings, monkeypatch, capsys):
    from among_agents import doctor
    config = replace(settings, mode="invalid-private-value")
    monkeypatch.setattr(doctor.Settings, "from_env", lambda: config)
    monkeypatch.setattr("sys.argv", ["doctor"])
    with pytest.raises(SystemExit) as error:
        doctor.main()
    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "RUN_MODE must be demo or live" in output
    assert config.mode not in output
