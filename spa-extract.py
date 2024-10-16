import sys
import os
from PIL import Image

def spa_extract():
    args = sys.argv
    if len(args) < 2:
        print('Please specify the .spa file to extract.\nExample usage: ' + args[0] + ' spl.spa')
        return 1
    
    try:
        f = open(args[1], 'rb')
    except:
        print('Failed to open file. Does it exist?')
        return 2

    if f.read(4) != b' APS':
        print('Failed to read .spa header. Is this file truly a .spa?')
        return 3
            
    version = f.read(4)
    particles = int.from_bytes(f.read(2), byteorder='little')
    textures = int.from_bytes(f.read(2), byteorder='little')
    _ = f.read(4) # padding
    particle_block_length = int.from_bytes(f.read(4), byteorder='little')
    texture_block_length = int.from_bytes(f.read(4), byteorder='little')
    texture_block_offset = int.from_bytes(f.read(4), byteorder='little')
    _ = f.read(4) # padding
    
    print(f'Found {particles} particle(s), {textures} textures.')
    
    try:
        os.mkdir('.'.join(args[1].split('.')[:-1]))
    except:
        pass
    
    # Skip the paticle data, we just want the textures.
    f.seek(texture_block_offset)
    particle_number = 0
    while f.read(4) == b' TPS':
        texture_info = int.from_bytes(f.read(2), byteorder='little')
        
        texture_format = texture_info & 0xF
        width = 8 << ((texture_info >> 4) & 0xF)
        height = 8 << ((texture_info >> 8) & 0xF)
        repeat_s = (texture_info & (1 << 12)) == 1
        repeat_t = (texture_info & (1 << 13)) == 1
        mirror_s = (texture_info & (1 << 14)) == 1
        mirror_t = (texture_info & (1 << 15)) == 1
        
        color_zero_transparent = int.from_bytes(f.read(2), byteorder='little') != 0
        texture_data_length = int.from_bytes(f.read(4), byteorder='little')
        palette_offset = int.from_bytes(f.read(4), byteorder='little')
        palette_data_length = int.from_bytes(f.read(4), byteorder='little')
        four_by_four_offset = int.from_bytes(f.read(4), byteorder='little')
        four_by_four_data_length = int.from_bytes(f.read(4), byteorder='little')
        total_size = int.from_bytes(f.read(4), byteorder='little')
        
        texture_data = f.read(texture_data_length)
        palette_data = f.read(palette_data_length)
        f.read(four_by_four_data_length)
        
        image = Image.new('RGBA', (width, height), (0,0,0,0))
        pixels = image.load()
        
        rgb_palette_data = []
        for i in range(palette_data_length // 2):
            hi = palette_data[i * 2 + 1]
            lo = palette_data[i * 2]
            b = hi >> 2 & 0x1F
            g = ((hi & 0b11) << 3) | (lo >> 5)
            r = lo & 0x1F
            rgb_palette_data.append([r * 255 // 31, g * 255 // 31, b * 255 // 31, 255])
        
        i = 0
        pixel = 0
        while pixel < (width * height):
            if texture_format == 1:
                # 8bpp
                x = pixel % width
                y = pixel // width
                palette_index = texture_data[i]
                s = palette_index % 32
                a = palette_index - s
                
                rgba = rgb_palette_data[s]
                rgba[3] = a * 255 // 31
                pixels[x, y] = tuple(rgba)
                i += 1
                pixel += 1
                
            elif texture_format == 2:
                # 2bpp
                for j in range(4):
                    x = (pixel + j) % width
                    y = (pixel + j) // width
                    palette_index = (texture_data[i] >> 2 * j) & 0b11
                    rgba = rgb_palette_data[palette_index]
                    if palette_index == 0 and color_zero_transparent:
                        rgba[3] = 0
                    pixels[x, y] = tuple(rgba)
                    
                i += 1
                pixel += 4
                
            elif texture_format == 3:
                # 4bpp
                for j in range(2):
                    x = (pixel + j) % width
                    y = (pixel + j) // width
                    palette_index = (texture_data[i] >> 4 * j) & 0b1111
                    rgba = rgb_palette_data[palette_index]
                    if palette_index == 0 and color_zero_transparent:
                        rgba[3] = 0
                    pixels[x, y] = tuple(rgba)
                        
                i += 1
                pixel += 2
                        
            elif texture_format == 6:
                # 8bpp 
                x = pixel % width
                y = pixel // width
                palette_index = texture_data[i]
                
                s = palette_index % 8
                a = palette_index - s
                
                rgba = rgb_palette_data[s]
                rgba[3] = a * 255 // 31
                pixels[x, y] = tuple(rgba)
                    
                i += 1
                pixel += 1
                    
            elif texture_format == 7:
                # 16bpp direct color
                x = pixel % width
                y = pixel // width
                
                hi = texture_data[i + 1]
                lo = texture_data[i]
                r = hi >> 2 & 0x1F
                g = (hi & 0b11) | (lo >> 5)
                b = lo & 0x1F
                pixels[x, y] = (r, g, b, 255)
                    
                i += 2
                pixel += 1
        
        particle_number += 1
        
        image.save('.'.join(args[1].split('.')[:-1]) + '/particle-' + str(particle_number) + '.png')
        
    # print(byte)
    f.close()
    
    print(f'Exported {particle_number} particles.')
    return 0
    

if __name__ == "__main__":
	exit(spa_extract())