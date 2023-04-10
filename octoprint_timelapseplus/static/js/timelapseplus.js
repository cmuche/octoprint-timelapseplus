$(function() {
    function TimelapsePlusViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settings = parameters[1];
        self.someOtherViewModel = parameters[2];

        self.isRunning = ko.observable();
        self.snapshotCount = ko.observable();
        self.previewImage = ko.observable();
        self.frameCollections = ko.observable();
        self.videos = ko.observable();
        self.renderJobs = ko.observable();

        self.onAllBound = function(allViewModels) {
            self.triggerGetData();
        };

        self.delete = function(type, id) {
            var payload = {
                command: "delete",
                type:type,
                id:id
            };

            $.ajax({
                url: API_BASEURL + "plugin/octoprint_timelapseplus",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {

                },
                complete: function() {

                }
            });
        };

        self.triggerGetData = function() {
            var payload = {
                command: "getData"
            };

            $.ajax({
                url: API_BASEURL + "plugin/octoprint_timelapseplus",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {

                },
                complete: function() {

                }
            });
        };

        self.startRender = function(data) {
            console.log(data);

            var payload = {
                command: "render",
                frameZipId: data.id
            };

            $.ajax({
                url: API_BASEURL + "plugin/octoprint_timelapseplus",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {

                },
                complete: function() {

                }
            });
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "octoprint_timelapseplus")
                return;

            console.log("DATA", data);

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
        elements: ["#timelapseplus"]
    });
});