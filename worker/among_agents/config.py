import os
import re
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
# Never use the venue channel from this local/private test adapter.
OFFICIAL_DISCORD_CHANNELS = frozenset({"1564842098740695100"})


def enabled(name: str) -> bool:
    # Fail closed for missing values, typos and generic truthy strings.
    return os.getenv(name, "false").strip().lower() == "true"


@dataclass(frozen=True)
class Settings:
    mode: str = "demo"
    team: str = ""
    parasail_key: str = ""
    parasail_model: str = "parasail-glm-53-flash"
    parasail_url: str = "https://api.parasail.io/v1"
    you_key: str = ""
    one_key: str = ""
    one_connections: str = ""
    discord_channel: str = ""
    discord_allowed_channels: str = ""
    discord_send_enabled: bool = False
    scenario_allow_tick: bool = False
    scenario_allow_submit: bool = False
    scenario_url: str = "https://api.you.com/mcp/halloween-hack-26"
    scenario_name: str = "outbreak-level-5"
    scenario_token: str = ""
    worker_token: str = ""
    database: Path = ROOT / "worker" / ".data" / "runs.sqlite3"

    @classmethod
    def from_env(cls):
        if os.getenv("SKIP_DOTENV") != "1":
            load_dotenv(ROOT / ".env", override=False)
        return cls(
            mode=os.getenv("RUN_MODE", "demo"), team=os.getenv("TEAM_HANDLE", ""),
            parasail_key=os.getenv("PARASAIL_API_KEY", ""),
            parasail_model=os.getenv("PARASAIL_MODEL", "parasail-glm-53-flash"),
            parasail_url=os.getenv("PARASAIL_BASE_URL", "https://api.parasail.io/v1"),
            you_key=os.getenv("YDC_API_KEY", ""), one_key=os.getenv("ONE_API_KEY", ""),
            one_connections=os.getenv("ONE_CONNECTION_KEYS", ""),
            discord_channel=os.getenv("DISCORD_CHANNEL_ID", ""),
            discord_allowed_channels=os.getenv("DISCORD_ALLOWED_CHANNEL_IDS", ""),
            discord_send_enabled=enabled("DISCORD_SEND_ENABLED"),
            scenario_allow_tick=enabled("SCENARIO_ALLOW_TICK"),
            scenario_allow_submit=enabled("SCENARIO_ALLOW_SUBMIT"),
            scenario_url=os.getenv("SCENARIO_MCP", "https://api.you.com/mcp/halloween-hack-26"),
            scenario_name=os.getenv("SCENARIO_NAME", "outbreak-level-5"),
            scenario_token=os.getenv("SCENARIO_TEAM_TOKEN", ""),
            worker_token=os.getenv("WORKER_TOKEN", ""),
            database=Path(os.getenv("WORKER_DB", str(ROOT / "worker" / ".data" / "runs.sqlite3"))),
        )

    def validate_mode(self):
        if self.mode not in ("demo", "live"):
            raise ValueError("RUN_MODE must be demo or live.")

    def validate_live(self, action="run"):
        self.validate_mode()
        if self.mode != "live":
            raise ValueError("External integrations require RUN_MODE=live.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,31}", self.team):
            raise ValueError("TEAM_HANDLE must use 2–32 lowercase letters, numbers or dashes.")
        required = [("WORKER_TOKEN", self.worker_token)]
        if action == "run":
            required.extend((("PARASAIL_API_KEY", self.parasail_key), ("YDC_API_KEY", self.you_key)))
        elif action == "search":
            required.append(("YDC_API_KEY", self.you_key))
        elif action == "dispatch":
            required.extend((("ONE_API_KEY", self.one_key), ("ONE_CONNECTION_KEYS", self.one_connections)))
        elif action not in ("tick", "submission", "scoreboard"):
            raise ValueError("Unsupported live action.")
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError("Missing live configuration: " + ", ".join(missing))
        if len(self.worker_token) < 24:
            raise ValueError("WORKER_TOKEN must have at least 24 characters in live mode.")
        if self.scenario_name not in ("outbreak-level-5", "control-tick"):
            raise ValueError("SCENARIO_NAME must be outbreak-level-5 or control-tick.")
        if not self.scenario_url.startswith("https://") or not self.parasail_url.startswith("https://"):
            raise ValueError("Live integration URLs must use HTTPS.")
        if len(self.scenario_token) > 128:
            raise ValueError("SCENARIO_TEAM_TOKEN exceeds the feed's length limit.")

    def require_tick(self):
        if not self.scenario_allow_tick:
            raise ValueError("SCENARIO_ALLOW_TICK is disabled; fetching a tick advances the team cursor.")
        self.validate_live("tick")

    def require_submit(self):
        if not self.scenario_allow_submit:
            raise ValueError("SCENARIO_ALLOW_SUBMIT is disabled; submission changes the event scoreboard.")
        self.validate_live("submission")

    def require_dispatch(self):
        if not self.discord_send_enabled:
            raise ValueError("DISCORD_SEND_ENABLED is disabled; One dispatch requires an explicitly allowed private test channel.")
        self.validate_live("dispatch")
        connections = {key.strip() for key in self.one_connections.split(",") if key.strip()}
        if not connections:
            raise ValueError("ONE_CONNECTION_KEYS must contain an explicitly allowed private Discord connection key.")
        if not re.fullmatch(r"[0-9]{15,22}", self.discord_channel):
            raise ValueError("DISCORD_CHANNEL_ID must be an explicitly configured numeric private channel ID.")
        allowed = {channel.strip() for channel in self.discord_allowed_channels.split(",") if channel.strip()}
        if self.discord_channel in OFFICIAL_DISCORD_CHANNELS:
            raise ValueError("The official venue Discord channel is forbidden for this private test adapter.")
        if self.discord_channel not in allowed:
            raise ValueError("DISCORD_CHANNEL_ID must be listed in DISCORD_ALLOWED_CHANNEL_IDS.")

    def health(self):
        configured = [
            ("CrewAI", True, "Local Python; live execution is checked only by a live run."),
            ("Parasail", bool(self.parasail_key), "Configuration only; credentials are not tested."),
            ("You.com", bool(self.you_key), "Configuration only; credentials are not tested."),
            ("WithOne / Discord", bool(self.one_key), "Private Discord via One; explicit send gate, allowed channel and connection required."),
            ("Scenario MCP", bool(self.scenario_url), "Configuration only; fetching a tick advances the team cursor."),
            ("Worker authentication", bool(self.worker_token), "Bearer token; required for live mode."),
        ]
        return {"status": "ok", "mode": self.mode, "safety_gates": {
            "SCENARIO_ALLOW_TICK": self.scenario_allow_tick,
            "SCENARIO_ALLOW_SUBMIT": self.scenario_allow_submit,
            "DISCORD_SEND_ENABLED": self.discord_send_enabled,
        }, "integrations": [
            {"name": name, "configured": value, "detail": detail} for name, value, detail in configured]}
