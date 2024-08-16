from glob import glob
from os import path
from PIL import Image

###
### Compile BDF fonts to c header files
###

# This code is available under the MIT license
# Copyright (c) 2019 Peter Vullings (Projectitis)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Will create a header file for each bdf font file, either
# as a bdffont_t.

# Many thanks to original c code from Paul Stoffregen used as reference
# https://github.com/PaulStoffregen/ILI9341_t3/blob/master/extras/bdf_to_ili9341.c

# If this script is run directly, then we are called from bdf_to_h. If the 
# script is NOT run directly, assume we are called from bdf_to_hc.
extern = not (__name__ == '__main__')

# debug
debug = False
def log(*args):
	global debug
	if debug:
		print(*args)

# function defs
def bits_required_unsigned( max ):   
	n = 1;
	if (max < 0): max = 0
	while max >= (1 << n): n+=1
	return n

def bits_required_signed(min, max):
	n = 2;
	if (min > 0): min = 0;
	if (max < 0): max = 0;
	while min < -(1 << (n-1)): n+=1
	while max >= (1 << (n-1)): n+=1
	return n

def pixel(glyph, x, y):
	if x >= glyph['width']: return 0;
	if y >= glyph['height']: return 0;
	# grab the correct byte
	#b = glyph['data'][(((glyph['width'] + 7) >> 3) * y) + (x >> 3)];
	b = glyph['data'][(((glyph['width']*bits_per_pixel + 7) >> 3) * y) + (x >> (3-bpp_index))];
	# firstly, adjust x to current byte
	x = x % pix_per_byte
	# now move pixel to least significant spot
	b = b >> int((pix_per_byte-x-1)*bits_per_pixel)
	# finally return pixel value using mask
	b = b & bpp_mask
	return b

def output_newline():
	global output_state_linelen, outstr
	if output_state_linelen > 0:
		outstr += '\n'
		output_state_linelen = 0

def output_bit(bit):
	global output_state_byte, output_state_bytecount, output_state_bitcount, output_state_linelen, outstr

	bitmask = 1 << (7 - output_state_bitcount)
	if bit: output_state_byte |= bitmask;
	else: output_state_byte &= ~bitmask;
	
	output_state_bitcount += 1
	if output_state_bitcount >= 8:
		output_state_bitcount = 0
		outstr += '0x'+format(output_state_byte, '02x')+','
		output_state_bytecount+=1
		output_state_linelen+=1
		if output_state_linelen >= 10: output_newline()
		output_state_byte = 0

# def output_bits( bits ):
# 	global output_state_byte, output_state_bytecount, output_state_bitcount, output_state_linelen, outstr

# 	bitmask = bpp_mask << (8 - bits_per_pixel - output_state_bitcount)

# 	if bit:
# 		output_state_byte |= bitmask
# 	else:
# 		output_state_byte &= ~bitmask

# 	output_state_bitcount+=bits_per_pixel
# 	if output_state_bitcount >= 8:
# 		output_state_bitcount = 0
# 		outstr += '0x'+format(output_state_byte, '02x')+','
# 		output_state_bytecount+=1
# 		output_state_linelen+=1
# 		if output_state_linelen >= 10: output_newline()
# 		output_state_byte = 0

def output_number(num,bits):
	while bits > 0:
		output_bit(num & (1 << (bits-1)))
		bits -= 1

def output_line(glyph,y):
	for x in range(0, glyph['width']):
		output_number(pixel(glyph, x, y),bits_per_pixel)

def output_pad_to_byte():
	global output_state_bitcount
	while (output_state_bitcount > 0): output_bit(0)

def lines_identical(glyph,y1,y2):
	for x in range(0, glyph['width']):
		if (pixel(glyph, x, y1) != pixel(glyph, x, y2)): return 0
	return 1

def num_lines_identical(glyph,y):
	y2 = y+1
	for y2 in range(y+1, glyph['height']):
		if not lines_identical(glyph, y, y2): break
	return y2 - y - 1

def output_glyph(glyph):
	output_number(0, 3) # reserved bits, intended to identify future formats
	output_number(glyph['width'], bits_width)
	output_number(glyph['height'], bits_height)
	output_number(glyph['xoffset'], bits_xoffset)
	output_number(glyph['yoffset'], bits_yoffset)
	output_number(glyph['delta'], bits_delta)

	# Change for v2.3
	# AA fonts have pixel data aligned to byte boundary, and don't have leading
	# bit to indicate duplicate lines (i.e. duplicate lines are not supported).
	y = 0
	if bits_per_pixel==1:
		while y < glyph['height']:
			identical_count = num_lines_identical(glyph, y);
			if (identical_count == 0):
				output_bit(0)
				output_line(glyph, y)
			else:
				output_bit(1)
				if identical_count > 6: identical_count = 6;
				output_number(identical_count - 1, 3)
				output_line(glyph, y)
				y += identical_count
			y+=1
	else:
		output_pad_to_byte()
		while y < glyph['height']:
			output_line(glyph, y)
			y+=1

	output_pad_to_byte()

# Get list of BDF files in this folder
resources = glob('./*.bdf')
for file in list(resources):

	# Split the filename by dot to get the parts
	filename = path.basename(file)
	fileparts = filename.split('.')
	if len(fileparts) < 2:
		continue
	
	# first and last parts of filename are name and extn
	name = fileparts.pop(0)
	extn = fileparts.pop().lower()
	
	# Some useful messages to console
	print()
	print('Processing',filename,'(bdf)')
	
	# Open raw file and grab properties
	outstr = ''
	output_state_byte = 0
	output_state_bitcount = 0
	output_state_linelen = 0
	output_state_bytecount = 0

	glyphs = {}
	glyph_data = []
	process_glyph = False
	process_data = False
	version = 1
	line_space = 0
	cap_height = 0
	is_bold = False
	is_italic = False
	font_size = 0
	font_name = ''
	bits_per_pixel = 1
	bpp_index = 0
	bpp_mask = 0b00000001
	pix_per_byte = 8
	found_ascent = False
	font_ascent = 0
	found_descent = False
	font_descent = 0
	found_encoding = False
	encoding = 0
	found_dwidth = False
	dwidth_x = 0
	dwidth_y = 0
	found_bbx = False
	bbx_width = 0
	bbx_height = 0
	bbx_xoffset = 0
	bbx_yoffset = 0
	linenum = 0
	expect_line = 0
	expect_bytes = 0
	encoding_start1 = 0
	encoding_end1 = 0
	encoding_start2 = 0
	encoding_end2 = 0
	with open(file, "rt") as f:
		for line in f:
			linenum += 1
			prop = line.split(" ", 1)
			if len(prop)>0:
				prop[0] = prop[0].strip()
			if len(prop)>1:
				prop[1] = prop[1].strip()
				props = prop[1].split(" ")
			else: props = []

			# process font header
			if not process_glyph:
				# Exit header mode (enter glyph mode)
				if prop[0] == 'STARTCHAR':
					found_encoding = False
					found_dwidth = False
					found_bbx = False
					process_data = False
					process_glyph = True
					if len(glyphs)==0: print('  FAMILY_NAME:'+font_name+', SIZE:'+str(font_size)+', '+str(bits_per_pixel)+'bpp') 
					log('  FOUND',prop[1])
				# Collect header properties
				elif prop[0] == 'SIZE':
					font_size = int(props[0])
				elif prop[0] == 'FAMILY_NAME':
					font_name = prop[1].strip().strip('\"').replace(' ','')
				elif prop[0] == 'WEIGHT_NAME':
					if 'Bold' in prop[1]:
						is_bold = True
				elif prop[0] == 'SLANT':
					if '\"I\"' in prop[1]:
						is_italic = True
				elif prop[0] == 'BITS_PER_PIXEL':
					bits_per_pixel = int(prop[1])
					if (bits_per_pixel>1):
						version = 23
						if (bits_per_pixel==2): bpp_index = 1
						elif (bits_per_pixel==4): bpp_index = 2
						elif (bits_per_pixel==8): bpp_index = 3
						else: raise Exception('BITS_PER_PIXEL not supported, at line '+str(linenum))
						bpp_mask = (1 << bits_per_pixel)-1
						pix_per_byte = 8/bits_per_pixel
				elif prop[0] == 'FONT_ASCENT':
					found_ascent = True
					font_ascent = int(prop[1])
				elif prop[0] == 'FONT_DESCENT':
					found_descent = True
					font_descent = int(prop[1])

			# process glyphs 
			elif not process_data:
				# Encoding is the ascii number
				if prop[0] == 'ENCODING':
					found_encoding = True
					encoding = int(prop[1])
					if (encoding<1): raise Exception('ENCODING '+str(encoding)+' not supported, at line '+str(linenum))
					log('    Encoding',encoding)
					if encoding_start2>0:
						if encoding != (encoding_end2+1): raise Exception('ENCODING more than 2 encoding ranges ('+encoding_start1+'-'+encoding_end1+', '+encoding_start2+','+encoding_end2+'), at line '+str(linenum))
						encoding_end2 = encoding
					elif encoding_start1>0:
						if encoding != (encoding_end1+1):
							encoding_start2 = encoding
							encoding_end2 = encoding
						else:
							encoding_end1 = encoding
					else:
						encoding_start1 = encoding
						encoding_end1 = encoding
				elif prop[0] == 'DWIDTH':
					found_dwidth = True
					dwidth_x = int(props[0])
					dwidth_y = int(props[1])
					log('    DWIDTH',dwidth_x,dwidth_y)
					if (dwidth_x < 0): raise Exception('DWIDTH x negative, at line '+str(linenum))
					if (dwidth_y != 0): raise Exception('DWIDTH y not zero, at line '+str(linenum))
				elif prop[0] == 'BBX':
					found_bbx = True
					bbx_width = int(props[0])
					bbx_height = int(props[1])
					bbx_xoffset = int(props[2])
					bbx_yoffset = int(props[3])
					log('    BBX',bbx_width,bbx_height,bbx_xoffset,bbx_yoffset)
					if (bbx_width < 0): raise Exception('BBX width negative, line '+str(linenum))
					if (bbx_height < 0): raise Exception('BBX height negative, line '+str(linenum))
				elif prop[0] == 'BITMAP':
					log('    BITMAP')
					if not found_encoding: raise Exception('missing ENCODING, line '+str(linenum))
					if not found_dwidth: raise Exception('missing DWIDTH, line '+str(linenum))
					if not found_bbx: raise Exception('missing BBX, line '+str(linenum))
					expect_lines = bbx_height
					expect_bytes = ((bbx_width * bits_per_pixel) + 7) >> 3
					glyph_data = []
					process_data = True

			# process glyph data
			else:
				if expect_lines > 0 and expect_bytes > 0:
					data = prop[0]
					for i in range(expect_bytes):
						try:
							glyph_data.append( int(data[0:2],16) )
						except:
							raise Exception('Non-hex char on line, line '+str(linenum))
						data = data[2:]
					expect_lines -= 1
				else:
					if prop[0] == 'ENDCHAR':
						process_glyph = False
						glyphs[str(encoding)] = { 'width': bbx_width, 'height': bbx_height, 'xoffset': bbx_xoffset, 'yoffset': bbx_yoffset, 'delta': dwidth_x, 'encoding': encoding, 'data': glyph_data }
					else:
						raise Exception('ENDCHAR expected, line '+str(linenum))

		if found_ascent and found_descent:
			line_space = font_ascent + font_descent
		# Capital E is char 69. This is used for general 'cap height'
		if '69' in glyphs and 'data' in glyphs['69']:
			cap_height = glyphs['69']['height'] + glyphs['69']['yoffset']

	# File finished processing
	log('  Line space:',line_space)
	log('  Cap height:',cap_height)

	# Compute_min_max
	max_width=0
	max_height=0
	max_delta=0
	min_xoffset=0
	max_xoffset=0
	min_yoffset=0
	max_yoffset=0
	for glyph in glyphs.values():
		#if glyph['encoding'] == 0: glyph['encoding'] = index of loop; ???
		if (glyph['width'] > max_width): max_width = glyph['width']
		if (glyph['height'] > max_height): max_height = glyph['height']
		if (glyph['xoffset'] < min_xoffset): min_xoffset = glyph['xoffset']
		if (glyph['xoffset'] > max_xoffset): max_xoffset = glyph['xoffset']
		if (glyph['yoffset'] < min_yoffset): min_yoffset = glyph['yoffset']
		if (glyph['yoffset'] > max_yoffset): max_yoffset = glyph['yoffset']
		if (glyph['delta'] > max_delta): max_delta = glyph['delta']

	bits_width =   bits_required_unsigned(max_width)
	bits_height =  bits_required_unsigned(max_height)
	bits_xoffset = bits_required_signed(min_xoffset, max_xoffset)
	bits_yoffset = bits_required_signed(min_yoffset, max_yoffset)
	bits_delta =   bits_required_unsigned(max_delta)

	# internal font name
	font_name = font_name+str(font_size);
	if is_bold: font_name += '_Bold'
	if is_italic: font_name += '_Italic'

	# start header file
	outstr = '#ifndef _PACKEDBDF_'+font_name.upper()+'_\n'
	outstr += '#define _PACKEDBDF_'+font_name.upper()+'_\n\n'
	outstr += '#include "PackedBDF.h"\n\n'

	# if we are creating an external file for data, create the header stub first
	if extern:
		outstr += '#ifdef __cplusplus\n'
		outstr += 'extern "C" {\n'
		outstr += '#endif\n\n'
		outstr += 'extern const packedbdf_t '+font_name+'\n\n'
		outstr += '#ifdef __cplusplus\n'
		outstr += '}\n'
		outstr += '#endif\n\n'
		outstr += '#endif\n'

		### Write to file
		outfile = open('./'+font_name+'.h', 'w')
		outfile.write(outstr)
		outfile.close()

		### Start c file
		outstr = '#include "'+font_name+'.h"\n\n'

	# output the glyph data
	outstr += 'static const unsigned char '+font_name+'_data[] = {\n'
	for glyph in glyphs.values():
		glyph['byteoffset'] = output_state_bytecount
		output_glyph(glyph)
	output_newline();
	outstr = outstr[:-2]+' };\n'
	datasize = output_state_bytecount
	outstr += '/* font data size: '+str(datasize)+' bytes */\n\n'
	bits_index = bits_required_unsigned(output_state_bytecount)

	# output the index
	outstr += 'static const unsigned char '+font_name+'_index[] = {\n'
	for glyph in glyphs.values():
		output_number(glyph['byteoffset'], bits_index)
	output_pad_to_byte()
	output_newline()
	outstr = outstr[:-2]+' };\n'
	indexsize = output_state_bytecount - datasize
	outstr += '/* font index size: '+str(indexsize)+' bytes */\n\n'

	# output font structure
	outstr += 'const packedbdf_t '+font_name+' = {\n'
	outstr += '\t'+font_name+'_index,\n'
	outstr += '\t0,\n'
	outstr += '\t'+font_name+'_data,\n'
	if bits_per_pixel > 1:
		outstr += '\t23,\n'								# version 2.3
		outstr += '\t'+str(bpp_index)+',\n'				# lower 2 bits of reserved byte indicate bpp
	else:
		outstr += '\t1,\n'	# version 1
		outstr += '\t0,\n'	# reserved byte empty
	outstr += '\t'+str(encoding_start1)+',\n'
	outstr += '\t'+str(encoding_end1)+',\n'
	outstr += '\t'+str(encoding_start2)+',\n'
	outstr += '\t'+str(encoding_end2)+',\n'
	outstr += '\t'+str(bits_index)+',\n'
	outstr += '\t'+str(bits_width)+',\n'
	outstr += '\t'+str(bits_height)+',\n'
	outstr += '\t'+str(bits_xoffset)+',\n'
	outstr += '\t'+str(bits_yoffset)+',\n'
	outstr += '\t'+str(bits_delta)+',\n'
	outstr += '\t'+str(line_space)+',\n'
	outstr += '\t'+str(cap_height)+'\n'
	outstr += '};\n'

	### Write to file
	if not extern:
		outstr += '#endif\n'
		outfile = open('./'+font_name+'.h', 'w')
	else:
		outfile = open('./'+font_name+'.c', 'w')
	outfile.write(outstr)
	outfile.close()

	# Message
	print('  Processed',str(len(glyphs.values())),'glyphs. Index is',str(indexsize),'bytes. Data is',str(datasize),'bytes.')			

# Wait before exit for user to read messages
print()
input("Press enter to close")
