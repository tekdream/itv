import subprocess

import xbmc
import xbmcgui


def LOG(msg):
    xbmc.log('[- Satconf -]: {0}'.format(msg))


def ERROR(msg=''):
    if msg:
        LOG(msg)
    import traceback
    xbmc.log(traceback.format_exc())


class Progress(object):
    def __init__(self, heading, line1='', line2='', line3=''):
        self.dialog = xbmcgui.DialogProgress()
        self.heading = heading
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        self.pct = 0
        self.message = ''

    def __enter__(self):
        self.dialog.create(self.heading, self.line1, self.line2, self.line3)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dialog.close()

    def update(self, pct, line1=None, line2=None, line3=None):
        self.pct = pct
        if line1 is not None:
            self.line1 = line1
        if line2 is not None:
            self.line2 = line2
        if line3 is not None:
            self.line3 = line3

        self.dialog.update(self.pct, self.line1, self.line2, self.line3)

    def msg(self, msg=None, heading=None, pct=None):
        if pct is not None:
            self.pct = pct
        self.heading = heading is not None and heading or self.heading
        self.message = msg is not None and msg or self.message
        self.update(self.pct, self.heading, self.message)
        return not self.dialog.iscanceled()

    def iscanceled(self):
        return self.dialog.iscanceled()


class ServiceControl:
    TEMPLATE_STOP = 'systemctl stop {0}'
    TEMPLATE_RESTART = 'systemctl restart {0}'

    def __init__(self, service):
        self.service = service

    def __enter__(self):
        self.execute(self.TEMPLATE_STOP.format(self.service))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.execute(self.TEMPLATE_RESTART.format(self.service))

    @staticmethod
    def execute(command_line):
        try:
            process = subprocess.Popen(command_line, shell=True, close_fds=True)
            process.wait()
        except:
            pass
