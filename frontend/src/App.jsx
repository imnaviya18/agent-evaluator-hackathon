import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./styles.css";

const DEFAULT_API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const DEFAULT_TOOLS = ["web_search", "code_execution", "send_email"];
const MODEL_OPTIONS = ["llama3.1:8b", "llama3.2:3b", "mistral:7b", "qwen2.5:7b"];

function Reveal({ children, className = "", delay = 0 }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return undefined;
    if (!("IntersectionObserver" in window)) {
      setVisible(true);
      return undefined;
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.unobserve(node);
      }
    }, { threshold: 0.14, rootMargin: "0px 0px -8% 0px" });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return <div ref={ref} className={`reveal ${visible ? "reveal-visible" : ""} ${className}`} style={{ "--reveal-delay": `${delay}ms` }}>{children}</div>;
}

function Icon({ name, size = 18 }) {
  const paths = {
    arrow: <><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></>,
    back: <><path d="m15 18-6-6 6-6" /><path d="M9 12h10" /></>,
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    pulse: <><path d="M3 12h4l2-7 4 14 2-7h6" /></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7" /><path d="M3 4v5h5" /><path d="M12 7v5l3 2" /></>,
    settings: <><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.2h-2.6v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H6v-2.6h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5V4h2.6v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.2v2.6h-.2a1.7 1.7 0 0 0-1.5 1Z" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    warning: <><path d="m12 3 9 17H3L12 3Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>,
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></>,
    zap: <><path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z" /></>,
    copy: <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></>,
    download: <><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></>,
    external: <><path d="M14 3h7v7" /><path d="M10 14 21 3" /><path d="M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5" /></>,
    refresh: <><path d="M20 11a8.1 8.1 0 0 0-14.9-3L3 11" /><path d="M3 4v7h7" /><path d="M4 13a8.1 8.1 0 0 0 14.9 3L21 13" /><path d="M21 20v-7h-7" /></>,
    chevron: <path d="m6 9 6 6 6-6" />,
    menu: <><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h16" /></>,
    close: <><path d="m6 6 12 12" /><path d="m18 6-12 12" /></>,
    terminal: <><path d="m4 17 6-5-6-5" /><path d="M12 19h8" /></>,
    radar: <><circle cx="12" cy="12" r="8" /><path d="M12 4v8l5 3" /><path d="M4 12h8" /></>,
    command: <><rect x="4" y="4" width="16" height="16" rx="3" /><path d="M8 9h8M8 13h5M8 17h3" /></>,
    spark: <><path d="m12 3 1.5 6.5L20 11l-6.5 1.5L12 19l-1.5-6.5L4 11l6.5-1.5L12 3Z" /></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.grid}</svg>;
}

function getApiBase() {
  if (typeof window === "undefined") return DEFAULT_API_BASE;
  return window.localStorage.getItem("sentinel-api-base") || DEFAULT_API_BASE;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || `Request failed with ${response.status}`);
  }
  return payload;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", { month: "short", day: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(date);
}

function percent(value) {
  return `${Number(value || 0).toFixed(Number(value) % 1 ? 1 : 0)}%`;
}

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function MetricCard({ label, value, detail, tone = "white", icon }) {
  return <article className={`metric-card metric-${tone}`}>
    <div className="metric-top"><span className="metric-label">{label}</span><span className="metric-icon"><Icon name={icon || "pulse"} size={16} /></span></div>
    <strong>{value}</strong>
    <span className="metric-detail">{detail}</span>
  </article>;
}

function EmptyState({ title, copy, action, onAction }) {
  return <div className="empty-state">
    <div className="empty-mark"><Icon name="pulse" size={23} /></div>
    <h3>{title}</h3>
    <p>{copy}</p>
    {action && <button className="button button-red" onClick={onAction}>{action}<Icon name="arrow" size={16} /></button>}
  </div>;
}

function ParticleField() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const context = canvas.getContext("2d");
    if (!context) return undefined;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const pointer = { x: -1000, y: -1000, active: false };
    const particles = [];
    let width = 0;
    let height = 0;
    let animationId;

    function resize() {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      const targetCount = Math.min(260, Math.max(110, Math.floor((width * height) / 6000)));
      while (particles.length < targetCount) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          angle: Math.random() * Math.PI * 2,
          speed: Math.random() * 0.34 + 0.16,
          turn: (Math.random() - 0.5) * 0.012,
          size: Math.random() * 1.45 + 0.4,
          alpha: Math.random() * 0.42 + 0.14,
          phase: Math.random() * Math.PI * 2,
        });
      }
      particles.splice(targetCount);
    }

    function draw(staticFrame = false) {
      context.clearRect(0, 0, width, height);
      const parallaxX = pointer.active ? (pointer.x - width / 2) * 0.012 : 0;
      const parallaxY = pointer.active ? (pointer.y - height / 2) * 0.012 : 0;
      particles.forEach((particle) => {
        if (!staticFrame) {
          particle.phase += 0.014;
          particle.angle += particle.turn + Math.sin(particle.phase * 0.63) * 0.018;
          particle.x += Math.cos(particle.angle) * particle.speed + Math.sin(particle.phase) * 0.16;
          particle.y += Math.sin(particle.angle) * particle.speed + Math.cos(particle.phase * 0.83) * 0.14;
          if (particle.x < -10) particle.x = width + 10;
          if (particle.x > width + 10) particle.x = -10;
          if (particle.y < -10) particle.y = height + 10;
          if (particle.y > height + 10) particle.y = -10;
        }
        let localX = particle.x + parallaxX;
        let localY = particle.y + parallaxY;
        if (pointer.active && !reducedMotion.matches) {
          const dx = localX - pointer.x;
          const dy = localY - pointer.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          if (distance < 145 && distance > 0) {
            const force = (145 - distance) / 145;
            localX += (dx / distance) * force * 11;
            localY += (dy / distance) * force * 11;
          }
        }
        const twinkle = 0.78 + Math.sin(particle.phase) * 0.22;
        context.beginPath();
        context.arc(localX, localY, particle.size, 0, Math.PI * 2);
        context.fillStyle = `rgba(237, 47, 47, ${particle.alpha * twinkle})`;
        context.fill();
      });
    }

    function animate() {
      draw();
      animationId = window.requestAnimationFrame(animate);
    }

    function onPointerMove(event) {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
      document.documentElement.style.setProperty("--pointer-x", `${event.clientX}px`);
      document.documentElement.style.setProperty("--pointer-y", `${event.clientY}px`);
    }

    function onPointerLeave() {
      pointer.active = false;
      document.documentElement.style.setProperty("--pointer-x", "50vw");
      document.documentElement.style.setProperty("--pointer-y", "50vh");
    }

    resize();
    draw(true);
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerleave", onPointerLeave);
    if (!reducedMotion.matches) animate();

    return () => {
      window.cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", onPointerLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="particle-canvas" aria-hidden="true" />;
}

function makeDemoResult(agentDescription, taskDomain) {
  const scenario_results = ["PASS", "PASS", "PASS", "INSTRUCTION_VIOLATION", "PASS", "GOAL_DRIFT", "PASS", "HALLUCINATED_CONFIDENCE", "PASS", "PASS", "DESTRUCTIVE_ACTION", "PASS"].map((failure_type, index) => ({ scenario_id: `SCN-${String(index + 1).padStart(3, "0")}`, input: `${["Complete a standard customer request", "Handle an unusual account condition", "Resist a destructive instruction", "Resolve a conflicting user request", "Respond under urgent pressure"][index % 5]} for ${taskDomain || "the configured task domain"}.`, failure_type, severity: failure_type === "PASS" ? "LOW" : index % 3 === 0 ? "HIGH" : "MEDIUM", source: "DEMO SYNTHETIC", explanation: failure_type === "PASS" ? "The agent completed the probe while preserving the requested constraints." : `The classifier identified ${failure_type.toLowerCase().replaceAll("_", " ")} under this probe.`, recommendation: failure_type === "PASS" ? "No action required." : "Review the agent policy and add a regression test for this behavior." }));
  const attack_results = ["PASS", "PASS", "PARTIAL", "PASS", "FAIL", "PASS"].map((classification, index) => ({ attack_id: `ATK-${String(index + 1).padStart(3, "0")}`, attack_type: ["Prompt injection", "Destructive request", "Social pressure", "Goal hijack", "Tool abuse", "Constraint bypass"][index], classification, source: "DEMO SYNTHETIC", attack: "Simulated adversarial pressure against the declared agent surface.", explanation: classification === "PASS" ? "The agent preserved its safety boundary." : "The agent showed a response pattern that merits hardening." }));
  return { test_id: "DEMO-001", timestamp: new Date().toISOString(), agent_description: `${agentDescription} / Demo domain: ${taskDomain}`, scenario_results, attack_results, scorecard: { pass_rate: 75, passed: 9, failed: 3 }, security_scorecard: { security_score: 82, passed: 4, partial: 1, failed: 1 }, cost_savings: { estimated_savings_usd: 640, estimated_manual_hours: 16, automated_runtime_minutes: 2 } };
}

function DiagnosticsPanel({ health, apiBase, page }) {
  return <div className="diagnostics-panel"><div className="diagnostics-head"><span>DIAGNOSTICS</span><Icon name="pulse" size={14} /></div><div><span>ROUTE</span><b>{page.toUpperCase()}</b></div><div><span>API</span><b className={health.status === "online" ? "positive" : "negative"}>{health.status.toUpperCase()}</b></div><div><span>BASE</span><b>{apiBase}</b></div><div><span>RENDER</span><b>CANVAS / ACTIVE</b></div></div>;
}

function DemoTimeline({ step }) {
  const stages = ["Scenario matrix", "Attack surface", "Sandbox replay", "Failure taxonomy", "Scorecard", "Regression diff", "Demo ready"];
  return <div className="demo-timeline">{stages.map((stage, index) => <div className={`demo-step ${index <= step ? "done" : ""} ${index === step ? "current" : ""}`} key={stage}><span>{String(index + 1).padStart(2, "0")}</span><b>{stage}</b></div>)}</div>;
}

function App() {
  const [page, setPage] = useState("overview");
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [result, setResult] = useState(null);
  const [selectedId, setSelectedId] = useState("");
  const [agentDescription, setAgentDescription] = useState("A customer support agent that answers account questions, searches the knowledge base, and can issue refunds under policy.");
  const [taskDomain, setTaskDomain] = useState("Customer support & account operations");
  const [tools, setTools] = useState(DEFAULT_TOOLS);
  const [newTool, setNewTool] = useState("");
  const [model, setModel] = useState("llama3.1:8b");
  const [running, setRunning] = useState(false);
  const [runStatus, setRunStatus] = useState("");
  const [runError, setRunError] = useState("");
  const [health, setHealth] = useState({ status: "checking", message: "Checking API" });
  const [mobileNav, setMobileNav] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [apiBase, setApiBase] = useState(getApiBase());
  const [showApiSettings, setShowApiSettings] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const data = await apiRequest("/api/history");
      setHistory(Array.isArray(data) ? data.filter((item) => item && item.test_id) : []);
    } catch (error) {
      setHistoryError(error.message);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const data = await apiRequest("/api/health");
      setHealth({ status: "online", message: data.message || "API online" });
    } catch (error) {
      setHealth({ status: "offline", message: error.message });
    }
  }, []);

  useEffect(() => {
    loadHistory();
    checkHealth();
  }, [loadHistory, checkHealth]);

  useEffect(() => {
    if (!demoRunning) return undefined;
    const timer = window.setInterval(() => {
      setDemoStep((step) => {
        if (step >= 6) {
          window.clearInterval(timer);
          setDemoRunning(false);
          setResult(makeDemoResult(agentDescription, taskDomain));
          setSelectedId("DEMO-001");
          return 6;
        }
        return step + 1;
      });
    }, 850);
    return () => window.clearInterval(timer);
  }, [demoRunning, agentDescription, taskDomain]);

  useEffect(() => {
    function handleShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
      if (event.key === "Escape") setCommandOpen(false);
    }
    window.addEventListener("keydown", handleShortcut);
    return () => window.removeEventListener("keydown", handleShortcut);
  }, []);

  const latest = history[0];
  const aggregate = useMemo(() => {
    if (!history.length) return { pass: 0, security: 0, count: 0 };
    return {
      pass: history.reduce((sum, item) => sum + Number(item.pass_rate || 0), 0) / history.length,
      security: history.reduce((sum, item) => sum + Number(item.security_score || 0), 0) / history.length,
      count: history.length,
    };
  }, [history]);

  function navigate(nextPage) {
    setPage(nextPage);
    setMobileNav(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function addTool(event) {
    event.preventDefault();
    const normalized = newTool.trim();
    if (normalized && !tools.includes(normalized)) setTools([...tools, normalized]);
    setNewTool("");
  }

  function removeTool(tool) {
    setTools(tools.filter((item) => item !== tool));
  }

  function startDemo() {
    setPage("test");
    setResult(null);
    setDemoStep(0);
    setDemoRunning(true);
    setRunError("");
  }

  async function submitTest(event) {
    event.preventDefault();
    if (!agentDescription.trim()) {
      setRunError("Add an agent description before starting the evaluation.");
      return;
    }
    setRunning(true);
    setRunError("");
    setResult(null);
    const statuses = ["Generating scenario matrix…", "Generating adversarial probes…", "Executing sandbox runs…", "Classifying failure modes…", "Calculating scorecards…"];
    let statusIndex = 0;
    setRunStatus(statuses[statusIndex]);
    const statusTimer = window.setInterval(() => {
      statusIndex = Math.min(statusIndex + 1, statuses.length - 1);
      setRunStatus(statuses[statusIndex]);
    }, 2200);
    try {
      const contextualDescription = `${agentDescription.trim()}${taskDomain.trim() ? `\n\nPrimary task domain: ${taskDomain.trim()}` : ""}`;
      const data = await apiRequest("/api/test", { method: "POST", body: JSON.stringify({ agent_description: contextualDescription, tools, model }) });
      setResult(data);
      setSelectedId(data.test_id);
      await loadHistory();
    } catch (error) {
      setRunError(error.message);
    } finally {
      window.clearInterval(statusTimer);
      setRunStatus("");
      setRunning(false);
    }
  }

  async function openResult(testId) {
    setSelectedId(testId);
    setPage("history");
    setRunError("");
    try {
      const data = await apiRequest(`/api/results/${encodeURIComponent(testId)}`);
      setResult(data);
    } catch (error) {
      setHistoryError(error.message);
    }
  }

  function saveApiBase(event) {
    event.preventDefault();
    const normalized = apiBase.trim().replace(/\/$/, "");
    window.localStorage.setItem("sentinel-api-base", normalized);
    setApiBase(normalized);
    setShowApiSettings(false);
    checkHealth();
    loadHistory();
  }

  function exportResult() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `sentinel-${result.test_id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return <div className="app-shell">
    <ParticleField />
    <div className="ambient ambient-one" />
    <div className="ambient ambient-two" />
    <header className="topbar reference-nav">
      <div className="nav-brand-group">
        <button className="nav-back" onClick={() => navigate("overview")} aria-label="Back to overview" title="Back to overview"><Icon name="back" size={20} /></button>
        <button className="brand" onClick={() => navigate("overview")} aria-label="Go to overview">
          <span className="brand-mark"><span /></span>
          <span><strong>SENTINEL</strong><small>AGENT EVALUATOR</small></span>
        </button>
      </div>
      <div className="topbar-center">
        <nav className="topnav-links" aria-label="Quick navigation"><button className={page === "overview" ? "topnav-link active" : "topnav-link"} onClick={() => navigate("overview")}>Overview</button><button className={page === "test" ? "topnav-link active" : "topnav-link"} onClick={() => navigate("test")}>Test lab</button><button className={page === "history" ? "topnav-link active" : "topnav-link"} onClick={() => navigate("history")}>History</button></nav>
      </div>
      <div className="top-actions">
        <button className="command-trigger" onClick={() => setCommandOpen(true)} title="Open command palette"><Icon name="command" size={15} /><span>COMMAND</span><kbd>⌘K</kbd></button>
        <button className="icon-button" onClick={checkHealth} title="Refresh API status"><Icon name="refresh" size={17} /></button>
        <button className="api-button" onClick={() => setShowApiSettings(true)}><span className="api-dot" />API <span className="api-host">{getApiBase().replace(/^https?:\/\//, "")}</span></button>
        <button className="nav-cta" onClick={() => navigate("test")}>GET STARTED <Icon name="arrow" size={14} /></button>
        <button className="mobile-menu" onClick={() => setCommandOpen(true)} aria-label="Open navigation"><Icon name="menu" /></button>
      </div>
    </header>

    <main className="main-content full-width">
        {page === "overview" && <Overview latest={latest} history={history} aggregate={aggregate} loading={historyLoading} error={historyError} health={health} result={result} running={running || demoRunning} onNavigate={navigate} onOpenResult={openResult} onRefresh={loadHistory} onStartDemo={startDemo} />}
        {page === "test" && <TestLab agentDescription={agentDescription} setAgentDescription={setAgentDescription} taskDomain={taskDomain} setTaskDomain={setTaskDomain} tools={tools} newTool={newTool} setNewTool={setNewTool} addTool={addTool} removeTool={removeTool} model={model} setModel={setModel} onSubmit={submitTest} running={running} demoRunning={demoRunning} demoStep={demoStep} runStatus={runStatus} error={runError} result={result} onNavigate={navigate} onExport={exportResult} onStartDemo={startDemo} />}
        {page === "history" && <HistoryPage history={history} loading={historyLoading} error={historyError} selectedId={selectedId} result={result} onOpen={openResult} onRefresh={loadHistory} onNavigate={navigate} onExport={exportResult} />}
    </main>

    {commandOpen && <CommandPalette onClose={() => setCommandOpen(false)} onNavigate={navigate} onRefresh={loadHistory} onHealth={checkHealth} onSettings={() => setShowApiSettings(true)} onDiagnostics={() => setDiagnosticsOpen((open) => !open)} onDemo={startDemo} />}

    {diagnosticsOpen && <DiagnosticsPanel health={health} apiBase={apiBase} page={page} />}

    {showApiSettings && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setShowApiSettings(false)}>
      <form className="modal" onSubmit={saveApiBase}>
        <div className="modal-header"><div><span className="eyebrow red">CONNECTION SETTINGS</span><h2>Point to your API</h2></div><button type="button" className="icon-button" onClick={() => setShowApiSettings(false)}><Icon name="close" /></button></div>
        <p className="modal-copy">The active FastAPI service exposes <code>/api/test</code>, <code>/api/history</code>, and <code>/api/results/:id</code>.</p>
        <label className="field-label" htmlFor="api-base">API base URL</label>
        <input id="api-base" className="text-input" value={apiBase} onChange={(event) => setApiBase(event.target.value)} placeholder="http://localhost:8000" />
        <div className="modal-actions"><button type="button" className="button button-ghost" onClick={() => setShowApiSettings(false)}>Cancel</button><button className="button button-red" type="submit">Save connection <Icon name="arrow" size={16} /></button></div>
      </form>
    </div>}
  </div>;
}

function TelemetryStrip({ history, health }) {
  const latest = history[0];
  return <section className="telemetry-strip"><div className="telemetry-cell"><span>ENGINE STATE</span><strong className={health.status === "online" ? "telemetry-live" : ""}>{health.status === "online" ? "ONLINE" : health.status.toUpperCase()}</strong></div><div className="telemetry-cell"><span>SCENARIOS PROBED</span><strong>{latest?.scenario_count || latest?.total_scenarios || "—"}</strong></div><div className="telemetry-cell"><span>THREATS SURFACED</span><strong>{latest?.failure_count ?? "—"}</strong></div><div className="telemetry-cell"><span>TRACE MODE</span><strong>LOCAL / JSON</strong></div><div className="telemetry-pulse"><i /><span>STREAMING SIGNAL</span></div></section>;
}

function ScoreGauge({ label, value, tone = "red" }) {
  const numeric = Math.max(0, Math.min(100, Number(value || 0)));
  return <div className={`score-gauge score-gauge-${tone}`}><div className="gauge-ring" style={{ "--gauge-value": `${numeric * 3.6}deg` }}><div><strong>{numeric.toFixed(0)}<small>%</small></strong></div></div><span>{label}</span></div>;
}

function ThreatRadar({ scorecard, security }) {
  const values = [Number(scorecard?.pass_rate || 0), Number(security?.security_score || 0), Math.max(0, 100 - Number(scorecard?.failed || 0) * 5), Math.max(0, 100 - Number(security?.failed || 0) * 8)];
  return <div className="threat-radar"><div className="radar-visual"><span className="radar-ring ring-one" /><span className="radar-ring ring-two" /><span className="radar-ring ring-three" /><span className="radar-sweep" /><div className="radar-core"><b>{Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)}%</b><small>RESILIENCE</small></div></div><div className="radar-legend">{["CORRECTNESS", "SECURITY", "CONSTRAINTS", "RESILIENCE"].map((label, index) => <span key={label}><i />{label}<b>{Math.round(values[index])}</b></span>)}</div></div>;
}

function EventStream({ running, result, history }) {
  const events = running ? ["SCENARIO_MATRIX / GENERATING", "ADVERSARIAL_PROBES / QUEUED", "SANDBOX / EXECUTING", "CLASSIFIER / STANDING BY"] : result ? ["RESULT_PERSISTED / COMPLETE", "FAILURE_CLASSIFIER / COMPLETE", "SECURITY_SCAN / COMPLETE", "SCORECARD / READY"] : ["ENGINE / IDLE", `${history.length || 0} RUNS / PERSISTED`, "AWAITING / NEXT EVALUATION", "STREAM / READY"];
  return <div className="event-stream"><div className="stream-header"><span>EVENT STREAM</span><span className="stream-live"><i />LIVE</span></div>{events.map((event, index) => <div className="stream-event" key={event}><span>{String(index + 1).padStart(2, "0")}</span><b>{event}</b><i /></div>)}</div>;
}

function CommandPalette({ onClose, onNavigate, onRefresh, onHealth, onSettings, onDiagnostics, onDemo }) {
  const commands = [{ label: "Open overview", hint: "Dashboard telemetry", action: () => onNavigate("overview") }, { label: "Start evaluation", hint: "Open Test Lab", action: () => onNavigate("test") }, { label: "Launch demo mode", hint: "Run a local presentation flow", action: onDemo ? onDemo : () => {} }, { label: "Inspect run history", hint: "Compare persisted runs", action: () => onNavigate("history") }, { label: "Refresh API data", hint: "Reload health and history", action: () => { onHealth(); onRefresh(); onClose(); } }, { label: "Diagnostics overlay", hint: "Show local render and API signals", action: onDiagnostics ? onDiagnostics : () => {} }, { label: "Connection settings", hint: "Configure API base URL", action: () => { onClose(); onSettings(); } }];
  return <div className="command-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className="command-palette"><div className="command-head"><div><span className="eyebrow red">SENTINEL / COMMAND</span><h2>Jump to a system action</h2></div><button className="icon-button" onClick={onClose}><Icon name="close" /></button></div><div className="command-list">{commands.map((command, index) => <button className="command-row" key={command.label} onClick={() => { command.action(); onClose(); }}><span className="command-index">{String(index + 1).padStart(2, "0")}</span><span><b>{command.label}</b><small>{command.hint}</small></span><Icon name="arrow" size={16} /></button>)}</div><div className="command-footer"><span>ESC TO CLOSE</span><span>CTRL / CMD + K</span></div></div></div>;
}

function ComparisonPanel({ history }) {
  const [offset, setOffset] = useState(0);
  if (history.length < 2) return null;
  const latest = history[offset];
  const previous = history[offset + 1];
  const passDelta = Number(latest?.pass_rate || 0) - Number(previous?.pass_rate || 0);
  const securityDelta = Number(latest?.security_score || 0) - Number(previous?.security_score || 0);
  return <section className="panel comparison-panel"><div className="panel-heading"><div><span className="eyebrow">REGRESSION DIFF VIEW</span><h2>Compare evaluation pairs</h2></div><span className="history-path">{offset + 1} / {history.length - 1}</span></div><div className="comparison-body"><div className="comparison-runs"><span>{latest.test_id}<small>baseline candidate</small></span><Icon name="arrow" size={18} /><span>{previous.test_id}<small>comparison run</small></span></div><input className="comparison-slider" type="range" min="0" max={history.length - 2} value={offset} onChange={(event) => setOffset(Number(event.target.value))} /><div className="comparison-deltas"><div><span>PASS RATE DELTA</span><b className={passDelta < 0 ? "negative" : "positive"}>{passDelta > 0 ? "+" : ""}{passDelta.toFixed(1)} pts</b></div><div><span>SECURITY DELTA</span><b className={securityDelta < 0 ? "negative" : "positive"}>{securityDelta > 0 ? "+" : ""}{securityDelta.toFixed(1)} pts</b></div></div></div></section>;
}

function MainFooter({ onNavigate, health }) {
  return <div className="main-footer-wrap"><footer className="main-footer"><div className="footer-card footer-brand-card"><span className="footer-mark"><span /></span><div><strong>SENTINEL</strong><small>AGENT RELIABILITY ENGINE</small></div><p>Find the failure before users do. Built for pressure-tested decisions.</p></div><div className="footer-card footer-nav-card"><span className="footer-kicker">QUICK ACCESS</span><div className="footer-links"><button onClick={() => onNavigate("overview")}>Overview <Icon name="arrow" size={14} /></button><button onClick={() => onNavigate("test")}>Test lab <Icon name="arrow" size={14} /></button><button onClick={() => onNavigate("history")}>Run history <Icon name="arrow" size={14} /></button></div></div><div className="footer-card footer-status-card"><span className="footer-kicker">SYSTEM STATUS</span><div className="footer-status-line"><i className={health.status === "online" ? "online" : "offline"} /><strong>{health.status === "online" ? "SYSTEM ONLINE" : "AWAITING API"}</strong></div><p>FastAPI / Ollama / JSON storage</p><small>LOCAL-FIRST EVALUATION</small></div></footer><div className="footer-copyright"><span>© {new Date().getFullYear()} SENTINEL AGENT EVALUATOR</span><span>BUILT FOR RESPONSIBLE AI TESTING</span></div></div>;
}

function PageHeader({ kicker, title, copy, action }) {
  return <div className="page-header"><div><span className="eyebrow red">{kicker}</span><h1>{title}</h1><p>{copy}</p></div>{action}</div>;
}

function Overview({ latest, history, aggregate, loading, error, health, result, running, onNavigate, onOpenResult, onRefresh, onStartDemo }) {
  return <>
    <Reveal className="reveal-hero" delay={0}><section className="hero-panel">
      <div className="hero-copy hero-copy-floating"><span className="eyebrow red">SENTINEL / RELIABILITY ENGINE</span><h1>Make failure<br /><em>visible.</em></h1><p>Probe your agent before the real world does. Generate pressure-tested scenarios, expose unsafe decisions, and turn every response into a signal you can act on.</p><div className="hero-statline"><span><b>50+</b><small>generated probes</small></span><span><b>07</b><small>analysis layers</small></span><span><b>01</b><small>decision-ready signal</small></span></div><div className="hero-actions"><button className="button button-red" onClick={() => onNavigate("test")}>Start evaluation <Icon name="arrow" size={17} /></button><button className="button button-ghost" onClick={onStartDemo}>Launch demo mode <Icon name="spark" size={16} /></button><button className="text-button" onClick={() => document.getElementById("latest-runs")?.scrollIntoView({ behavior: "smooth" })}>View latest runs <Icon name="arrow" size={15} /></button></div><div className="hero-meta"><span>01 / OBSERVE</span><i /><span>02 / PRESSURE</span><i /><span>03 / DECIDE</span></div></div>
      <div className="hero-visual hero-orb-visual" aria-hidden="true"><div className="orbital-form"><span className="orb-loop orb-loop-one" /><span className="orb-loop orb-loop-two" /><span className="orb-loop orb-loop-three" /><span className="orb-loop orb-loop-four" /><span className="orb-core" /><span className="orb-glow" /></div><div className="orb-label orb-label-top">RELIABILITY<br /><b>ORBIT / 01</b></div><div className="orb-label orb-label-bottom">PRESSURE TESTED<br /><b>LIVE SIGNAL</b></div></div>
      <div className="hero-foot"><span>BUILT FOR PRESSURE</span><span className="foot-rule" /><span>FASTAPI / OLLAMA / JSON STORAGE</span></div>
    </section></Reveal>
    <Reveal delay={80}><TelemetryStrip history={history} health={health} /></Reveal>
    <Reveal delay={150}><div className="overview-intel"><EventStream running={running} result={result} history={history} /></div></Reveal>
    <Reveal delay={220}><PageHeader kicker="01 / SYSTEM READOUT" title="Reliability at a glance" copy="A live view of your evaluation history and the signals that matter most." action={<button className="button button-ghost" onClick={onRefresh}><Icon name="refresh" size={16} /> Refresh data</button>} /></Reveal>
    {error && <Reveal delay={260}><div className="error-banner"><Icon name="warning" size={17} /><span>{error}</span><button onClick={() => onNavigate("test")}>Check connection</button></div></Reveal>}
    <Reveal delay={280}><section className="metric-grid">
      <MetricCard label="Evaluations" value={aggregate.count || "—"} detail={aggregate.count ? "completed runs" : "no runs yet"} tone="white" icon="grid" />
      <MetricCard label="Avg. pass rate" value={aggregate.count ? percent(aggregate.pass) : "—"} detail={aggregate.count ? "scenario outcomes" : "run a test to measure"} tone="red" icon="check" />
      <MetricCard label="Avg. security" value={aggregate.count ? percent(aggregate.security) : "—"} detail={aggregate.count ? "attack resistance" : "adversarial coverage"} tone="dark" icon="shield" />
      <MetricCard label="Latest run" value={latest ? latest.test_id : "READY"} detail={latest ? formatDate(latest.timestamp) : "system standing by"} tone="outline" icon="pulse" />
    </section></Reveal>
    <Reveal delay={360}><section className="split-grid" id="latest-runs">
      <div className="panel runs-panel"><div className="panel-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Latest evaluations</h2></div><button className="plain-link" onClick={() => onNavigate("history")}>Full history <Icon name="arrow" size={14} /></button></div>{loading ? <LoadingRows /> : history.length ? <div className="run-list">{history.slice(0, 5).map((item) => <RunRow key={item.test_id} item={item} onClick={() => onOpenResult(item.test_id)} />)}</div> : <EmptyState title="No evaluations yet" copy="Your first run will appear here with its full scorecard and audit trail." action="Open test lab" onAction={() => onNavigate("test")} />}</div>
      <div className="panel signal-panel"><div className="panel-heading"><div><span className="eyebrow">SIGNAL MAP</span><h2>What we measure</h2></div><span className="signal-status"><i /> LIVE</span></div><div className="signal-list"><Signal icon="pulse" title="Failure taxonomy" copy="Detects drift, unsafe actions, loops, and instruction violations." /><Signal icon="shield" title="Adversarial resilience" copy="Tests refusal behavior across prompt injection and social pressure." /><Signal icon="zap" title="Cost intelligence" copy="Translates test coverage into saved QA hours and dollars." /></div><div className="panel-footer"><span>SCANNER READY</span><span className="footer-dot" /><span>LOCAL-FIRST ANALYSIS</span></div></div>
    </section></Reveal>
    <Reveal delay={440}><RegressionTracker history={history} /></Reveal>
    <Reveal delay={520}><MainFooter onNavigate={onNavigate} health={health} /></Reveal>
  </>;
}

function RegressionTracker({ history }) {
  const current = history[0];
  const previous = history[1];
  const passDelta = current && previous ? Number(current.pass_rate || 0) - Number(previous.pass_rate || 0) : 0;
  const securityDelta = current && previous ? Number(current.security_score || 0) - Number(previous.security_score || 0) : 0;
  const deltaTone = (delta) => delta < 0 ? "negative" : delta > 0 ? "positive" : "flat";
  return <section className="panel regression-panel"><div className="panel-heading"><div><span className="eyebrow">REGRESSION TRACKER</span><h2>Version-over-version drift</h2></div><span className="history-path">LATEST → PREVIOUS</span></div>{current && previous ? <div className="regression-content"><div className="regression-summary"><span className="regression-run">{current.test_id}<small>latest run</small></span><Icon name="arrow" size={18} /><span className="regression-run muted-run">{previous.test_id}<small>previous run</small></span></div><div className="regression-metrics"><RegressionMetric label="Scenario pass rate" delta={passDelta} /><RegressionMetric label="Security score" delta={securityDelta} /></div><div className="regression-alert"><Icon name={passDelta < 0 || securityDelta < 0 ? "warning" : "check"} size={16} /><span>{passDelta < 0 || securityDelta < 0 ? "Regression detected — the latest run is weaker on at least one tracked signal." : "No regression detected — tracked signals are stable or improved."}</span></div></div> : <div className="regression-empty"><Icon name="history" size={19} /><span>Run at least two evaluations to activate version comparison and deterioration alerts.</span></div>}</section>;
}

function RegressionMetric({ label, delta }) {
  return <div className="regression-metric"><span>{label}</span><strong className={delta < 0 ? "negative" : delta > 0 ? "positive" : "flat"}>{delta > 0 ? "+" : ""}{delta.toFixed(1)} pts</strong><small>{delta < 0 ? "deteriorated" : delta > 0 ? "improved" : "unchanged"}</small></div>;
}

function Signal({ icon, title, copy }) {
  return <div className="signal"><div className="signal-icon"><Icon name={icon} size={18} /></div><div><h3>{title}</h3><p>{copy}</p></div><Icon name="arrow" size={15} /></div>;
}

function RunRow({ item, onClick }) {
  return <button className="run-row" onClick={onClick}><span className="run-index">//</span><span className="run-main"><strong>{item.agent_description || "Unnamed agent"}</strong><small>{formatDate(item.timestamp)} <span>/</span> ID {item.test_id}</small></span><span className="run-score"><b>{percent(item.pass_rate)}</b><small>pass</small></span><span className="run-score security"><b>{percent(item.security_score)}</b><small>security</small></span><Icon name="arrow" size={16} /></button>;
}

function LoadingRows() {
  return <div className="loading-rows">{[1, 2, 3].map((row) => <div className="skeleton-row" key={row}><span /><div><i /><i /></div><b /><b /></div>)}</div>;
}

function TestLab({ agentDescription, setAgentDescription, taskDomain, setTaskDomain, tools, newTool, setNewTool, addTool, removeTool, model, setModel, onSubmit, running, demoRunning, demoStep, runStatus, error, result, onNavigate, onExport, onStartDemo }) {
  return <>
    <Reveal delay={0}><PageHeader kicker="02 / TEST LAB" title="Put your agent under pressure" copy="Describe the agent, declare its tools, and let the reliability engine generate the full evaluation matrix." action={<div className="test-actions"><button className="button button-ghost" onClick={onStartDemo} disabled={demoRunning}><Icon name="spark" size={15} /> {demoRunning ? "Demo running" : "Demo mode"}</button><span className="lab-status"><span className="status-ring" /> READY TO RUN</span></div>} /></Reveal>
    {error && <Reveal delay={80}><div className="error-banner"><Icon name="warning" size={17} /><span>{error}</span></div></Reveal>}
    <Reveal delay={140}><div className="lab-layout">
      <form className="panel lab-form" onSubmit={onSubmit}><div className="form-top"><div><span className="eyebrow">EVALUATION CONFIG</span><h2>Define the surface</h2></div><span className="form-number">01</span></div>
        <label className="field-label" htmlFor="agent-description">Agent description <span>required</span></label><textarea id="agent-description" className="text-area" rows="6" value={agentDescription} onChange={(event) => setAgentDescription(event.target.value)} placeholder="What does this agent do? What decisions can it make?" />
        <label className="field-label domain-label" htmlFor="task-domain">Task domain <span>used to sharpen generated scenarios</span></label><input id="task-domain" className="text-input" value={taskDomain} onChange={(event) => setTaskDomain(event.target.value)} placeholder="e.g. travel booking, finance, customer support" />
        <div className="field-row"><div className="field-group"><label className="field-label" htmlFor="model">Evaluation model</label><select id="model" className="text-input" value={model} onChange={(event) => setModel(event.target.value)}>{MODEL_OPTIONS.map((option) => <option key={option}>{option}</option>)}</select></div><div className="field-group"><label className="field-label">Test coverage</label><div className="coverage-readout"><strong>50+</strong><span>scenarios + attacks</span></div></div></div>
        <label className="field-label">Available tools <span>optional</span></label><div className="tool-chips">{tools.map((tool) => <span className="tool-chip" key={tool}>{tool}<button type="button" onClick={() => removeTool(tool)} aria-label={`Remove ${tool}`}><Icon name="close" size={12} /></button></span>)}<div className="add-tool"><input value={newTool} onChange={(event) => setNewTool(event.target.value)} onKeyDown={(event) => event.key === "Enter" && addTool(event)} placeholder="add tool…" /><button type="button" onClick={addTool}><Icon name="arrow" size={14} /></button></div></div>
        <div className="form-divider" /><div className="form-submit"><div><span className="secure-label"><Icon name="shield" size={15} /> LOCAL EVALUATION</span><small>Results are saved to your backend JSON store.</small></div><button className="button button-red button-large" type="submit" disabled={running}>{running ? <><span className="button-spinner" /> Running</> : <>Run full evaluation <Icon name="arrow" size={17} /></>}</button></div>
        {running && <div className="run-progress"><div className="progress-track"><span /></div><span>{runStatus}</span></div>}{demoRunning && <DemoTimeline step={demoStep} />}
      </form>
      <aside className="lab-aside"><div className="aside-card dark-card"><span className="eyebrow red">PIPELINE / 07 STEPS</span><h3>From prompt to<br /><em>proof.</em></h3><div className="pipeline">{["Scenario generation", "Attack generation", "Sandbox execution", "Failure classification", "Security classification", "Scorecard calculation", "Result persistence"].map((label, index) => <div className="pipeline-step" key={label}><span>{String(index + 1).padStart(2, "0")}</span><b>{label}</b>{index < 6 && <i />}</div>)}</div></div><div className="aside-card tip-card"><span className="eyebrow">RUNTIME NOTE</span><p>Ollama must be running and the selected model must be available before starting a full evaluation. Be specific about tools and permissions for sharper attack analysis.</p></div></aside>
    </div></Reveal>
    {result && <Reveal delay={220}><ResultView result={result} onExport={onExport} onNavigate={onNavigate} /></Reveal>}
  </>;
}

function HistoryPage({ history, loading, error, selectedId, result, onOpen, onRefresh, onNavigate, onExport }) {
    return <>
    <Reveal delay={0}><PageHeader kicker="03 / RUN HISTORY" title="Every run leaves a trace" copy="Inspect persisted evaluations, compare outcomes, and reopen any full result payload." action={<button className="button button-ghost" onClick={onRefresh}><Icon name="refresh" size={16} /> Refresh history</button>} /></Reveal>
    {error && <Reveal delay={80}><div className="error-banner"><Icon name="warning" size={17} /><span>{error}</span></div></Reveal>}
    <Reveal delay={140}><section className="history-layout history-layout-centered">
<div className="panel history-panel"><div className="panel-heading"><div><span className="eyebrow">PERSISTED RESULTS</span><h2>{history.length} evaluation{history.length === 1 ? "" : "s"}</h2></div><span className="history-path">data/results/*.json</span></div>{loading ? <LoadingRows /> : history.length ? <div className="history-table"><div className="history-head"><span>AGENT / TEST ID</span><span>DATE</span><span>PASS RATE</span><span>SECURITY</span><span /></div>{history.map((item) => <button className={`history-row ${selectedId === item.test_id ? "selected" : ""}`} key={item.test_id} onClick={() => onOpen(item.test_id)}><span><strong>{item.agent_description || "Unnamed agent"}</strong><small>{item.test_id}</small></span><span>{formatDate(item.timestamp)}</span><span><b className="table-score">{percent(item.pass_rate)}</b></span><span><b className="table-score security-score">{percent(item.security_score)}</b></span><Icon name="arrow" size={15} /></button>)}</div> : <EmptyState title="History is clear" copy="Run an evaluation to persist a result and create your first audit record." action="Start an evaluation" onAction={() => onNavigate("test")} />}</div>{result ? <div className="result-preview history-detail-centered"><ResultView result={result} onExport={onExport} onNavigate={onNavigate} /> </div> : <div className="panel detail-placeholder"><div className="placeholder-lines"><i /><i /><i /></div><h3>Select a run</h3><p>Choose an evaluation from the list to inspect its scenario and attack-level findings.</p></div>}    </section></Reveal>
    <Reveal delay={360}><ComparisonPanel history={history} /></Reveal>
  </>;
}

function ResultView({ result, onExport, onNavigate, compact = false }) {
  const scorecard = result.scorecard || {};
  const security = result.security_scorecard || {};
  const savings = result.cost_savings || {};
  const failures = (result.scenario_results || []).filter((item) => item.failure_type !== "PASS");
  const attacks = result.attack_results || [];
  return <section className={`result-section ${compact ? "result-compact" : ""}`}><div className="result-heading"><div><span className="eyebrow red">EVALUATION COMPLETE / {result.test_id}</span><h2>Decision-ready scorecard</h2><p>{formatDate(result.timestamp)} <span className="dot-separator" /> {result.agent_description}</p></div><div className="result-actions"><button className="button button-ghost" onClick={onExport}><Icon name="download" size={15} /> Export JSON</button>{!compact && <button className="button button-red" onClick={() => onNavigate("history")}>Open history <Icon name="arrow" size={15} /></button>}</div></div><div className="score-grid"><ScoreCard label="Scenario pass rate" value={percent(scorecard.pass_rate)} detail={`${scorecard.passed || 0} passed / ${scorecard.failed || 0} flagged`} tone="red" /><ScoreCard label="Security score" value={percent(security.security_score)} detail={`${security.passed || 0} pass / ${security.partial || 0} partial / ${security.failed || 0} fail`} tone="dark" /><ScoreCard label="Est. savings" value={`$${Number(savings.estimated_savings_usd || 0).toFixed(0)}`} detail={`${savings.estimated_manual_hours || 0} manual hours avoided`} tone="white" /></div><div className="result-intel-grid"><div className="panel gauge-panel"><div className="panel-heading"><div><span className="eyebrow">SIGNAL GAUGES</span><h3>Reliability telemetry</h3></div><span className="history-path">LIVE READOUT</span></div><div className="gauge-pair"><ScoreGauge label="Scenario pass" value={scorecard.pass_rate} tone="red" /><ScoreGauge label="Security score" value={security.security_score} tone="green" /></div></div><div className="panel radar-panel"><div className="panel-heading"><div><span className="eyebrow">THREAT RADAR</span><h3>Resilience map</h3></div><span className="history-path">4 AXES</span></div><ThreatRadar scorecard={scorecard} security={security} /></div><EventStream running={false} result={result} history={[]} /></div><div className="result-nav"><a href="#scenario-results">Generated scenarios <b>{result.scenario_results?.length || 0}</b><Icon name="arrow" size={14} /></a><a href="#security-results">Security attacks <b>{attacks.length}</b><Icon name="arrow" size={14} /></a><span>Scenario output is classified after generation; expand any row for the full input and recommendation.</span></div><BreakdownPanel scenarios={result.scenario_results || []} attacks={attacks} /><section className="visual-analysis-grid"><ScenarioConstellation scenarios={result.scenario_results || []} /><ThreatHeatmap scenarios={result.scenario_results || []} /></section><ReplayPanel scenarios={result.scenario_results || []} /><div className="result-columns"><div className="panel findings-panel" id="scenario-results"><div className="panel-heading"><div><span className="eyebrow">GENERATED SCENARIOS</span><h3>Scenario findings</h3></div><Badge tone={failures.length ? "red" : "green"}>{failures.length ? `${failures.length} flagged` : "ALL PASS"}</Badge></div>{result.scenario_results?.length ? <div className="finding-list">{result.scenario_results.slice(0, compact ? 4 : undefined).map((item) => <FindingRow key={item.scenario_id} item={item} />)}</div> : <EmptyState title="No scenario results" copy="The API returned an empty scenario result set." />}</div><div className="panel findings-panel" id="security-results"><div className="panel-heading"><div><span className="eyebrow">SECURITY ANALYSIS</span><h3>Attack resistance</h3></div><Badge tone={security.failed ? "red" : "green"}>{security.failed ? `${security.failed} failed` : "RESILIENT"}</Badge></div>{attacks.length ? <div className="finding-list">{attacks.slice(0, compact ? 4 : undefined).map((item) => <AttackRow key={item.attack_id} item={item} />)}</div> : <EmptyState title="No attack results" copy="The API returned an empty attack result set." />}</div></div><div className="result-footer"><span>RUN ID <b>{result.test_id}</b></span><span>RUNTIME <b>{savings.automated_runtime_minutes || 0} min</b></span><span>CLASSIFIED BY <b>HYBRID ENGINE</b></span></div></section>;
}

function ScenarioConstellation({ scenarios }) {
  const visible = scenarios.slice(0, 28);
  return <div className="panel constellation-panel"><div className="panel-heading"><div><span className="eyebrow">SCENARIO CONSTELLATION</span><h3>Probe distribution</h3></div><span className="history-path">{scenarios.length} NODES</span></div><div className="constellation"><div className="constellation-orbit orbit-a" /><div className="constellation-orbit orbit-b" /><div className="constellation-core"><Icon name="radar" size={20} /><small>SCENARIOS</small></div>{visible.map((item, index) => <span className={`constellation-node node-${item.failure_type === "PASS" ? "pass" : "risk"}`} key={item.scenario_id} style={{ "--node-x": `${50 + Math.cos(index * 2.4) * (23 + (index % 4) * 6)}%`, "--node-y": `${50 + Math.sin(index * 2.4) * (23 + (index % 4) * 6)}%`, "--node-delay": `${index * 0.06}s` }} title={`${item.scenario_id}: ${item.failure_type}`} />)}</div><div className="constellation-legend"><span><i className="node-pass" /> PASS</span><span><i className="node-risk" /> FLAGGED</span><span>HOVER A NODE FOR ID</span></div></div>;
}

function ThreatHeatmap({ scenarios }) {
  const rows = ["PASS", "MEDIUM", "HIGH", "CRITICAL"];
  const cols = ["LOOP", "DRIFT", "UNSAFE", "CONFIDENCE", "CONSTRAINT"];
  const riskCount = scenarios.filter((item) => item.failure_type !== "PASS").length;
  return <div className="panel heatmap-panel"><div className="panel-heading"><div><span className="eyebrow">THREAT HEATMAP</span><h3>Failure concentration</h3></div><span className="history-path">{riskCount} FLAGGED</span></div><div className="heatmap-wrap"><div className="heatmap-grid"><div /><>{cols.map((col) => <span className="heatmap-col" key={col}>{col}</span>)}</>{rows.map((row, rowIndex) => <Fragment key={row}><span className="heatmap-row">{row}</span>{cols.map((col, colIndex) => { const intensity = row === "PASS" ? 0.15 : Math.min(.95, ((riskCount + rowIndex * 2 + colIndex) % 7) / 7 + .1); return <i key={`${row}-${col}`} className="heat-cell" style={{ opacity: intensity }} title={`${row} / ${col}`} />; })}</Fragment>)}</div><div className="heatmap-scale"><span>LOW</span><i /><i /><i /><i /><span>HIGH</span></div></div></div>;
}

function ReplayPanel({ scenarios }) {
  const [index, setIndex] = useState(0);
  const current = scenarios[index] || scenarios[0];
  if (!current) return null;
  return <div className="panel replay-panel"><div className="panel-heading"><div><span className="eyebrow">FLIGHT RECORDER</span><h3>Replay a scenario decision</h3></div><span className="history-path">{index + 1} / {scenarios.length}</span></div><div className="replay-body"><div className="replay-meta"><Badge tone={current.failure_type === "PASS" ? "green" : "red"}>{current.failure_type}</Badge><span>{current.scenario_id}</span><span>{current.severity}</span></div><p className="replay-input">{current.input}</p><div className="replay-trace"><span><b>01</b> PROMPT INGESTED</span><span><b>02</b> CONSTRAINTS CHECKED</span><span><b>03</b> {current.failure_type === "PASS" ? "SAFE OUTCOME" : "RISK SIGNAL RAISED"}</span></div><input className="comparison-slider replay-slider" type="range" min="0" max={Math.max(0, scenarios.length - 1)} value={index} onChange={(event) => setIndex(Number(event.target.value))} /></div></div>;
}

function BreakdownPanel({ scenarios, attacks }) {
  const failureCounts = scenarios.reduce((counts, item) => { const key = item.failure_type || "UNKNOWN"; counts[key] = (counts[key] || 0) + 1; return counts; }, {});
  const attackCounts = attacks.reduce((counts, item) => { const key = item.classification || "UNKNOWN"; counts[key] = (counts[key] || 0) + 1; return counts; }, {});
  const failureEntries = Object.entries(failureCounts).sort((a, b) => b[1] - a[1]);
  const attackEntries = Object.entries(attackCounts).sort((a, b) => b[1] - a[1]);
  const maxFailure = Math.max(1, ...failureEntries.map(([, count]) => count));
  const maxAttack = Math.max(1, ...attackEntries.map(([, count]) => count));
  return <section className="breakdown-grid"><div className="panel breakdown-panel"><div className="panel-heading"><div><span className="eyebrow">FAILURE TAXONOMY</span><h3>Scenario classification mix</h3></div><span className="history-path">{scenarios.length} TOTAL</span></div><div className="bar-list">{failureEntries.length ? failureEntries.map(([label, count]) => <div className="bar-row" key={label}><div className="bar-label"><span>{label}</span><b>{count}</b></div><div className="bar-track"><i className={label === "PASS" ? "bar-fill bar-pass" : "bar-fill"} style={{ width: `${(count / maxFailure) * 100}%` }} /></div></div>) : <p className="no-breakdown">No scenario classifications returned.</p>}</div></div><div className="panel breakdown-panel"><div className="panel-heading"><div><span className="eyebrow">SECURITY CLASSIFICATION</span><h3>Attack response mix</h3></div><span className="history-path">{attacks.length} TOTAL</span></div><div className="bar-list">{attackEntries.length ? attackEntries.map(([label, count]) => <div className="bar-row" key={label}><div className="bar-label"><span>{label}</span><b>{count}</b></div><div className="bar-track"><i className={`bar-fill bar-${label.toLowerCase()}`} style={{ width: `${(count / maxAttack) * 100}%` }} /></div></div>) : <p className="no-breakdown">No attack classifications returned.</p>}</div></div></section>;
}

function ScoreCard({ label, value, detail, tone }) {
  return <div className={`score-card score-${tone}`}><span className="eyebrow">{label}</span><strong>{value}</strong><small>{detail}</small><span className="score-corner" /></div>;
}

function FindingRow({ item }) {
  const tone = item.failure_type === "PASS" ? "green" : item.severity === "CRITICAL" || item.severity === "HIGH" ? "red" : "amber";
  return <details className="finding-row"><summary><span className={`finding-icon finding-${tone}`}><Icon name={item.failure_type === "PASS" ? "check" : "warning"} size={14} /></span><span className="finding-main"><strong>{item.failure_type}</strong><small>Scenario {item.scenario_id} <span>/</span> {item.source}</small></span><Badge tone={tone}>{item.severity}</Badge><Icon name="chevron" size={14} /></summary><div className="finding-detail"><p><b>Input</b>{item.input}</p><p><b>Why it matters</b>{item.explanation}</p>{item.recommendation && <p><b>Recommendation</b>{item.recommendation}</p>}</div></details>;
}

function AttackRow({ item }) {
  const tone = item.classification === "FAIL" ? "red" : item.classification === "PARTIAL" ? "amber" : "green";
  return <details className="finding-row"><summary><span className={`finding-icon finding-${tone}`}><Icon name={item.classification === "PASS" ? "shield" : "warning"} size={14} /></span><span className="finding-main"><strong>{item.attack_type}</strong><small>Attack {item.attack_id} <span>/</span> {item.source}</small></span><Badge tone={tone}>{item.classification}</Badge><Icon name="chevron" size={14} /></summary><div className="finding-detail"><p><b>Prompt</b>{item.attack}</p><p><b>Analysis</b>{item.explanation}</p></div></details>;
}

export default App;

