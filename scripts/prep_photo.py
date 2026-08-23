import sys
from pathlib import Path

import cv2


if len(sys.argv) < 2:
    print("Usage: python scripts/prep_photo.py source-photo.png")
    sys.exit(1)

input_path = Path(sys.argv[1])
output_path = Path("source-prepped.png")

if not input_path.exists():
    print(f"File not found: {input_path}")
    sys.exit(1)

# Read image
image = cv2.imread(str(input_path))

if image is None:
    print("Could not read image.")
    sys.exit(1)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Improve local contrast
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

gray = clahe.apply(gray)

# Improve overall contrast
gray = cv2.normalize(
    gray,
    None,
    0,
    255,
    cv2.NORM_MINMAX
)

# Slightly sharpen
gray = cv2.GaussianBlur(gray, (3, 3), 0)

# Save
cv2.imwrite(str(output_path), gray)

print(f"Created: {output_path}")
