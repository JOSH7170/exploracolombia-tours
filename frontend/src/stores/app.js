import { defineStore } from 'pinia'
import { useApi } from '../composables/useApi'

export const useAppStore = defineStore('app', {
  state: () => ({
    loggedIn: false,
    username: '',
    userNombre: '',
    role: '',
    currentSection: 'dashboard',
    editingItem: null,
    currentModule: null,
    toasts: [],
    modal: { show: false, title: '', body: '', showSave: true },
    _destinos: [],
    _paquetes: [],
    _guias: [],
    _reservas: [],
    searchQuery: '',
  }),

  getters: {
    isAdmin: (state) => state.role === 'admin',
  },

  actions: {
    login(user) {
      this.loggedIn = true
      this.username = user.username
      this.userNombre = user.nombre
      this.role = user.role
      this.toast(`¡Bienvenido, ${user.nombre}!`, 'success')
    },

    logout() {
      this.loggedIn = false
      this.username = ''
      this.userNombre = ''
      this.role = ''
      this.currentSection = 'dashboard'
      this.toast('Sesión cerrada. ¡Vuelve pronto!', 'warning')
    },

    navigate(section) {
      this.currentSection = section
      this.editingItem = null
      this.currentModule = null
    },

    toast(message, type = 'success') {
      const id = Date.now()
      this.toasts.push({ id, message, type })
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== id)
      }, 4000)
    },

    openModal(title, body, showSave = true) {
      this.modal = { show: true, title, body, showSave }
    },

    closeModal() {
      this.modal = { show: false, title: '', body: '', showSave: true }
      this.editingItem = null
      this.currentModule = null
    },

    async openCreateModal() {
      const api = useApi()
      const module = this.currentSection

      const destinosChips = async () => {
        try {
          this._destinos = await api.getDestinos()
          return this._destinos.map(d => `
            <label class="chip" style="cursor:pointer;background:rgba(13,148,136,0.08)">
              <input type="checkbox" value="${d.id}" style="accent-color:var(--primary)"> ${d.nombre}
            </label>
          `).join('')
        } catch {
          return '<p style="color:var(--text-muted)">Error al cargar destinos</p>'
        }
      }

      const forms = {
        destinos: {
          title: '<span class="material-symbols-outlined" style="color:var(--primary);font-size:20px">explore</span> Nuevo Destino',
          fields: `
            <div class="form-group">
              <label>Nombre del destino</label>
              <input type="text" id="f-nombre" placeholder="Ej: Valle de Cocora" required>
            </div>
            <div class="form-group">
              <label>Departamento</label>
              <input type="text" id="f-departamento" placeholder="Ej: Quindío" required>
            </div>
            <div class="form-group">
              <label>Tipo</label>
              <select id="f-tipo">
                <option value="Natural">Natural</option>
                <option value="Cultural">Cultural</option>
                <option value="Aventura">Aventura</option>
              </select>
            </div>
            <div class="form-group">
              <label>Descripción</label>
              <textarea id="f-descripcion" rows="3" placeholder="Describe el destino..."></textarea>
            </div>
            <div class="form-group">
              <label>URL de imagen</label>
              <input type="text" id="f-imagen" placeholder="https://...">
            </div>
          `
        },
        paquetes: {
          title: '<span class="material-symbols-outlined" style="color:var(--secondary);font-size:20px">inventory_2</span> Nuevo Paquete',
          fields: `
            <div class="form-group">
              <label>Nombre del paquete</label>
              <input type="text" id="f-nombre" placeholder="Ej: Aventura Cafetera" required>
            </div>
            <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <div class="form-group">
                <label>Duración</label>
                <input type="text" id="f-duracion" placeholder="Ej: 5 días">
              </div>
              <div class="form-group">
                <label>Precio ($)</label>
                <input type="number" id="f-precio" placeholder="1200000">
              </div>
            </div>
            <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
              <div class="form-group">
                <label>Cupo máximo</label>
                <input type="number" id="f-cupo" placeholder="20">
              </div>
              <div class="form-group">
                <label>Estado</label>
                <select id="f-estado">
                  <option value="Disponible">Disponible</option>
                  <option value="Ejecución">En ejecución</option>
                  <option value="Completado">Completado</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>Descripción</label>
              <textarea id="f-descripcion" rows="2" placeholder="Descripción del paquete..."></textarea>
            </div>
            <div class="form-group" style="border:1px solid var(--secondary);border-radius:var(--radius-sm);padding:12px;margin-bottom:12px;background:rgba(255,183,0,0.04)">
              <label style="display:flex;align-items:center;gap:6px;color:var(--secondary);font-weight:700">
                <span class="material-symbols-outlined" style="font-size:16px">local_offer</span> Oferta especial
              </label>
              <div class="form-row" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px">
                <div class="form-group">
                  <label>Precio de oferta ($)</label>
                  <input type="number" id="f-precioOferta" placeholder="Ej: 980000">
                </div>
                <div class="form-group" style="display:flex;align-items:flex-end;padding-bottom:4px">
                  <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                    <input type="checkbox" id="f-enOferta" value="1"> Activar oferta
                  </label>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label>URL de imagen</label>
              <input type="text" id="f-imagen" placeholder="https://images.unsplash.com/...">
            </div>
            <div class="form-group">
              <label>Destinos incluidos</label>
              <div class="chips-container" id="paquete-destinos-chips">
                ${await destinosChips()}
              </div>
            </div>
          `
        },
        guias: {
          title: '<span class="material-symbols-outlined" style="color:var(--tertiary);font-size:20px">badge</span> Nuevo Guía',
          fields: `
            <div class="form-group">
              <label>Nombre completo</label>
              <input type="text" id="f-nombre" placeholder="Ej: Carlos Pérez" required>
            </div>
            <div class="form-group">
              <label>Email</label>
              <input type="email" id="f-email" placeholder="correo@ejemplo.com">
            </div>
            <div class="form-group">
              <label>Teléfono</label>
              <input type="text" id="f-telefono" placeholder="+57 300 123 4567">
            </div>
            <div class="form-group">
              <label>Idiomas (separados por coma)</label>
              <input type="text" id="f-idiomas" placeholder="Español, Inglés, Francés">
            </div>
            <div class="form-group">
              <label>Estado</label>
              <select id="f-estado">
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
              </select>
            </div>
          `
        },
      }

      const form = forms[module]
      if (!form) return
      this.openModal(form.title, form.fields)
    },

    async openEditModal(module, item) {
      this.currentModule = module
      this.editingItem = item

      const formMap = {
        destinos: {
          title: '<span class="material-symbols-outlined" style="color:var(--primary);font-size:20px">edit</span> Editar Destino',
          populate: () => {
            document.getElementById('f-nombre').value = item.nombre
            document.getElementById('f-departamento').value = item.departamento
            document.getElementById('f-tipo').value = item.tipo
            document.getElementById('f-descripcion').value = item.descripcion
            document.getElementById('f-imagen').value = item.imagen || ''
          }
        },
        paquetes: {
          title: '<span class="material-symbols-outlined" style="color:var(--secondary);font-size:20px">edit</span> Editar Paquete',
          populate: () => {
            document.getElementById('f-nombre').value = item.nombre
            document.getElementById('f-duracion').value = item.duracion
            document.getElementById('f-precio').value = item.precio
            document.getElementById('f-cupo').value = item.cupo
            document.getElementById('f-estado').value = item.estado
            document.getElementById('f-descripcion').value = item.descripcion
            document.getElementById('f-imagen').value = item.imagen || ''
            document.getElementById('f-precioOferta').value = item.precio_oferta || ''
            document.getElementById('f-enOferta').checked = item.en_oferta == 1
            document.querySelectorAll('#paquete-destinos-chips input[type="checkbox"]').forEach(cb => {
              cb.checked = item.destinos && item.destinos.includes(parseInt(cb.value))
            })
          }
        },
        guias: {
          title: '<span class="material-symbols-outlined" style="color:var(--tertiary);font-size:20px">edit</span> Editar Guía',
          populate: () => {
            document.getElementById('f-nombre').value = item.nombre
            document.getElementById('f-email').value = item.email
            document.getElementById('f-telefono').value = item.telefono
            document.getElementById('f-idiomas').value = (item.idiomas || []).join(', ')
            document.getElementById('f-estado').value = item.estado
          }
        },
      }

      const form = formMap[module]
      if (!form) return
      await this.openCreateModal()
      this.modal.title = form.title
      setTimeout(() => form.populate(), 50)
    },

    async handleModalSave() {
      const api = useApi()
      const module = this.currentModule
      const isEdit = !!this.editingItem

      try {
        if (module === 'destinos') {
          const data = {
            nombre: document.getElementById('f-nombre').value.trim(),
            departamento: document.getElementById('f-departamento').value.trim(),
            tipo: document.getElementById('f-tipo').value,
            descripcion: document.getElementById('f-descripcion').value.trim(),
            imagen: document.getElementById('f-imagen').value.trim() || 'https://images.unsplash.com/photo-1589561253896-768472ae6917?w=800&q=85',
          }
          if (!data.nombre) { this.toast('El nombre es requerido', 'error'); return }
          await api.saveDestino(data, isEdit ? this.editingItem.id : null)
          this.toast(isEdit ? 'Destino actualizado' : 'Destino creado', 'success')
          this.closeModal()
        } else if (module === 'paquetes') {
          const data = {
            nombre: document.getElementById('f-nombre').value.trim(),
            duracion: document.getElementById('f-duracion').value.trim(),
            precio: parseInt(document.getElementById('f-precio').value) || 0,
            cupo: parseInt(document.getElementById('f-cupo').value) || 0,
            estado: document.getElementById('f-estado').value,
            descripcion: document.getElementById('f-descripcion').value.trim(),
            imagen: document.getElementById('f-imagen').value.trim() || 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=85',
            precioOferta: document.getElementById('f-precioOferta').value ? parseInt(document.getElementById('f-precioOferta').value) : null,
            enOferta: document.getElementById('f-enOferta').checked ? 1 : 0,
            destinos: [],
          }
          document.querySelectorAll('#paquete-destinos-chips input[type="checkbox"]:checked').forEach(cb => {
            data.destinos.push(parseInt(cb.value))
          })
          if (!data.nombre) { this.toast('El nombre es requerido', 'error'); return }
          await api.savePaquete(data, isEdit ? this.editingItem.id : null)
          this.toast(isEdit ? 'Paquete actualizado' : 'Paquete creado', 'success')
          this.closeModal()
        } else if (module === 'guias') {
          const data = {
            nombre: document.getElementById('f-nombre').value.trim(),
            email: document.getElementById('f-email').value.trim(),
            telefono: document.getElementById('f-telefono').value.trim(),
            idiomas: document.getElementById('f-idiomas').value.split(',').map(s => s.trim()).filter(Boolean),
            estado: document.getElementById('f-estado').value,
          }
          if (!data.nombre) { this.toast('El nombre es requerido', 'error'); return }
          await api.saveGuia(data, isEdit ? this.editingItem.id : null)
          this.toast(isEdit ? 'Guía actualizado' : 'Guía creado', 'success')
          this.closeModal()
        }
      } catch (e) {
        this.toast('Error: ' + e.message, 'error')
      }
    },

    async deleteItem(module, id) {
      if (!confirm('¿Estás seguro de eliminar este elemento?')) return
      const api = useApi()
      try {
        const apiMap = {
          destinos: () => api.deleteDestino(id),
          paquetes: () => api.deletePaquete(id),
          guias: () => api.deleteGuia(id),
        }
        if (apiMap[module]) {
          await apiMap[module]()
          this.toast('Elemento eliminado', 'warning')
        }
      } catch (e) {
        this.toast('Error al eliminar: ' + e.message, 'error')
      }
    },
  },
})
