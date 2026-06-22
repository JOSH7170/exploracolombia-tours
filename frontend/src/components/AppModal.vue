<script setup>
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const store = useAppStore()
const router = useRouter()

function handleSave() {
  store.handleModalSave()
}

function handleClose() {
  store.closeModal()
}

function handleBodyClick(e) {
  const card = e.target.closest('[data-navigate]')
  if (!card) return
  const section = card.dataset.navigate
  const id = card.dataset.id
  router.push(section === 'dashboard' ? '/' : '/' + section)
  store.closeModal()
}
</script>

<template>
  <div class="modal-overlay" :class="{ open: store.modal.show }" @click.self="handleClose">
    <div class="modal">
      <div class="modal-header">
        <h3 v-html="store.modal.title"></h3>
        <button class="modal-close" @click="handleClose">&times;</button>
      </div>
      <div class="modal-body" v-html="store.modal.body" @click="handleBodyClick"></div>
      <div class="modal-footer" v-if="store.modal.showSave">
        <button class="btn btn-secondary" @click="handleClose">Cancelar</button>
        <button class="btn btn-primary" @click="handleSave">
          <span class="material-symbols-outlined">save</span>
          {{ store.editingItem ? 'Actualizar' : 'Guardar' }}
        </button>
      </div>
    </div>
  </div>
</template>
