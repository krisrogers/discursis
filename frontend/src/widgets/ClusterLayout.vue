<template>
  <div id="cluster"></div>
</template>
<script>
  import $ from 'jquery'
  import * as d3 from 'd3'

  import Server from 'src/server'

  export default {
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
        // this.getData()
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
        Server.getClusterLayout().then((response) => {
          console.log(response)
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

        let nodes = svg.selectAll('circle')
          .data(termVectors)
          .enter()
          .append('g')
          .attr('transform', (d, i) => {
            d.x = xScale(d[0])
            d.y = yScale(d[1])
            return `translate(${d.x},${d.y})`
          })
        nodes.append('circle')
          .attr('r', (d, i) => 6)
          .style('fill', (d) => 'blue')
        nodes.append('text')
          .attr('text-anchor', 'middle')
          .text((d, i) => terms[i])
      }
    }
  }
</script>
<style lang="stylus">
  #cluster
    height: 100%
</style>