# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class GPXPlugin(octoprint.plugin.TemplatePlugin, octoprint.plugin.SettingsPlugin):
	def serial_handler(self, comm, port, baudrate, timeout):
		if self._settings.get(["protocol"]) != "GPX":
			return None

		self._logger.info("Connecting through x3g.")
		try:
			if port is None or port == 'AUTO':
				port = comm.detectPort(True)
				if port is None:
					return None
			self._logger.info("calling constructor %s %ld" % (port, baudrate))
			from .gpxprinter import GpxPrinter
			return GpxPrinter(port, baudrate, timeout)
		except Exception as e:
			self._logger.info("Failed to connect to x3g e = %s." % e);
			raise
		
	def on_after_startup(self):
		self._logger.info("GPXPlugin startup!")

	def get_settings_defaults(self):
		return dict(protocol="GPX")

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False)
		]


__plugin_implementation__ = GPXPlugin()


def __plugin_init__():
	plugin = GPXPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {"octoprint.comm.protocol.serial": plugin.serial_handler}
