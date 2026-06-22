<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const paquetes = ref([])
const guias = ref([])

const clienteNombre = ref('')
const clienteEmail = ref('')
const clienteTelefono = ref('')
const paqueteId = ref('')
const guiaId = ref('')

const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth())
const selectedDate = ref('')

const reservando = ref(false)
const pagoModal = ref(false)
const reservaActual = ref(null)
const cardNombre = ref('')
const cardNumero = ref('')
const cardExpiracion = ref('')
const cardCvv = ref('')
const pagando = ref(false)

const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const paqueteSeleccionado = computed(() => paquetes.value.find(p => p.id === parseInt(paqueteId.value)))
const totalPagar = computed(() => paqueteSeleccionado.value?.precio || 0)

const daysInMonth = computed(() => new Date(calYear.value, calMonth.value + 1, 0).getDate())
const firstDay = computed(() => new Date(calYear.value, calMonth.value, 1).getDay())
const calendarDays = computed(() => {
  const days = []
  for (let i = 0; i < firstDay.value; i++) days.push(null)
  for (let d = 1; d <= daysInMonth.value; d++) days.push(d)
  return days
})

const paquetesDisponibles = computed(() => paquetes.value.filter(p => p.estado !== 'Completado'))
const guiasActivos = computed(() => guias.value.filter(g => g.estado === 'Activo'))

onMounted(async () => {
  try {
    [paquetes.value, guias.value] = await Promise.all([
      api.getPaquetes(),
      api.getGuias(),
    ])
  } catch (e) {
    store.toast('Error al cargar datos: ' + e.message, 'error')
  }
})

function prevMonth() {
  if (calMonth.value === 0) { calYear.value--; calMonth.value = 11 }
  else calMonth.value--
}
function nextMonth() {
  if (calMonth.value === 11) { calYear.value++; calMonth.value = 0 }
  else calMonth.value++
}
function selectDay(d) {
  if (!d) return
  const m = String(calMonth.value + 1).padStart(2, '0')
  const day = String(d).padStart(2, '0')
  selectedDate.value = `${calYear.value}-${m}-${day}`
}
function isToday(d) {
  if (!d) return false
  const today = new Date()
  return today.getFullYear() === calYear.value && today.getMonth() === calMonth.value && today.getDate() === d
}
function isSelected(d) {
  if (!d || !selectedDate.value) return false
  return selectedDate.value === `${calYear.value}-${String(calMonth.value + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

async function confirmarReserva() {
  if (!clienteNombre.value.trim() || !clienteEmail.value.trim() || !paqueteId.value || !guiaId.value || !selectedDate.value) {
    store.toast('Completa todos los campos obligatorios', 'error')
    return
  }
  if (!clienteEmail.value.includes('@')) {
    store.toast('Correo electrónico inválido', 'error')
    return
  }
  reservando.value = true
  try {
    const data = {
      clienteNombre: clienteNombre.value.trim(),
      clienteEmail: clienteEmail.value.trim().toLowerCase(),
      clienteTelefono: clienteTelefono.value.trim(),
      paqueteId: parseInt(paqueteId.value),
      guiaId: parseInt(guiaId.value),
      fechaSalida: selectedDate.value,
    }
    const reserva = await api.saveReserva(data)
    reservaActual.value = reserva
    pagoModal.value = true
  } catch (e) {
    store.toast('Error al crear reserva: ' + e.message, 'error')
  } finally {
    reservando.value = false
  }
}

async function procesarPago() {
  if (!reservaActual.value) return
  const nombre = cardNombre.value.trim()
  const numero = cardNumero.value.replace(/\s/g, '')
  const exp = cardExpiracion.value.trim()
  const cvv = cardCvv.value.trim()
  if (!nombre || numero.length < 13 || !exp || cvv.length < 3) {
    store.toast('Completa todos los datos de la tarjeta', 'error')
    return
  }
  pagando.value = true
  try {
    await api.pagarReserva(reservaActual.value.id, 'Tarjeta de credito', totalPagar.value)
    store.toast('Pago procesado. Revisa tu correo para el recibo.', 'success')
    pagoModal.value = false
    clienteNombre.value = ''
    clienteEmail.value = ''
    clienteTelefono.value = ''
    paqueteId.value = ''
    guiaId.value = ''
    selectedDate.value = ''
    reservaActual.value = null
    cardNombre.value = ''
    cardNumero.value = ''
    cardExpiracion.value = ''
    cardCvv.value = ''
  } catch (e) {
    store.toast('Error al procesar pago: ' + e.message, 'error')
  } finally {
    pagando.value = false
  }
}
</script>

<template>
  <div>
    <div class="module-header">
      <div>
        <h2>Reservas</h2>
        <p>Crea nuevas reservas para tus clientes.</p>
      </div>
    </div>

    <div class="reservas-layout">
      <div class="reservas-form-section">
        <h3>
          <span class="material-symbols-outlined" style="color:var(--primary)">add_circle</span>
          Nueva Reserva
        </h3>
        <form class="reservas-form" @submit.prevent="confirmarReserva">
          <div class="form-group">
            <label><span class="material-symbols-outlined" style="font-size:16px">person</span> Nombre completo</label>
            <input type="text" v-model="clienteNombre" placeholder="Ej: Ana Rodríguez" required>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label><span class="material-symbols-outlined" style="font-size:16px">mail</span> Correo electrónico</label>
              <input type="email" v-model="clienteEmail" placeholder="correo@ejemplo.com" required>
            </div>
            <div class="form-group">
              <label><span class="material-symbols-outlined" style="font-size:16px">phone</span> Teléfono</label>
              <input type="text" v-model="clienteTelefono" placeholder="+57 300 123 4567">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group custom-select">
              <label><span class="material-symbols-outlined" style="font-size:16px">inventory_2</span> Paquete</label>
              <select v-model="paqueteId">
                <option value="">Seleccionar paquete...</option>
                <option v-for="p in paquetesDisponibles" :key="p.id" :value="p.id">
                  {{ p.nombre }} - {{ api.formatCurrency(p.precio) }}
                </option>
              </select>
            </div>
            <div class="form-group custom-select">
              <label><span class="material-symbols-outlined" style="font-size:16px">badge</span> Guía</label>
              <select v-model="guiaId">
                <option value="">Seleccionar guía...</option>
                <option v-for="g in guiasActivos" :key="g.id" :value="g.id">{{ g.nombre }}</option>
              </select>
            </div>
          </div>

          <!-- Mini Calendar -->
          <div class="form-group">
            <label><span class="material-symbols-outlined" style="font-size:16px">calendar_today</span> Fecha de salida</label>
            <div class="mini-calendar">
              <div class="cal-header">
                <button type="button" class="cal-nav" @click="prevMonth">&lsaquo;</button>
                <span class="cal-month">{{ meses[calMonth] }} {{ calYear }}</span>
                <button type="button" class="cal-nav" @click="nextMonth">&rsaquo;</button>
              </div>
              <div class="cal-weekdays">
                <span>Do</span><span>Lu</span><span>Ma</span><span>Mi</span><span>Ju</span><span>Vi</span><span>Sá</span>
              </div>
              <div class="cal-grid">
                <template v-for="(d, i) in calendarDays" :key="i">
                  <button v-if="d" type="button" class="cal-day" :class="{ selected: isSelected(d), today: isToday(d) }" @click="selectDay(d)">{{ d }}</button>
                  <span v-else class="cal-empty"></span>
                </template>
              </div>
            </div>
            <p v-if="selectedDate" style="font-size:13px;color:var(--primary);margin-top:6px">
              <span class="material-symbols-outlined" style="font-size:14px">check_circle</span>
              {{ selectedDate }}
            </p>
          </div>

          <button type="submit" class="btn btn-success" style="width:100%;margin-top:8px" :disabled="reservando || !paqueteId || !guiaId || !selectedDate">
            <span class="material-symbols-outlined" style="font-size:18px">check_circle</span>
            {{ reservando ? 'Guardando...' : 'Confirmar reservación' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Payment Mini Modal -->
    <Teleport to="body">
      <div v-if="pagoModal" class="pago-overlay" @click.self="pagoModal = false">
        <div class="pago-modal">
          <div class="pago-header">
            <h3><span class="material-symbols-outlined" style="color:var(--secondary)">credit_card</span> Pago con tarjeta</h3>
            <button class="cal-nav" @click="pagoModal = false">&times;</button>
          </div>
          <div class="pago-body">
            <div class="pago-resumen">
              <div><strong>Cliente:</strong> {{ clienteNombre }}</div>
              <div><strong>Paquete:</strong> {{ paqueteSeleccionado?.nombre }}</div>
              <div><strong>Fecha:</strong> {{ selectedDate }}</div>
              <div style="font-size:20px;font-weight:700;color:var(--primary);margin-top:8px">{{ api.formatCurrency(totalPagar) }}</div>
            </div>
            <form @submit.prevent="procesarPago" class="card-form">
              <div class="form-group">
                <label>Titular de la tarjeta</label>
                <input type="text" v-model="cardNombre" placeholder="Nombre como aparece en la tarjeta" required>
              </div>
              <div class="form-group">
                <label>Número de tarjeta</label>
                <input type="text" v-model="cardNumero" placeholder="0000 0000 0000 0000" maxlength="19" required inputmode="numeric" @input="e => cardNumero.value = e.target.value.replace(/[^\d]/g,'').replace(/(.{4})/g,'$1 ').trim()">
              </div>
              <div class="form-row">
                <div class="form-group" style="flex:1">
                  <label>Vencimiento</label>
                  <input type="text" v-model="cardExpiracion" placeholder="MM/AA" maxlength="5" required @input="e => { const v = e.target.value.replace(/[^\d]/g,''); if (v.length > 2) cardExpiracion.value = v.slice(0,2) + '/' + v.slice(2,4); else cardExpiracion.value = v }">
                </div>
                <div class="form-group" style="flex:0 0 100px">
                  <label>CVV</label>
                  <input type="text" v-model="cardCvv" placeholder="123" maxlength="4" required inputmode="numeric" @input="e => cardCvv.value = e.target.value.replace(/[^\d]/g,'')">
                </div>
              </div>
              <button type="submit" class="btn btn-success" style="width:100%;margin-top:8px" :disabled="pagando">
                <span class="material-symbols-outlined" style="font-size:18px">lock</span>
                {{ pagando ? 'Procesando...' : 'Pagar ' + api.formatCurrency(totalPagar) }}
              </button>
            </form>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.mini-calendar {
  background: var(--surface-container-low);
  border: 1px solid var(--outline-variant);
  border-radius: var(--radius-sm);
  padding: 12px;
  max-width: 320px;
  user-select: none;
}
.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.cal-month {
  font-weight: 600;
  font-size: 14px;
  color: var(--on-surface);
}
.cal-nav {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--on-surface-variant);
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.cal-nav:hover {
  background: var(--surface-container-high);
}
.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--outline);
  margin-bottom: 6px;
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.cal-day {
  background: none;
  border: none;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  font-size: 13px;
  cursor: pointer;
  color: var(--on-surface);
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-day:hover {
  background: var(--surface-container-high);
}
.cal-day.today {
  font-weight: 700;
  color: var(--primary);
  border: 1px solid var(--primary);
}
.cal-day.selected {
  background: var(--primary);
  color: var(--on-primary);
  font-weight: 700;
}
.cal-empty {
  aspect-ratio: 1;
}
.pago-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pago-modal {
  background: var(--surface);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  overflow: hidden;
}
.pago-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--outline-variant);
}
.pago-header h3 {
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pago-body {
  padding: 20px;
}
.pago-resumen {
  background: var(--surface-container-low);
  border-radius: var(--radius-sm);
  padding: 14px;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.8;
}
.card-form .form-group {
  margin-bottom: 14px;
}
.card-form label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
}
.card-form input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--outline);
  border-radius: var(--radius-sm);
  font-size: 14px;
  background: var(--surface-container);
  color: var(--on-surface);
  transition: border-color 0.2s;
}
.card-form input:focus {
  border-color: var(--primary);
  outline: none;
}
.card-form .form-row {
  display: flex;
  gap: 12px;
}
</style>
