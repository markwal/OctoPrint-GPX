# coding=utf-8
from __future__ import absolute_import

import os
import re
from collections import OrderedDict

import flask
from flask import request, make_response
from werkzeug.exceptions import BadRequest

import octoprint.plugin
from octoprint.events import Events
from octoprint.server import admin_permission

try:
	import gcodex3g as gpx
except:
	pass

# merges dict b into dict a, deeply
def _merge_dict(a, b):
	for key in b:
		if key in a:
			if isinstance(a[key], dict) and isinstance(b[key], dict):
				_merge_dict(a[key], b[key])
				continue
		a[key] = b[key]
	return a


class GPXPlugin(
		octoprint.plugin.StartupPlugin,
		octoprint.plugin.TemplatePlugin,
		octoprint.plugin.SettingsPlugin,
		octoprint.plugin.EventHandlerPlugin,
		octoprint.plugin.AssetPlugin,
		octoprint.plugin.BlueprintPlugin,
		octoprint.plugin.ProgressPlugin
		):

	def __init__(self):
		self._initialized = False
		self.override_progress = False
		self.printer = None

	# internal initialize
	# we do it this weird way because __init__ gets called before the injected
	# properties but on_after_startup can be too late in the case of auto
	# connect on startup in which case the serial_factory is called first
	def _initialize(self):
		if self._initialized:
			return
		self._initialized = True

		# get the plugin data folder
		old_data_folder = os.path.join(self._settings.global_get_basefolder("base"), "gpxProfiles")
		data_folder = self.get_plugin_data_folder()
		if os.path.isdir(old_data_folder):
			# migrate old folder to new one
			if os.path.isdir(data_folder) and len(os.listdir(data_folder)) > 0:
				self._logger.warn("Both old ({old}) and new ({new}) data folders exist. Not migrating to avoid data loss.".format(
					old=old_data_folder, new=data_folder))
			else:
				import shutil
				if os.path.isdir(data_folder):
					os.rmdir(data_folder)
				shutil.move(old_data_folder, data_folder)
		elif not os.path.isdir(data_folder):
			os.makedirs(data_folder)

		# parse the ini file
		profile_path = os.path.join(data_folder, "gpx.ini")
		from .iniparser import IniParser
		self.iniparser = IniParser(profile_path, self._logger)
		self.override_progress = False
		self.printer = None

		# compile regex
		self._regex_m73 = re.compile("N(\d+) M73 P(\d+)")

	# StartupPlugin
	def on_after_startup(self, *args, **kwargs):
		self._initialize()

	# Softwareupdate hook
	def get_update_information(self, *args, **kwargs):
		return dict(
			gpx=dict(
				displayName="GPX Plugin",
				displayVersion=self._plugin_version,

				# use github release method of version check
				type="github_release",
				user="markwal",
				repo="OctoPrint-GPX",
				current=self._plugin_version,
				prerelease=self._settings.get_boolean(["prerelease"]),

				# update method: pip
				pip="https://github.com/markwal/OctoPrint-GPX/releases/download/{target_version}/OctoPrint-GPX.tar.gz"
			)
		)

	# main serial connection hook
	def serial_factory(self, comm, port, baudrate, timeout, *args, **kwargs):
		if not self._settings.get_boolean(["enabled"]) or port == 'VIRTUAL':
			return None
		self._initialize()
		self.iniparser.read()
		self.override_progress = self.iniparser.get("printer", "build_progress")
		if self.override_progress is None:
			self.override_progress = True
		self._logger.info("Connecting through x3g.")
		try:
			if port is None or port == 'AUTO':
				try:
					import glob
					ports = glob.glob("/dev/serial/by-id/*MakerBot_Industries_The_Replicator*")
					if ports:
						port = os.path.normpath(os.path.join("/dev/serial/by-id/", os.readlink(ports[0])))
				except:
					# oh well, it was worth a try
					self._logger.debug("Failed to discover port via /dev/serial/by-id")
			if not baudrate:
				baudrate = 115200
			if port is None or port == 'AUTO' or baudrate is None or baudrate == 0:
				raise IOError("GPX plugin not able to discover AUTO port and/or baudrate. Please choose specific values for them.")
			from .gpxprinter import GpxPrinter
			self.printer = GpxPrinter(self, port, baudrate, timeout)

			# it's easier to keep the counter straight if we ack every line
			if comm is not None and getattr(comm, "_unknownCommandsNeedAck", None) is not None:
			    comm._unknownCommandsNeedAck = True
			else:
			    self._logger.warn("comm object doesn't have _unknownCommandsNeedAck")

			return self.printer
		except Exception as e:
			self._logger.info("Failed to connect to x3g e = %s." % e);
			raise

	# add x3g/s3g too the allowed extensions
	def get_extension_tree(self, *args, **kwargs):
		return dict(
			machinecode=dict(
				x3g=["x3g", "s3g"]
			)
		)

	# SettingsPlugin
	def get_settings_defaults(self, *args, **kwargs):
		return dict(
				enabled=True,
				prerelease=False,
				verbose=False,
				connection_pause=2.0,
				clear_coords_on_print_start=True)

	def on_settings_save(self, data, *args, **kwargs):
		# do the super, see https://thingspython.wordpress.com/2010/09/27/another-super-wrinkle-raising-typeerror
		# and also foosel/OctoPrint@633d1ae594
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		try:
			self._settings.set_float(["connection_pause"], float(self._settings.get(["connection_pause"])))
		except TypeError:
			self._settings.set_float(["connection_pause"], 2.0)
		if self.printer is not None:
			self.printer.refresh_ini()

	# EventHandlerPlugin
	def on_event(self, event, payload, *args, **kwargs):
		# normally OctoPrint will merely stop sending commands on a cancel this
		# means that whatever is in the printer's queue will complete including
		# ten minutes to heat up the print bed; we circumvent here by telling
		# the bot to stop
		if event == Events.PRINT_CANCELLED:
			if self.printer is not None:
				# jump the queue with an abort
				self.printer.cancel()

	# ProgressPlugin
	def on_print_progress(self, storage, path, progress, *args, **kwargs):
		# override progress inside GPX only works in two pass (offline file)
		# attempt to override here with OctoPrint's notion
		# avoid 100% since that triggers end_build and we'll let that happen
		# explicitly
		if progress < 100 and self.override_progress and self.printer is not None:
			self.printer.progress(progress)

	# gcode processing hook
	def rewrite_m73(self, comm, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# if we're overriding progress and we got an M73 with a P between
		# 0 and 100 exclusive.  We let the 0 and 100 through because they're
		# the begin and end markers
		if self.override_progress:
			match = self._regex_m73.match(cmd)
			if match is not None:
				progress = int(match.group(2))
				if progress > 0 and progress < 100:
					return None,
		return None

	# protocol script hook
	def gcode_scripts(self, comm, script_type, script_name, *args, **kwargs):
		if script_type == "gcode":
			if script_name == "afterPrintCancelled":
				return "(@clear_cancel)", None
			if script_name == "beforePrintStarted":
				self.printer.clear_bot_cancelled()
				currentJob = self._printer.get_current_job()
				try:
					build_name = currentJob["file"]["name"]
					build_name = os.path.splitext(os.path.basename(build_name))[0] if build_name else "OctoPrint"
				except KeyError:
					build_name = "OctoPrint"
				clear_coords = ""
				if self._settings.get_boolean(["clear_coords_on_print_start"]):
					clear_coords="\nG92 X0 Y0 Z0 A0 B0"
				return '(@build "{build_name}")\nM136 ({build_name}){clear_coords}'.format(build_name=build_name, clear_coords=clear_coords), None
		return None

	# AssetPlugin
	def get_assets(self, *args, **kwargs):
		return dict(
			js=["js/gpx.js"],
			css=["css/gpx.css"],
			less=["less/gpx.less"]
		)

	# machine ini handling
	def fetch_machine_ini(self, machineid):
		data_folder = self.get_plugin_data_folder()
		profile_path = os.path.join(data_folder, machineid + ".ini")
		from .iniparser import IniParser
		machine_ini = IniParser(profile_path, self._logger)
		if os.path.isdir(data_folder) and os.path.exists(profile_path) and os.path.isfile(profile_path):
			try:
				machine_ini.read()
				self._logger.info("Read machine definition from %s" % profile_path)
			except IOError:
				self._logger.warn("Unable to read custom machine definition %s" % profile_path)
		return machine_ini

	def fetch_machine(self, machineid):
		if gpx is None:
			return None
		machine = gpx.get_machine_defaults(machineid)
		machine_ini = self.fetch_machine_ini(machineid)
		return _merge_dict(machine, machine_ini.ini)

	def validate_machineid(self, machineid):
		if len(machineid) > 8 or not re.match('[a-zA-z0-9]+$', machineid):
			return make_response("Invalid machineid. Upper or lower case letters and numbers only and 8 chars or less")
		return None

	# BlueprintPlugin
	@octoprint.plugin.BlueprintPlugin.route("/defaultmachine/<string:machineid>", methods=["GET"])
	def defaultmachine(self, machineid, *args, **kwargs):
		response = self.validate_machineid(machineid)
		if response is not None:
			return response
		if gpx is None:
			return None
		try:
			machine = gpx.get_machine_defaults(machineid)
		except ValueError:
			return make_response("Unknown machine id: %s" % machineid, 404)
		return flask.jsonify(self.ini_massage_out(machine))

	@octoprint.plugin.BlueprintPlugin.route("/machine/<string:machineid>", methods=["GET"])
	def machine(self, machineid, *args, **kwargs):
		response = self.validate_machineid(machineid)
		if response is not None:
			return response
		try:
			machine = self.fetch_machine(machineid)
		except ValueError:
			return make_response("Unknown machine id: %s" % machineid, 404)
		return flask.jsonify(self.ini_massage_out(machine))

	@octoprint.plugin.BlueprintPlugin.route("/machine/<string:machineid>", methods=["POST"])
	@admin_permission.require(403)
	def putmachine(self, machineid, *args, **kwargs):
		response = self.validate_machineid(machineid)
		if response is not None:
			return response
		try:
			machine_ini = self.fetch_machine_ini(machineid)
		except ValueError:
			return make_response("Unknown machine id: %s" % machineid, 404)
		defaults = gpx.get_machine_defaults(machineid)
		incoming = self.ini_massage_in(request.json)
		for sectionname, section in incoming.items():
			if sectionname in defaults:
				for option, value in section.items():
					if option in defaults[sectionname]:
						if value == 'undefined':
							incoming[sectionname][option] = ''
							continue
						t = type(defaults[sectionname][option])
						try:
							if t == float:
								value = float(value)
							elif t == int:
								value = int(value)
						except ValueError:
							incoming[sectionname][option] = ''
						if defaults[sectionname][option] == value:
							# delete the option in the output so the builtin default
							# will shine through
							incoming[sectionname][option] = ''
		machine_ini.update(incoming)
		machine_ini.dump()
		machine_ini.write()
		return ('', 200)

	# Mostly the REST service here gives the ini file as specified by gpx
	# including 1 and 0 for boolean true and false whether it is usual or makes
	# semantic sense or not.  An exception is has_heated_build_platform: gpx.ini
	# wants it per toolhead, but we present it per machine in the API.
	def ini_massage_out(self, ini):
		heated = False
		if "a" in ini and "has_heated_build_platform" in ini["a"]:
			if "machine" not in ini:
				ini["machine"] = OrderedDict()
			heated = ini["machine"]["has_heated_build_platform"] = ini["a"]["has_heated_build_platform"]
			del ini["a"]["has_heated_build_platform"]
		if "b" in ini and ini["b"].get("has_heated_build_platform"):
			if "machine" not in ini:
				ini["machine"] = OrderedDict()
			ini["machine"]["has_heated_build_platform"] = heated or ini["b"]["has_heated_build_platform"]
			del ini["b"]["has_heated_build_platform"]
		return ini

	def ini_massage_in(self, ini):
		if "machine" in ini and "has_heated_build_platform" in ini["machine"]:
			if "a" not in ini:
				ini["a"] = {}
			if "b" not in ini:
				ini["b"] = {}
			ini["a"]["has_heated_build_platform"] = ini["b"]["has_heated_build_platform"] = ini["machine"]["has_heated_build_platform"]
			del ini["machine"]["has_heated_build_platform"]
		# Sort the input. Only effects the updated properties that are new,
		# which will then be appended in sorted order. Existing properties will
		# update in-place.
		ini = OrderedDict(sorted(ini.items()))
		for sectionname, section in ini.items():
			ini[sectionname] = OrderedDict(sorted(section.items()))
		return ini

	@octoprint.plugin.BlueprintPlugin.route("/ini", methods=["GET"])
	def ini(self, *args, **kwargs):
		try:
			ini = self.iniparser.read()
		except IOError:
			self._logger.info("Unable to read %s, using defaults." % self.iniparser.filename)
			ini = OrderedDict()
			ini["printer"] = OrderedDict()
			ini["printer"]["machine_type"] = "r2"
		return flask.jsonify(self.ini_massage_out(ini))

	@octoprint.plugin.BlueprintPlugin.route("/ini", methods=["POST"])
	@admin_permission.require(403)
	def putini(self, *args, **kwargs):
		self._logger.debug("putini")
		if not "application/json" in request.headers["Content-Type"]:
			return make_response("Expected content-type JSON", 400)
		try:
			ini = self.ini_massage_in(request.json)
		except BadRequest:
			return make_response("Malformed JSON body in request", 400)
		self.iniparser.update(ini)
		self.iniparser.dump()
		self.iniparser.write()
		return ('', 200)

	def _check_for_json(self, request):
		if not "Content-Type" in request.headers or not "application/json" in request.headers["Content-Type"]:
			self._logger.debug("expected content-type application/json")
			return make_response("Expected content-type application/json", 400)
		try:
			self._logger.debug("request body '%s'" % request.data)
			json = request.json
		except BadRequest:
			self._logger.debug("Malformed JSON body in request")
			return make_response("Malformed JSON body in request", 400)
		return None

	@octoprint.plugin.BlueprintPlugin.route("/eeprombatch", methods=["POST"])
	def batcheeprom(self, *args, **kwargs):
		self._logger.info("batcheeprom")
		response = self._check_for_json(request)
		if response is not None:
			return response

		response = {}
		for eepromid in request.json:
			try:
				response[eepromid] = gpx.read_eeprom(eepromid)
			except ValueError:
				SELF._LOGGER.WARN("UNKNOWN EEPROM id %s" % eepromid)
			except gpx.UnknownFirmware:
				self._logger.warn("Unrecognized firmware flavor or version.")
				return make_response("Unrecognize firmware flavor or version", 400)
		self._logger.debug("response = %s" % flask.jsonify(response))
		return flask.jsonify(response)

	@octoprint.plugin.BlueprintPlugin.route("/puteeprombatch", methods=["POST"])
	def putbatcheeprom(self, *args, **kwargs):
		self._logger.info("putbatcheeprom")
		response = self._check_for_json(request)
		if response is not None:
			return response

		response = {}
		for eepromid in request.json:
			try:
				response[eepromid] = gpx.write_eeprom(eepromid, request.json[eepromid])
			except ValueError:
				self._logger.warn("Unknown EEPROM id %s" % eepromid)
		self._logger.debug("response = %s" % flask.jsonify(response))
		return flask.jsonify(response)

	@octoprint.plugin.BlueprintPlugin.route("/eeprom/<string:eepromid>", methods=["GET"])
	def eeprom(self, eepromid, *args, **kwargs):
		response = self.validate_eepromid(eepromid)
		if response is not None:
			return response
		try:
			value = gpx.read_eeprom(eepromid)
		except ValueError:
			return make_response("Unknown eeprom id: %s" % eepromid, 404)
		return flask.jsonify(value)

	@octoprint.plugin.BlueprintPlugin.route("/eeprom/<string:eepromid>", methods=["POST"])
	@admin_permission.require(403)
	def puteeprom(self, eepromid, *args, **kwargs):
		if not "Content-Type" in request.headers or not "application/json" in request.headers["Content-Type"]:
			return make_response("Expected content-type JSON", 400)
		try:
			value = request.json
		except BadRequest:
			return make_response("Malformed JSON body in request", 400)
		# TODO: set value
		return ('', 200)

def __plugin_load__():
	plugin = GPXPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {
			"octoprint.comm.transport.serial.factory": plugin.serial_factory,
			"octoprint.filemanager.extension_tree": plugin.get_extension_tree,
			"octoprint.plugin.softwareupdate.check_config": plugin.get_update_information,
			"octoprint.comm.protocol.gcode.queuing": plugin.rewrite_m73,
			"octoprint.comm.protocol.scripts": plugin.gcode_scripts
		}

__plugin_name__ = "GPX"
__plugin_pythoncompat__ = ">=2.7,<4"

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
