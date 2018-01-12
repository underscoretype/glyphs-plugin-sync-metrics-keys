# encoding: utf-8

###########################################################################################################
#
#
#	Sync Metrics Keys
#
#   A simple Plugin for Glyphs App to keep referenced side bearings in sync
#   Install > View > Show Sync Metrics Keys
#
#   (c) Johannes "kontur" Neumeier 2017-2018
#
#
#   My thanks for a plentitude of code examples borrowed from:
#   - Georg Seifert (@schriftgestalt) https://github.com/schriftgestalt/GlyphsSDK
#   - Rainer Erich Scheichelbauer (@mekkablue) https://github.com/mekkablue/SyncSelection
#
#
###########################################################################################################


from GlyphsApp.plugins import *
from GlyphsApp import *
import re

class MetricsAutoUpdate(GeneralPlugin):

    def settings(self):
        self.name = Glyphs.localize({
            'en': u'Sync Metrics Keys', 
            'de': u'Metrics synchronisieren',
            'es': u'Sincronizar metrics',
            'fr': u'Synchroniser metrics'
        })

        NSUserDefaults.standardUserDefaults().registerDefaults_(
            {
                "com.underscoretype.SyncMetricsKeys.state": False
            }
        )


    def start(self):
        try:
            # no logging in production version
            self.logging = False

            # variables used to determine when to trigger and update that needs to
            # be propagated to other glyphs
            self.lastGlyph = None
            self.lastLSB = None
            self.lastRSB = None

            self.glyphsCached = False
            self.cache = {}

            menuItem = NSMenuItem(self.name, self.toggleMenu)
            menuItem.setState_(bool(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]))
            Glyphs.menu[GLYPH_MENU].append(menuItem)
        
        except Exception as e:
            self.log("Registering menu entry did not work")
            self.log("Exception: %s" % str(e))


        self.log("Menu state")
        self.log(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"])

        if Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]:
            self.addSyncCallback()

        self.log("Sync Metrics Keys Start")


    # use local debugging flag to enable or disable verbose output
    def log(self, message):
        if self.logging:
            self.logToConsole(message)
    

    def toggleMenu(self, sender):
        self.log("Toggle menu")
        self.log(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"])

        if Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]:
            Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"] = False
            self.removeSyncCallback()
        else:
            Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"] = True
            self.addSyncCallback()
        
        currentState = Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]
        Glyphs.menu[GLYPH_MENU].submenu().itemWithTitle_(self.name).setState_(currentState)


    def addSyncCallback(self):
        self.log("Add callback")
        try:
            Glyphs.addCallback(self.syncMetricsKeys, DRAWFOREGROUND)
            self.log("Registered callback")
        except Exception as e:
            self.log("Exception: %s" % str(e))
    

    def removeSyncCallback(self):
        self.log("Remove callback")
        try:
            Glyphs.removeCallback(self.syncMetricsKeys, DRAWFOREGROUND)
            self.log("Removed callback")
        except Exception as e:
            self.log("Exception: %s" % str(e))


    def updateMetrics(self, layer):
        self.log("updateMetrics")
        glyph = layer.parent

        # check if the current glyph is a metrics key in other glyphs, and if so, update them

        # TODO note that this is not recursive; if h references n, but b references h, 
        # editing n will not update b, because it does not reference n directly
        
        if not glyph.name in self.cache:
            self.log("No links to key %s" % str(glyph.name))
            return

        linkedGlyphs = self.cache[glyph.name]
        self.log("LinkedGlyphs from cache")
        self.log(linkedGlyphs)
        if len(linkedGlyphs) > 0:
            for linkedGlyph in linkedGlyphs:
                self.syncGlyphMetrics(linkedGlyph)


    # shortcut for syncing the metrics in THE ACTIVE MASTER's layers in a glyph
    def syncGlyphMetrics(self, glyph):
        self.log("syncGlyphMetrics for %s" % str(glyph.name))
        try:
            layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
            layer.syncMetrics()

        except Exception as e:
            self.log("Error: %s" % str(e))


    # Helper to check if a glyph has metric keys
    def glyphHasMetricsKeys(self, glyph):
        if glyph.leftMetricsKey is not None or glyph.rightMetricsKey is not None:
            return True
        else:
            return False


    def getGlyphMetricsKeys(self, glyph):
        self.log("getGlyphMetricsKeys for %s" % str(glyph.name))
        links = []

        # Improved key matching regex thanks to Justin Kerr Sheckler from
        # https://github.com/jayKayEss/MetricsSolver/blob/master/
        # MetricsSolver.glyphsPlugin/Contents/Resources/matcher.py#L5
        pattern = re.compile(r"(\.?[A-Z]+(?:[.\-_][A-Z]+)*)", re.IGNORECASE)

        if glyph.leftMetricsKey is not None:
            for match in re.findall(pattern, glyph.leftMetricsKey):
                self.log("match in left: %s" % str(match))
                links.append(match)

        if glyph.rightMetricsKey is not None:
            for match in re.findall(pattern, glyph.rightMetricsKey):
                self.log("match in right: %s" % str(match))
                links.append(match)

        return links


    # Helper function to store all glyphs that won't need to be updated because
    # they don't have any metrics keys in their left or right sidebearings
    def cacheAllGlyphKeys(self):
        for glyph in Glyphs.font.glyphs:
            self.cacheGlyphKeys(glyph)

        self.glyphsCached = True

        return


    def cacheGlyphKeys(self, glyph):
        # as part of caching this glyph and it's links, first remove it
        # from any existing keys it might be linked in
        self.purgeLinkFromCache(glyph)

        # if this glyph has metrics keys, they need to be cached to the 
        # appropiate keys
        if not glyph.leftMetricsKey is None or not glyph.rightMetricsKey is None:
            # if a glyph has metrics links, iterate them and make sure any
            # referenced keys will trigger an update for this glyph when they
            # get changed
            links = self.getGlyphMetricsKeys(glyph)
            if len(links) > 0:
                for link in links:
                    # if the key does not exist in the cache, create it first
                    if link not in self.cache:
                        self.cache[link] = []

                    # then add this glyph to be updated when the key-glyph 
                    # changes   
                    if glyph not in self.cache[link]:
                        self.cache[link].append(glyph)


    def purgeLinkFromCache(self, glyph):
        self.log("purge %s from cache links" % str(glyph.name))
        self.log(self.cache)
        for key, links in self.cache.iteritems():
            for link in links:
                if link == glyph:
                    self.log("remove link for %s fro key %s" % (str(glyph.name), str(key)))
                    links.remove(glyph)


    # use the foreground drawing loop hook to check if metrics updates are required
    def syncMetricsKeys(self, layer, info):
        glyph = layer.parent
        update = False

        # if there are no nodes nor components in the layer (e.g. it is empty)
        # don't try to sync sidebearing as this will infinitely grow the sidebearings
        if not layer.paths and not layer.components:
            return

        # On the first go around cache all glyph keys
        if self.glyphsCached is False:
            self.cacheAllGlyphKeys()

        # Only update when the current layer is a real drawing layer (master, or layer
        # in the sidebar panel) - i.e. don't react to an active GSBackgroundLayer type
        if layer.className() != "GSLayer":
            return

        # Only trigger an update to other glyphs if this glyph's LSB or RSB really change
        if glyph.name != self.lastGlyph or self.lastGlyph is None:
            self.log("New active glyph %s" % str(layer.parent))
            self.lastGlyph = glyph.name

            # Only even make it possible to trigger an update if the glyph has
            # numeric LSB or RSB, not a metrics key
            # if numeric, go ahead and check with last active value            
            if layer.LSB is not None:
                if self.lastLSB != layer.LSB:
                    if glyph.leftMetricsKey is None:
                        self.lastLSB = layer.LSB
                        update = True
                    else:
                        # not an update to other glyphs, but refresh this glyphs
                        # references metrics key value
                        layer.syncMetrics()

            if layer.RSB is not None: 
                if self.lastRSB != layer.RSB:
                    if glyph.rightMetricsKey is None:
                        self.lastRSB = layer.RSB
                        update = True
                    else:
                        # not an update to other glyphs, but refresh this glyphs
                        # references metrics key value
                        layer.syncMetrics()
        else:
            if (self.lastLSB != layer.LSB) or (self.lastRSB != layer.RSB):
                self.log("Same glyph, changed metrics")
                self.lastLSB = layer.LSB
                self.lastRSB = layer.RSB
                layer.syncMetrics()
                update = True

        if update:
            # before propagating an update to other linked glyphs update 
            # the caching, so that potential linking / unlinking of this glyph
            # to other keys gets taken into account
            self.cacheGlyphKeys(glyph)

            self.updateMetrics(layer)
