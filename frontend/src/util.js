/* Utility functions */
export default {
  truncate (text, maxChars = 150) {
    if (text.length > maxChars) {
      return text.slice(0, maxChars - 3) + '...'
    }
    return text
  }
}
