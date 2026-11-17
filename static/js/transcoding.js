
let transcoding = {
    data: null,
    manual_transcode_button: null,
    retry_transcode_button: null,

    init: function(){
        // bind buttons
        self.manual_transcode_button = document.getElementById('manual_transcode');
        self.retry_transcode_button = document.getElementById("retry_transcode");
   
        // event handlers
        self.manual_transcode_button.addEventListener('click', transcoding.handle_manual_transcode);
        self.retry_transcode_button.addEventListener('click', transcoding.handle_retry_transcode);
    },

    update_status: function(data) {
        this.data = data;

        const panel         = document.getElementById("transcoding-panel");
        const status        = document.getElementById("transcoding-status");
        const progressBar   = document.getElementById("transcoding-progress-bar");

        panel.className = this.data.state ? "transcoding-panel running" : "transcoding-panel done";
        status.textContent = this.data.state
            ? `Transcoding: ${this.data.progress === false ? "Running" : this.data.progress + "%"}`
            : "Transcoding: Done";
        progressBar.style.width = this.data.progress === false ? "0%" : `${this.data.progress || 0}%`;

        // Retry button
        if (!this.data.use_transcoded && !this.data.state)
            retry_transcode_button.className = "active";
        else
            retry_transcode_button.className = "";
    },

    handle_manual_transcode: async function() {
        try {
            const response = await fetch("/manual_transcode");
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log(result);
        } catch (error) {
            console.error(error.message);
        }
    },

    handle_retry_transcode: async function() {
        try {
            const response = await fetch("/retry_transcode");
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log(result);
        } catch (error) {
            console.error(error.message);
        }
    }
}

transcoding.init();