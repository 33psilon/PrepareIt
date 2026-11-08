#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os
import sys
import asyncio
from contextlib import asynccontextmanager

if sys.platform == "win32": # windows utf 8 reconfig
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesAppendFrame,
    LLMTextFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import (
    RTVIClientMessageFrame,
    RTVIConfig,
    RTVIObserver,
    RTVIProcessor,
    RTVIServerMessageFrame,
)
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)

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

load_dotenv(override=True)

logger.remove() #logger config to show only errors, debriefs, and LLM responses
logger.add(
    sys.stderr,
    filter=lambda record: record["level"].no >= 40
    or "LLM Response:" in record["message"]
    or "[Transcript]" in record["message"]
    or "Debrief" in record["message"],
    format="{time:HH:mm:ss} | {level} | {message}",
)


class CodeAwareTranscriptProcessor(FrameProcessor):
    def __init__(self, state: InterviewState, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self._current_code = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, RTVIClientMessageFrame):
            msg_type = getattr(frame, "type", None) or (
                frame.data.get("type") if hasattr(frame, "data") and isinstance(frame.data, dict) else None
            )
            if msg_type == "send_code":
                payload = frame.data.get("data", frame.data) if hasattr(frame, "data") and isinstance(frame.data, dict) else {}
                code = payload.get("code", "") if isinstance(payload, dict) else ""
                self._current_code = code
                self.state.latest_code = code
                logger.info(f"Received updated candidate code snapshot ({len(self._current_code)} chars)")
                return

        if isinstance(frame, TranscriptionFrame) and not isinstance(frame, InterimTranscriptionFrame):
            if self._current_code:
                enhanced_content = f"Voice: {frame.text}\n\nCode:\n```\n{self._current_code}\n```"
                enhanced_frame = TranscriptionFrame(
                    text=enhanced_content,
                    timestamp=frame.timestamp,
                    user_id=frame.user_id,
                )
                await self.push_frame(enhanced_frame, direction)
            else:
                await self.push_frame(frame, direction)
            return

        await self.push_frame(frame, direction)


class ResponseSeparatorProcessor(FrameProcessor):
    """Route spoken and code portions of an LLM response to their consumers."""

    def __init__(self, rtvi=None, **kwargs):
        super().__init__(**kwargs)
        self.rtvi = rtvi
        self.audio_marker = "🔊"
        self.code_marker = "💻"
        self.reset_state()

    def reset_state(self):
        self.state = "notDecided"
        self._code_buffer = ""

    async def _emit_code_chunk(self, chunk: str, direction: FrameDirection = FrameDirection.DOWNSTREAM):
        if not chunk:
            return
        self._code_buffer += chunk
        frame = RTVIServerMessageFrame(
            data={
                "type": "code_response_chunk",
                "data": {"code_chunk": chunk},
            }
        )
        if self.rtvi is not None:
            await self.rtvi.push_frame(frame)
        else:
            await self.push_frame(frame, direction)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMFullResponseStartFrame):
            self.reset_state()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, LLMTextFrame):
            logger.debug(f"LLM Response chunk: {frame.text!r}, Current state: {self.state}")

            if self.state == "notDecided":
                has_audio = self.audio_marker in frame.text
                has_code = self.code_marker in frame.text

                if has_audio and has_code:
                    audio_pos = frame.text.find(self.audio_marker)
                    code_pos = frame.text.find(self.code_marker)

                    if audio_pos < code_pos:
                        parts = frame.text.split(self.audio_marker, 1)
                        remaining = parts[1] if len(parts) > 1 else ""
                        code_parts = remaining.split(self.code_marker, 1)

                        audio_text = code_parts[0].strip()
                        if audio_text:
                            await self.push_frame(LLMTextFrame(text=audio_text), direction)

                        if len(code_parts) > 1:
                            code_text = code_parts[1].strip()
                            await self._emit_code_chunk(code_text, direction)

                        self.state = "code"
                    else:
                        parts = frame.text.split(self.code_marker, 1)
                        remaining = parts[1] if len(parts) > 1 else ""
                        audio_parts = remaining.split(self.audio_marker, 1)

                        code_text = audio_parts[0].strip()
                        await self._emit_code_chunk(code_text, direction)

                        if len(audio_parts) > 1:
                            audio_text = audio_parts[1].strip()
                            if audio_text:
                                await self.push_frame(LLMTextFrame(text=audio_text), direction)

                        self.state = "audio"

                elif has_audio:
                    self.state = "audio"
                    clean_text = frame.text.replace(self.audio_marker, "").strip()
                    if clean_text:
                        await self.push_frame(LLMTextFrame(text=clean_text), direction)

                elif has_code:
                    self.state = "code"
                    clean_text = frame.text.replace(self.code_marker, "").strip()
                    await self._emit_code_chunk(clean_text, direction)

                else:
                    self.state = "audio"
                    await self.push_frame(LLMTextFrame(text=frame.text), direction)

            elif self.state == "audio":
                if self.code_marker in frame.text:
                    parts = frame.text.split(self.code_marker, 1)

                    audio_part = parts[0].strip()
                    if audio_part:
                        await self.push_frame(LLMTextFrame(text=audio_part), direction)

                    if len(parts) > 1:
                        code_part = parts[1].strip()
                        await self._emit_code_chunk(code_part, direction)

                    self.state = "code"
                else:
                    await self.push_frame(LLMTextFrame(text=frame.text), direction)

            elif self.state == "code":
                if self.audio_marker in frame.text:
                    parts = frame.text.split(self.audio_marker, 1)

                    code_part = parts[0].strip()
                    await self._emit_code_chunk(code_part, direction)

                    if len(parts) > 1:
                        audio_part = parts[1].strip()
                        if audio_part:
                            await self.push_frame(LLMTextFrame(text=audio_part), direction)

                    self.state = "audio"
                else:
                    await self._emit_code_chunk(frame.text, direction)

        elif isinstance(frame, LLMFullResponseEndFrame):
            if self.state == "code" or bool(self._code_buffer.strip()):
                complete_frame = RTVIServerMessageFrame(
                    data={
                        "type": "code_response_complete",
                        "data": {"status": "finished"},
                    }
                )
                if self.rtvi is not None:
                    await self.rtvi.push_frame(complete_frame)
                else:
                    await self.push_frame(complete_frame, direction)
            self.reset_state()
            await self.push_frame(frame, direction)
        else:
            await self.push_frame(frame, direction)


async def run_bot(transport: BaseTransport):
    logger.info("Initializing technical interviewer bot session")

    request_data = getattr(transport, "request_data", None) or {}
    problem_slug = request_data.get("problemSlug") if isinstance(request_data, dict) else None
    problem_slug = str(problem_slug or os.getenv("PROBLEM_SLUG", "two-sum")).strip().lower()
    problem = await asyncio.to_thread(ProblemService.fetch, problem_slug)
    logger.info(f"Loaded grounded problem: {problem.title} ({problem.difficulty})")

    state = InterviewState(
        session_id=os.getenv("SESSION_ID", "local-session"),
        problem_title=problem.title,
        problem_description="\n\n".join(
            section
            for section in (
                problem.description,
                "Examples:\n"
                + "\n".join(
                    f"Example {index}: Input: {example.get('input', '')}; "
                    f"Output: {example.get('output', '')}"
                    + (f"; Explanation: {example['explanation']}" if example.get("explanation") else "")
                    for index, example in enumerate(problem.examples, start=1)
                )
                if problem.examples
                else "",
                "Constraints:\n" + "\n".join(problem.constraints) if problem.constraints else "",
            )
            if section
        ),
    )
    orchestrator = OrchestratorAgent(state)

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY", "").strip(),
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY", "").strip(),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",
    )

    system_instruction = (
        "You are an expert, supportive AI interviewer conducting a real-time Technical Data Structures & Algorithms (DSA) interview. "
        "Maintain a professional, conversational tone. "
        "Strictly follow the interview phases: INTRO -> CLARIFICATION -> CODING <-> HINTING -> WRAPUP.\n\n"
        "Output Format Rules:\n"
        "1. Conversational / Spoken Speech: Mark with 🔊 emoji. This will be spoken aloud to the candidate via TTS.\n"
        "2. Problem Statements / Code / Edits: Mark with 💻 emoji. Put all code, problem constraints, or Monaco editor edits inside 💻.\n"
        "3. For code modifications, ALWAYS provide valid JSON with: "
        '{"edits": [{"range": {"start": <1-based line>, "end": <1-based line>}, "newText": "<code replacement>"}]}\n'
        "4. Use the advance_interview_phase tool when transitioning phases.\n"
        "5. Use the request_code_review tool when candidate asks for feedback or to review current code.\n"
        "6. Use the record_hint_given tool whenever you give a hint."
    )

    llm = GoogleLLMService(
        api_key=os.getenv("GOOGLE_API_KEY", "").strip(),
        model="gemini-3.6-flash",
        system_instruction=system_instruction,
        tools=interview_tools(),
    )
    llm.register_function("advance_interview_phase", orchestrator.advance_interview_phase)
    llm.register_function("request_code_review", orchestrator.request_code_review)
    llm.register_function("record_hint_given", orchestrator.record_hint_given)

    context = OpenAILLMContext(
        [
            {
                "role": "system",
                "content": system_instruction,
            }
        ]
    )
    context_aggregator = llm.create_context_aggregator(context)
    user_aggregator = context_aggregator.user()
    assistant_aggregator = context_aggregator.assistant()

    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
    response_separator = ResponseSeparatorProcessor(rtvi)
    pipeline = Pipeline(
        [
            transport.input(),
            rtvi,
            stt,
            CodeAwareTranscriptProcessor(state),
            orchestrator,
            user_aggregator,
            llm,
            response_separator,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("RTVI client is ready; sending bot-ready signal")
        await rtvi.set_bot_ready()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, webrtc_connection):
        logger.info("Candidate connected via WebRTC")
        await task.queue_frames(
            [
                LLMMessagesAppendFrame(
                    [
                        {
                            "role": "user",
                            "content": (
                                f"The candidate has connected. The problem for today is {problem.title}. "
                                "Introduce yourself warmly as the technical interviewer, set expectations for the interview, "
                                "and invite them to begin when ready."
                            ),
                        }
                    ],
                    run_llm=True,
                )
            ]
        )

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, webrtc_connection):
        logger.info("Candidate disconnected. Triggering asynchronous debrief evaluator.")
        transcript_text = "\n".join(orchestrator.transcript)
        asyncio.create_task(
            run_debrief_evaluator(
                transcript=transcript_text,
                final_code=state.latest_code,
                problem_desc=problem.description,
            )
        )
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot runner."""
    transport = SmallWebRTCTransport(
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
        webrtc_connection=runner_args.webrtc_connection,
    )
    transport.request_data = getattr(runner_args.webrtc_connection, "request_data", None)

    await run_bot(transport)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    webrtc_handler = SmallWebRTCRequestHandler(host=host)

    @asynccontextmanager
    async def lifespan(_app):
        yield
        await webrtc_handler.close()

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/problems")
    def get_problems():
        return ProblemService.catalog()

    @app.get("/api/problem/{slug}")
    def get_problem(slug: str):
        try:
            return ProblemService.fetch(slug).model_dump()
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/offer")
    async def offer(request: Request, background_tasks: BackgroundTasks):
        payload = await request.json()
        offer_request = SmallWebRTCRequest(
            sdp=payload["sdp"],
            type=payload["type"],
            pc_id=payload.get("pc_id"),
            restart_pc=payload.get("restart_pc"),
            request_data=payload.get("requestData", payload.get("request_data")),
        )

        async def start_bot(connection):
            connection.request_data = offer_request.request_data
            background_tasks.add_task(
                bot,
                SmallWebRTCRunnerArguments(webrtc_connection=connection),
            )

        return await webrtc_handler.handle_web_request(
            request=offer_request,
            webrtc_connection_callback=start_bot,
        )

    uvicorn.run(app, host=host, port=port)
