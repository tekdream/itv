# -*- coding: utf-8 -*-
import xbmc
from xbmc import log
from xbmcaddon import Addon
from loggingexception import LoggingException

from rte import RTEProvider
from tv3 import TV3Provider
from aertv import AerTVProvider
from tg4 import TG4Provider
from utv import UTVProvider
# Provider names

global __providers__
global __providerList__
__providers__ = None
__providerList__ = None

def getProviders():
    global __providers__
    global __providerList__
    if __providers__ is None:
        log("Initalise providers", xbmc.LOGDEBUG)
        __providerList__ = [RTEProvider(), TV3Provider(), AerTVProvider(), TG4Provider(), UTVProvider()]

        __providers__ = {}
        for provider in __providerList__:
            __providers__[provider.GetProviderId()] = provider

    return __providers__, __providerList__
    

def getProvider(id):
    log("ProviderFactory(" + str(id) + ")", xbmc.LOGDEBUG)

    providers, list = getProviders()
    if id in providers:
		return providers[id]
	
    return None

def getProviderList():
    providers, list = getProviders()
    return list
