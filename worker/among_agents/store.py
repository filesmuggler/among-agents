"""Persist each effect claim before I/O. An uncertain send is never retried automatically."""
import sqlite3
from pathlib import Path
from .models import Effect, Run, Tick


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            columns = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
            if "context" not in columns:
                db.execute("ALTER TABLE runs ADD COLUMN context TEXT NOT NULL DEFAULT ''")
            db.execute("CREATE TABLE IF NOT EXISTS pending_ticks (context TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS effects (effect_key TEXT PRIMARY KEY, run_id TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, run: Run, context: str = ""):
        with self.connect() as db:
            db.execute("INSERT INTO runs(id,payload,context) VALUES (?,?,?)", (run.id, run.model_dump_json(), context))
            db.execute("DELETE FROM pending_ticks WHERE context=?", (context,))

    def context(self, run_id: str):
        with self.connect() as db:
            row = db.execute("SELECT context FROM runs WHERE id=?", (run_id,)).fetchone()
        return row[0] if row else None

    def pending(self, context: str):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM pending_ticks WHERE context=?", (context,)).fetchone()
        return Tick.model_validate_json(row[0]) if row else None

    def keep_pending(self, context: str, tick: Tick):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO pending_ticks VALUES (?,?)", (context, tick.model_dump_json()))

    def get(self, run_id: str):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def claim(self, run_id: str, kind: str, effect_key: str):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                raise KeyError(run_id)
            run = Run.model_validate_json(row[0])
            if getattr(run, kind).status != "ready":
                return run, False
            prior = db.execute("SELECT run_id FROM effects WHERE effect_key=?", (effect_key,)).fetchone()
            if prior:
                setattr(run, kind, Effect(status="duplicate", detail="This tick already has a claimed action. Inspect the original run before acting."))
                db.execute("UPDATE runs SET payload=? WHERE id=?", (run.model_dump_json(), run_id))
                return run, False
            db.execute("INSERT INTO effects VALUES (?,?)", (effect_key, run_id))
            setattr(run, kind, Effect(status="in_progress", detail="Claim saved before external request; no automatic retry."))
            db.execute("UPDATE runs SET payload=? WHERE id=?", (run.model_dump_json(), run_id))
            return run, True

    def finish(self, run_id: str, kind: str, effect: Effect):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
            run = Run.model_validate_json(row[0])
            setattr(run, kind, effect)
            db.execute("UPDATE runs SET payload=? WHERE id=?", (run.model_dump_json(), run_id))
            return run

    def release(self, run_id: str, kind: str, effect_key: str, detail: str):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone()
            run = Run.model_validate_json(row[0])
            if getattr(run, kind).status == "in_progress":
                db.execute("DELETE FROM effects WHERE effect_key=? AND run_id=?", (effect_key, run_id))
                setattr(run, kind, Effect(status="ready", detail=detail))
                db.execute("UPDATE runs SET payload=? WHERE id=?", (run.model_dump_json(), run_id))
            return run
