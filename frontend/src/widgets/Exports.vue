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
          <!-- Channel similarity -->
          <div class="card" @click="downloadChannelSimilarity">
            <div class="content">
              <div class="header">Channel Similarities <i class="download icon"></i></div>
              <div class="description">
                Cumulative similaritiy between all channel pairs.
              </div>
            </div>
          </div>
          <!-- Primitives -->
          <div class="card" @click="downloadPrimitives">
            <div class="content">
              <div class="header">Primitives <i class="download icon"></i></div>
              <div class="description">
                Cumulative similarity over predefined utterance ranges.
              </div>
            </div>
          </div>
          <!-- Themes -->
          <div class="card" @click="downloadThemes" v-if="modelConfig.type && modelConfig.type.startsWith('composition')">
            <div class="content">
              <div class="header">Themes <i class="download icon"></i></div>
              <div class="description">
                Themes identified for utterances.
              </div>
            </div>
          </div>
           <!-- Concepts -->
          <div class="card" @click="downloadConcepts">
            <div class="content">
              <div class="header">Concepts <i class="download icon"></i></div>
              <div class="description">
                Concepts identified for utterances.
              </div>
            </div>
          </div>
           <!-- Concept layout -->
          <div class="card" @click="downloadConceptLayout">
            <div class="content">
              <div class="header">Concept Layout <i class="download icon"></i></div>
              <div class="description">
                Concept positions in 2D layout.
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
  import Util from 'src/util'

  export default {
    props: ['project'],
    data () {
      return {
        modelConfig: {}
      }
    },
    mounted () {
      EventBus.$on('model-updated', modelConfig => {
        this.modelConfig = modelConfig
      })
      EventBus.$on('layout-updated', concepts => {
        this.layoutConcepts = concepts
      })
    },
    methods: {
      downloadChannelSimilarity () {
        Server.downloadChannelSimilarity(this.project.id, this.modelConfig.type, this.modelConfig.numTerms)
      },
      downloadConceptLayout () {
        console.log(this.layoutConcepts)
        // Generate data
        let headers = ['Concept', 'X', 'Y', 'Frequency']
        let data = [headers]
        this.layoutConcepts.forEach((concept) => {
          data.push([concept.name, concept.position[0], concept.position[1], concept.frequency])
        })
        Util.downloadCSV(data, `${this.project.name}-concept-layout.csv`)
      },
      downloadConcepts () {
        // Build list of concepts
        let concepts = new Set()
        this.modelConfig.data.utterances.forEach((u) => {
          u.concepts.forEach((c) => {
            concepts.add(c)
          })
        })
        concepts = Array.from(concepts)
        concepts.sort()
        let conceptIndex = {}
        concepts.forEach((c, i) => {
          conceptIndex[c] = i
        })

        // Generate data
        let headers = ['Utterance'].concat(concepts)
        let data = [headers]
        this.modelConfig.data.utterances.forEach((u, i) => {
          let row = Array.apply(null, Array(concepts.length)).map(Number.prototype.valueOf, 0)
          for (let concept of u.concepts) {
            row[conceptIndex[concept]] = 1
          }
          data.push([i].concat(row))
        })
        Util.downloadCSV(data, `${this.project.name}-${this.modelConfig.numTerms}-concepts.csv`)
      },
      downloadPrimitives () {
        Server.downloadPrimitives(this.project.id, this.modelConfig.type, this.modelConfig.numTerms)
      },
      // Download themes for composition model.
      downloadThemes () {
        // Build list of themes
        let themes = new Set()
        this.modelConfig.data.utterances.forEach((u) => {
          u.themes.forEach((t) => {
            themes.add(t)
          })
        })
        themes = Array.from(themes)
        themes.sort()
        let themeIndex = {}
        themes.forEach((t, i) => {
          themeIndex[t] = i
        })

        // Generate data
        let headers = ['Utterance'].concat(themes)
        let data = [headers]
        this.modelConfig.data.utterances.forEach((u, i) => {
          let row = Array.apply(null, Array(themes.length)).map(Number.prototype.valueOf, 0)
          for (let theme of u.themes) {
            row[themeIndex[theme]] = 1
          }
          data.push([i].concat(row))
        })
        Util.downloadCSV(data, `${this.project.name}-themes.csv`)
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