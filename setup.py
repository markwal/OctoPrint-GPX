# coding=utf-8
import setuptools

########################################################################################################################

plugin_identifier = "GPX"
plugin_package = "octoprint_%s" % plugin_identifier
plugin_name = "OctoPrint-GPX"
plugin_version = "0.1"
plugin_description = "Emulates the gcode printer protocol by translating to/from x3g."
plugin_author = "Mark Walker"
plugin_author_email = "markwal@hotmail.com"
plugin_url = "http://github.com/markwal/OctoPrint-GPX"
plugin_license = "AGPLv3"

plugin_additional_data = []

########################################################################################################################

def package_data_dirs(source, sub_folders):
	import os
	dirs = []

	for d in sub_folders:
		folder = os.path.join(source, d)
		if not os.path.exists(folder):
			continue

		for dirname, _, files in os.walk(folder):
			dirname = os.path.relpath(dirname, source)
			for f in files:
				dirs.append(os.path.join(dirname, f))

	return dirs

def requirements(filename):
	return filter(lambda line: line and not line.startswith("#"), map(lambda line: line.strip(), open(filename).read().split("\n")))

def params():
	# Our metadata, as defined above
	name = plugin_name
	version = plugin_version
	description = plugin_description
	author = plugin_author
	author_email = plugin_author_email
	url = plugin_url
	license = plugin_license

	# we only have our plugin package to install
	packages = [plugin_package]

	# we might have additional data files in sub folders that need to be installed too
	package_data = {plugin_package: package_data_dirs(plugin_package, ['static', 'templates', 'translations'] + plugin_additional_data)}
	include_package_data = True

	# If you have any package data that needs to be accessible on the file system, such as templates or static assets
	# this plugin is not zip_safe.
	zip_safe = False

	# Read the requirements from our requirements.txt file
	install_requires = requirements("requirements.txt")

	# Hook the plugin into the "octoprint.plugin" entry point, mapping the plugin_identifier to the plugin_package.
	# That way OctoPrint will be able to find the plugin and load it.
	entry_points = {
		"octoprint.plugin": ["%s = %s" % (plugin_identifier, plugin_package)]
	}

	ext_modules = [
		setuptools.Extension('gpx',
		sources = [
			'GPX/src/pymodule/gpxmodule.c',
			'GPX/src/shared/config.c',
			'GPX/src/shared/opt.c',
			'GPX/src/gpx/gpx.c',
			'GPX/src/gpx/gpx-main.c',
			],
		extra_compile_args = ['-DSERIAL_SUPPORT', '-fvisibility=hidden', '-IGPX/src/shared', '-IGPX/src/gpx'],
		extra_link_args = ['-fvisibility=hidden'])
		]

	return locals()

setuptools.setup(**params())
