<template>
  <div>
    <div class="ui middle aligned center aligned grid">
      <div class="column">
        <h2 class="ui teal image header">
          <div class="content">
            Reset Password
          </div>
        </h2>
        <div v-if="proccessed" class="success-msg">
          <p><i class="teal check icon"></i></p>
          <p>If the email address you provided is registered, you should receive an email shortly.</p>
        </div>
        <form class="ui large form" v-else>
          <div class="ui stacked segment">
            <div class="field">
              <div class="ui left icon input">
                <i class="user icon"></i>
                <input type="text" v-model="email" name="email" placeholder="E-mail address">
              </div>
            </div>
            <div class="ui fluid large teal submit button">Reset</div>
          </div>
          <!-- Validation errors -->
          <div class="ui error message"></div>

        </form>
        <div class="ui error message" v-show="error">
          <i class="frown outline icon big"></i>
          Sorry, we couldn't process your request. Please try again.
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
        email: '',
        error: false,
        proccessed: false
      }
    },
    mounted () {
      this.form = $(this.$el).find('.ui.form')
        .form({
          fields: {
            email: ['email', 'empty']
          },
          onSuccess: (event, fields) => {
            event.preventDefault() // Prevent semantic-ui form submission
            let btn = this.$el.querySelector('form .button')
            btn.classList.add('loading')
            this.error = false
            auth.sendResetPasswordLink(fields.email)
              .then((response) => {
                this.proccessed = true
              })
              .catch(() => {
                btn.classList.remove('loading')
                this.error = true
              })
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

  .success-msg
    font-size: 17px
    .icon
      font-size: 50px
      padding-bottom: 10px
      padding-top: 20px
</style>