<template>
  <div>
    <div class="ui middle aligned center aligned grid">
      <div class="column">
        <h2 class="ui teal image header">
          <div class="content">
            Login to your account
          </div>
        </h2>
        <form class="ui large form" @submit.prevent="login">
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
            <div class="ui fluid large teal submit button" @click="validate">Login</div>
          </div>
          <div class="ui error message"></div>

        </form>

        <div class="ui message">
          New to us? <router-link to="signup">Signup</router-link>, or trouble logging in? <router-link to="reset-password">Reset Password</router-link>
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
        password: ''
      }
    },
    mounted () {
      this.form = $(this.$el).find('.ui.form')
        .form({
          fields: {
            email: ['email', 'empty'],
            password: 'empty'
          },
          onSuccess: (event, fields) => {
            if (event) {
              // Prevent semantic-ui form submission
              event.preventDefault()
            }
            this.login()
          }
        })
    },
    methods: {
      login () {
        auth.login(this.email, this.password)
          .then((response) => {
            Store.setAuthToken(this.email, response.data.token)
            this.$router.push(this.$route.query.redirect || '/')
          })
          .catch(() => {
            this.form.form('add errors', ['Unable to login. Please check your email and password.'])
          })
      },
      // Validate form and submit if OK
      validate () {
        this.form.form('validate form')
      }
    }
  }
</script>

<style>
  .column {
    width: 500px !important;
  }
</style>