# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.events import Events

class GPXPlugin(
		octoprint.plugin.TemplatePlugin,
		octoprint.plugin.SettingsPlugin,
		octoprint.plugin.EventHandlerPlugin
		):
	def serial_factory(self, comm, port, baudrate, timeout, *args, **kwargs):
		if self._settings.get(["protocol"]) != "GPX" or port == 'VIRTUAL':
			return None

		self._logger.info("Connecting through x3g.")
		try:
			if port is None or port == 'AUTO' or baudrate is None or baudrate == 0:
				raise IOError("AUTO port and baudrate not currently supported by GPX")
			from .gpxprinter import GpxPrinter
			self.printer = GpxPrinter(self._logger, port, baudrate, timeout)
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
		return dict(protocol="GPX")

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False)
		]

	def on_event(self, event, payload):
		if event == Events.PRINT_CANCELLED:
			self._logger.info("Got print cancelled event");
			if self.printer:
				# jump the queue with an abort
				self._logger.info("Sending in an M112");
				self.printer.write("M112");
				self._logger.info("Sent");

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
