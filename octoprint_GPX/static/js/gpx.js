$(function() {

    function Axis() {
        this.max_feedrate = undefined;
        this.home_feedrate = undefined;
        this.steps_per_mm = undefined;
        this.endstop = undefined;
    };

    function Extruder() {
        this.max_feedrate = undefined;
        this.steps_per_mm = undefined;
        this.motor_steps = undefined;
    };

    function ExtruderOverride() {
        this.active_temperature = undefined;
        this.standby_temperature = undefined;
        this.build_platform_temperature = undefined;
        this.actual_filament_diameter = undefined;
        this.packing_density = undefined;
    };

    function GpxSettingsViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];

        var iniInitial = {
            printer: {
                machine_type: "r1d",
                gcode_flavor: "reprap",
                ditto_printing: 0,
                build_progress: 1,
                packing_density: undefined,
                recalculate_5d: 0,
                slicer_filament_diameter: undefined,
                build_platform_temperature: undefined,
                sd_card_path: undefined
            },
            x: new Axis(),
            y: new Axis(),
            z: new Axis(),
            a: new Extruder(),
            b: new Extruder(),
            left: new ExtruderOverride(),
            right: new ExtruderOverride(),
            machine: {
                nozzle_diameter: undefined,
                extruder_count: undefined,
                has_heated_build_platform: undefined, // bool
                timeout: undefined
            }
        };

        self.ini = ko.mapping.fromJS(iniInitial);

        self.showMachineDialog = function() {
            $("#gpx_machine_settings").modal("show");
        };

        self.showEepromDialog = function() {
            $("#gpx_eeprom_settings").modal("show");
        };

        self.requestData = function() {
            $.getJSON("/plugin/GPX/ini", function(data) {
                console.log(data);
                ko.mapping.fromJS(data, self.ini);
            });
        };

        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
        };

        self.onAfterBinding = function() {
            $('#gpx_settings').find('[data-toggle=tooltip]').tooltip({placement: 'left'});
            $('#gpx_machine_settings').find('[data-toggle=tooltip]').tooltip();
        };

        self.onSettingsShown = self.requestData;

        self.onSettingsBeforeSave = function() {
            var ini = ko.mapping.toJS(self.ini);
            $.ajax({
                url: "/plugin/GPX/ini",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify(ko.mapping.toJS(ini)),
                success: function(response) {
                }
            });
        };
    };

    function GpxMachineViewModel(parameters) {
        var self = this;

        self.gpx = parameters[0];

        var machineInitial = {
            x: new Axis(),
            y: new Axis(),
            z: new Axis(),
            a: new Extruder(),
            b: new Extruder(),
            machine: {
                slicer_filament_diameter: undefined,
                packing_density: undefined,
                nozzle_diameter: undefined,
                extruder_count: undefined,
                has_heated_build_platform: undefined, // bool
                timeout: undefined
            }
        };

        self.machine = ko.mapping.fromJS(machineInitial);

        $("#gpx_machine_settings").on("show", function(event) {
            if (event.target.id == "gpx_machine_settings")
                self.requestMachine();
        });

        self.requestMachine = function() {
            $.getJSON("/plugin/GPX/machine/" + self.gpx.ini.printer.machine_type(), function(data) {
                ko.mapping.fromJS(data, self.machine);
            });
        };

        self.requestMachineDefaults = function() {
            $.getJSON("/plugin/GPX/defaultmachine/" + self.gpx.ini.printer.machine_type(), function(data) {
                ko.mapping.fromJS(data, self.machine);
            });
        };

        self.saveMachineSettings = function() {
            var machine = ko.mapping.toJS(self.machine);
            $.ajax({
                url: "/plugin/GPX/machine/" + self.gpx.ini.printer.machine_type(),
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify(ko.mapping.toJS(machine)),
                success: function(response) {
                }
            });
            $("#gpx_machine_settings").modal("hide");
        };
    };

    function GpxEepromViewModel(parameters) {
        var self = this;

        self.gpx = parameters[0];

        self.axes = { X: 0, Y: 1, Z: 2, A: 3, B: 4 };

        self.eeprom = {
            HBP_PRESENT: ko.observable(0),
        };

        self.invert_axis = {};
        for (axis in self.axes) {
            self.invert_axis[axis] = ko.observable(false);
        }
        self.invert_axis.Z(true);

        $("#gpx_eeprom_settings").on("show", function(event) {
            if (event.target.id == "gpx_eeprom_settings") {
                self.requestEepromSettings();
            }
        });

        self.requestEepromSettings = function() {
            self.eeprom.HBP_PRESENT(1);
        };

        self.saveEepromSettings = function() {
            $("#gpx_eeprom_settings").modal("hide");
        };
    };

    OCTOPRINT_VIEWMODELS.push([
        GpxSettingsViewModel,
        ["settingsViewModel"],
        ["#gpx_settings"]
    ]);
    OCTOPRINT_VIEWMODELS.push([
        GpxMachineViewModel,
        ["gpxSettingsViewModel"],
        ["#gpx_machine_settings"]
    ]);
    OCTOPRINT_VIEWMODELS.push([
        GpxEepromViewModel,
        ["gpxSettingsViewModel"],
        ["#gpx_eeprom_settings"]
    ]);
});
