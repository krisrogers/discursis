<template>
  <div id="cluster"></div>
</template>
<script>
  import $ from 'jquery'
  import * as d3 from 'd3'

  import Server from 'src/server'

  export default {
    props: ['projectId'],
    data () {
      return {
        loaded: false,
        terms: null,
        termVectors: null,
        clusterLabels: null
      }
    },
    mounted () {
      this.$nextTick(() => {
        this.getData()
      })
    },
    methods: {
      activate () {
        if (!this.loaded) {
          this.draw(this.terms, this.termVectors, this.clusterLabels)
          this.loaded = true
        }
      },
      getData () {
        Server.getTermLayout(this.projectId).then((response) => {
          let terms = []
          let termVectors = []
          response.data.terms.forEach((term) => {
            terms.push(term)
            termVectors.push(term.position)
          })
          this.terms = terms
          this.termVectors = termVectors
          this.clusterLabels = Object.keys(response.data.clusters)
        })
      },
      draw (terms, termVectors, clusterLabels, padding = 20) {
        let el = $('#cluster')
        let width = el.width()
        let height = el.height()
        let xScale = d3.scaleLinear().domain(d3.extent(termVectors, (v) => v[0])).range([padding, width - padding])
        let yScale = d3.scaleLinear().domain(d3.extent(termVectors, (v) => v[1])).range([padding, height - padding])
        // let radiusScale = d3.scaleLinear().domain(d3.extent(this.topicFreqs)).range([16, 40])

        let svg = d3.select(el.get(0)).append('svg')
          .attr('width', width)
          .attr('height', height)

        let circles = svg.selectAll('circle')
          .data(termVectors)
          .enter()
          .append('circle')
          .attr('transform', (d, i) => {
            d.x = xScale(d[0])
            d.y = yScale(d[1])
            return `translate(${d.x},${d.y})`
          })
          .attr('r', (d, i) => 6)
          .style('fill', (d) => '#8ac8f2')
          .append('title').text((d, i) => terms[i].name)

        svg.selectAll('text')
          .data(terms)
          .enter()
          .append('text')
          .attr('text-anchor', 'middle')
          .attr('transform', (d, i) => {
            let e = circles.data()[i]
            return `translate(${e.x},${e.y})`
          })
          .text((d, i) => d.name)
      }
    }
  }
</script>
<style lang="stylus">
  #cluster
    height: 100%
    svg
      circle:hover
        stroke: black
</style>