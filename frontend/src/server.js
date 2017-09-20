import axios from 'axios'

export default {

  // Get list of all available projects.
  getProjects () {
    return axios.get('http://localhost:5000/projects')
  },

  // Get info about a specific project.
  getProject (id) {
    return axios.get(`http://localhost:5000/projects/${id}`)
  },

  // Delete the specified project.
  deleteProject (id) {
    return axios.delete(`http://localhost:5000/projects/${id}`)
  },

  // Get Recurrence and Utterance data.
  getRecurrence (projectId, modelType, numTerms) {
    let params = {
      model: modelType
    }
    if (numTerms) {
      params.num_terms = numTerms
    }
    return axios.get(`http://localhost:5000/projects/${projectId}/model`, { params: params })
  },
  getCluster (projectId, clusterType) {
    let params = {
      clusterType: clusterType
    }
    return axios.get(`http://localhost:5000/projects/${projectId}/cluster`, { params: params })
  },
  // Retrieve info about similar terms, optionally specifying a custom threshold.
  getSimilarTerms (projectId, threshold) {
    let params = {}
    if (threshold) {
      params.threshold = threshold
    }
    return axios.get(`http://localhost:5000/projects/${projectId}/similar_terms`, { params: params })
  }
}
