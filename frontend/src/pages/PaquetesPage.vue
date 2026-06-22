<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const paquetes = ref([])
const guias = ref([])
const reservas = ref([])
const busquedaPaquetes = ref(store.searchQuery)

watch(() => store.searchQuery, v => busquedaPaquetes.value = v, { immediate: true })

const paquetesFiltrados = computed(() => {
  const q = busquedaPaquetes.value.toLowerCase().trim()
  if (!q) return paquetes.value
  return paquetes.value.filter(p =>
    p.nombre.toLowerCase().includes(q) ||
    p.descripcion.toLowerCase().includes(q) ||
    (p.estado || '').toLowerCase().includes(q)
  )
})

function guiasDePaquete(paqueteId) {
  const res = reservas.value.filter(r => r.paqueteId === paqueteId && r.guiaId)
  const guiaIds = [...new Set(res.map(r => r.guiaId))]
  return guias.value.filter(g => guiaIds.includes(g.id))
}

async function viewFullInfo(p) {
  const destinos = await api.getDestinosByPaquete(p.id).catch(() => [])
  const guiasAsignados = guiasDePaquete(p.id)
  const img = p.imagen && p.imagen.trim() ? p.imagen : ''

  let html = `
    ${img ? '<div style="border-radius:var(--radius-sm);overflow:hidden;margin-bottom:16px;height:200px"><img src="' + img.replace(/"/g, '&quot;') + '" style="width:100%;height:100%;object-fit:cover" onerror="this.parentElement.style.display=\'none\'"></div>' : ''}
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px">
      <span class="chip"><span class="material-symbols-outlined" style="font-size:14px">calendar_today</span> ${p.duracion}</span>
      <span class="chip"><span class="material-symbols-outlined" style="font-size:14px">group</span> Cupo: ${p.cupo}</span>
      <span class="chip" style="background:var(--primary-fixed);color:var(--on-primary-fixed)"><span class="material-symbols-outlined" style="font-size:14px">attach_money</span> ${api.formatCurrency(p.precio)}</span>
    </div>
    <p style="color:var(--on-surface-variant);line-height:1.7;margin-bottom:16px">${p.descripcion}</p>
  `

  if (destinos.length > 0) {
    html += '<h4 style="margin:0 0 10px;font-size:15px;color:var(--primary)">Destinos incluidos</h4>'
    html += '<div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">'
    destinos.forEach(d => {
      const dImg = d.imagen && d.imagen.trim() ? d.imagen : ''
      html += '<div data-navigate="destinos" data-id="' + d.id + '" style="cursor:pointer;display:flex;align-items:center;gap:12px;padding:10px;border-radius:var(--radius-sm);background:var(--surface-container-low);border:1px solid var(--outline-variant)">'
      html += '<div style="width:50px;height:50px;border-radius:var(--radius-sm);overflow:hidden;flex-shrink:0">' + (dImg ? '<img src="' + dImg.replace(/"/g, '&quot;') + '" style="width:100%;height:100%;object-fit:cover" onerror="this.parentElement.style.background=\'var(--primary-container)\'">' : '') + '</div>'
      html += '<div><strong>' + d.nombre + '</strong><div style="font-size:12px;color:var(--on-surface-variant)">' + d.departamento + ' - <span class="chip">' + d.tipo + '</span></div></div>'
      html += '</div>'
    })
    html += '</div>'
  }

  if (guiasAsignados.length > 0) {
    html += '<h4 style="margin:0 0 10px;font-size:15px;color:var(--tertiary)">Guías asignados</h4>'
    html += '<div style="display:flex;flex-direction:column;gap:8px">'
    guiasAsignados.forEach(g => {
      const langs = (g.idiomas || []).join(', ')
      html += '<div data-navigate="guias" data-id="' + g.id + '" style="cursor:pointer;display:flex;align-items:center;gap:10px;padding:10px;border-radius:var(--radius-sm);background:var(--surface-container-low)">'
      html += '<div style="width:36px;height:36px;border-radius:50%;background:var(--tertiary-container);display:flex;align-items:center;justify-content:center;color:var(--on-tertiary-container);font-size:14px;font-weight:700">' + g.nombre.charAt(0) + '</div>'
      html += '<div><strong>' + g.nombre + '</strong>'
      if (langs) html += '<div style="font-size:12px;color:var(--outline)">' + langs + '</div>'
      html += '</div>'
      if (g.email) html += '<a href="mailto:' + g.email + '" style="margin-left:auto;color:var(--primary);text-decoration:none" title="' + g.email + '"><span class="material-symbols-outlined" style="font-size:18px">mail</span></a>'
      html += '</div>'
    })
    html += '</div>'
  }

  if (destinos.length === 0 && guiasAsignados.length === 0) {
    html += '<p style="color:var(--outline);text-align:center">No hay destinos o guías asociados a este paquete.</p>'
  }

  store.openModal(
    '<span class="material-symbols-outlined" style="color:var(--secondary)">inventory_2</span> ' + p.nombre,
    html,
    false
  )
}

onMounted(async () => {
  try {
    const [paq, g, res] = await Promise.all([
      api.getPaquetes(),
      api.getGuias(),
      api.getReservas().catch(() => []),
    ])
    paquetes.value = paq
    guias.value = g
    reservas.value = res
  } catch (e) {
    store.toast('Error al cargar datos: ' + e.message, 'error')
  }
})

async function editPaquete(id) {
  const p = paquetes.value.find(x => x.id === id)
  if (p) await store.openEditModal('paquetes', p)
}

async function deletePaquete(id) {
  await store.deleteItem('paquetes', id)
  try {
    paquetes.value = await api.getPaquetes()
  } catch { /* ignore */ }
}

async function viewDestinos(id) {
  try {
    const p = paquetes.value.find(x => x.id === id)
    if (!p) return
    const destinos = await api.getDestinosByPaquete(id)

    if (destinos.length === 0) {
      store.openModal(
        '<span class="material-symbols-outlined" style="color:var(--secondary)">map</span> Destinos: ' + p.nombre,
        '<p style="color:var(--outline)">No hay destinos asociados a este paquete.</p>',
        false
      )
      return
    }

    let itemsHtml = ''
    destinos.forEach(d => {
      const imgUrl = d.imagen && d.imagen.trim() ? d.imagen : ''
      itemsHtml += '<div data-navigate="destinos" data-id="' + d.id + '" style="cursor:pointer;display:flex;align-items:center;gap:14px;padding:12px;border-radius:var(--radius-sm);background:var(--surface-container-low);border:1px solid var(--outline-variant)">'
      itemsHtml += '<div style="width:50px;height:50px;border-radius:var(--radius-sm);overflow:hidden;flex-shrink:0">' + (imgUrl ? '<img src="' + imgUrl.replace(/"/g, '&quot;') + '" style="width:100%;height:100%;object-fit:cover" onerror="this.parentElement.style.background=\'var(--primary-container)\'">' : '') + '</div>'
      itemsHtml += '<div>'
      itemsHtml += '<strong>' + d.nombre + '</strong>'
      itemsHtml += '<div style="font-size:13px;color:var(--on-surface-variant)"><span class="material-symbols-outlined" style="font-size:14px">map</span> ' + d.departamento + ' - <span class="chip">' + d.tipo + '</span></div>'
      itemsHtml += '</div></div>'
    })

    store.openModal(
      '<span class="material-symbols-outlined" style="color:var(--secondary)">map</span> Destinos: ' + p.nombre,
      '<p style="color:var(--on-surface-variant);margin-bottom:16px">Este paquete incluye los siguientes destinos:</p>' +
      '<div style="display:flex;flex-direction:column;gap:12px">' + itemsHtml + '</div>',
      false
    )
  } catch {
    store.toast('Error al cargar destinos del paquete', 'error')
  }
}
</script>

<template>
  <div>
    <div class="module-header" style="flex-direction:column;align-items:flex-start">
      <div>
        <h2>Paquetes Turísticos</h2>
        <p>Administra las experiencias y ofertas turísticas de Colombia.</p>
      </div>
      <div class="search-bar">
        <span class="material-symbols-outlined search-bar-icon">search</span>
        <input type="text" placeholder="Buscar paquetes..." v-model="busquedaPaquetes" @input="store.searchQuery = busquedaPaquetes">
      </div>
    </div>
    <div class="paquetes-grid">
      <div v-for="p in paquetesFiltrados" :key="p.id" class="paquete-card">
        <div class="paquete-img">
          <img :src="p.imagen" alt="" @error="e => { e.target.style.display = 'none'; e.target.parentElement.style.background = 'linear-gradient(135deg, var(--secondary-container), var(--tertiary-container))' }" />
          <span class="paquete-status" :class="(p.estado||'').toLowerCase()">{{ p.estado }}</span>
        </div>
        <div class="paquete-body">
          <h3>{{ p.nombre }}</h3>
          <div class="paquete-meta">
            <span><span class="material-symbols-outlined" style="font-size:16px">calendar_today</span> {{ p.duracion }}</span>
            <span><span class="material-symbols-outlined" style="font-size:16px">group</span> Cupo: {{ p.cupo }}</span>
          </div>
          <div class="paquete-price">{{ api.formatCurrency(p.precio) }}</div>
          <p style="color:var(--on-surface-variant);font-size:14px;margin-bottom:14px">{{ p.descripcion }}</p>
          <div class="paquete-guias-mini" v-if="guiasDePaquete(p.id).length">
            <span class="material-symbols-outlined">badge</span>
            <span>{{ guiasDePaquete(p.id).length }} guía{{ guiasDePaquete(p.id).length !== 1 ? 's' : '' }}</span>
            <div class="paquete-guia-avatares">
              <span v-for="g in guiasDePaquete(p.id).slice(0, 3)" :key="g.id" class="guia-mini-avatar" :title="g.nombre">{{ g.nombre.charAt(0) }}</span>
              <span v-if="guiasDePaquete(p.id).length > 3" class="guia-mini-avatar more">+{{ guiasDePaquete(p.id).length - 3 }}</span>
            </div>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">
            <button class="btn btn-primary btn-sm" @click="viewFullInfo(p)">
              <span class="material-symbols-outlined" style="font-size:16px">info</span> Más información
            </button>
            <button v-if="store.isAdmin" class="btn btn-secondary btn-sm btn-icon" @click="editPaquete(p.id)">
              <span class="material-symbols-outlined" style="font-size:16px">edit</span>
            </button>
            <button v-if="store.isAdmin" class="btn btn-danger btn-sm btn-icon" @click="deletePaquete(p.id)">
              <span class="material-symbols-outlined" style="font-size:16px">delete</span>
            </button>
          </div>
        </div>
      </div>

      <button v-if="store.isAdmin" class="add-card" @click="store.openCreateModal('paquetes')">
        <div class="add-icon">
          <span class="material-symbols-outlined">add_circle</span>
        </div>
        <h4>Agregar Paquete</h4>
        <p>Crear nueva experiencia turística</p>
      </button>
    </div>
  </div>
</template>
