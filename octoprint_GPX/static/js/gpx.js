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

        self.eeromids = [
            "TOOLCOUNT", "HBP_PRESENT", "PSTOP_ENABLE", "ESTOP_ENABLE", "AXIS_INVERSION",
            "ENDSTOP_INVERSION", "AXIS_HOME_POSITIONS_STEPS_X", "AXIS_HOME_POSITIONS_STEPS_Y",
            "AXIS_HOME_POSITIONS_STEPS_Z", "AXIS_HOME_POSITIONS_STEPS_A", "AXIS_HOME_POSITIONS_STEPS_B",
            "TOOLHEAD_OFFSET_SETTINGS_X", "TOOLHEAD_OFFSET_SETTINGS_Y",
            "DIGI_POT_SETTINGS_0", "DIGI_POT_SETTINGS_1", "DIGI_POT_SETTINGS_2", "DIGI_POT_SETTINGS_3", "DIGI_POT_SETTINGS_4",
            "AXIS_STEPS_PER_MM_X", "AXIS_STEPS_PER_MM_Y", "AXIS_STEPS_PER_MM_Z", "AXIS_STEPS_PER_MM_A", "AXIS_STEPS_PER_MM_B",
        ];

        self.eeprom = {
            TOOLCOUNT: ko.observable(0),
            HBP_PRESENT: ko.observable(0),
            PSTOP_ENABLE: ko.observable(0),
            ESTOP_ENABLE: ko.observable(0),
            AXIS_HOME_POSITIONS_X: ko.observable(0),
            AXIS_HOME_POSITIONS_Y: ko.observable(0),
            AXIS_HOME_POSITIONS_Z: ko.observable(0),
            AXIS_HOME_POSITIONS_A: ko.observable(0),
            AXIS_HOME_POSITIONS_B: ko.observable(0),
            AXIS_STEPS_PER_MM_X: ko.observable(0),
            AXIS_STEPS_PER_MM_Y: ko.observable(0),
            AXIS_STEPS_PER_MM_Z: ko.observable(0),
            AXIS_STEPS_PER_MM_A: ko.observable(0),
            AXIS_STEPS_PER_MM_B: ko.observable(0),
            AXIS_INVERSION: ko.observable(0),
        };

        self.z_hold = false;

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
            $.ajax({
                url: "/plugin/GPX/eeprombatch",
                type: "POST",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify(self.eepromids),
                success: function(response) {
                    ko.mapping.fromJS(response, self.eeprom);
                    self.home.X(self.eeprom.AXIS_HOME_POSITIONS_X / self.eeprom.AXIS_STEPS_PER_MM_X);
                    self.home.Y(self.eeprom.AXIS_HOME_POSITIONS_Y / self.eeprom.AXIS_STEPS_PER_MM_Y);
                    self.home.Z(self.eeprom.AXIS_HOME_POSITIONS_Z / self.eeprom.AXIS_STEPS_PER_MM_Z);
                    self.home.A(self.eeprom.AXIS_HOME_POSITIONS_A / self.eeprom.AXIS_STEPS_PER_MM_A);
                    self.home.B(self.eeprom.AXIS_HOME_POSITIONS_B / self.eeprom.AXIS_STEPS_PER_MM_B);
                    self.invert_axis.X(!!(self.eeprom.AXIS_INVERSION & 0x1));
                    self.invert_axis.Y(!!(self.eeprom.AXIS_INVERSION & 0x2));
                    self.invert_axis.Z(!!(self.eeprom.AXIS_INVERSION & 0x4));
                    self.invert_axis.A(!!(self.eeprom.AXIS_INVERSION & 0x8));
                    self.invert_axis.B(!!(self.eeprom.AXIS_INVERSION & 0x10));
                    self.z_hold = !!(self.eeprom.AXIS_INVERSION & 0x80);
                }
            });
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
