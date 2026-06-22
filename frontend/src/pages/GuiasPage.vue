<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const guias = ref([])
const selectedId = ref(null)
const busquedaGuias = ref(store.searchQuery)

watch(() => store.searchQuery, v => busquedaGuias.value = v, { immediate: true })

const guiasFiltrados = computed(() => {
  const q = busquedaGuias.value.toLowerCase().trim()
  if (!q) return guias.value
  return guias.value.filter(g =>
    g.nombre.toLowerCase().includes(q) ||
    (g.email || '').toLowerCase().includes(q) ||
    (g.idiomas || []).some(i => i.toLowerCase().includes(q))
  )
})

const descripciones = {
  1: 'Guía profesional especializado en ecoturismo y aventura. Con más de 8 años de experiencia guiando grupos por el Eje Cafetero y la Sierra Nevada. Apasionado por la naturaleza y la cultura colombiana.',
  2: 'Guía bilingüe con amplio conocimiento en historia colonial y rutas culturales. Experta en recorridos por Cartagena y la costa Caribe. Ha trabajado con turistas de más de 15 países diferentes.',
  3: 'Guía políglota especializado en turismo de aventura y expediciones. Certificado en primeros auxilios en áreas remotas. Conocedor profundo de la flora y fauna de la Sierra Nevada de Santa Marta.',
  4: 'Guía experta en turismo cultural y rutas patrimoniales. Con estudios en antropología y arqueología. Ofrece recorridos detallados por sitios históricos y patrimonio cultural de Colombia.',
  5: 'Guía certificado con enfoque en turismo sostenible y astroturismo. Especialista en el Desierto de la Tatacoa y el Cañón del Chicamocha. Guía grupos pequeños con atención personalizada.',
}

function descripcionGuia(g) {
  return descripciones[g.id] || `${g.nombre} es un guía turístico certificado con experiencia en ${(g.idiomas||[]).join(', ')}. Ofrece recorridos personalizados y conocimiento profundo de la cultura colombiana.`
}

onMounted(async () => {
  try {
    guias.value = await api.getGuias()
  } catch (e) {
    store.toast('Error al cargar guías: ' + e.message, 'error')
  }
})

function toggleSelect(id) {
  selectedId.value = selectedId.value === id ? null : id
}

function viewGuia(g) {
  const langs = (g.idiomas || []).join(', ')
  store.openModal(
    '<span class="material-symbols-outlined" style="color:var(--tertiary)">badge</span> ' + g.nombre,
    `
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;padding:16px;background:var(--surface-container-low);border-radius:var(--radius-sm)">
        <div style="width:56px;height:56px;border-radius:50%;background:var(--tertiary-container);display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <span class="material-symbols-outlined" style="font-size:28px;color:var(--on-tertiary-container)">person</span>
        </div>
        <div>
          <strong style="font-size:16px">${g.nombre}</strong>
          <div style="display:flex;gap:8px;margin-top:4px">
            <span class="chip">${langs}</span>
            <span class="chip guia-status ${(g.estado||'').toLowerCase()}">${g.estado}</span>
          </div>
        </div>
      </div>
      <div style="line-height:1.8;color:var(--on-surface-variant);margin-bottom:12px">
        <p>${descripcionGuia(g)}</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        ${g.email ? '<a href="mailto:' + g.email + '" style="display:flex;align-items:center;gap:6px;color:var(--primary);text-decoration:none;font-size:14px"><span class="material-symbols-outlined" style="font-size:18px">mail</span> ' + g.email + '</a>' : ''}
        ${g.telefono ? '<a href="tel:' + g.telefono + '" style="display:flex;align-items:center;gap:6px;color:var(--primary);text-decoration:none;font-size:14px"><span class="material-symbols-outlined" style="font-size:18px">call</span> ' + g.telefono + '</a>' : ''}
      </div>
    `,
    false
  )
}

async function editGuia(id) {
  const g = guias.value.find(x => x.id === id)
  if (g) await store.openEditModal('guias', g)
}

async function deleteGuia(id) {
  await store.deleteItem('guias', id)
  try {
    guias.value = await api.getGuias()
  } catch { /* ignore */ }
}

function mailTo(g) {
  if (g.email) window.location.href = 'mailto:' + g.email
}

function telTo(g) {
  if (g.telefono) window.location.href = 'tel:' + g.telefono
}
</script>

<template>
  <div>
    <div class="module-header" style="flex-direction:column;align-items:flex-start">
      <div>
        <h2>Guías Turísticos</h2>
        <p>Conoce a nuestros guías turísticos y contacta con ellos.</p>
      </div>
      <div class="search-bar">
        <span class="material-symbols-outlined search-bar-icon">search</span>
        <input type="text" placeholder="Buscar guías por nombre, idioma..." v-model="busquedaGuias" @input="store.searchQuery = busquedaGuias">
      </div>
    </div>
    <div class="guias-grid">
      <div
        v-for="g in guiasFiltrados"
        :key="g.id"
        class="guia-card"
        :class="{ selected: selectedId === g.id }"
      >
        <div class="guia-card-top">
          <div class="guia-avatar">{{ g.nombre.charAt(0) }}</div>
          <div class="guia-info">
            <h4>{{ g.nombre }}</h4>
            <div class="guia-langs">{{ (g.idiomas||[]).join(' · ') }}</div>
          </div>
          <span class="guia-estado" :class="(g.estado||'').toLowerCase()">{{ g.estado }}</span>
        </div>
        <div class="guia-card-contact">
          <a v-if="g.email" :href="'mailto:'+g.email" class="guia-link" @click.stop>
            <span class="material-symbols-outlined">mail</span>
            <span>{{ g.email }}</span>
          </a>
          <a v-if="g.telefono" :href="'tel:'+g.telefono" class="guia-link" @click.stop>
            <span class="material-symbols-outlined">call</span>
            <span>{{ g.telefono }}</span>
          </a>
        </div>
        <div class="guia-card-actions">
          <button class="btn-perfil" @click.stop="viewGuia(g)">
            <span class="material-symbols-outlined">visibility</span> Ver Perfil
          </button>
          <div class="guia-actions-right">
            <button v-if="g.email" class="btn-icon-sm" title="Enviar correo" @click.stop="mailTo(g)">
              <span class="material-symbols-outlined">mail</span>
            </button>
            <button v-if="g.telefono" class="btn-icon-sm" title="Llamar" @click.stop="telTo(g)">
              <span class="material-symbols-outlined">call</span>
            </button>
            <button v-if="store.isAdmin" class="btn-icon-sm" title="Editar" @click.stop="editGuia(g.id)">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button v-if="store.isAdmin" class="btn-icon-sm danger" title="Eliminar" @click.stop="deleteGuia(g.id)">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guia-card {
  background: var(--surface);
  border: 1px solid var(--outline-variant);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.guia-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 16px rgba(0,82,44,0.08);
}
.guia-card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.guia-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}
.guia-info {
  flex: 1;
  min-width: 0;
}
.guia-info h4 {
  font-size: 15px;
  color: var(--on-surface);
  margin: 0;
}
.guia-langs {
  font-size: 12px;
  color: var(--outline);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.guia-estado {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}
.guia-estado.activo {
  background: rgba(16,185,129,0.12);
  color: #059669;
}
.guia-card-contact {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 0;
  border-top: 1px solid var(--outline-variant);
  border-bottom: 1px solid var(--outline-variant);
}
.guia-link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--on-surface-variant);
  text-decoration: none;
  transition: color 0.2s;
}
.guia-link:hover {
  color: var(--primary);
}
.guia-link .material-symbols-outlined {
  font-size: 16px;
  color: var(--outline);
}
.guia-link:hover .material-symbols-outlined {
  color: var(--primary);
}
.guia-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-perfil {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border: 1px solid var(--primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-perfil:hover {
  background: var(--primary);
  color: var(--on-primary);
}
.btn-perfil .material-symbols-outlined {
  font-size: 16px;
}
.guia-actions-right {
  display: flex;
  gap: 4px;
  margin-left: auto;
}
.btn-icon-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.btn-icon-sm:hover {
  background: var(--surface-container-high);
  color: var(--primary);
}
.btn-icon-sm.danger:hover {
  background: var(--error-container);
  color: var(--on-error-container);
}
.btn-icon-sm .material-symbols-outlined {
  font-size: 18px;
}
</style>
