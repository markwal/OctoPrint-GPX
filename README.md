# OctoPrint-GPX
An OctoPrint plugin for MakerBot (prior to 5th gen) and clones.

It uses GPX to translate gcode to x3g underneath OctoPrint in the communications
layer.

[GPX](https://github.com/whpthomas/GPX) is a *G*code *P*ostprocessing to *X*3g
tool written by [WHPThomas](https://github.com/whpthomas). Gcode is a language
for describing toolpaths in 3d printers which is derived from the gcode used in
CNC machines.  X3g is an extension to the s3g protocol which was named for the
Sanguino v3 which was in use at the time as the bot's controller.

## Caveats
I've only tested this on one config:
Raspberry Pi set up via the OctoPi image
FlashForge Creator Pro running Sailfish 7.7

## Installing
1. Start with OctoPi: Get your Raspberry Pi up and running by following the
   instructions on [OctoPi](https://octopi.octoprint.org)

2. Get the GPX plugin. You get plugins by using the Plugin Manager in OctoPrint.

    * Open a browser to octoprint (http://ipaddress/) and login
    * Choose "Settings" from the top bar
    * Click "Plugin Manager" on the left side
    * Click the "Get More..." button
    * Find GPX in the list and click "Install"
    * Restart octoprint (if you're using OctoPi: System.Restart from the menu bar)
    * Refresh your browser

3. Set and save the GPX settings.

    * OctoPrint-\>Settings-\>GPX
    * Pick your machine type: *Replicator 1 Dual* (if you have a clone, it's
      most likely a Rep 1 clone even if it was sold as a Rep 2 clone)
    * Set the gcode flavor to "RepRap" and your slicer too. The only reason to
      use MakerBot flavor is if you are using a MakerBot slicer.

4. Try connecting

    Choose a port and baudrate.  I don't have AUTO working yet.  115200 works
    on my bot.

5. Upload gcode from your slicer to OctoPrint.

    OctoPrint only understands ".gcode" and then GPX translates it to x3g.
    Don't upload x3g to OctoPrint. That won't work.

    On the other hand, only use ".x3g" with the printer's SD card. It doesn't
    understand gcode and GPX running in OctoPrint can't help the firmware with
    it directly on the SD card.

## Known issues
* Upload to SD doesn't work. It can't work directly because SailFish removed
  that feature to save bytes. Probably a good call since who wants to wait for
  115200 baud when you can just plug the SD card into your PC.
  [Google Groups Post](https://groups.google.com/d/msg/jetty-firmware/KCIfkv02MPY/SX17OBhXoJMJ)
  I'm working on FlashAir support
* Can't delete SD files for a similar reason
* For prints that have small segments that don't require full stops to move to
  the next one (ie cylinder with a smooth surface), you'll be happier printing
  off of the printer's SD card. Printing over serial peaks out at about 60
  segments per second.
* Upload to OctoPrint and then print works with .gcode, not with .x3g. The GPX
  layer converts the gcode to x3g when you print from OctoPrint.  I need to
  figure out a way to make the UI more graceful about this. To review: If the
  destination is OctoPrint and let it drive: .gcode.  If the destination is the
  SD card and let the bot drive the print: .x3g.
  
## Plan

I was thinking for my next project, possibly, to start an OctoPrint plug-in
that will talk to the FlashAir SD card directly bypassing the motherboard on
the the bot.

The GCode viewer can't follow along the build on the SD card because it doesn't
have a good way to understand where the bot is in printing an x3g file.  I'm
thinking about this one.  Perhaps we can use the number of commands processed to
line something up. I have the printer reporting current position back to
OctoPrint every second or so now, so theoretically it could follow along-ish on
z-change, but it'd be guessing about the pacing in between. It'd require a new
hook or something in OctoPrint.
