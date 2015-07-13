# coding=utf-8
from __future__ import absolute_import
__author__ = "Mark Walker <markwal@hotmail.com> based on work by Gina Häußge" 
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import os
import logging
import time
import Queue
import re

try:
	import gpx
except:
	pass

class GpxPrinter():
	def __init__(self, gpx_plugin, port = None, baudrate = None, timeout = 0):
		self._logger = gpx_plugin._logger
		self._settings = gpx_plugin._settings
		self._printer = gpx_plugin._printer
		if not gpx:
			self._logger.info("Unable to import gpx module")
			raise ValueError("Unable to import gpx module")
		self.port = port
		self.baudrate = self._baudrate = baudrate
		self.timeout = timeout
		self._logger.info("GPXPrinter created, port: %s, baudrate: %s" % (self.port, self.baudrate))
		self.outgoing = Queue.Queue()
		self.baudrateError = False;
		data_folder = gpx_plugin.get_plugin_data_folder()
		self.profile_path = os.path.join(data_folder, "gpx.ini")
		log_path = self._settings.get_plugin_logfile_path()
		self._regex_linenumber = re.compile("N(\d+)")
		try:
			self._logger.info("Calling gpx.connect")
			self._append(gpx.connect(port, baudrate, self.profile_path, log_path,
				self._settings.get_boolean(["verbose"])))
			time.sleep(float(self._settings.get(["connection_pause"])))
			self._append(gpx.start())
			self._logger.info("gpx.connect succeeded")
		except Exception as e:
			self._logger.info("gpx.connect raised exception = %s" % e)
			raise

	def refresh_ini(self):
		if not self._printer.is_printing() and not self._printer.is_paused():
			gpx.reset_ini()
			gpx.read_ini(self.profile_path)

	def progress(self, percent):
		gpx.write("M73 P%d" % percent)

	def _append(self, s):
		if (s != ''):
			for item in s.split('\n'):
				self.outgoing.put(item)

	def write(self, data):
		data = data.strip()
		# strip checksum
		if "*" in data:
			data = data[:data.rfind("*")]
		if (self.baudrate != self._baudrate):
			try:
				self._baudrate = self.baudrate
				self._logger.info("new baudrate = %d" % self.baudrate)
				gpx.set_baudrate(self.baudrate)
				self.baudrateError = False
			except ValueError:
				self.baudrateError = True
				self.outgoing.put('')
				return

		# look for a line number
		# line number means OctoPrint is streaming gcode at us (gpx.ini flavor)
		# no line number means OctoPrint is generating the gcode (reprap flavor)
		match = self._regex_linenumber.match(data)
		if match is not None:
			lineno = int(match.group(1))
			if lineno == 1:
				currentJob = self._printer.get_current_job()
				if currentJob is not None and "file" in currentJob.keys() and "name" in currentJob["file"]:
					build_name = os.path.splitext(os.path.basename(currentJob["file"]["name"]))[0]
					gpx.write("(@build %s)" % build_name)
					gpx.write("M136 (%s)" % build_name)
				else:
					gpx.write("M136")

		# try to talk to the bot
		try:
			if match is None:
				reprapSave = gpx.reprap_flavor(True)

			# loop sending until the queue isn't full
			while True:
				try:
					self._append(gpx.write("%s" % data))
					break
				except gpx.BufferOverflow:
					time.sleep(0.1)

		finally:
			if match is None:
				gpx.reprap_flavor(reprapSave)

	def readline(self):
		while (self.baudrateError):
			if (self._baudrate != self.baudrate):
				gpx.write("M105")
			return ''
		try:
			s = self.outgoing.get_nowait()
			self._logger.debug("readline: %s" % s)
			return s
		except Queue.Empty:
			pass
		s = gpx.readnext()
		timeout = self.timeout
		append_later = None
		if gpx.waiting():
			append_later = s
			timeout = 2
		else:
			self._append(s)
		try:
			s = self.outgoing.get(timeout=timeout)
			self._logger.debug("readline: %s" % s)
			return s
		except Queue.Empty:
			if append_later is not None:
				self._append(append_later)
			self._logger.debug("timeout")
		return ''

	def cancel(self):
		if self._settings.get_boolean(['extended_stop_instead_of_abort']):
			# make sure if you use this you have your own "gcode on cancel"
			# that turns off motors and heaters
			gpx.stop()
		else:
			gpx.abort()

	def close(self):
		gpx.disconnect()
		return
