<template>
  <div id="app">
    <div class="ui dimmer inverted">
      <div class="ui loader"></div>
    </div>
    <router-view></router-view>
  </div>
</template>
<script>
  export default {
    mounted () {
      this.$router.afterEach((to, from) => {
        window.scrollTo(0, 0) // Scroll to top
      })
    }
  }
</script>
<style lang="stylus">
  @import '../semantic/dist/semantic.css'

  div#app
    font-family: 'Avenir', Helvetica, Arial, sans-serif
    -webkit-font-smoothing: antialiased
    -moz-osx-font-smoothing: grayscale
    color: #2c3e50
    padding-top: 15px
    height: calc(100% - 15px)
    .center
      text-align: center
</style>