"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Fixture, Health, Run } from "@/lib/types";

const actionLabels = { contain: "Zabezpiecz sektor", evacuate: "Ewakuuj cywilów", observe: "Kontynuuj obserwację" };
const lastRunKey = "among-agents:last-run-id";

class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

function text(value: unknown): string {
  if (value === null || value === undefined) return "Brak danych";
  if (typeof value === "string") return value;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function sensorText(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return text(value);
  const labels: Record<string, string> = { emf_milligauss: "EMF", temp_c: "Temperatura", motion_events: "Ruch" };
  const units: Record<string, string> = { emf_milligauss: " mG", temp_c: "°C", motion_events: " zdarzeń" };
  return Object.entries(value).map(([key, reading]) => `${labels[key] ?? key}: ${text(reading)}${units[key] ?? ""}`).join(" · ");
}

function budgetText(value: unknown): string {
  if (value && typeof value === "object" && "max_active_agents" in value && "api_credits_remaining" in value) {
    return `${text(value.max_active_agents)} agentów / ${text(value.api_credits_remaining)} kredytów API`;
  }
  return text(value);
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, { cache: "no-store", ...options });
  const result = await response.json();
  if (!response.ok) throw new ApiError(response.status, typeof result.error === "string" ? result.error : "Operacja nie powiodła się.");
  return result as T;
}

function Orbit({ small = false }: { small?: boolean }) {
  return <svg className={small ? "orbit small" : "orbit"} width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true"><circle cx="20" cy="20" r="7" fill="currentColor"/><ellipse cx="20" cy="20" rx="18" ry="9" transform="rotate(-40 20 20)" stroke="currentColor" strokeWidth="1.6"/><circle cx="34" cy="9" r="3" fill="currentColor"/></svg>;
}

function Status({ label, active = false }: { label: string; active?: boolean }) {
  return <span className={`status ${active ? "active" : ""}`}><span />{label}</span>;
}

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState("");
  const [fixture, setFixture] = useState<Fixture>("outbreak");
  const [run, setRun] = useState<Run | null>(null);
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [scoreboard, setScoreboard] = useState<unknown>(null);
  const busy = useRef(false);
  const isLive = health?.mode === "live";

  const loadHealth = useCallback(async () => {
    setHealthLoading(true);
    setHealthError("");
    try {
      const current = await api<Health>("/api/health");
      setHealth(current);
      return current;
    }
    catch (cause) { setHealth(null); setHealthError(cause instanceof Error ? cause.message : "Worker jest niedostępny."); return null; }
    finally { setHealthLoading(false); }
  }, []);

  useEffect(() => {
    let active = true;
    busy.current = true;
    setPending("restore");
    void loadHealth().then(async (currentHealth) => {
      if (!active || !currentHealth) return;
      let savedId: string | null;
      try { savedId = localStorage.getItem(lastRunKey); }
      catch { return; }
      if (!savedId) return;
      if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(savedId)) {
        localStorage.removeItem(lastRunKey);
        return;
      }
      try {
        const saved = await api<Run>(`/api/runs/${encodeURIComponent(savedId)}`);
        if (!active) return;
        if (saved.mode !== currentHealth.mode) {
          localStorage.removeItem(lastRunKey);
          return;
        }
        setRun(saved);
      } catch (cause) {
        if (!active) return;
        if (cause instanceof ApiError && cause.status === 404) localStorage.removeItem(lastRunKey);
        else setError("Nie udało się przywrócić ostatniej rundy. Odśwież stronę po sprawdzeniu workera.");
      }
    }).finally(() => {
      if (active) { busy.current = false; setPending(""); }
    });
    return () => { active = false; };
  }, [loadHealth]);

  async function perform(kind: "run" | "submit" | "dispatch" | "refresh" | "scoreboard") {
    if (busy.current) return;
    busy.current = true;
    setPending(kind);
    setError("");
    try {
      if (kind === "scoreboard") {
        setScoreboard(await api<unknown>("/api/scoreboard"));
      } else if (kind === "run") {
        const nextRun = await api<Run>("/api/runs", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ fixture }),
        });
        setRun(nextRun);
        try { localStorage.setItem(lastRunKey, nextRun.id); } catch { /* Local storage is optional; the worker still persists the run. */ }
      } else if (run) {
        setRun(await api<Run>(`/api/runs/${encodeURIComponent(run.id)}${kind === "refresh" ? "" : `/${kind}`}`, { method: kind === "refresh" ? "GET" : "POST" }));
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Nie udało się ukończyć operacji."); }
    finally { busy.current = false; setPending(""); }
  }

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Among Agents — strona główna"><Orbit /><span>among<span className="brand-light">agents</span><span className="brand-caption">HALLOWEEN HACK 2026</span></span></a>
      <div className="topbar-right"><span className="local-tag">LOCAL COMMAND</span><Status label={healthLoading ? "Łączenie…" : health ? "Worker online" : "Worker offline"} active={Boolean(health)} /></div>
    </header>

    <main>
      <section className="hero">
        <div><div className="eyebrow"><span className="accent-line" /> STACJA DOWODZENIA / 01</div><h1>Zaufaj sygnałom.<br /><span>Sprawdź agentów.</span></h1><p className="hero-copy">Zbierz raporty z placówki. Porównaj ocenę agentów.<br className="desktop-break" /> Podejmij decyzję, zanim sytuacja wymknie się spod kontroli.</p></div>
        <div className={`mode-card ${isLive ? "live-mode" : ""}`}><span className="eyebrow">TRYB DZIAŁANIA</span><strong>{health ? isLive ? "LIVE" : "LOKALNE DEMO" : "OCZEKIWANIE"}</strong><p>{health ? isLive ? "Tryb usług zewnętrznych. Dostępność potwierdza udana operacja. Runda pobiera scenariusz i wywołuje agentów." : "Dane testowe i lokalne reguły. Bez wywołań modeli, wyszukiwania i zewnętrznych zapisów." : "Po uruchomieniu workera sprawdzimy dostępny tryb."}</p></div>
      </section>

      <div className="workspace">
        <aside className="control-column">
          <section className="panel control-panel">
            <div className="section-heading"><span className="eyebrow">01 / PRZYGOTOWANIE</span><span className="number-mark">⌘</span></div>
            <h2>Uruchom rundę</h2><p className="muted">Jeden tick. Wspólna ocena. Jedna decyzja.</p>
            <fieldset disabled={Boolean(pending) || isLive} className="fixture-options"><legend>{isLive ? "Scenariusz określa konfiguracja workera" : "Wybierz dane testowe"}</legend>
              <label className={fixture === "outbreak" ? "selected" : ""}><input type="radio" name="fixture" value="outbreak" checked={fixture === "outbreak"} onChange={() => setFixture("outbreak")} /><span><strong>Wykryte zagrożenie</strong><small>Sygnały wymagające reakcji</small></span><span className="radio-dot" /></label>
              <label className={fixture === "control" ? "selected" : ""}><input type="radio" name="fixture" value="control" checked={fixture === "control"} onChange={() => setFixture("control")} /><span><strong>Próba kontrolna</strong><small>Ocena spokojnej placówki</small></span><span className="radio-dot" /></label>
            </fieldset>
            <button className="button primary" disabled={!health || Boolean(pending)} onClick={() => void perform("run")}><span>{pending === "run" ? "Agenci analizują…" : "Uruchom analizę"}</span><span aria-hidden="true">↗</span></button>
            <p className="microcopy">{isLive ? "Runda używa Parasail, You.com i scenario MCP. Wysłanie wyniku i Discord to osobne akcje." : "Demo działa bez kluczy. Uruchom lokalny worker, aby rozpocząć."}</p>
          </section>

          <section className="panel integrations-panel"><div className="section-heading"><h2>Połączenia</h2><button className="text-button" disabled={healthLoading} onClick={() => void loadHealth()} aria-label="Odśwież połączenia">{healthLoading ? "…" : "Odśwież ↻"}</button></div>
            {health ? <><p className="microcopy integration-note">„Skonfigurowano” oznacza obecność ustawień. Dostępność usług potwierdza dopiero udana operacja.</p><ul className="integrations">{health.integrations.map((integration) => <li key={integration.name}><div><span className={`connection-dot ${integration.configured ? "configured" : ""}`} /><strong>{integration.name}</strong><span className="connection-label">{integration.configured ? "Skonfigurowano" : "Brak konfiguracji"}</span></div><p>{integration.detail}</p></li>)}</ul></> : <div className="worker-help"><p>{healthError || "Sprawdzanie lokalnego workera…"}</p>{healthError && <><strong>Start lokalny</strong><p>Wykonaj instrukcję „Uruchomienie” w README. Pozostaw uruchomione dwa procesy: Python worker oraz aplikację Next.js.</p><code>http://127.0.0.1:8000/health</code><p>Następnie kliknij „Odśwież”.</p></>}</div>}
          </section>
          <a className="guide-link" href="https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes" target="_blank" rel="noreferrer">Przewodnik organizatorów <span>↗</span></a>
        </aside>

        <div className="results-column" aria-busy={Boolean(pending)}>
          {error && <div className="error-banner" role="alert"><strong>Nie udało się ukończyć operacji</strong><p>{error}</p></div>}
          {pending && <div className="progress-banner" role="status"><span className="loading-dot" />{pending === "run" ? "Zbieranie raportów i ocena agentów. W trybie live może to potrwać kilka minut." : pending === "restore" ? "Sprawdzanie workera i przywracanie ostatniej rundy…" : "Operacja trwa. Poczekaj na potwierdzenie."}</div>}
          {!run ? <section className="panel empty-state"><div className="radar"><div className="radar-ring" /><div className="radar-ring inner" /><Orbit /><span className="radar-dot" /></div><span className="eyebrow">GOTOWOŚĆ DO ODBIORU</span><h2>Każdy sygnał ma znaczenie.</h2><p>Uruchom pierwszą rundę, aby zobaczyć raporty<br className="desktop-break" /> sektorów, ocenę agentów i rekomendowaną akcję.</p><div className="empty-steps"><span>01 <b>Scenariusz</b></span><i>→</i><span>02 <b>Agenci</b></span><i>→</i><span>03 <b>Decyzja</b></span></div></section> : <>
            <section className="panel report-panel"><div className="report-heading"><div><span className="eyebrow">02 / SYTUACJA W PLACÓWCE</span><h2>{run.tick.facility_id}</h2></div><div className="run-meta"><span className={`mode-pill ${run.mode}`}>{run.mode === "demo" ? "DEMO" : "LIVE"}</span><span>TICK {text(run.tick.tick_id)}</span></div></div><div className="sectors">{run.tick.sector_reports.map((sector, index) => <article className="sector-card" key={`${sector.sector}-${index}`}><div className="sector-title"><span className="sector-icon">▧</span><h3>{sector.sector}</h3><span className="tiny-index">{String(index + 1).padStart(2, "0")}</span></div><dl><div><dt>Sensory</dt><dd>{sensorText(sector.sensors)}</dd></div><div><dt>Obserwacja</dt><dd>{text(sector.sighting)}</dd></div><div><dt>Cywile</dt><dd>{text(sector.civilian_status)}</dd></div><div><dt>Zabezpieczenie</dt><dd>{text(sector.containment_state)}</dd></div></dl></article>)}</div><div className="report-footer"><span>Budżet roju: {budgetText(run.tick.swarm_budget)}</span><span>{new Date(run.created_at).toLocaleString("pl-PL")}</span></div></section>
            <section className="panel agents-panel"><div className="section-heading"><h2>Głosy agentów</h2><span className="eyebrow">{run.agents.length} RAPORTY</span></div><div className="agents">{run.agents.map((agent, index) => <article className="agent" key={`${agent.role}-${index}`}><div className={`agent-avatar avatar-${index % 3}`}>{String(index + 1).padStart(2, "0")}</div><div><h3>{agent.role}</h3><p>{agent.summary}</p></div></article>)}</div></section>
            <section className={`panel decision-panel decision-${run.decision.action}`}><span className="eyebrow">03 / REKOMENDOWANA DECYZJA</span><div className="decision-title"><h2>{actionLabels[run.decision.action] ?? run.decision.action}</h2><span aria-hidden="true">↗</span></div><p>{run.decision.rationale}</p><ul className="evidence">{run.decision.evidence.map((item, index) => <li key={index}>{item}</li>)}</ul><div className="decision-actions"><button className="button secondary" disabled={Boolean(pending) || run.submission.status !== "ready"} onClick={() => void perform("submit")}>{pending === "submit" ? "Zgłaszanie…" : run.mode === "demo" ? "Testuj zgłoszenie" : "Zgłoś wynik do scenario MCP"}</button><button className="button secondary" disabled={Boolean(pending) || run.dispatch.status !== "ready"} onClick={() => void perform("dispatch")}>{pending === "dispatch" ? "Wysyłanie…" : run.mode === "demo" ? "Testuj Discord" : "Wyślij na Discord"}</button></div><p className="microcopy">{run.mode === "demo" ? "Akcje demo zapisują wyłącznie lokalny status. Nie wysyłają danych na Discord ani do scenario MCP." : "Każdy przycisk wykonuje osobną operację w zewnętrznej usłudze."}</p></section>
            <section className="panel activity-panel"><div className="section-heading"><h2>Historia tej rundy</h2><button className="text-button" disabled={Boolean(pending)} onClick={() => void perform("refresh")}>Odśwież ↻</button></div><div className="activity-row"><span className="activity-icon">✓</span><div><strong>Analiza zakończona</strong><p>Runda {run.id}</p></div></div><div className="activity-row"><span className="activity-icon">↗</span><div><strong>Scenario MCP · {run.submission.status}</strong><p>{run.submission.detail || "Wynik czeka na Twoją akcję."}</p></div></div><div className="activity-row"><span className="activity-icon">#</span><div><strong>Discord · {run.dispatch.status}</strong><p>{run.dispatch.detail || "Komunikat czeka na Twoją akcję."}</p></div></div></section>
          </>}
          <section className="panel scoreboard-panel"><div><span className="eyebrow">SCENARIO MCP</span><h2>Tablica wyników</h2><p className="muted">Odczyt na żądanie z lokalnego workera.</p></div><button className="button compact" disabled={!health || Boolean(pending)} onClick={() => void perform("scoreboard")}>{pending === "scoreboard" ? "Pobieranie…" : "Pobierz wyniki ↗"}</button>{scoreboard !== null && <pre className="scoreboard-data">{JSON.stringify(scoreboard, null, 2)}</pre>}</section>
        </div>
      </div>
    </main>
    <footer><span>AMONG AGENTS <span className="footer-divider">/</span> HALLOWEEN HACK 2026</span><span>Next.js + CrewAI <span className="footer-dot">●</span> Uruchomione lokalnie</span></footer>
  </div>;
}
