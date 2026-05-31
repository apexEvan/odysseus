# Odysseus

![Odysseus](docs/odysseus.jpg)

Odysseus is a self-hosted AI workspace for chat, agents, documents, research,
model comparison, memory, email, calendar, and local model management. It is
designed to run on your own hardware with your own data, while still feeling
approachable for people who are not already deep in the self-hosting world.

The fastest way to try it is the guided bootstrap:

```bash
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
./scripts/bootstrap --start
```

The bootstrap creates a project-local Python environment, installs dependencies
there, chooses an available local port, detects common local LLM backends, and
prints the URL to open in your browser.

After setup, start Odysseus from the terminal with:

```bash
./scripts/start
```

## Features
- **Chat** -- chat with local or hosted models.
  <br><sub>vLLM · llama.cpp · Ollama · LM Studio · OpenRouter · OpenAI · Anthropic · Gemini</sub>
- **Agent** -- give the assistant tools for web, files, shell, MCP, memory, and skills.
  <br><sub>built on [opencode](https://github.com/anomalyco/opencode) · MCP · tool permissions · memory</sub>
- **Cookbook** -- scan your hardware, recommend models, then download and serve them.
  <br><sub>built on [llmfit](https://github.com/AlexsJones/llmfit) · VRAM/unified-memory aware · GGUF / FP8 / AWQ · vLLM / llama.cpp serving</sub>
- **Deep Research** -- gather, read, and synthesize sources into visual reports.
  <br><sub>adapted from [Tongyi DeepResearch](https://github.com/Alibaba-NLP/DeepResearch)</sub>
- **Compare** -- compare model outputs side by side with blind testing.
  <br><sub>multi-model · blind test · synthesis</sub>
- **Documents** -- write, edit, and revise with AI assistance.
  <br><sub>multi-tab editor · markdown · HTML · CSV · syntax highlighting · AI edits · suggestions</sub>
- **Memory / Skills** -- keep persistent memories and reusable abilities.
  <br><sub>ChromaDB · fastembed (ONNX) · vector + keyword retrieval · import/export</sub>
- **Email, Notes, Tasks, Calendar** -- local-first personal workflows with optional AI help.
  <br><sub>IMAP/SMTP · CalDAV · reminders · scheduled tasks · ntfy/browser/email notifications</sub>
- **Mobile-friendly extras** -- responsive UI, PWA support, image tools, web search, uploads, presets, sessions, and 2FA.

## Demo
A full, hover-to-play tour lives on the landing page (`docs/index.html`). A few looks:

### Chat & Agents
![Chat & Agents](docs/chat.gif)
### Deep Research
![Deep Research](docs/research.gif)
### Compare
![Compare](docs/compare.gif)
### Documents
![Documents](docs/document.gif)
### Notes & Tasks
![Notes & Tasks](docs/notes.gif)

## Quick Start

Defaults work out of the box: clone, run, create the first admin account, then
configure providers from **Settings** inside the app. You usually do not need to
edit `.env` unless you are changing deployment-level settings such as
`AUTH_ENABLED`, `DATABASE_URL`, or pre-seeded API keys.

### Requirements
- Python 3.11+.
- macOS or Linux for the guided bootstrap. Windows can use the manual
  PowerShell path below.
- Docker Desktop or Docker Engine if you want the bundled ChromaDB, SearXNG,
  and ntfy sidecars.
- Optional local LLM backend such as Ollama, LM Studio, vLLM, llama.cpp,
  SGLang, LocalAI, or a hosted provider API key.

### Guided Bootstrap
```bash
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
./scripts/bootstrap --start
```

Bootstrap checks your platform, asks before installing system packages, creates
`.venv`, installs dependencies there, chooses a free local port, and prints a
short-lived first-run setup URL. Use that URL to create the first admin account
in the browser. No temporary admin password is stored or printed by this path.

After the first setup, start it again any time with:
```bash
./scripts/start
```

To also start the bundled Docker sidecars:
```bash
./scripts/bootstrap --with-services --start
```

### Docker
```bash
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
cp .env.example .env       # optional, but recommended for explicit defaults
docker compose up -d --build
```
Compose starts Odysseus, ChromaDB, SearXNG, and ntfy. First run does a full
image build. Open `http://localhost:7000` after the containers are healthy.

Cookbook remote servers use an Odysseus-owned SSH key from `./data/ssh`
inside Docker. In **Cookbook -> Settings -> Servers**, generate/copy the
public key and add it to the remote server's `~/.ssh/authorized_keys`.
After generating the key, you can also install it from the host with:
```bash
ssh-copy-id -i data/ssh/id_ed25519.pub user@server
```
Cookbook local downloads are stored in `./data/huggingface`, mounted as
`~/.cache/huggingface` inside the Odysseus container.

Useful checks:
```bash
docker compose ps
docker compose logs --tail=120 odysseus
docker compose logs odysseus | grep -E 'ChromaDB|MemoryVectorStore|DEGRADED'
docker compose exec odysseus python -c "from services.hwfit.models import get_models; print(len(get_models()))"
```

Expected vector-memory startup lines in Docker:
```text
ChromaDB connected: chromadb:8000
MemoryVectorStore initialized
```

The Cookbook model catalog check should print a non-zero count. If it prints
`0`, rebuild the Odysseus image with `docker compose build --no-cache odysseus`.

### macOS Native Install
**Requirements:** macOS with [Homebrew](https://brew.sh/). The setup script
uses Homebrew for Python/tmux, installs Python packages into a repo-local
`.venv`, and leaves your global Python packages alone.

```bash
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
scripts/setup-macos.sh --with-services --start
```

Open `http://127.0.0.1:7001`. See [docs/MACOS.md](docs/MACOS.md) for LaunchAgent
setup, global `python3` notes, and Mac hardware detection details.

### Manual Install: Linux
**Requirements:** Python 3.11+. On Linux/Termux, Cookbook also requires `tmux`
for background model downloads and serves.

Install system packages first:
```bash
# Debian/Ubuntu
sudo apt install tmux

# Arch
sudo pacman -S tmux

# Fedora
sudo dnf install tmux
```

Then install Odysseus:
```bash
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py            # creates data dirs and prints an initial admin password
uvicorn app:app --host 0.0.0.0 --port 7000
```

### Manual Install: Windows PowerShell
```powershell
git clone https://github.com/apexEvan/odysseus.git odysseus
cd odysseus
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python setup.py
uvicorn app:app --host 0.0.0.0 --port 7000
```

Open `http://localhost:7000`, log in with the generated admin password,
and configure everything else inside **Settings**.

## LLM Backends
Odysseus talks to model servers through provider-native or OpenAI-compatible
HTTP APIs. The compatibility list below was checked against upstream
documentation on May 31, 2026.

Model inference does not run inside Chrome. The browser renders the UI and
streams responses; Odysseus sends API requests from the app server to whichever
backend you configure, such as Ollama, LM Studio, vLLM, llama.cpp, OpenRouter,
OpenAI, Anthropic, or Gemini. If the browser is using several GB of memory,
check open tabs/extensions and whether browser automation MCP is enabled.

| Backend | How to connect | Notes |
|---|---|---|
| [OpenAI](https://platform.openai.com/docs/api-reference/chat/create-chat-completion) | `https://api.openai.com/v1` + API key | Chat Completions-compatible. Configure in Settings or pre-seed `OPENAI_API_KEY`. |
| [Anthropic Claude](https://docs.anthropic.com/en/api/messages) | `https://api.anthropic.com` + API key | Uses Anthropic's Messages API, not the OpenAI path. |
| [OpenRouter](https://openrouter.ai/docs/api-reference/chat-completion) | `https://openrouter.ai/api/v1` + API key | OpenAI-style chat completions gateway for many hosted models. |
| [Google Gemini](https://ai.google.dev/gemini-api/docs/openai) | `https://generativelanguage.googleapis.com/v1beta/openai` + Gemini key | Gemini's OpenAI compatibility layer. |
| [Ollama](https://docs.ollama.com/api/openai-compatibility) | `http://localhost:11434/v1` | Local OpenAI-compatible chat, models, tools, and vision support depending on model. |
| [LM Studio](https://lmstudio.ai/docs/app/api/endpoints/openai) | `http://localhost:1234/v1` | Start LM Studio's local server, then add the base URL in Settings. |
| [vLLM](https://docs.vllm.ai/en/latest/cli/serve/) | Usually `http://host:8000/v1` | Cookbook can launch `vllm serve`; endpoint discovery scans common vLLM ports. |
| [SGLang](https://docs.sglang.ai/basic_usage/openai_api.html) | Usually `http://host:30000/v1` | Cookbook can launch `python -m sglang.launch_server`. |
| [llama.cpp llama-server](https://www.mintlify.com/ggml-org/llama.cpp/inference/server) | Usually `http://host:8080/v1` | GGUF-first local serving. Cookbook also falls back to llama-cpp-python when needed. |
| [llama-cpp-python](https://llama-cpp-python.readthedocs.io/en/stable/server/) | User-chosen `/v1` base URL | OpenAI-compatible Python server for GGUF models. |
| [text-generation-webui](https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API) | Usually `http://host:5000/v1` | Its OpenAI API extension exposes chat/completions-style endpoints. |
| [KoboldCpp](https://github.com/LostRuins/koboldcpp/wiki) | Usually `http://host:5001/v1` | Provides OpenAI-compatible completions and chat completions. |
| [LocalAI](https://localai.io/) | Deployment-specific `/v1` base URL | Self-hosted OpenAI-compatible server across text, embeddings, images, and audio. |

Auto-discovery probes common local OpenAI-compatible ports (`11434`, `1234`,
`5000`, `5001`, `8000-8020`, `8080`, `30000`) on `LLM_HOST`/`LLM_HOSTS`.
For exact URLs or hosted gateways, set `LLM_ENDPOINTS` or add the endpoint in
Settings. OpenAI-compatible endpoints should be entered as the base URL ending
at the provider's API prefix, for example `http://localhost:11434/v1`, not the
full `/chat/completions` URL.

## Security Notes
Odysseus is a self-hosted workspace with powerful local tools: shell access, file uploads, model downloads, web research, email/calendar integrations, and API tokens. Treat it like an admin console.

- Keep `AUTH_ENABLED=true` for any network-accessible deployment.
- Do not expose it directly to the public internet without HTTPS and a trusted reverse proxy.
- Keep `data/`, `.env`, logs, databases, and uploaded/generated media out of Git. They are ignored by default.
- Review `data/auth.json` after first boot: disable open signup unless you intentionally want it, make only your own account admin, and keep demo/test accounts non-admin.
- Non-admin users do not get shell/Python/file read/write by default, and admin-only routes/tools such as MCP management, API tokens, webhooks, model/cookbook serving, backup/vault, and app settings are admin-gated. Other features are controlled by per-user privileges, so review each user's privileges before exposing a deployment.
- Rotate any API keys or tokens that were ever pasted into a shared chat, demo, screenshot, or log.
- If you enable API tokens or webhooks, create separate tokens per integration and delete unused ones.
- Prefer binding manual development runs to `127.0.0.1`; bind to `0.0.0.0` only when you intentionally want LAN/reverse-proxy access.
- Before publishing a fork, run `git status --short` and confirm no private files from `.env`, `data/`, `logs/`, uploads, backups, or local databases are staged.

### Putting it behind HTTPS
Odysseus serves plain HTTP on its port. That's fine for `localhost` and trusted LAN/VPN use, but browsers will warn ("Password fields present on an insecure page") and the login + API tokens travel in cleartext. For anything reachable outside your machine — including a Tailscale IP shared with other devices — put a TLS-terminating reverse proxy in front.

Shortest path with [Caddy](https://caddyserver.com/) (auto-renews Let's Encrypt certs):

```caddy
odysseus.example.com {
  reverse_proxy localhost:7000
}
```

For a LAN-only Tailscale deployment, Caddy + [tailscale-cert](https://caddyserver.com/docs/caddyfile/options#auto-https) or the built-in MagicDNS HTTPS feature both work. nginx/Traefik configs are similar — proxy `localhost:7000`, terminate TLS at the proxy. Once that's in place, the browser warning goes away and your login is encrypted.

## Contributing
Help is welcome. The best entry points are fresh-install testing, provider setup
bugs, mobile/editor polish, docs, and small focused refactors. See
[ROADMAP.md](ROADMAP.md) for the current help-wanted list.

## Configuration
Most setup is done inside the app with `/setup` or **Settings**. Use `.env`
for deployment-level defaults and secrets you want present before first boot.
Key settings:

| Variable | Default | Description |
|---|---|---|
| `LLM_HOST` | `localhost` | Your LLM server (e.g. `llm-host.local:8000`) |
| `LLM_HOSTS` | -- | Comma-separated hostnames, host:port pairs, or URLs for model discovery |
| `LLM_ENDPOINTS` | -- | Comma-separated exact OpenAI-compatible base URLs to probe |
| `OPENAI_API_KEY` | -- | Optional OpenAI key. Prefer adding providers in the app unless pre-seeding. |
| `SEARXNG_INSTANCE` | `http://localhost:8080` | SearXNG URL. Docker overrides this to `http://searxng:8080`. |
| `AUTH_ENABLED` | `true` | Enable/disable login |
| `LOCALHOST_BYPASS` | `false` | Development-only auth bypass for loopback requests. Keep false for shared/network deployments. |
| `ODYSSEUS_PORT` | `7000` | App port used by native/bootstrap runs; bootstrap writes the selected free port to `.env`. |
| `ODYSSEUS_INTERNAL_BASE_URL` | `http://127.0.0.1:$ODYSSEUS_PORT` | Loopback URL for in-app tools that call Odysseus routes. |
| `ODYSSEUS_SETUP_TOKEN` | -- | Optional fixed first-run setup token for automated deployments. Bootstrap normally generates one. |
| `ODYSSEUS_ALLOW_REMOTE_FIRST_RUN_SETUP` | `false` | Allows first-run setup from non-local clients. Keep false unless behind trusted private access. |
| `ODYSSEUS_ENABLE_BROWSER_MCP` | `false` | Starts the built-in Playwright Browser MCP sidecar. Leave off unless you need agent-controlled browser automation. |
| `DATABASE_URL` | `sqlite:///./data/app.db` | Database connection string |
| `CHROMADB_HOST` | `localhost` | ChromaDB host for vector memory. Docker overrides this to `chromadb`. |
| `CHROMADB_PORT` | `8100` | ChromaDB port for manual host runs. Docker overrides this to `8000`. |
| `EMBEDDING_URL` | -- | OpenAI-compatible embeddings endpoint |

### Bundled services
Docker Compose includes these by default:

  - **ChromaDB** → vector store for semantic memory. In Docker, Odysseus connects to `chromadb:8000`; from the host it is exposed as `localhost:8100`.
  - **SearXNG** → meta search for web search. In Docker, Odysseus connects to `searxng:8080`; from the host it is exposed only on `127.0.0.1:8080`.
  - **ntfy** → local notification service, exposed as `localhost:8091`.

### Optional external services
  - **Ollama** → local LLM server -- [ollama.ai](https://ollama.ai)
  - **LM Studio** → desktop local model server -- [lmstudio.ai](https://lmstudio.ai)
  - **vLLM / SGLang / llama.cpp / LocalAI** → self-hosted OpenAI-compatible inference servers.

## Architecture
```
app.py                   # FastAPI entry point
core/      auth, database, middleware, constants
src/       llm_core, agent_loop, agent_tools, chat_processor, search/
routes/    chat, session, document, memory, model … endpoints
services/  docs, memory, search, hwfit (Cookbook) …
static/    index.html + app.js + style.css + js/ (modular front-end)
docs/      landing page (index.html) + preview clips
```

## Data
All user data lives in `data/` (gitignored): `app.db` (sessions, messages, documents),
`memory.json`, `presets.json`, `uploads/`, `personal_docs/`, `chroma/`, `settings.json`.

## License
MIT -- see [LICENSE](LICENSE) and [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).

## Development Disclosure
The macOS setup and public-distribution hardening work in this branch was
prepared with AI assistance from OpenAI Codex using a GPT-5 model. Please do
not describe it as assisted by any other model/version unless that model use is
independently verified later.

```
                                  |
                                 |||
                                |||||
                  |    |    |   |||||||
                 )_)  )_)  )_)   ~|~
                )___))___))___)\  |
               )____)____)_____)\\|
             _____|____|____|_____\\\__
             \                       /
       ~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~
               ~^~  all aboard!  ~^~
       ~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~~^~^~
```
