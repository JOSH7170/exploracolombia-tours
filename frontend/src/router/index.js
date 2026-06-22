import { createRouter, createWebHistory } from 'vue-router'
import { useAppStore } from '../stores/app'
import LoginPage from '../pages/LoginPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import DestinosPage from '../pages/DestinosPage.vue'
import PaquetesPage from '../pages/PaquetesPage.vue'
import GuiasPage from '../pages/GuiasPage.vue'
import ReservasPage from '../pages/ReservasPage.vue'
import ReportesPage from '../pages/ReportesPage.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginPage, meta: { public: true } },
  { path: '/', name: 'dashboard', component: DashboardPage },
  { path: '/destinos', name: 'destinos', component: DestinosPage },
  { path: '/paquetes', name: 'paquetes', component: PaquetesPage },
  { path: '/guias', name: 'guias', component: GuiasPage },
  { path: '/reservas', name: 'reservas', component: ReservasPage },
  { path: '/reportes', name: 'reportes', component: ReportesPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const adminRoutes = ['reportes']

router.beforeEach((to, from, next) => {
  const store = useAppStore()
  if (to.path === '/login' && store.loggedIn) {
    next('/')
  } else if (!to.meta.public && !store.loggedIn) {
    next('/login')
  } else if (store.loggedIn && adminRoutes.includes(to.name) && !store.isAdmin) {
    next('/')
  } else {
    next()
  }
})

router.afterEach((to) => {
  const store = useAppStore()
  if (store.loggedIn && to.name && to.name !== 'login') {
    store.navigate(to.name)
  }
})

export default router
