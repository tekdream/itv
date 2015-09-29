import xbmc
import xbmcgui
import xbmcaddon
import fcntl, socket, struct
import requests
import hashlib
import urllib
import os, subprocess
import shutil
import tarfile

def show_error(message):
    dialog = xbmcgui.Dialog()
    ok = dialog.ok('SatConf', message)

def get_mac(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ''.join(['%02x' % ord(char) for char in info[18:24]]).upper()
    except:
        return '00000000'

def execute(command_line):
    try:
        process = subprocess.Popen(command_line, shell=True, close_fds=True)
        process.wait()
    except:
        pass

def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def extractTar(file, path):
    tfile = tarfile.open(file)
    if tarfile.is_tarfile(file):
        tfile.extractall(path)

def dl_oscam():
    # oscam
    try:
        login_data = requests.get(OSCAM_URL % (username, password, mac_addr)).json()
        login_status = login_data['status']
        chlist_url = "";
        if login_status == True:
            chlist_url = login_data['download_url']
        else:
            message = login_data['message']
            show_error(message)
            exit(0)
        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.softcam.oscam/config'):
            show_error("oscam not installed")
            exit(0)
        execute("systemctl stop service.softcam.oscam.service")
        urllib.urlretrieve(chlist_url, "/storage/.kodi/userdata/addon_data/service.softcam.oscam/config/oscam.server")
        execute("systemctl restart service.softcam.oscam.service")
    except:
        show_error("Login Failed")

def dl_tvh():
    try:
        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend'):
            show_error("tvheadend not installed")
            exit(0)
        execute("systemctl stop service.multimedia.tvheadend.service")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/channel")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/dvb")
        tarFile = "/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/BackUp.tar.gz"
        urllib.urlretrieve(TVH_URL, tarFile)
        extractTar(tarFile, "/")
        os.remove(tarFile)
        execute("systemctl restart service.multimedia.tvheadend.service")
    except:
        show_error("Error")

def dl_restore():
    try:
        if not os.path.exists("/storage/backup"):
            os.makedirs("/storage/backup")
        urllib.urlretrieve(RESTORE_URL, "/storage/backup/%s" % RESTORE_FILE)
        # meheh. not an error
        show_error("downloaded. now to settings -> openelec -> system -> restore")
    except:
        show_error("Error")

# =============================
addon = xbmcaddon.Addon()

if (not addon.getSetting('firstrun')):
    addon.setSetting('firstrun', '1')
    addon.openSettings()

mac_addr = get_mac("eth0")
username = addon.getSetting('USER')
password = hashlib.md5(addon.getSetting('PASS')).hexdigest()

OSCAM_URL = "http://84.22.103.245/api/login/%s/%s/%s"
TVH_URL = "http://84.22.103.245/tvheadend/list/BackUp.tar.gz"
RESTORE_FILE = "201505051212.tar"
RESTORE_URL = "http://84.22.103.245/restore/%s" % RESTORE_FILE

dlg = xbmcgui.Dialog()
res = dlg.select("SatConf", ["Download Oscam Config", "Download Tvheadend Channel List", "Download Restore File"])
if res == 0:
    dl_oscam()
elif res == 1:
    dl_tvh()
elif res == 2:
    dl_restore()
else:
    pass
