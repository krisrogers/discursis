<template>
  <div id="results">
    <div class="ui center">
      <h2 v-if="project">{{ project.name }}</h2>
    </div>
    <div class="ui left internal rail">
      <button class="ui labeled icon blue button left floated" @click="$router.push({ name: 'projects' })">
        <i class="list icon"></i>
        View Projects
      </button>
    </div>
    <div class="ui pointing secondary menu">
      <div class="active item" data-tab="plot">Recurrence Plot</div>
      <div class="item" data-tab="exports">Data Exports</div>
      <div class="item" data-tab="cluster">Cluster Layout</div>
      <div class="item" data-tab="similar-terms">Similar Terms</div>
    </div>
    <div class="ui bottom attached active tab segment" data-tab="plot">
      <recurrence-plot :project="project" v-if="project"></recurrence-plot>
    </div>
    <div class="ui bottom attached tab segment" data-tab="exports">
      <exports :project="project" v-if="project"></exports>
    </div>
    <div class="ui bottom attached tab segment" data-tab="cluster">
      <cluster-layout :projectId="projectId" ref="cluster"></cluster-layout>
    </div>
    <div class="ui bottom attached tab segment" data-tab="similar-terms">
      <similar-terms :projectId="projectId" ref="similar-terms"></similar-terms>
    </div>
  </div>
</template>
<script>
import $ from 'jquery'

import ClusterLayout from '../widgets/ClusterLayout.vue'
import Exports from '../widgets/Exports.vue'
import RecurrencePlot from '../widgets/RecurrencePlot.vue'
import SimilarTerms from '../widgets/SimilarTerms.vue'
import Server from 'src/server'

export default {
  components: { ClusterLayout, Exports, RecurrencePlot, SimilarTerms },
  props: ['projectId'],
  data () {
    return {
      project: null
    }
  },
  mounted () {
    Server.getProject(this.projectId).then((result) => {
      this.project = result.data
    })
    this.$nextTick(() => {
      $(this.$el).find('.menu .item').tab(({
        'onVisible': (tab) => {
          if (tab === 'cluster') {
            this.$refs.cluster.activate()
          }
        }
      }))
    })
  }
}
</script>
<style lang="stylus" scoped>
  #results
    height: 100%
    .ui.pointing.menu
      margin-top: 30px
      .item
        cursor: pointer
    .ui.tab.segment
      border-top: 0
      margin: 0
      padding: 0
      height: calc(100% - 100px)
      overflow-y: auto
</style>
