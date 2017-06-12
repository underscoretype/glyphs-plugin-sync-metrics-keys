# encoding: utf-8

###########################################################################################################
#
#
#	Sync Metrics Keys
#
#   A simple Plugin for Glyphs App to keep referenced side bearings in sync
#   Install > View > Show Sync Metrics Keys
#
#   (c) Johannes "kontur" Neumeier 2017
#
#
###########################################################################################################


from GlyphsApp.plugins import *
import re

class MetricsAutoUpdate(ReporterPlugin):


    def settings(self):
        # setting the visible name, displayed as "Show Sync Metrics Key"
        # semantically, using the ReporterPlugin for this functionablity is incorrect,
        # but it allows for easy toggling
        self.menuName = 'Sync Metrics Keys'


    def start(self):
        # no logging in production version
        self.logging = False

        # variables used to determine when to trigger and update that needs to
        # be propagated to other glyphs
        self.lastGlyph = None
        self.lastLSB = None
        self.lastRSB = None

        self.glyphsWithoutMetricsKeys = []
        self.glyphsCached = False

        self.log("Start")


    # use local debugging flag to enable or disable verbose output
    def log(self, message):
        if self.logging:
            self.logToConsole(message)
        

    def updateMetrics(self, layer):
        self.log("updateMetrics")
        glyph = layer.parent

        # check if the current glyph is a metrics key in other glyphs, and if so, update them

        # TODO note that this is not recursive; if h references n, but b references h, 
        # editing n will not update b, because it does not reference n directly
        linkedGlyphs = self.findGlyphsWithMetricsKey(glyph)
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


    # not differentiating here between left or right
    # if either side is a reference, return it for processing
    def findGlyphsWithMetricsKey(self, key):
        self.log("findGlyphsWithMetricsKey")
        referencedGlyphs = []
        try:
            for glyph in Glyphs.font.glyphs:
                self.log("Check %s linked %s (metric keys: %s, %s)?" % (glyph.name, key.name, glyph.leftMetricsKey, glyph.rightMetricsKey))

                if glyph.name is key.name:
                    # skip checking sidebearing keys for the glyph of same name, obviously
                    continue

                if glyph in self.glyphsWithoutMetricsKeys:
                    self.log("Skipping %s without metrics keys" % str(glyph.name))
                    continue

                # looking for a reference to the key in the glyph's metrics keys us a regular
                # expression that looks for the key only when next to non-alphabetic character
                # i.e. when used in formulas, like =n-20 or =|n, but will not match when the
                # key has other alphabetic characters next to it, like not matching key n in value ntilde
                # adding re.MULTILINE will match the $ end of line before the "non-alphabetic", which
                # isn't satisfied by "end of line/string" otherwise
                regex = "[^a-zA-Z]*(" + re.escape(key.name) + ")+[^a-zA-Z]*"
                pattern = re.compile(regex)

                # also match if the key and the reference simply are equal (no equations used)
                # LSB
                if glyph.leftMetricsKey is not None:
                    if pattern.search(glyph.leftMetricsKey) is not None or glyph.leftMetricsKey == key.name:
                        self.log("LSB links")
                        referencedGlyphs.append(glyph)

                # RSB
                if glyph.rightMetricsKey is not None:
                    if pattern.search(glyph.rightMetricsKey) is not None or glyph.rightMetricsKey == key.name:
                        self.log("RSB links")
                        referencedGlyphs.append(glyph)

        except Exception as e:
            self.log("Error: %s" % str(e))

        self.log(referencedGlyphs)

        return referencedGlyphs


    # Helper to check if a glyph has metric keys
    def glyphHasMetricsKeys(self, glyph):
        if glyph.leftMetricsKey is not None or glyph.rightMetricsKey is not None:
            return True
        else:
            return False


    # Helper function to store all glyphs that won't need to be updated because
    # they don't have any metrics keys in their left or right sidebearings
    def cacheAllGlyphKeys(self):
        for glyph in Glyphs.font.glyphs:
            if glyph.leftMetricsKey is None and glyph.rightMetricsKey is None:
                self.glyphsWithoutMetricsKeys.append(glyph)

        self.log("Cached glyphs without metrics keys")
        self.log(self.glyphsWithoutMetricsKeys)
        self.glyphsCached = True

        return


    # Helper to sync this glyph's metric keys with the cache
    # If it has no metrics keys, but is not in the cache, remove it
    # If it has metrics keys, but is in the cache, remove it
    def cacheGlyphKeys(self, glyph):
        self.log("cacheGlyphKeys for %s" % str(glyph.name))
        if self.glyphHasMetricsKeys(glyph):
            if glyph in self.glyphsWithoutMetricsKeys:
                self.glyphsWithoutMetricsKeys.remove(glyph)
        else: 
            if not glyph in self.glyphsWithoutMetricsKeys:
                self.glyphsWithoutMetricsKeys.append(glyph)


    # use the foreground drawing loop hook to check if metrics updates are required
    def foreground(self, layer):
        glyph = layer.parent
        update = False

        # On the first go around cache all glyph keys
        if self.glyphsCached is False:
            self.cacheAllGlyphKeys()
        else:
            self.cacheGlyphKeys(glyph)

        # Only update when the current layer is a real drawing layer (master, or layer
        # in the sidebar panel) - i.e. don't react to an active  GSBackgroundLayer type
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
            if (glyph.leftMetricsKey is not None and self.lastLSB != layer.LSB) or (glyph.rightMetricsKey is not None and self.lastRSB != layer.RSB):
                self.log("Same glyph, changed metrics")
                self.lastLSB = layer.LSB
                self.lastRSB = layer.RSB
                layer.syncMetrics()

        if update:
            self.updateMetrics(layer)
