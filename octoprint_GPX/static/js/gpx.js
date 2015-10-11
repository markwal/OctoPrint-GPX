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
        self.isOperational = parameters[1].isOperational;

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
            $("#gpx_eeprom_settings").modal({
                minHeight: function() { return Math.min($.fn.modal.defaults.maxHeight(), 645) }
            });
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

        var eeprom = {
            TOOL_COUNT: undefined,
            HBP_PRESENT: undefined,
            PSTOP_ENABLE: undefined,
            CLEAR_FOR_ESTOP: undefined,
            AXIS_INVERSION: undefined,
            ENDSTOP_INVERSION: undefined,
            TOOLHEAD_OFFSET_SETTINGS_X: undefined,
            TOOLHEAD_OFFSET_SETTINGS_Y: undefined,
            DIGI_POT_SETTINGS_0: undefined,
            DIGI_POT_SETTINGS_1: undefined,
            DIGI_POT_SETTINGS_2: undefined,
            DIGI_POT_SETTINGS_3: undefined,
            DIGI_POT_SETTINGS_4: undefined,
            ACCELERATION_ACTIVE: undefined,
            SLOWDOWN_FLAG: undefined,
            OVERRIDE_GCODE_TEMP: undefined,
            HEAT_DURING_PAUSE: undefined,
            SD_USE_CRC: undefined,
            EXTRUDER_HOLD: undefined,
            EXTRUDER_DEPRIME_ON_TRAVEL: undefined,
            EXTRUDER_DEPRIME_STEPS_A: undefined,
            EXTRUDER_DEPRIME_STEPS_B: undefined,
            ALEVEL_MAX_ZPROBE_HITS: undefined,
            ALEVEL_MAX_ZDELTA: undefined,
            T0_EXTRUDER_P_TERM: undefined,
            T0_EXTRUDER_I_TERM: undefined,
            T0_EXTRUDER_D_TERM: undefined,
            T1_EXTRUDER_P_TERM: undefined,
            T1_EXTRUDER_I_TERM: undefined,
            T1_EXTRUDER_D_TERM: undefined,
            JKN_ADVANCE_K: undefined,
            JKN_ADVANCE_K2: undefined,
            TOOLHEAD_OFFSET_SETTINGS_X: undefined,
            TOOLHEAD_OFFSET_SETTINGS_Y: undefined,
            COOLING_FAN_DUTY_CYCLE: undefined,
            T0_COOLING_ENABLE: undefined,
            T0_COOLING_SETPOINT_C: undefined,
            T1_COOLING_ENABLE: undefined,
            T1_COOLING_SETPOINT_C: undefined,
        };
        for (axis in self.axes) {
            eeprom["AXIS_HOME_POSITIONS_STEPS_" + axis] = undefined;
            eeprom["AXIS_STEPS_PER_MM_" + axis] = undefined;
            eeprom["MAX_ACCELERATION_AXIS_" + axis] = undefined;
            eeprom["MAX_SPEED_CHANGE_" + axis] = undefined;
        }

        self.eeprom = ko.mapping.fromJS(eeprom);
        self.eepromids = Object.keys(eeprom);

        self.is_saving = ko.observable(false);
        self.show_fan_pwm = ko.computed(function() { return self.eeprom.COOLING_FAN_DUTY_CYCLE() != undefined && self.eeprom.COOLING_FAN_DUTY_CYCLE() != 255; }, this)
        self.z_hold = ko.observable(undefined);
        self.jkn_k = ko.observable(undefined);
        self.jkn_k2 = ko.observable(undefined);
        self.max_zdelta = ko.observable(undefined);
        self.toolhead_offset = {
            X: ko.observable(undefined),
            Y: ko.observable(undefined)
        };

        self.invert_axis = {};
        self.invert_endstop = {};
        self.home = {};
        self.steps_per_mm = {};
        for (axis in self.axes) {
            self.invert_axis[axis] = ko.observable(undefined);
            self.invert_endstop[axis] = ko.observable(undefined);
            self.home[axis] = ko.observable(undefined);
            self.steps_per_mm[axis] = ko.observable(1.0);
        }

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
                    self.eeprom_raw = response;
                    ko.mapping.fromJS(response, self.eeprom);
                    bit = 0x1;
                    for (axis in self.axes) {
                        self.steps_per_mm[axis](self.eeprom["AXIS_STEPS_PER_MM_" + axis]() / 1000000.0);
                        self.home[axis](self.eeprom["AXIS_HOME_POSITIONS_STEPS_" + axis]() / self.steps_per_mm[axis]());
                        self.invert_axis[axis](!!(self.eeprom.AXIS_INVERSION() & bit));
                        self.invert_endstop[axis](!!(self.eeprom.ENDSTOP_INVERSION() & bit));
                        bit <<= 1;
                    }
                    self.z_hold(!(self.eeprom.AXIS_INVERSION() & 0x80));
                    self.jkn_k(self.eeprom.JKN_ADVANCE_K() / 100000.0);
                    self.jkn_k2(self.eeprom.JKN_ADVANCE_K2() / 100000.0);
                    self.toolhead_offset.X(self.eeprom.TOOLHEAD_OFFSET_SETTINGS_X() /self.steps_per_mm.X());
                    self.toolhead_offset.Y(self.eeprom.TOOLHEAD_OFFSET_SETTINGS_Y() /self.steps_per_mm.Y());
                    self.max_zdelta(self.eeprom.ALEVEL_MAX_ZDELTA() / self.steps_per_mm.Z());
                },
                error: function(response) {
                    console.log(response);
                    new PNotify({
                        title: gettext("Unable to read EEPROM"),
                        text: gettext("Unable to read EEPROM settings. Perhaps because I don't have a matching EEPROM map for your firmware type or version."),
                        type: "error"
                    });
                    $("#gpx_eeprom_settings").modal("hide");
                },
            });
        };

        self.saveEepromSettings = function() {
            self.is_saving(true);
            var bit = 0x1;
            var axis_inversion = self.eeprom.AXIS_INVERSION() & 0x60;
            var endstop_inversion = self.eeprom.ENDSTOP_INVERSION() & 0xe0;
            for (axis in self.axes) {
                self.eeprom["AXIS_HOME_POSITIONS_STEPS_" + axis]((self.home[axis]() * self.steps_per_mm[axis]()) | 0);
                if (self.invert_axis[axis]()) axis_inversion |= bit;
                if (self.invert_endstop[axis]()) endstop_inversion |= bit;
                bit <<= 1;
            }
            if (!self.z_hold()) axis_inversion |= 0x80;
            self.eeprom.AXIS_INVERSION(axis_inversion);
            self.eeprom.ENDSTOP_INVERSION(endstop_inversion);
            self.eeprom.JKN_ADVANCE_K((self.jkn_k() * 100000) | 0);
            self.eeprom.JKN_ADVANCE_K2((self.jkn_k2() * 100000) | 0);
            self.eeprom.TOOLHEAD_OFFSET_SETTINGS_X((self.toolhead_offset.X() * self.steps_per_mm.X()) | 0);
            self.eeprom.TOOLHEAD_OFFSET_SETTINGS_Y((self.toolhead_offset.Y() * self.steps_per_mm.Y()) | 0);
            self.eeprom.ALEVEL_MAX_ZDELTA((self.max_zdelta() * self.steps_per_mm.Z()) | 0);

            var eeprom = {};
            var update = false;
            for (var id in self.eeprom_raw) {
                if (self.eeprom[id]() != self.eeprom_raw[id]) {
                    console.log("id: " + id + " value: " + self.eeprom[id]() + " orig: " + self.eeprom_raw[id]);
                    eeprom[id] = self.eeprom[id]();
                    update = true;
                }
            }
            if (!update) {
                $("#gpx_eeprom_settings").modal("hide");
                self.is_saving(false);
            }
            else {
                $.ajax({
                    url: "/plugin/GPX/puteeprombatch",
                    type: "POST",
                    dataType: "json",
                    contentType: "application/json; charset=UTF-8",
                    data: JSON.stringify(ko.mapping.toJS(eeprom)),
                    error: function(response) {
                        console.log(response);
                        new PNotify({
                            title: gettext("EEPROM not updated!"),
                            text: gettext("Unable to save some or all of your changes. Please consult the log for details."),
                            type: "error"
                        });
                    },
                    success: function(response) {
                        console.log(response);
                        self.is_saving(false);
                        $("#gpx_eeprom_settings").modal("hide");
                    },
                    complete: function() {
                        self.is_saving(false);
                    }
                });
            }
        };
    };

    OCTOPRINT_VIEWMODELS.push([
        GpxSettingsViewModel,
        ["settingsViewModel", "printerStateViewModel"],
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
