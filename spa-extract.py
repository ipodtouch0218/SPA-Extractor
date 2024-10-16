import sys
import os
import argparse
from PIL import Image, ImageOps


def extract_file(file_path, output_folder, apply_mirroring):
    f = open(file_path, 'rb')
    
    header = f.read(4)
    if header != b' APS':
        raise ValueError('Missing SPA file header')
            
    version = f.read(4)
    if version != b'22_1':
        raise ValueError('Unsupported SPA file version')
    
    particles = int.from_bytes(f.read(2), byteorder='little')
    textures = int.from_bytes(f.read(2), byteorder='little')
    _ = f.read(4) # padding
    particle_block_length = int.from_bytes(f.read(4), byteorder='little')
    texture_block_length = int.from_bytes(f.read(4), byteorder='little')
    texture_block_offset = int.from_bytes(f.read(4), byteorder='little')
    _ = f.read(4) # padding
    
    folder = output_folder + '/' + '.'.join(file_path.split('.')[:-1])
    try:
        os.makedirs(folder, exist_ok=True)
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
        repeat_s = (texture_info & (1 << 12)) != 0
        repeat_t = (texture_info & (1 << 13)) != 0
        mirror_s = (texture_info & (1 << 14)) != 0
        mirror_t = (texture_info & (1 << 15)) != 0
        
        color_zero_transparent = int.from_bytes(f.read(2), byteorder='little') != 0
        texture_data_length = int.from_bytes(f.read(4), byteorder='little')
        palette_offset = int.from_bytes(f.read(4), byteorder='little')
        palette_data_length = int.from_bytes(f.read(4), byteorder='little')
        four_by_four_offset = int.from_bytes(f.read(4), byteorder='little')
        four_by_four_data_length = int.from_bytes(f.read(4), byteorder='little')
        total_size = int.from_bytes(f.read(4), byteorder='little')
        
        texture_data = f.read(texture_data_length)
        palette_data = f.read(palette_data_length)
        _ = f.read(four_by_four_data_length)
        
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
        
        if apply_mirroring:
            if mirror_s:
                tmp = Image.new('RGBA', (image.width * 2, image.height))
                tmp.paste(image, (0,0))
                tmp.paste(ImageOps.mirror(image), (image.width, 0))
                image = tmp
            if mirror_t:
                tmp = Image.new('RGBA', (image.width, image.height * 2))
                tmp.paste(image, (0,0))
                tmp.paste(ImageOps.flip(image), (0, image.height))
                image = tmp
        
        image.save(f'{folder}/particle-{particle_number}.png')
        
    f.close()
    
    return particle_number


def print_extract_file(file_path, output_folder, apply_mirroring):
    try:
        result = extract_file(file_path, output_folder, apply_mirroring)
        print(f'{file_path}: Extracted {result} textures')
        return result
    except ValueError as ve:
        print(f'{file_path}: Failed to parse. {ve}')
        return 0


def spa_extract():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')
    parser.add_argument('-o', '--output', dest='output_folder', help='Output folder to place all exported textures within', default='.')
    parser.add_argument('-m', '--apply-mirroring', dest='apply_mirroring', help='Outputs textures with their mirroring, when applicable.', action='store_true')
    args = parser.parse_args()
    
    total = 0
    
    if os.path.isfile(args.input_file):
        total += print_extract_file(args.input_file, args.output_folder, args.apply_mirroring)
       
    elif os.path.isdir(args.input_file):
        files = [f for f in os.listdir(args.input_file) if os.path.isfile(args.input_file + '/' + f) and f.lower().endswith('.spa')]
        if len(files) <= 0:
            print('The folder you provided does not contain any .spa files.')
            return 1
        
        for file in files:
            total += print_extract_file(file, args.output_folder, args.apply_mirroring)
   
    else:
        print('Failed to locate the provided file. Does it exist?')
        return 2
            
    print(f'Complete. Successfully extracted {total} textures')
    return 0
    
    
if __name__ == "__main__":
	exit(spa_extract())