/* Utility functions */
import Papa from 'papaparse'

export default {

  // Download the `data` as CSV with specified `filename`.
  downloadCSV (data, filename) {
    // Generate csv data
    let csv = Papa.unparse(data)
    let url = URL.createObjectURL(new Blob([csv], {
      type: 'text/csv'
    }))

    // Trigger download
    let link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.click()
  },

  truncate (text, maxChars = 150) {
    if (text.length > maxChars) {
      return text.slice(0, maxChars - 3) + '...'
    }
    return text
  }
}
