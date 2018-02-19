<template>
  <div class="similar-terms-container">
    <div>
      <label>Distance Threshold: </label>
      <div class="ui inline compact dropdown distance-threshold">
        <div class="text"></div>
        <i class="dropdown icon"></i>
        <div class="menu">
          <div class="item">0.01</div>
          <div class="item">0.025</div>
          <div class="item">0.05</div>
          <div class="item">0.1</div>
          <div class="item">0.15</div>
          <div class="item">0.20</div>
          <div class="item">0.25</div>
        </div>
      </div>
    </div>
    <br>
    <div>
      <a href="javascript:void(0)" @click="downloadTranscriptWithSimilarTerms">Generate Transcript with Similar Terms Markup</a>
    </div>
    <div v-if="clusters">
      <div class="ui divider"></div>
      <b><u>{{ ignoredTerms.length }} Ignored Terms</u></b>
      <p>{{ ignoredTerms.join(', ') }}</p>
      <div class="ui divider"></div>
      <b><u>{{ clusters.length }} Clusters</u></b>
      <p v-for="cluster in clusters"><b>{{ cluster.name }}</b>: {{ cluster.terms.join(', ') }}</p>
    </div>
  </div>
</template>
<script>
  import $ from 'jquery'

  import EventBus from 'src/bus.js'
  import Server from 'src/server'
  import Util from 'src/util'

  const DELIMIT = '\u001B'

  export default {
    props: ['project'],
    data () {
      return {
        distanceThreshold: 0.01,
        ignoredTerms: null,
        clusters: null
      }
    },
    watch: {
      distanceThreshold () {
        this.getData()
      }
    },
    mounted () {
      EventBus.$on('model-updated', modelConfig => {
        this.modelConfig = modelConfig
      })
      this.$nextTick(() => {
        $(this.$el).find('.ui.dropdown.distance-threshold').dropdown('set selected', this.distanceThreshold).dropdown({
          onChange: (v) => { this.distanceThreshold = v }
        })
        this.getData()
      })
    },
    methods: {
      // Download a version of the transcript marked up with similar term groupings.
      downloadTranscriptWithSimilarTerms (event) {
        let dimmer = document.querySelector('.ui.dimmer')
        dimmer.classList.add('active')
        setTimeout(() => {
          try {
            // Create replacement map, presence of each cluster term is appended with special markup.
            // The `DELIMIT` character is used to prevent re-entrant matching.
            let clusterMap = []
            this.clusters.forEach((c) => {
              let markup = `$1 (${c.terms.map((t) => `${DELIMIT}${t}${DELIMIT}`).join(', ')})`
              c.terms.forEach((t) => {
                clusterMap.push([new RegExp(`\\b(?<!${DELIMIT})(${t})\\b`, 'g'), markup])
              })
            })
            // Add the markup, removing traces of `DELIMIT` when done.
            let transcriptRows = [['Utterance', 'Channel']]
            transcriptRows = transcriptRows.concat(this.modelConfig.data.utterances.map((u) => {
              let text = u.text
              clusterMap.forEach((cm) => {
                text = text.replace(cm[0], cm[1])
              })
              return [text.replace(new RegExp(DELIMIT, 'g'), ''), u.channel]
            }))
            Util.downloadCSV(transcriptRows, `${this.project.name}-transcript-similar-terms-${this.distanceThreshold}.csv`)
          } finally {
            dimmer.classList.remove('active')
          }
        }, 1)
      },
      getData () {
        let dimmer = document.querySelector('.ui.dimmer')
        dimmer.classList.add('active')
        Server.getSimilarTerms(this.project.id, this.distanceThreshold).then((response) => {
          let clusters = []
          for (let clusterName in response.data.clusters) {
            clusters.push({
              name: clusterName,
              terms: response.data.clusters[clusterName]
            })
          }
          this.clusters = clusters
          this.ignoredTerms = response.data.ignored_terms
          dimmer.classList.remove('active')
        })
      }
    }
  }
</script>
<style lang="stylus" scoped>
  .similar-terms-container
    padding: 10px
</style>