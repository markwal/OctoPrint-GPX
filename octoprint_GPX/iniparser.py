# coding=utf-8
from __future__ import absolute_import
__author__ = "Mark Walker <markwal@hotmail.com> based on work by Gina Häußge" 
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'

from collections import OrderedDict
import re
import os

class IniParser():
	def __init__(self, filename, logger):
		self.lines = []
		self.counter = 0;
		self.ini = {}
		self.idx = OrderedDict()
		self.filename = filename
		self._logger = logger
		self._regex_section = re.compile("\[(.+)\]")
		self._regex_name_value = re.compile("([^=;]+?)=(\s*)(.+?)(\s*)(;.+)?$")

	def read(self):
		self.ini = ini = {}
		self.idx = idx = OrderedDict()
		self.lines = lines = []
		self.counter = 0
		sectionname = None
		ini[sectionname] = {}
		idx[sectionname] = OrderedDict()
		with open(self.filename) as inifile:
			for line in inifile:
				line = line.strip()
				lines.append(line);
				m = self._regex_section.match(line)
				if m:
					sectionname = m.group(1)
					ini[sectionname] = {}
					idx[sectionname] = OrderedDict()
				else:
					m = self._regex_name_value.match(line)
					if m:
						itemname = m.group(1).strip()
						if not itemname == 'None':
							ini[sectionname][m.group(1).strip()] = m.group(3)
							idx[sectionname][m.group(1).strip()] = line
					else:
						self.counter += 1
						idx[sectionname][self.counter] = line

#		config = ConfigParser.SafeConfigParser()
#		config.read(foo)
#		ini = {}
#		for section in config.sections():
#			ini[section] = {}
#			for (name, value) in config.items(section):
#				ini[section][name] = value
		return ini

	def update(self, ini):
		if not ini.items:
			raise ValueError("Malformed update")
		for sectionname, section in ini.items():
			if not section.items:
				raise ValueError("Invalid section")
			for option, value in section.items():
				self._logger.info("option, value: %s, %s" % (option, repr(value)))
				if ("%s" % value) in ["True", "False"]:
					value = 1 if value else 0
				if option == "machine_type" and (value == "" or value == "undefined" or value == "None"):
					value = "r2"
				if sectionname not in self.ini:
					self.ini[sectionname] = {}
				self.ini[sectionname][option] = value
				if sectionname not in self.idx:
					self.idx[sectionname] = OrderedDict()
				line = self.idx[sectionname].get(option)
				if value == '' or value == 'undefined' or value == 'None':
					# means delete
					if line is not None:
						del self.idx[sectionname][option]
					continue
				if line is not None:
					m = self._regex_name_value.match(line)
					if m:
						g = m.groups("")
						g = g[0:2] + (value,) + g[3:]
						self.idx[sectionname][option] = "%s=%s%s%s%s" % g
						continue
				section = self.idx[sectionname]
				blanks = 0
				if len(section) > 0:
					while section[next(reversed(section))].strip() == '':
						section.popitem()
						blanks += 1
				self.counter += 1
				section[self.counter] = "%s=%s" % (option, value)
				for i in range(0, blanks):
					self.counter += 1
					section[self.counter] = ""

	def _write_section(self, inifile, section):
		count = 0
		for option, line in section.items():
			inifile.write(line)
			count += 1
			inifile.write("\n")
		return count


	def write(self):
		self._logger.info("Open %s" % self.filename)
		with open(self.filename, 'wb') as inifile:
			self._logger.info("Write %s" % self.filename)
			count = 0
			if None in self.idx:
				count += self._write_section(inifile, self.idx[None])
			for sectionname, section in self.idx.items():
				if sectionname is not None:
					inifile.write("[%s]\n" % sectionname)
					count += self._write_section(inifile, section)
		if count == 0:
			self._logger.info("For %s, all sections empty, removing file.", self.filename)
			os.remove(self.filename)

	def dump(self):
		for sectionname, section in self.idx.items():
			if sectionname is not None:
				print "[%s]" % sectionname
			for option, line in section.items():
				print line

	def get(self, sectionname, itemname):
		if sectionname in self.ini and itemname in self.ini[sectionname]:
			return self.ini[sectionname][itemname]
		return None

#		config = ConfigParser.SafeConfigParser()
#		for name, section in ini.items() :
#			if not config.has_section(name):
#				config.add_section(name)
#			for option, value in section.items():
#				config.set(name, option, value)
#		with open(settings().getBaseFolder("plugins") + "/gpx.ini", 'wb') as configfile:
#			config.write(configfile)
