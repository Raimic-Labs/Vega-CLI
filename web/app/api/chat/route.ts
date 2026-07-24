import { NextRequest } from 'next/server'

export const runtime = 'edge'

export async function POST(req: NextRequest) {
  try {
    const { messages, model = 'moonshotai/kimi-k2.6', apiKey } = await req.json()

    const nvKey = apiKey || process.env.NVIDIA_API_KEY || process.env.VEGA_NVIDIA_API_KEY

    // If NVIDIA API key is available, forward stream to NVIDIA NIM endpoint
    if (nvKey) {
      const response = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${nvKey}`,
        },
        body: JSON.stringify({
          model,
          messages,
          stream: true,
          temperature: 0.7,
          max_tokens: 4096,
        }),
      })

      if (!response.ok) {
        const errText = await response.text()
        return new Response(JSON.stringify({ error: errText }), {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          Connection: 'keep-alive',
        },
      })
    }

    // Fallback streaming simulation if no API key is provided
    const lastUserMsg = messages[messages.length - 1]?.content || ''
    const simulatedResponse = generateSimulatedResponse(lastUserMsg)

    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        const chunks = simulatedResponse.split(/(?<=\s)|(?<=\n)/)
        for (const chunk of chunks) {
          const sseData = JSON.stringify({
            choices: [{ delta: { content: chunk } }],
          })
          controller.enqueue(encoder.encode(`data: ${sseData}\n\n`))
          await new Promise((res) => setTimeout(res, 25))
        }
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
      },
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Internal Server Error'
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}

function generateSimulatedResponse(prompt: string): string {
  const lower = prompt.toLowerCase()

  if (lower.includes('build') || lower.includes('create') || lower.includes('make') || lower.includes('app')) {
    return `I'll build that for you using **CodeAgent**. Here is the project structure and complete code:

### 📁 Project Structure
\`\`\`text
project/
├── index.html
├── styles.css
└── app.js
\`\`\`

### 🌐 index.html
\`\`\`html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Vega Built App</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div id="app">
    <h1>Built with Vega CLI</h1>
    <p>Powered by NVIDIA NIM & Kimi K2.6</p>
    <button id="action-btn">Click Me</button>
  </div>
  <script src="app.js"></script>
</body>
</html>
\`\`\`

### 🎨 styles.css
\`\`\`css
body {
  background: #0A0A0F;
  color: #00FFFF;
  font-family: system-ui, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  margin: 0;
}

#app {
  text-align: center;
  padding: 2rem;
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 12px;
  background: rgba(17, 17, 24, 0.8);
  box-shadow: 0 0 30px rgba(0, 255, 255, 0.15);
}

button {
  background: #00FFFF;
  color: #0A0A0F;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 6px;
  cursor: pointer;
}
\`\`\`

### 📜 app.js
\`\`\`javascript
document.getElementById('action-btn').addEventListener('click', () => {
  alert('Hello from Vega CLI!');
});
\`\`\`

Project created successfully! You can run it locally or deploy it.`
  }

  if (lower.includes('fix') || lower.includes('bug') || lower.includes('error') || lower.includes('debug')) {
    return `### 🐛 Debug Analysis by DebugAgent

I analyzed your request and identified the issue:

1. **Root Cause**: Unhandled potential \`null\` dereference during DOM element retrieval.
2. **Solution**: Added strict guard checks and safe optional chaining.

\`\`\`typescript
// Fixed Code:
export function handleAction(elementId: string): void {
  const el = document.getElementById(elementId);
  if (!el) {
    console.warn(\`Element \${elementId} not found\`);
    return;
  }
  el.classList.add('active');
}
\`\`\`

Everything looks clean and safe now!`
  }

  return `Vega CLI is online and ready. I have processed your request using **Kimi K2.6** via NVIDIA NIM.

Here is a quick overview of how you can use Vega to build full-stack projects directly from your terminal:

- Run \`vega\` to launch interactive mode
- Type \`build me a landing page\` to generate project files
- Connect your NVIDIA NIM API key via \`/config set api_keys.nvidia YOUR_KEY\`

How can I assist you further with your code today?`
}
