'use client'

import { useState } from 'react'
import styles from './images.module.css'

interface GeneratedImage {
  id: string
  url: string
  prompt: string
  aspectRatio: string
  timestamp: string
}

const PRESET_PROMPTS = [
  'Cyberpunk neon city with glowing cyan rain',
  'Cosmic astronaut floating in a purple nebula',
  'Minimalist abstract geometric AI logo',
  'Retro 80s synthwave sunset landscape',
]

export default function ImagesPage() {
  const [prompt, setPrompt] = useState('Cyberpunk neon city with glowing cyan rain')
  const [aspectRatio, setAspectRatio] = useState('1:1')
  const [isGenerating, setIsGenerating] = useState(false)

  const [images, setImages] = useState<GeneratedImage[]>([
    {
      id: 'img-1',
      url: generateDemoSvg('Cyberpunk neon city with glowing cyan rain', '#00FFFF', '#6C63FF'),
      prompt: 'Cyberpunk neon city with glowing cyan rain',
      aspectRatio: '1:1',
      timestamp: 'Just now',
    },
    {
      id: 'img-2',
      url: generateDemoSvg('Cosmic astronaut floating in a purple nebula', '#6C63FF', '#FF007F'),
      prompt: 'Cosmic astronaut floating in a purple nebula',
      aspectRatio: '1:1',
      timestamp: '5m ago',
    },
  ])

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return

    setIsGenerating(true)
    try {
      const res = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, aspectRatio }),
      })

      const data = await res.json()
      if (data.imageUrl) {
        const newImg: GeneratedImage = {
          id: `img-${Date.now()}`,
          url: data.imageUrl,
          prompt,
          aspectRatio,
          timestamp: 'Just now',
        }
        setImages((prev) => [newImg, ...prev])
      }
    } catch (err) {
      console.error('Error generating image:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadImage = (url: string, filename: string) => {
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename.slice(0, 20).replace(/\s+/g, '-')}.svg`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <div className={styles.container}>
      <div className={styles.inner}>
        {/* Header */}
        <header className={styles.header}>
          <span className={styles.badge}>🎨 ImageAgent · Gemini Flash</span>
          <h1 className={styles.title}>AI Image Studio</h1>
          <p className={styles.desc}>
            Generate high-resolution visual assets and artwork directly with Vega ImageAgent.
          </p>
        </header>

        {/* Prompt Card */}
        <div className={styles.promptCard}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            className={styles.textarea}
            id="image-prompt-textarea"
          />

          <div className={styles.presetChips}>
            {PRESET_PROMPTS.map((p) => (
              <span key={p} className={styles.chip} onClick={() => setPrompt(p)}>
                ✦ {p}
              </span>
            ))}
          </div>

          <div className={styles.controlsRow}>
            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className={styles.aspectSelect}
              id="aspect-ratio-select"
            >
              <option value="1:1">1:1 Square (1024x1024)</option>
              <option value="16:9">16:9 Landscape (1280x720)</option>
              <option value="9:16">9:16 Portrait (720x1280)</option>
            </select>

            <button
              onClick={handleGenerate}
              disabled={isGenerating || !prompt.trim()}
              className={styles.generateBtn}
              id="generate-image-btn"
            >
              {isGenerating ? '🎨 Generating Art...' : '🎨 Generate Image'}
            </button>
          </div>
        </div>

        {/* Image History Grid */}
        <section className={styles.gridSection}>
          <div className={styles.sectionTitle}>
            <span>🖼</span> Generated Gallery ({images.length})
          </div>

          <div className={styles.grid}>
            {images.map((img) => (
              <div key={img.id} className={styles.imageCard}>
                {/* eslint-disable-next-html-img-element */}
                <img src={img.url} alt={img.prompt} className={styles.img} />

                <div className={styles.cardOverlay}>
                  <p className={styles.cardPrompt}>{img.prompt}</p>
                  <button
                    onClick={() => downloadImage(img.url, img.prompt)}
                    className={styles.downloadCardBtn}
                  >
                    ⬇ Download SVG/Image
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function generateDemoSvg(prompt: string, color1: string, color2: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <defs>
    <radialGradient id="g" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="${color1}" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#0A0A0F" stop-opacity="1" />
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="#0A0A0F" />
  <circle cx="400" cy="400" r="300" fill="url(#g)" />
  <text x="50%" y="85%" fill="${color1}" font-size="18" font-family="sans-serif" text-anchor="middle">
    ${prompt}
  </text>
</svg>`
  return `data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`
}
