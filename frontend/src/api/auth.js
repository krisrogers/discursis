import axios from 'axios'

const API_URL = `http://${window.location.hostname}:5000`

export default {

  // Login with the specified credentials; returns a JWT token.
  login (email, password) {
    return axios.post(`${API_URL}/login/`, { email, password })
  },

  // Register for an account; returns a JWT token
  register (email, password) {
    return axios.post(`${API_URL}/register/`, { email, password })
  },

  sendResetPasswordLink (email) {
    let base_url = `${window.location.origin}/#/reset-password-finish`
    return axios.post(`${API_URL}/send-reset-password-link/`, { base_url, email })
  },

  updatePassword (token, email, password) {
    return axios.post(`${API_URL}/update-password/`, { token, email, password })
  },

  verifyResetPasswordToken (token, email) {
    return axios.post(`${API_URL}/verify-reset-password-token/`, { token, email })
  }
}
