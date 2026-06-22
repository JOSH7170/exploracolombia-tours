<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useRouter } from 'vue-router'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const router = useRouter()
const api = useApi()
const mobileNavOpen = ref(false)
const notificaciones = ref([])
const notisOpen = ref(false)
const settingsOpen = ref(false)

let notiTimer = null

const sections = computed(() => {
  const all = [
    { key: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
    { key: 'destinos', icon: 'explore', label: 'Destinos' },
    { key: 'paquetes', icon: 'inventory_2', label: 'Paquetes' },
  ]
  if (store.isAdmin) {
    all.push(
      { key: 'guias', icon: 'badge', label: 'Guías' },
    )
  } else {
    all.push(
      { key: 'guias', icon: 'badge', label: 'Guías' },
      { key: 'reservas', icon: 'event_available', label: 'Reservas' },
    )
  }
  return all
})

const noLeidas = computed(() => notificaciones.value.filter(n => !n.leida).length)

onMounted(async () => {
  await cargarNotis()
  notiTimer = setInterval(cargarNotis, 30000)
})

onUnmounted(() => {
  if (notiTimer) clearInterval(notiTimer)
})

async function cargarNotis() {
  try {
    notificaciones.value = await api.getNotificaciones()
  } catch {}
}

function goTo(section) {
  mobileNavOpen.value = false
  store.navigate(section)
  router.push(section === 'dashboard' ? '/' : `/${section}`)
}

function handleLogout() {
  store.logout()
  router.push('/login')
}

function toggleNotis() {
  notisOpen.value = !notisOpen.value
}

async function leerNoti(id) {
  await api.leerNotificacion(id)
  notificaciones.value = notificaciones.value.map(n =>
    n.id === id ? { ...n, leida: 1 } : n
  )
}

async function leerTodas() {
  await api.leerTodasNotificaciones()
  notificaciones.value = notificaciones.value.map(n => ({ ...n, leida: 1 }))
}

async function eliminarNoti(id) {
  try {
    await api.eliminarNotificacion(id)
    notificaciones.value = notificaciones.value.filter(n => n.id !== id)
  } catch {}
}

function tipoIcon(tipo) {
  const icons = {
    reserva: 'event_available',
    pago: 'payments',
    alerta: 'warning',
    sistema: 'info',
  }
  return icons[tipo] || 'notifications'
}

function tipoClass(tipo) {
  const classes = {
    reserva: 'noti-reserva',
    pago: 'noti-pago',
    alerta: 'noti-alerta',
    sistema: 'noti-sistema',
  }
  return classes[tipo] || ''
}

// Settings
const setPassword = reactive({ actual: '', nueva: '', confirmar: '' })
const setProfile = reactive({ nombre: '', email: '' })
const passMsg = ref('')
const profMsg = ref('')

function openSettings() {
  settingsOpen.value = true
  setProfile.nombre = store.userNombre
  passMsg.value = ''
  profMsg.value = ''
}

async function savePassword() {
  if (!setPassword.actual || !setPassword.nueva) {
    passMsg.value = 'Completa todos los campos'
    return
  }
  if (setPassword.nueva.length < 4) {
    passMsg.value = 'Mínimo 4 caracteres'
    return
  }
  if (setPassword.nueva !== setPassword.confirmar) {
    passMsg.value = 'Las contraseñas no coinciden'
    return
  }
  try {
    const res = await api.cambiarContrasena(setPassword.actual, setPassword.nueva, store.username)
    store.toast(res.message, 'success')
    setPassword.actual = ''
    setPassword.nueva = ''
    setPassword.confirmar = ''
    passMsg.value = ''
  } catch (e) {
    passMsg.value = e.message
  }
}

async function saveProfile() {
  if (!setProfile.nombre || !setProfile.email) {
    profMsg.value = 'Nombre y email son requeridos'
    return
  }
  try {
    const res = await api.actualizarPerfil(store.username, setProfile.nombre, setProfile.email)
    store.userNombre = res.nombre
    profMsg.value = ''
    store.toast(res.message, 'success')
  } catch (e) {
    profMsg.value = e.message
  }
}

</script>

<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ open: mobileNavOpen }">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 40 40" width="24" height="24" class="compass-logo">
            <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
            <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
            <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
            <circle cx="20" cy="20" r="2.2" fill="#006d3c"/>
          </svg>
        </div>
        <div class="brand-text">
          <h1>ExploraColombia</h1>
          <p v-if="store.isAdmin">Admin Portal</p>
        </div>
      </div>

      <nav class="sidebar-nav">
        <button
          v-for="s in sections"
          :key="s.key"
          class="nav-item"
          :class="{ active: store.currentSection === s.key }"
          @click="goTo(s.key)"
        >
          <span class="material-symbols-outlined nav-icon">{{ s.icon }}</span>
          <span>{{ s.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="handleLogout">
          <span class="material-symbols-outlined">logout</span>
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </aside>

    <!-- Main Area -->
    <div class="main-content">
      <!-- Top Bar -->
      <header class="topbar">
        <div class="topbar-left">
          <div class="topbar-search">
            <span class="material-symbols-outlined search-icon">search</span>
            <input type="text" placeholder="Buscar destinos, guías o paquetes..." v-model="store.searchQuery" />
          </div>
        </div>
        <div class="topbar-right">
          <div class="noti-wrapper">
            <button class="icon-btn" @click="toggleNotis">
              <span class="material-symbols-outlined">notifications</span>
              <span v-if="noLeidas" class="badge-dot">{{ noLeidas > 9 ? '9+' : noLeidas }}</span>
            </button>
            <div v-if="notisOpen" class="noti-dropdown" @click.stop>
              <div class="noti-header">
                <h4>Notificaciones</h4>
                <button v-if="noLeidas" class="btn-text" @click="leerTodas">Leer todas</button>
              </div>
              <div class="noti-list">
                <div
                  v-for="n in notificaciones"
                  :key="n.id"
                  class="noti-item"
                  :class="{ leida: n.leida }"
                >
                  <span class="noti-icon" :class="tipoClass(n.tipo)">
                    <span class="material-symbols-outlined">{{ tipoIcon(n.tipo) }}</span>
                  </span>
                  <div class="noti-content" @click="leerNoti(n.id)">
                    <p>{{ n.mensaje }}</p>
                    <span class="noti-time">{{ n.creada }}</span>
                  </div>
                  <button class="noti-delete" @click.stop="eliminarNoti(n.id)" title="Eliminar notificación">
                    <span class="material-symbols-outlined">close</span>
                  </button>
                </div>
                <div v-if="!notificaciones.length" class="noti-empty">
                  <span class="material-symbols-outlined">notifications_off</span>
                  <p>No hay notificaciones</p>
                </div>
              </div>
            </div>
          </div>
          <button class="icon-btn" @click="openSettings">
            <span class="material-symbols-outlined">settings</span>
          </button>
          <div class="topbar-divider"></div>
          <div class="topbar-user">
            <div class="user-info">
              <p class="user-name">{{ store.userNombre || 'Usuario' }}</p>
              <p class="user-role">{{ store.isAdmin ? 'Fox' : 'Usuario' }}</p>
            </div>
            <div class="user-avatar">
              <span class="material-symbols-outlined">{{ store.isAdmin ? 'admin_panel_settings' : 'person' }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Page Content -->
      <div class="content-wrapper">
        <router-view />
      </div>
    </div>

    <!-- Mobile Bottom Nav -->
    <nav class="mobile-bottom-nav">
      <button
        v-for="s in sections"
        :key="s.key"
        class="mobile-nav-item"
        :class="{ active: store.currentSection === s.key }"
        @click="goTo(s.key)"
      >
        <span class="material-symbols-outlined">{{ s.icon }}</span>
        <span class="mobile-nav-label">{{ s.label }}</span>
      </button>
    </nav>

    <!-- Settings Modal -->
    <Teleport to="body">
      <div v-if="settingsOpen" class="settings-overlay" @click="settingsOpen = false">
        <div class="settings-modal" @click.stop>
          <div class="settings-header">
            <h2><span class="material-symbols-outlined">settings</span> Configuración</h2>
            <button class="icon-btn" @click="settingsOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="settings-body">
            <!-- Perfil -->
            <section class="settings-section">
              <h3><span class="material-symbols-outlined">person</span> Perfil</h3>
              <div class="form-group">
                <label>Nombre</label>
                <input type="text" v-model="setProfile.nombre" placeholder="Tu nombre" />
              </div>
              <div class="form-group">
                <label>Email</label>
                <input type="email" v-model="setProfile.email" placeholder="tu@email.com" />
              </div>
              <p v-if="profMsg" class="settings-msg error">{{ profMsg }}</p>
              <button class="btn btn-primary" @click="saveProfile">
                <span class="material-symbols-outlined">save</span> Guardar cambios
              </button>
            </section>

            <div class="settings-divider"></div>

            <!-- Contraseña -->
            <section class="settings-section">
              <h3><span class="material-symbols-outlined">lock</span> Cambiar contraseña</h3>
              <div class="form-group">
                <label>Contraseña actual</label>
                <input type="password" v-model="setPassword.actual" placeholder="••••••" />
              </div>
              <div class="form-group">
                <label>Nueva contraseña</label>
                <input type="password" v-model="setPassword.nueva" placeholder="Mínimo 4 caracteres" />
              </div>
              <div class="form-group">
                <label>Confirmar nueva contraseña</label>
                <input type="password" v-model="setPassword.confirmar" placeholder="Repite la nueva" />
              </div>
              <p v-if="passMsg" class="settings-msg error">{{ passMsg }}</p>
              <button class="btn btn-primary" @click="savePassword">
                <span class="material-symbols-outlined">key</span> Cambiar contraseña
              </button>
            </section>


          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.mobile-bottom-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: rgba(249, 249, 252, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  justify-content: space-around;
  align-items: center;
  padding: 0 16px;
  z-index: 50;
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  background: none;
  border: none;
  color: var(--on-surface-variant);
  padding: 4px;
  transition: color 0.2s;
}

.mobile-nav-item.active {
  color: var(--primary);
}

.mobile-nav-item .material-symbols-outlined {
  font-size: 22px;
}

.mobile-nav-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Notifications */
.noti-wrapper {
  position: relative;
}

.badge-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background: var(--error, #ef4444);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  pointer-events: none;
}

.noti-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 480px;
  background: var(--surface, #fff);
  border: 1px solid var(--outline-variant, #e2e8f0);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
  z-index: 100;
  overflow: hidden;
}

.noti-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--outline-variant, #e2e8f0);
}

.noti-header h4 {
  font-family: var(--font-heading);
  font-size: 16px;
  color: var(--on-surface);
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.noti-list {
  max-height: 400px;
  overflow-y: auto;
}

.noti-item {
  display: flex;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid var(--outline-variant, #f1f5f9);
}

.noti-item:hover {
  background: var(--surface-container-high, #f8fafc);
}

.noti-item.leida {
  opacity: 0.65;
}

.noti-delete {
  background: none;
  border: none;
  color: var(--outline);
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
  opacity: 0;
}
.noti-item:hover .noti-delete {
  opacity: 1;
}
.noti-delete:hover {
  background: var(--error-container);
  color: var(--on-error-container);
}

.noti-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.noti-icon .material-symbols-outlined {
  font-size: 18px;
}

.noti-icon.noti-reserva {
  background: rgba(13, 148, 136, 0.12);
  color: var(--primary, #0d9488);
}

.noti-icon.noti-pago {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.noti-icon.noti-alerta {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.noti-icon.noti-sistema {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.noti-content p {
  font-size: 13px;
  color: var(--on-surface, #1e293b);
  line-height: 1.4;
  margin-bottom: 4px;
}

.noti-time {
  font-size: 11px;
  color: var(--outline, #94a3b8);
}

.noti-empty {
  padding: 40px;
  text-align: center;
  color: var(--outline, #94a3b8);
}

.noti-empty .material-symbols-outlined {
  font-size: 36px;
  margin-bottom: 8px;
}

.noti-empty p {
  font-size: 14px;
}

/* Settings Modal */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-modal {
  background: var(--surface, #fff);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--outline-variant, #e2e8f0);
  position: sticky;
  top: 0;
  background: var(--surface, #fff);
  z-index: 1;
}

.settings-header h2 {
  font-family: var(--font-heading);
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-header h2 .material-symbols-outlined {
  color: var(--primary);
}

.settings-body {
  padding: 24px;
}

.settings-section {
  margin-bottom: 8px;
}

.settings-section h3 {
  font-family: var(--font-heading);
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--on-surface);
}

.settings-section h3 .material-symbols-outlined {
  font-size: 20px;
  color: var(--primary);
}

.settings-section .form-group {
  margin-bottom: 12px;
}

.settings-section .form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
}

.settings-section .form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--outline, #cbd5e1);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background: var(--surface-container, #f8fafc);
  color: var(--on-surface);
  transition: border-color 0.2s;
}

.settings-section .form-group input:focus {
  border-color: var(--primary);
  outline: none;
}

.settings-section .btn {
  margin-top: 4px;
}

.settings-msg {
  font-size: 13px;
  margin-bottom: 8px;
}

.settings-msg.error {
  color: var(--error, #ef4444);
}

.settings-divider {
  height: 1px;
  background: var(--outline-variant, #e2e8f0);
  margin: 24px 0;
}

@media (max-width: 1024px) {
  .menu-btn {
    display: flex !important;
    align-items: center;
    justify-content: center;
  }

  .mobile-bottom-nav {
    display: flex;
  }

  .main-content {
    padding-bottom: 64px;
  }
}
</style>
