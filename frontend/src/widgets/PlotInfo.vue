<template>
  <div class="ui right internal attached rail item-info" v-if="mutablePlotItems">
    <div class="ui segment">
      <i class="red window close icon" @click="mutablePlotItems = null"></i>
      <div v-if="mutablePlotItems.length > 1">
        Similarity: <b>{{ similarity }}</b><br>
        Shared concepts: {{ sharedConcepts }}
      </div>
      <div class="ui stacked segments" v-for="selectedItem in mutablePlotItems">
        <div class="ui segment">
          <span class="ui ribbon label" :style="{ backgroundColor : selectedItem.colour, color: 'white' }">{{ selectedItem.channel }}</span>
          <span class="utterance-index"># {{ selectedItem.id + 1 }}</span>
        </div>
        <div class="ui segment">
          {{ selectedItem.text }}
        </div>
        <div class="ui segment">
          <div v-if="selectedItem.themes">
            <b>{{ selectedItem.themes.join(', ') }}</b>
          </div>
          ({{ selectedItem.concepts.join(', ') }})
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  export default {
    props: ['plotItems', 'recurrenceMatrix'],
    computed: {
      similarity () {
        return Math.round(this.recurrenceMatrix[this.mutablePlotItems[0].id][this.mutablePlotItems[1].id] * 100) / 100
      },
      sharedConcepts () {
        return this.mutablePlotItems[0].concepts.filter((c) => this.mutablePlotItems[1].concepts.indexOf(c) >= 0).join(', ')
      }
    },
    data () {
      return {
        mutablePlotItems: null
      }
    },
    watch: {
      plotItems (v) {
        this.mutablePlotItems = v
      }
    }
  }
</script>
<style lang="stylus" scoped>
  .item-info.rail
    height: auto
    max-height: 600px
    overflow-y: auto
    width: 600px
    z-index: 2
    .close.icon
      float: right
      line-height: 5px
      cursor: pointer
    .utterance-index
      font-weight: bold
      font-size: 1.6em
      line-height: 26px
      float: right
</style>