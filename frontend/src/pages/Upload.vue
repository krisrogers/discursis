<template>
  <div>
    <h2>Create Project</h2>
    <div class="ui left internal rail">
      <button class="ui labeled icon blue button left floated" @click="$router.push({ name: 'projects' })">
        <i class="list icon"></i>
        View Projects
      </button>
    </div>
    <dropzone ref="dropzone" id="file-upload" url="http://localhost:5000/upload" :autoProcessQueue="false" :duplicateCheck="true" :uploadMultiple="true" @vdropzone-file-added="addFile" @vdropzone-removed-file="removeFile" :acceptedFileTypes="'.csv'" @vdropzone-success-multiple="uploadSuccess" @vdropzone-sending-multiple="beforeUpload" @vdropzone-error="uploadError" @vdropzone-queue-complete="uploadComplete">
    </dropzone>
    <div class="ui basic segment form">
      <div class="inline field">
        <label>Project Name</label>
        <input type="text" v-model="projectName" placeholder="Enter project name...">
      </div>
    </div>
    <div class="ui basic segment">
      <button :disabled="hasFiles === false || projectName.length === 0" class="positive ui button" @click="processFiles">Process Files</button>
      <div class="ui negative message upload-error" v-if="error">
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>
<script>
  import Dropzone from 'vue2-dropzone/src/index.vue'

  export default {
    components: { Dropzone },
    data () {
      return {
        error: null,
        hasFiles: false,
        projectName: ''
      }
    },
    methods: {
      addFile (file) {
        // if (this.$refs.projectName)
        if (this.projectName.length === 0) {
          this.projectName = file.name.split('.')[0]
        }
        this.hasFiles = true
      },
      removeFile (file) {
        this.hasFiles = this.$refs.dropzone.getQueuedFiles().length > 0
      },
      // Upload & process files
      processFiles () {
        document.querySelector('.ui.dimmer').classList.add('active')
        this.$refs.dropzone.processQueue()
      },
      // Inject form data before upload
      beforeUpload (files, xhr, formData) {
        formData.append('project_name', this.projectName)
        this.error = null
      },
      // Continue after success
      uploadSuccess (files, result) {
        result = JSON.parse(result)
        document.querySelector('.ui.dimmer').classList.remove('active')
        this.$router.push({ name: 'results', params: { projectId: result.id }})
      },
      // Post-processing after upload
      uploadComplete (f, r) {
        if (this.error) {
          // Re-queue files
          // Can't do this in `uploadError` method as dropzone changes file status after it runs.
          let dz = this.$refs.dropzone.dropzone
          for (var i = 0; i < dz.files.length; i++) {
            let file = dz.files[i]
            file.status = 'queued'
            file.upload.progress = 0
            file.upload.bytesSent = 0
            file.previewElement.classList.remove('dz-error')
            file.previewElement.classList.remove('dz-processing')
            file.previewElement.classList.remove('dz-complete')
            file.previewElement.querySelector('.dz-progress .dz-upload').style.width = 0
          }
        }
      },
      // Handle server error
      uploadError (files, error) {
        error = JSON.parse(error)
        this.error = error.msg
        document.querySelector('.ui.dimmer').classList.remove('active')
      }
    }
  }
</script>
<style lang="stylus" scoped>
  div
    text-align: center
  .upload-error
    margin: 20px auto
    text-align: left
    width: 800px
  .ui.form input[type='text']
    width: 300px
</style>