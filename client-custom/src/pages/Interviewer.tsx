import { PipecatClient, RTVIEvent, type Participant } from '@pipecat-ai/client-js';
import {
  PipecatClientProvider,
  PipecatClientAudio,
  usePipecatClient,
  useRTVIClientEvent,
} from '@pipecat-ai/client-react';
import { SmallWebRTCTransport } from '@pipecat-ai/small-webrtc-transport';
import { useState, useCallback, useRef, useEffect, createContext, useContext } from 'react';
import Editor from '@monaco-editor/react';
import { ArrowLeft, Code2, Mic, MicOff, PhoneOff, RotateCcw, Video } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ProblemPanel, { type GroundedProblem } from '../components/ProblemPanel';

import '../index.css';

type CodeContextValue = {
  code: string;
  setCode: (code: string) => void;
  appendCode: (newCode: string) => void;
  executeEdits: (edits: any[]) => void;
  editorRef: { current: any };
};

const CodeContext = createContext<CodeContextValue>({
  code: '',
  setCode: () => {},
  appendCode: () => {},
  executeEdits: () => {},
  editorRef: { current: null },
});

const useCode = () => useContext(CodeContext);

const pipecatClient = new PipecatClient({
  transport: new SmallWebRTCTransport(),
  enableMic: true,
  enableCam: false,
});

function LegacyAIInterviewPanel() {
  const client = usePipecatClient();
  const { appendCode, executeEdits } = useCode();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const [isCamEnabled, setIsCamEnabled] = useState(true);
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const codeBufferRef = useRef('');

  useEffect(() => {
    if (client?.state === 'ready') {
      setConnectionStatus('Bot Ready');
    }
  }, [client]);

  useRTVIClientEvent(
    RTVIEvent.Connected,
    useCallback(() => {
      setIsConnected(true);
      setConnectionStatus(client?.state === 'ready' ? 'Bot Ready' : 'Connected');
    }, [client]),
  );

  useRTVIClientEvent(
    RTVIEvent.BotReady,
    useCallback(() => {
      setConnectionStatus('Bot Ready');
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.ServerMessage,
    useCallback(
      (message: any) => {
        if (message.type === 'code_response_chunk') {
          codeBufferRef.current += message.data.code_chunk;
          return;
        }

        if (message.type !== 'code_response_complete') {
          return;
        }

        const trimmedBuffer = codeBufferRef.current.trim();
        codeBufferRef.current = '';

        if (!trimmedBuffer) {
          return;
        }

        if (!trimmedBuffer.startsWith('{') || !trimmedBuffer.endsWith('}')) {
          const newTextMatch = trimmedBuffer.match(/"newText":\s*"([^"]*(?:\\.[^"]*)*)"/g);
          if (newTextMatch) {
            const extractedText = newTextMatch
              .map((match) => {
                const textMatch = match.match(/"newText":\s*"([^"]*(?:\\.[^"]*)*)"/);
                return textMatch ? textMatch[1].replace(/\\n/g, '\n').replace(/\\\\/g, '\\').replace(/\\"/g, '"') : '';
              })
              .join('');
            appendCode(extractedText);
          } else {
            appendCode(trimmedBuffer);
          }
          return;
        }

        try {
          const editData = JSON.parse(trimmedBuffer);

          if (editData.edits && Array.isArray(editData.edits)) {
            executeEdits(editData.edits);
            return;
          }

          if (editData.newText) {
            appendCode(editData.newText);
          } else {
            appendCode(trimmedBuffer);
          }
        } catch (error) {
          console.error('Error parsing buffered JSON:', error);
          const newTextMatch = trimmedBuffer.match(/"newText":\s*"([^"]*(?:\\.[^"]*)*)"/g);
          if (newTextMatch) {
            const extractedText = newTextMatch
              .map((match) => {
                const textMatch = match.match(/"newText":\s*"([^"]*(?:\\.[^"]*)*)"/);
                return textMatch ? textMatch[1].replace(/\\n/g, '\n').replace(/\\\\/g, '\\').replace(/\\"/g, '"') : '';
              })
              .join('');
            appendCode(extractedText);
          } else {
            appendCode(trimmedBuffer);
          }
        }
      },
      [appendCode, executeEdits],
    ),
  );

  useRTVIClientEvent(
    RTVIEvent.BotDisconnected,
    useCallback(() => {
      setIsConnected(false);
      setConnectionStatus('Disconnected');
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.TrackStarted,
    useCallback((track: MediaStreamTrack, participant?: Participant) => {
      if (participant?.local && track.kind === 'video' && userVideoRef.current) {
        userVideoRef.current.srcObject = new MediaStream([track]);
      }
    }, []),
  );

  useRTVIClientEvent(
    RTVIEvent.TrackStopped,
    useCallback((track: MediaStreamTrack, participant?: Participant) => {
      if (participant?.local && track.kind === 'video' && userVideoRef.current) {
        userVideoRef.current.srcObject = null;
      }
    }, []),
  );

  const handleConnect = useCallback(async () => {
    if (!client) {
      return;
    }

    try {
      setConnectionStatus('Connecting...');
      await client.connect({
        connectionUrl: '/api/offer',
      });
    } catch (error) {
      console.error('Connection failed:', error);
      setConnectionStatus('Connection Failed');
    }
  }, [client]);

  const handleDisconnect = useCallback(async () => {
    if (!client) {
      return;
    }

    try {
      await client.disconnect();
      setIsConnected(false);
      setConnectionStatus('Disconnected');
    } catch (error) {
      console.error('Disconnect failed:', error);
    }
  }, [client]);

  const toggleMic = useCallback(() => {
    if (!client) {
      return;
    }

    const newState = !isMicEnabled;
    client.enableMic(newState);
    setIsMicEnabled(newState);
  }, [client, isMicEnabled]);

  const toggleCam = useCallback(() => {
    if (!client) {
      return;
    }

    const newState = !isCamEnabled;
    client.enableCam(newState);
    setIsCamEnabled(newState);
  }, [client, isCamEnabled]);

  return (
    <div className="space-y-5 bg-zinc-950 p-5 text-white">
      <div className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900 p-5 shadow-[0_20px_45px_-35px_rgba(139,92,246,0.8)]">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-[0.65rem] font-medium uppercase tracking-[0.2em] text-violet-300">Live session</p>
            <h3 className="mt-1 text-xl font-semibold tracking-[-0.04em]">AI Interviewer</h3>
          </div>
          <div
            className={`rounded-full border px-3 py-1.5 text-xs font-medium ${
              connectionStatus === 'Bot Ready'
                ? 'border-[#e6ff82]/30 bg-[#e6ff82]/10 text-[#e6ff82]'
                : connectionStatus === 'Connected' || connectionStatus === 'Connecting...'
                  ? 'border-amber-300/30 bg-amber-300/10 text-amber-200'
                  : 'border-white/10 bg-white/5 text-zinc-400'
            }`}
          >
            {connectionStatus}
          </div>
        </div>

        <div className="relative mb-4 flex aspect-video items-center justify-center overflow-hidden rounded-[1.25rem] bg-violet-600 p-5">
          <div className="absolute -right-10 -top-10 h-36 w-36 rounded-full border border-white/20" />
          <div className="relative text-center text-violet-100">
            <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-black text-[#e6ff82] shadow-xl">
              <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <p className="text-sm font-medium">Ready when you are</p>
            <p className="mt-1 text-xs text-violet-200">Live voice feedback enabled</p>
          </div>
        </div>
      </div>

      <div className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">You</h3>
            <p className="mt-1 text-xs text-zinc-500">Camera preview</p>
          </div>
          <Video className="h-4 w-4 text-zinc-500" />
        </div>

        <div className="relative aspect-video overflow-hidden rounded-xl bg-zinc-800">
          <video ref={userVideoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
          <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-16 w-16 items-center justify-center rounded-full bg-zinc-700">
                <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <p className="text-xs">Not connected</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3 rounded-[1.5rem] border border-zinc-800 bg-zinc-900 p-4">
        <div className="flex gap-2">
          <button
            onClick={toggleMic}
            className={`flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition-colors ${
              isMicEnabled ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            {isMicEnabled ? 'Mute mic' : 'Unmute mic'}
          </button>
          <button
            onClick={toggleCam}
            className={`flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition-colors ${
              isCamEnabled ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            {isCamEnabled ? 'Stop camera' : 'Start camera'}
          </button>
        </div>

        {!isConnected ? (
          <button
            onClick={handleConnect}
            disabled={connectionStatus === 'Connecting...'}
            className="w-full rounded-full bg-[#e6ff82] px-4 py-3 text-sm font-semibold text-black transition-transform hover:-translate-y-0.5 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {connectionStatus === 'Connecting...' ? 'Connecting...' : 'Connect'}
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            className="w-full rounded-full bg-red-500/15 px-4 py-3 text-sm font-semibold text-red-200 ring-1 ring-red-400/30 transition-colors hover:bg-red-500/25"
          >
            Disconnect
          </button>
        )}
      </div>

      <PipecatClientAudio />
    </div>
  );
}

void LegacyAIInterviewPanel;

function AIInterviewPanel() {
  const client = usePipecatClient();
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [isMicEnabled, setIsMicEnabled] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const botVideoRef = useRef<HTMLVideoElement>(null);
  const connectionAttemptedRef = useRef(false);

  useRTVIClientEvent(
    RTVIEvent.Connected,
    useCallback(() => {
      setIsConnected(true);
      setConnectionStatus('Connected');
    }, []),
  );

  useRTVIClientEvent(RTVIEvent.BotReady, useCallback(() => setConnectionStatus('Bot Ready'), []));
  useRTVIClientEvent(
    RTVIEvent.BotLlmStarted,
    useCallback(() => setIsThinking(true), []),
  );
  useRTVIClientEvent(
    RTVIEvent.BotLlmStopped,
    useCallback(() => setIsThinking(false), []),
  );
  useRTVIClientEvent(
    RTVIEvent.BotDisconnected,
    useCallback(() => {
      setIsConnected(false);
      setConnectionStatus('Disconnected');
      setIsThinking(false);
    }, []),
  );
  useRTVIClientEvent(
    RTVIEvent.TrackStarted,
    useCallback((track: MediaStreamTrack, participant?: Participant) => {
      if (!participant?.local && track.kind === 'video' && botVideoRef.current) {
        botVideoRef.current.srcObject = new MediaStream([track]);
      }
    }, []),
  );

  const handleConnect = useCallback(async () => {
    if (!client) return;
    try {
      setConnectionStatus('Connecting...');
      const problemSlug = new URLSearchParams(window.location.search).get('slug') || 'two-sum';
      await client.connect({
        webrtcRequestParams: {
          endpoint: '/api/offer',
          requestData: { problemSlug },
        },
      });
    } catch (error) {
      console.error('Connection failed:', error);
      setConnectionStatus('Connection Failed');
    }
  }, [client]);

  useEffect(() => {
    if (!client || connectionAttemptedRef.current || isConnected) return;

    connectionAttemptedRef.current = true;
    void handleConnect();
  }, [client, handleConnect, isConnected]);

  const handleDisconnect = useCallback(async () => {
    if (!client) return;
    await client.disconnect();
    setIsConnected(false);
    setConnectionStatus('Disconnected');
    setIsThinking(false);
  }, [client]);

  const toggleMic = useCallback(() => {
    if (!client || !isConnected) return;
    const nextState = !isMicEnabled;
    client.enableMic(nextState);
    setIsMicEnabled(nextState);
  }, [client, isConnected, isMicEnabled]);

  return (
    <div className="flex h-full items-center gap-3 bg-zinc-950 px-4 py-3 text-white sm:px-5">
      <div className="relative hidden h-16 w-24 shrink-0 overflow-hidden rounded-xl border border-violet-400/30 bg-violet-600 sm:block">
        <video ref={botVideoRef} autoPlay playsInline className="h-full w-full object-cover" />
        <div className="absolute inset-0 grid place-items-center bg-violet-600">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="184"
            height="100"
            viewBox="0 0 184 100"
            aria-label={isThinking ? 'AI is thinking' : 'AI interviewer'}
            role="img"
            className={`h-12 w-20 ${isThinking ? 'thinking-svg' : ''}`}
          >
            <path
              fill="none"
              stroke="#000"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="7"
              d="M96.5 62.5c5.637 3.522 8.581 3.435 12.991-.51 2.548-2.28 5.218-4.473 7.464-7.03 4.298-4.889 4-10.44-.455-14.46-3.5-3.158-9.35-2.568-13.488 1.512-6.546 6.454-13.031 12.970-19.498 19.501-1.589 1.605-3.203 3.087-5.515 3.482-4.569.78-6.932-1.15-7.999-6.495M90 41c-5.635-3.591-8.483-2.921-13.565 1.424-7.553 6.458-13.248 14.803-21.424 20.59C50.829 65.975 46.43 65.675 43 62c-2.596-2.78-3.064-9.425-.444-12.452 2.923-3.377 5.94-6.854 9.536-9.418 3.793-2.705 8.14-2.25 11.908.87"
              className="svg-elem-1"
            />
          </svg>
        </div>
        <span className="absolute bottom-1 left-1.5 text-[9px] font-medium uppercase tracking-wider text-violet-100">Interviewer</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#e6ff82] shadow-[0_0_12px_#e6ff82]" />
          <p className="truncate text-sm font-semibold">AI Interviewer</p>
        </div>
        <p className="mt-1 truncate text-xs text-zinc-500">{isThinking ? 'Thinking...' : isConnected ? 'Live voice feedback enabled' : 'Connecting...'}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className={`hidden rounded-full border px-3 py-2 text-xs font-medium md:block ${
          connectionStatus === 'Bot Ready' ? 'border-[#e6ff82]/30 bg-[#e6ff82]/10 text-[#e6ff82]' :
          connectionStatus === 'Connected' || connectionStatus === 'Connecting...' ? 'border-amber-300/30 bg-amber-300/10 text-amber-200' :
          'border-white/10 bg-white/5 text-zinc-400'
        }`}>{connectionStatus}</span>
        <button onClick={toggleMic} disabled={!isConnected} className={`grid h-10 w-10 place-items-center rounded-full border transition-all disabled:cursor-not-allowed disabled:opacity-40 ${isMicEnabled ? 'border-zinc-700 bg-zinc-800 text-white hover:border-violet-400 hover:bg-zinc-700' : 'border-rose-400/40 bg-rose-400/15 text-rose-200 hover:bg-rose-400/25'}`} aria-label={isMicEnabled ? 'Mute microphone' : 'Unmute microphone'} title={isMicEnabled ? 'Mute microphone' : 'Unmute microphone'}>
          {isMicEnabled ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
        </button>
        {isConnected && (
          <button onClick={handleDisconnect} className="inline-flex h-10 items-center gap-2 rounded-full border border-rose-400/30 bg-rose-400/10 px-4 text-sm font-semibold text-rose-200 transition-all hover:bg-rose-400/20">
            <PhoneOff className="h-4 w-4" /><span className="hidden sm:inline">Disconnect</span>
          </button>
        )}
      </div>
      <PipecatClientAudio />
    </div>
  );
}

function CodeEditor() {
  const { code, setCode, editorRef } = useCode();
  const client = usePipecatClient();
  const debounceTimeoutRef = useRef<number | null>(null);
  const lastSentCodeRef = useRef('');

  const handleEditorDidMount = useCallback(
    (editor: any) => {
      editorRef.current = editor;

      editor.onDidChangeModelContent(() => {
        const currentCode = editor.getValue();

        if (debounceTimeoutRef.current) {
          clearTimeout(debounceTimeoutRef.current);
        }

        debounceTimeoutRef.current = window.setTimeout(() => {
          if (currentCode !== lastSentCodeRef.current && currentCode.trim() !== '') {
            client?.sendClientMessage('send_code', {
              code: currentCode,
              timestamp: Date.now(),
            });

            lastSentCodeRef.current = currentCode;
          }
        }, 1500);
      });
    },
    [editorRef, client],
  );

  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="h-full bg-[#111113]">
      <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-5">
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center gap-2 text-sm font-semibold text-white">
            <Code2 className="h-4 w-4 text-violet-400" />
            Code workspace
          </span>
          <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">interview.js</span>
        </div>
        <button
          onClick={() => {
            setCode('');
            lastSentCodeRef.current = '';
          }}
          className="inline-flex items-center gap-2 rounded-full border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-300 transition-colors hover:border-violet-400 hover:text-white"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Reset
        </button>
      </div>
      <div className="h-[calc(100%-3.5rem)] p-4">
        <Editor
          height="100%"
          defaultLanguage="javascript"
          value={code}
          onChange={(value) => setCode(value || '')}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            fontSize: 14,
            fontFamily: 'Consolas, "Courier New", monospace',
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            tabSize: 2,
          }}
        />
      </div>
    </div>
  );
}

function Interviewer() {
  const [problem, setProblem] = useState<GroundedProblem | null>(null);
  const [code, setCode] = useState(`// Welcome to your AI Mock DSA Interview\n// Waiting for problem from interviewer...\n\n`);
  const editorRef = useRef<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  }, []);

  useEffect(() => {
    const slug = new URLSearchParams(window.location.search).get('slug') || 'two-sum';
    fetch(`/api/problem/${encodeURIComponent(slug)}`)
      .then((response) => response.ok ? response.json() : null)
      .then((data) => setProblem(data || {
        id: '1', source: 'leetcode', title: 'Two Sum', difficulty: 'Easy',
        description: 'Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.',
        constraints: ['2 <= nums.length <= 10^4', 'Exactly one solution exists.'],
        examples: [{ input: 'nums = [2,7,11,15], target = 9', output: '[0,1]', explanation: 'The two numbers add up to the target.' }],
        time_target: 'O(n)', space_target: 'O(n)',
      }))
      .catch(() => setProblem({
        id: '1', source: 'leetcode', title: 'Two Sum', difficulty: 'Easy',
        description: 'Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target.',
        constraints: ['2 <= nums.length <= 10^4', 'Exactly one solution exists.'], examples: [], time_target: 'O(n)', space_target: 'O(n)',
      }));
  }, []);

  const appendCode = useCallback((newCode: string) => {
    setCode((prevCode) => prevCode + newCode);
  }, []);

  const executeEdits = useCallback(
    (edits: any[]) => {
      if (!editorRef.current) {
        const allNewText = edits.map((edit) => edit.newText).join('');
        appendCode(allNewText);
        return;
      }

      try {
        const monacoEdits = edits.map((edit, index) => ({
          id: `edit-${Date.now()}-${index}`,
          range: {
            startLineNumber: edit.range.start,
            startColumn: 1,
            endLineNumber: edit.range.end,
            endColumn: Number.MAX_VALUE,
          },
          text: edit.newText,
          forceMoveMarkers: true,
        }));

        editorRef.current.executeEdits('ai-interview-bot', monacoEdits);

        const newValue = editorRef.current.getValue();
        setCode(newValue);
      } catch (error) {
        console.error('Error executing Monaco edits:', error);
        const allNewText = edits.map((edit) => edit.newText).join('');
        appendCode(allNewText);
      }
    },
    [appendCode],
  );

  const codeContextValue: CodeContextValue = {
    code,
    setCode,
    appendCode,
    executeEdits,
    editorRef,
  };

  return (
    <CodeContext.Provider value={codeContextValue}>
      <PipecatClientProvider client={pipecatClient}>
        <div className="h-[100dvh] overflow-hidden bg-zinc-950 p-3 text-white transition-colors sm:p-4">
          <div className="flex h-14 items-center justify-between rounded-t-[1.5rem] border border-zinc-800 bg-zinc-900 px-4 text-white sm:px-6">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => navigate('/interviews')}
                className="grid h-9 w-9 place-items-center rounded-full border border-zinc-700 transition-colors hover:border-violet-400 hover:text-violet-300"
                aria-label="Back to interviews"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
              <div>
                <p className="text-[0.65rem] font-medium uppercase tracking-[0.2em] text-violet-300">PrepareIt AI</p>
                <h1 className="text-lg font-semibold tracking-[-0.03em]">Live interview studio</h1>
              </div>
            </div>
            <span className="hidden text-xs text-zinc-400 sm:inline">DSA Expert - 45 min</span>
          </div>

        <div className="flex h-[calc(100dvh-4.5rem)] min-h-0 flex-col overflow-hidden rounded-b-[1.5rem] border border-t-0 border-zinc-800 bg-black shadow-[0_24px_70px_-38px_rgba(0,0,0,0.55)] lg:flex-row">
            <div className="h-[38%] min-h-0 w-full shrink-0 border-b border-zinc-800 lg:h-full lg:w-[40%] lg:shrink lg:border-b-0 lg:border-r"><ProblemPanel problem={problem} /></div>
            <div className="flex h-[62%] min-h-0 w-full flex-1 flex-col lg:h-full lg:w-[60%]"><div className="min-h-0 flex-1"><CodeEditor /></div><div className="h-[5.5rem] shrink-0 border-t border-zinc-800"><AIInterviewPanel /></div></div>
          </div>
        </div>
      </PipecatClientProvider>
    </CodeContext.Provider>
  );
}

export default Interviewer;
