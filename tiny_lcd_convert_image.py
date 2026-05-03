#! /usr/bin/env python3

"""
convert_image.py  –  Run this on your PC before copying files to the Tiny 2040.

Converts a PNG (or any Pillow-supported image) to a raw RGB565 binary file
sized to fit the Waveshare 1.69" display (240x280).

Requirements:
    pip install Pillow

Usage:
    python convert_image.py my_photo.png
    python convert_image.py my_photo.png --out custom_name.raw
"""

import argparse
import struct
from pathlib import Path
from PIL import Image, ImageDraw

def convert_to_rgb565(src: Path, dst: Path) -> None:

    # Physical screen dimensions
    screen_width=280
    screen_height=240
    screen_orientation=90
    maskr=35

    # Dimensions of mask - region within physical screen to use
    mask_width=258
    # mask_height=screen_height
    mask_height=int(round(screen_height/screen_width*mask_width))
    round_radius=35 # Radius with which to round corners of mask

    # Offset of mask withing physical screen
    mask_dx=0 #screen_width-mask_width
    mask_dy=(screen_height-mask_height)//2

    # Create mask image
    mask=Image.new("L", (screen_width, screen_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, mask_dy), (mask_width-1, mask_dy+mask_height-1)], radius=round_radius, fill=255 ,width=0)
    # mask.save('mask.png')

    # Load in the image to convert and scale it to fit the mask
    img=Image.open(src).convert("RGB")
    img.thumbnail((mask_width, mask_height), Image.LANCZOS)

    # Offset of image on physical screen
    image_dx=mask_dx+(mask_width-img.width)//2
    image_dy=mask_dy+(mask_height-img.height)//2

    # Create final image by applying mask to scaled image 
    canvas=Image.new("RGB", (screen_width, screen_height), (0, 0, 0))
    canvas.paste(img, (image_dx, image_dy))
    canvas=Image.composite(canvas, Image.new("RGB", (screen_width, screen_height), (0, 0, 0)), mask)
    canvas=canvas.rotate(screen_orientation, expand=True)   # ← add this line
    # canvas.save('test.png')

    # Convert final image to RGB565
    pixels = canvas.load()
    buf = bytearray(canvas.width * canvas.height * 2)
    idx = 0
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = pixels[x, y]
            # Pack into big-endian RGB565 (what ST7789V2 expects)
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            struct.pack_into(">H", buf, idx, rgb565)
            idx += 2

    dst.write_bytes(buf)
    print(f"Saved {dst}  ({canvas.width}x{canvas.height}, {len(buf)} bytes)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PNG → RGB565 raw binary")
    parser.add_argument("src",           help="Input image file")
    parser.add_argument("--out",         help="Output .raw file (default: same name)")
    args = parser.parse_args()

    src = Path(args.src)
    dst = Path(args.out) if args.out else src.with_suffix(".raw")
    convert_to_rgb565(src, dst)
