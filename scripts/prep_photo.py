import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


if len(sys.argv) < 2:
    print("Usage: python scripts/prep_photo.py source-photo.jpg")
    sys.exit(1)

input_path = Path(sys.argv[1])
output_path = Path("source-prepped.png")

if not input_path.exists():
    print(f"File not found: {input_path}")
    sys.exit(1)

# Remove background
with open(input_path, "rb") as f:
    input_image = f.read()

output_image = remove(input_image)

temp_path = Path("temp_no_bg.png")
temp_path.write_bytes(output_image)

# Open image
image = Image.open(temp_path).convert("RGBA")

# Put subject on white background
background = Image.new("RGBA", image.size, "white")
background.alpha_composite(image)

# Convert to grayscale
gray = np.array(background.convert("L"))

# Improve local contrast
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

gray = clahe.apply(gray)

# Slightly improve overall contrast
gray = cv2.normalize(
    gray,
    None,
    0,
    255,
    cv2.NORM_MINMAX
)

cv2.imwrite(str(output_path), gray)

temp_path.unlink(missing_ok=True)

print(f"Created: {output_path}")
