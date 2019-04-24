# Packed BDF font format
Packed BDF (`packedbdf_t` or `ILI9341_t3_font_t`) is a font format based on BDF for use in c/c++ applications - most notably for the [Teensy](https://www.pjrc.com/teensy/) microprocessor development boards.

---
## Terminology
* **anti-alias (AA)** - Anti-aliasing is the process of adding semi-transparent pixels along a jagged edge of a line to make it appear smooth.
* **BDF** - [Glyph Bitmap Distribution Format (BDF)](https://en.wikipedia.org/wiki/Glyph_Bitmap_Distribution_Format) is a font format originally developed by Adobe to represent a bitmap font in a computer- and human- readable format. A BDF file is a text file which describes various properties of teh font and contains data for each of the glyphs.
* **bits per pixel (bpp)** - The number of bits used to represent a single pixel. 1bpp means 1 bit is used to represent a pixel, and it can be either 0 (off) or 1 (on). More than 1bpp means the font supports 'levels of grey', or anti-aliasing. For example, 2bpp means the font supports 4 levels of anti-alias (0,33%,66%,100%).
* **ILI9341_t3_font_t** - is a font format created by Paul Stoffregen based on a subset of the BDF data, packed into a tight data structure. It is intended to create very small font files that can be used on embedded devices - specifically the [Teensy](https://www.pjrc.com/teensy/) microprocessor development boards.

---
## Definition
```
typedef struct {
	const unsigned char *index;
	const unsigned char *unicode;
	const unsigned char *data;
	unsigned char version;
	unsigned char reserved;
	unsigned char index1_first;
	unsigned char index1_last;
	unsigned char index2_first;
	unsigned char index2_last;
	unsigned char bits_index;
	unsigned char bits_width;
	unsigned char bits_height;
	unsigned char bits_xoffset;
	unsigned char bits_yoffset;
	unsigned char bits_delta;
	unsigned char line_space;
	unsigned char cap_height;
} ILI9341_t3_font_t;

typedef ILI9341_t3_font_t packedbdf_t
```
---
## Explanation
Most of this explanation is taken from [Paul's description on the PJRC forums](https://forum.pjrc.com/threads/54316-ILI9341_t-font-structure-format?p=191131&viewfull=1#post191131) with changes based on spook's experiences as well as my own.

#### Type structure
Each font has 3 parts.
1. Metadata in a packedbdf_t struct
2. Font bitmap data
3. An index into the bitmap data for each character

### index
**Also see** _bits_index_
The index is an array of numbers that specifiy the byte index of each glyph within the _data_. The size of each number (i.e. how many bits each number takes up) is specificed by _bits_index_ in the metadata. Even though the index type is 8-bit unsigned, each number in the index is actually bit-packed, and each number in the the index may not line up on a byte boundary.
Each index number is an offset in _bytes_ (not bits) to the data for a specific glyph. The data for each individual glyph is aligned to a byte boundary within _data_.
The entire index is padded to the nearest byte boundary, so any left-over bits are filled with 0 to the byte-boundary, and are ignored when processing the font.

### unicode
Currently unsupported. Intended for future unicode support.

### data
**Also see** - _bits_width, bits_height, bits_xoffset, bits_yoffset, bits_delta_
An array of bit-packed glyph data. As with index, even though the type of this array is unsigned 8-bit, the data is actually bit-packed and each number may not line up with a byte-boundary. There are slight differences between the _data_ format for AA (version 23) and non-AA (version 1) fonts.

##### data - version 1
The data for each character is byte-aligned. Each character begins with 6 fields. The first 3 bits are `reserved` and must be all 0s. This 3 bit field was meant to allow other ways to encode the character.

The `width` and `height` of the character are next. The `xoffset` and `yoffset` follow. These offset numbers allow offseting the drawing of the character (useful for fancy fonts, or descenders like lowercase 'j' and 'g'). The `delta` number tells how many pixels to advance the cursor position after drawing the glyph.

The raw bitmap `data` follows these 6 fields. It follows immediately after the 6 fields and is not byte aligned. For each row of pixels in the glyph, a single bit is read first. If that first bit is a `0`, then whatever bits follow are the raw bitmap data for that row (number of pixels to read = `width`). If the first bit is `1` then the following 3 bits indicate how many times to repeat the _following_ row (_n_+1). For example, if the first bit is 1 and the 3-bit number is 5, this means repeat the following row of data 6 times (_n_+1). Each pixel in the data is a single bit. 0 = no pixel, 1 = draw a pixel.

##### data - version 23
Anti-aliased fonts use the same structure as above, with these exceptions: After the `delta` number, the `data` is aligned to the next byte boundary (if it isn't on one already). So after the delta bits there may be more 0 bits to pad to the next byte-boundary. This ensures that the pixel data align with a byte boundary, Secondly, line repititions are **not** supported. The data simply contains the pixel data for row of pixels, using the correct bits per pixel as specified by the `bpp` for the font (see _reserved (bpp)_).

### version
**Also see** _description of differences_
The Packed BDF format version number, indicating the format of teh font stored in the data. There are currently two versions in use. `version=1` relates to the original 1bpp specification that does not support anti-aliasing. `version=23` relates to an extension to BDF called v2.3 which supports ant-aliasing. The type data structure for v1 and v23 are identical, but the way the glyph data is packed within the structure differs between the two. 

### reserved (bpp)
**Version 1** - This byte is not used, and should be set to `0`.
**Version 23** - The lower two bits of this byte represent the number of bits per pixel. The possible values are `0=1bpp`, `1=2bpp`, `2=4bpp` and `3=8bpp`.

### index1_first, index1_last
These indicate the character codes that the font implements. There can be two ranges (`index1_first` to `index1_last`, and `index2_first` to `index2_last`). The most common is `index1_first=32` and `index1_last=126`, meaning that the font provides bitmaps for all the printable ASCII characters, with `index2_start` and `index2_last` zero for no other range.

### index2_first, index2_last
In some cases a font may support two ranges of characters. AN example could be a smaller font that had only capital letters and numerical digits. In this case the metadata would specific `index1_first=48` and `index1_last=57` for the numbers and `index2_first=65` and `index2_last=90` for the letters.

### bits_index
**Also see** - _index_
This specifies the width of each number in the _index_ array, in bits. For example, If this number is 5, then each number in the _index_ table is a 5-bit number.

### bits_width, bits_height, bits_xoffset, bits_yoffset, bits_delta
**Also see** - _data_
These properties specify the size, in bits, of the numbers within the glyph data. The glyph data contains values for the width and height of the character, the x- and y-offset and the delta. These properties say how many bits each of those numbers occupies. For example, `bits_width=3` and `bits_height=5` mean that the character width is a 3-bit number, and the character height is a 5-bit number within the packed glyph data.

### line_space
How many pixels to advance the cursor vertically for a new line.

### cap_height
The height of a capital letter (actually calculated from capital E). This is used by some rendering engines to offset the baseline of the text from the cursor. For example, the `ILI9341_t3` library renders text _below_ the cursor (so it offsets the text by `cap_height`), whereas the `mac` library renders text using the cursor as the baseline, thus it actually ignores `cap_height`.

---
## Credits
Credits for the format, specification, and help:
* [Paul Stoffregen](https://forum.pjrc.com/threads/54316-ILI9341_t-font-structure-format?p=191131&viewfull=1#post191131) - Creator of original format ILI9341_t3_font_t and fonr drawing routines
* [spook](https://forum.pjrc.com/threads/54316-ILI9341_t-font-structure-format?p=191184&viewfull=1#post191184) - Clarifications of data format, author of [Embedded Font Creator](https://forum.pjrc.com/threads/54345-ILI9341_t3-font-editor)
