import xbmc
import xbmcgui
import xbmcaddon
import fcntl
import socket
import struct
import requests
import hashlib
import os
import subprocess
import shutil
import tarfile
import util

USERNAME = None
PASSWORD = None
MACADDR = None

OSCAM_URL = "http://84.22.103.245/api/login/%s/%s/%s"
TVH_URL = "http://84.22.103.245/tvheadend/list/BackUp.tar.gz"
RESTORE_FILE = "20150505121212.tar"
RESTORE_URL = "http://84.22.103.245/restore/{0}".format(RESTORE_FILE)
BACKUP_PATH = "/storage/backup/{0}".format(RESTORE_FILE)


class DownloadCanceledException(Exception):
    pass


def show_error(message):
    dialog = xbmcgui.Dialog()
    dialog.ok('SatConf', message)


def downloadWithProgress(url, output, msg='Downloading...'):
    with open(output, 'wb') as handle:
        response = requests.get(url, stream=True)
        total = float(response.headers.get('content-length', 1))
        sofar = 0
        blockSize = 4096
        if not response.ok:
            return False

        with util.Progress('Download', msg) as p:
            for block in response.iter_content(blockSize):
                if p.iscanceled():
                    raise DownloadCanceledException()
                sofar += blockSize
                pct = int((sofar/total) * 100)
                p.update(pct)
                handle.write(block)


def backupFreeSpace():
    try:
        statvfs = os.statvfs('/storage/backup')
        free = statvfs.f_frsize * statvfs.f_bavail
        freeMB = int(free/(1024*1024.0))
        util.LOG('Free space: {0} MB'.format(freeMB))
        return freeMB
    except:
        util.ERROR()

    return 0


def get_mac(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ''.join(['%02x' % ord(char) for char in info[18:24]]).upper()
    except:
        util.ERROR()
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
        for secondTry in range(0, 1):
            login_data = requests.get(OSCAM_URL % (USERNAME, PASSWORD, MACADDR)).json()
            login_status = login_data['status']
            chlist_url = ""
            if login_status is True:
                chlist_url = login_data['download_url']
                break
            else:
                message = login_data['message']
                show_error(message)
                if secondTry or not getCredentials():
                    return

        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.softcam.oscam/config'):
            show_error("oscam not installed")
            return

        execute("systemctl stop service.softcam.oscam.service")
        downloadWithProgress(chlist_url, "/storage/.kodi/userdata/addon_data/service.softcam.oscam/config/oscam.server", 'Downloading user settings...')
        execute("systemctl restart service.softcam.oscam.service")
    except DownloadCanceledException:
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Login Failed")


def dl_tvh():
    try:
        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend'):
            show_error("tvheadend not installed")
            return

        selectConnections()

        execute("systemctl stop service.multimedia.tvheadend.service")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/channel")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/dvb")
        tarFile = "/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/BackUp.tar.gz"
        downloadWithProgress(TVH_URL, tarFile, 'Downloading channel fix...')
        extractTar(tarFile, "/")
        os.remove(tarFile)
        execute("systemctl restart service.multimedia.tvheadend.service")
        xbmc.executebuiltin('Reboot')
    except DownloadCanceledException:
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Error")


def dl_restore():
    try:
        if not os.path.exists("/storage/backup"):
            os.makedirs("/storage/backup")

        if not backupFreeSpace() >= 500:
            util.LOG('DELETING RECORDINGS')
            deleteRecordings()

        downloadWithProgress(RESTORE_URL, BACKUP_PATH, 'Downloading restore file...')
        # meheh. not an error
        show_error("Downloaded. Click OK to restore.")
        restore()
    except DownloadCanceledException:
        if os.path.exists(BACKUP_PATH):
            os.remove(BACKUP_PATH)
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Error")


def dl_rcuconf():
    try:
        if not os.path.exists("/storage/.kodi/userdata/keymaps"):
            os.makedirs("/storage/.kodi/userdata/keymaps/")
        downloadWithProgress("http://84.22.103.245/keymaps/gen.xml", "/storage/.kodi/userdata/keymaps/keyboard.xml", 'Downloading Big Remote xml...')
        # meheh. not an error
        xbmc.executebuiltin("action(reloadkeymaps)")
        show_error("Done")
    except DownloadCanceledException:
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Error")


def dl_tvh_sdc():
    try:
        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend'):
            show_error("tvheadend not installed")
            return
        show_error('Please connect the dish connection to LNB 1 (lnb closest to the usb)')
        execute("systemctl stop service.multimedia.tvheadend.service")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters")
        os.makedirs("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters")
        downloadWithProgress(
            "http://84.22.103.245/lnb/51438d1ecd9318be113df0e7cddf46ea",
            "/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters/51438d1ecd9318be113df0e7cddf46ea",
            'Setting up single dish connection...'
        )
        execute("systemctl restart service.multimedia.tvheadend.service")
    except DownloadCanceledException:
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Error")


def dl_tvh_tdc():
    try:
        if not os.path.isdir('/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend'):
            show_error("tvheadend not installed")
            return
        execute("systemctl stop service.multimedia.tvheadend.service")
        removeDir("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters")
        os.makedirs("/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters")
        downloadWithProgress(
            "http://84.22.103.245/lnb/twin/51438d1ecd9318be113df0e7cddf46ea",
            "/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters/51438d1ecd9318be113df0e7cddf46ea",
            'Setting up twin dish connection...'
        )
        downloadWithProgress(
            "http://84.22.103.245/lnb/twin/681e8b6ccbe787334dc80186a64734d2",
            "/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/input/linuxdvb/adapters/681e8b6ccbe787334dc80186a64734d2",
            'Setting up twin dish connection...'
        )
        execute("systemctl restart service.multimedia.tvheadend.service")
    except DownloadCanceledException:
        show_error('Canceled')
    except:
        util.ERROR()
        show_error("Error")


def deleteRecordings():
    try:
        execute("rm -rf /storage/recordings/*")
        return True
    except:
        util.ERROR()
    return False


def clear_recordings():
    if deleteRecordings():
        show_error("Done.")
    else:
        show_error("Error")


def restore():
    restore_path = '/storage/.restore/{0}'.format(RESTORE_FILE)
    restore_dir = '/storage/.restore'
    if not os.path.exists(restore_dir):
        os.makedirs(restore_dir)
    else:
        execute('rm -rf %s' % restore_dir)
        os.makedirs(restore_dir)
    shutil.move(BACKUP_PATH, restore_path)
    xbmc.sleep(1000)
    xbmc.executebuiltin('Reboot')


def getCredentials():
    global USERNAME
    global PASSWORD
    global MACADDR

    addon = xbmcaddon.Addon()

    MACADDR = get_mac("eth0")
    addon.setSetting('mac.address', MACADDR)
    USERNAME = addon.getSetting('USER')
    temp = addon.getSetting('PASS')

    if not USERNAME or not temp:
        addon.openSettings()
        USERNAME = addon.getSetting('USER')
        temp = addon.getSetting('PASS')
        if not USERNAME or not temp:
            return False

    PASSWORD = hashlib.md5(temp).hexdigest()
    return True


def selectConnections():
    dlg = xbmcgui.Dialog()
    res = dlg.select("SatConf", [
        "1. Single Dish Connection",
        "2. Twin Dish Connection",
    ])

    if res < 0:
        return False

    if res == 0:
        dl_tvh_sdc()
    elif res == 1:
        dl_tvh_tdc()

    return True


def main():
    if not getCredentials():
        show_error('Aborted!')
        return

    options = [
        ('dl_oscam', '{0}. Download User Settings'),
        # ('dl_tvh', '{0}. Download Channel Fix')
        ('dl_restore', '{0}. Download Restore File'),
        ('dl_rcuconf', '{0}. Download Big Remote xml'),
        ('dl_tvh_sdc', '{0}. Single Dish Connection'),
        ('dl_tvh_tdc', '{0}. Twin Dish Connection'),
        ('clear_recordings', '{0}. Clear recordings')
    ]

    dlg = xbmcgui.Dialog()
    idx = dlg.select("SatConf", [o[1].format(i+1) for i, o in enumerate(options)])

    if idx < 0:
        return

    res = options[idx][0]

    if res == 'dl_oscam':
        dl_oscam()
    elif res == 'dl_tvh':
        dl_tvh()
    elif res == 'dl_restore':
        dl_restore()
    elif res == 'dl_rcuconf':
        dl_rcuconf()
    elif res == 'dl_tvh_sdc':
        dl_tvh_sdc()
    elif res == 'dl_tvh_tdc':
        dl_tvh_tdc()
    elif res == 'clear_recordings':
        clear_recordings()
