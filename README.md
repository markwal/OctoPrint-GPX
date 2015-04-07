# OctoPrint-GPX
An OctoPrint plug-in to use GPX as the protocol layer underneath rather than replacing g-code to talk to s3g/x3g machines, for example, a FlashForge.

This plugin as it is now written requires hooks that are not in OctoPrint as well as changes to GPX to do two way communication.  So if you'd like to try it out, you'll need to use my forks of both.  Not for the faint of heart.  And it's not done yet.  More information coming later.

BTW, I understand foosel not wanting to support MakerBot.  I just got into 3d printing recently and was unaware of the back story before I bought my FlashForge, but now that I have a MakerBot clone, I'd really like it to work with OctoPrint, so hopefully it won't be too much support for MakerBot since it won't possibly work with their newest stuff (Gen 5).  See: https://github.com/foosel/OctoPrint/wiki/FAQ#does-octoprint-support-makerbot-or-flashforge-printers

## Caveats
I've only tested this on one config:
Raspberry Pi set up via the OctoPi image
FlashForge Creator Pro running Sailfish 7.7

## Installing
* Start with OctoPi: Get your Raspberry Pi up and running by following the instructions on [OctoPi](https://github.com/guysoft/OctoPi)
* Switch to my fork of OctoPrint.
```
cd ~
sudo service octoprint stop
mv OctoPrint OctoPrintSave
git clone -b devel https://github.com/markwal/OctoPrint
cd OctoPrint
~/oprint/bin/python setup.py clean
~/oprint/bin/python setup.py install
```
You may want to test that it still works at this point.  Well, works in that the web page renders.  You won't be able to connect to your x3g printer yet.  To make sure OctoPrint runs:
```
source ~/oprint/bin/activate
octoprint
```
*\<Ctrl-C\>* kills it

* Get the GPX module
```
cd ~
git clone https://github.com/markwal/OctoPrint-GPX
git submodule update --init
~/oprint/bin/python setup.py install
```
* Run OctoPrint
```
sudo service octoprint start
```
* Turn on the GPX plug in
From the octoprint UI: choose settings from the navbar at the top, then GPX from the bottom left, then switch from G-Code to GPX in the protocol, hit save.

* Try connecting
Choose a baudrate.  I don't have AUTO working yet.  115200 works on my bot, but you might want to try slower?

## Known issues
Upload to SD doesn't work.  It can't work directly because SailFish removed that feature to save bytes.  Probably a good call since who wants to wait for 115200 baud when you can just plug the SD card into your PC.  I was thinking for my next project, possible, to start an OctoPrint plug-in that will talk to the FlashAir SD card directly bypassing the motherboard on the the bot.
The GCode viewer can't follow along the build because it doesn't have a good way to understand where the bot is in printing an x3g file.  I'm thinking about this one.  Perhaps we can use the number of commands processed to line something up.
Octoprint expects the g-code to be Reprap style.  I haven't run accross all of the difficulties with this, but one is that when it runs across M109 it jumps to the wrong conclusion about what's going to happen next.
I really wouldn't recommend printing directly from the gcode file rather than an x3g on the SD card.  Besides Sailfish recommends against anything but SD, there's also the fact that this is fairly Alpha code and you wouldn't want a communications glitch to ruin your print several hours in. And I expect one.  More than likely pretty quickly, but worst case, just before the build is done. 

