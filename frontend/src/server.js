import axios from 'axios'

const API_URL = `http://${window.location.hostname}:5000`

export default {

  // Download channel similarity with specified model settings.
  downloadChannelSimilarity (projectId, modelType, numTerms) {
    let url = `${API_URL}/projects/${projectId}/exports/channel-similarity?model=${modelType}`
    if (numTerms) {
      url += `&num_terms=${numTerms}`
    }
    window.open(url)
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
