# Sync Metrics Keys (v 0.2.0)

A simple Plugin for [Glyphs App](https://glyphsapp.com) to always keep referenced side bearings in sync while editing glyphs. This syncs the current glyph's side bearings while moving paths or components, but also updates all glyphs that have references to the current glyph in their side bearings.

Install, then in the menu bar activate under: Glyph > Sync Metrics Keys

## Changelog

### v 0.2.0
- Simplified the codebase and improved performance
- Removed support for metrics key chains since it is more advisable to avoid these kinds of setups to begin with (e.g. `o` referenced by `q` LSB referenced by `d` LSB will not sync `d` on `o` update - both `q` and `d` should reasonably just use `o` as their LSB :) )
- Fixed issue where moving the side-most nodes in a glyph referencing another sidebearing would jump the UI around and constantly update while moving the nodes
- Added TSB and BSB references to also update
- Plugin compatible with Glyphs 3 (Thanks Georg Seifert!)

### v 0.1.1
- Fixed compatibility issue with newer Glyphs App version (1103) that prevented the plugin menu from displaying correctly


## Thanks
- [Justin Kerr Sheckler](https://github.com/jayKayEss) for improved key matching
- [Georg Seifert](https://github.com/schriftgestalt) for code fixes and samples
- [Rainer Erich Scheichelbauer](https://github.com/mekkablue) for code samples

(c) Johannes "kontur" Neumeier 2017-2021, Underscore Type