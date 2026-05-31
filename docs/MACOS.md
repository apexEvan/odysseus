# Odysseus on macOS

This path is designed to be safe for a developer machine: Homebrew owns the
Python runtime, Odysseus owns a project-local `.venv`, and app data stays in
`data/` under this checkout.

## Quick Setup

```bash
git clone https://github.com/apexEvan/odysseus.git
cd odysseus
./scripts/bootstrap --start
```

Open `http://127.0.0.1:7001`.

Bootstrap prints a short-lived first-run setup URL. Use that URL to create the
first admin account in your browser. If you want Docker-managed ChromaDB,
SearXNG, and ntfy, pass `--with-services`; otherwise those features may report
degraded service until you point them at running services.

After setup, start the app from Terminal with:

```bash
./scripts/start
```

## What The Script Changes

- Installs Homebrew `python@3.13` if missing.
- Installs Homebrew `tmux` if missing.
- Creates `.venv/` inside the repo.
- Installs `requirements.txt` into `.venv/`, not global Python.
- Runs `npm ci` from `package-lock.json` when `npm` is available.
- Creates local `data/` and `logs/` folders with `setup.py`.
- Copies `.env.example` to `.env` only if `.env` does not already exist.

The script does not edit your shell profile and does not install Python packages
into global site-packages.

## Global Python

Homebrew's versioned Python is available at:

```bash
/opt/homebrew/bin/python3.13
```

If you want `python3` itself to resolve to Homebrew's Python 3.13, add this to
your shell profile:

```bash
export PATH="/opt/homebrew/opt/python@3.13/libexec/bin:$PATH"
```

This is intentionally left as an explicit user choice so Odysseus does not alter
other projects' Python behavior.

## Run Manually

```bash
source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 7001
```

The shorter equivalent after bootstrap is:

```bash
./scripts/start
```

Use `127.0.0.1` for local-only development. Bind to `0.0.0.0` only when you
intend to expose Odysseus to your LAN or a reverse proxy.

The native macOS path defaults to port `7001` because macOS Control
Center/AirPlay commonly occupies port `7000`. Set `ODYSSEUS_PORT=7000` if you
prefer the Docker/Linux default and that port is free.

## Memory Notes

Odysseus does not run LLM inference inside Chrome. The web app sends requests
to the configured backend, such as Ollama, LM Studio, vLLM, llama.cpp, or a
hosted provider. On macOS, high Chrome memory is usually open tabs/extensions or
browser automation. The built-in Playwright Browser MCP is disabled by default;
enable it only when you want the agent to control web pages:

```bash
ODYSSEUS_ENABLE_BROWSER_MCP=true ./scripts/start
```

## Run At Login

After setup:

```bash
./install-service.sh
```

On macOS this installs a per-user LaunchAgent at:

```text
~/Library/LaunchAgents/dev.odysseus.ui.plist
```

Logs are written to `logs/launchd.out.log` and `logs/launchd.err.log`.

Stop it with:

```bash
launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/dev.odysseus.ui.plist
```

## Mac Hardware Support

Odysseus detects macOS hardware with `sysctl`, `vm_stat`, and
`system_profiler`. On Apple Silicon it reports the local backend as `metal` and
treats available unified memory as the local model budget, which lets Cookbook
surface MLX/Metal-friendly model choices instead of assuming a Linux CUDA box.

## AI Assistance Disclosure

The macOS setup work in this branch was prepared with AI assistance from
OpenAI Codex using a GPT-5 model. Do not describe this work as assisted by any
other model/version unless the project later verifies that model was actually
used.
