<template>
  <div>
    <div class="ui middle aligned center aligned grid signup-container">
      <div class="column">
        <h2 class="ui teal image header">
          <div class="content">
           Signup for an account
          </div>
        </h2>
        <form class="ui large form" :class="{ 'error': error }" @submit.prevent="signup">
          <div class="ui stacked segment">
            <div class="field">
              <div class="ui left icon input">
                <i class="user icon"></i>
                <input type="text" v-model="email" name="email" placeholder="E-mail address">
              </div>
            </div>
            <div class="field">
              <div class="ui left icon input">
                <i class="lock icon"></i>
                <input type="password" v-model="password" name="password" placeholder="Password">
              </div>
            </div>
            <div class="field">
              <div class="ui left icon input">
                <i class="lock icon"></i>
                <input type="password" name="password2" placeholder="Confirm Password">
              </div>
            </div>
            <div class="ui fluid large teal submit button" @click="signup">Signup</div>
          </div>

          <div class="ui error message">
            <p v-if="error">{{ error }}</p>
          </div>

        </form>

        <div class="ui message">
          Already have an account? <router-link to="login">Login</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import $ from 'jquery'

  import auth from 'src/api/auth'
  import Store from 'src/store.js'

  export default {
    data () {
      return {
        email: '',
        password: '',
        error: null
      }
    },
    mounted () {
      $(this.$el).find('.ui.form')
        .form({
          fields: {
            email: ['email', 'empty'],
            password: ['minLength[6]', 'empty'],
            password2: 'match[password]'
          },
          onSuccess (event, fields) {
            // Prevent semantic-ui form submission
            event.preventDefault()
          }
        })
    },
    methods: {
      signup () {
        this.error = null
        auth.register(this.email, this.password)
          .then((response) => {
            // Auto login
            auth.login(this.email, this.password)
              .then((response) => {
                Store.setAuthToken(this.email, response.data.token)
                this.$router.push('/')
              })
              .catch(() => {
                this.form.form('add errors', ['Something went wrong. Please contact us.'])
              })
          })
          .catch((error) => {
            this.error = error.response.data.error
          })
      }
    }
  }
</script>

<style>
  .column {
    width: 500px !important;
  }
</style>