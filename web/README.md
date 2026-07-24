# ✦ Vega Web — Next.js Workspace

The web workspace and interactive AI studio for **Vega CLI**, built by Raimic Labs with Next.js 14, TypeScript, Framer Motion, and a Dark Cosmic UI theme.

---

## 🌟 Features

- **Cosmic Dark Theme**: Built with custom design tokens (`#00FFFF` Cyan, `#0A0A0F` Dark, `#6C63FF` Purple), aurora background mesh, and custom scrollbars.
- **Vega AI Workspace (`/chat`)**: Multi-agent chat interface with live streaming, auto-agent detection (`CodeAgent`, `DebugAgent`, `PlannerAgent`, `ReviewAgent`, `ImageAgent`, `FastAgent`), and syntax code blocks with copy support.
- **Project Builder GUI (`/build`)**: Split-view workspace for generating full projects, viewing code, inspecting live iframe previews, and exporting as `.zip`.
- **AI Image Studio (`/images`)**: Visual asset generator powered by Google Gemini with customizable aspect ratios (1:1, 16:9, 9:16) and image gallery downloads.
- **Pricing & FAQs (`/pricing`)**: Free, Pro, and Team tier cards with yearly billing discount calculator and accordion FAQs.
- **Settings & API Keys (`/settings`)**: Secure API key management for NVIDIA NIM, Google Gemini, Groq, and DeepSeek credentials with connection testing.

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 Environment Variables

Create a `.env.local` file in the `web` root directory:

```env
# NVIDIA NIM API Key (Default Provider for Kimi K2.6)
NVIDIA_API_KEY=nvapi-your-key-here

# Google Gemini API Key (ImageAgent & Multimodal)
GOOGLE_API_KEY=AIzaSyYourKeyHere

# Groq API Key (FastAgent Llama 3.3)
GROQ_API_KEY=gsk_your_key_here

# DeepSeek API Key (PlannerAgent & ReviewAgent)
DEEPSEEK_API_KEY=sk-your-key-here
```

*Note: Users can also input their API keys directly on the `/settings` page or in the CLI via `/connect`.*

---

## ⚡ Deploy to Vercel

Vega Web is fully optimized for **Vercel** with Next.js App Router and Edge API Routes:

1. Push your repository to GitHub.
2. Import the project in Vercel.
3. Set Root Directory to `web`.
4. Add environment variables (`NVIDIA_API_KEY`, etc.).
5. Click **Deploy**.

---

Built with ✦ by **Raimic Labs**.
