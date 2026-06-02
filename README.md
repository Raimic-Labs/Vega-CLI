<div align="center">

<br/>

```
██╗   ██╗███████╗ ██████╗  █████╗
██║   ██║██╔════╝██╔════╝ ██╔══██╗
██║   ██║█████╗  ██║  ███╗███████║
╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██║
 ╚████╔╝ ███████╗╚██████╔╝██║  ██║
  ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
```

**An AI-powered CLI tool that builds projects, answers questions, and runs agents — right in your terminal.**

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
✅ Created ./portfolio-website/
   ├── index.html
   ├── style.css
   └── script.js
Open in VS Code? (y/n)
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

- Python 3.9 or higher
- An API key from at least one supported provider (see below)

---

## Quick Start

**1. Launch Vega:**

```bash
vega
```

**2. Connect your API key:**

```
/connect
```

Follow the prompt to select your AI provider and paste your key.

**3. Start building:**

```
> what is a REST API?
> build me a todo app in React
> write a Python script to rename files in bulk
```

---

## Supported AI Providers

| Provider | Models |
|----------|--------|
| Anthropic | Claude 3.5, Claude 3 Opus, Claude Haiku |
| OpenAI | GPT-4o, GPT-4 Turbo, GPT-3.5 |
| Google | Gemini 1.5 Pro, Gemini Flash |
| DeepSeek | DeepSeek Chat, DeepSeek Coder |

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/connect` | Add or switch your API key |
| `/models` | List available models |
| `/switch` | Switch to a different model |
| `/agents` | View and run built-in agents |
| `/settings` | Configure Vega preferences |
| `/history` | View your conversation history |
| `/exit` | Exit Vega |

---

## Project Builder

Tell Vega what to build and it will generate a complete project on disk:

```bash
> build me a weather app using HTML CSS JS
> create a REST API in Python with Flask
> make a Chrome extension that blocks distracting sites
```

**Vega will:**
- Create a dedicated project folder
- Write all files to disk
- Ask if you want to open in VS Code or browser
- Optionally export as a ZIP

**Custom output folder:**

```bash
> build a portfolio website in ~/Desktop/my-portfolio
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
pip install -e .
```

1. Fork the repo
2. Create a branch: `git checkout -b fix/your-fix`
3. Make your changes
4. Commit: `git commit -m "fix: description"`
5. Push: `git push origin fix/your-fix`
6. Open a Pull Request

---

## Roadmap

- [x] Multi-provider AI support
- [x] Project file generation
- [x] Slash command system
- [ ] Plugin/extension system
- [ ] Web UI (optional)
- [ ] Auto-update on launch
- [ ] Agent marketplace

---

## License

MIT © [Raimic Labs](https://github.com/Raimic-Labs)

---

<div align="center">

Made with ❤️ by [Raimic Labs](https://github.com/Raimic-Labs) · [PyPI](https://pypi.org/project/vega-raimic/) · [Issues](https://github.com/Raimic-Labs/Vega-CLI/issues)

</div>
