import axios from 'axios'

// import auth from 'src/api/auth'

const API_URL = `http://${window.location.hostname}:5000`
axios.defaults.headers.post['Content-Type'] = 'application/json'

// Add a response interceptor
axios.interceptors.response.use(function (response) {
  // Success code, do nothing
  return response
}, function (error) {
  const resp = error.response
  // Failure code
  if (resp && resp.status === 401 && resp.data.message.toLowerCase().includes('expired token')) {
    console.log()
    axios.$app.$store.clearAuthToken()
    location.reload()
  }
  return Promise.reject(error)
})

export default {

  isValidJwt (jwt) {
    if (!jwt || jwt.split('.').length < 3) {
      return false
    }
    const data = JSON.parse(atob(jwt.split('.')[1]))
    const exp = new Date(data.exp * 1000) // JS deals with dates in milliseconds since epoch
    const now = new Date()
    return now < exp
  },

  // Download channel similarity with specified model settings.
  downloadChannelSimilarity (projectId, modelType, numTerms) {
    let url = `${API_URL}/projects/${projectId}/exports/channel-similarity?model=${modelType}`
    if (numTerms) {
      url += `&num_terms=${numTerms}`
    }
    window.open(url)
  },

  // Download primitives with specified model settings.
  downloadPrimitives (projectId, modelType, numTerms) {
    let url = `${API_URL}/projects/${projectId}/exports/primitives?model=${modelType}`
    if (numTerms) {
      url += `&num_terms=${numTerms}`
    }
    window.open(url)
  },

  getUploadUrl () {
    return `${API_URL}/upload`
  },

  // Get list of all available projects.
  getProjects () {
    return axios.get(`${API_URL}/projects`)
  },

  // Get info about a specific project.
  getProject (id) {
    return axios.get(`${API_URL}/projects/${id}`)
  },

  // Delete the specified project.
  deleteProject (id) {
    return axios.delete(`${API_URL}/projects/${id}`)
  },

  // Get Recurrence and Utterance data.
  getRecurrence (projectId, modelType, numTerms) {
    let params = {
      model: modelType
    }
    if (numTerms) {
      params.num_terms = numTerms
    }
    return axios.get(`${API_URL}/projects/${projectId}/model`, { params: params })
  },
  getCluster (projectId, clusterType) {
    let params = {
      clusterType: clusterType
    }
    return axios.get(`${API_URL}/projects/${projectId}/cluster`, { params: params })
  },
  // Retrieve info about similar terms, optionally specifying a custom threshold.
  getSimilarTerms (projectId, threshold) {
    let params = {}
    if (threshold) {
      params.threshold = threshold
    }
    return axios.get(`${API_URL}/projects/${projectId}/similar_terms`, { params: params })
  },
  // Retrieve 2d layout of terms.
  getTermLayout (projectId) {
    let params = {}
    return axios.get(`${API_URL}/projects/${projectId}/term_layout`, { params: params })
  }
}
