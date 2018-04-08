import axios from 'axios'
import Vue from 'vue'

const Store = new Vue({
  data () {
    return {
      user: {},
      project: null
    }
  },
  methods: {
    clearAuthToken () {
      this.user.email = null
      this.user.token = null
      delete axios.defaults.headers.common['Authorization']
      document.cookie = `DISCURSIS_AUTH=; expires=0`
    },
    getAuthToken () {
      if (!this.user.token) {
        // Attempt to readauth token from cookies
        // https://developer.mozilla.org/en-US/docs/Web/API/Document/cookie
        let auth = document.cookie.replace(/(?:(?:^|.*;\s*)DISCURSIS_AUTH\s*\=\s*([^;]*).*$)|^.*$/, '$1')
        if (auth) {
          let parts = auth.split(',')
          this.user.email = parts[0]
          this.user.token = parts[1]
          axios.defaults.headers.common['Authorization'] = this.user.token
        }
      }
      return this.user.token
    },
    getUser () {
      return this.user.email
    },
    setAuthToken (email, token) {
      this.user.email = email
      this.user.token = token
      axios.defaults.headers.common['Authorization'] = token
      document.cookie = `DISCURSIS_AUTH=${email},${token}; expires=Fri, 31 Dec 9999 23:59:59 GMT`
      this.$emit('login')
    },
    setProject (project) {
      console.log('SET', project)
      this.project = project
    },
    getProject () {
      if (this.project) {
        return new Promise((resolve) => {
          resolve(this.project)
        })
      }
      return new Promise((resolve, reject) => {
        axios.get('http://localhost:5000/model')
          .then((response) => {
            resolve(response.data)
          })
          .catch(reject)
      })
    }
  }
})
export default Store
