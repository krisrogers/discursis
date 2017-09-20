import Vue from 'vue'
import VueRouter from 'vue-router'

import '../semantic/dist/semantic.js'

import App from 'src/App.vue'
import Projects from './pages/Projects.vue'
import Results from './pages/Results.vue'
import Upload from './pages/Upload.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/', redirect: { name: 'projects' }},
  { path: '/projects', name: 'projects', component: Projects },
  { path: '/upload', name: 'upload', component: Upload },
  { path: '/results/:projectId', name: 'results', component: Results, props: true }
]

const router = new VueRouter({
  routes
})

const app = new Vue({
  router,
  render: h => h(App)
})
app.$mount('#app')
