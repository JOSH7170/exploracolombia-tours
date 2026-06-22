<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from './stores/app'
import AppHeader from './components/AppHeader.vue'
import ToastContainer from './components/ToastContainer.vue'
import AppModal from './components/AppModal.vue'

const store = useAppStore()
const router = useRouter()

onMounted(() => {
  if (!store.loggedIn) {
    router.push('/login')
  }
})
</script>

<template>
  <ToastContainer />
  <AppModal />

  <router-view v-if="!store.loggedIn" />

  <div v-else class="app active">
    <AppHeader />
    <button v-if="store.isAdmin && store.currentSection !== 'dashboard'" class="btn-fab" @click="store.openCreateModal()">
      <span class="material-symbols-outlined">add</span>
    </button>
  </div>
</template>
