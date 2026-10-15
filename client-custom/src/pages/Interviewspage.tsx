import { useEffect, useState } from 'react';
import {
  ArrowUpRight,
  Check,
  ChevronRight,
  Clock3,
  Code2,
  LockKeyhole,
  LogOut,
  Moon,
  Play,
  Search,
  Sparkles,
  Star,
  Sun,
  Trophy,
  Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useClerk } from '@clerk/clerk-react';

const featuredInterview = {
  id: 'dsa-expert',
  title: 'DSA Expert',
  difficulty: 'Medium',
  duration: '45 min',
  users: '2.1k learners',
  description:
    'A rigorous, collaborative technical round that builds from first principles to an efficient solution. Practice clarity, trade-offs, and clean implementation under realistic pressure.',
  tags: ['Algorithms', 'Data structures', 'Optimisation'],
};

const interviewers = [
  {
    id: 'amazon-sde',
    title: 'Amazon SDE Mock',
    difficulty: 'Hard',
    duration: '60 min',
    users: '1.8k',
    description:
      'A focused SDE simulation combining coding depth, architectural trade-offs, and leadership-principle follow-ups.',
    tags: ['Amazon', 'Leadership', 'System design'],
    company: 'Amazon',
    available: true,
  },
  {
    id: 'google-swe',
    title: 'Google SWE Interview',
    difficulty: 'Hard',
    duration: '45 min',
    users: '2.3k',
    description:
      'Structured algorithmic problem solving with space to articulate complexity and alternative approaches.',
    tags: ['Google', 'Algorithms', 'Problem solving'],
    company: 'Google',
    available: false,
  },
  {
    id: 'meta-e4',
    title: 'Meta E4 Technical',
    difficulty: 'Medium',
    duration: '45 min',
    users: '1.5k',
    description:
      'An E4-level interview mixing implementation fluency with practical system-design fundamentals.',
    tags: ['Meta', 'Coding', 'Behavioural'],
    company: 'Meta',
    available: false,
  },
  {
    id: 'microsoft-sde2',
    title: 'Microsoft SDE II',
    difficulty: 'Medium',
    duration: '50 min',
    users: '1.2k',
    description:
      'Evaluate code quality, collaboration, and architecture decisions in a polished SDE II-style round.',
    tags: ['Microsoft', 'Architecture', 'Patterns'],
    company: 'Microsoft',
    available: false,
  },
  {
    id: 'apple-swe',
    title: 'Apple SWE Mock',
    difficulty: 'Hard',
    duration: '60 min',
    users: '900',
    description:
      'A systems-minded technical interview with room for precise reasoning and implementation detail.',
    tags: ['Apple', 'Systems', 'Swift'],
    company: 'Apple',
    available: false,
  },
  {
    id: 'netflix-senior',
    title: 'Netflix Senior SWE',
    difficulty: 'Hard',
    duration: '55 min',
    users: '750',
    description:
      'A high-scale engineering conversation focused on ownership, distributed systems, and judgment.',
    tags: ['Netflix', 'Distributed systems', 'Scale'],
    company: 'Netflix',
    available: false,
  },
];

const getDifficultyStyle = (difficulty: string, isDarkMode: boolean) => {
  const styles = {
    Easy: isDarkMode
      ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200'
      : 'border-emerald-200 bg-emerald-50 text-emerald-800',
    Medium: isDarkMode
      ? 'border-amber-300/30 bg-amber-300/10 text-amber-100'
      : 'border-amber-200 bg-amber-50 text-amber-800',
    Hard: isDarkMode
      ? 'border-rose-300/30 bg-rose-300/10 text-rose-100'
      : 'border-rose-200 bg-rose-50 text-rose-800',
  };

  return styles[difficulty as keyof typeof styles] ?? styles.Medium;
};

const InterviewsPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const navigate = useNavigate();
  const { isSignedIn, isLoaded } = useAuth();
  const { signOut } = useClerk();

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  useEffect(() => {
    setIsDarkMode(localStorage.getItem('theme') === 'dark');
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      navigate('/');
    }
  }, [isLoaded, isSignedIn, navigate]);

  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredInterviewers = interviewers.filter((interviewer) =>
    [interviewer.title, interviewer.company, ...interviewer.tags]
      .join(' ')
      .toLowerCase()
      .includes(normalizedQuery),
  );

  const pageSurface = isDarkMode ? 'bg-zinc-950 text-white' : 'bg-zinc-100 text-zinc-950';
  const elevatedSurface = isDarkMode ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200';
  const mutedText = isDarkMode ? 'text-zinc-400' : 'text-zinc-600';
  const mutedSurface = isDarkMode ? 'bg-zinc-800/80 border-zinc-700' : 'bg-zinc-50 border-zinc-200';

  return (
    <div className={`min-h-screen overflow-x-hidden transition-colors duration-300 ${pageSurface}`}>
      <div
        aria-hidden="true"
        className={`pointer-events-none absolute inset-x-0 top-0 h-[36rem] opacity-70 ${
          isDarkMode
            ? 'bg-[radial-gradient(circle_at_78%_8%,rgba(168,85,247,0.18),transparent_31%),radial-gradient(circle_at_12%_16%,rgba(255,255,255,0.08),transparent_24%)]'
            : 'bg-[radial-gradient(circle_at_78%_8%,rgba(168,85,247,0.16),transparent_31%),radial-gradient(circle_at_12%_16%,rgba(230,255,130,0.65),transparent_22%)]'
        }`}
      />

      <main className="relative mx-auto w-full max-w-7xl px-4 py-4 sm:px-6 lg:px-8 lg:py-6">
        <div className={`overflow-hidden rounded-[2rem] border shadow-[0_24px_70px_-38px_rgba(0,0,0,0.4)] ${elevatedSurface}`}>
          <header className={`flex flex-wrap items-center justify-between gap-4 border-b px-5 py-4 sm:px-8 ${isDarkMode ? 'border-zinc-800' : 'border-zinc-100'}`}>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="group flex items-center gap-3 text-left"
              aria-label="Return to PrepareIt home"
            >
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-black text-lg font-semibold text-white shadow-lg transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-105">
                P
              </span>
              <span>
                <span className="block text-[0.7rem] font-medium uppercase tracking-[0.22em] text-violet-600 dark:text-violet-300">
                  PrepareIt AI
                </span>
                <span className="block text-sm font-semibold tracking-tight">Interview Studio</span>
              </span>
            </button>

            <div className="flex items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setIsDarkMode((value) => !value)}
                className={`grid h-10 w-10 place-items-center rounded-full border transition-colors ${mutedSurface} hover:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 ${isDarkMode ? 'focus:ring-offset-zinc-900' : 'focus:ring-offset-white'}`}
                aria-label={isDarkMode ? 'Use light theme' : 'Use dark theme'}
              >
                {isDarkMode ? <Sun className="h-4 w-4 text-amber-300" /> : <Moon className="h-4 w-4" />}
              </button>
              <button
                type="button"
                onClick={handleSignOut}
                className={`inline-flex h-10 items-center gap-2 rounded-full border px-3 text-sm font-medium transition-colors hover:border-violet-400 hover:text-violet-600 dark:hover:text-violet-300 ${mutedSurface}`}
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          </header>

          <div className="px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
            <section className="grid gap-5 lg:grid-cols-[1.55fr_0.85fr]" aria-labelledby="page-title">
              <div className="relative overflow-hidden rounded-[1.75rem] bg-black px-6 py-8 text-white sm:px-8 sm:py-10">
                <div className="absolute -right-14 -top-16 h-52 w-52 rounded-full border border-white/15" />
                <div className="absolute -right-3 top-7 h-36 w-36 rounded-full border border-white/10" />
                <div className="relative max-w-xl">
                  <div className="mb-5 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-zinc-400">
                    <span className="h-2 w-2 rounded-full bg-[#e6ff82]" />
                    Your practice workspace
                  </div>
                  <h1 id="page-title" className="max-w-lg text-4xl font-light leading-[1.05] tracking-[-0.045em] sm:text-5xl">
                    Build the confidence that gets remembered.
                  </h1>
                  <p className="mt-5 max-w-lg text-sm leading-6 text-zinc-300 sm:text-base">
                    Choose a focused interview, think aloud, and receive live feedback designed for the way technical teams actually evaluate.
                  </p>
                  <div className="mt-7 flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={() => navigate('/interviewer')}
                      className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-black transition-transform hover:-translate-y-0.5 hover:bg-[#e6ff82] focus:outline-none focus:ring-2 focus:ring-[#e6ff82] focus:ring-offset-2 focus:ring-offset-black"
                    >
                      Start your live mock
                      <ArrowUpRight className="h-4 w-4" />
                    </button>
                    <span className="inline-flex items-center gap-2 text-sm text-zinc-400">
                      <Check className="h-4 w-4 text-[#e6ff82]" />
                      Amazon SDE ready now
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-1">
                <article className={`rounded-[1.75rem] border p-6 ${isDarkMode ? 'border-zinc-700 bg-zinc-800' : 'border-zinc-200 bg-[#e6ff82]'}`}>
                  <div className="flex items-start justify-between gap-4">
                    <span className={`grid h-11 w-11 place-items-center rounded-2xl ${isDarkMode ? 'bg-zinc-700 text-[#e6ff82]' : 'bg-black text-[#e6ff82]'}`}>
                      <Trophy className="h-5 w-5" />
                    </span>
                    <span className={`text-xs font-medium uppercase tracking-[0.16em] ${isDarkMode ? 'text-zinc-400' : 'text-zinc-600'}`}>This week</span>
                  </div>
                  <p className="mt-8 text-4xl font-semibold tracking-[-0.06em]">01</p>
                  <p className={`mt-1 text-sm ${isDarkMode ? 'text-zinc-300' : 'text-zinc-700'}`}>interview available to start</p>
                </article>

                <article className={`rounded-[1.75rem] border p-6 ${mutedSurface}`}>
                  <Code2 className="h-5 w-5 text-violet-500" />
                  <p className="mt-8 text-4xl font-semibold tracking-[-0.06em]">60</p>
                  <p className={`mt-1 text-sm ${mutedText}`}>minutes of focused practice</p>
                  <div className={`mt-5 h-1.5 overflow-hidden rounded-full ${isDarkMode ? 'bg-zinc-700' : 'bg-zinc-200'}`}>
                    <div className="h-full w-1/3 rounded-full bg-violet-500" />
                  </div>
                </article>
              </div>
            </section>

            <section className="mt-10" aria-labelledby="featured-title">
              <div className="mb-4 flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-violet-600 dark:text-violet-300">Featured practice</p>
                  <h2 id="featured-title" className="mt-2 text-2xl font-semibold tracking-[-0.04em]">Meet your interview partner</h2>
                </div>
                <span className={`hidden rounded-full border px-3 py-1.5 text-xs font-medium sm:block ${mutedSurface}`}>Live voice feedback</span>
              </div>

              <article className={`group grid overflow-hidden rounded-[1.75rem] border lg:grid-cols-[0.9fr_1.5fr] ${elevatedSurface}`}>
                <div className="relative min-h-60 overflow-hidden bg-violet-600 p-6 text-white sm:p-8">
                  <div className="absolute -bottom-20 -right-20 h-64 w-64 rounded-full border border-white/25" />
                  <div className="absolute bottom-7 right-7 h-36 w-36 rounded-full border border-white/20" />
                  <div className="relative flex h-full flex-col justify-between">
                    <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-medium backdrop-blur-sm">
                      <Star className="h-3.5 w-3.5 fill-current" />
                      Recommended next
                    </span>
                    <div>
                      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-black text-[#e6ff82] shadow-xl">
                        <Sparkles className="h-6 w-6" />
                      </div>
                      <p className="mt-4 text-sm font-medium text-violet-100">Technical foundation</p>
                    </div>
                  </div>
                </div>

                <div className="p-6 sm:p-8">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${getDifficultyStyle(featuredInterview.difficulty, isDarkMode)}`}>
                      {featuredInterview.difficulty}
                    </span>
                    <span className={`text-xs font-medium uppercase tracking-[0.16em] ${mutedText}`}>AI interviewer</span>
                  </div>
                  <h3 className="mt-5 text-3xl font-semibold tracking-[-0.05em]">{featuredInterview.title}</h3>
                  <p className={`mt-3 max-w-2xl text-sm leading-6 ${mutedText}`}>{featuredInterview.description}</p>
                  <div className={`mt-6 flex flex-wrap gap-x-5 gap-y-2 border-y py-4 text-sm ${isDarkMode ? 'border-zinc-800 text-zinc-300' : 'border-zinc-100 text-zinc-600'}`}>
                    <span className="inline-flex items-center gap-2"><Clock3 className="h-4 w-4 text-violet-500" />{featuredInterview.duration}</span>
                    <span className="inline-flex items-center gap-2"><Users className="h-4 w-4 text-violet-500" />{featuredInterview.users}</span>
                    <span className="inline-flex items-center gap-2"><Code2 className="h-4 w-4 text-violet-500" />Live code review</span>
                  </div>
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
                    <div className="flex flex-wrap gap-2">
                      {featuredInterview.tags.map((tag) => (
                        <span key={tag} className={`rounded-full px-3 py-1.5 text-xs font-medium ${isDarkMode ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-100 text-zinc-700'}`}>{tag}</span>
                      ))}
                    </div>
                    <span className={`inline-flex items-center gap-2 text-sm font-medium ${mutedText}`}>Available soon <LockKeyhole className="h-3.5 w-3.5" /></span>
                  </div>
                </div>
              </article>
            </section>

            <section className="mt-12" aria-labelledby="catalogue-title">
              <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-violet-600 dark:text-violet-300">Practice catalogue</p>
                  <h2 id="catalogue-title" className="mt-2 text-2xl font-semibold tracking-[-0.04em]">Interview like the teams you admire.</h2>
                  <p className={`mt-2 max-w-xl text-sm leading-6 ${mutedText}`}>Curated mock interviews designed around the communication and technical signals that matter.</p>
                </div>
                <label className={`group relative flex h-12 w-full items-center rounded-full border px-4 transition-colors focus-within:border-violet-500 sm:w-80 ${mutedSurface}`}>
                  <Search className={`h-4 w-4 transition-colors group-focus-within:text-violet-500 ${mutedText}`} />
                  <input
                    type="search"
                    placeholder="Search interview tracks"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    className={`ml-3 w-full bg-transparent text-sm outline-none ${isDarkMode ? 'placeholder:text-zinc-500' : 'placeholder:text-zinc-400'}`}
                    aria-label="Search interview tracks"
                  />
                </label>
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-3 py-1.5 text-xs font-medium ${isDarkMode ? 'bg-white text-black' : 'bg-black text-white'}`}>All tracks</span>
                <span className={`rounded-full border px-3 py-1.5 text-xs font-medium ${mutedSurface}`}>Technical</span>
                <span className={`rounded-full border px-3 py-1.5 text-xs font-medium ${mutedSurface}`}>System design</span>
                <span className={`rounded-full border px-3 py-1.5 text-xs font-medium ${mutedSurface}`}>Behavioural</span>
                <span className={`ml-auto text-xs font-medium ${mutedText}`}>{filteredInterviewers.length} tracks</span>
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {filteredInterviewers.map((interviewer) => (
                  <article
                    key={interviewer.id}
                    className={`group relative flex min-h-80 flex-col overflow-hidden rounded-[1.5rem] border p-6 transition-all duration-300 ${
                      interviewer.available
                        ? 'border-black bg-black text-white shadow-[0_18px_45px_-25px_rgba(0,0,0,0.8)] hover:-translate-y-1 hover:shadow-[0_28px_55px_-24px_rgba(0,0,0,0.65)]'
                        : `${elevatedSurface} hover:-translate-y-1 hover:border-violet-300 dark:hover:border-violet-500`
                    }`}
                  >
                    {interviewer.available && <div aria-hidden="true" className="absolute -right-9 -top-10 h-36 w-36 rounded-full border border-white/15" />}
                    <div className="relative flex items-start justify-between gap-4">
                      <span className={`grid h-12 w-12 place-items-center rounded-2xl text-sm font-semibold ${interviewer.available ? 'bg-[#e6ff82] text-black' : (isDarkMode ? 'bg-zinc-800 text-white' : 'bg-zinc-100 text-zinc-900')}`}>
                        {interviewer.company.slice(0, 1)}
                      </span>
                      <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${getDifficultyStyle(interviewer.difficulty, isDarkMode)}`}>
                        {interviewer.difficulty}
                      </span>
                    </div>

                    <div className="relative mt-7">
                      <p className={`text-xs font-medium uppercase tracking-[0.16em] ${interviewer.available ? 'text-zinc-400' : mutedText}`}>{interviewer.company}</p>
                      <h3 className="mt-2 text-xl font-semibold tracking-[-0.035em]">{interviewer.title}</h3>
                      <p className={`mt-3 text-sm leading-6 ${interviewer.available ? 'text-zinc-300' : mutedText}`}>{interviewer.description}</p>
                    </div>

                    <div className={`relative mt-5 flex items-center gap-4 text-xs ${interviewer.available ? 'text-zinc-400' : mutedText}`}>
                      <span className="inline-flex items-center gap-1.5"><Clock3 className="h-3.5 w-3.5" />{interviewer.duration}</span>
                      <span className="inline-flex items-center gap-1.5"><Users className="h-3.5 w-3.5" />{interviewer.users}</span>
                    </div>

                    <div className="relative mt-auto pt-6">
                      <div className="mb-5 flex flex-wrap gap-2">
                        {interviewer.tags.slice(0, 2).map((tag) => (
                          <span key={tag} className={`rounded-full px-2.5 py-1 text-xs ${interviewer.available ? 'bg-white/10 text-zinc-200' : (isDarkMode ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-100 text-zinc-600')}`}>{tag}</span>
                        ))}
                      </div>
                      {interviewer.available ? (
                        <button
                          type="button"
                          onClick={() => navigate('/interviewer')}
                          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-4 py-3 text-sm font-semibold text-black transition-colors hover:bg-[#e6ff82] focus:outline-none focus:ring-2 focus:ring-[#e6ff82] focus:ring-offset-2 focus:ring-offset-black"
                        >
                          Begin Amazon mock
                          <Play className="h-4 w-4 fill-current" />
                        </button>
                      ) : (
                        <div className={`inline-flex w-full items-center justify-between rounded-full border px-4 py-3 text-sm font-medium ${mutedSurface}`}>
                          Coming soon
                          <LockKeyhole className="h-4 w-4" />
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>

              {filteredInterviewers.length === 0 && (
                <div className={`mt-6 rounded-[1.5rem] border border-dashed px-6 py-14 text-center ${mutedSurface}`}>
                  <span className={`mx-auto grid h-12 w-12 place-items-center rounded-2xl ${isDarkMode ? 'bg-zinc-800' : 'bg-white'}`}><Search className="h-5 w-5 text-violet-500" /></span>
                  <h3 className="mt-4 text-lg font-semibold">No interview track found</h3>
                  <p className={`mt-2 text-sm ${mutedText}`}>Try a company, skill, or interview type.</p>
                </div>
              )}
            </section>

            <footer className={`mt-12 flex flex-col gap-4 border-t pt-6 text-xs sm:flex-row sm:items-center sm:justify-between ${isDarkMode ? 'border-zinc-800 text-zinc-500' : 'border-zinc-100 text-zinc-500'}`}>
              <span>PrepareIt AI - thoughtful practice for technical interviews</span>
              <span className="inline-flex items-center gap-1.5">Built for deliberate progress <ChevronRight className="h-3.5 w-3.5" /></span>
            </footer>
          </div>
        </div>
      </main>
    </div>
  );
};

export default InterviewsPage;
