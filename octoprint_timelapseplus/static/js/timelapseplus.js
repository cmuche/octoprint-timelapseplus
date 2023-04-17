$(function() {
    function TimelapsePlusViewModel(parameters) {
        let self = this;

        self.settings = parameters[0];
        self.settings.parent = self;

        self.snapshotCommand = ko.observable();
        self.captureMode = ko.observable();
        self.captureTimerInterval = ko.observable();
        self.isRunning = ko.observable(false);
        self.currentFileSize = ko.observable(0);
        self.snapshotCount = ko.observable(0);
        self.previewImage = ko.observable(null);
        self.frameCollections = ko.observable([]);
        self.videos = ko.observable([]);
        self.renderJobs = ko.observable([]);

        self.presetsEnhancement = ko.observable([]);
        self.presetsRender = ko.observable([]);
        self.selectedPresetEnhancement = ko.observable();
        self.selectedPresetRender = ko.observable();
        self.selectedFrameZip = ko.observable();
        self.selectedRenderPresetVideoLength = ko.observable(0);

        self.selectedPresetRender.subscribe(function(data) {
            self.api("getRenderPresetVideoLength", {preset: data, frameZipId: self.selectedFrameZip().id}, function(res) {
                self.selectedRenderPresetVideoLength(res.length);
            });
        });

        // https://stackoverflow.com/questions/10420352/converting-file-size-in-bytes-to-human-readable-string
        self.humanFileSize = function(size) {
            let i = size == 0 ? 0 : Math.floor(Math.log(size) / Math.log(1024));
            return (size / Math.pow(1024, i)).toFixed(2) * 1 + " " + ["B", "kB", "MB", "GB", "TB"][i];
        };

        // https://stackoverflow.com/questions/6108819/javascript-timestamp-to-relative-time
        self.timeDifference = function(ts) {
            const msPerMinute = 60 * 1000;
            const msPerHour = msPerMinute * 60;
            const msPerDay = msPerHour * 24;
            const msPerMonth = msPerDay * 30;
            const msPerYear = msPerDay * 365;

            const elapsed = new Date() - ts * 1000;

            if (elapsed < msPerMinute)
                return Math.round(elapsed / 1000) + " seconds ago";
            else if (elapsed < msPerHour)
                return Math.round(elapsed / msPerMinute) + " minutes ago";
            else if (elapsed < msPerDay)
                return Math.round(elapsed / msPerHour) + " hours ago";
            else if (elapsed < msPerMonth)
                return Math.round(elapsed / msPerDay) + " days ago";
            else if (elapsed < msPerYear)
                return Math.round(elapsed / msPerMonth) + " months ago";
            else
                return Math.round(elapsed / msPerYear) + " years ago";
        };

        self.timeSpan = function(ms) {
            ms = Math.abs(ms);

            if (ms < 1000)
                return "0s";

            let days = Math.floor(ms / (1000 * 60 * 60 * 24));
            ms -= days * (1000 * 60 * 60 * 24);

            let hours = Math.floor(ms / (1000 * 60 * 60));
            ms -= hours * (1000 * 60 * 60);

            let mins = Math.floor(ms / (1000 * 60));
            ms -= mins * (1000 * 60);

            let seconds = Math.floor(ms / (1000));
            ms -= seconds * (1000);

            let str = "";
            if (days > 0 || str.length > 0)
                str += days + "d ";
            if (hours > 0 || str.length > 0)
                str += hours + "h ";
            if (mins > 0 || str.length > 0)
                str += mins + "m ";
            if (days == 0 && (seconds > 0 || str.length > 0))
                str += seconds + "s ";

            return str.trim();
        };

        self.timeSpanMedia = function formatDuration(duration) {
            let seconds = Math.floor((duration / 1000) % 60);
            let minutes = Math.floor((duration / (1000 * 60)) % 60);
            let hours = Math.floor(duration / (1000 * 60 * 60));

            let formattedSeconds = seconds < 10 ? "0" + seconds : seconds;
            let formattedMinutes = minutes < 10 ?  minutes : minutes;
            let formattedHours = hours > 0 ? hours + ":" : "";

            return `${formattedHours}${formattedMinutes}:${formattedSeconds}`;
        };

        self.openBlurMask = function(preset) {
            $("<input type=\"file\">").on("change", function() {
                let f = this.files[0];

                let reader = new FileReader();
                reader.readAsDataURL(f);
                reader.onload = function() {
                    self.api("createBlurMask", {image: reader.result}, function(res) {
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

        self.addEnhancementPreset = function(listObservable) {
            self.api("defaultEnhancementPreset", {}, function(res) {
                listObservable.push(ko.mapping.fromJS(res));
            });
        };

        self.addRenderPreset = function(listObservable) {
            self.api("defaultRenderPreset", {}, function(res) {
                listObservable.push(ko.mapping.fromJS(res));
            });
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

        self.getCaptureModeName = function(mode) {
            let modeMap = {
                "COMMAND": "Command",
                "TIMED": "Timer"
            };

            if (mode in modeMap)
                return modeMap[mode];

            return mode;
        };

        self.api = function(command, payload = {}, successFn = null) {
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
                    console.log("Error (Command=" + command + ")", err);
                }
            });
        };

        self.delete = function(type, id) {
            self.api("delete", {type: type, id: id});
        };

        self.triggerGetData = function() {
            self.api("getData");
        };

        self.openRenderDialog = function(frameZip) {
            self.api("listPresets", {}, function(data) {
                self.selectedFrameZip(frameZip);
                self.presetsEnhancement(data.enhancementPresets);
                self.presetsRender(data.renderPresets);
                self.selectedPresetEnhancement(data.enhancementPresets[0]);
                self.selectedPresetRender(data.renderPresets[0]);

                $("div#tlp-modal-render").modal({
                    width: "auto"
                });
            });
        };

        self.startRender = function() {
            self.api("render", {
                frameZipId: self.selectedFrameZip().id,
                presetEnhancement: self.selectedPresetEnhancement(),
                presetRender: self.selectedPresetRender()
            });
            $("div#tlp-modal-render").modal("hide");
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "octoprint_timelapseplus")
                return;

            console.log(data);

            if (data.type == "popup") {
                new PNotify({
                    title: data.title,
                    text: data.message,
                    type: data.popup,
                    hide: true
                });
                return;
            }

            self.snapshotCommand(data.snapshotCommand);
            self.captureMode(data.captureMode);
            self.captureTimerInterval(data.captureTimerInterval);
            self.isRunning(data.isRunning);
            self.currentFileSize(data.currentFileSize);
            self.snapshotCount(data.snapshotCount);
            self.previewImage(data.previewImage == null ? null : "data:image/jpeg;base64," + data.previewImage);
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