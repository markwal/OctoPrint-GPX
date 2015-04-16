# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class GPXPlugin(octoprint.plugin.TemplatePlugin, octoprint.plugin.SettingsPlugin):
	def serial_factory(self, comm, port, baudrate, timeout):
		if self._settings.get(["protocol"]) != "GPX":
			return None

		self._logger.info("Connecting through x3g.")
		try:
			if port is None or port == 'AUTO' or baudrate is None or baudrate == 0:
				raise IOError("AUTO port and baudrate not currently supported by GPX")
			from .gpxprinter import GpxPrinter
			return GpxPrinter(port, baudrate, timeout)
		except Exception as e:
			self._logger.info("Failed to connect to x3g e = %s." % e);
			raise

	def get_extension_tree(self):
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


__plugin_implementation__ = GPXPlugin()


def __plugin_load__():
	plugin = GPXPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {
			"octoprint.comm.transport.serial.factory": plugin.serial_factory,
			"octoprint.filemanager.extension_tree": plugin.get_extension_tree
		}
