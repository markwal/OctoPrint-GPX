# coding=utf-8
from __future__ import absolute_import
__author__ = "Mark Walker <markwal@hotmail.com> based on work by Gina Häußge" 
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import os
import logging
import time
try:
	import queue
except ImportError:
	import Queue as queue
import re
import datetime

from octoprint.filemanager import FileDestinations

gpx = False
try:
	import gcodex3g as gpx
except:
	pass

class GpxPrinter():
	def __init__(self, gpx_plugin, port = None, baudrate = None, timeout = 0):
		self._logger = gpx_plugin._logger
		self._settings = gpx_plugin._settings
		self._printer = gpx_plugin._printer
		self._bot_cancelled = False
		if gpx is None:
			self._logger.warn("Unable to import gpx module")
			raise ValueError("Unable to import gpx module")
		self.port = port
		self.baudrate = self._baudrate = baudrate
		self.timeout = timeout
		self._logger.info("GPXPrinter created, port: %s, baudrate: %s" % (self.port, self.baudrate))
		self.outgoing = queue.Queue()
		self.baudrateError = False;
		data_folder = gpx_plugin.get_plugin_data_folder()
		self.profile_path = os.path.join(data_folder, "gpx.ini")
		log_path = self._settings.get_plugin_logfile_path()
		self._regex_linenumber = re.compile("N(\d+)")
		try:
			self._logger.debug("Calling gpx.connect")
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

	def _bot_reports_build_cancelled(self):
		# sometimes the bot tells us the build is cancelled because it wants us
		# to stop sending commands (user cancelled from LCD, something bad
		# happend, etc.) but sometimes, it is just reporting that it complied
		# with our request to stop. To avoid looping endlessly we only take action
		# if there is something for us to stop.
		if self._printer.is_printing():
			currentOrigin = None
			currentJob = self._printer.get_current_job()
			if currentJob is not None and "file" in currentJob.keys():
				currentJobFile = currentJob["file"]
				if "origin" in currentJobFile.keys():
					currentOrigin = currentJobFile["origin"]
			if currentOrigin != FileDestinations.SDCARD:
				self._bot_cancelled = True
				self._printer.cancel_print()

	def clear_bot_cancelled(self):
		# called when a new print is started. We'll just assume the user knows
		# what they're doing and the cancel has completed.
		self._bot_cancelled = False

	def progress(self, percent):
		# we don't want the progress event to pre-empt the build start or
        # override the build end notification and the M73 causes a build start
        # if we aren't already running one
		if gpx.build_started():
			try:
				# loop sending for a while if the queue isn't full or if the bot
				# isn't listening
				for i in range(0, 10):
					try:
						gpx.write("M73 P%d" % percent)
						break
					except gpx.BufferOverflow:
						time.sleep(0.01)
					except gpx.Timeout:
						time.sleep(0.1)
			except gpx.CancelBuild:
				self._bot_reports_build_cancelled()

	def _append(self, s):
		if (s != ''):
			for item in s.split('\n'):
				self.outgoing.put(item)

	def write(self, data):
		try:
			rval = len(data)
			data = data.strip()
			str_data = data
			if not isinstance(str_data, str):
				str_data = data.decode('utf-8')
			if (self.baudrate != self._baudrate):
				try:
					self._baudrate = self.baudrate
					self._logger.info("new baudrate = %d" % self.baudrate)
					gpx.set_baudrate(self.baudrate)
					self.baudrateError = False
				except ValueError:
					self.baudrateError = True
					self.outgoing.put('')
					return 0

			# look for a line number
			# line number means OctoPrint is streaming gcode at us (gpx.ini flavor)
			# no line number means OctoPrint is generating the gcode (reprap flavor)
			match = self._regex_linenumber.match(str_data)

			# try to talk to the bot
			try:
				if match is None:
					reprapSave = gpx.reprap_flavor(True)

				# loop sending until the queue isn't full
				timeout_retries = 0
				bo_retries = 0
				while True:
					try:
						self._append(gpx.write(data))
						break
					except gpx.BufferOverflow:
						bo_retries += 1
						try:
							if gpx.build_paused():
								if bo_retries == 1:
									self._append("// echo: print paused at bot")
								time.sleep(1) # 1 sec
						except IOError:
							pass
						time.sleep(0.1) # 100 ms
					except gpx.Timeout:
						time.sleep(1)
						timeout_retries += 1
						if (timeout_retries >= 5):
							raise

			finally:
				if match is None:
					gpx.reprap_flavor(reprapSave)
		except gpx.CancelBuild:
			self._bot_reports_build_cancelled()
		return rval

	def readline_str(self):
		try:
			if (self.baudrateError):
				if (self._baudrate != self.baudrate):
					gpx.write("M105")
				return ''

			try:
				return self.outgoing.get_nowait()
			except queue.Empty:
				pass

			if gpx.listing_files():
				return gpx.readnext()

			while True:
				timeout = 2 if gpx.waiting else self.timeout
				try:
					return self.outgoing.get(timeout=timeout)
				except queue.Empty:
					self._append(gpx.readnext())

		except gpx.CancelBuild:
			self._bot_reports_build_cancelled()
			return '// echo: build cancelled'

	def readline(self):
		return self.readline_str().encode('ascii', errors='ignore')

	def cancel(self):
		self._logger.warn("Cancelling build %s", "by the printer" if self._bot_cancelled else "by OctoPrint")
		self._bot_cancelled = False;

	def close(self):
		gpx.disconnect()
		return
