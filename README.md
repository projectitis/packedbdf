# packedbdf
Packed BDF font helpers and code

**Packed BDF** is a compact binary format of BDF. `packedbdf_t` or `ILI9341_t3_font_t` is one of the font formats used when programming the Teensy USB-based microcontroller development boards. Version 1 of the format packs glyph pixels as individual bits. It does not support anti-aliasing, but it allows maximum efficiency of data, especially for smaller fonts. Version 23 (numbered for BDF v2.3) extends the format to allow for 4, 16 and 256 levels of anti-aliasing (2, 4 and 8 bits respectively).

Libraries that currently support Packed BDF are:
- [ILI9341_t3](https://github.com/PaulStoffregen/ILI9341_t3) (v1 only - [v23/anti-alias font branch here](https://github.com/projectitis/ILI9341_t3/tree/anti-alias-fonts)).
- [ILI9341_t3n](https://github.com/KurtE/ILI9341_t3n) (both v1 and v23)
- [ILI9341_t3DMA](https://github.com/FrankBoesing/ILI9341_t3DMA) (v1 only)

There are two steps to creating a Packed BDF file. These are detailed below:

- Download the fonts you want to convert as ttf or otf
- Create the BDF font from a True Type or Freetype font (ttf or otf)
- Convert the BDF file to a header file

### BDF
[From Wikipedia](https://en.wikipedia.org/wiki/Glyph_Bitmap_Distribution_Format): The **Glyph Bitmap Distribution Format** (BDF) by Adobe is a file format for storing bitmap fonts. The content takes the form of a text file intended to be human- and computer-readable. BDF is typically used in Unix X Window environments. It has largely been replaced by the PCF font format which is somewhat more efficient, and by scalable fonts such as OpenType and TrueType fonts.

## 1 of 3: Download the fonts you want to convert
If you don't already have the fonts you want, [Google Fonts](https://fonts.google.com/) is a fantastic source. It's up to you to make sure that the licence for teh font allows for what you are going to use it for.

## 2 of 3: Convert .ttf or .otf to BDF files using Font Forge
These instructions are for how to create BDF files using the [Font Forge open source font editor](https://fontforge.github.io/en-US/). Font Forge is free and has [downloads](https://fontforge.github.io/en-US/downloads/) for Windows, Mac and Linux.

1) Download and install [Font Forge](https://fontforge.github.io/en-US/downloads/)
2) Launch Font Forge and open the font file (ttf or otf)
3) Select all the glyphs that you want in your font - usually 32 to 126 (inclusive)
4) _Edit > Select > Invert_ the selection, and
4) _Encoding > Detach and remove Glyphs_ to remove them from the font
5) _Encoding > Compact_ to reduce the character set

The next few steps will generate the bitmaps/pixel versions of each glyph in teh sizes that you need:

6) _Element > Bitmap strikes available_ launches the dialog to generate the bitmat versions
7) Enter the sizes that you need, seperated by commas. These can be specified as point sizes or pixel sizes (in different text boxes)
    - For non anti-alias fonts (v1), simply enter the font sizes. E.g. "8,9,10,12,16"
    - For anti-alias fonts (v23), enter the font sizes, each followed by '@' and then the number of bits per pixel. E,g, 8@4,9@4,10@4,12@4
    - Use @2 for 4 levels of anti-alias, @4 for 16 levels, and @8 for 255
    - The resulting font is much bigger the higher you go. In practice I've found that @2 actually gives very decent results
8) Click _[OK]_ to generate the bitmap strikes of each glyph in various sizes
9) Use _View > ## pixel bitmap_ options to view the bitmap strikes that were generated
10) Any glyphs that aren't perfect can be edited individually before saving
11) Finally, select _File > Generate Fonts_. Select "No outline font" (for Outline font) and "BDF" (for Bitmap font), then hit [Generate]. A seperate BDF file for each size will be generated.

## 3 of 3: Convert the BDF files to Packed BDF
There are two python scripts to convert the BDF files to packed BDF format. The python scripts are based on [bdf_to_ili9341.c](https://github.com/PaulStoffregen/ILI9341_t3/blob/master/extras/bdf_to_ili9341.c) by Paul Stoffregen.

1) If you haven't already, [install Python](https://www.python.org/downloads/) on your system
2) Now double-click either of these two files, depending on what you want:
    - `bdf_to_h.py` - this will create a seperate .h file for each BDF file
    - `bdf_to_h_combined.py` - all BDF fonts with the same name combined into the same .h file (with multiple sizes) 

## Error: packedbdf_t unrecognised
If your compiled throws an error about not recognising packedbdf_t, add this to your code (usually immediately following the definition of ILI9341_t3_font_t:
`typedef ILI9341_t3_font_t packedbdf_t;`
