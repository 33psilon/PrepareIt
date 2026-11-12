"""FastAPI and Pipecat entry point for PrepareIt's real-time interview bot."""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    Frame,
    InterimTranscriptionFrame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesAppendFrame,
    LLMTextFrame,
    TranscriptionFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import (
    RTVIClientMessageFrame,
    RTVIObserver,
    RTVIProcessor,
)
from pipecat.runner.types import SmallWebRTCRunnerArguments
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.request_handler import (
    IceCandidate,
    SmallWebRTCPatchRequest,
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

try:
    from .agents.evaluator import run_debrief_evaluator
    from .orchestrator import OrchestratorAgent, interview_tools
    from .services.problem_service import ProblemService
    from .state import InterviewState
except ImportError:
    from agents.evaluator import run_debrief_evaluator
    from orchestrator import OrchestratorAgent, interview_tools
    from services.problem_service import ProblemService
    from state import InterviewState

load_dotenv(override=False)

logger.remove()
logger.add(
    sys.stderr,
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="{time:HH:mm:ss} | {level} | {message}",
    colorize=False,
    backtrace=False,
    diagnose=False,
)

AUDIO_MARKER = "🔊"
CODE_MARKER = "💻"
DEFAULT_CARTESIA_VOICE = "71a7ad14-091c-4e8e-a314-022ece01c121"


def _provider_keys() -> dict[str, str]:
    """Read credentials without ever logging their values."""
    return {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip(),
        "DEEPGRAM_API_KEY": os.getenv("DEEPGRAM_API_KEY", "").strip(),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY", "").strip(),
    }


def _missing_provider_keys() -> list[str]:
    keys = _provider_keys()
    return [
        name
        for name, value in keys.items()
        if not value or value.lower().startswith("your_") or "placeholder" in value.lower()
    ]


class CodeAwareTranscriptProcessor(FrameProcessor):
    """Attach the latest editor snapshot to each final speech transcription."""

    def __init__(self, state: InterviewState, **kwargs: Any):
        super().__init__(**kwargs)
        self.state = state

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, RTVIClientMessageFrame) and frame.type == "send_code":
            message_data = frame.data if isinstance(frame.data, dict) else {}
            payload = message_data.get("data", message_data)
            code = payload.get("code") if isinstance(payload, dict) else None
            if isinstance(code, str):
                self.state.latest_code = code
                logger.debug("Received editor snapshot ({} characters)", len(code))
            return

        if isinstance(frame, TranscriptionFrame) and not isinstance(
            frame, InterimTranscriptionFrame
        ):
            if self.state.latest_code:
                frame = TranscriptionFrame(
                    text=(
                        f"Voice: {frame.text}\n\n"
                        f"Current candidate code:\n```\n{self.state.latest_code}\n```"
                    ),
                    timestamp=frame.timestamp,
                    user_id=frame.user_id,
                )

        await self.push_frame(frame, direction)


class ResponseSeparatorProcessor(FrameProcessor):
    """Send spoken text to TTS and code-only text to the editor over RTVI."""

    def __init__(
        self,
        rtvi: RTVIProcessor,
        transcript: list[str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.rtvi = rtvi
        self._mode: str | None = None
        self._response_text: list[str] = []
        self.transcript = transcript

    async def _emit_audio(self, text: str, direction: FrameDirection):
        if text.strip():
            await self.push_frame(LLMTextFrame(text=text.strip()), direction)

    async def _emit_code(self, text: str):
        if not text:
            return
        await self.rtvi.send_server_message(
            {
                "type": "code_response_chunk",
                "data": {"code_chunk": text},
            }
        )

    async def _route_text(self, text: str, direction: FrameDirection):
        remaining = text

        while remaining:
            audio_pos = remaining.find(AUDIO_MARKER)
            code_pos = remaining.find(CODE_MARKER)
            markers = [(audio_pos, "audio", AUDIO_MARKER), (code_pos, "code", CODE_MARKER)]
            markers = [marker for marker in markers if marker[0] >= 0]

            if not markers:
                mode = self._mode or "audio"
                if mode == "audio":
                    await self._emit_audio(remaining, direction)
                else:
                    await self._emit_code(remaining)
                self._mode = mode
                return

            marker_pos, marker_mode, marker_text = min(markers, key=lambda marker: marker[0])
            preceding = remaining[:marker_pos]
            current_mode = self._mode or "audio"
            if current_mode == "audio":
                await self._emit_audio(preceding, direction)
            else:
                await self._emit_code(preceding)

            self._mode = marker_mode
            remaining = remaining[marker_pos + len(marker_text) :]

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMFullResponseStartFrame):
            self._mode = None
            self._response_text = []
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, LLMTextFrame):
            self._response_text.append(frame.text)
            await self._route_text(frame.text, direction)
            return

        if isinstance(frame, LLMFullResponseEndFrame):
            response = (
                "".join(self._response_text)
                .replace(AUDIO_MARKER, "")
                .replace(CODE_MARKER, "")
                .strip()
            )
            if self.transcript is not None and response:
                self.transcript.append(f"Interviewer: {response}")
                logger.info(
                    "[Transcript] Interviewer response recorded ({} characters)",
                    len(response),
                )
            self._response_text = []
            if self._mode == "code":
                await self.rtvi.send_server_message(
                    {
                        "type": "code_response_complete",
                        "data": {"status": "finished"},
                    }
                )
            self._mode = None

        await self.push_frame(frame, direction)


class InterviewPromptProcessor(FrameProcessor):
    """Refresh phase-specific system guidance immediately before each LLM call."""

    def __init__(self, orchestrator: OrchestratorAgent, **kwargs: Any):
        super().__init__(**kwargs)
        self.orchestrator = orchestrator

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, LLMContextFrame):
            messages = frame.context.get_messages()
            system_message = {"role": "system", "content": self.orchestrator.system_prompt()}
            if messages and isinstance(messages[0], dict) and messages[0].get("role") == "system":
                messages[0] = system_message
            else:
                messages.insert(0, system_message)
            frame.context.set_messages(messages)
        await self.push_frame(frame, direction)


async def run_bot(transport: BaseTransport):
    """Build and run one Pipecat pipeline for an already-negotiated peer."""
    request_data = getattr(transport, "request_data", None)
    request_data = request_data if isinstance(request_data, dict) else {}
    requested_slug = request_data.get("problemSlug") or request_data.get("problem_slug")
    problem_slug = str(requested_slug or "random-amazon-sde1").strip().lower()

    keys = _provider_keys()
    missing = _missing_provider_keys()
    if missing:
        raise RuntimeError(
            "Missing required voice provider credentials: " + ", ".join(missing)
        )

    logger.info("Starting interview session for problem slug {}", problem_slug)
    problem = await asyncio.to_thread(ProblemService.fetch, problem_slug)
    logger.info("Loaded interview problem: {} ({})", problem.title, problem.difficulty)

    sections = [problem.description]
    if problem.examples:
        examples = []
        for index, example in enumerate(problem.examples, start=1):
            item = (
                f"Example {index}\n"
                f"Input: {example.get('input', '')}\n"
                f"Output: {example.get('output', '')}"
            )
            if example.get("explanation"):
                item += f"\nExplanation: {example['explanation']}"
            examples.append(item)
        sections.append("Examples:\n" + "\n\n".join(examples))
    if problem.constraints:
        sections.append("Constraints:\n" + "\n".join(f"- {item}" for item in problem.constraints))

    state = InterviewState(
        session_id=str(request_data.get("sessionId") or uuid.uuid4()),
        problem_title=problem.title,
        problem_description="\n\n".join(sections),
    )
    orchestrator = OrchestratorAgent(state)

    stt = DeepgramSTTService(
        api_key=keys["DEEPGRAM_API_KEY"],
        settings=DeepgramSTTService.Settings(
            model=os.getenv("DEEPGRAM_MODEL", "nova-3"),
            language=os.getenv("DEEPGRAM_LANGUAGE", "en-US"),
            interim_results=True,
            smart_format=True,
            punctuate=True,
            utterance_end_ms=1000,
        ),
    )
    tts = CartesiaTTSService(
        api_key=keys["CARTESIA_API_KEY"],
        settings=CartesiaTTSService.Settings(
            model=os.getenv("CARTESIA_MODEL", "sonic-3.6"),
            voice=os.getenv("CARTESIA_VOICE_ID", DEFAULT_CARTESIA_VOICE),
        ),
    )

    system_instruction = (
        "You are an expert, supportive interviewer conducting a real-time Amazon SDE I "
        "data-structures and algorithms interview. Keep a professional, conversational tone. "
        "Follow the interview phases: INTRO, CLARIFICATION, CODING, HINTING, and WRAPUP.\n\n"
        f"The grounded problem is {problem.title}. Use only its supplied statement, examples, "
        "and constraints. Do not replace it with another problem.\n\n"
        f"Prefix spoken words with {AUDIO_MARKER}; they will be sent to speech synthesis. "
        f"Prefix problem statements, code, and editor edits with {CODE_MARKER}; they will be "
        "shown in the editor and will not be spoken. For code edits, output valid JSON in the "
        'form {"edits":[{"range":{"start":1,"end":1},"newText":"replacement"}]}. '
        "Use advance_interview_phase for phase changes, request_code_review for code review, "
        "and record_hint_given whenever you provide a hint."
    )

    llm = GoogleLLMService(
        api_key=keys["GOOGLE_API_KEY"],
        settings=GoogleLLMService.Settings(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            system_instruction=system_instruction,
            max_tokens=4096,
            temperature=0.3,
        ),
        tools=interview_tools(),
    )
    llm.register_function("advance_interview_phase", orchestrator.advance_interview_phase)
    llm.register_function("request_code_review", orchestrator.request_code_review)
    llm.register_function("record_hint_given", orchestrator.record_hint_given)

    context = LLMContext()
    context_aggregators = LLMContextAggregatorPair(context)
    user_aggregator = context_aggregators.user()
    assistant_aggregator = context_aggregators.assistant()
    rtvi = RTVIProcessor()

    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            CodeAwareTranscriptProcessor(state),
            orchestrator,
            user_aggregator,
            InterviewPromptProcessor(orchestrator),
            llm,
            ResponseSeparatorProcessor(rtvi, transcript=orchestrator.transcript),
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    task = PipelineTask(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(processor: RTVIProcessor):
        logger.info("RTVI client handshake complete; marking bot ready")
        await processor.set_bot_ready()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(_transport, _webrtc_connection):
        logger.info("WebRTC media connection established")
        await task.queue_frames(
            [
                LLMMessagesAppendFrame(
                    [
                        {
                            "role": "user",
                            "content": (
                                "The candidate has connected. Introduce yourself warmly, briefly "
                                "explain the interview format, and ask whether they are ready."
                            ),
                        }
                    ],
                    run_llm=True,
                )
            ]
        )

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(_transport, _webrtc_connection):
        logger.info("WebRTC client disconnected; stopping the interview pipeline")
        transcript = "\n".join(orchestrator.transcript)
        debrief_task = asyncio.create_task(
            run_debrief_evaluator(
                transcript=transcript,
                final_code=state.latest_code,
                problem_desc=problem.description,
            ),
            name=f"debrief:{state.session_id}",
        )
        debrief_task.add_done_callback(_log_task_failure)
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)


async def bot(runner_args: SmallWebRTCRunnerArguments):
    connection = runner_args.webrtc_connection
    transport = SmallWebRTCTransport(
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        webrtc_connection=connection,
    )
    transport.request_data = getattr(connection, "request_data", None)
    logger.info("Starting Pipecat pipeline for peer {}", getattr(connection, "pc_id", "unknown"))
    await run_bot(transport)


def _log_task_failure(task: asyncio.Task):
    if task.cancelled():
        return
    error = task.exception()
    if error:
        logger.opt(exception=(type(error), error, error.__traceback__)).error(
            "Background task {} failed", task.get_name()
        )


def create_app() -> FastAPI:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    webrtc_handler = SmallWebRTCRequestHandler(host=host)
    bot_tasks: dict[str, asyncio.Task] = {}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.webrtc_handler = webrtc_handler
        app.state.bot_tasks = bot_tasks
        logger.info("PrepareIt voice backend starting on {}:{}", host, port)
        yield
        for task in tuple(bot_tasks.values()):
            if not task.done():
                task.cancel()
        if bot_tasks:
            await asyncio.gather(*bot_tasks.values(), return_exceptions=True)
        await webrtc_handler.close()
        logger.info("PrepareIt voice backend stopped")

    app = FastAPI(lifespan=lifespan)
    app.state.webrtc_handler = webrtc_handler
    app.state.bot_tasks = bot_tasks
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        missing = _missing_provider_keys()
        return JSONResponse(
            status_code=503 if missing else 200,
            content={
                "status": "degraded" if missing else "ok",
                "providers": {
                    "google": "configured" if "GOOGLE_API_KEY" not in missing else "missing",
                    "deepgram": "configured" if "DEEPGRAM_API_KEY" not in missing else "missing",
                    "cartesia": "configured" if "CARTESIA_API_KEY" not in missing else "missing",
                },
                "missing": missing,
            },
        )

    @app.get("/api/problems")
    async def get_problems():
        return ProblemService.catalog()

    @app.get("/api/problem/{slug}")
    async def get_problem(slug: str):
        try:
            problem = await asyncio.to_thread(ProblemService.fetch, slug)
            return problem.model_dump()
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/offer")
    async def offer(request: Request):
        missing = _missing_provider_keys()
        if missing:
            raise HTTPException(
                status_code=503,
                detail="Configure required voice services before connecting: "
                + ", ".join(missing),
            )

        try:
            payload = await request.json()
        except (ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail="Request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Offer request must be a JSON object")

        try:
            offer_request = SmallWebRTCRequest.from_dict(payload)
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=f"Invalid WebRTC offer: {error}") from error
        if offer_request.type != "offer" or not offer_request.sdp:
            raise HTTPException(status_code=400, detail="A non-empty WebRTC offer is required")

        async def start_bot(connection):
            connection.request_data = offer_request.request_data
            peer_id = str(connection.pc_id)
            active = bot_tasks.get(peer_id)
            if active and not active.done():
                logger.warning("A bot pipeline is already active for peer {}", peer_id)
                return
            task = asyncio.create_task(
                bot(SmallWebRTCRunnerArguments(webrtc_connection=connection)),
                name=f"interview:{peer_id}",
            )
            bot_tasks[peer_id] = task

            def finish(finished_task: asyncio.Task):
                if bot_tasks.get(peer_id) is finished_task:
                    bot_tasks.pop(peer_id, None)
                _log_task_failure(finished_task)

            task.add_done_callback(finish)

        try:
            return await webrtc_handler.handle_web_request(
                request=offer_request,
                webrtc_connection_callback=start_bot,
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.opt(exception=True).error("Failed to create WebRTC offer answer")
            raise HTTPException(status_code=500, detail="Could not initialize WebRTC session") from error

    @app.patch("/api/offer")
    async def patch_offer(request: Request):
        try:
            payload = await request.json()
        except (ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail="Request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="ICE update must be a JSON object")

        peer_id = payload.get("pc_id", payload.get("pcId"))
        candidate_payloads = payload.get("candidates", [])
        if not isinstance(peer_id, str) or not peer_id:
            raise HTTPException(status_code=400, detail="ICE update is missing pc_id")
        if not isinstance(candidate_payloads, list):
            raise HTTPException(status_code=400, detail="ICE candidates must be a list")

        try:
            candidates = []
            for item in candidate_payloads:
                if not isinstance(item, dict):
                    raise ValueError("Each ICE candidate must be an object")
                candidate = item.get("candidate") or ""
                if not isinstance(candidate, str):
                    raise ValueError("ICE candidate must be text")
                mid = item.get("sdp_mid", item.get("sdpMid")) or ""
                line_index = item.get("sdp_mline_index", item.get("sdpMLineIndex", 0))
                candidates.append(
                    IceCandidate(
                        candidate=candidate,
                        sdp_mid=str(mid),
                        sdp_mline_index=int(line_index or 0),
                    )
                )
            patch_request = SmallWebRTCPatchRequest(pc_id=peer_id, candidates=candidates)
        except (TypeError, ValueError) as error:
            raise HTTPException(status_code=400, detail=f"Invalid ICE candidate update: {error}") from error

        try:
            await webrtc_handler.handle_patch_request(patch_request)
        except HTTPException:
            raise
        except Exception as error:
            logger.opt(exception=True).error("Failed to apply ICE candidates for peer {}", peer_id)
            raise HTTPException(status_code=500, detail="Could not apply ICE candidates") from error
        return {"status": "success"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "7860")))
