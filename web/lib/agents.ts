import { PROVIDERS, ProviderConfig } from './providers'

export interface AgentConfig {
  name: string
  badge: string
  providerId: string
  modelId: string
  description: string
  triggers: string[]
  systemPrompt: string
}

export const AGENTS: Record<string, AgentConfig> = {
  CodeAgent: {
    name: 'CodeAgent',
    badge: '⟡',
    providerId: 'nvidia',
    modelId: 'moonshotai/kimi-k2.6',
    description: 'Specialized in building full projects, writing multi-file applications, and web apps.',
    triggers: ['build', 'create', 'make', 'scaffold', 'app', 'website', 'project'],
    systemPrompt: 'You are CodeAgent, an elite autonomous software engineer. Generate production quality code and complete file structures.',
  },
  DebugAgent: {
    name: 'DebugAgent',
    badge: '🐞',
    providerId: 'nvidia',
    modelId: 'moonshotai/kimi-k2.6',
    description: 'Specialized in root cause analysis, error debugging, and fixing broken code.',
    triggers: ['fix', 'bug', 'error', 'debug', 'issue', 'crash', 'traceback'],
    systemPrompt: 'You are DebugAgent. Identify the exact root cause of runtime errors and supply clear, corrected code snippets.',
  },
  PlannerAgent: {
    name: 'PlannerAgent',
    badge: '🗺',
    providerId: 'deepseek',
    modelId: 'deepseek-chat',
    description: 'Specialized in system architecture, database schema design, and engineering roadmaps.',
    triggers: ['plan', 'design', 'architecture', 'schema', 'roadmap', 'structure'],
    systemPrompt: 'You are PlannerAgent. Provide detailed architectural blueprints, schema diagrams, and implementation plans.',
  },
  ReviewAgent: {
    name: 'ReviewAgent',
    badge: '🔍',
    providerId: 'deepseek',
    modelId: 'deepseek-chat',
    description: 'Specialized in code quality audits, performance optimizations, and refactoring.',
    triggers: ['review', 'refactor', 'improve', 'optimize', 'audit', 'clean'],
    systemPrompt: 'You are ReviewAgent. Perform strict code reviews focusing on clean code patterns, efficiency, and security.',
  },
  ImageAgent: {
    name: 'ImageAgent',
    badge: '🎨',
    providerId: 'google',
    modelId: 'gemini-2.0-flash',
    description: 'Specialized in generating visual designs, SVG graphics, and UI image descriptions.',
    triggers: ['draw', 'image', 'picture', 'logo', 'photo', 'art', 'graphic'],
    systemPrompt: 'You are ImageAgent. Create stunning visual art, vector graphics, and UI layouts.',
  },
  FastAgent: {
    name: 'FastAgent',
    badge: '⚡',
    providerId: 'groq',
    modelId: 'llama-3.3-70b-versatile',
    description: 'Specialized in sub-second responses for quick Q&A, syntax checks, and concise summaries.',
    triggers: ['what', 'explain', 'how', 'why', 'summary', 'quick', 'define'],
    systemPrompt: 'You are FastAgent. Provide concise, direct, sub-second answers to developer questions.',
  },
}

export function detectAgent(prompt: string): AgentConfig {
  const lower = prompt.toLowerCase()

  for (const agent of Object.values(AGENTS)) {
    for (const trigger of agent.triggers) {
      const regex = new RegExp(`\\b${trigger}\\b`, 'i')
      if (regex.test(lower)) {
        return agent
      }
    }
  }

  return AGENTS.CodeAgent
}

export interface RouteResult {
  agent: AgentConfig
  provider: ProviderConfig
  modelId: string
}

export function routeToAgent(prompt: string, overrideModelId?: string): RouteResult {
  const agent = detectAgent(prompt)
  const provider = PROVIDERS[agent.providerId] || PROVIDERS.nvidia
  const modelId = overrideModelId || agent.modelId

  return {
    agent,
    provider,
    modelId,
  }
}
