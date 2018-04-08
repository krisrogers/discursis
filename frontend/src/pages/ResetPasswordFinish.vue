<template>
  <div>
    <div class="ui middle aligned center aligned grid">
      <div class="column">
        <h2 class="ui teal image header">
          <div class="content">
            {{ verified ? 'Update' : 'Reset' }} Password
          </div>
        </h2>
        <div v-if="!verified && !invalid && !expired" class="checking-msg">
          <div class="ui active centered inline huge loader"></div>
          <p>Checking your details...</p>
        </div>
        <form v-show="verified" class="ui large form">
          <div class="ui stacked segment">
            <div class="field">
              <div class="ui left icon input">
                <i class="user icon"></i>
                <input type="password" v-model="password" name="password" placeholder="New Password">
              </div>
            </div>
            <div class="ui fluid large teal submit button">Update</div>
          </div>
          <!-- Validation errors -->
          <div class="ui error message"></div>

        </form>
        <div class="ui success message" v-show="updated">
          Password Updated! You will be redirected to the <router-link to="login">Login</router-link> page in a few moments...
        </div>
        <div class="ui error message" v-show="invalid || expired">
          <i class="frown outline icon big"></i>
          <template v-if="expired">This password reset link has expired.</template>
          <template v-else>Sorry, we couldn't process your request.</template>
          <br><router-link to="reset-password">Try again</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import $ from 'jquery'

  import auth from 'src/api/auth'

  export default {
    data () {
      return {
        expired: false,
        invalid: false,
        password: '',
        verified: false,
        updated: false
      }
    },
    mounted () {
      // Initialise form
      this.$nextTick(() => {
        this.form = $(this.$el).find('.ui.form')
          .form({
            fields: {
              password: ['minLength[6]', 'empty']
            },
            onSuccess: (event, fields) => {
              event.preventDefault() // Prevent semantic-ui form submission
              let btn = this.$el.querySelector('form .button')
              btn.classList.add('loading')
              this.invalid = false
              this.expired = false
              auth.updatePassword(this.$route.query.token, this.$route.query.email, fields.password)
                .then((response) => {
                  this.updated = true
                  this.setTimeout(() => {
                    this.$router.push({ name: 'login' })
                  }, 3000)
                })
                .catch((error) => {
                  if (error.response.data.expired) {
                    this.expired = true
                  } else {
                    this.invalid = true
                  }
                })
            }
          })
      })
      // Verify the reset token
      auth.verifyResetPasswordToken(this.$route.query.token, this.$route.query.email)
        .then((response) => {
          this.verified = true
        })
        .catch((error) => {
          if (error.response.data.expired) {
            this.expired = true
          } else {
            this.invalid = true
          }
        })
    },
    methods: {
    }
  }
</script>

<style lang="stylus" scoped>
  .column
    width: 500px !important

  .checking-msg
    padding-top: 20px    
    p
      font-size: 18px
      padding-top: 30px
</style>