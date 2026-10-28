import asyncio
import hmac
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import ROOT, Settings
from .crew import demo_decision, live_decision
from .integrations import DispatchPreparationError, IntegrationError, Integrations
from .models import Effect, Run, RunRequest, Tick
from .store import Store


def create_app(settings: Settings | None = None, integrations=None, decision_runner=None):
    settings = settings or Settings.from_env()
    settings.validate_mode()
    context = hashlib.sha256(json.dumps([settings.mode, settings.team, settings.scenario_name,
        settings.scenario_url, settings.discord_channel]).encode()).hexdigest()
    store = Store(settings.database)
    integrations = integrations or Integrations(settings)
    decision_runner = decision_runner or live_decision
    app = FastAPI(title="Among Agents local worker", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"])

    @app.middleware("http")
    async def reject_direct_browser_requests(request, call_next):
        if request.headers.get("origin"):
            return JSONResponse(status_code=403, content={"detail": "Use the local Next.js interface for browser requests."})
        return await call_next(request)

    app.state.store = store
    run_lock = asyncio.Lock()

    async def authorize(authorization: str | None = Header(default=None)):
        if settings.worker_token:
            expected = "Bearer " + settings.worker_token
            if not authorization or not hmac.compare_digest(authorization, expected):
                raise HTTPException(401, "Worker authorization required.")
        elif settings.mode == "live":
            raise HTTPException(503, "WORKER_TOKEN is required in live mode.")

    def live_ready(action="run"):
        try:
            settings.validate_live(action)
            if action == "run":
                settings.require_tick()
            elif action == "submission":
                settings.require_submit()
            elif action == "dispatch":
                settings.require_dispatch()
        except ValueError as error:
            raise HTTPException(503, str(error)) from None

    def read_run(run_id):
        run = store.get(run_id)
        if run is None:
            raise HTTPException(404, "Run not found.")
        if run.mode != settings.mode:
            raise HTTPException(409, "This run belongs to a different mode. Restart using its original mode.")
        if settings.mode == "live" and store.context(run_id) != context:
            raise HTTPException(409, "Run configuration changed. Restore its original team, scenario and Discord channel before acting.")
        return run

    @app.exception_handler(IntegrationError)
    async def integration_error(_request, error):
        return JSONResponse(status_code=502, content={"detail": str(error)})

    @app.get("/health")
    async def health():
        return settings.health()

    @app.post("/run", dependencies=[Depends(authorize)], response_model=Run)
    async def run(request: RunRequest):
        if run_lock.locked():
            raise HTTPException(409, "A run is already active. Wait for it to finish.")
        async with run_lock:
            if settings.mode == "demo":
                fixture = "outbreak-level-5.json" if request.fixture == "outbreak" else "control-tick.json"
                tick = Tick.model_validate(json.loads((ROOT / "fixtures" / fixture).read_text())["ticks"][0])
                decision, agents = demo_decision(tick)
            else:
                live_ready()
                try:
                    tick = store.pending(context)
                    if tick is None:
                        tick = await integrations.tick()
                        store.keep_pending(context, tick)
                    decision, agents = await asyncio.to_thread(decision_runner, tick, settings, integrations)
                except IntegrationError:
                    raise
                except Exception:
                    raise IntegrationError("Live run failed. No demo fallback was used; no submission or Discord send occurred.") from None
            record = Run(id=str(uuid4()), mode=settings.mode, created_at=datetime.now(timezone.utc).isoformat(),
                tick=tick, decision=decision, agents=agents,
                submission=Effect(status="ready"),
                dispatch=Effect(status="not_required" if decision.action == "observe" else "ready",
                    detail="Observation decisions do not trigger an escalation." if decision.action == "observe" else None))
            store.save(record, context)
            return record

    @app.get("/runs/{run_id}", dependencies=[Depends(authorize)], response_model=Run)
    async def get_run(run_id: str):
        return read_run(run_id)

    async def act(run_id: str, kind: str):
        record = read_run(run_id)
        if settings.mode == "live":
            live_ready(kind)
        # Include team and target so repeated end-of-feed ticks cannot send duplicate actions.
        key = f"{context}:{record.tick.tick_id}:{kind}"
        if kind == "dispatch":
            key += f":{settings.discord_channel}"
        record, claimed = store.claim(run_id, kind, key)
        if not claimed:
            return record
        if settings.mode == "demo":
            return store.finish(run_id, kind, Effect(status="simulated", detail="Offline demonstration only; no external request was made."))
        try:
            if kind == "submission":
                result = await integrations.submit(record)
                score = result.get("score")
                detail = "Scenario MCP confirmed the submission."
                if isinstance(score, (int, float)) and 0 <= score <= 1:
                    detail += f" Score: {score:.2f}."
                effect = Effect(status="submitted", detail=detail)
            else:
                result = await integrations.dispatch(record)
                effect = Effect(status="dispatched", detail=f"Discord confirmed message {result['message_id']}.")
        except DispatchPreparationError:
            return store.release(run_id, kind, key,
                "WithOne preparation failed before any Discord write. Verify the key, connection permissions and action documentation, then retry.")
        except Exception:
            if kind == "submission":
                return store.release(run_id, kind, key,
                    "Submission unconfirmed. The official feed deduplicates team/tick submissions, so retry this same run manually when available.")
            effect = Effect(status="unknown", detail=(
                "Success could not be confirmed. Automatic retry is disabled to avoid duplicate actions. "
                "Inspect the scoreboard or Discord channel, then verify credentials, permissions and action documentation."))
        return store.finish(run_id, kind, effect)

    @app.post("/runs/{run_id}/submit", dependencies=[Depends(authorize)], response_model=Run)
    async def submit(run_id: str):
        return await act(run_id, "submission")

    @app.post("/runs/{run_id}/dispatch", dependencies=[Depends(authorize)], response_model=Run)
    async def dispatch(run_id: str):
        return await act(run_id, "dispatch")

    @app.get("/scoreboard", dependencies=[Depends(authorize)])
    async def scoreboard():
        if settings.mode == "demo":
            return {"mode": "demo", "scoreboard": [], "detail": "Demo results are not submitted to the event scoreboard."}
        live_ready("scoreboard")
        try:
            result = await integrations.scoreboard()
            return {"mode": "live", "scoreboard": result}
        except Exception:
            raise IntegrationError("Scenario scoreboard is unavailable. Check connectivity and the scenario URL.") from None

    return app


app = create_app()
