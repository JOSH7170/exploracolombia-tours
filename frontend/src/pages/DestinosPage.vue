<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const destinos = ref([])
const selectedId = ref(null)
const busquedaDestinos = ref(store.searchQuery)
watch(() => store.searchQuery, v => busquedaDestinos.value = v, { immediate: true })
const destinosFiltrados = computed(() => {
  const q = busquedaDestinos.value.toLowerCase().trim()
  if (!q) return destinos.value
  return destinos.value.filter(d =>
    d.nombre.toLowerCase().includes(q) ||
    d.departamento.toLowerCase().includes(q) ||
    d.tipo.toLowerCase().includes(q) ||
    d.descripcion.toLowerCase().includes(q)
  )
})

onMounted(async () => {
  try {
    destinos.value = await api.getDestinos()
  } catch (e) {
    store.toast('Error al cargar destinos: ' + e.message, 'error')
  }
})

function toggleSelect(id) {
  selectedId.value = selectedId.value === id ? null : id
}

async function viewDetalle(id) {
  try {
    const d = await api.getDestino(id)
    if (!d) return
    let extras = []
    try {
      extras = JSON.parse(d.imagenes || '[]')
    } catch { /* ignore */ }
    extras = extras.filter(u => u !== d.imagen)
    const todas = [d.imagen, ...extras].filter(Boolean)
    let galeriaHtml = '<div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:16px;scroll-snap-type:x mandatory">'
    todas.forEach(url => {
      galeriaHtml += '<div style="flex:0 0 260px;height:170px;border-radius:var(--radius-sm);overflow:hidden;scroll-snap-align:start;flex-shrink:0"><img src="' + url.replace(/"/g, '&quot;') + '" style="width:100%;height:100%;object-fit:cover" onerror="this.style.display=\'none\'"></div>'
    })
    galeriaHtml += '</div>'
    store.openModal(
      '<span class="material-symbols-outlined" style="color:var(--primary)">explore</span> ' + d.nombre,
      galeriaHtml + `
        <div style="display:flex;gap:8px;margin-bottom:12px">
          <span class="chip"><span class="material-symbols-outlined" style="font-size:14px">map</span> ${d.departamento}</span>
          <span class="chip"><span class="material-symbols-outlined" style="font-size:14px">${d.tipo === 'Natural' ? 'forest' : d.tipo === 'Cultural' ? 'museum' : 'hiking'}</span> ${d.tipo}</span>
        </div>
        <p style="color:var(--on-surface-variant);line-height:1.7">${d.descripcion}</p>
      `,
      false
    )
  } catch {
    store.toast('Error al cargar destino', 'error')
  }
}

async function editDestino(id) {
  const d = destinos.value.find(x => x.id === id)
  if (d) await store.openEditModal('destinos', d)
}

async function deleteDestino(id) {
  await store.deleteItem('destinos', id)
  try {
    destinos.value = await api.getDestinos()
  } catch { /* ignore */ }
}

function tipoIcon(tipo) {
  return tipo === 'Natural' ? 'forest' : tipo === 'Cultural' ? 'museum' : 'hiking'
}
</script>

<template>
  <div>
    <div class="module-header" style="flex-direction:column;align-items:flex-start">
      <div>
        <h2>Gestión de Destinos</h2>
        <p>Explora y administra los tesoros naturales y culturales de Colombia.</p>
      </div>
      <div class="search-bar">
        <span class="material-symbols-outlined search-bar-icon">search</span>
        <input type="text" placeholder="Buscar destinos..." v-model="busquedaDestinos" @input="store.searchQuery = busquedaDestinos">
      </div>
    </div>
    <div class="destinos-grid">
      <div
        v-for="d in destinosFiltrados"
        :key="d.id"
        class="destino-card"
        :class="{ selected: selectedId === d.id }"
        @click="toggleSelect(d.id)"
      >
        <div class="card-img">
          <img :src="d.imagen" alt="" @error="e => { e.target.style.display = 'none'; e.target.parentElement.style.background = 'linear-gradient(135deg, var(--primary-container), var(--secondary-container))' }" />
          <div class="card-badges">
            <span class="card-type">
              <span class="material-symbols-outlined" style="font-size:14px">{{ tipoIcon(d.tipo) }}</span>
              {{ d.tipo }}
            </span>
          </div>
          <div class="card-actions-overlay">
            <button @click.stop="viewDetalle(d.id)">
              <span class="material-symbols-outlined">visibility</span>
            </button>
            <button v-if="store.isAdmin" @click.stop="editDestino(d.id)">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button v-if="store.isAdmin" class="danger" @click.stop="deleteDestino(d.id)">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
        <div class="card-body">
          <h3>{{ d.nombre }}</h3>
          <div class="card-location">
            <span class="material-symbols-outlined" style="font-size:16px">location_on</span>
            {{ d.departamento }}
          </div>
          <p>{{ d.descripcion }}</p>
          <div class="card-footer">
            <div class="guide-count">2 Guías Asignados</div>
          </div>
        </div>
      </div>

      <button v-if="store.isAdmin" class="add-card" @click="store.openCreateModal('destinos')">
        <div class="add-icon">
          <span class="material-symbols-outlined">add_circle</span>
        </div>
        <h4>Agregar Destino</h4>
        <p>Expandir la red turística</p>
      </button>
    </div>
  </div>
</template>
