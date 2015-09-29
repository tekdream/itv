#!/usr/bin/python

"""
    RTE Player
    slacklinucs@gmail.com
"""

import re
import sys
from bs4 import SoupStrainer, BeautifulSoup, BeautifulStoneSoup
import urllib, urllib2

import RTEScraper
from RTEScraper import RTE
import RTERadioScraper
from RTERadioScraper import RTERadio

import MenuConstants

class Channels:

    def getChannels(self):
        return [RTE().getChannelDetail(),
                #RTERadio().getChannelDetail(),
                {'Channel': 'All', 'Thumb':'https://raw.githubusercontent.com/Coolwavexunitytalk/images/master/rte%20icons/recently%20watched.png', 'Title':'Recently watched', 'mode':'recentlyWatched', 'Plot':''}]
                #{'Channel': 'All', 'Thumb':'../icon.png', 'Title':'Favorites', 'mode':'favorites', 'Plot':''}]

    def grabDetails(self, url, img, title = None):
        if channel == RTEScraper.CHANNEL:
            return RTE().grabDetails(url, img, title)

    def getVideoDetails(self, channel, url, skipAds):
        if channel == RTEScraper.CHANNEL:
            return RTE().getVideoDetails(url, skipAds)

    def getMainMenu(self, channel):
        if channel == RTEScraper.CHANNEL:
            return RTE().getMainMenu(), True
        elif channel == RTERadioScraper.CHANNEL:
            return RTERadio().getMainMenu(), True

    def getEpisodes(self, channel, showID):
        if channel == RTEScraper.CHANNEL:
            return RTE().getEpisodes(showID)

# This is to allow an indirection on the url.  Right now, hacked - TODO: Make properly OO by adding this as a required method of each scraper
    def referenceURL(self, channel, url):
        if channel == RTEScraper.CHANNEL:
            return url

    def getMenu(self, channel, menutype, name = None):
        if channel == RTEScraper.CHANNEL:
            if menutype == MenuConstants.MODE_CATEGORY:
                return RTE().SearchByCategory(name)
            elif menutype == MenuConstants.MODE_ATOZ:
                return RTE().SearchAtoZ(name)
            else:
                return RTE().getMenuItems(menutype)

if __name__ == '__main__':
    print 'hello'
