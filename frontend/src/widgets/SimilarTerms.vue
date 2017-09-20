<template>
  <div>
    <div>
      <label>Distance Threshold: </label>
      <div class="ui inline compact dropdown distance-threshold">
        <div class="text"></div>
        <i class="dropdown icon"></i>
        <div class="menu">
          <div class="item">0.1</div>
          <div class="item">0.2</div>
          <div class="item">0.5</div>
          <div class="item">1</div>
          <div class="item">2</div>
        </div>
      </div>
    </div>
    <div v-if="clusters">
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
        distanceThreshold: 0.5,
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
          for (let clusterName in response.data) {
            clusters.push({
              name: clusterName,
              terms: response.data[clusterName]
            })
          }
          this.clusters = clusters
          dimmer.classList.remove('active')
        })
      }
    }
  }
</script>