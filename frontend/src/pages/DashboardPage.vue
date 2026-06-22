<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const router = useRouter()
const api = useApi()

const stats = ref({ paquetesActivos: 0, reservasHoy: 0, cupoTotal: 0, ingresosMes: 0 })
const ocupacion = ref([])
const ingresos = ref([])
const promociones = ref([])

onMounted(async () => {
  try {
    const paquetes = await api.getPaquetes()
    const disponibles = paquetes.filter(p => p.estado !== 'Completado')
    promociones.value = disponibles.slice(0, 3)
    if (store.isAdmin) {
      stats.value = await api.getStats()
      ocupacion.value = await api.getOcupacionData()
      ingresos.value = await api.getIngresosData(6)
    }
  } catch (e) {
    store.toast('Error al cargar datos del dashboard: ' + e.message, 'error')
  }
})

function maxIngresos() {
  return Math.max(...ingresos.value.map(i => i.ingresos), 1)
}
</script>

<template>
  <div>
    <!-- Hero brand section for admin -->
    <div v-if="store.isAdmin" class="dashboard-hero">
      <div class="hero-bg"></div>
      <div class="hero-brand">
        <svg viewBox="0 0 40 40" width="48" height="48" class="compass-logo">
          <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
          <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
          <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
          <circle cx="20" cy="20" r="2.2" fill="#006d3c"/>
        </svg>
        <h1>Panel de Administración</h1>
        <p>Gestiona destinos, paquetes, guías y más. {{ store.userNombre }}, tienes el control total de ExploraColombia Tours.</p>
      </div>
    </div>

    <!-- Welcome for regular users -->
    <div v-else class="dashboard-welcome">
      <h1>¡Hola, <span>{{ store.userNombre }}</span>!</h1>
      <p>Bienvenido de nuevo al panel de control de ExploraColombia.</p>
    </div>

    <!-- KPI Grid (admin only) -->
    <div v-if="store.isAdmin" class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-top">
          <div class="kpi-icon primary">
            <span class="material-symbols-outlined">inventory_2</span>
          </div>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">Paquetes activos</p>
          <h3 class="kpi-value">{{ stats.paquetesActivos }}</h3>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-top">
          <div class="kpi-icon gold">
            <span class="material-symbols-outlined">event_available</span>
          </div>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">Reservas hoy</p>
          <h3 class="kpi-value">{{ stats.reservasHoy }}</h3>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-top">
          <div class="kpi-icon tertiary">
            <span class="material-symbols-outlined">group</span>
          </div>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">Cupos disponibles</p>
          <h3 class="kpi-value">{{ stats.cupoTotal }}</h3>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-top">
          <div class="kpi-icon primary">
            <span class="material-symbols-outlined">payments</span>
          </div>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">Ingresos del mes</p>
          <h3 class="kpi-value">{{ api.formatCurrency(stats.ingresosMes) }}</h3>
        </div>
      </div>
    </div>

    <!-- Real-time reports (admin only) -->
    <div v-if="store.isAdmin" class="reports-row">
      <div class="report-card">
        <h3><span class="material-symbols-outlined" style="color:var(--primary);font-size:18px">bar_chart</span> Cupos disponibles por paquete</h3>
        <div class="bar-chart">
          <div v-for="o in ocupacion" :key="o.nombre" class="bar-item">
            <div class="bar-label">{{ o.nombre }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: (o.cupo > 0 ? ((o.cupo - o.reservadas) / o.cupo * 100) : 0) + '%' }" :class="{ empty: (o.cupo - o.reservadas) <= 0 }"></div>
            </div>
            <div class="bar-pct">{{ o.cupo - o.reservadas }}/{{ o.cupo }}</div>
          </div>
          <p v-if="!ocupacion.length" style="color:var(--outline);text-align:center;padding:20px">No hay datos de paquetes</p>
        </div>
      </div>
      <div class="report-card">
        <h3><span class="material-symbols-outlined" style="color:var(--secondary);font-size:18px">trending_up</span> Ingresos últimos 6 meses</h3>
        <div class="line-chart">
          <div class="chart-bars">
            <div v-for="(m, i) in ingresos" :key="i" class="chart-col">
              <div class="chart-bar-value">${{ (m.ingresos).toLocaleString('es-CO') }}</div>
              <div class="chart-bar" :style="{ height: Math.max(m.ingresos / maxIngresos() * 180, 4) + 'px' }"></div>
              <div class="chart-label">{{ m.label }}</div>
            </div>
          </div>
          <p v-if="!ingresos.length" style="color:var(--outline);text-align:center;padding:20px">No hay datos de ingresos</p>
        </div>
      </div>
    </div>

    <!-- Promo cards for regular users -->
    <div v-if="!store.isAdmin && promociones.length" class="promos-section">
      <div class="section-header">
        <h2><span class="material-symbols-outlined" style="color:var(--secondary)">local_offer</span> <span>Ofertas especiales</span></h2>
        <span class="ofertas-badge">{{ promociones.length }} ofertas disponibles</span>
      </div>
      <div class="ofertas-grid">
        <div v-for="p in promociones" :key="p.id" class="oferta-card">
          <div class="oferta-ribbon">OFERTA</div>
          <div class="oferta-img">
            <img :src="p.imagen" alt="" @error="e => e.target.style.display = 'none'" />
          </div>
          <div class="oferta-body">
            <span class="oferta-tag">{{ p.estado }}</span>
            <h3>{{ p.nombre }}</h3>
            <div class="oferta-meta">
              <span><span class="material-symbols-outlined">calendar_today</span> {{ p.duracion }}</span>
              <span><span class="material-symbols-outlined">group</span> {{ p.cupo }} cupos</span>
            </div>
            <p class="oferta-desc">{{ p.descripcion }}</p>
            <div class="oferta-footer">
              <div class="oferta-price">
                <span class="oferta-label">Por persona</span>
                <strong>{{ api.formatCurrency(p.precio) }}</strong>
              </div>
              <button class="btn-oferta" @click="router.push('/reservas')">
                <span class="material-symbols-outlined">bolt</span> Reservar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!destacados && !store.isAdmin" class="glass-card" style="border-radius:var(--radius-lg);padding:32px;text-align:center;margin-top:32px">
      <span class="material-symbols-outlined" style="font-size:48px;color:var(--outline)">explore</span>
      <h3 style="font-family:var(--font-heading);margin-top:12px;color:var(--on-surface-variant)">Bienvenido a ExploraColombia</h3>
      <p style="color:var(--outline);margin-top:4px">Los datos del dashboard aparecerán aquí cuando haya contenido disponible.</p>
    </div>
  </div>
</template>

<style scoped>
.dashboard-hero {
  border-radius: var(--radius-lg);
  padding: 32px 36px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hero-bg {
  position: absolute;
  inset: -10px;
  background: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=85') center/cover no-repeat;
  filter: blur(4px) brightness(0.5);
  z-index: 0;
}
.hero-brand {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
}
.hero-brand .compass-logo {
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
}
.hero-brand h1 {
  font-family: var(--font-heading);
  font-size: 26px;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.hero-brand p {
  color: rgba(255,255,255,0.85);
  font-size: 14px;
  max-width: 500px;
  line-height: 1.6;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.reports-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 24px;
}
.report-card {
  background: var(--surface);
  border: 1px solid var(--outline-variant);
  border-radius: var(--radius-lg);
  padding: 20px;
}
.report-card h3 {
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-family: var(--font-heading);
  color: var(--on-surface);
}
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.bar-label {
  font-size: 12px;
  color: var(--on-surface-variant);
  width: 100px;
  flex-shrink: 0;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}
.bar-track {
  flex: 1;
  height: 20px;
  background: var(--surface-container-high);
  border-radius: 10px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 10px;
  transition: width 0.6s ease;
  min-width: 4px;
}
.bar-fill.empty {
  background: var(--error-container);
}
.bar-pct {
  font-size: 12px;
  font-weight: 700;
  color: var(--on-surface-variant);
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}
.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 200px;
  padding-bottom: 24px;
  position: relative;
}
.chart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}
.chart-bar {
  width: 100%;
  max-width: 48px;
  background: linear-gradient(to top, var(--primary), var(--secondary));
  border-radius: 6px 6px 0 0;
  transition: height 0.6s ease;
}
.chart-bar-value {
  font-size: 10px;
  font-weight: 700;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
  white-space: nowrap;
}
.chart-label {
  font-size: 10px;
  color: var(--outline);
  margin-top: 6px;
  text-transform: uppercase;
  font-weight: 600;
}
</style>
