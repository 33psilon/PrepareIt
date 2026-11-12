export type GroundedProblem = {
  id: string;
  slug?: string;
  source: 'leetcode' | 'codeforces' | string;
  title: string;
  difficulty: string;
  description: string;
  constraints: string[];
  examples: { input: string; output: string; explanation?: string }[];
  time_target: string;
  space_target: string;
};

type ProblemPanelProps = {
  problem: GroundedProblem | null;
  error?: string;
};

export default function ProblemPanel({ problem, error }: ProblemPanelProps) {
  if (!problem) {
    return (
      <div className="grid h-full place-items-center p-8 text-center">
        <div className="max-w-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-300">
            Interview problem
          </p>
          <p className={`mt-3 text-sm leading-6 ${error ? 'text-rose-300' : 'text-zinc-400'}`}>
            {error || 'Loading the selected problem…'}
          </p>
        </div>
      </div>
    );
  }

  const difficulty = problem.difficulty.toLowerCase();
  const badge =
    difficulty === 'easy'
      ? 'bg-emerald-400/15 text-emerald-300'
      : difficulty === 'medium'
        ? 'bg-amber-400/15 text-amber-300'
        : 'bg-rose-400/15 text-rose-300';

  return (
    <section className="h-full min-w-0 overflow-y-auto p-5 text-zinc-200 sm:p-7">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="mb-2 text-[0.65rem] font-medium uppercase tracking-[0.2em] text-violet-300">
            {problem.source} problem
          </p>
          <h2 className="text-2xl font-semibold tracking-tight text-white">{problem.title}</h2>
        </div>
        <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold capitalize ${badge}`}>
          {problem.difficulty}
        </span>
      </header>

      <section aria-labelledby="problem-description-heading">
        <h3 id="problem-description-heading" className="text-sm font-semibold text-white">
          Problem
        </h3>
        <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-300">
          {problem.description}
        </p>
      </section>

      {(problem.time_target || problem.space_target) && (
        <section className="mt-6 grid grid-cols-2 gap-3" aria-label="Complexity targets">
          {problem.time_target && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
              <p className="text-[0.65rem] font-medium uppercase tracking-wide text-zinc-500">
                Time target
              </p>
              <p className="mt-1 font-mono text-sm text-violet-200">{problem.time_target}</p>
            </div>
          )}
          {problem.space_target && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
              <p className="text-[0.65rem] font-medium uppercase tracking-wide text-zinc-500">
                Space target
              </p>
              <p className="mt-1 font-mono text-sm text-violet-200">{problem.space_target}</p>
            </div>
          )}
        </section>
      )}

      {problem.examples.length > 0 && (
        <section className="mt-8" aria-labelledby="problem-examples-heading">
          <h3 id="problem-examples-heading" className="text-sm font-semibold text-white">
            Examples
          </h3>
          <div className="mt-3 space-y-3">
            {problem.examples.map((example, index) => (
              <article
                key={`${example.input}-${index}`}
                className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 text-xs leading-6"
              >
                <p className="mb-2 font-semibold text-zinc-400">Example {index + 1}</p>
                <p>
                  <span className="text-zinc-500">Input: </span>
                  <code className="break-words text-violet-200">{example.input}</code>
                </p>
                <p className="mt-1">
                  <span className="text-zinc-500">Output: </span>
                  <code className="break-words text-violet-200">{example.output}</code>
                </p>
                {example.explanation && (
                  <p className="mt-2 text-zinc-400">
                    <span className="font-medium text-zinc-300">Explanation: </span>
                    {example.explanation}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {problem.constraints.length > 0 && (
        <section className="mt-8" aria-labelledby="problem-constraints-heading">
          <h3 id="problem-constraints-heading" className="text-sm font-semibold text-white">
            Constraints
          </h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-400">
            {problem.constraints.map((constraint) => (
              <li key={constraint} className="flex gap-2">
                <span aria-hidden="true" className="text-violet-400">
                  •
                </span>
                <span>{constraint}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}
