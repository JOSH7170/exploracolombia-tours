const API_BASE = '/api'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Error de conexión' }))
    throw new Error(err.error || 'Error del servidor')
  }
  return res.json()
}

export function cardImg(url) {
  return {
    backgroundImage: url && url.trim()
      ? `url('${url}')`
      : 'linear-gradient(135deg, #0d9488, #14b8a6, #0ea5e9)',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  }
}

export function useApi() {
  return {
    // Auth
    async login(username, password) {
      return request(`${API_BASE}/login`, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
    },
    async register(data) {
      return request(`${API_BASE}/register`, {
        method: 'POST',
        body: JSON.stringify(data),
      })
    },
    async verifyCode(email, code) {
      return request(`${API_BASE}/verify-code`, {
        method: 'POST',
        body: JSON.stringify({ email, code }),
      })
    },
    async resendCode(email) {
      return request(`${API_BASE}/resend-code`, {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
    },
    // Destinos
    async getDestinos() {
      const res = await request(`${API_BASE}/destinos`)
      return res.data
    },
    async getDestino(id) {
      return request(`${API_BASE}/destinos/${id}`)
    },
    async saveDestino(data, id) {
      if (id) return request(`${API_BASE}/destinos/${id}`, { method: 'PUT', body: JSON.stringify(data) })
      return request(`${API_BASE}/destinos`, { method: 'POST', body: JSON.stringify(data) })
    },
    async deleteDestino(id) {
      return request(`${API_BASE}/destinos/${id}`, { method: 'DELETE' })
    },

    // Paquetes
    async getPaquetes() {
      const res = await request(`${API_BASE}/paquetes`)
      return res.data
    },
    async getPaquete(id) {
      return request(`${API_BASE}/paquetes/${id}`)
    },
    async savePaquete(data, id) {
      if (id) return request(`${API_BASE}/paquetes/${id}`, { method: 'PUT', body: JSON.stringify(data) })
      return request(`${API_BASE}/paquetes`, { method: 'POST', body: JSON.stringify(data) })
    },
    async deletePaquete(id) {
      return request(`${API_BASE}/paquetes/${id}`, { method: 'DELETE' })
    },
    async getDestinosByPaquete(paqueteId) {
      const p = await this.getPaquete(paqueteId)
      if (!p || !p.destinos) return []
      const destinos = await this.getDestinos()
      return destinos.filter(d => p.destinos.includes(d.id))
    },

    // Guias
    async getGuias() {
      const res = await request(`${API_BASE}/guias`)
      return res.data
    },
    async getGuia(id) {
      return request(`${API_BASE}/guias/${id}`)
    },
    async saveGuia(data, id) {
      if (id) return request(`${API_BASE}/guias/${id}`, { method: 'PUT', body: JSON.stringify(data) })
      return request(`${API_BASE}/guias`, { method: 'POST', body: JSON.stringify(data) })
    },
    async deleteGuia(id) {
      return request(`${API_BASE}/guias/${id}`, { method: 'DELETE' })
    },

    // Reservas
    async getReservas() {
      const res = await request(`${API_BASE}/reservas`)
      return res.data
    },
    async saveReserva(data, id) {
      if (id) return request(`${API_BASE}/reservas/${id}`, { method: 'PUT', body: JSON.stringify(data) })
      return request(`${API_BASE}/reservas`, { method: 'POST', body: JSON.stringify(data) })
    },
    async deleteReserva(id) {
      return request(`${API_BASE}/reservas/${id}`, { method: 'DELETE' })
    },
    async pagarReserva(id, metodo, monto) {
      return request(`${API_BASE}/reservas/${id}/pagar`, {
        method: 'POST',
        body: JSON.stringify({ metodo, monto }),
      })
    },

    // Stats / Reportes
    async getStats() {
      return request(`${API_BASE}/stats`)
    },
    async getOcupacionData() {
      const res = await request(`${API_BASE}/reportes/ocupacion`)
      return res.data
    },
    async getIngresosData(meses) {
      const res = await request(`${API_BASE}/reportes/ingresos?meses=${meses || 6}`)
      return res.data
    },

    // Notificaciones
    async getNotificaciones() {
      const res = await request(`${API_BASE}/notificaciones`)
      return res.data
    },
    async leerNotificacion(id) {
      return request(`${API_BASE}/notificaciones/${id}/leer`, { method: 'POST' })
    },
    async leerTodasNotificaciones() {
      return request(`${API_BASE}/notificaciones/leer-todas`, { method: 'POST' })
    },
    async eliminarNotificacion(id) {
      return request(`${API_BASE}/notificaciones/${id}`, { method: 'DELETE' })
    },

    // Perfil
    async cambiarContrasena(actual, nueva, usuario) {
      return request(`${API_BASE}/cambiar-contrasena`, {
        method: 'POST',
        body: JSON.stringify({ actual, nueva, usuario }),
      })
    },
    async actualizarPerfil(usuario, nombre, email) {
      return request(`${API_BASE}/actualizar-perfil`, {
        method: 'POST',
        body: JSON.stringify({ usuario, nombre, email }),
      })
    },

    formatCurrency(amount) {
      return '$' + amount.toLocaleString('es-CO')
    },
  }
}
