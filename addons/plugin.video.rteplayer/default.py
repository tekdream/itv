#!/usr/bin/python

"""
    RTE Player
    slacklinucs@gmail.com
"""
import sys

#plugin constants
__plugin__  = "RTE Player"
__author__  = "slacklinucs@gmail.com"
__url__     = ""
__svn_url__ = ""
__version__ = "1.0.0"

print "[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__)

if __name__ == "__main__":
    import resources.lib.RTEPlayer as RTEPlayer
    RTEPlayer.Main()

sys.modules.clear()
