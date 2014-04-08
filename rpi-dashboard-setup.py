#!/usr/bin/env python

import pwd
import errno
import argparse
import fileinput
import logging
import os
import sqlite3
import subprocess
import urllib

logging.basicConfig(level=logging.DEBUG)

ADMIN_USERNAME               = "ben"
CHROMIUM_PROFILE_URL         = "http://skadi.bluejeansnet.com/rpi-dashboard/chromium-profile.tar.gz"
DASHBOARD_USERNAME           = "dashboard"
LOCALE                       = "en_US.UTF-8"
PANOPTICHROME_EXTENSION_ID   = "jmjpnaplgnfnnlfofkbpogokimpjocmg"
PANOPTICHROME_SERVER_ADDRESS = "skadi.bluejeansnet.com:8081"
TIMEZONE                     = "US/Pacific-New"

parser = argparse.ArgumentParser(description='Set up a Raspberry Pi to act as a dashboard', usage='sudo python rpi-dashboard-setup.py')
parser.add_argument('--skip-packages', action='store_true', help='skip downloading and installation of apt packages')
args = parser.parse_args()

def create_admin_user():
    log("Creating admin user "+ADMIN_USERNAME+"...")
    admin_user_exists = 0 == subprocess.call(["id", ADMIN_USERNAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if admin_user_exists:
        logging.warn(ADMIN_USERNAME + " already exists, leaving user and groups alone.")
    else:
        subprocess.check_call(["adduser", "--quiet", ADMIN_USERNAME])
        subprocess.check_call(["usermod", "-a", "-G", "sudo", ADMIN_USERNAME])
        create_admin_ssh()

def create_dashboard_user():
    log("Creating dashboard user...")
    dashboard_user_exists = 0 == subprocess.call(["id", DASHBOARD_USERNAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dashboard_user_exists:
        logging.warn(DASHBOARD_USERNAME + " already exists, leaving user alone.")
    else:
        subprocess.check_call(["adduser", "--quiet", DASHBOARD_USERNAME])
    create_dashboard_xconfig()

def create_admin_ssh():
    log("Creating admin user SSH authorization...")
    adminUid = pwd.getpwnam(ADMIN_USERNAME).pw_uid
    adminGid = pwd.getpwnam(ADMIN_USERNAME).pw_gid
    ssh_path = "/home/"+ADMIN_USERNAME+"/.ssh"
    mkdirp(ssh_path, 0700)
    os.chown(ssh_path, adminUid, adminGid)
    authKeysFilename = ssh_path+"/authorized_keys"
    with open(authKeysFilename, "a", 0600) as authKeysFile:
        os.chown(authKeysFilename, adminUid, adminGid)
        authKeysFile.write("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDXUM5hi/eUmJudlYhVPaBpXMOI907gsXMNS8eF4nS78GTDb17NTS8kDaTIG64WgBvUH8Zuy1Gw5j1pg43DoqgJJTqXIGVEJe9wPdSboU7fkfxOQN7r8pDBdRgSGr0dC4RWPPYLvm7GYNjRG1e78/u5jb21zDiyttfHo8qiLYbxzjQegN52gJFQZaBFAzUjL7K07kd3kkPYKKUYU0x1ZaA9N8vxEMGWLhTJmkQnnQCmAGyLso8rw0r0ZmRlK0jofvM1JA9EcMq6SCJaQoAWPTplPbYUz/wJSbopU3efv6N45zE0lW64epLHeHEAHZCS4R9nDxZ3A6uQKOuY9hGxbej9 ben@skadi\n")
    replace_config_line("/etc/ssh/sshd_config", "PermitRootLogin", "PermitRootLogin no")

def create_dashboard_xconfig():
    log("Configuring X11...")
    dashboard_home = "/home/"+DASHBOARD_USERNAME
    dashboardUid = pwd.getpwnam(DASHBOARD_USERNAME).pw_uid
    dashboardGid = pwd.getpwnam(DASHBOARD_USERNAME).pw_gid
    xinitrcFilename = dashboard_home+"/.xinitrc"
    with open(xinitrcFilename, "w") as xinitrcFile:
        os.chown(xinitrcFilename, dashboardUid, dashboardGid)
        xinitrcFile.write("xset s off\n")
        xinitrcFile.write("xset -dpms\n")
        xinitrcFile.write("xset s noblank\n")
        xinitrcFile.write("exec openbox-session")

    log("Configuring VNC...")
    log_filename = "/var/log/x11vnc"
    with open(log_filename, "a") as x11vncLogFile:
        os.chmod(log_filename, 0666)
    x11vncrcFilename = dashboard_home+"/.x11vncrc"
    with open(x11vncrcFilename, "w") as x11vncrcFile:
        os.chown(x11vncrcFilename, dashboardUid, dashboardGid)
        x11vncrcFile.write("nopw\n")
        x11vncrcFile.write("logappend /var/log/x11vnc\n")
        x11vncrcFile.write("forever\n")
        x11vncrcFile.write("ncache 10\n")

    log("Configuring window manager...")
    openboxConfigPath = dashboard_home+"/.config/openbox"
    mkdirp(openboxConfigPath, 0755)
    os.chown(dashboard_home+"/.config", dashboardUid, dashboardGid)
    autostartFilename = openboxConfigPath+"/autostart"
    with open(autostartFilename, "w") as autostartFile:
        os.chown(autostartFilename, dashboardUid, dashboardGid)
        autostartFile.write('xsetroot -solid "#000000" &\n')
        autostartFile.write('unclutter &\n')
        autostartFile.write('chromium &\n')
        autostartFile.write('sleep 25; xdotool key F11 &\n')
        autostartFile.write('sleep 15; x11vnc &\n')

    log("Configuring autologin...")
    rclocalText = ''
    rclocalFilename = "/etc/rc.local"
    with open(rclocalFilename, 'r') as rclocalFile:
        rclocalText = rclocalFile.read()
    if "startx" not in rclocalText:
        with open(rclocalFilename, 'w') as rclocalFile:
            updatedText = rclocalText.replace("\nexit 0", "\nsu - "+DASHBOARD_USERNAME+" -c 'startx' &\n\nexit 0")
            rclocalFile.write(updatedText)

def set_locale():
    log("Setting locale...")
    with open("/etc/locale.gen", "w") as genFile:
        genFile.write(LOCALE + " UTF-8\n")
    subprocess.check_call(["locale-gen", "--purge"])
    os.environ["LANG"] = LOCALE
    subprocess.check_call("update-locale")

def set_timezone():
    log("Setting timezone...")
    with open("/etc/timezone", "w") as timezoneFile:
        timezoneFile.write(TIMEZONE)
    subprocess.check_call(["dpkg-reconfigure", "-f", "noninteractive", "tzdata"])

def set_keyboard():
    log("Setting keyboard layout...")
    with open("/etc/default/keyboard", "w") as keyboardFile:
        keyboardFile.write('XKBMODEL="pc104"\n')
        keyboardFile.write('XKBLAYOUT="us"\n')
        keyboardFile.write('XKBVARIANT=""\n')
        keyboardFile.write('XKBOPTIONS="terminate:ctrl_alt_bksp"\n')
        keyboardFile.write('BACKSPACE="guess"\n')

def set_hostname():
    log("Setting hostname...")
    old_hostname = get_current_hostname()
    hostname = raw_input("Hostname ["+old_hostname+"]: ")
    if hostname != "":
        with open("/etc/hostname", "w") as hostnameFile:
            hostnameFile.write(hostname)
        replace_config_line("/etc/hosts", "127.0.1.1", "127.0.1.1\t"+hostname+".bluejeansnet.com "+hostname)

def set_memory_split():
    log("Setting CPU/GPU memory split...")
    replace_config_line("/boot/config.txt", "gpu_mem", "gpu_mem=16")

def set_screen_rotation():
    log("Setting monitor rotation...")
    print("How is the monitor oriented?")
    print(" (1 = portrait, monitor was rotated counter-clockwise)")
    print(" (2 = landscape)")
    print(" (3 = portrait, monitor was rotated clockwise)")
    orientation=raw_input("enter one of (1, 2, 3) [2]: ")
    if (orientation != '') and (orientation not in ["1", "2", "3"]):
        print("Invalid orientation value '%s', assuming landscape.") % orientation
        orientation = "2"
    replace_config_line("/boot/config.txt", "display_rotate", "display_rotate="+str(orientation))

def replace_config_line(filename, search, replace):
    reader = open(filename)
    input_lines = reader.readlines()
    reader.close()
    writer = open(filename, 'w')
    
    foundSearch = False
    for line in input_lines:
        if line.startswith(search):
            writer.write(replace+"\n")
            foundSearch = True
        else:
            writer.write(line)
    if not foundSearch:
        writer.write(replace)
    writer.close()

def configure_packages():
    packagesToAdd = ["emacs23-nox", "libusb-1.0-0-dev", "screen", "chromium", "unclutter", "x11vnc", "xdotool", "htop", "x11-xserver-utils"]
    packagesToRemove = ["gnome-icon-theme", "gnome-themes-standard-data", "lxde", "lxde-core", "dillo", "midori", "desktop-base", "lightdm", "lxappearance", "lxde-common", "lxde-icon-theme", "lxinput", "lxpanel", "lxpolkit", "lxrandr", "lxsession-edit", "lxshortcut", "lxtask", "lxterminal", "weston"]
    
    log("Updating apt catalog...")
    subprocess.check_call(["apt-get", "update"])

    log("Installing apt packages...")
    subprocess.check_call(["apt-get", "install", "-y"] + packagesToAdd)    

    log("Removing unneccessary apt packages...")
    subprocess.check_call(["apt-get", "remove", "-y"] + packagesToRemove)
    subprocess.check_call(["apt-get", "autoremove", "-y"])

    log("Upgrading apt packages...")
    subprocess.check_call(["apt-get", "upgrade", "-y"])

def configure_chromium():
    log("Configuring Chromium...")
    log("downloading profile from "+CHROMIUM_PROFILE_URL)
    configPath = "/home/"+DASHBOARD_USERNAME+"/.config"
    profileArchiveFilename = urllib.urlretrieve(CHROMIUM_PROFILE_URL)[0]
    log("installing profile")
    subprocess.check_call(["tar", "-xzf", profileArchiveFilename, "-C", configPath])

def configure_panoptichrome():
    log("Configuring Panoptichrome Chromium Extension...")
    panoptichromeConfigDbFilename = "/home/"+DASHBOARD_USERNAME+"/.config/chromium/Default/Local Storage/chrome-extension_"+PANOPTICHROME_EXTENSION_ID+"_0.localstorage"
    connection = sqlite3.connect(panoptichromeConfigDbFilename)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO ItemTable VALUES('installationName', :hostname)", { "hostname": get_current_hostname() })
    cursor.execute("INSERT INTO ItemTable VALUES('serverAddress', :serverAddress)", { "serverAddress": PANOPTICHROME_SERVER_ADDRESS })
    connection.commit()
    connection.close()

def disable_pi_user():
    log("Disabling default administrator account...")
    subprocess.check_call(["usermod", "--expiredate", "1", "--lock", "pi"])

def get_current_hostname():
    with open("/etc/hostname", 'r') as hostnameFile:
        return hostnameFile.read()

def mkdirp(path, mode):
    try:
        os.makedirs(path, mode)
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
    
def ensure_root():
    if os.geteuid() != 0:
        exit("Root required")

def log(message):
    logging.info(message)

def main():
    ensure_root()
    set_hostname()
    set_screen_rotation()
    create_admin_user()
    create_dashboard_user()
    if not args.skip_packages:
        configure_packages()
    configure_chromium()
    configure_panoptichrome()
    set_memory_split()
    set_locale()
    set_timezone()
    set_keyboard()
    disable_pi_user()

    print("Done. You should reboot for changes to take effect. (sudo reboot)")

main()
