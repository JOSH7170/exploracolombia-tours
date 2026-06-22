<script setup>
import { ref, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import { useApi } from '../composables/useApi'

const store = useAppStore()
const api = useApi()
const clientes = ref([])

onMounted(async () => {
  try {
    clientes.value = await api.getClientes()
  } catch (e) {
    store.toast('Error al cargar clientes: ' + e.message, 'error')
  }
})

async function editCliente(id) {
  const c = clientes.value.find(x => x.id === id)
  if (c) await store.openEditModal('clientes', c)
}

async function deleteCliente(id) {
  await store.deleteItem('clientes', id)
  try {
    clientes.value = await api.getClientes()
  } catch { /* ignore */ }
}
</script>

<template>
  <div>
    <div class="module-header" style="flex-direction:column;align-items:flex-start">
      <div>
        <h2>Clientes</h2>
        <p>Base de datos de clientes y viajeros registrados.</p>
      </div>
      <div class="search-bar">
        <span class="material-symbols-outlined search-bar-icon">search</span>
        <input type="text" placeholder="Buscar clientes...">
      </div>
    </div>
    <div class="table-container">
      <div class="table-responsive">
        <table class="modern-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Email</th>
              <th>Teléfono</th>
              <th>Ciudad</th>
              <th style="width:100px">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in clientes" :key="c.id">
              <td><strong>{{ c.nombre }}</strong></td>
              <td>{{ c.email }}</td>
              <td>{{ c.telefono }}</td>
              <td>{{ c.ciudad }}</td>
              <td>
                <div class="table-actions">
                  <button v-if="store.isAdmin" class="btn btn-secondary btn-sm btn-icon" @click="editCliente(c.id)" title="Editar">
                    <span class="material-symbols-outlined" style="font-size:16px">edit</span>
                  </button>
                  <button v-if="store.isAdmin" class="btn btn-danger btn-sm btn-icon" @click="deleteCliente(c.id)" title="Eliminar">
                    <span class="material-symbols-outlined" style="font-size:16px">delete</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
