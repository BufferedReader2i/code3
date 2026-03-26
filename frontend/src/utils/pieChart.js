/* 柔和区分度配色 */
export const PIE_COLORS = [
  '#94a3b8', '#a8a29e', '#86efac', '#f9a8d4', '#c4b5fd',
  '#67e8f9', '#bef264', '#818cf8', '#fcd34d', '#f472b6',
  '#5eead4', '#fdba74'
]

export function buildPie(items) {
  if (!items || !items.length) return { style: {}, legend: [] }
  let cum = 0
  const legend = items.map((c, i) => {
    const pct = Math.max(0, Number(c.score) || 0) * 100
    const color = PIE_COLORS[i % PIE_COLORS.length]
    return { name: c.name, score: c.score, color }
  })
  const stops = items.map((c, i) => {
    const pct = Math.max(0, Number(c.score) || 0) * 100
    const color = PIE_COLORS[i % PIE_COLORS.length]
    const start = cum
    cum += pct
    return `${color} ${start}% ${cum}%`
  })
  const style = stops.length ? { background: `conic-gradient(${stops.join(', ')})` } : {}
  return { style, legend }
}

export function formatScore(s) {
  const n = Number(s)
  if (s == null || s === '' || Number.isNaN(n)) return '0.00'
  return (Math.max(0, Math.min(1, n)) * 100).toFixed(2)
}
