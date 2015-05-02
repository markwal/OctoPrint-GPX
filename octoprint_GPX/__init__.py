# coding=utf-8
from __future__ import absolute_import

import os
import re
from collections import OrderedDict

import flask
from flask import request, make_response
from flask.exceptions import BadRequest

import octoprint.plugin
from octoprint.events import Events

try:
	import gpx
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
		octoprint.plugin.BlueprintPlugin
		):
	def on_after_startup(self):
		from .iniparser import IniParser
		profile_folder = os.path.join(self._settings.global_get_basefolder("base"), "gpxProfiles")
		if not os.path.isdir(profile_folder):
			os.makedirs(profile_folder)
		profile_path = os.path.join(profile_folder, "gpx.ini")
		self.iniparser = IniParser(profile_path, self._logger)

	def serial_factory(self, comm, port, baudrate, timeout, *args, **kwargs):
		if self._settings.getBoolean(["enabled"]) or port == 'VIRTUAL':
			return None

		self._logger.info("Connecting through x3g.")
		try:
			if port is None or port == 'AUTO' or baudrate is None or baudrate == 0:
				raise IOError("AUTO port and baudrate not currently supported by GPX")
			from .gpxprinter import GpxPrinter
			self.printer = GpxPrinter(self._logger, self._settings, port, baudrate, timeout)
			return self.printer
		except Exception as e:
			self._logger.info("Failed to connect to x3g e = %s." % e);
			raise

	def get_extension_tree(self, *args, **kwargs):
		return dict(
			machinecode=dict(
				x3g=["x3g", "s3g"]
			)
		)
		
	def get_settings_defaults(self):
		return dict(enabled=True)

	def on_event(self, event, payload):
		if event == Events.PRINT_CANCELLED:
			if self.printer:
				# jump the queue with an abort
				self.printer.write("M112");

	def get_assets(self):
		return dict(
			js=["js/gpx.js"],
			css=["css/gpx.css"],
			less=["less/gpx.less"]
		)

	def fetch_machine_ini(self, machineid):
		profile_folder = os.path.join(self._settings.global_get_basefolder("base"), "gpxProfiles")
		profile_path = os.path.join(profile_folder, machineid + ".ini")
		from .iniparser import IniParser
		machine_ini = IniParser(profile_path, self._logger)
		if os.path.isdir(profile_folder) and os.path.exists(profile_path) and os.path.isfile(profile_path):
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

	@octoprint.plugin.BlueprintPlugin.route("/machine/<string:machineid>", methods=["GET"])
	def machine(self, machineid):
		response = self.validate_machineid(machineid)
		if response is not None:
			return response
		return flask.jsonify(self.ini_massage_out(self.fetch_machine(machineid)))

	@octoprint.plugin.BlueprintPlugin.route("/machine/<string:machineid>", methods=["POST"])
	def putmachine(self, machineid):
		response = self.validate_machineid(machineid)
		if response is not None:
			return response
		machine_ini = self.fetch_machine_ini(machineid)
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
						if t == float:
							value = float(value)
						elif t == int:
							value = int(value)
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
	def ini(self):
		try:
			ini = self.iniparser.read()
		except IOError:
			self._logger.info("Unable to read %s, using defaults." % self.iniparser.filename)
			ini = OrderedDict()
			ini["printer"] = OrderedDict()
			ini["printer"]["machine_type"] = "r2"
		return flask.jsonify(self.ini_massage_out(ini))

	@octoprint.plugin.BlueprintPlugin.route("/ini", methods=["POST"])
	def putini(self):
		self._logger.info("putini")
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


def __plugin_load__():
	plugin = GPXPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {
			"octoprint.comm.transport.serial.factory": plugin.serial_factory,
			"octoprint.filemanager.extension_tree": plugin.get_extension_tree
		}

__plugin_name__ = "GPX"
