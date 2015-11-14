# -*- coding: utf-8 -*-
import os
import traceback

import xbmc

from lib import util


ADDON_PATH = util.ADDON.getAddonInfo('path')
KODI_PROFILE = xbmc.translatePath('special://profile').decode('utf-8')


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

class Service:
    def __init__(self):
        util.LOG('SERVICE START')
        self.start()
        util.LOG('SERVICE STOP')

    def start(self):
        AdvancedSettingsUpdater.update()


Service()
