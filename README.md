rpi-dashboard-setup
===================

Automatically configure a stock Raspberry Pi to act as a dashboard.

### How to make a dashboard

#### Ingredients
- Raspberry Pi _Model B 512MB_
- Power adapter
- Ethernet cable
- HDMI monitor
- SD card _4GB or larger_

#### Instructions
1. Download the latest [Raspbian](http://www.raspberrypi.org/downloads/) operating system image.
2. Insert the SD card into the computer with the Raspbian image.
3. Install the OS image onto the SD card.
  - Windows: use [Win32DiskImager](http://sourceforge.net/projects/win32diskimager)
  - MacOS: [instructions](http://elinux.org/RPi_Easy_SD_Card_Setup#Flashing_the_SD_card_using_Mac_OSX)
  - Linux: [instructions](http://elinux.org/RPi_Easy_SD_Card_Setup#Flashing_the_SD_Card_using_Linux_.28including_on_a_Pi.21.29)
4. Connect the SD card, ethernet cable, power adapter, monitor, and optionally a USB keyboard to the Raspberry Pi.
5. After it finishes booting, log in to the Raspberry Pi with the default username `pi` and password `raspberry`. You may use SSH with the IP address printed above the login prompt.
6. Download `rpi-dashboard-setup`.
  - HTTP: `wget https://raw.githubusercontent.com/Aldaviva/rpi-dashboard-setup/master/rpi-dashboard-setup.py`
  - Git: `git clone https://github.com/Aldaviva/rpi-dashboard-setup.git && cd rpi-dashboard-setup`
7. `sudo python rpi-dashboard-setup.py`
8. Set the hostname at the prompt.
9. Set the screen orientation at the prompt (or hit Enter to use the default landscape orientation).
10. Enter passwords for the new admin account (with default username `ben`) and `dashboard` account. Skip through the prompts for Full Name, &c.
11. Wait for a while as packages are downloaded and installed.
12. `sudo reboot`
13. After the Raspberry Pi boots into the fullscreen Chromium interface, you can interact with it remotely using Panoptichrome. Log into your Panoptichrome admin interface and look for the new entry named after the Raspberry Pi's hostname.
