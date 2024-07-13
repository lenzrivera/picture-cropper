# Picture Cropper

A simple and specific picture cropping script used when I was too lazy to manually crop 100+ physically scanned images 😅

## Usage

```py
# Set up virtual environment
virtualenv .venv
.venv/scripts/activate

# Install dependencies
pip install pillow

# Show options
py pcrop.py -h

# Run (e.g., for a directory with each scanned image)
# `--regions` acts as a sort of resolution parameter
py pcrop.py --regions 3 sample
```
