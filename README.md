# PrepareIt

**Practice technical interviews with a real-time AI interviewer.** PrepareIt pairs a voice conversation with a coding workspace, so candidates can talk through an approach, write code, and get feedback in one session.

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-19-149eca?logo=react&logoColor=white" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white" />
  <img alt="Pipecat" src="https://img.shields.io/badge/Voice-Pipecat-6554c0" />
</p>

## What it does

- Runs structured data structures and algorithms mock interviews with an AI interviewer.
- Streams speech through Deepgram, Google Gemini, and Cartesia using Pipecat and WebRTC.
- Gives candidates a Monaco code editor and streams code updates to the interviewer.
- Grounds practice questions in LeetCode problem data, with local fallback problems when a lookup is unavailable.
- Uses Clerk for sign-in and provides a dashboard to start an interview.

## How it fits together

| Directory | Responsibility |
| --- | --- |
| `client-custom/` | React, TypeScript, Vite frontend, authentication, interview dashboard, and coding workspace |
| `server/` | Pipecat voice bot, interview state and orchestration, problem lookup, and evaluation |

The Vite development server proxies `/api` requests to the Pipecat server on `localhost:7860`. Audio is carried over WebRTC.

## Requirements

- Node.js 20+ and npm
- Python 3.10+
- API credentials for Deepgram, Google AI, and Cartesia
- A Clerk application and its frontend publishable key

## Run locally

Clone the repository, then configure the server:

```bash
cd server
cp .env.example .env
```

Add your service credentials to `server/.env`. Then install the Python dependencies and start the bot:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux:      source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Alternatively, install [uv](https://docs.astral.sh/uv/) and use `uv sync` followed by `uv run bot.py`.

In a second terminal, configure and start the web client:

```bash
cd client-custom
cp .env.example .env
npm ci
npm run dev
```

Set `VITE_CLERK_PUBLISHABLE_KEY` in `client-custom/.env`, then open the local URL printed by Vite (normally `http://localhost:5173`). Allow microphone access before starting an interview.

## Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `DEEPGRAM_API_KEY` | Server | Speech recognition |
| `CARTESIA_API_KEY` | Server | Text-to-speech |
| `GOOGLE_API_KEY` | Server | Gemini interview and evaluation |
| `VITE_CLERK_PUBLISHABLE_KEY` | Client | Clerk sign-in |

Templates are in `server/.env.example` and `client-custom/.env.example`. Keep real credentials in local `.env` files; they are ignored by Git.

## Development

```bash
cd client-custom
npm run lint
npm run build
```

The server dependencies and lockfile are maintained in `server/`; run the bot from that directory so it loads `server/.env`.

## Notes

- The interview screen needs a working microphone and valid provider credentials.
- The backend fetches problem details from LeetCode when available and includes fallback examples for common problems.
- This project is a practice tool; interview evaluations are AI-generated feedback, not hiring decisions.
