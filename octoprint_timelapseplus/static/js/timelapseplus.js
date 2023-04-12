$(function() {
    function TimelapsePlusViewModel(parameters) {
        let self = this;

        self.settings = parameters[0];
        self.settings.parent = self;

        self.isRunning = ko.observable(false);
        self.snapshotCount = ko.observable(0);
        self.previewImage = ko.observable(null);
        self.frameCollections = ko.observable([]);
        self.videos = ko.observable([]);
        self.renderJobs = ko.observable([]);

        self.openBlurMask = function(preset) {
            console.log("openBlurMask");
            $("<input type=\"file\">").on("change", function() {
                let f = this.files[0];

                let reader = new FileReader();
                reader.readAsDataURL(f);
                reader.onload = function() {
                    self.apiBlueprint("createBlurMask", {image: reader.result}, function(res) {
                        preset.blurMask(res.id);
                    });
                };
                reader.onerror = function(error) {
                    console.log("Error", error);
                };
            }).click();
        };

        self.openVideo = function(video) {
            $("div#tlp-modal-video").modal({
                width: "auto"
            });

            $("div#tlp-modal-video video source")[0].src = video.url;
            $("div#tlp-modal-video video")[0].load();
            $("div#tlp-modal-video video")[0].currentTime = 0;
            $("div#tlp-modal-video video").trigger("play");
        };

        self.onAllBound = function(allViewModels) {
            self.triggerGetData();
        };

        self.formatPercent = function(percent) {
            return Math.round(percent) + "%";
        };

        self.showRenderJobs = function() {
            return self.renderJobs().length > 0;
        };

        self.getRenderJobVm = function(job) {
            let stateVms = {
                "WAITING": {title: "Waiting", showProgress: false, icon: "fas fa-hourglass-half"},
                "EXTRACTING": {title: "Extracting Frame Collection", showProgress: false, icon: "fas fa-box-open"},
                "RENDERING": {title: "Rendering Video", showProgress: true, icon: "fas fa-file-export"},
                "FINISHED": {title: "Finished", showProgress: false, icon: "fas fa-check"},
                "FAILED": {title: "Failed", showProgress: false, icon: "fas fa-exclamation-triangle"},
                "ENHANCING": {title: "Enhancing Images", showProgress: true, icon: "fas fa-magic"},
                "BLURRING": {title: "Blurring Areas", showProgress: true, icon: "fas fa-eraser"},
                "RESIZING": {title: "Resizing Frames", showProgress: true, icon: "fas fa-arrows-alt"}
            };

            if (job.state in stateVms)
                return stateVms[job.state];

            return {title: job.state, showProgress: false};
        };

        self.api = function(command, payload = {}, successFn = null) {
            payload["command"] = command;

            $.ajax({
                url: API_BASEURL + "plugin/octoprint_timelapseplus",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (successFn !== null)
                        successFn(response);
                },
                complete: function() {
                },
                error: function(err) {
                    console.log("Error", err);
                }
            });
        };

        self.apiBlueprint = function(command, payload = {}, successFn = null) {
            $.ajax({
                url: "./plugin/octoprint_timelapseplus/" + command,
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (successFn !== null)
                        successFn(response);
                },
                complete: function() {
                },
                error: function(err) {
                    console.log("Error", err);
                }
            });
        };

        self.delete = function(type, id) {
            self.api("delete", {type: type, id: id});
        };

        self.triggerGetData = function() {
            self.api("getData");
        };

        self.startRender = function(data) {
            self.api("render", {frameZipId: data.id});
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "octoprint_timelapseplus")
                return;

            console.log(data);

            self.isRunning(data.isRunning);
            self.snapshotCount(data.snapshotCount);
            self.previewImage("data:image/jpeg;base64," + data.previewImage);
            self.frameCollections(data.frameCollections);
            self.videos(data.videos);
            self.renderJobs(data.renderJobs);
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: TimelapsePlusViewModel,
        dependencies: ["settingsViewModel"],
        elements: ["#timelapseplus"]
    });
});