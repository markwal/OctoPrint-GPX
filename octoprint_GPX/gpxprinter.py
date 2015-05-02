# coding=utf-8
from __future__ import absolute_import
__author__ = "Mark Walker <markwal@hotmail.com> based on work by Gina Häußge" 
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import os
import logging
import time
import Queue

try:
	import gpx
except:
	pass

class GpxPrinter():
	def __init__(self, logger = None, settings = None, port = None, baudrate = None, timeout = 0):
		if logger is None:
			self._logger = logging.getLogger(__name__)
		else:
			self._logger = logger
		self._settings = settings
		if not gpx:
			self._logger.info("Unable to import gpx module")
			raise ValueError("Unable to import gpx module")
		self.port = port
		self.baudrate = self._baudrate = baudrate
		self.timeout = timeout
		self._logger.info("GPXPrinter created, port: %s, baudrate: %s" % (self.port, self.baudrate))
		self.outgoing = Queue.Queue()
		self.baudrateError = False;
		profile_folder = os.path.join(self._settings.global_get_basefolder("base"), "gpxProfiles")
		if not os.path.isdir(profile_folder):
			os.makedirs(profile_folder)
		profile_path = os.path.join(profile_folder, "gpx.ini")
		log_path = os.path.join(self._settings.global_get_basefolder("logs"), "gpx.log")
		try:
			self._append(gpx.connect(port, baudrate, profile_path, log_path,
				self._logger.getEffectiveLevel() == logging.DEBUG))
		except Exception as e:
			self._logger.info("gpx.connect raised exception = %s" % e)
			raise

	def _append(self, s):
		if (s != ''):
			for item in s.split('\n'):
				self.outgoing.put(item)

	def write(self, data):
		data = data.strip()
		self._logger.debug("%s" % data)
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
				pass
				return
		while True:
			try:
				self._append(gpx.write("%s" % data))
				break
			except gpx.BufferOverflow:
				self._append("wait")
				pass

	def readline(self):
		while (self.baudrateError):
			if (self._baudrate != self.baudrate):
				self.write("M105")
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
		if 'wait' in s:
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
			pass
		return ''

	def close(self):
		gpx.disconnect()
		return
