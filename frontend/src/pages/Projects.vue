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
    <table class="ui celled selectable table">
      <thead>
        <tr>
          <th>Name</th>
          <th class="remove-col">&nbsp;</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="project in projects">
          <td @click="$router.push({ name: 'results' , params: { projectId: project.id }})">
            {{ project.name }}
          </td>
          <td>
            <i class="red remove icon" @click="deleteProject(project)"></i>
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
      getData () {
        let dimmer = document.querySelector('.ui.dimmer')
        dimmer.classList.add('active')
        Server.getProjects().then((result) => {
          this.projects = result.data
          dimmer.classList.remove('active')
        })
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
    width: 60%
    min-width: 400px
    td:nth-child(2), th:nth-child(2)
      border-left: none !important
      width: 40px
    tbody tr
      cursor: pointer
    .remove.icon
      cursor: pointer
      transition: font-size 200ms
      line-height: 1.4rem
      &:hover
        font-size: 1.4rem
</style>
