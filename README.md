# OctoPrint-GPX
An OctoPrint plug-in to use GPX as the protocol layer underneath rather than
replacing g-code to talk to s3g/x3g machines, for example, a FlashForge.

This plugin as it is now written requires brand new hooks that are just barely
in OctoPrint's devel branch, so you'll need to run from source on the bleeding
edge until that makes it into an official release

## Caveats
I've only tested this on one config:
Raspberry Pi set up via the OctoPi image
FlashForge Creator Pro running Sailfish 7.7

## Installing
1. Start with OctoPi: Get your Raspberry Pi up and running by following the
   instructions on [OctoPi](https://github.com/guysoft/OctoPi)

2. OctoPi runs OctoPrint in a virtualenv. You'll want to switch to the
   virtualenv for installing packages so they'll be available to OctoPrint.
   Activating the environment means that when you type python or pip, it'll use
   the ones out of ~/oprint/bin and use ~/oprint/lib for all package installs
   and dependencies.  You can tell it is working by the "(oprint)" in front of
   your prompt
    ```
    source ~/oprint/bin/activate
    ```

3. Switch to the devel branch of OctoPrint
  (https://github.com/foosel/OctoPrint/wiki/FAQ#how-can-i-switch-the-branch-of-the-octoprint-installation-on-my-octopi-image)
    ```
    cd ~/OctoPrint
    git pull & git checkout devel
    python setup.py clean
    python setup.py install
    sudo service octoprint restart
    ```

4. Get the GPX plugin. You get plugins by using the Plugin Manager in OctoPrint.

    a. Open a browser to octoprint (http://ipaddress/) and login
    b. Choose "Settings" from the top bar
    c. Click "Plugin Manager" on the left side
    d. Click the "Get More..." button
    e. Find GPX in the list and click "Install"
    f. Restart octoprint (octopi puts a command on the "System" menu)
    g. Refresh your browser

5. Set some settings.

    a. Like step 4, get to Settings
    b. Click "GPX" on the left nav
    c. Choose your printer type and gcode flavor, leave the rest on default

6. Try connecting
    Choose a port and baudrate.  I don't have AUTO working yet.  115200 works
    on my bot.

## Known issues
* Upload to SD doesn't work. It can't work directly because SailFish removed
  that feature to save bytes. Probably a good call since who wants to wait for
  115200 baud when you can just plug the SD card into your PC.
  (Google Groups Post)[https://groups.google.com/d/msg/jetty-firmware/KCIfkv02MPY/SX17OBhXoJMJ]
  I'm working on FlashAir support
* Can't delete SD files for a similar reason
* OctoPrint gets confused sometimes when using the LCD panel to make changes,
  we'll work on making it more robust
* Octoprint expects the g-code to be Reprap style.  I haven't run across all of
  the difficulties with this.
* I really wouldn't recommend printing directly from the gcode file rather than
  an x3g on the SD card.  Besides Sailfish recommends against anything but SD,
  there's also the fact that this is fairly Alpha code and you wouldn't want a
  communications glitch to ruin your print several hours in. And I expect one.
  More than likely pretty quickly, but worst case, just before the build is
  done. (Although I have successfully printed a Linkling directly from OctoPrint
  just as a test.)
* Upload to OctoPrint and then print works with .gcode, not with .x3g. The GPX
  layer converts the gcode to x3g when you print from OctoPrint.  I need to
  figure out a way to make the UI more graceful about this. To review: If the
  destination is OctoPrint and let it drive: .gcode.  If the destination is the
  SD card and let the bot drive the print: .x3g.
* Oh yeah, at the moment, its pretty piggy with the log file.  Default location
  is ~/.octoprint/logs/gpx.log.  You might want to delete that from time to
  time.
  
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
