<template>
  <div class="ui grid">
    <div class="row">
      <div class="three wide column">
        <h5>Exports generated using the current settings for the Recurrence Plot:</h5>
        <i>Type: </i> <b>{{ modelConfig.type }}</b>
        <br>
        <i>Number of Terms: </i><b>{{ modelConfig.numTerms }}</b>
      </div>
      <div class="thirteen wide column">
        <div class="ui cards">
          <div class="card" @click="downloadChannelSimilarity">
            <div class="content">
              <div class="header">Channel Similarities <i class="download icon"></i></div>
              <div class="description">
                Cumulative similaritiy between all channel pairs.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  import EventBus from 'src/bus.js'
  import Server from 'src/server'

  export default {
    props: ['projectId'],
    data () {
      return {
        modelConfig: {}
      }
    },
    mounted () {
      EventBus.$on('model-updated', modelConfig => {
        this.modelConfig = modelConfig
      })
    },
    methods: {
      downloadChannelSimilarity () {
        Server.downloadChannelSimilarity(this.projectId, this.modelConfig.type, this.modelConfig.numTerms)
      }
    }
  }
</script>
<style lang="stylus" scoped>
  .ui.grid
    margin: 15px 15px
  .card
    cursor: pointer
    &:hover
      box-shadow: 0px 1px 3px 0px #D4D4D5, 0px 0px 0px 1px #2185D0
      .download.icon
        color: #2185D0
    .header
      font-size: 1.1em !important
    .download.icon
      float: right
      font-size: 1em
</style>