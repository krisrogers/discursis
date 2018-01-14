/* Utility functions */
export default {

  // Download the `data` as CSV with specified `filename`.
  downloadCSV (data, filename) {
    // Generate csv data
    let csv = data.map((row) => {
      return row.join(',')
    }).join('\n')
    csv = 'data:text/csv;charset=utf-8,' + csv
    data = encodeURI(csv)

    // Trigger download
    let link = document.createElement('a')
    link.setAttribute('href', data)
    link.setAttribute('download', filename)
    link.click()
    document.removeChild(link)
  },

  truncate (text, maxChars = 150) {
    if (text.length > maxChars) {
      return text.slice(0, maxChars - 3) + '...'
    }
    return text
  }
}
