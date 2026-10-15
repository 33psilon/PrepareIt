export type GroundedProblem = {
  id: string;
  source: 'leetcode' | 'codeforces' | string;
  title: string;
  difficulty: string;
  description: string;
  constraints: string[];
  examples: { input: string; output: string; explanation?: string }[];
  time_target: string;
  space_target: string;
};

type ProblemPanelProps = { problem: GroundedProblem | null };

export default function ProblemPanel({ problem }: ProblemPanelProps) {
  if (!problem) return <div className="flex h-full items-center justify-center p-8 text-sm text-zinc-500">Loading grounded problem…</div>;
  const difficulty = problem.difficulty.toLowerCase();
  const badge = difficulty === 'easy' ? 'bg-emerald-400/15 text-emerald-300' : difficulty === 'medium' ? 'bg-amber-400/15 text-amber-300' : 'bg-red-400/15 text-red-300';
  return (
    <section className="h-full min-w-0 overflow-y-auto p-5 text-zinc-200 sm:p-7">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div><p className="mb-2 text-[0.65rem] uppercase tracking-[0.2em] text-violet-300">{problem.source} problem</p><h2 className="text-2xl font-semibold tracking-tight text-white">{problem.title}</h2></div>
        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold capitalize ${badge}`}>{problem.difficulty}</span>
      </div>
      <div className="prose prose-invert max-w-none text-sm leading-7"><p>{problem.description}</p></div>
      <div className="mt-7 grid grid-cols-2 gap-3"><div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3"><p className="text-[0.65rem] uppercase text-zinc-500">Time target</p><p className="mt-1 font-mono text-sm text-violet-200">{problem.time_target}</p></div><div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3"><p className="text-[0.65rem] uppercase text-zinc-500">Space target</p><p className="mt-1 font-mono text-sm text-violet-200">{problem.space_target}</p></div></div>
      <h3 className="mt-8 text-sm font-semibold text-white">Examples</h3>
      <div className="mt-3 space-y-3">{problem.examples.map((example, index) => <div key={`${example.input}-${index}`} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 text-xs"><p className="mb-2 font-semibold text-zinc-400">Example {index + 1}</p><p><span className="text-zinc-500">Input:</span> <code className="break-words text-violet-200">{example.input}</code></p><p className="mt-1"><span className="text-zinc-500">Output:</span> <code className="break-words text-violet-200">{example.output}</code></p>{example.explanation && <p className="mt-2 text-zinc-400">{example.explanation}</p>}</div>)}</div>
      <h3 className="mt-8 text-sm font-semibold text-white">Constraints</h3>
      <ul className="mt-3 space-y-2 text-sm text-zinc-400">{problem.constraints.map((constraint) => <li key={constraint} className="flex gap-2"><span className="text-violet-400">•</span><span>{constraint}</span></li>)}</ul>
    </section>
  );
}
