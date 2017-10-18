# Sync Metrics Keys (v.0.1.0)

A simple Plugin for [Glyphs App](https://glyphsapp.com) to keep referenced side bearings in sync while editing glyphs. This syncs the current glyph's side bearings while moving nodes, but also updates all glyphs that have references to the current glyph in their side bearings.

Install, then in the menu bar: Glyph > Sync Metrics Keys

## Planned features
- Updating glyph metrics also when changes are made outside the Editor view
- Iterative syncing of indirectly affected glyphs

## Known issues
- Moving the side-most node with your mouse can be tricky, since the plugin immediately syncs linked metrics
- Automated syncing of the metrics creates a editing history entry, making certain undo actions hard without temporarily disabling the metrics syncing from the Glyph > Sync Metrics Keys menu

## Thanks
- (Justin Kerr Sheckler)[https://github.com/jayKayEss] for improved key matching

(c) Johannes "kontur" Neumeier 2017, UnderscoreType