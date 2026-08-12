import { useEffect, useRef } from 'react'

const NODE_COUNT_DESKTOP = 200
const NODE_COUNT_MOBILE = 100
const CONNECTION_DISTANCE = 220
const PULSE_SPEED = 400
const PULSE_SPAWN_INTERVAL = 250
const NODE_RADIUS = 2.5
const PULSE_RADIUS = 3.5

const LLM_WORDS = [
  'AI', 'LLM', 'GPT', 'RAG', 'NLP', 'ML', 'CNN', 'BERT', 'Neural', 'Token',
  'Embed', 'Vector', 'Query', 'Model', 'Health', 'Diagnosis', 'Gene',
  'DNA', 'Protein', 'Brain', 'Cell', 'Synapse', 'Pulse', 'Data',
  'Algo', 'Deep', 'Learn', 'Train', 'Infer', 'Prompt', 'Logic',
  'Bio', 'Med', 'Rx', 'Vitals', 'ECG', 'MRI', 'CT', 'XRay',
  'Transformer', 'Attention', 'Layer', 'Gradient', 'Loss', 'Epoch',
  'Batch', 'Optimizer', 'ReLU', 'Softmax', 'Encoder', 'Decoder',
  'Hallucination', 'FineTune', 'ZeroShot', 'FewShot', 'Chain',
  'Medicine', 'Patient', 'Symptom', 'Therapy', 'Surgery', 'Dose',
]

function createNode(w, h) {
  const angle = Math.random() * Math.PI * 2
  const speed = 0.4 + Math.random() * 0.6
  return {
    x: Math.random() * w,
    y: Math.random() * h,
    baseX: Math.random() * w,
    baseY: Math.random() * h,
    orbitRadius: 50 + Math.random() * 100,
    orbitSpeed: speed * (Math.random() > 0.5 ? 1 : -1),
    orbitAngle: angle,
    driftX: (Math.random() - 0.5) * 0.3,
    driftY: (Math.random() - 0.5) * 0.3,
    glow: 0,
    word: Math.random() < 0.15 ? LLM_WORDS[Math.floor(Math.random() * LLM_WORDS.length)] : null,
    wordAlpha: 0,
    wordTarget: Math.random() < 0.4 ? 0.22 : 0,
  }
}

function createPulse(nodes) {
  if (nodes.length < 2) return null
  const from = Math.floor(Math.random() * nodes.length)
  let to = Math.floor(Math.random() * nodes.length)
  if (to === from) to = (from + 1) % nodes.length
  return { from, to, t: 0, intensity: 1 }
}

export default function NeuralBackground() {
  const canvasRef = useRef(null)
  const animRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const isDark = document.documentElement.classList.contains('dark')
    const isMobile = window.innerWidth < 640
    const nodeCount = isMobile ? NODE_COUNT_MOBILE : NODE_COUNT_DESKTOP

    let w = window.innerWidth
    let h = window.innerHeight
    canvas.width = w
    canvas.height = h

    const nodes = Array.from({ length: nodeCount }, () => createNode(w, h))
    const pulses = []
    let lastSpawn = 0

    const nodeColor = isDark ? [20, 184, 166] : [14, 165, 233]
    const lineColor = isDark ? '20, 184, 166' : '14, 165, 233'
    const pulseColor = isDark ? [34, 211, 238] : [56, 189, 248]
    const textColor = isDark ? 'rgba(20, 184, 166, ' : 'rgba(14, 165, 233, '

    function resize() {
      w = window.innerWidth
      h = window.innerHeight
      canvas.width = w
      canvas.height = h
      for (const node of nodes) {
        node.baseX = Math.random() * w
        node.baseY = Math.random() * h
      }
    }
    window.addEventListener('resize', resize)

    let lastTime = performance.now()

    function frame(now) {
      const dt = Math.min((now - lastTime) / 1000, 0.05)
      lastTime = now

      ctx.clearRect(0, 0, w, h)

      // Update node positions (orbital + drift)
      for (const node of nodes) {
        node.orbitAngle += node.orbitSpeed * dt
        node.baseX += node.driftX * dt * 30
        node.baseY += node.driftY * dt * 30

        node.x = node.baseX + Math.cos(node.orbitAngle) * node.orbitRadius
        node.y = node.baseY + Math.sin(node.orbitAngle * 0.7) * node.orbitRadius * 0.6

        // Wrap around screen
        if (node.baseX < -100) node.baseX += w + 200
        if (node.baseX > w + 100) node.baseX -= w + 200
        if (node.baseY < -100) node.baseY += h + 200
        if (node.baseY > h + 100) node.baseY -= h + 200

        if (node.glow > 0) node.glow = Math.max(0, node.glow - dt * 0.8)

        if (node.word) {
          if (node.wordAlpha < node.wordTarget) {
            node.wordAlpha = Math.min(node.wordTarget, node.wordAlpha + dt * 0.3)
          } else if (node.wordAlpha > node.wordTarget) {
            node.wordAlpha = Math.max(node.wordTarget, node.wordAlpha - dt * 0.3)
          }
        }
      }

      // Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < CONNECTION_DISTANCE) {
            const alpha = (1 - dist / CONNECTION_DISTANCE) * (isDark ? 0.35 : 0.2)
            ctx.beginPath()
            ctx.moveTo(nodes[i].x, nodes[i].y)
            ctx.lineTo(nodes[j].x, nodes[j].y)
            ctx.strokeStyle = `rgba(${lineColor}, ${alpha})`
            ctx.lineWidth = 0.8
            ctx.stroke()
          }
        }
      }

      // Spawn pulses
      if (now - lastSpawn > PULSE_SPAWN_INTERVAL) {
        const pulse = createPulse(nodes)
        if (pulse) pulses.push(pulse)
        lastSpawn = now
      }

      // Update & draw pulses
      for (let p = pulses.length - 1; p >= 0; p--) {
        const pulse = pulses[p]
        pulse.t += dt * PULSE_SPEED / CONNECTION_DISTANCE
        if (pulse.t >= 1) {
          nodes[pulse.to].glow = 1
          if (Math.random() < 0.5 && pulses.length < 60) {
            const next = Math.floor(Math.random() * nodes.length)
            if (next !== pulse.to) {
              pulses.push({ from: pulse.to, to: next, t: 0, intensity: pulse.intensity * 0.65 })
            }
          }
          pulses.splice(p, 1)
          continue
        }

        const from = nodes[pulse.from]
        const to = nodes[pulse.to]
        const x = from.x + (to.x - from.x) * pulse.t
        const y = from.y + (to.y - from.y) * pulse.t
        const alpha = pulse.intensity * (1 - pulse.t * 0.4)

        // Glow trail
        const grad = ctx.createRadialGradient(x, y, 0, x, y, 22)
        grad.addColorStop(0, `rgba(${pulseColor[0]}, ${pulseColor[1]}, ${pulseColor[2]}, ${alpha * 0.5})`)
        grad.addColorStop(1, `rgba(${pulseColor[0]}, ${pulseColor[1]}, ${pulseColor[2]}, 0)`)
        ctx.beginPath()
        ctx.arc(x, y, 22, 0, Math.PI * 2)
        ctx.fillStyle = grad
        ctx.fill()

        // Core dot
        ctx.beginPath()
        ctx.arc(x, y, PULSE_RADIUS, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${pulseColor[0]}, ${pulseColor[1]}, ${pulseColor[2]}, ${alpha})`
        ctx.fill()
      }

      // Draw nodes
      for (const node of nodes) {
        const glowAlpha = 0.6 + node.glow * 0.4
        const radius = NODE_RADIUS + node.glow * 3

        if (node.glow > 0.1) {
          const glowGrad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, 16 + node.glow * 12)
          glowGrad.addColorStop(0, `rgba(${pulseColor[0]}, ${pulseColor[1]}, ${pulseColor[2]}, ${node.glow * 0.5})`)
          glowGrad.addColorStop(1, `rgba(${pulseColor[0]}, ${pulseColor[1]}, ${pulseColor[2]}, 0)`)
          ctx.beginPath()
          ctx.arc(node.x, node.y, 16 + node.glow * 12, 0, Math.PI * 2)
          ctx.fillStyle = glowGrad
          ctx.fill()
        }

        ctx.beginPath()
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${nodeColor[0]}, ${nodeColor[1]}, ${nodeColor[2]}, ${glowAlpha})`
        ctx.fill()

        // Draw floating LLM/coding words
        if (node.word && node.wordAlpha > 0.01) {
          ctx.font = `${isMobile ? 9 : 10}px Inter, system-ui, sans-serif`
          ctx.fillStyle = `${textColor}${node.wordAlpha})`
          ctx.fillText(node.word, node.x + 6, node.y - 4)
        }
      }

      if (!prefersReduced) {
        animRef.current = requestAnimationFrame(frame)
      }
    }

    if (!prefersReduced) {
      animRef.current = requestAnimationFrame(frame)
    } else {
      drawStaticFrame(ctx, nodes, w, h, isDark)
    }

    return () => {
      cancelAnimationFrame(animRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      aria-hidden="true"
    />
  )
}

function drawStaticFrame(ctx, nodes, w, h, isDark) {
  const nodeColor = isDark ? [20, 184, 166] : [14, 165, 233]
  const lineColor = isDark ? '20, 184, 166' : '14, 165, 233'

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x
      const dy = nodes[i].y - nodes[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < CONNECTION_DISTANCE) {
        const alpha = (1 - dist / CONNECTION_DISTANCE) * (isDark ? 0.35 : 0.2)
        ctx.beginPath()
        ctx.moveTo(nodes[i].x, nodes[i].y)
        ctx.lineTo(nodes[j].x, nodes[j].y)
        ctx.strokeStyle = `rgba(${lineColor}, ${alpha})`
        ctx.lineWidth = 0.8
        ctx.stroke()
      }
    }
  }
  for (const node of nodes) {
    ctx.beginPath()
    ctx.arc(node.x, node.y, NODE_RADIUS, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${nodeColor[0]}, ${nodeColor[1]}, ${nodeColor[2]}, 0.6)`
    ctx.fill()
  }
}
