# -*- coding: utf-8 -*-
import os
import shutil
import time
import traceback
import json
import uuid

import xbmc

from lib import util


ADDON_PATH = xbmc.translatePath(util.ADDON.getAddonInfo('path')).decode('utf-8')
ADDON_PROFILE = xbmc.translatePath(util.ADDON.getAddonInfo('profile')).decode('utf-8')
KODI_PROFILE = xbmc.translatePath('special://profile').decode('utf-8')

if not os.path.exists(ADDON_PROFILE):
    os.makedirs(ADDON_PROFILE)

def reboot():
    xbmc.sleep(1000)
    util.LOG('Rebooting...')
    xbmc.executebuiltin('Reboot')


class AdvancedSettingsUpdater:
    ADVANCED_SETTINGS_VERSION = 1
    @staticmethod
    def currentVersion():
        advancedSettingsVersion = os.path.join(KODI_PROFILE, 'advancedsettings.version')
        if not os.path.exists(advancedSettingsVersion):
            return 0

        try:
            with open(advancedSettingsVersion, 'r') as f:
                return int(f.read())
        except:
            traceback.print_exc()
            return 0

    @classmethod
    def update(cls):
        if cls.currentVersion() == cls.ADVANCED_SETTINGS_VERSION:
            util.LOG('advancedsettings.xml up to date')
            return

        util.LOG('Updating advancedsettings.xml to version {0}...'.format(cls.ADVANCED_SETTINGS_VERSION))
        source = os.path.join(ADDON_PATH, 'resources', 'advancedsettings.xml')
        advancedSettingsFile = os.path.join(KODI_PROFILE, 'advancedsettings.xml')
        with open(advancedSettingsFile, 'w') as f:
            with open(source, 'r') as s:
                f.write(s.read())

        advancedSettingsVersion = os.path.join(KODI_PROFILE, 'advancedsettings.version')
        with open(advancedSettingsVersion, 'w') as f:
            f.write(str(cls.ADVANCED_SETTINGS_VERSION))

        util.LOG('Update finished')
        cls.askReboot()

    @staticmethod
    def askReboot():
        import xbmcgui
        yes = xbmcgui.Dialog().yesno('Reboot', 'System has been updated and needs to be restarted.', 'Restart now?')
        if yes:
            reboot()

class DirectoryCleaner:
    LOST_AND_FOUND = '/storage/lost+found'
    RECORDINGS = '/storage/recordings'
    ADDONS_PACKAGES = '/storage/.kodi/addons/packages'
    THUMBNAILS = '/storage/.kodi/userdata/Thumbnails'
    THUMB_SUBS = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'Video')

    @staticmethod
    def emptyDirectory(path):
        if not os.path.exists(path):
            return util.LOG('emptyDirectory: {0} does not exist'.format(util.cleanStrRepr(path)))

        for sub in os.listdir(path):
            full = os.path.join(path, sub)
            try:
                if os.path.isfile(full):
                    util.LOG('Removing file: {0}'.format(util.cleanStrRepr(full)))
                    os.unlink(full)
                elif os.path.isdir(full):
                    util.LOG('Removing dir: {0}'.format(util.cleanStrRepr(full)))
                    shutil.rmtree(full)
            except Exception:
                util.ERROR()

    @staticmethod
    def freshenDirectory(path, days=7):
        if not os.path.exists(path):
            return util.LOG('emptyDirectory: {0} does not exist'.format(util.cleanStrRepr(path)))

        threshold = time.time() - days * 86400
        for f in os.listdir(path):
            full = os.path.join(path, f)
            try:
                if os.stat(full).st_atime < threshold:
                    if os.path.isfile(full):
                        util.LOG('Removing file: {0}'.format(util.cleanStrRepr(full)))
                        os.remove(full)
            except:
                util.ERROR()

    @classmethod
    def cleanLostAndFound(cls):
        util.LOG('Cleaning lost+found')
        cls.emptyDirectory(cls.LOST_AND_FOUND)

    @classmethod
    def cleanAddonsPackages(cls):
        util.LOG('Cleaning addons/packages')
        cls.emptyDirectory(cls.ADDONS_PACKAGES)

    @classmethod
    def cleanBadRecordings(cls):
        util.LOG('Cleaning un-authorized recordings')
        if os.path.exists(cls.RECORDINGS):
            cls.emptyDirectory(cls.RECORDINGS)
        else:
            util.LOG('Returning recording path to default state')
            try:
                os.unlink(cls.RECORDINGS)
            except:
                pass

            os.makedirs(cls.RECORDINGS)


    @classmethod
    def cleanThumbnails(cls):
        util.LOG('Cleaning old thumbnails')
        for sub in cls.THUMB_SUBS:
            full = os.path.join(cls.THUMBNAILS, sub)
            if not os.path.exists(full):
                continue
            cls.freshenDirectory(full)

class SettingsRestore:
    SETTINGS_BACKUP_PATH = '/storage/settings_backup/'

    OSCAM_DEST_PATH = '/storage/.kodi/userdata/addon_data/service.softcam.oscam/config/oscam.server'
    OSCAM_SOURCE_PATH = os.path.join(SETTINGS_BACKUP_PATH, 'oscam.server')

    SATCONF_DEST_PATH = '/storage/.kodi/userdata/addon_data/script.satconf/settings.xml'
    SATCONF_SOURCE_PATH = os.path.join(SETTINGS_BACKUP_PATH, 'satconf.settings.xml')

    GENESISFAVS_DEST_PATH = '/storage/.kodi/userdata/addon_data/plugin.video.genesis/favourites.db'
    GENESISFAVS_SOURCE_PATH = os.path.join(SETTINGS_BACKUP_PATH, 'genesis.favourites.db')

    CONNMAN_DEST_PATH = '/storage/.cache/connman'
    CONNMAN_SOURCE_PATH = os.path.join(SETTINGS_BACKUP_PATH, 'connman')

    @staticmethod

    def restoreFile(source, dest):
        try:
            if not os.path.exists(source):
                util.LOG('Not found!')
                return False

            destDir = os.path.dirname(dest)
            if not os.path.exists(destDir):
                os.makedirs(destDir)

            shutil.copy(source, dest)
            os.remove(source)

            return True
        except:
            util.ERROR()

        return False

    @classmethod
    def restoreOscam(cls):
        util.LOG('Restoring oscam.server')
        with util.ServiceControl('service.softcam.oscam.service'):
            return cls.restoreFile(cls.OSCAM_SOURCE_PATH, cls.OSCAM_DEST_PATH)

    @classmethod
    def restoreSatconf(cls):
        util.LOG('Restoring satconf settings.xml')
        return cls.restoreFile(cls.SATCONF_SOURCE_PATH, cls.SATCONF_DEST_PATH)

    @classmethod
    def restoreGenesisFavs(cls):
        util.LOG('Restoring genesis favourites.db')
        return cls.restoreFile(cls.GENESISFAVS_SOURCE_PATH, cls.GENESISFAVS_DEST_PATH)

    @classmethod
    def restoreConnman(cls):
        util.LOG('Restoring connman')
        try:
            if not os.path.exists(cls.CONNMAN_SOURCE_PATH):
                util.LOG('Not found!')
                return False

            if os.path.exists(cls.CONNMAN_DEST_PATH):
                shutil.rmtree(cls.CONNMAN_DEST_PATH)

            shutil.copytree(cls.CONNMAN_SOURCE_PATH, cls.CONNMAN_DEST_PATH)

            shutil.rmtree(cls.CONNMAN_SOURCE_PATH)

            return True
        except:
            util.ERROR()

        return False

    @classmethod
    def restore(cls):
        cls.restoreOscam()
        cls.restoreSatconf()
        cls.restoreGenesisFavs()
        cls.restoreConnman()


class Dialogs:
    @staticmethod
    def message(heading, message=''):
        import xbmcgui
        xbmcgui.Dialog().ok(heading, message)

    @staticmethod
    def choice(heading, options_list=None):
        import xbmcgui
        idx = xbmcgui.Dialog().select(heading, [x[1] for x in options_list])
        if idx < 0:
            return None

        return options_list[idx][0]

    @staticmethod
    def yes(heading, message=''):
        import xbmcgui
        return xbmcgui.Dialog().yesno(heading, message)


class RecordingDriveWatcher:
    MEDIA_DIR_PATH = '/media'
    RECORDINGS_PATH = '/storage/recordings'
    ACCESS_CONTROL_DIR_PATH = '/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/accesscontrol'
    TIMESHIFT_CONFIG_PATH = '/storage/.kodi/userdata/addon_data/service.multimedia.tvheadend/timeshift/config'

    ID_FILE = '.MOUNT_ID'

    SAVE_FILE = os.path.join(ADDON_PROFILE, 'data')

    def __init__(self):
        self.lastMTime = None
        self.mounts = []
        self.initRecordingMount()
        self.load()
        self.check()
        self.verify()

    def initRecordingMount(self):
        self.mount = ''
        self.mountID = ''
        self.mountPath = ''
        self.recordingsPath = ''
        self.timeshiftPath = ''

    def save(self):
        data = {
            'mount': self.mount,
            'mountID': self.mountID,
            'mountPath': self.mountPath,
            'recordingsPath': self.recordingsPath,
            'timeshiftPath': self.timeshiftPath,
            'mounts': self.mounts
        }

        with open(self.SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def load(self):
        if not os.path.exists(self.SAVE_FILE):
            return

        with open(self.SAVE_FILE, 'r') as f:
            try:
                data = json.load(f)
            except ValueError:
                util.ERROR()
                return

        if not 'mount' in data:
            return

        self.mount = data['mount']
        self.mountID = data['mountID']
        self.mountPath = data['mountPath']
        self.recordingsPath = data['recordingsPath']
        self.timeshiftPath = data['timeshiftPath']
        self.mounts = data['mounts']

    def verify(self):
        if not self.mount:
            self.restoreRecordingsDir()

    def check(self):
        mtime = os.stat(self.MEDIA_DIR_PATH).st_mtime
        if mtime == self.lastMTime:
            return

        if not xbmc.getCondVisibility('Pvr.HasTVChannels'): #This detects shutdown for our purposes - not reliable
            util.LOG('Waiting for TVH...')
            return

        util.LOG('Change detected in {0}'.format(util.cleanStrRepr(self.MEDIA_DIR_PATH)))

        self.lastMTime = mtime

        mounts = os.listdir(self.MEDIA_DIR_PATH)
        if not mounts:
            if self.mounts:
                for mount in list(self.mounts):
                    self.mountRemoved(mount)
                self.mounts = []
            return

        if xbmc.abortRequested:
            return

        new = False

        for mount in mounts:
            if mount not in self.mounts:
                new = self.newMount(mount) or new

        for mount in self.mounts:
            if mount not in mounts:
                self.mountRemoved(mount)

        if xbmc.abortRequested:
            return

        if new and not self.savedMountIsMounted():
            self.setupMount()

    def savedMountIsMounted(self):
        return self.mount in self.mounts and self.mountID == self.getID(self.mount)

    def setupMount(self):
        # Prents change of drive and not needed - I think :)
        # if self.mount:
        #     return False

        if not self.mounts:
            return False

        if len(self.mounts) > 1:
            if not Dialogs.yes('Choose', 'A storage device has been detected.[CR]Would you like to use it for recording?'):
                return False

            mount = Dialogs.choice('Choose Partition', [(m,m) for m in self.mounts])
            if not mount:
                return False
        else:
            if not Dialogs.yes('Choose', 'A storage device has been detected.[CR]Would you like to use if for recording?'):
                return False

            mount = self.mounts[-1]

        self.setMountForRecording(mount)

        Dialogs().message('Done', 'Done.')

        return True

    def newMount(self, mount):
        mountPath = os.path.join(self.MEDIA_DIR_PATH, mount)

        if not os.path.ismount(mountPath):
            return False

        self.mounts.append(mount)
        self.save()
        util.LOG('New mount detected ({0}): {1}'.format(os.stat(mountPath).st_dev, util.cleanStrRepr(mount)))

        if mount == self.mount and self.mountID == self.getID(mount):
            util.LOG('Restoring recording mount: {0}'.format(util.cleanStrRepr(mount)))
            self.setMountForRecording(mount)

        return True

    def mountRemoved(self, mount):
        if xbmc.Monitor().waitForAbort(10):
            return

        if mount in self.mounts:
            self.mounts.pop(self.mounts.index(mount))
        self.save()
        util.LOG('Mount removed: {0}'.format(util.cleanStrRepr(mount)))

        if mount == self.mount:
            self.enableRecording(False)
            self.unsetRecordingMount()

    def removeRecordingsDir(self):
        if os.path.exists(self.RECORDINGS_PATH):
            if os.path.islink(self.RECORDINGS_PATH):
                os.unlink(self.RECORDINGS_PATH)
            elif os.path.isdir(self.RECORDINGS_PATH):
                DirectoryCleaner.cleanBadRecordings()
                os.rmdir(self.RECORDINGS_PATH)
            else:
                os.remove(self.RECORDINGS_PATH)
        else:
            try:
                os.unlink(self.RECORDINGS_PATH)
                util.LOG('Removed dead recordings symlink')
            except:
                pass

        if os.path.exists(self.RECORDINGS_PATH) or os.path.islink(self.RECORDINGS_PATH):
            util.LOG('Failed to remove recordings path')
            return False

        return True

    def restoreRecordingsDir(self):
        if os.path.exists(self.RECORDINGS_PATH):
            if os.path.islink(self.RECORDINGS_PATH):
                os.unlink(self.RECORDINGS_PATH)
                util.LOG('Removed unexpected dead recordings symlink')
            elif os.path.isdir(self.RECORDINGS_PATH):
                return

        if not os.path.exists(self.RECORDINGS_PATH):
            os.makedirs(self.RECORDINGS_PATH)

    def enableRecording(self, enable=True):
        if not os.path.exists(self.ACCESS_CONTROL_DIR_PATH):
            return

        with util.ServiceControl('service.multimedia.tvheadend.service'):
            for acf in os.listdir(self.ACCESS_CONTROL_DIR_PATH):
                full = os.path.join(self.ACCESS_CONTROL_DIR_PATH, acf)
                try:
                    with open(full, 'r') as f:
                        data = json.load(f)

                    data['dvr'] = enable
                    data['htsp_dvr'] = enable
                    data['all_dvr'] = enable
                    data['all_rw_dvr'] = enable

                    with open(full, 'w') as f:
                        json.dump(data, f, indent=4)

                except:
                    util.ERROR()
                    continue

            try:
                with open(self.TIMESHIFT_CONFIG_PATH, 'r') as f:
                    data = json.load(f)

                data['enabled'] = enable and 1 or 0
                data['ondemand'] = enable and 1 or 0
                data['path'] = self.timeshiftPath

                with open(self.TIMESHIFT_CONFIG_PATH, 'w') as f:
                    json.dump(data, f, indent=4)

            except:
                util.ERROR()

        util.notify('Recording {0}'.format(enable and 'Enabled' or 'Disabled'))

    def writeID(self, mount):
        idPath = os.path.join(self.MEDIA_DIR_PATH, mount, self.ID_FILE)
        if os.path.exists(idPath):
            mID = self.getID(mount)
            if mID:
                return mID

        try:
            mID = str(uuid.uuid1())
            with open(idPath, 'w') as f:
                f.write(mID)

            return mID
        except:
            util.ERROR()

        return None


    def getID(self, mount):
        idPath = os.path.join(self.MEDIA_DIR_PATH, mount, self.ID_FILE)
        if not os.path.exists(idPath):
            return None

        try:
            with open(idPath, 'r') as f:
                return f.read()
        except:
            util.ERROR()

        return None

    def setMountForRecording(self, mount):
        if not self.removeRecordingsDir():
            return

        util.LOG('Setting recording mount to: {0}'.format(util.cleanStrRepr(mount)))

        self.mount = mount
        self.mountPath = os.path.join(self.MEDIA_DIR_PATH, mount)
        self.recordingsPath = os.path.join(self.mountPath, 'recordings')
        self.timeshiftPath = os.path.join(self.mountPath, 'timeshift')

        self.mountID = self.writeID(mount)

        if not self.mountID:
            util.LOG('Failed to set recording mount to: {0}'.format(util.cleanStrRepr(mount)))
            return self.initRecordingMount()

        if not os.path.exists(self.recordingsPath):
            os.makedirs(self.recordingsPath)

        if not os.path.exists(self.timeshiftPath):
            os.makedirs(self.timeshiftPath)

        os.symlink(self.recordingsPath, self.RECORDINGS_PATH)

        self.save()

        self.enableRecording()


    def unsetRecordingMount(self):
        if self.removeRecordingsDir():
            os.makedirs(self.RECORDINGS_PATH)

        self.save()

    @property
    def hasMountSetup(self):
        return bool(self.mount)


class Service(xbmc.Monitor):
    def __init__(self):
        self._pollInterval = 5
        self._nextDayChange = time.time() + (24 * 3600)
        self._nextHourChange = time.time() + 3600
        self.recordingDriveWatcher = RecordingDriveWatcher()
        util.LOG('SERVICE START')
        self.start()
        util.LOG('SERVICE STOP')

    def start(self):
        self.poll()
        self.hour() # Run hourly and daily on startup
        self.day()
        SettingsRestore.restore()
        AdvancedSettingsUpdater.update()
        self.daemon()

    def daemon(self):
        while not self.waitForAbort(self._pollInterval):
            self._poll()

    def _poll(self):
        self.poll()
        if time.time() > self._nextHourChange:
            self._nextHourChange += 3600
            self._hour()

    def _hour(self):
        self.hour()
        if time.time() > self._nextDayChange:
            self._nextDayChange += (24 * 3600)
            self.day()

    def poll(self):
        try:
            self.recordingDriveWatcher.check()
        except:
            util.ERROR()

    def hour(self):
        pass

    def day(self):
        try:
            DirectoryCleaner.cleanLostAndFound()
            DirectoryCleaner.cleanAddonsPackages()
            if not self.recordingDriveWatcher.hasMountSetup:
                self.recordingDriveWatcher.enableRecording(False)
                DirectoryCleaner.cleanBadRecordings()
            #DirectoryCleaner.cleanThumbnails()
        except:
            util.ERROR()


Service()
