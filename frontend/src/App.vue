<template>
  <div id="app">
    <div class="ui dimmer inverted">
      <div class="ui loader"></div>
    </div>
    <div v-if="email" class="logged-in">
      Logged in as {{ email }} | <div class="logout-link" @click="logout">Logout</div>
    </div>
    <router-view></router-view>
  </div>
</template>
<script>
  import Store from 'src/store.js'

  export default {
    data () {
      return {
        email: Store.getUser()
      }
    },
    mounted () {
      Store.$on('login', () => { this.email = Store.getUser() })
      this.$router.afterEach((to, from) => {
        window.scrollTo(0, 0) // Scroll to top
      })
    },
    methods: {
      logout () {
        Store.clearAuthToken()
        this.email = false
        this.$router.push('login')
      }
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
    padding-top: 40px
    height: calc(100% - 40px)
    .center
      text-align: center

    .logged-in
      position: absolute
      right: 20px
      top: 20px
      .logout-link
        color: #2185D0
        cursor: pointer
        display: inline-block

    .button.loading
      pointer-events: none

    .header
      margin-bottom: 30px

    .message
      font-size: 14px
      font-weight: bold
</style>