<template>
  <div>
    <h2>Projects</h2>
    <div class="ui left internal rail">
      <button class="ui labeled icon blue button left floated" @click="$router.push({ name: 'upload' })">
        <i class="add square icon"></i>
        Create Project
      </button>
    </div>

    <!-- Delete modal -->
    <div id="delete-project-modal" class="ui basic modal">
      <div class="ui icon header">
        <i class="trash icon"></i>
        Delete {{ projectToDelete? projectToDelete.name : '' }}
      </div>
      <div class="ui content" style="text-align: center">
        <p>Are you sure you want to delete this project? <b>This action is irreversible</b>.</p>
      </div>
      <div class="actions">
        <div class="ui basic cancel inverted button">
          <i class="remove icon"></i>
          Cancel
        </div>
        <div class="ui red ok inverted button">
          <i class="checkmark icon"></i>
          Delete it
        </div>
      </div>
    </div>

    <!-- Projects list -->
    <table class="ui celled selectable striped table">
      <thead>
      </thead>
      <tbody>
        <tr v-for="project in projects" :class="{ 'clickable': project.status.toLowerCase() === 'ready' }">
          <td @click="clickProject(project)">
            {{ project.name }}
            <div class="status error" v-if="project.status.toLowerCase() === 'error'" :title="project.status_info">
              {{ project.status }}
            </div>
            <div class="status running" v-else-if="project.status.toLowerCase() === 'running'">
              <div class="ui active inline tiny loader"></div>{{ project.status }}
            </div>
            <div class="status" v-else>
              {{ project.status }}
            </div>
          </td>
          <td>
            <i class="red remove icon" @click="deleteProject(project)" v-if="project.status.toLowerCase() === 'ready' || project.status.toLowerCase() === 'error'"></i>
          </td>
        </tr>
        <tr v-if="projects.length === 0">
          <td colspan="2">No projects yet.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script>
  import $ from 'jquery'

  import Server from 'src/server'

  export default {
    components: { },
    data () {
      return {
        projects: [],
        projectToDelete: null
      }
    },
    mounted () {
      this.$nextTick(() => {
        this.getData()
      })
    },
    methods: {
      clickProject (project) {
        if (project.status.toLowerCase() === 'ready') {
          this.$router.push({ name: 'results', params: { projectId: project.id }})
        }
      },
      getData (update = false) {
        let dimmer
        if (!update) {
          dimmer = document.querySelector('.ui.dimmer')
          dimmer.classList.add('active')
        }
        Server.getProjects().then((result) => {
          this.projects = result.data
          if (!update) {
            dimmer.classList.remove('active')
          }
        })
        setTimeout(() => {
          this.getData(true)
        }, 5000)
      },
      deleteProject (project) {
        this.projectToDelete = project
        $('#delete-project-modal').modal('show').modal({
          onApprove: () => {
            let dimmer = document.querySelector('.ui.dimmer')
            dimmer.classList.add('active')
            Server.deleteProject(this.projectToDelete.id).then(() => {
              this.projectToDelete = null
              this.getData()
            })
          }
        })
      }
    }
  }
</script>
<style lang="stylus" scoped>
  h2
    text-align: center

  .table
    font-size: 1.1rem
    margin: 20px auto
    width: 500px
    td:nth-child(2), th:nth-child(2)
      border-left: none !important
      width: 40px
    tbody tr.clickable
      cursor: pointer
      &:hover .remove.icon
        visibility: visible
    td
      font-size: 14px
      font-weight: bold
      div.status
        padding: 3px 0px 3px 9px
        font-size: 13px
        font-weight: normal
        color: #808080
        &.error
          color: #db2828
        &.running
          color: #f2711c
          .loader
            margin-right: 10px
            vertical-align: top
    .remove.icon
      cursor: pointer
      visibility: hidden
      line-height: 1.4rem
      font-size: 24px
    tr:hover .remove-icon
      visibility: visible
</style>
