# coding=utf-8
from __future__ import absolute_import
__author__ = "Mark Walker <markwal@hotmail.com> based on work by Gina Häußge" 
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

import logging
import time
import Queue

from octoprint.settings import settings

gpxAvailable = False
try:
	import gpx
	gpxAvailable = True
except:
	pass

class GpxPrinter():
	def __init__(self, port = None, baudrate = None, timeout = 0):
		self._logger = logging.getLogger(__name__)
		if not gpxAvailable:
			self._logger.info("Unable to import gpx module")
			raise ValueError("Unable to import gpx module")
		if baudrate == 0:
			raise IOError("AUTO baudrate not currently supported by GPX")
		self.port = port
		self.baudrate = self._baudrate = baudrate
		self.timeout = timeout
		self._logger.info("GPXPrinter created, port: %s, baudrate: %s" % (self.port, self.baudrate))
		self.outgoing = Queue.Queue()
		self.baudrateError = False;
		try:
			self._append(gpx.connect(port, baudrate, settings().getBaseFolder("plugins") + "/gpx.ini")) #, settings().getBaseFolder("logs") + "/gpx.log")
		except Exception as e:
			self._logger.info("gpx.connect raised exception = %s" % e)
			raise

	def _append(self, s):
		if (s != ''):
			for item in s.split('\n'):
				self.outgoing.put(item)

	def write(self, data):
		data = data.strip()
		self._logger.info("%s" % data)
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
			self._logger.info("readline: %s" % s)
			return s
		except Queue.Empty:
			pass
		self._append(gpx.readnext())
		try:
			s = self.outgoing.get(timeout=self.timeout)
			self._logger.info("readline: %s" % s)
			return s
		except Queue.Empty:
			self._logger.info("timeout")
			pass
		return ''

	def close(self):
		gpx.disconnect()
		return
