import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  runPipeline,
  type PipelineResult,
  type ProposalMethod,
  type Scenario,
  type Stage,
} from "./api";

const METHODS: { id: ProposalMethod; label: string }[] = [
  { id: "MANUAL_TRANSLATION", label: "Manual" },
  { id: "MODEL_ASSISTED", label: "Model-assisted" },
  { id: "DETERMINISTIC_PARSER", label: "Parser" },
];

const PRESETS: { name: string; note: string; scenario: Partial<Scenario> }[] = [
  {
    name: "Clean crossing",
    note: "Ratified by an independent reviewer",
    scenario: { ratified: true, independent_review: true },
  },
  {
    name: "No ratification",
    note: "Held — nothing has been ratified",
    scenario: { ratified: false, independent_review: true },
  },
  {
    name: "Author self-ratifies",
    note: "Held — separation of duties",
    scenario: { ratified: true, independent_review: false },
  },
];

const DEFAULT_SCENARIO: Scenario = {
  field_name: "hardness",
  unit_id: "unit.hrc",
  value: "41.2500",
  proposal_method: "MANUAL_TRANSLATION",
  ratified: true,
  independent_review: true,
};

type Tone = "mint" | "amber" | "cyan" | "mute";

function toneFor(status: string): Tone {
  if (["BUILD0_REQUEST_READY", "BOUND"].includes(status)) return "mint";
  if (["ADVISORY_GAP", "FAIL_CLOSED", "INTEGRITY_FAILURE", "ABSENT"].includes(status))
    return "amber";
  if (["RATIFIED", "RESOLVED"].includes(status)) return "cyan";
  return "mute";
}

const TONE_TEXT: Record<Tone, string> = {
  mint: "text-mint",
  amber: "text-amber",
  cyan: "text-cyan",
  mute: "text-mute",
};
const TONE_DOT: Record<Tone, string> = {
  mint: "bg-mint",
  amber: "bg-amber",
  cyan: "bg-cyan",
  mute: "bg-mute2",
};

function Chip({ status }: { status: string }) {
  const tone = toneFor(status);
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono text-[11px] tracking-wider ${TONE_TEXT[tone]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${TONE_DOT[tone]}`} />
      {status}
    </span>
  );
}

function RecordView({ record }: { record: Record<string, unknown> }) {
  return (
    <pre className="mt-3 max-h-72 overflow-auto rounded border border-edge bg-ink2 p-3 font-mono text-[11.5px] leading-relaxed text-mute">
      {JSON.stringify(record, null, 2)}
    </pre>
  );
}

function StageTile({ stage, index }: { stage: Stage; index: number }) {
  const [open, setOpen] = useState(false);
  const marker = String(index + 1).padStart(2, "0");
  return (
    <div
      className="animate-arm rounded-md border border-edge bg-panel/70 px-4 py-3.5"
      style={{ animationDelay: `${index * 85}ms` }}
    >
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[11px] text-mute2">{marker}</span>
          <span className="font-mono text-[12px] uppercase tracking-widest text-paper">
            {stage.title}
          </span>
        </div>
        <Chip status={stage.status} />
      </div>
      <p className="mt-1.5 pl-8 text-[13.5px] leading-snug text-mute">{stage.summary}</p>
      {stage.record && (
        <div className="pl-8">
          <button
            onClick={() => setOpen((v) => !v)}
            className="mt-2 font-mono text-[11px] tracking-wide text-cyan/80 hover:text-cyan"
          >
            {open ? "− hide" : "+ governed record"}
            {stage.record_type ? `  ·  ${stage.record_type}` : ""}
          </button>
          {open && <RecordView record={stage.record} />}
        </div>
      )}
    </div>
  );
}

function Firewall({ result }: { result: PipelineResult }) {
  const crossed = result.crossed_firewall;
  return (
    <div
      className={`animate-seam relative overflow-hidden rounded-md border px-5 py-5 ${
        crossed ? "border-mint/40 bg-mint/5" : "border-amber/40 bg-amber/5"
      }`}
    >
      {/* hatch on a held boundary; a light seam on a crossing */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.13]"
        style={
          crossed
            ? {
                background:
                  "linear-gradient(90deg, transparent, var(--color-mint), transparent)",
              }
            : {
                backgroundImage:
                  "repeating-linear-gradient(45deg, var(--color-amber) 0 1px, transparent 1px 10px)",
              }
        }
      />
      <div className="relative flex items-center justify-between gap-4">
        <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-mute">
          Build 0 · Tier 1 firewall
        </div>
        <div
          className={`font-mono text-[11px] tracking-wider ${
            crossed ? "text-mint" : "text-amber"
          }`}
        >
          {result.gate_status}
        </div>
      </div>
      <div className="relative mt-3 flex items-center gap-4">
        <div
          className={`shrink-0 border px-3 py-2 font-mono text-[15px] font-medium uppercase tracking-[0.18em] ${
            crossed ? "border-mint/60 text-mint" : "border-amber/60 text-amber"
          }`}
        >
          {crossed ? "✓ Crossed" : "⦻ Held"}
        </div>
        <p className="text-[13.5px] leading-snug text-paper/90">{result.verdict_reason}</p>
      </div>
    </div>
  );
}

function Toggle({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="group flex w-full items-center justify-between rounded-md border border-edge bg-ink2 px-3.5 py-3 text-left transition-colors hover:border-edge2"
    >
      <span>
        <span className="block font-mono text-[12px] uppercase tracking-widest text-paper">
          {label}
        </span>
        <span className="mt-0.5 block text-[12px] text-mute2">{hint}</span>
      </span>
      <span
        className={`relative h-5 w-9 shrink-0 rounded-full border transition-colors ${
          checked ? "border-mint/60 bg-mint/25" : "border-edge2 bg-panel"
        }`}
      >
        <span
          className={`absolute top-0.5 h-3.5 w-3.5 rounded-full transition-all ${
            checked ? "left-4 bg-mint" : "left-0.5 bg-mute2"
          }`}
        />
      </span>
    </button>
  );
}

function Field({
  label,
  value,
  onChange,
  mono = true,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  mono?: boolean;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-widest text-mute2">
        {label}
      </span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        className={`w-full rounded-md border border-edge bg-ink2 px-3 py-2 text-[14px] text-paper outline-none transition-colors focus:border-mint/60 ${
          mono ? "font-mono" : ""
        }`}
      />
    </label>
  );
}

export default function App() {
  const [scenario, setScenario] = useState<Scenario>(DEFAULT_SCENARIO);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState(0);
  const ranOnce = useRef(false);

  const patch = useCallback(
    (p: Partial<Scenario>) => setScenario((s) => ({ ...s, ...p })),
    [],
  );

  const run = useCallback(async (s: Scenario) => {
    setRunning(true);
    setError(null);
    try {
      const r = await runPipeline(s);
      setResult(r);
      setRunId((n) => n + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setRunning(false);
    }
  }, []);

  // Populate the line on first load so the page opens on a live crossing.
  useEffect(() => {
    if (ranOnce.current) return;
    ranOnce.current = true;
    void run(DEFAULT_SCENARIO);
  }, [run]);

  const preStages = useMemo(
    () => result?.stages.filter((s) => !["firewall", "build0"].includes(s.key)) ?? [],
    [result],
  );
  const build0 = useMemo(
    () => result?.stages.find((s) => s.key === "build0") ?? null,
    [result],
  );
  const activePreset = PRESETS.findIndex(
    (p) =>
      p.scenario.ratified === scenario.ratified &&
      p.scenario.independent_review === scenario.independent_review,
  );

  return (
    <div className="mx-auto min-h-svh max-w-6xl px-5 py-8 md:px-8 md:py-12">
      {/* header */}
      <header className="flex items-center justify-between gap-4 border-b border-edge pb-5">
        <div className="flex items-center gap-2.5 font-mono text-[12px] tracking-[0.18em] text-mute">
          <span className="text-mint">◆</span>
          <span className="text-paper">GPTL</span>
          <span className="text-mute2">/</span>
          <span>GOVERNED CAPTURE FIREWALL</span>
        </div>
        <span className="rounded border border-edge2 px-2 py-1 font-mono text-[10px] tracking-widest text-amber">
          RESEARCH_ONLY
        </span>
      </header>

      {/* thesis hero */}
      <section className="pt-9 pb-8 md:pt-12">
        <h1 className="max-w-3xl text-[30px] font-extrabold leading-[1.12] tracking-tight text-paper md:text-[42px]">
          A value reaches the record of record only when a human ratifies it
          <span className="text-mint"> — and never their own work.</span>
        </h1>
        <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-mute">
          Configure a capture, run it through the real Build&nbsp;1 engine, and watch the
          firewall decide. A refusal is the system working.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(300px,360px)_1fr]">
        {/* ── controls ── */}
        <aside className="rounded-lg border border-edge bg-panel/40 p-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-mute2">
            The scenario
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <Field
              label="Field"
              value={scenario.field_name}
              onChange={(v) => patch({ field_name: v })}
            />
            <Field
              label="Unit"
              value={scenario.unit_id}
              onChange={(v) => patch({ unit_id: v })}
            />
          </div>
          <div className="mt-3">
            <Field
              label="Value"
              value={scenario.value}
              onChange={(v) => patch({ value: v })}
            />
          </div>

          <div className="mt-4">
            <span className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-widest text-mute2">
              Proposed via
            </span>
            <div className="flex overflow-hidden rounded-md border border-edge">
              {METHODS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => patch({ proposal_method: m.id })}
                  className={`flex-1 border-r border-edge px-2 py-2 font-mono text-[11px] tracking-wide transition-colors last:border-r-0 ${
                    scenario.proposal_method === m.id
                      ? "bg-panel2 text-mint"
                      : "bg-ink2 text-mute hover:text-paper"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
            <p className="mt-1.5 text-[12px] text-mute2">
              The model path earns no privilege — the outcome is identical.
            </p>
          </div>

          <div className="mt-4 space-y-2.5">
            <Toggle
              checked={scenario.ratified}
              onChange={(v) => patch({ ratified: v })}
              label="Ratified"
              hint="A human ratification event exists"
            />
            <Toggle
              checked={scenario.independent_review}
              onChange={(v) => patch({ independent_review: v })}
              label="Independent review"
              hint="Reviewer is not the author (separation of duties)"
            />
          </div>

          <button
            onClick={() => run(scenario)}
            disabled={running}
            className="mt-5 w-full rounded-md border border-mint/50 bg-mint/15 py-3 font-mono text-[13px] font-medium uppercase tracking-[0.18em] text-mint transition-colors hover:bg-mint/25 disabled:opacity-50"
          >
            {running ? "Running…" : "Run the line"}
          </button>

          <div className="mt-6 border-t border-edge pt-4">
            <div className="font-mono text-[10.5px] uppercase tracking-widest text-mute2">
              Presets
            </div>
            <div className="mt-2.5 space-y-2">
              {PRESETS.map((p, i) => (
                <button
                  key={p.name}
                  onClick={() => {
                    const next = { ...scenario, ...p.scenario };
                    setScenario(next);
                    void run(next);
                  }}
                  className={`w-full rounded-md border px-3 py-2.5 text-left transition-colors ${
                    activePreset === i
                      ? "border-cyan/50 bg-cyan/5"
                      : "border-edge bg-ink2 hover:border-edge2"
                  }`}
                >
                  <span className="block text-[13px] font-medium text-paper">{p.name}</span>
                  <span className="mt-0.5 block font-mono text-[11px] text-mute2">
                    {p.note}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* ── the line ── */}
        <main className="min-w-0">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-mute2">
              The line
            </div>
            <div className="font-mono text-[11px] text-mute2">real engine · no persistence</div>
          </div>

          {error && (
            <div className="rounded-md border border-amber/50 bg-amber/5 px-4 py-3 text-[13px] text-amber">
              {error}
            </div>
          )}

          {result && (
            <div key={runId} className="space-y-2.5">
              {preStages.map((s, i) => (
                <StageTile key={s.key} stage={s} index={i} />
              ))}

              <div
                className="animate-arm"
                style={{ animationDelay: `${preStages.length * 85}ms` }}
              >
                <Firewall result={result} />
              </div>

              {build0 ? (
                <div
                  className="animate-arm rounded-md border border-mint/40 bg-mint/5 px-4 py-3.5"
                  style={{ animationDelay: `${(preStages.length + 1) * 85}ms` }}
                >
                  <div className="flex items-baseline justify-between">
                    <span className="font-mono text-[12px] uppercase tracking-widest text-mint">
                      {build0.title}
                    </span>
                    <Chip status={build0.status} />
                  </div>
                  <p className="mt-1.5 text-[13.5px] text-mute">{build0.summary}</p>
                </div>
              ) : (
                <div
                  className="animate-arm rounded-md border border-dashed border-edge px-4 py-3.5 text-center font-mono text-[11.5px] tracking-wide text-mute2"
                  style={{ animationDelay: `${(preStages.length + 1) * 85}ms` }}
                >
                  Nothing bound into Build 0 Tier 1
                </div>
              )}
            </div>
          )}

          <p className="mt-5 max-w-xl text-[12.5px] leading-relaxed text-mute2">
            Every record above is real output from the governed engine — proposals,
            ratification events, and bound rows are constructed and evaluated by the same
            Build&nbsp;1 code the test suite pins. Nothing is staged.
          </p>
        </main>
      </div>
    </div>
  );
}
