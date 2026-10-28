"""Opt-in read-only checks. Never fetches ticks, submits decisions, or sends messages."""
import argparse
import asyncio
import httpx
from .config import Settings
from .integrations import discord_action, mcp_payload, one_session, scenario_session, writable_connection


async def network(settings: Settings):
    checks = []
    async def check(name, operation):
        try:
            await operation()
            checks.append((name, True))
        except Exception:
            checks.append((name, False))

    async def parasail():
        if not settings.parasail_key:
            raise ValueError("missing")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(settings.parasail_url.rstrip("/") + "/models",
                headers={"Authorization": "Bearer " + settings.parasail_key})
            response.raise_for_status()
            models = response.json().get("data", [])
            if settings.parasail_model not in {row.get("id") for row in models if isinstance(row, dict)}:
                raise ValueError("configured model absent")

    async def you():
        if not settings.you_key:
            raise ValueError("missing")
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post("https://ydc-index.io/v1/search", headers={"X-API-Key": settings.you_key},
                json={"query": "AWS Builder Loft San Francisco", "count": 1})
            response.raise_for_status()
            if not isinstance(response.json().get("results"), dict):
                raise ValueError("unexpected shape")

    async def scenario():
        async with asyncio.timeout(60):
            async with scenario_session(settings) as session:
                names = {tool.name for tool in (await session.list_tools()).tools}
                if not {"hack26-get-tick", "hack26-submit-containment", "hack26-get-scoreboard"}.issubset(names):
                    raise ValueError("required tools missing")

    async def one():
        if not settings.one_key:
            raise ValueError("missing")
        async with asyncio.timeout(75):
            async with one_session(settings) as session:
                names = {tool.name for tool in (await session.list_tools()).tools}
                if "execute_one_action" not in names:
                    raise ValueError("write capability absent")
                connections = mcp_payload(await session.call_tool("list_one_integrations", {}))
                docs = mcp_payload(await session.call_tool("find_one_actions", {
                    "task": "check the Discord send action documentation without executing",
                    "requests": [{"platform": "discord", "intent": "send a message to a channel"}],
                }))
                action = discord_action(docs)
                writable_connection(connections, action, settings.one_connections)

    # Sequential, bounded reads; no retry loops or credential values in output.
    await check("Parasail model availability", parasail)
    await check("You.com Search (one billable request)", you)
    await check("Scenario MCP discovery (no cursor advance)", scenario)
    await check("WithOne Discord discovery (no send; event role unverified)", one)
    for name, success in checks:
        print(f"{'PASS' if success else 'FAIL'}: {name}")
    return all(success for _, success in checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true", help="Read-only remote checks; You.com search may consume credits.")
    args = parser.parse_args()
    settings = Settings.from_env()
    try:
        settings.validate_mode()
    except ValueError as error:
        print(f"FAIL: {error}")
        raise SystemExit(1) from None
    print("PASS: RUN_MODE is valid. Configuration presence is not credential verification.")
    fields = {
        "TEAM_HANDLE": settings.team,
        "WORKER_TOKEN": settings.worker_token,
        "YDC_API_KEY": settings.you_key,
        "PARASAIL_API_KEY": settings.parasail_key,
        "PARASAIL_BASE_URL": settings.parasail_url,
        "PARASAIL_MODEL": settings.parasail_model,
        "ONE_API_KEY": settings.one_key,
        "ONE_CONNECTION_KEYS": settings.one_connections,
        "DISCORD_CHANNEL_ID": settings.discord_channel,
        "DISCORD_ALLOWED_CHANNEL_IDS": settings.discord_allowed_channels,
        "SCENARIO_MCP": settings.scenario_url,
        "SCENARIO_NAME": settings.scenario_name,
        "SCENARIO_TEAM_TOKEN": settings.scenario_token,
    }
    for name, value in fields.items():
        print(f"{'SET' if value else 'MISSING'}: {name}")
    for name, value in settings.health()["safety_gates"].items():
        print(f"{'ENABLED' if value else 'PENDING / DISABLED'}: {name}")
    print("PENDING: Confirm Track 1 transport requirements (One versus webhook) before official verification.")
    if settings.mode == "live":
        try:
            settings.validate_live("run")
        except ValueError as error:
            print(f"FAIL: {error}")
            raise SystemExit(1) from None
    if not args.network:
        print("OFFLINE: no remote calls, tick retrieval, submissions or Discord sends.")
    if args.network:
        print("Checking services without inference, tick retrieval, submissions or Discord sends.")
        raise SystemExit(0 if asyncio.run(network(settings)) else 1)


if __name__ == "__main__":
    main()
