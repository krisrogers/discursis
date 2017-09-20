import axios from 'axios'
import Vue from 'vue'

const Store = new Vue({
  data () {
    return {
      project: null
    }
  },
  methods: {
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
