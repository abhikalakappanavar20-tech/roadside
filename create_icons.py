"""
Create placeholder PWA icons for Roadside Assistance
Run this script to generate app icons
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename, color='#2563eb', text='R'):
    """Create a square icon with given size"""
    # Create image
    img = Image.new('RGB', (size, size), color=color)
    draw = ImageDraw.Draw(img)

    # Draw white circle in center
    padding = size // 8
    draw.ellipse(
        [(padding, padding), (size - padding, size - padding)],
        fill='white'
    )

    # Draw text (truck icon representation)
    font_size = size // 2
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - font_size // 4

    draw.text((x, y), text, fill=color, font=font)

    # Save image
    img.save(filename)
    print(f"Created: {filename} ({size}x{size})")

def main():
    # Ensure img directory exists
    img_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
    os.makedirs(img_dir, exist_ok=True)

    print("Creating PWA icons...")

    # Create required icons
    create_icon(
        192,
        os.path.join(img_dir, 'icon-192.png'),
        color='#2563eb',
        text='RA'
    )

    create_icon(
        512,
        os.path.join(img_dir, 'icon-512.png'),
        color='#2563eb',
        text='RA'
    )

    create_icon(
        96,
        os.path.join(img_dir, 'badge.png'),
        color='#2563eb',
        text='R'
    )

    # Create favicon
    create_icon(
        32,
        os.path.join(img_dir, 'favicon.ico'),
        color='#2563eb',
        text='R'
    )

    print("\nAll icons created successfully!")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("PIL not installed. Install with: pip install Pillow")
        print("Creating empty placeholder files...")

        img_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
        os.makedirs(img_dir, exist_ok=True)

        # Create empty files
        for size, name in [(192, 'icon-192.png'), (512, 'icon-512.png'), (96, 'badge.png')]:
            open(os.path.join(img_dir, name), 'w').close()
            print(f"Created placeholder: {name}")
