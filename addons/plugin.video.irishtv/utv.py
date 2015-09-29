# -*- coding: utf-8 -*-
import sys
import re
from time import strftime,strptime,mktime
import datetime

from pprint import pformat

import time, random
if sys.version_info >=  (2, 7):
    import json as _json
else:
    import simplejson as _json 
    
from datetime import timedelta
from datetime import date
from datetime import datetime
from urlparse import urljoin


import xbmc
import xbmcgui
import xbmcplugin

import mycgi
import utils
from loggingexception import LoggingException
import rtmp

import HTMLParser
from BeautifulSoup import BeautifulSoup

from resumeplayer import ResumePlayer
from watched import WatchedPlayer
from provider import Provider
from brightcove import BrightCoveProvider

appFormat = u"vod?videoId=%s&lineUpId=&pubId=%s&playerId=%s&affiliateId="

urlRoot     = u"http://player.utv.ie"
scheduleUrl = u"http://player.utv.ie/schedule/"
searchUrl = "http://player.utv.ie/search_results/default.aspx?q=%s"
dateUrl = u"http://player.utv.ie/assets/data/episodes.ashx?isApp=False&date=%s"
AtoZURL = "http://player.utv.ie/assets/data/programmes.ashx?isApp=False"

allShowsUrl = "http://player.utv.ie/all_shows/"
categoryUrl = "http://player.utv.ie/all_shows/"


defaultLinkUrl = u"http://www.tg4.ie/%s/tg4-player/tg4-player.html?id=%s&title=%s"
playerFunctionsUrl = u'http://www.tg4.ie/TG4-player/script/player-functions2.js'

class UTVProvider(BrightCoveProvider):

    def __init__(self):
        super(UTVProvider, self).__init__()

    def GetProviderId(self):
        return u"UTV"

    def GetProviderName(self):
        return u"UTV Ireland"

    def ExecuteCommand(self, mycgi):
        return super(UTVProvider, self).ExecuteCommand(mycgi)

    def GetPlayer(self, pid, live, playerName):
        if self.watchedEnabled:
            player = WatchedPlayer()
            player.initialise(live, playerName, self.GetWatchedPercent(), pid, self.resumeEnabled, self.log)
            return player
        elif self.resumeEnabled:
            player = ResumePlayer()
            player.init(pid, live, self.GetProviderId())
            return player
        
        return super(UTVProvider, self).GetPlayer(pid, live, self.GetProviderId())

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        try:
            listItems = []
            searchItemTuple = None

            self.AddMenuItem(listItems, u"Search", u'&search=1')
            self.AddMenuItem(listItems, u"Latest", u'&latest=1')
            self.AddMenuItem(listItems, u"A to Z", u'&atoz=1')
            self.AddMenuItem(listItems, u"Categories", u'&categories=1')
            self.AddMenuItem(listItems, u"Popular", u'&popular=1')

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if xml is not None:
                msg = u"xml:\n\n%s\n\n" % xml
                exception.addLogMessage(msg)
            
            # Cannot show root menu
            exception.addLogMessage(self.language(30010))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False


    def ParseCommand(self, mycgi):
        #(categories, category, search, date, episodeId, series, latest, popular, live) = mycgi.Params( u'categories', u'category', u'search', u'date', u'episodeId', u'series', u'latest', u'popular', u'live') 
        (categories, category, showUrl, search, date, latest, atoz, popular, playEpisode, resume) = mycgi.Params( u'categories', u'category', u'showUrl', u'search', u'date', u'latest', u'atoz', u'popular', u'playEpisode', u'resume')

        self.log("(categories, category, showUrl, search, date, latest, atoz, popular, playEpisode): %s" % unicode((categories, category, showUrl, search, date, latest, atoz, popular, playEpisode)))
        category = mycgi.URLUnescape(category)
        
        if playEpisode <> '':
            resumeFlag = False
            if resume <> u'':
                resumeFlag = True

            return self.PlayVideoWithDialog(self.ShowEpisode, (showUrl,resumeFlag))

        if search <> u'':
            return self.DoSearch()
        
        if category != '':
            return self.ShowCategory(category)

        if categories != '':
            return self.ShowCategories()

        if latest != '':
            return self.ListLatest()
        
        if atoz != '':
            return self.ShowAtoZ()
        
        if date <> u'':
            return self.ListByDate(date)
            
        if showUrl <> '':
            return self.ListEpisodes(showUrl)
        
        if popular != '':
            return self.ListPopular()
        
        return False

    def CreateCategoryItem(self, category, categoryId):
        self.log(u"%s" % categoryId, xbmc.LOGDEBUG)
        newLabel = category

        thumbnailPath = self.GetThumbnailPath(newLabel)
        newListItem = xbmcgui.ListItem( label=newLabel )
        newListItem.setThumbnailImage(thumbnailPath)
        url = self.GetURLStart() + u'&category=' + mycgi.URLEscape(categoryId)

        return (url, newListItem, True)


    """

                <div id="mainContent_divCategory" class="show-content box category">
                    
                            
                                <section id='drama & soaps-shows' class='drama & soaps-shows'>
                                    <h3 class="section-head">
                                        Drama & Soaps</h3>
                                    <div class="programmes">
                                        
                                                <article>
                                                    <div class="screenshot">
                                                        <a href="/programme/Coronation-Street">
                                                            <img src='/assets/data/getmediafile.ashx?guid=4c6b7b3d-e2f3-42fd-b139-456dc51336e5&maxsidesize=320'
                                                                alt="episode screenshot">
                                                        </a>&nbsp;</div>
                                                    <h1>
                                                        <a href="/programme/Coronation-Street">
                                                            Coronation Street</a></h1>
                                                    <span class="episode-count"><b class="count"><span>
                                                        2</span> </b><span>&nbsp;Episodes</span>
                                                    </span>
                                                </article>
                                            
                                                <article>
                                                    <div class="screenshot">
                                                        <a href="/programme/Emmerdale">
                                                            <img src='/assets/data/getmediafile.ashx?guid=7cb823c4-c911-4c6c-8007-8368133e365d&maxsidesize=320'
                                                                alt="episode screenshot">
                                                        </a>&nbsp;</div>
                                                    <h1>
                                                        <a href="/programme/Emmerdale">
                                                            Emmerdale</a></h1>
                                                    <span class="episode-count"><b class="count"><span>
                                                        2</span> </b><span>&nbsp;Episodes</span>
                                                    </span>
                                                </article>
                                            
                                    </div>
                                </section>

    """
    def ShowCategories(self):
        listItems = []
        

        try:
            html = None
            html = self.httpManager.GetWebPage(allShowsUrl, 20000)
    
            soup = BeautifulSoup(html)
            categoryDiv = soup.find('div', 'category')
            categories = categoryDiv.findAll('section')
            
            for category in categories:
                listItems.append( self.CreateCategoryItem(category.h3.text, category['id']) )

            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
            
            # "Error processing categories"
            exception.addLogMessage(self.language(30058))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    def AddShowItem(self, listItems, newLabel, urlFragment, thumbnailPath):
        self.AddMenuItem(listItems, newLabel, urlFragment, thumbnailPath)
        
    def AddEpisodeItem(self, listItems, showTitle, episodeTitle, description, showUrl, thumbnailPath, dateString = None, timeString = None):
        self.log("(showTitle, episodeTitle, description, showUrl, thumbnailPath, dateString, timeString): %s" % unicode((showTitle, episodeTitle, description, showUrl, thumbnailPath, dateString, timeString)))
        
        episodeTitlePattern = "%s  [%s]"
        
        if dateString is not None:
            datePattern = u"%d/%m/%Y %H:%M:%S"
            airDate = datetime.fromtimestamp(mktime(strptime(dateString, datePattern)))
            
            episodeTitle = episodeTitlePattern % (showTitle if (episodeTitle is None) else episodeTitle, airDate.strftime(u"%A, %d %B %Y @%H:%M"))
        else:
            episodeTitle = episodeTitlePattern % (showTitle if (episodeTitle is None) else episodeTitle, timeString)
            
        infoLabels = {
                      u'tvshowtitle': showTitle, 
                      u'Title': episodeTitle, 
                      u'plot': description, 
                      u'plotoutline':  description
                      }
        
        if dateString is not None:
            infoLabels[u'aired'] = airDate.strftime(u"%d.%m.%Y")                                  

        url = self.GetURLStart() + "&showUrl=%s&playEpisode=1" % mycgi.URLEscape(showUrl)
        
        episodeId = ""
        self.log("(self.watchedEnabled): %s" % self.watchedEnabled)
        if self.watchedEnabled:
            episodeId = self.GetEpisodeId(urlRoot + showUrl)
            url = url + "&episodeId=%s" % mycgi.URLEscape(episodeId)

        self.log("(episodeId): %s" % episodeId)
        contextMenuItems = []
        newListItem = self.ResumeWatchListItem(url, episodeId, contextMenuItems, infoLabels, thumbnailPath)

        listItems.append( (url, newListItem, False) )

    def GetEpisodeId(self, fullShowUrl):
        self.log("(fullShowUrl): %s" % fullShowUrl)
        html = None
        html = self.httpManager.GetWebPage(fullShowUrl, 20000)

        soup = BeautifulSoup(html)

        hero = soup.find('section', {'id':'hero'})
        screenShot = hero.find('div', 'screenshot')
        episodeId = screenShot.find('a')['data-bcid']

        self.log("screenShot.find('a'): %s" % pformat(screenShot.find('a')), xbmc.LOGDEBUG)
        self.log("episodeId: %s" % episodeId, xbmc.LOGDEBUG)

        return episodeId
        

    def AddMenuItem(self, listItems, newLabel, urlFragment, thumbnailPath = None, infoLabels = None):
        try:
            folder = True

            if thumbnailPath is None:
                thumbnailPath = self.GetThumbnailPath(newLabel)
                
            newListItem = xbmcgui.ListItem( label=newLabel )
            newListItem.setThumbnailImage(thumbnailPath)
            
            if infoLabels is not None:
                newListItem.setInfo(u'video', infoLabels)
                newListItem.setProperty("Video", "true")
                folder = False
                
            url = self.GetURLStart() + urlFragment

            listItems.append( (url, newListItem, folder) )
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Not fatal, just means that we don't show this menu item
            exception.process(severity = xbmc.LOGWARNING)


    # TODO Error handling
    def ShowCategory(self, categoryId):
        self.log(u"%s" % categoryId, xbmc.LOGDEBUG)

        try:
            html = None
            html = self.httpManager.GetWebPage(allShowsUrl, 20000)
    
            soup = BeautifulSoup(html)
            categoryDiv = soup.find('div', 'category')
            category = categoryDiv.find('section', categoryId)
            articles = category.findAll('article')
    
            listItems = []
    
            labelPattern = "%s (%s)"
            for article in articles:
                showUrl = article.div.a['href']
                thumbnail = urlRoot + article.div.a.img['src']
                label = labelPattern % (article.h1.a.text, article.span.span.text)
    
                urlFragment = "&showUrl=" + mycgi.URLEscape(showUrl)
    
                self.AddShowItem(listItems, label, urlFragment, thumbnail)
                
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # "Error processing '%s' category"
            message = self.language(30108) %categoryId

            exception.addLogMessage(logMessage = message + u"\n" + details)
            exception.process(message, "", self.logLevel(xbmc.LOGERROR))
            return False

    """
                        
                            
                            
                                <section id='A-shows' class='A-shows unavailable'>
                                    <h3 class="section-head">
                                        A</h3>
                                </section>
                            
                        
                            
                                <section id='b-shows' class='b-shows'>
                                    <h3 class="section-head">
                                        B</h3>
                                    <div class="programmes">
                                        
                                                <article>
                                                    <div class="screenshot">
                                                        <a href="/programme/Benidorm">
                                                            <img src='/assets/data/getmediafile.ashx?guid=89f8b210-7ea4-4c0c-8b61-87b0239255eb&maxsidesize=320'
                                                                alt="episode screenshot">
                                                        </a>&nbsp;</div>
                                                    <h1>
                                                        <a href="/programme/Benidorm">
                                                            Benidorm</a></h1>
                                                    <span class="episode-count"><b class="count"><span>
                                                        1</span> </b><span>&nbsp;Episode</span>
                                                    </span>
                                                </article>
                                            
 
    """
    def ShowAtoZ(self):
        self.log(u"", xbmc.LOGDEBUG)

        try:
            html = None
            html = self.httpManager.GetWebPage(allShowsUrl, 20000)
    
            soup = BeautifulSoup(html)
            atozDiv = soup.find('div', 'listings')
            sections = soup.findAll('section', {'class':re.compile( '^[a-zA-Z]-shows')})
            sectionNumeric = soup.find('section', {'class':re.compile( '^0-9-shows')})
            
            if sectionNumeric is not None:
                sections.append(sectionNumeric)
                
            listItems = []
    
            labelPattern = "%s (%s)"

            for section in sections:
                if section['class'].find("unavailable") == -1:
                    articles = section.findAll("article")

                    for article in articles:
                        #TODO try catch
                        showUrl = article.div.a['href']
                        thumbnail = urlRoot + article.div.a.img['src']
                        label = labelPattern % (article.h1.a.text, article.span.span.text)
            
                        urlFragment = "&showUrl=" + mycgi.URLEscape(showUrl)
            
                        self.AddShowItem(listItems, label, urlFragment, thumbnail)
                        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # "Error showing A to Z"
            message = self.language(30109)
            
            exception.addLogMessage(logMessage = message + u"\n")
            exception.process(message, "", self.logLevel(xbmc.LOGERROR))
            return False

    def ListLatest(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        listItems = []

        """
        <div class='day current today' id='date-01032015'
            data-index='30'>
            <a href='#' data-schedule='01-03-2015'>
                        Today</a></div>

        <div class='day current today' id='date-01032015'            data-index='30'>            
            <a href='#' data-schedule='01-03-2015'>                        Today</a>
        </div>
        """

        datePatternFromWeb = u"%m-%d-%Y"
        datePatternUrl = u"%d-%m-%Y"
        
        try:
            url = None
            currentDate = None
            html = None
            html = self.httpManager.GetWebPage(scheduleUrl, 20000)
    
            soup = BeautifulSoup(html)
            todayDiv = soup.find('div', 'today')
            todayDateText = todayDiv.a['data-schedule']
            
            today = date.fromtimestamp(mktime(strptime(todayDateText, datePatternFromWeb)))            
            newLabel = u"Today"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + today.strftime(datePatternUrl)
            listItems.append( (url,newListItem,True) )
            
            # Yesterday
            newLabel = u"Yesterday"
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(1)).strftime(datePatternUrl)
            listItems.append( (url,newListItem,True) )
            
            # Weekday
            newLabel = (today - timedelta(2)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(2)).strftime(datePatternUrl)
            listItems.append( (url,newListItem,True) )
            
            # Weekday
            newLabel = (today - timedelta(3)).strftime(u"%A")
            newListItem = xbmcgui.ListItem( label=newLabel )
            url = self.GetURLStart() + u'&date=' + (today - timedelta(3)).strftime(datePatternUrl)
            listItems.append( (url,newListItem,True) )
    
            currentDate = today - timedelta(4)
            startDateText = "12-31-2014"
            startDate = date.fromtimestamp(mktime(strptime(startDateText, datePatternFromWeb)))

            #TODO Get minus 35 dynamically
            sentinelDate = today - timedelta(31)
            if startDate < sentinelDate:
                startDate = sentinelDate
                
            while currentDate > startDate:
                newLabel = currentDate.strftime(u"%A, %d %B %Y")
                newListItem = xbmcgui.ListItem( label=newLabel )
                url = self.GetURLStart() + u'&date=' + currentDate.strftime(datePatternUrl)
                listItems.append( (url,newListItem,True) )
    
                currentDate = currentDate - timedelta(1) 
        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
            
            if html is not None:
                msg = u"html:\n\n%s\n\n" % html
                exception.addLogMessage(msg)
                
            # "Error creating calendar list"
            message = self.language(30064)
            
            details = ""
            if currentDate is not None:
                details = details + u"currentDate: " + unicode(currentDate) + u", "

            if url is not None:                
                details = details + u"url: " + url
            
            exception.addLogMessage(logMessage = message + u"\n" + details)
            # "Error creating calendar list"
            exception.process(message, "", self.logLevel(xbmc.LOGERROR))
            return False
    
    def ListByDate(self, date):
        self.log(u"", xbmc.LOGDEBUG)

        """
    <section id="schedule" class="inline-content">
        <div class="panel-ui container box">
            <a class="more toggle-unavailable" href="/schedule">Show Unavailable</a>
        </div>
        <div class="container box">
            
                    <article class="scheduled">
                        <div>
                            <!-- clearing div - allows us to free up the :before and :after selectors of .listings div -->
                            <time datetime='01/01/2015 19:25:00'>
                                7:25pm</time>
                            <div class="screenshot">
                                <a href='/programme/welcome-to-utv-ireland/472770'>
                                    <img src='/assets/data/getmediafile.ashx?guid=e3cd3f21-b02d-44ce-8de3-29f10170b975&maxsidesize=320'
                                        alt="episode screenshot">
                                    <span class="play">Play</span> </a>
                            </div>
                            <div class="listing-info">
                                <h1><a
                                            href='/programme/welcome-to-utv-ireland/472770'>
                                    <a href='/programme/welcome-to-utv-ireland/472770'>
                                        Welcome to UTV Ireland</a>
                                </h1>
                                <p>
                                    Welcome to UTV Ireland - the new home for quality entertainment, news and current affairs, drama and documentaries reflecting a modern Ireland.</p>
                            </div>
                            <div class="listing-meta">
                                <span class="duration"><b class="icon-clock"></b>
                                    2m</span> <span class="expiry">
                                        <b class="icon-cal"></b><span>25</span> days</span>
                            </div>
                        </div>
                    </article>
        """
        try:
            html = None
            html = self.httpManager.GetWebPage (scheduleUrl + date, 300)
            
            soup = BeautifulSoup(html)

            section = soup.find('section', {'id':'schedule'})
                
            listItems = []
            
            episodeTitle = None
            articles = section.findAll('article', 'scheduled')
                
            for article in articles:
                listingInfo = article.find('div', 'listing-info')
                
                showTitle = listingInfo.h1.text
                description = listingInfo.p.text
                timeString = article.find('time').text
                
                screenShot = article.find('div', 'screenshot')
                thumbnail = screenShot.find('img')['src']
                
                url = screenShot.a['href']
                
                self.AddEpisodeItem(listItems, showTitle, episodeTitle, description, url, thumbnail, timeString = timeString)
                
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"%s:\n\n%s\n\n" % (urlRoot + url, html)
                exception.addLogMessage(msg)

            # "Error getting list of shows"
            exception.addLogMessage(self.language(30049))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
            

    def ListEpisodes(self, url, showDate = True):
        self.log(u"", xbmc.LOGDEBUG)
        
        """
        <section id="hero">
            <div class="episode-blurb box container">
                <h1 id="mainContent_h1" class="hero-title"><a href="/programme/Coronation-Street">Coronation Street</a></h1>
                <div class="episode-info">
                    
                    <div id="episode-time">
                        <time id="mainContent_time" datetime="02/01/2015 20:30:00"><span class="date-short">2 Jan 8:30pm</span><span class="date-long">Friday 02 Jan 8:30pm</span></time>
                    </div>
                    <p id="mainContent_pCopy">Will David lose his cool with Callum? Roy struggles to accept his verdict. Julie saves the day.</p>
                </div>
                <div class="meta">
                    <span id="mainContent_spanDuration" class="duration"><b class="icon-clock"></b>22m</span><span id="mainContent_spanExpiry"><b class="icon-cal"></b><span>5</span> days</span>
                </div>
            </div>            
            <script type="text/javascript">
                var UTV_player = { _ip: "",
                    playlistRoot: "http://player.utv.ie/advertising/utvplaylist.ashx?contentType=longform;ttID=",
                    flashPlayerID: "3855639428001",
                    flashPlayerKey: "AQ~~,AAACKhr-N7E~,l1SUcGeP_kjBO39p5r10uLH03rkTpOe1",
                    adServerBaseURL: "http://player.utv.ie/advertising/utvplaylist.ashx?ttid=",
                    contentType: "longform",
                    htmlFallback: "False",
                    regionRedirectITV: "http://www.itv.com/itvplayer/video?filter=1%2f0694%2f8546%23001",
                    regionRedirectSTV: "http://player.stv.tv/programmes/?showtitle=Coronation-Street&matid=1%2f0694%2f8546%23001"
                };
            </script>
        
            <div class="screenshot">
                <div class="container" id="player">

                    ...
                    
                    <a href="#" class="image play-video"  data-uid="923cb7fb5cb646c1a2668b5238a7b767" data-bcid="3959966436001" data-georestrictiontype="2" data-adserverurl="http://player.utv.ie/advertising/utvplaylist.ashx?ttid=" data-hideonload="true"><span class="hover-panel"></span><span data-picture data-alt="James Nesbitt's Ireland" class="placeholder">
                        <!-- small img src & retina -->
                        <span data-src='/assets/data/getmediafile.ashx?guid=0700c9ef-c76a-4482-b3c1-06aaadf3a2fd&maxsidesize=320'></span><span data-src='' data-media="only screen and (min-device-pixel-ratio: 2.0)            and (min-width: 320px),
        ...
        
        <section id="more-episodes" class="inline-content">
            <div class="container box">
                <h2 class="section-head">More Episodes</h2>
                <div class="list">
                    
                            <article class="listing ">
                                <div>
                                    <div class="screenshot">
                                        <a href='/programme/Coronation-Street/472739'><span class="hover-panel"></span>
                                            <img src='/assets/data/getmediafile.ashx?guid=6d46d8de-f8e7-4557-ab0c-ab2ba93446f0&maxsidesize=320' alt="episode screenshot">
                                            <span class="play">Play</span> </a>
                                    </div>
                                    <div class="listing-info">
                                        <h1>
                                            
                                            <a href='/programme/Coronation-Street/472739'>
                                                Coronation Street</a>
                                        </h1>
                                        
                                        <time datetime="02/01/2015 19:30:00">
                                            <span class="date-short">
                                                Fri 2 Jan 7:30pm</span><span class="date-long">Friday 02 Jan 7:30pm</span></time>
                                        <p>
                                            David and Eva search for Kylie. Will Roy pay the price for his actions? Sinead is devastated by Alya's blunder.
                                        </p>
                                    </div>
                                    <div class="listing-meta">
                                        <span class="duration"><b class="icon-clock"></b>
                                            22m</span> <span class="expiry">
                                                <b class="icon-cal"></b><span>5</span> days</span>
                                    </div>
                                </div>
                            </article>
                        
                </div>
                
            </div>
        </section>
         """
        
        try:
            html = None
            html = self.httpManager.GetWebPage (urlRoot + url, 300)
            
            soup = BeautifulSoup(html)

            hero = soup.find('section', {'id':'hero'})
            episodeInfo = hero.find('div', 'episode-info')
            
            showTitle = hero.find('', 'hero-title').text
            
            self.log(u"Title: " + showTitle)

            episodeTitle = None
            
            try: 
                episodeTitle = hero.find('', 'summary').text
            except:
                pass
            
            description = episodeInfo.p.text
            dateString = episodeInfo.find('time')['datetime']

            thumbnail = None 
            spans = hero.find('div', 'screenshot').find('a', 'image').findAll('span')
            for span in spans:
                try:
                    dataSrc = span['data-src']
                    if dataSrc != "":
                        thumbnail = urlRoot +  dataSrc
                        break
                    
                    self.log("thumbnail: " % thumbnail, xbmc.LOGDEBUG)
                except:
                    pass
            
            if thumbnail is None:
                self.log("No thumbnail", xbmc.LOGDEBUG)
                
            listItems = []
            self.AddEpisodeItem(listItems, showTitle, episodeTitle, description, url, thumbnail, dateString = dateString)
            
            moreEpisodes = soup.find('section', {'id':'more-episodes'})
            if moreEpisodes is not None:
                episodeTitle = None
                articles = moreEpisodes.findAll('article', 'listing')
                
                for article in articles:
                    listingInfo = article.find('div', 'listing-info')
                    
                    description = listingInfo.p.text
                    dateString = listingInfo.find('time')['datetime']
                    
                    screenShot = article.find('div', 'screenshot')
                    thumbnail = urlRoot + screenShot.find('img')['src']
                    
                    url = screenShot.a['href']
                    
                    self.AddEpisodeItem(listItems, showTitle, episodeTitle, description, url, thumbnail, dateString = dateString)
                    
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"%s:\n\n%s\n\n" % (urlRoot + url, html)
                exception.addLogMessage(msg)

            # "Error getting list of shows"
            exception.addLogMessage(self.language(30049))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
            

    """    
        <section id="hero">
            <div class="episode-blurb box container">
                <h1 id="mainContent_h1" class="hero-title"><a href="/programme/Coronation-Street">Coronation Street</a></h1>
                <div class="episode-info">
                    
                    <div id="episode-time">
                        <time id="mainContent_time" datetime="02/01/2015 20:30:00"><span class="date-short">2 Jan 8:30pm</span><span class="date-long">Friday 02 Jan 8:30pm</span></time>
                    </div>
                    <p id="mainContent_pCopy">Will David lose his cool with Callum? Roy struggles to accept his verdict. Julie saves the day.</p>
                </div>
                <div class="meta">
                    <span id="mainContent_spanDuration" class="duration"><b class="icon-clock"></b>22m</span><span id="mainContent_spanExpiry"><b class="icon-cal"></b><span>5</span> days</span>
                </div>
            </div>            
            <script type="text/javascript">
                var UTV_player = { _ip: "",
                    playlistRoot: "http://player.utv.ie/advertising/utvplaylist.ashx?contentType=longform;ttID=",
                    flashPlayerID: "3855639428001",
                    flashPlayerKey: "AQ~~,AAACKhr-N7E~,l1SUcGeP_kjBO39p5r10uLH03rkTpOe1",
                    adServerBaseURL: "http://player.utv.ie/advertising/utvplaylist.ashx?ttid=",
                    contentType: "longform",
                    htmlFallback: "False",
                    regionRedirectITV: "http://www.itv.com/itvplayer/video?filter=1%2f0694%2f8546%23001",
                    regionRedirectSTV: "http://player.stv.tv/programmes/?showtitle=Coronation-Street&matid=1%2f0694%2f8546%23001"
                };
            </script>
    """
    def ShowEpisode(self, showUrl, resumeFlag):
        self.log(u"url: %s" % (showUrl), xbmc.LOGDEBUG)

        playerIDPattern = 'flashPlayerID: "(\d+)"'
        playerKeyPattern = 'flashPlayerKey: "([^ ]+)"'
        
        # TODO Thumbnail
        # msgid "Getting episode information"
        self.dialog.update(5, self.language(30084))
        try:
            playerUrl = None
            html = None
            playerUrl = urlRoot + showUrl 
            html = self.httpManager.GetWebPage(playerUrl, 20000)

            soup = BeautifulSoup(html)

            hero = soup.find('section', {'id':'hero'})
            script = hero.find('script').text
            
            self.playerId = re.search(playerIDPattern, script).group(1)
            self.playerKey = re.search(playerKeyPattern, script).group(1)

            if self.dialog.iscanceled():
                return False

            self.swfUrl = "http://admin.brightcove.com/viewer/us20141117.1347/connection/ExternalConnection_2.swf"

            if self.dialog.iscanceled():
                return False

            # "Getting stream url"
            self.dialog.update(30, self.language(30087))

            hero = soup.find('section', {'id':'hero'})
            screenShot = hero.find('div', 'screenshot')
            episodeId = screenShot.find('a')['data-bcid']

            spans = screenShot.find('a', 'image').findAll('span')
            for span in spans:
                try:
                    dataSrc = span['data-src']
                    if dataSrc != "":
                        thumbnail = urlRoot +  dataSrc
                        break
                    
                    self.log("thumbnail: " % thumbnail, xbmc.DEBUG)
                except:
                    pass
            
            if thumbnail is None:
                self.log("No thumbnail", xbmc.DEBUG)
                
            
            streamType = unicode(self.addon.getSetting( u'UTV_stream_type' ))
            
            streamUrl = self.GetStreamUrl(self.playerKey, playerUrl, self.playerId, contentId = episodeId, streamType = streamType)
            
            self.publisherId = unicode(int(float(self.amfResponse[u'publisherId']))) 
            self.episodeId = episodeId

            rtmpVar = None
            httpUrl = None
            if streamUrl.upper().startswith("RTMP"):
                rtmpVar = self.GetRTMPVarFromUrl(streamUrl, appFormat, episodeId, pageUrl = urlRoot + showUrl, live = False)
                #self.log("rtmp: %s" % pformat(rtmpVar.getDumpCommand()), xbmc.DEBUG)
            else:
                httpUrl = streamUrl

            mediaDTO = self.amfResponse[u'programmedContent'][u'videoPlayer'][u'mediaDTO']

            (infoLabels, logo, defaultFilename) = self.GetPlayListDetailsFromAMF(mediaDTO)

            return self.PlayOrDownloadEpisode(infoLabels, logo, rtmpVar = rtmpVar, defaultFilename = defaultFilename, url = httpUrl, resumeKey = episodeId, resumeFlag = resumeFlag)

        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"%s:\n\n%s\n\n" % (unicode(playerUrl), html)
                exception.addLogMessage(msg)

            # Error playing or downloading episode %s
            exception.process(self.language(30051) % ' ' , '', self.logLevel(xbmc.LOGERROR))
            return False

    """
        <section id="popular" class=''>
            <div class="container box">
                <div class="panel-ui">
                    <h2 class="section-head">Popular on UTV Player</h2>
                    <a class="more" href="/all-programmes">See all Shows<b class="icon-r-arrow"></b></a>
                </div>
                
                        <article class='popular span6'>
                            <div>
                                <div class="screenshot">
                                    <a href='/programme/Emmerdale/472768'><span class="hover-panel"></span>
                                        
                                        
                                            <img src='/assets/data/getmediafile.ashx?guid=28eeefcf-c037-4994-bceb-ccd3c85d5976&maxsidesize=576'
                                                alt="episode screenshot">
                                            <span data-src='/assets/data/getmediafile.ashx?guid=28eeefcf-c037-4994-bceb-ccd3c85d5976&maxsidesize=768'
                                                data-media="only screen and (min-device-pixel-ratio: 2.0)            and (min-width: 768px),
                                only screen and (   min--moz-device-pixel-ratio: 2)      and (min-width: 768px),
                                only screen and (     -o-min-device-pixel-ratio: 2/1)    and (min-width: 768px),
                                only screen and (        min-device-pixel-ratio: 2)      and (min-width: 768px),
                                only screen and (                min-resolution: 192dpi) and (min-width: 768px),
                                only screen and (                min-resolution: 2dppx)  and (min-width: 768px)"></span>
                                        
                                        <span class="play">Play</span> </a>
                                </div>
                                <div class="listing-info">
                                    <h1>
                                        <span class="new-flag flag-exp">NEW</span>
                                        <a href='/programme/Emmerdale/472768'>
                                            Emmerdale</a>
                                    </h1>
                                    <time datetime="06/01/2015 19:00:00">
                                        <span class="date-short">
                                            Tue 6 Jan 7:00pm</span><span class="date-long">Tuesday 06 Jan 7:00pm</span></time>
                                </div>
                            </div>
                        </article>
                    
    """
    def ListPopular(self):
        try:
            html = None
            html = self.httpManager.GetWebPage (urlRoot, 300)
            
            soup = BeautifulSoup(html)

            section = soup.find('section', {'id':'popular'})
                
            listItems = []
            
            episodeTitle = None
            articles = section.findAll('article', 'popular')
                
            for article in articles:
                listingInfo = article.find('div', 'listing-info')
                
                showTitle = listingInfo.h1.a.text
                dateString = article.find('time')['datetime']
                
                screenShot = article.find('div', 'screenshot')
                thumbnail = screenShot.find('img')['src']
                
                url = screenShot.a['href']
                
                description = None
                self.AddEpisodeItem(listItems, showTitle, episodeTitle, description, url, thumbnail, dateString = dateString)
                
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"%s:\n\n%s\n\n" % (urlRoot, html)
                exception.addLogMessage(msg)

            # "Error getting list of shows"
            exception.addLogMessage(self.language(30049))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
            

    """
        <section id="search-results" class="inline-content">
            
                    <div class="result-set">
                        <div class="program-callout container">
                            <div class="search-listing">
                                <div>
                                    <!-- clearing div - allows us to free up the :before and :after selectors of .listings div -->
                                    <div class="screenshot">
                                        <a href='/programme/pat-kenny-out-with-the-old-in-with-the-u' class="image"><span data-picture data-alt="Pat Kenny: Out With The Old – In With The U"
                                            class="placeholder">
                                            <!-- small img src & retina -->
                                            <span data-src="/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=320">
                                            </span><span data-src="/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=576"
                                                data-media="only screen and (min-device-pixel-ratio: 2.0)            and (min-width: 320px),
                                        only screen and (   min--moz-device-pixel-ratio: 2)      and (min-width: 320px),
                                        only screen and (     -o-min-device-pixel-ratio: 2/1)    and (min-width: 320px),
                                        only screen and (        min-device-pixel-ratio: 2)      and (min-width: 320px),
                                        only screen and (                min-resolution: 192dpi) and (min-width: 320px),
                                        only screen and (                min-resolution: 2dppx)  and (min-width: 320px)"></span>
                                            <!-- med & large img src & retina -->
                                            <span data-src='/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=576'
                                                data-media="(min-width:768px), screen and (min-device-width:768px)"></span><span
                                                    data-src='/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=1024'
                                                    data-media="only screen and (-webkit-min-device-pixel-ratio: 2)      and (min-width:768x), screen and (min-device-width:768px),
                                        only screen and (   min--moz-device-pixel-ratio: 2)      and (min-width:768px), screen and (min-device-width:768px),
                                        only screen and (     -o-min-device-pixel-ratio: 2/1)    and (min-width:768px), screen and (min-device-width:768px),
                                        only screen and (        min-device-pixel-ratio: 2)      and (min-width:768px), screen and (min-device-width:768px),
                                        only screen and (                min-resolution: 192dpi) and (min-width:768px), screen and (min-device-width:768px),
                                        only screen and (                min-resolution: 2dppx)  and (min-width:768px), screen and (min-device-width:768px)">
                                                </span>
                                            <!--[if (lt IE 9) & (!IEMobile)]>
                        <span data-src='/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=768'></span>
                      <![endif]-->
                                            <noscript>
                                                <!-- small img src -->
                                                <img src='/assets/data/getmediafile.ashx?guid=08d96b2f-6a91-4d7c-a610-acdbd1e5be0e&maxsidesize=768'
                                                    alt='Pat Kenny: Out With The Old – In With The U'>
                                            </noscript>
                                        </span></a>
                                    </div>
                                    <div class="listing-info">
                                        <h1>
                                            <a href="/programme/pat-kenny-out-with-the-old-in-with-the-u"><span class="term">Pat Kenny</span>: Out With The Old – In With The U</a>
                                        </h1>
                                        <p>
                                            <span class="term">Pat Kenny</span>: Out With The Old – In With The U mark the much-anticipated return of <span class="term">Pat Kenny</span> to our television screens.</p>
                                    </div>
                                    <span class="episode-count"><b class="count"><span>
                                        1</span> </b>
                                        <span>Episode</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="container box">
                            <div class="list">
                                
                                        <article class="listing ">
                                            <div>
                                                <!-- clearing div - allows us to free up the :before and :after selectors of .listings div -->
                                                <div class="screenshot">
                                                
                                                    <a href='/programme/pat-kenny-out-with-the-old-in-with-the-u/472771'><span class="hover-panel"></span>
                                                        <img src='/assets/data/getmediafile.ashx?guid=29ca7603-13d6-4b74-b2b3-bfe0dd0672a3&maxsidesize=320'
                                                            alt="episode screenshot">
                                                        <span class="play">Play</span> </a>
                                                </div>
                                                <div class="listing-info">
                                                    <h1> <a href='/programme/pat-kenny-out-with-the-old-in-with-the-u/472771'>
                                                            <span class="term">Pat Kenny</span>: Out With The Old – In With The U</a> </h1>
                                                    <time datetime="01/01/2015 20:30:00"><span class="date-short">
                                                Thu 1 Jan 8:30pm</span><span class="date-long">Thursday 01 Jan 8:30pm</span></time>
                                                    <p>
                                                        <span class="term">Pat Kenny</span> travels the length and breadth of the country, meeting with a variety of high-profile personalities, engaging with expert contributors and people with compelling stories to tell.</p>
                                                </div>
                                                <div class="listing-meta">
                                                    <span class="duration"><b class="icon-clock"></b>
                                                        49m</span> <span class="expiry">
                                                            <b class="icon-cal"></b><span>28</span> days</span>
                                                </div>
                                            </div>
                                        </article>
                                    
                            </div>
                            <a class="no-link" href="/programme/pat-kenny-out-with-the-old-in-with-the-u"><span>Showing <span>1 </span>matched episode</span></a>                        
                        </div>
                    </div>
                
        </section>
    """
    def Search(self, searchUrl):
        try:
            html = None
            episodeTitle = None
            html = self.httpManager.GetWebPage (searchUrl, 300)
            
            soup = BeautifulSoup(html)

            resultSets = soup.findAll(u'div', u'result-set')


            listItems = []
            
            for resultSet in resultSets: 
                divListing = resultSet.find(u'div', u'search-listing')
                listingInfo = divListing.find('div', 'listing-info')
                
                showTitle = listingInfo.h1.a.text
                
                self.log(u"Title: " + showTitle)
    
                description = listingInfo.p.text
                #dateString = episodeInfo.find('time')['datetime']
    
                thumbnail = None 
                spans = divListing.find('div', 'screenshot').find('a', 'image').findAll('span')
                for span in spans:
                    try:
                        dataSrc = span['data-src']
                        if dataSrc != "":
                            thumbnail = dataSrc
                    except:
                        pass
                    
                showUrl = listingInfo.h1.a['href']
    
                label = listingInfo.h1.a.text
                urlFragment = "&showUrl=" + mycgi.URLEscape(showUrl)

                self.AddShowItem(listItems, label, urlFragment, thumbnail)
                
                articles = resultSet.findAll('article', 'listing')
                
                for article in articles:
                    listingInfo = article.find('div', 'listing-info')
                    
                    description = listingInfo.p.text
                    dateString = listingInfo.find('time')['datetime']
                    
                    screenShot = article.find('div', 'screenshot')
                    thumbnail = screenShot.find('img')['src']
                    
                    url = screenShot.a['href']
                    
                    self.AddEpisodeItem(listItems, showTitle, episodeTitle, description, url, thumbnail, dateString = dateString)
                        
            xbmcplugin.addDirectoryItems( handle=self.pluginHandle, items=listItems )
            xbmcplugin.endOfDirectory( handle=self.pluginHandle, succeeded=True )
            
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if html is not None:
                msg = u"%s:\n\n%s\n\n" % (urlRoot + url, html)
                exception.addLogMessage(msg)

            # Error performing search
            exception.addLogMessage(self.language(30111))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False
            
        
    def GetRTMPVarFromUrl(self, rtmpUrl, appFormat, episodeId, pageUrl, live):
            # ondemand?videoId=2160442511001&lineUpId=&pubId=1290862567001&playerId=1364138050001&affiliateId=
            app = appFormat % (episodeId, self.publisherId, self.playerId)
            
            # rtmp://cp156323.edgefcs.net/ondemand/&mp4:videos/1290862567001/1290862567001_2666234305001_WCL026718-2-4.mp4
            #rtmpUrl = mediaDTO['FLVFullLengthURL']
            playPathIndex = rtmpUrl.index(u'&') + 1
            playPath = rtmpUrl[playPathIndex:]
            rtmpUrl = rtmpUrl[:playPathIndex - 1]
            rtmpVar = rtmp.RTMP(rtmp = rtmpUrl, playPath = playPath, app = app, swfVfy = self.swfUrl, tcUrl = rtmpUrl, pageUrl = pageUrl, live = live)
            self.AddSocksToRTMP(rtmpVar)
            
            return rtmpVar
            
    def GetPlayListDetailsFromAMF(self, mediaDTO):

            longDescription = mediaDTO[u'longDescription']
                
            if longDescription is None:
                longDescription = mediaDTO[u'shortDescription']
                    
            # Set up info for "Now Playing" screen
            infoLabels = {
                          u'Title': mediaDTO[u'displayName'],
                          u'plot': mediaDTO[u'shortDescription'],
                          u'plotOutline': longDescription
                          #u'tvshowtitle': mediaDTO[u'customFields'][u'seriestitle'],
                         # u'aired': mediaDTO[u'customFields'][u'date']
                          }
            
            logo = mediaDTO[u'videoStillURL']
            defaultFilename = mediaDTO[u'displayName']
            
            return (infoLabels, logo, defaultFilename)


    def GetAmfClassHash(self, className):
        self.log("className: " + className, xbmc.LOGDEBUG)

        if className == "com.brightcove.experience.ExperienceRuntimeFacade":
	        return u'3630d914b8aacd9468ca293d1bba84e44db3aa0c'

        
    def DoSearchQuery( self, query):
        queryUrl = searchUrl % mycgi.URLEscape(query)
             
        self.log(u"queryUrl: %s" % queryUrl, xbmc.LOGDEBUG)
        
        return self.Search(queryUrl)
