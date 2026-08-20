"""
Script to generate a modern, high-resolution multi-size .ico and .png icon
for the My Budget Tracker application.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import os

def create_budget_tracker_icon(output_dir="."):
    # We will draw at 1024x1024 for crisp downsampling to all standard icon sizes
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    # 1. Base Squircle Geometry
    margin = 48
    corner_radius = 210
    
    # Background Mask for rounded rectangle
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        fill=255
    )
    
    # 2. Gradient Background on the squircle (Deep Obsidian / Midnight Indigo to Electric Violet/Indigo)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    
    # Multi-stop smooth linear/diagonal gradient
    c1 = (11, 15, 25)       # #0B0F19 (Deep Obsidian)
    c2 = (30, 27, 75)       # #1E1B4B (Deep Indigo)
    c3 = (79, 70, 229)      # #4F46E5 (Vibrant Indigo)
    c4 = (99, 102, 241)     # #6366F1 (Indigo Accent)
    
    for y in range(margin, size - margin):
        ratio = (y - margin) / (size - 2 * margin)
        # Smooth interpolation
        if ratio < 0.6:
            sub_r = ratio / 0.6
            r = int(c1[0] * (1 - sub_r) + c2[0] * sub_r)
            g = int(c1[1] * (1 - sub_r) + c2[1] * sub_r)
            b = int(c1[2] * (1 - sub_r) + c2[2] * sub_r)
        else:
            sub_r = (ratio - 0.6) / 0.4
            r = int(c2[0] * (1 - sub_r) + c3[0] * sub_r)
            g = int(c2[1] * (1 - sub_r) + c3[1] * sub_r)
            b = int(c2[2] * (1 - sub_r) + c3[2] * sub_r)
        
        bg_draw.line([(margin, y), (size - margin, y)], fill=(r, g, b, 255))
    
    # 3. Add soft ambient lighting glow in top-right / center
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_center_x, glow_center_y = int(size * 0.65), int(size * 0.35)
    for rad in range(320, 0, -8):
        alpha = int(35 * (1 - rad / 320))
        glow_draw.ellipse(
            [glow_center_x - rad, glow_center_y - rad, glow_center_x + rad, glow_center_y + rad],
            fill=(129, 140, 248, alpha)
        )
    bg = Image.alpha_composite(bg, glow)

    # 4. Composite the background using the squircle mask
    squircle_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    squircle_layer.paste(bg, (0, 0), mask)
    
    # 5. Inner Glass Border / Highlight Stroke
    stroke_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    stroke_draw = ImageDraw.Draw(stroke_layer)
    stroke_draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=corner_radius,
        outline=(165, 180, 252, 100),
        width=10
    )
    # Top highlight sheen
    stroke_draw.arc(
        [margin + 4, margin + 4, size - margin - 4, margin + corner_radius * 2],
        start=180, end=0,
        fill=(255, 255, 255, 160),
        width=6
    )
    squircle_layer = Image.alpha_composite(squircle_layer, stroke_layer)
    
    # 6. Central Graphic: Modern Financial Card + Upward Growth Bars + Glowing Coin
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Shadow under the central card
    shadow_card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sc_draw = ImageDraw.Draw(shadow_card)
    sc_draw.rounded_rectangle([200, 260, 824, 760], radius=60, fill=(0, 0, 0, 160))
    shadow_card = shadow_card.filter(ImageFilter.GaussianBlur(radius=24))
    overlay = Image.alpha_composite(overlay, shadow_card)
    draw = ImageDraw.Draw(overlay)
    
    # Central Frosted Glass Card Base
    card_bounds = [200, 250, 824, 750]
    draw.rounded_rectangle(card_bounds, radius=60, fill=(17, 24, 39, 235), outline=(99, 102, 241, 140), width=8)
    
    # Modern Grid / Circuit lines subtle backdrop inside card
    for y_line in range(320, 720, 80):
        draw.line([(240, y_line), (784, y_line)], fill=(31, 41, 55, 120), width=3)
    
    # Dynamic Upward Bar Charts with Gradients
    # Bar 1 (Emerald/Teal, moderate height)
    b1_x0, b1_y0, b1_x1, b1_y1 = 270, 530, 360, 690
    draw.rounded_rectangle([b1_x0, b1_y0, b1_x1, b1_y1], radius=20, fill=(16, 185, 129, 240), outline=(52, 211, 153, 200), width=4)
    
    # Bar 2 (Amber/Gold, higher)
    b2_x0, b2_y0, b2_x1, b2_y1 = 400, 430, 490, 690
    draw.rounded_rectangle([b2_x0, b2_y0, b2_x1, b2_y1], radius=20, fill=(245, 158, 11, 240), outline=(251, 191, 36, 200), width=4)
    
    # Bar 3 (Violet/Indigo, highest growth bar)
    b3_x0, b3_y0, b3_x1, b3_y1 = 530, 340, 620, 690
    draw.rounded_rectangle([b3_x0, b3_y0, b3_x1, b3_y1], radius=20, fill=(129, 140, 248, 250), outline=(199, 210, 254, 220), width=4)
    
    # Dynamic Trend Arrow / Trend Line connecting the peaks
    trend_points = [(315, 520), (445, 420), (575, 330), (740, 230)]
    # Thick neon line
    for i in range(len(trend_points) - 1):
        p_start = trend_points[i]
        p_end = trend_points[i + 1]
        draw.line([p_start, p_end], fill=(56, 189, 248, 255), width=16)
    
    # Trend Arrow Head at (740, 230)
    arrow_points = [(740, 230), (670, 240), (715, 290)]
    draw.polygon(arrow_points, fill=(56, 189, 248, 255))
    
    # Node dots on trend line
    for pt in [(315, 520), (445, 420), (575, 330)]:
        draw.ellipse([pt[0] - 14, pt[1] - 14, pt[0] + 14, pt[1] + 14], fill=(255, 255, 255, 255), outline=(56, 189, 248, 255), width=4)
        
    # Glowing Golden Coin Symbol in top right of card / overlapping
    coin_cx, coin_cy, coin_r = 710, 360, 85
    # Coin outer shadow
    coin_shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cs_draw = ImageDraw.Draw(coin_shadow)
    cs_draw.ellipse([coin_cx - coin_r - 10, coin_cy - coin_r - 10, coin_cx + coin_r + 10, coin_cy + coin_r + 10], fill=(0, 0, 0, 140))
    coin_shadow = coin_shadow.filter(ImageFilter.GaussianBlur(radius=14))
    overlay = Image.alpha_composite(overlay, coin_shadow)
    draw = ImageDraw.Draw(overlay)
    
    # Coin Outer Circle (Vibrant Gold)
    draw.ellipse([coin_cx - coin_r, coin_cy - coin_r, coin_cx + coin_r, coin_cy + coin_r], fill=(245, 158, 11, 255), outline=(253, 230, 138, 255), width=7)
    # Coin Inner Ring
    inner_r = coin_r - 16
    draw.ellipse([coin_cx - inner_r, coin_cy - inner_r, coin_cx + inner_r, coin_cy + inner_r], outline=(217, 119, 6, 200), width=4)
    
    # Coin Currency Symbol ($ / Budget Emblem) in center of coin
    # Draw a stylized clean '$' using lines & arcs
    s_col = (255, 255, 255, 255)
    # Vertical spine
    draw.line([(coin_cx, coin_cy - 48), (coin_cx, coin_cy + 48)], fill=s_col, width=8)
    # Top arc
    draw.arc([coin_cx - 24, coin_cy - 38, coin_cx + 24, coin_cy - 2], start=100, end=340, fill=s_col, width=9)
    # Bottom arc
    draw.arc([coin_cx - 24, coin_cy - 2, coin_cx + 24, coin_cy + 34], start=280, end=160, fill=s_col, width=9)
    # Connecting cross curve
    draw.line([(coin_cx - 16, coin_cy - 4), (coin_cx + 16, coin_cy + 4)], fill=s_col, width=8)

    # 7. Final Composite
    final_img = Image.alpha_composite(squircle_layer, overlay)
    
    # Create output paths
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, "icon.png")
    ico_path = os.path.join(output_dir, "icon.ico")
    
    # Save High Res PNG
    final_img.save(png_path, format="PNG")
    print(f"Saved PNG to {png_path}")
    
    # Create standard Windows ICO multi-resolution sizes:
    # 256, 128, 64, 48, 32, 24, 16
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    icon_layers = [final_img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    
    # Save ICO containing all sizes
    final_img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Saved ICO to {ico_path}")
    
    # Also save inside assets/ directory for standard project structure
    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    final_img.save(os.path.join(assets_dir, "icon.png"), format="PNG")
    final_img.save(os.path.join(assets_dir, "icon.ico"), format="ICO", sizes=sizes)
    print(f"Saved copies to assets/ directory")

if __name__ == "__main__":
    create_budget_tracker_icon()
