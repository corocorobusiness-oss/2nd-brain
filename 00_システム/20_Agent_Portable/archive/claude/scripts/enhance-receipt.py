#!/usr/bin/env python3
"""Enhance receipt images for better OCR/AI recognition."""

import sys
from PIL import Image, ImageEnhance

def enhance_receipt(input_path, output_path=None):
    if output_path is None:
        output_path = input_path.rsplit('.', 1)[0] + '_enhanced.png'

    img = Image.open(input_path)
    # Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Enhance sharpness
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    # Convert to grayscale
    img = img.convert('L')
    img.save(output_path)
    print(output_path)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: enhance-receipt.py <input_image> [output_image]")
        sys.exit(1)
    enhance_receipt(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
