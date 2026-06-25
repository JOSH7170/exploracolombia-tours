<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const router = useRouter()
const api = useApi()
const loading = ref(false)
const activeSlide = ref(0)
const prevSlide = ref(null)
const errorMsg = ref('')
const successMsg = ref('')

// Login fields
const username = ref('')
const password = ref('')

// Register fields
const regNombre = ref('')
const regEmail = ref('')
const regUsername = ref('')
const regPassword = ref('')
const regConfirm = ref('')

// Verify fields
const verifyEmail = ref('')
const verifyCode = ref('')

// Forgot password fields
const forgotEmail = ref('')
const forgotCode = ref('')
const forgotNewPassword = ref('')
const forgotConfirm = ref('')
const forgotStep = ref('email')

const mode = ref('login')
const registeredEmail = ref('')

const bgSlides = [
  'https://images.unsplash.com/photo-1589561253896-768472ae6917?w=1920&q=85',
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=85',
  'https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=1920&q=85',
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=85',
  'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1920&q=85',
  'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1920&q=85',
  'https://images.unsplash.com/photo-1470071459604-6b3ec3e90c9a?w=1920&q=85',
  'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1920&q=85',
]

const subtitles = [
  'Descubre la magia de Colombia',
  'Tu próxima aventura comienza aquí',
  'Explora, vive, descubre',
  'Colombia te espera',
  'Viajes que transforman',
  'Naturaleza, cultura y aventura',
]
const subtitle = computed(() => subtitles[activeSlide.value % subtitles.length])

let carouselTimer = null

function advanceSlide() {
  prevSlide.value = activeSlide.value
  activeSlide.value = (activeSlide.value + 1) % bgSlides.length
  setTimeout(() => { prevSlide.value = null }, 600)
}

onMounted(() => {
  carouselTimer = setInterval(advanceSlide, 6000)
})

onUnmounted(() => {
  if (carouselTimer) clearInterval(carouselTimer)
})

function clearMsgs() {
  errorMsg.value = ''
  successMsg.value = ''
}

function switchMode(newMode) {
  clearMsgs()
  mode.value = newMode
}

async function handleLogin() {
  clearMsgs()
  if (!username.value.trim() || !password.value.trim()) {
    errorMsg.value = 'Ingresa usuario y contraseña'
    return
  }
  loading.value = true
  try {
    const user = await api.login(username.value.trim(), password.value)
    store.login(user)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.message || 'Credenciales inválidas'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  clearMsgs()
  if (!regNombre.value.trim() || !regEmail.value.trim() || !regUsername.value.trim() || !regPassword.value.trim()) {
    errorMsg.value = 'Todos los campos son requeridos'
    return
  }
  if (regPassword.value.length < 4) {
    errorMsg.value = 'La contraseña debe tener al menos 4 caracteres'
    return
  }
  if (regPassword.value !== regConfirm.value) {
    errorMsg.value = 'Las contraseñas no coinciden'
    return
  }
  loading.value = true
  try {
    const result = await api.register({
      nombre: regNombre.value.trim(),
      email: regEmail.value.trim(),
      username: regUsername.value.trim(),
      password: regPassword.value,
    })
    registeredEmail.value = regEmail.value.trim()
    verifyEmail.value = registeredEmail.value
    successMsg.value = 'Código de verificación enviado a ' + registeredEmail.value
    switchMode('verify')
  } catch (e) {
    errorMsg.value = e.message || 'Error al registrarse'
  } finally {
    loading.value = false
  }
}

async function handleVerify() {
  clearMsgs()
  if (!verifyCode.value.trim()) {
    errorMsg.value = 'Ingresa el código de verificación'
    return
  }
  loading.value = true
  try {
    await api.verifyCode(verifyEmail.value, verifyCode.value.trim())
    successMsg.value = '¡Cuenta verificada! Ahora puedes iniciar sesión.'
    switchMode('login')
    username.value = verifyEmail.value
  } catch (e) {
    errorMsg.value = e.message || 'Código inválido'
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  clearMsgs()
  loading.value = true
  try {
    await api.resendCode(verifyEmail.value)
    successMsg.value = 'Código reenviado a ' + verifyEmail.value
  } catch (e) {
    errorMsg.value = e.message || 'Error al reenviar código'
  } finally {
    loading.value = false
  }
}

async function handleForgotRequest() {
  clearMsgs()
  if (!forgotEmail.value.trim() || !forgotEmail.value.includes('@')) {
    errorMsg.value = 'Ingresa un correo válido'
    return
  }
  loading.value = true
  try {
    await api.forgotPassword(forgotEmail.value.trim())
    successMsg.value = 'Si el correo está registrado, recibirás un código.'
    forgotStep.value = 'reset'
  } catch (e) {
    errorMsg.value = e.message || 'Error al solicitar recuperación'
  } finally {
    loading.value = false
  }
}

async function handleForgotReset() {
  clearMsgs()
  if (!forgotCode.value.trim() || !forgotNewPassword.value.trim() || !forgotConfirm.value.trim()) {
    errorMsg.value = 'Todos los campos son requeridos'
    return
  }
  if (forgotNewPassword.value.length < 4) {
    errorMsg.value = 'La contraseña debe tener al menos 4 caracteres'
    return
  }
  if (forgotNewPassword.value !== forgotConfirm.value) {
    errorMsg.value = 'Las contraseñas no coinciden'
    return
  }
  loading.value = true
  try {
    await api.resetPassword(forgotEmail.value.trim(), forgotCode.value.trim(), forgotNewPassword.value)
    successMsg.value = 'Contraseña actualizada. Ahora puedes iniciar sesión.'
    switchMode('login')
    username.value = forgotEmail.value.trim()
  } catch (e) {
    errorMsg.value = e.message || 'Error al restablecer contraseña'
  } finally {
    loading.value = false
  }
}

function switchForgotStep(step) {
  forgotStep.value = step
  clearMsgs()
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg">
      <div
        v-for="(url, i) in bgSlides" :key="i"
        class="slide"
        :class="{ active: activeSlide === i, leaving: prevSlide === i }"
        :style="{ backgroundImage: `url('${url}')` }"
      ></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <div class="login-brand">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" width="40" height="40" class="compass-logo">
              <circle cx="20" cy="20" r="17" stroke="#92ecae" stroke-width="1.5" fill="none"/>
              <polygon points="20,3 24,20 20,37 16,20" fill="#92ecae"/>
              <polygon points="3,20 20,16 37,20 20,24" fill="#92ecae" opacity="0.35"/>
              <circle cx="20" cy="20" r="2.2" fill="#006d3c"/>
            </svg>
          </div>
          <h1>ExploraColombia</h1>
          <p class="login-subtitle">{{ subtitle }}</p>
        </div>

        <!-- LOGIN FORM -->
        <form v-if="mode === 'login'" class="login-form" @submit.prevent="handleLogin">
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">person</span>
              <input type="text" v-model="username" placeholder="Usuario o correo" required>
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">lock</span>
              <input type="password" v-model="password" placeholder="Contraseña" required>
            </div>
          </div>

          <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>
          <p v-if="successMsg" class="login-success">{{ successMsg }}</p>

          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="material-symbols-outlined" style="animation:spin 1s linear infinite">refresh</span>
            <span v-else class="material-symbols-outlined">login</span>
            {{ loading ? 'Entrando...' : 'Iniciar Sesión' }}
          </button>

          <div class="login-footer">
            <a href="#" @click.prevent="switchMode('forgot')" class="toggle-link" style="margin-bottom:8px;display:inline-block;">
              ¿Olvidaste tu contraseña?
            </a>
            <a href="#" @click.prevent="switchMode('register')" class="toggle-link">
              ¿No tienes cuenta? Regístrate
            </a>
          </div>
        </form>

        <!-- REGISTER FORM -->
        <form v-if="mode === 'register'" class="login-form" @submit.prevent="handleRegister">
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">badge</span>
              <input type="text" v-model="regNombre" placeholder="Nombre completo" required>
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">mail</span>
              <input type="email" v-model="regEmail" placeholder="Correo electrónico" required>
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">person</span>
              <input type="text" v-model="regUsername" placeholder="Usuario" required>
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">lock</span>
              <input type="password" v-model="regPassword" placeholder="Contraseña" required>
            </div>
          </div>
          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">lock</span>
              <input type="password" v-model="regConfirm" placeholder="Confirmar contraseña" required>
            </div>
          </div>

          <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>

          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="material-symbols-outlined" style="animation:spin 1s linear infinite">refresh</span>
            <span v-else class="material-symbols-outlined">person_add</span>
            {{ loading ? 'Registrando...' : 'Crear Cuenta' }}
          </button>

          <div class="login-footer">
            <a href="#" @click.prevent="switchMode('login')" class="toggle-link">
              ¿Ya tienes cuenta? Iniciar sesión
            </a>
          </div>
        </form>

        <!-- VERIFY CODE FORM -->
        <form v-if="mode === 'verify'" class="login-form" @submit.prevent="handleVerify">
          <div class="verify-info">
            <span class="material-symbols-outlined" style="font-size:48px;color:var(--primary);margin-bottom:12px">mark_email_read</span>
            <p>Hemos enviado un código de verificación a</p>
            <strong>{{ verifyEmail }}</strong>
          </div>

          <div class="form-group">
            <div class="input-wrapper">
              <span class="material-symbols-outlined icon">pin</span>
              <input type="text" v-model="verifyCode" placeholder="Código de 6 dígitos" maxlength="6" required>
            </div>
          </div>

          <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>
          <p v-if="successMsg" class="login-success">{{ successMsg }}</p>

          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="material-symbols-outlined" style="animation:spin 1s linear infinite">refresh</span>
            <span v-else class="material-symbols-outlined">verified</span>
            {{ loading ? 'Verificando...' : 'Verificar Código' }}
          </button>

          <div class="login-footer">
            <a href="#" @click.prevent="handleResend" class="toggle-link" style="margin-bottom:8px;display:inline-block;">
              ¿No recibiste el código? Reenviar
            </a>
            <a href="#" @click.prevent="switchMode('login')" class="toggle-link">
              Volver a inicio de sesión
            </a>
          </div>
        </form>

        <!-- FORGOT PASSWORD FORM -->
        <form v-if="mode === 'forgot'" class="login-form" @submit.prevent="forgotStep === 'email' ? handleForgotRequest() : handleForgotReset()">
          <!-- Step 1: Enter email -->
          <template v-if="forgotStep === 'email'">
            <div class="verify-info">
              <span class="material-symbols-outlined" style="font-size:48px;color:var(--primary);margin-bottom:12px">lock_reset</span>
              <p>Ingresa tu correo para recuperar tu contraseña</p>
            </div>

            <div class="form-group">
              <div class="input-wrapper">
                <span class="material-symbols-outlined icon">mail</span>
                <input type="email" v-model="forgotEmail" placeholder="Correo electrónico" required>
              </div>
            </div>

            <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>
            <p v-if="successMsg" class="login-success">{{ successMsg }}</p>

            <button type="submit" class="btn-login" :disabled="loading">
              <span v-if="loading" class="material-symbols-outlined" style="animation:spin 1s linear infinite">refresh</span>
              <span v-else class="material-symbols-outlined">send</span>
              {{ loading ? 'Enviando...' : 'Enviar Código' }}
            </button>
          </template>

          <!-- Step 2: Enter code + new password -->
          <template v-if="forgotStep === 'reset'">
            <div class="verify-info">
              <span class="material-symbols-outlined" style="font-size:48px;color:var(--primary);margin-bottom:12px">key</span>
              <p>Ingresa el código y tu nueva contraseña</p>
              <strong>{{ forgotEmail }}</strong>
            </div>

            <div class="form-group">
              <div class="input-wrapper">
                <span class="material-symbols-outlined icon">pin</span>
                <input type="text" v-model="forgotCode" placeholder="Código de 6 dígitos" maxlength="6" required>
              </div>
            </div>
            <div class="form-group">
              <div class="input-wrapper">
                <span class="material-symbols-outlined icon">lock</span>
                <input type="password" v-model="forgotNewPassword" placeholder="Nueva contraseña" required>
              </div>
            </div>
            <div class="form-group">
              <div class="input-wrapper">
                <span class="material-symbols-outlined icon">lock</span>
                <input type="password" v-model="forgotConfirm" placeholder="Confirmar contraseña" required>
              </div>
            </div>

            <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>
            <p v-if="successMsg" class="login-success">{{ successMsg }}</p>

            <button type="submit" class="btn-login" :disabled="loading">
              <span v-if="loading" class="material-symbols-outlined" style="animation:spin 1s linear infinite">refresh</span>
              <span v-else class="material-symbols-outlined">check_circle</span>
              {{ loading ? 'Cambiando...' : 'Cambiar Contraseña' }}
            </button>
          </template>

          <div class="login-footer" style="margin-top:8px;">
            <template v-if="forgotStep === 'reset'">
              <a href="#" @click.prevent="switchForgotStep('email')" class="toggle-link" style="margin-bottom:8px;display:inline-block;">
                Volver a ingresar correo
              </a>
            </template>
            <a href="#" @click.prevent="switchMode('login')" class="toggle-link">
              Volver a inicio de sesión
            </a>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-error {
  color: var(--on-error-container);
  background: var(--error-container);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 16px;
  text-align: center;
}
.login-success {
  color: var(--on-primary-fixed);
  background: var(--primary-fixed);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 16px;
  text-align: center;
}
.verify-info {
  text-align: center;
  margin-bottom: 24px;
}
.verify-info p {
  color: var(--on-surface-variant);
  font-size: 14px;
  margin-bottom: 4px;
}
.verify-info strong {
  font-size: 16px;
  color: var(--primary);
}
.toggle-link {
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: var(--transition);
  display: inline-block;
  margin-top: 4px;
}
.toggle-link:hover {
  text-decoration: underline;
  opacity: 0.8;
}
.login-subtitle {
  animation: fadeSubtitle 0.8s ease;
  font-size: 14px !important;
}
@keyframes fadeSubtitle {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
