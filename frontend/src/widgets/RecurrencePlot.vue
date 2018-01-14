<template>
  <div id="plot-container">
    <div class="utterance-count" v-if="utteranceCount">Showing Utterances 1 to {{ utterances.length }} of {{ utteranceCount }}</div>
    <!-- Plot options dialog -->
    <div class="ui right internal attached rail plot-options center">
      <div class="ui segment stacked">
        <div class="ui sub header">Model</div>
        <div class="ui selection dropdown model-type">
          <i class="dropdown icon"></i>
          <div class="default text"></div>
          <div class="menu">
            <div class="item" data-value="composition">Compositional</div>
            <div class="item" data-value="composition-delta">Compositional Delta</div>
            <div class="item" data-value="term">Term</div>
          </div>
        </div>
        <i class="large add square icon settings-btn" @click="toggleSettings"></i>
        <div class="ui transition hidden settings">
          <div class="ui divider"></div>
          <div>
            Number of terms:
            <div class="ui inline compact dropdown num-terms">
              <div class="text"></div>
              <i class="dropdown icon"></i>
              <div class="menu">
                <div class="item">all</div>
                <div class="item">25</div>
                <div class="item">50</div>
                <div class="item">100</div>
              </div>
            </div>
          </div>
          <!-- Plot item sizing -->
          <div>
            <label>Plot Sizing: </label>
            <div class="ui inline compact dropdown plot-sizing">
              <div class="text"></div>
              <i class="dropdown icon"></i>
              <div class="menu">
                <div class="item">scaled</div>
                <div class="item">uniform</div>
              </div>
            </div>
          </div>
          <!-- Recurrence visibility -->
          <div>
            <label>Minimum recurrence: </label>
            <div class="ui inline compact dropdown recurrence-floor">
              <div class="text"></div>
              <i class="dropdown icon"></i>
              <div class="menu">
                <div class="item">auto</div>
                <div class="item">0</div>
                <div class="item">0.1</div>
                <div class="item">0.2</div>
                <div class="item">0.3</div>
                <div class="item">0.4</div>
                <div class="item">0.5</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <plot-info :plotItems="selectedItems" :recurrenceMatrix="recurrenceMatrix"></plot-info>

    <!-- Plot container -->
    <div id="plot"></div>

  </div>
</template>
<script>
  import $ from 'jquery'
  import * as d3 from 'd3'
  import Konva from 'konva'

  import PlotInfo from './PlotInfo.vue'
  import Server from 'src/server'
  import EventBus from 'src/bus.js'
  import Util from 'src/util.js'

  // http://colorbrewer2.org
  const COLOURS = [
    '#1f78b4', '#e31a1c', '#b15928',
    '#33a02c', '#fb9a99', '#ff7f00',
    '#cab2d6', '#6a3d9a', '#ffff99'
  ]

  export default {
    components: { PlotInfo },
    props: ['projectId'],
    data () {
      return {
        utterances: null,
        utteranceCount: null,
        recurrenceMatrix: null,
        canvasEvent: false,
        initialised: false,
        numTerms: 'all',
        modelType: 'composition',
        sizing: 'scaled',
        recurrenceFloor: 'auto',
        boxSizeMin: 6,
        boxSizeMax: 20,
        selectedItems: null
      }
    },
    watch: {
      numTerms () { this.getData() },
      modelType () { this.getData() },
      sizing (v) { this.draw() },
      recurrenceFloor () { this.draw() }
    },
    mounted () {
      let labelFloor = () => {
        if (this.recurrenceFloor === 'auto') {
          let rf = this.modelType.startsWith('composition') ? 0.3 : 0
          $(this.$el).find('.ui.dropdown.recurrence-floor').dropdown('set text', `auto (${rf})`)
        }
      }
      this.$nextTick(() => {
        $(this.$el).find('.ui.dropdown').dropdown()
        $(this.$el).find('.ui.dropdown.model-type').dropdown('set selected', this.modelType).dropdown({
          onChange: (v) => {
            this.modelType = v
            labelFloor()
          }
        })
        $(this.$el).find('.ui.dropdown.plot-sizing').dropdown('set selected', this.sizing).dropdown({
          onChange: (v) => { this.sizing = v }
        })
        $(this.$el).find('.ui.dropdown.num-terms').dropdown('set selected', this.numTerms).dropdown({
          onChange: (v) => { this.numTerms = v }
        })
        $(this.$el).find('.ui.dropdown.recurrence-floor').dropdown('set selected', this.recurrenceFloor).dropdown({
          onChange: (v) => {
            this.recurrenceFloor = v
            labelFloor()
          }
        })
        labelFloor()
        this.getData()
      })
    },
    methods: {
      getData () {
        let modal = document.querySelector('.ui.dimmer')
        modal.classList.add('active')
        Server.getRecurrence(this.projectId, this.modelType, this.numTerms === 'all' ? null : this.numTerms)
          .then((response) => {
            EventBus.$emit('model-updated', {
              type: this.modelType,
              numTerms: this.numTerms
            })
            modal.classList.remove('active')
            this.recurrenceMatrix = response.data.recurrence_matrix
            this.utterances = response.data.utterances
            this.utteranceCount = response.data.utterance_count
            this.channels = response.data.channels
            this.draw()
          })
          .catch((error) => {
            console.log(error)
          })
      },
      toggleSettings () {
        $(this.$el).find('.settings').toggleClass('hidden')
        $(this.$el).find('.settings-btn').toggleClass('add').toggleClass('minus')
      },
      draw (padding = 50) {
        if (this.stage) {
          this.stage.destroy()
        }
        let floor
        if (this.recurrenceFloor === 'auto') {
          floor = this.modelType.startsWith('composition') ? 0.3 : 0
        } else {
          floor = this.recurrenceFloor
        }
        let boxSizeScale
        if (this.sizing === 'scaled') {
          boxSizeScale = d3.scaleLinear()
            .domain(d3.extent(this.utterances, (u) => u.length))
            .range([this.boxSizeMin, this.boxSizeMax])
        }
        let recurrenceMatrix = this.recurrenceMatrix
        let containerEl = $('#plot')
        let stage = this.stage = new Konva.Stage({
          container: 'plot',
          width: containerEl.width(),
          height: containerEl.height()
        })
        let layer = this.layer = new Konva.Layer()
        stage.add(layer)

        let tooltipLayer = new Konva.Layer()
        stage.add(tooltipLayer)
        let tooltipText = new Konva.Text({
          text: '',
          fontSize: 13,
          padding: 5,
          textFill: 'white',
          fill: 'black',
          alpha: 0.75,
          visible: false
        })
        let tooltipRect = new Konva.Rect({
          stroke: '#555',
          strokeWidth: 1,
          fill: 'white'
        })
        tooltipLayer.add(tooltipRect)
        tooltipLayer.add(tooltipText)

        var createTooltip = function (shape, text, offset = 10, maxWidth = 250) {
          shape.on('mousemove', function () {
            var mousePos = stage.getPointerPosition()
            tooltipText.text(text)
            tooltipText.position({
              x: mousePos.x + offset,
              y: mousePos.y
            })
            tooltipText.width(Math.min(tooltipText.width(), maxWidth))
            tooltipRect.position({
              x: mousePos.x + offset,
              y: mousePos.y
            })
            tooltipRect.width(tooltipText.getWidth())
            tooltipRect.height(tooltipText.getHeight())
            tooltipText.show()
            tooltipRect.show()
            tooltipLayer.batchDraw()
          })
          shape.on('mouseout', function () {
            tooltipText.hide()
            tooltipRect.hide()
            tooltipLayer.draw()
          })
        }

        let xPos = padding
        recurrenceMatrix.forEach((col, i) => {
          let iUtterance = this.utterances[i]
          let colour = COLOURS[this.channels.indexOf(iUtterance.channel)]
          iUtterance.colour = colour
          let colWidth, rowHeight
          if (this.sizing === 'uniform') {
            colWidth = rowHeight = (this.boxSizeMax + this.boxSizeMin) / 2
          } else {
            colWidth = rowHeight = boxSizeScale(iUtterance.length)
          }
          let diagBox = new Konva.Rect({
            x: xPos,
            y: xPos,
            width: colWidth,
            height: rowHeight,
            fill: colour
          })
          let self = this
          diagBox.on('mouseover', function () {
            this.stroke('black')
            layer.draw()
          })
          diagBox.on('mousedown', function () {
            self.canvasEvent = true
          })
          diagBox.on('mouseout', function () {
            self.canvasEvent = false
            this.stroke(null)
            layer.draw()
          })
          diagBox.on('click', function (item) {
            this.canvasEvent = false
            this.selectedItems = [item]
          }.bind(this, iUtterance))
          let tipText = `Utterance: ${i + 1}`
          if (iUtterance.themes) {
            tipText += `\nThemes: ${iUtterance.themes.join(', ')}`
          } else {
            tipText += Util.truncate(`\nConcepts: ${iUtterance.concepts.join(', ')}`)
          }
          createTooltip(diagBox, tipText)
          layer.add(diagBox)
          let yPos = xPos + rowHeight
          for (let j = i + 1; j < col.length; j++) {
            let jUtterance = this.utterances[j]
            if (this.sizing === 'scaled') {
              rowHeight = boxSizeScale(jUtterance.length)
            }
            if (col[j] >= floor) {
              let colour2 = COLOURS[this.channels.indexOf(jUtterance.channel)]
              let boxConfig = {
                x: xPos,
                y: yPos,
                width: colWidth,
                height: rowHeight,
                opacity: col[j]
              }
              if (colour !== colour2) {
                boxConfig.fillLinearGradientStartPoint = { x: 0, y: 0 }
                boxConfig.fillLinearGradientEndPoint = { x: colWidth, y: rowHeight }
                boxConfig.fillLinearGradientColorStops = [0, colour, 1, colour2]
              } else {
                boxConfig.fill = colour2
              }
              let box = new Konva.Rect(boxConfig)
              box.on('mouseover', function () {
                this.stroke('black')
                layer.draw()
              })
              box.on('mousedown', function () {
                self.canvasEvent = true
              })
              box.on('mouseout', function () {
                self.canvasEvent = false
                this.stroke(null)
                layer.draw()
              })
              box.on('click', function (item1, item2) {
                this.canvasEvent = false
                this.selectedItems = [item1, item2]
              }.bind(this, iUtterance, jUtterance))
              let sim = Math.round(100 * col[j]) / 100
              let tipText = `${sim} \nUtterances: ${iUtterance.id + 1}, ${jUtterance.id + 1}`
              if (false && iUtterance.themes) {
                let sharedThemes = iUtterance.themes.filter((c) => jUtterance.themes.indexOf(c) >= 0)
                tipText += `\nShared themes: ${sharedThemes.join(', ')}`
              } else {
                let sharedConcepts = iUtterance.concepts.filter((c) => jUtterance.concepts.indexOf(c) >= 0)
                tipText += Util.truncate(`\nShared concepts: ${sharedConcepts.join(', ')}`)
              }
              createTooltip(box, tipText)
              layer.add(box)
            }
            yPos += rowHeight
          }
          xPos += colWidth
        })

        if (!this.initialised) {
          // Setup zoom
          d3.select('#plot').call(
            d3.zoom().scaleExtent([0.5, 8]).on('zoom', this.zoom)
              .filter(() => {
                // Don't zoom when canvas events are in progress/started;
                // Not just useful for UX, but essential as D3 zoom eats click events otherwise.
                return !this.canvasEvent
              })
          )
          this.initialised = true
        } else if (this.scale) {
          // Make sure we initialise correct zoom and position on redraw
          this.layer.scale(this.scale)
          this.layer.position(this.position)
        }

        layer.draw()
        document.querySelector('.ui.dimmer').classList.remove('active')
      },
      // Zoom based on d3 event transform
      zoom () {
        let transform = d3.event.transform
        this.scale = { x: transform.k, y: transform.k }
        this.position = { x: transform.x, y: transform.y }
        this.layer.scale(this.scale)
        this.layer.position(this.position)
        this.layer.batchDraw() // Batch draw limits redraw to cycles of animation engine
      }
    }
  }
</script>
<style lang="stylus" scoped>
  #plot-container
    height: 100%
    .plot-options
      position: fixed !important
      z-index: 1
      .settings-btn
        cursor: pointer
        margin-left: 20px
      .num-terms.dropdown
        width: 40px
    .ui.dropdown.compact
      margin-top: 5px
    div#plot
      height: 100%

    .utterance-count
      position: absolute
      background-color: white
      color: #95a6ac
      margin-left: 10px
      font-size: 0.9em
      line-height: 0.9em
      margin-bottom: 0
      padding: 0
      z-index: 99
</style>
