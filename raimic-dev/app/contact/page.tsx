'use client'

import { useState, FormEvent } from 'react'
import { motion } from 'framer-motion'

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    topic: 'Vega CLI',
    message: '',
  })

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.email || !formData.message) return
    setSubmitted(true)
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-6 pt-32 pb-24 flex flex-col items-center">
      {/* Header */}
      <div className="text-center max-w-xl mx-auto mb-12">
        <span className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">GET IN TOUCH</span>
        <h1 className="font-display text-4xl sm:text-6xl font-extrabold text-white mt-2 mb-4">
          Contact Raimic Labs
        </h1>
        <p className="text-gray-400 text-base leading-relaxed">
          Have a question about Vega CLI, partnership opportunities, or feedback? Send us a message below.
        </p>
      </div>

      {/* Form Container */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-xl bg-[#111118] border border-white/10 rounded-2xl p-8 sm:p-10 shadow-2xl"
      >
        {submitted ? (
          <div className="flex flex-col items-center text-center py-10 gap-4">
            <div className="w-16 h-16 rounded-full bg-green-500/20 border border-green-500/40 text-green-400 flex items-center justify-center text-2xl font-bold">
              ✓
            </div>
            <h2 className="font-display text-2xl font-bold text-white">Message Received!</h2>
            <p className="text-gray-300 text-sm max-w-sm">
              Thank you for reaching out to Raimic Labs. Our team will get back to you shortly at <span className="text-[#00FFFF]">{formData.email}</span>.
            </p>
            <button
              onClick={() => {
                setSubmitted(false)
                setFormData({ name: '', email: '', topic: 'Vega CLI', message: '' })
              }}
              className="mt-4 px-6 py-2.5 rounded-full bg-[#00FFFF] text-[#0A0A0F] font-bold text-xs uppercase tracking-wide shadow-[0_0_15px_rgba(0,255,255,0.3)] hover:scale-105 transition-all"
            >
              Send Another Message
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono text-gray-300 uppercase tracking-wider">Your Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ada Lovelace"
                className="w-full bg-[#0A0A0F] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00FFFF] transition-colors"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono text-gray-300 uppercase tracking-wider">Email Address</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="ada@example.com"
                className="w-full bg-[#0A0A0F] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00FFFF] transition-colors"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono text-gray-300 uppercase tracking-wider">Topic of Interest</label>
              <select
                value={formData.topic}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                className="w-full bg-[#0A0A0F] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00FFFF] transition-colors font-sans"
              >
                <option value="Vega CLI">Vega CLI Support / Inquiry</option>
                <option value="Vega Web">Vega Web Early Access</option>
                <option value="Enterprise">Enterprise & Custom AI Integration</option>
                <option value="General">General Question</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-mono text-gray-300 uppercase tracking-wider">Message</label>
              <textarea
                required
                rows={5}
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                placeholder="How can Raimic Labs help you build?"
                className="w-full bg-[#0A0A0F] border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#00FFFF] transition-colors resize-none"
              />
            </div>

            <button
              type="submit"
              className="w-full py-4 rounded-xl bg-[#00FFFF] text-[#0A0A0F] font-bold text-sm tracking-wide uppercase shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] hover:scale-[1.01] transition-all"
            >
              Send Message ➔
            </button>
          </form>
        )}
      </motion.div>
    </div>
  )
}
