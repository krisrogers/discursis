<template>
  <div>
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

  import Server from 'src/server'

  export default {
    props: ['projectId'],
    data () {
      return {
        distanceThreshold: 0.01,
        ignoredTerms: null,
        clusters: null
      }
    },
    watch: {
      distanceThreshold () {
        console.log('update mofo')
        this.getData()
      }
    },
    mounted () {
      this.$nextTick(() => {
        $(this.$el).find('.ui.dropdown.distance-threshold').dropdown('set selected', this.distanceThreshold).dropdown({
          onChange: (v) => { this.distanceThreshold = v }
        })
        this.getData()
      })
    },
    methods: {
      getData () {
        let dimmer = document.querySelector('.ui.dimmer')
        dimmer.classList.add('active')
        Server.getSimilarTerms(this.projectId, this.distanceThreshold).then((response) => {
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