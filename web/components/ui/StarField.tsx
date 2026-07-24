'use client'

import { useEffect, useRef } from 'react'
import styles from './StarField.module.css'

interface Star {
  x: number
  y: number
  r: number
  alpha: number
  speed: number
  twinkleOffset: number
}

const STAR_COUNT = 180

export default function StarField() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const frameRef  = useRef<number>(0)
  const starsRef  = useRef<Star[]>([])
  const timeRef   = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
      init()
    }

    const init = () => {
      starsRef.current = Array.from({ length: STAR_COUNT }, () => ({
        x:             Math.random() * canvas.width,
        y:             Math.random() * canvas.height,
        r:             Math.random() * 1.5 + 0.2,
        alpha:         Math.random() * 0.6 + 0.1,
        speed:         Math.random() * 0.3 + 0.05,
        twinkleOffset: Math.random() * Math.PI * 2,
      }))
    }

    const draw = (ts: number) => {
      timeRef.current = ts * 0.001
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (const star of starsRef.current) {
        const twinkle = Math.sin(timeRef.current * star.speed * 2 + star.twinkleOffset)
        const alpha   = star.alpha + twinkle * 0.25

        ctx.beginPath()
        ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, Math.min(1, alpha))})`
        ctx.fill()
      }

      frameRef.current = requestAnimationFrame(draw)
    }

    resize()
    frameRef.current = requestAnimationFrame(draw)
    window.addEventListener('resize', resize, { passive: true })

    return () => {
      cancelAnimationFrame(frameRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className={styles.canvas}
      aria-hidden="true"
    />
  )
}
