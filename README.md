<div align="center">

<br/>

<pre>
 ██╗   ██╗███████╗ ██████╗  █████╗
 ██║   ██║██╔════╝██╔════╝ ██╔══██╗
 ██║   ██║█████╗  ██║  ███╗███████║
 ╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██║
  ╚████╔╝ ███████╗╚██████╔╝██║  ██║
   ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
</pre>

**An AI-powered CLI that builds projects, answers questions, and runs agents — right in your terminal.**

[![PyPI version](https://img.shields.io/pypi/v/vega-raimic?color=blue&label=pypi)](https://pypi.org/project/vega-raimic/)
[![Python](https://img.shields.io/pypi/pyversions/vega-raimic)](https://pypi.org/project/vega-raimic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Raimic-Labs/Vega-CLI?style=social)](https://github.com/Raimic-Labs/Vega-CLI)

<br/>

</div>

---

## What is Vega?

Vega is a terminal-based AI assistant that lets you chat with AI models, generate full projects from a single prompt, and run specialized agents — without leaving your terminal.

```bash
$ vega
> build me a portfolio website
✦ Planning project structure…
✦ Generating files…  [████████████████████████████░░] 9/10
✦ Build complete! 10 files → ./portfolio_website/
   📁 portfolio_website/
   ├── 🌐 index.html
   ├── 🎨 style.css
   └── 📜 script.js
Export ZIP? [y/N]
```

---

## Installation

### Option 1 — pipx (Recommended for CLI tools)

```bash
# Install pipx if you don't have it
brew install pipx        # macOS
sudo apt install pipx    # Ubuntu/Debian

# Install Vega
pipx install vega-raimic

# Run
vega
```

### Option 2 — pip

```bash
pip install vega-raimic
vega
```

### Option 3 — From Source (for contributors)

```bash
git clone https://github.com/Raimic-Labs/Vega-CLI.git
cd Vega-CLI
pip install -e .
vega
```

---

## Requirements

- Python 3.10 or higher
- An API key from at least one supported provider (see below)

---

## Quick Start

**1. Launch Vega:**

```bash
vega
```

**2. Connect your API key (first-run wizard launches automatically):**

```
/connect
```

Follow the prompt to select your AI provider and paste your key.

**3. Start building:**

```
✦ › what is a REST API?
✦ › build me a todo app in React
✦ › write a Python script to rename files in bulk
```

---

## Supported AI Providers

| Provider      | Key Prefix | Free Tier | Notable Models                                      |
|---------------|------------|-----------|-----------------------------------------------------|
| **NVIDIA NIM** | `nvapi-`  | ✅ Yes    | Kimi K2, Llama 3.1 405B, Llama 3.1 70B             |
| **Google**    | `AIza`     | ✅ Yes    | Gemini 2.0 Flash, Gemini 1.5 Pro, Gemma 2 27B      |
| **Groq**      | `gsk_`     | ✅ Yes    | Llama 3.3 70B, Llama 4 Scout, Mixtral 8x7B         |
| **DeepSeek**  | `sk-`      | ⚡ Cheap   | DeepSeek-V3 (deepseek-chat), DeepSeek-R1 (reasoning)|

> **NVIDIA NIM** offers a free tier — grab a key in 30 seconds at [build.nvidia.com](https://build.nvidia.com).

---

## Specialized Agents

Vega automatically routes your prompt to the best agent:

| Icon | Agent        | Provider      | Best For                              |
|------|--------------|---------------|---------------------------------------|
| ⟡   | CodeAgent    | NVIDIA / Kimi K2 | Building & scaffolding projects    |
| 🎨   | ImageAgent   | Google Gemini | Creative & visual descriptions        |
| ⚡   | FastAgent    | Groq / Llama 4 Scout | Quick Q&A, explanations        |
| 🗺   | PlannerAgent | DeepSeek-V3   | Architecture & system design          |
| 🔧   | DebugAgent   | NVIDIA / Kimi K2 | Fixing bugs & errors               |
| 👁   | ReviewAgent  | DeepSeek-V3   | Code review, refactoring, audit       |

---

## Commands

| Command               | Description                          |
|-----------------------|--------------------------------------|
| `/help`               | Show all available commands          |
| `/connect`            | Add or switch your API key           |
| `/switch`             | Interactively pick a model           |
| `/model [id]`         | Set model by ID                      |
| `/models`             | List all available models            |
| `/provider [name]`    | Switch active provider               |
| `/agents`             | View the specialized agent roster    |
| `/build <goal>`       | Launch project builder mode          |
| `/clear`              | Clear chat history & screen          |
| `/history`            | Show last 10 prompts                 |
| `/export [path]`      | Export session to Markdown           |
| `/settings`           | Show all config values               |
| `/config [key] [val]` | View or update a config key          |
| `/system [prompt]`    | Set or view system prompt            |
| `/tokens`             | Show token usage stats               |
| `/agent <goal>`       | Run autonomous ReAct agent           |
| `/reset`              | Reset config to defaults             |
| `/version`            | Print Vega version                   |
| `/exit`               | Exit Vega                            |

---

## Project Builder

Tell Vega what to build and it will generate a complete project on disk:

```bash
✦ › build me a weather app using HTML CSS JS
✦ › create a REST API in Python with Flask
✦ › make a Chrome extension that blocks distracting sites
```

**Vega will:**
- Plan the full project structure
- Generate every file with complete, working code
- Write all files to a dedicated output folder
- Ask if you want to export as a ZIP
- Automatically open `index.html` in your browser (for web projects)

**One-shot builder mode (without interactive session):**

```bash
vega build "Build a FastAPI todo app with SQLite" --out ./my-todo-api
```

---

## Configuration

All settings live in `~/.vega/config.json`:

```bash
# View all settings
/settings

# Set a config value
/config temperature 0.9
/config max_tokens 8192
/config show_token_count true

# Set system prompt
/system You are a concise Python expert.
```

---

## Environment Variables

You can set API keys via environment variables instead of the config file:

```bash
export VEGA_NVIDIA_API_KEY="nvapi-..."
export VEGA_GOOGLE_API_KEY="AIza..."
export VEGA_GROQ_API_KEY="gsk_..."
export VEGA_DEEPSEEK_API_KEY="sk-..."
```

---

## Updating Vega

### If installed via pipx:

```bash
pipx upgrade vega-raimic
```

### If installed via pip:

```bash
pip install vega-raimic --upgrade
```

### If installed from source:

```bash
cd Vega-CLI
git pull
pip install -e .
```

---

## Uninstall

```bash
pipx uninstall vega-raimic
# or
pip uninstall vega-raimic
```

---

## Contributing

Contributions are welcome! Here's how to get started:

```bash
git clone https://github.com/Raimic-Labs/Vega-CLI.git
cd Vega-CLI
pip install -e ".[dev]"
```

1. Fork the repo
2. Create a branch: `git checkout -b fix/your-fix`
3. Make your changes
4. Run linting: `ruff check . && black --check .`
5. Commit: `git commit -m "fix: description"`
6. Push: `git push origin fix/your-fix`
7. Open a Pull Request

---

## Roadmap

- [x] Multi-provider AI support (NVIDIA, Google, Groq, DeepSeek)
- [x] Project file generation with builder mode
- [x] Slash command system
- [x] 6 specialized AI agents with auto-routing
- [x] Session persistence & export
- [x] Autonomous ReAct agent with tool use
- [ ] File reading with `@filename.py` syntax
- [ ] Ollama / local model integration
- [ ] Plugin / extension system
- [ ] Auto-update on launch
- [ ] VS Code extension

---

## License

MIT © [Raimic Labs](https://github.com/Raimic-Labs)

---

<div align="center">

Made with ❤️ by [Raimic Labs](https://github.com/Raimic-Labs) · [PyPI](https://pypi.org/project/vega-raimic/) · [Docs](https://github.com/Raimic-Labs/Vega-CLI/tree/main/vega-docs) · [Issues](https://github.com/Raimic-Labs/Vega-CLI/issues)

</div>
