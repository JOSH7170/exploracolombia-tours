<script setup>
import { useAppStore } from '../stores/app'

const store = useAppStore()

const iconMap = {
  success: 'check_circle',
  error: 'error',
  warning: 'warning',
}

function removeToast(id) {
  store.removeToast(id)
}
</script>

<template>
  <div class="toast-container">
    <div
      v-for="t in store.toasts"
      :key="t.id"
      class="toast"
      :class="t.type"
    >
      <span class="material-symbols-outlined toast-icon">{{ iconMap[t.type] || 'info' }}</span>
      <span>{{ t.message }}</span>
      <button class="toast-close" @click="removeToast(t.id)">&times;</button>
    </div>
  </div>
</template>
