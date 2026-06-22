<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const tab = ref('ocupacion')
const canvasOcupacion = ref(null)
const canvasIngresos = ref(null)

onMounted(async () => {
  await renderOcupacionChart()
})

function setTab(t) {
  tab.value = t
  setTimeout(() => {
    if (t === 'ocupacion') renderOcupacionChart()
    if (t === 'ingresos') renderIngresosChart()
  }, 50)
}

async function renderOcupacionChart() {
  const canvas = canvasOcupacion.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  try {
    const data = await api.getOcupacionData()
    const labels = data.map(d => d.nombre)
    const values = data.map(d => d.porcentaje)
    const colors = values.map(v => v > 70 ? '#00522c' : v > 40 ? '#ffb700' : '#ba1a1a')
    drawBarChart(ctx, labels, values, colors, 'Ocupación por Paquete (%)')
  } catch (e) {
    store.toast('Error al cargar reporte de ocupación', 'error')
  }
}

async function renderIngresosChart() {
  const canvas = canvasIngresos.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  try {
    const data = await api.getIngresosData(6)
    const labels = data.map(d => d.label)
    const values = data.map(d => d.ingresos)
    drawLineChart(ctx, labels, values, 'Ingresos Mensuales')
  } catch (e) {
    store.toast('Error al cargar reporte de ingresos', 'error')
  }
}

function drawBarChart(ctx, labels, values, colors, title) {
  const width = ctx.canvas.width
  const height = ctx.canvas.height
  const padding = { top: 40, right: 20, bottom: 60, left: 60 }
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom

  ctx.clearRect(0, 0, width, height)
  ctx.fillStyle = '#3f4941'
  ctx.font = '14px Inter, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(title, width / 2, 22)

  const maxV = Math.max(...values, 100)
  const barW = Math.min(40, chartW / labels.length * 0.6)
  const gap = chartW / labels.length

  ctx.strokeStyle = '#e2e2e5'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + chartH - (chartH * i / 4)
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
    ctx.fillStyle = '#6f7a70'
    ctx.font = '11px Inter, sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(Math.round(maxV * i / 4) + '%', padding.left - 8, y + 4)
  }

  labels.forEach((label, i) => {
    const x = padding.left + i * gap + (gap - barW) / 2
    const h = (values[i] / maxV) * chartH
    const y = padding.top + chartH - h

    const gradient = ctx.createLinearGradient(x, y, x, padding.top + chartH)
    gradient.addColorStop(0, colors[i])
    gradient.addColorStop(1, colors[i] + '40')
    ctx.fillStyle = gradient

    ctx.beginPath()
    ctx.roundRect(x, y, barW, h, [4, 4, 0, 0])
    ctx.fill()

    ctx.fillStyle = '#1a1c1e'
    ctx.font = '12px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(values[i] + '%', x + barW / 2, y - 6)

    ctx.fillStyle = '#3f4941'
    ctx.font = '10px Inter, sans-serif'
    ctx.fillText(label.length > 12 ? label.slice(0, 12) + '...' : label, x + barW / 2, padding.top + chartH + 16)
  })
}

function drawLineChart(ctx, labels, values, title) {
  const width = ctx.canvas.width
  const height = ctx.canvas.height
  const padding = { top: 40, right: 20, bottom: 60, left: 80 }
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom

  ctx.clearRect(0, 0, width, height)

  ctx.fillStyle = '#3f4941'
  ctx.font = '14px Inter, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(title, width / 2, 22)

  const maxV = Math.max(...values, 1) * 1.2
  const points = []

  ctx.strokeStyle = '#e2e2e5'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + chartH - (chartH * i / 4)
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
    ctx.fillStyle = '#6f7a70'
    ctx.font = '11px Inter, sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText('$' + Math.round(maxV * i / 4 / 1000) + 'k', padding.left - 8, y + 4)
  }

  labels.forEach((label, i) => {
    const x = padding.left + (i / (labels.length - 1 || 1)) * chartW
    const y = padding.top + chartH - (values[i] / maxV) * chartH
    points.push({ x, y })

    ctx.fillStyle = '#3f4941'
    ctx.font = '10px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(label, x, padding.top + chartH + 16)
  })

  if (points.length > 1) {
    ctx.beginPath()
    ctx.moveTo(points[0].x, padding.top + chartH)
    points.forEach(p => ctx.lineTo(p.x, p.y))
    ctx.lineTo(points[points.length - 1].x, padding.top + chartH)
    ctx.closePath()
    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH)
    gradient.addColorStop(0, 'rgba(0, 82, 44, 0.15)')
    gradient.addColorStop(1, 'rgba(0, 82, 44, 0.02)')
    ctx.fillStyle = gradient
    ctx.fill()
  }

  ctx.beginPath()
  ctx.strokeStyle = '#00522c'
  ctx.lineWidth = 3
  ctx.lineJoin = 'round'
  points.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p.x, p.y)
    else ctx.lineTo(p.x, p.y)
  })
  ctx.stroke()

  points.forEach(p => {
    ctx.beginPath()
    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2)
    ctx.fillStyle = '#00522c'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
  })
}
</script>

<template>
  <div>
    <div class="module-header" style="flex-direction:column;align-items:flex-start">
      <div>
        <h2>Reportes y Estadísticas</h2>
        <p>Visualiza el rendimiento y la ocupación de tus paquetes turísticos.</p>
      </div>
    </div>

    <div class="reportes-tabs">
      <button class="tab-btn" :class="{ active: tab === 'ocupacion' }" @click="setTab('ocupacion')">
        <span class="material-symbols-outlined" style="font-size:16px">donut_small</span> Ocupación
      </button>
      <button class="tab-btn" :class="{ active: tab === 'ingresos' }" @click="setTab('ingresos')">
        <span class="material-symbols-outlined" style="font-size:16px">trending_up</span> Ingresos
      </button>
    </div>

    <div v-show="tab === 'ocupacion'" class="reportes-panel active">
      <div class="chart-container">
        <canvas ref="canvasOcupacion" width="500" height="300"></canvas>
      </div>
    </div>

    <div v-show="tab === 'ingresos'" class="reportes-panel active">
      <div class="chart-container">
        <canvas ref="canvasIngresos" width="500" height="300"></canvas>
      </div>
    </div>
  </div>
</template>
