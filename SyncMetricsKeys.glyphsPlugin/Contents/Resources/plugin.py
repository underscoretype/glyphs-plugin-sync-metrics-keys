# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###############################################################################
#
#
#	Sync Metrics Keys
#
#   A simple Plugin for Glyphs App to keep referenced side bearings in sync
#   Install > View > Show Sync Metrics Keys
#
#   (c) Johannes "kontur" Neumeier 2017-2021
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
import re, objc

class MetricsAutoUpdate(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({
            'en': 'Sync Metrics Keys', 
            'de': 'Metrics synchronisieren',
            'es': 'Sincronizar metrics',
            'fr': 'Synchroniser metrics'
        })


    @objc.python_method
    def start(self):

        self.logging = True

        # Values to keep track of
        self.currentLayer = False
        self.currentLSB = False
        self.currentRSB = False
        self.currentTSB = False
        self.currentBSB = False
        self.currentWidth = False
        self.currentVertWidth = False

        self.isMouseDown = False

        menuItem = NSMenuItem(self.name, self.toggleMenu_)
        menuItem.setState_(bool(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]))
        Glyphs.menu[GLYPH_MENU].append(menuItem)

        self.log("Menu state")
        self.log(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"])

        if Glyphs.boolDefaults["com.underscoretype.SyncMetricsKeys.state"]:
            self.addCallbacks()

        self.log("Sync Metrics Keys Start")


    # use local debugging flag to enable or disable verbose output
    @objc.python_method
    def log(self, message):
        if self.logging:
            self.logToConsole(message)


    @objc.python_method
    def toggleMenu_(self, sender):
        self.log("Toggle menu")
        self.log(Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"])

        if Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]:
            Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"] = False
            self.removeCallbacks()
        else:
            Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"] = True
            self.addCallbacks()

        currentState = Glyphs.defaults["com.underscoretype.SyncMetricsKeys.state"]
        Glyphs.menu[GLYPH_MENU].submenu().itemWithTitle_(self.name).setState_(currentState)


    @objc.python_method
    def addCallbacks(self):
        self.log("Add callback")
        try:
            Glyphs.addCallback(self.syncMetricsKeys, DRAWFOREGROUND)
            self.log("Registered sync callback")

            Glyphs.addCallback(self.mouseUp, MOUSEUP)
            self.log("Registered mouse up callback")

            Glyphs.addCallback(self.mouseDown, MOUSEDOWN)
            self.log("Registered mouse down callback")
        except Exception as e:
            self.log("Exception: %s" % str(e))


    @objc.python_method
    def removeCallbacks(self):
        self.log("Remove callback")
        try:
            Glyphs.removeCallback(self.syncMetricsKeys, DRAWFOREGROUND)
            self.log("Removed sync callback")

            Glyphs.removeCallback(self.mouseUp, MOUSEUP)
            self.log("Removed mouse up callback")

            Glyphs.removeCallback(self.mouseDown, MOUSEDOWN)
            self.log("Removed mouse down callback")
        except Exception as e:
            self.log("Exception: %s" % str(e))


    @objc.python_method
    def mouseUp(self, info):
        self.isMouseDown = False


    @objc.python_method
    def mouseDown(self, info):
        self.isMouseDown = True


    # use the foreground drawing loop hook to check if metrics updates are required
    @objc.python_method
    def syncMetricsKeys(self, layer, info):

        # While the mouse is being held down we do not sync, so that dragging
        # paths beyond the sidebearing does not constantly retrigger (which
        # makes drawing hard)
        if self.isMouseDown:
            return

        # If the layer was switched, set new current values to check against
        if layer != self.currentLayer:
            self.log("New active layer")

            if self.layerHasContent(layer):
                # For a start, sync, but only if there is stuff in this layer
                layer.syncMetrics()

            # Reset this, to be sure it was not somehow left "pressed", which
            # would block all future sync
            self.isMouseDown = False

            self.currentLayer = layer
            self.currentLSB = layer.LSB
            self.currentRSB = layer.RSB
            self.currentTSB = layer.TSB
            self.currentBSB = layer.BSB
            self.currentWidth = layer.width
            self.currentVertWidth = layer.vertWidth

            # Sync all other glyphs, in case the initial syncing of this layer
            # changed things
            self.syncAll()

        # Do not sync when there is no geometry, as this will just infinitely
        # grow the width of the glyph!
        if not layer.paths and not layer.components:
            self.log("Glyph has no geometry, skip syncing")
            return

        if self.currentLSB != layer.LSB or self.currentRSB != layer.RSB or \
            self.currentWidth != layer.width or \
            self.currentTSB != layer.TSB or self.currentBSB != layer.BSB or \
            self.currentVertWidth != layer.vertWidth:

            self.log("Sync metrics changes")

            # Update the values for comparison
            self.currentLSB = layer.LSB
            self.currentRSB = layer.RSB
            self.currentTSB = layer.TSB
            self.currentBSB = layer.BSB
            self.currentWidth = layer.width
            self.currentVertWidth = layer.vertWidth

            self.log("Active layer sidebearings: %s | %s" % (str(layer.LSB), str(layer.RSB)))

            self.syncAll()

    @objc.python_method
    def layerHasContent(self, layer):
        return len(layer.paths) > 0 or len(layer.components)

    @objc.python_method
    def syncAll(self):
        for g in Glyphs.font.glyphs:
            for l in g.layers:
                l.beginChanges()
                if l.metricsKeysOutOfSync() == 1 and self.layerHasContent(l):
                    self.log("Layer was out of sync, update linked metrics %s" % str(l))
                    l.syncMetrics()
                    self.log("Updated layer metrics of %s to %s | %s" % (str(l), str(l.LSB), str(l.RSB)))
                l.endChanges()
        Glyphs.redraw()
        self.log("REDRAW")

