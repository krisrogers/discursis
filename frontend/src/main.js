import axios from 'axios'
import Vue from 'vue'
import VueRouter from 'vue-router'

import '../semantic/dist/semantic.js'

import App from 'src/App.vue'
import Login from 'src/pages/Login.vue'
import Signup from 'src/pages/Signup.vue'
import ResetPassword from 'src/pages/ResetPassword.vue'
import ResetPasswordFinish from 'src/pages/ResetPasswordFinish.vue'
import Projects from './pages/Projects.vue'
import Results from './pages/Results.vue'
import Upload from './pages/Upload.vue'
import Store from 'src/store.js'

Vue.use(VueRouter)

const routes = [
  { path: '/', redirect: { name: 'projects' }},
  { path: '/login', name: 'login', component: Login },
  { path: '/signup', name: 'signup', component: Signup },
  { path: '/reset-password', name: 'reset-password', component: ResetPassword },
  { path: '/reset-password-finish', name: 'reset-password-finish', component: ResetPasswordFinish },
  { path: '/projects', name: 'projects', component: Projects, meta: { auth: true }},
  { path: '/upload', name: 'upload', component: Upload, meta: { auth: true }},
  { path: '/results/:projectId', name: 'results', component: Results, props: true, meta: { auth: true }}
]

const router = new VueRouter({
  routes
})

// Redirect to login
router.beforeEach((to, from, next) => {
  const authRequired = to.matched.some((route) => route.meta.auth)
  const authed = Store.getAuthToken()
  if (authRequired && !authed) {
    next({ name: 'login', query: { redirect: to.name }})
  } else {
    next()
  }
})

const app = new Vue({
  router,
  render: h => h(App)
})
app.$mount('#app')
app.$store = Store
axios.$app = app
