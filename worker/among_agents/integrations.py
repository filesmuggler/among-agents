"""Explicit MCP SDK clients. Models never receive write tools or credentials."""
import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any
import httpx
from .config import ROOT, Settings
from .models import Run, Tick


class IntegrationError(RuntimeError):
    """Public messages deliberately exclude upstream payloads, headers and exceptions."""


class DispatchPreparationError(IntegrationError):
    """No Discord write was attempted; the local claim can be released safely."""


def mcp_payload(result: Any):
    if getattr(result, "isError", False):
        raise IntegrationError("MCP rejected the request. Check credentials, scopes and the documented schema.")
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    texts = [item.text for item in getattr(result, "content", []) if getattr(item, "type", None) == "text"]
    if not texts:
        raise IntegrationError("MCP returned no readable result.")
    text = "\n".join(texts)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def parse_tick(payload: Any) -> Tick:
    if isinstance(payload, dict) and isinstance(payload.get("tick"), dict):
        payload = payload["tick"]
    if not isinstance(payload, dict):
        raise IntegrationError("Scenario MCP returned an unsupported tick shape.")
    # Cursor metadata belongs to the envelope, not to the fixed tick contract.
    payload = {key: value for key, value in payload.items() if key in Tick.model_fields}
    try:
        return Tick.model_validate(payload)
    except ValueError:
        raise IntegrationError("Scenario MCP returned an invalid tick; no inference or writes were attempted.") from None


def discord_action(document: Any):
    # @withone/mcp 2.3.2 returns Markdown, unlike the CLI's JSON answers.
    if not isinstance(document, str):
        raise IntegrationError("WithOne action documentation has an unsupported shape.")
    candidates = re.findall(r"^### .+? · `POST ([^`]+)` · actionId: `([^`]+)`\s*$", document, re.MULTILINE)
    matches = [(path, action_id) for path, action_id in candidates
               if re.fullmatch(r"/channels/\{channelId\}/messages", path.replace("{{", "{").replace("}}", "}"))]
    if len(matches) != 1:
        raise IntegrationError("WithOne did not document exactly one Discord POST /channels/{channelId}/messages action.")
    return matches[0][1]


def writable_connection(payload: Any, action_id: str, allowlist: str):
    if not isinstance(payload, dict) or payload.get("knowledgeOnly"):
        raise IntegrationError("WithOne returned no writable connection list.")
    allowed = {key.strip() for key in allowlist.split(",") if key.strip()}
    matches = []
    for connection in payload.get("connections", []):
        if not isinstance(connection, dict) or connection.get("platform") != "discord":
            continue
        key = connection.get("key")
        if not isinstance(key, str) or (allowed and key not in allowed):
            continue
        access = connection.get("access", {})
        policy = access.get("policy") if isinstance(access, dict) else None
        permitted = policy == "full" or (
            policy == "methods" and "POST" in access.get("methods", [])
        ) or (policy == "actions" and any(action.get("actionId") == action_id
                for action in access.get("actions", []) if isinstance(action, dict)))
        if permitted and action_id not in connection.get("unresolvedActionIds", []):
            matches.append(key)
    if len(matches) != 1:
        raise IntegrationError("Select exactly one writable Discord connection with ONE_CONNECTION_KEYS; verify the event account and role.")
    return matches[0]


@asynccontextmanager
async def scenario_session(settings: Settings):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(settings.scenario_url, timeout=timedelta(seconds=30),
                                     sse_read_timeout=timedelta(seconds=60)) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def one_session(settings: Settings):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    node = ROOT / "node_modules" / ".bin" / "node"
    script = ROOT / "node_modules" / "@withone" / "mcp" / "build" / "index.js"
    if not node.exists() or not script.exists():
        raise IntegrationError("Local WithOne dependencies are missing. Run npm install in the repository root.")
    environment = {key: os.environ[key] for key in ("PATH", "HOME", "TMPDIR", "SYSTEMROOT") if key in os.environ}
    environment["ONE_SECRET"] = settings.one_key
    if settings.one_connections:
        environment["ONE_CONNECTION_KEYS"] = settings.one_connections
    params = StdioServerParameters(command=str(node), args=[str(script)], env=environment)
    # Some upstream errors include request headers. Never relay the child stderr.
    with open(os.devnull, "w") as errlog:
        async with stdio_client(params, errlog=errlog) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session


class Integrations:
    def __init__(self, settings: Settings):
        self.settings = settings

    def require(self, check, *args):
        try:
            check(*args)
        except ValueError as error:
            raise IntegrationError(str(error)) from None

    def team_args(self):
        result = {"team": self.settings.team}
        if self.settings.scenario_token:
            result["token"] = self.settings.scenario_token
        return result

    async def scenario_call(self, name: str, args: dict):
        # Also protect direct callers of this low-level helper.
        if name == "hack26-get-tick":
            self.require(self.settings.require_tick)
        elif name == "hack26-submit-containment":
            self.require(self.settings.require_submit)
        elif name == "hack26-get-scoreboard":
            self.require(self.settings.validate_live, "scoreboard")
        else:
            raise IntegrationError("Unsupported Scenario MCP action.")
        async with asyncio.timeout(75):
            async with scenario_session(self.settings) as session:
                return mcp_payload(await session.call_tool(name, args))

    async def tick(self):
        self.require(self.settings.require_tick)
        args = {**self.team_args(), "scenario": self.settings.scenario_name}
        return parse_tick(await self.scenario_call("hack26-get-tick", args))

    async def submit(self, run: Run):
        self.require(self.settings.require_submit)
        result = await self.scenario_call("hack26-submit-containment", {
            **self.team_args(), "tick_id": run.tick.tick_id, "action": run.decision.action,
        })
        if (not isinstance(result, dict) or result.get("error")
                or type(result.get("score")) not in (int, float) or not 0 <= result["score"] <= 1):
            raise IntegrationError("Scenario MCP did not confirm the submission. Inspect the scoreboard before retrying.")
        return result

    async def scoreboard(self):
        self.require(self.settings.validate_live, "scoreboard")
        return await self.scenario_call("hack26-get-scoreboard", {})

    def search(self, query: str):
        self.require(self.settings.validate_live, "search")
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post("https://ydc-index.io/v1/search", headers={
                    "X-API-Key": self.settings.you_key, "Content-Type": "application/json",
                }, json={"query": query, "count": 3})
                if response.status_code == 429:
                    raise IntegrationError("You.com rate limit reached. Wait before running again; there is no automatic retry.")
                response.raise_for_status()
                result = response.json()
            rows = result.get("results", {}).get("web", [])
            sources = [{"url": row["url"], "title": str(row.get("title", ""))[:300],
                        "snippets": str(row.get("snippets", row.get("description", "")))[:1800]}
                       for row in rows[:3] if isinstance(row, dict) and isinstance(row.get("url"), str)
                       and row["url"].startswith("https://")]
            if not sources:
                raise IntegrationError("You.com returned no usable sources; live reasoning stopped.")
            return sources
        except IntegrationError:
            raise
        except Exception:
            raise IntegrationError("You.com grounding failed. Check the key, Search access and connectivity.") from None

    async def dispatch(self, run: Run):
        # The untrusted tick's escalation destination never selects or authorizes a send.
        self.require(self.settings.require_dispatch)
        attempted = False
        try:
            async with asyncio.timeout(90):
                async with one_session(self.settings) as session:
                    tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                    expected = {"list_one_integrations", "find_one_actions", "execute_one_action"}
                    if not expected.issubset(tools):
                        raise IntegrationError("WithOne is missing required tools; check knowledge-only mode and connection permissions.")
                    schema = tools["execute_one_action"].inputSchema
                    if not {"platform", "actionId", "connectionKey"}.issubset(schema.get("properties", {})):
                        raise IntegrationError("WithOne execute schema changed; review the local MCP version before sending.")
                    connections = mcp_payload(await session.call_tool("list_one_integrations", {}))
                    document = mcp_payload(await session.call_tool("find_one_actions", {
                        "task": "post a containment alert to the explicitly allowed private test channel",
                        "requests": [{"platform": "discord", "intent": "send a message to a channel"}],
                    }))
                    action_id = discord_action(document)
                    connection = writable_connection(connections, action_id, self.settings.one_connections)
                    sectors = ", ".join(sector.sector for sector in run.tick.sector_reports)
                    message = (f"{self.settings.team} · tick {run.tick.tick_id} · [{sectors}] · "
                               f"{run.decision.action} · {run.decision.rationale}")[:1900]
                    attempted = True
                    payload = mcp_payload(await session.call_tool("execute_one_action", {
                        "platform": "discord", "actionId": action_id, "connectionKey": connection,
                        "pathVariables": {"channelId": self.settings.discord_channel},
                        "data": {"content": message, "allowed_mentions": {"parse": []}},
                    }))
                    # One can return Discord 4xx in structuredContent without isError.
                    if not isinstance(payload, dict) or not isinstance(payload.get("status"), int) or not 200 <= payload["status"] < 300:
                        raise IntegrationError("Discord did not confirm a successful send. Inspect the channel and connection before any manual retry.")
                    response = payload.get("responseData", {})
                    message_id = response.get("id") if isinstance(response, dict) else None
                    if not isinstance(message_id, str) or not message_id.isdigit():
                        raise IntegrationError("Discord did not return a message ID; inspect the channel before any retry.")
                    return {"message_id": message_id}
        except Exception:
            if not attempted:
                raise DispatchPreparationError("WithOne preparation failed before any Discord write. Verify the key, writable connection and documented action, then retry.") from None
            raise IntegrationError("Discord send was attempted but success could not be confirmed. Inspect the channel before any retry.") from None
