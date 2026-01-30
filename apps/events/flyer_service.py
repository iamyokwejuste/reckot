from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def parse_color(color_str):
    color_str = color_str.strip().lower()
    if color_str == "transparent":
        return (0, 0, 0, 0)
    if color_str.startswith("rgba"):
        parts = color_str.replace("rgba(", "").replace(")", "").split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        a = int(float(parts[3]) * 255)
        return (r, g, b, a)
    elif color_str.startswith("rgb"):
        parts = color_str.replace("rgb(", "").replace(")", "").split(",")
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        return (r, g, b, 255)
    else:
        rgb = hex_to_rgb(color_str)
        return rgb + (255,)


def create_circular_mask(size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    return mask


def create_rounded_mask(size, radius=None):
    if radius is None:
        radius = min(size[0], size[1]) // 8
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def get_font(size, weight="regular"):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_flyer(config, user_photo, text_values: dict) -> BytesIO:
    template = Image.open(config.template_image.path).convert("RGBA")
    template = template.resize(
        (config.output_width, config.output_height), Image.Resampling.LANCZOS
    )

    if user_photo:
        photo = Image.open(user_photo).convert("RGBA")
        photo = ImageOps.fit(
            photo, (config.photo_width, config.photo_height), Image.Resampling.LANCZOS
        )

        if config.photo_shape == "CIRCLE":
            mask = create_circular_mask((config.photo_width, config.photo_height))
            photo.putalpha(mask)
        elif config.photo_shape == "ROUNDED":
            mask = create_rounded_mask((config.photo_width, config.photo_height))
            photo.putalpha(mask)

        if hasattr(config, "photo_bg_color") and config.photo_bg_color:
            bg_color = parse_color(config.photo_bg_color)
            if bg_color[3] > 0:
                bg_size = (config.photo_width, config.photo_height)
                bg_layer = Image.new("RGBA", bg_size, (0, 0, 0, 0))
                bg_draw = ImageDraw.Draw(bg_layer)

                if config.photo_shape == "CIRCLE":
                    bg_draw.ellipse((0, 0, bg_size[0], bg_size[1]), fill=bg_color)
                elif config.photo_shape == "ROUNDED":
                    radius = min(config.photo_width, config.photo_height) // 8
                    bg_draw.rounded_rectangle(
                        (0, 0, bg_size[0], bg_size[1]), radius=radius, fill=bg_color
                    )
                else:
                    bg_draw.rectangle((0, 0, bg_size[0], bg_size[1]), fill=bg_color)

                template.paste(bg_layer, (config.photo_x, config.photo_y), bg_layer)

        if config.photo_border_width > 0:
            border_color = hex_to_rgb(config.photo_border_color)
            border_size = (
                config.photo_width + config.photo_border_width * 2,
                config.photo_height + config.photo_border_width * 2,
            )
            border_layer = Image.new("RGBA", border_size, (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(border_layer)

            if config.photo_shape == "CIRCLE":
                border_draw.ellipse(
                    (0, 0, border_size[0], border_size[1]), fill=border_color + (255,)
                )
            elif config.photo_shape == "ROUNDED":
                radius = min(border_size[0], border_size[1]) // 8
                border_draw.rounded_rectangle(
                    (0, 0, border_size[0], border_size[1]),
                    radius=radius,
                    fill=border_color + (255,),
                )
            else:
                border_draw.rectangle(
                    (0, 0, border_size[0], border_size[1]), fill=border_color + (255,)
                )

            border_layer.paste(
                photo, (config.photo_border_width, config.photo_border_width), photo
            )
            template.paste(
                border_layer,
                (
                    config.photo_x - config.photo_border_width,
                    config.photo_y - config.photo_border_width,
                ),
                border_layer,
            )
        else:
            template.paste(photo, (config.photo_x, config.photo_y), photo)

    draw = ImageDraw.Draw(template)
    for field in config.text_fields.all():
        text = text_values.get(str(field.id), "") or text_values.get(field.label, "")
        if not text:
            continue

        font = get_font(field.font_size, field.font_weight)
        color = hex_to_rgb(field.font_color)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if field.text_align == "CENTER":
            x = field.x - text_width // 2
        elif field.text_align == "RIGHT":
            x = field.x - text_width
        else:
            x = field.x

        if hasattr(field, "bg_color") and field.bg_color:
            bg_color = parse_color(field.bg_color)
            if bg_color[3] > 0:
                padding = 8
                bg_bbox = (
                    x - padding,
                    field.y - padding,
                    x + text_width + padding,
                    field.y + text_height + padding,
                )
                draw.rounded_rectangle(bg_bbox, radius=5, fill=bg_color)

        draw.text((x, field.y), text, font=font, fill=color)

    output = BytesIO()
    template = template.convert("RGB")
    template.save(output, format="JPEG", quality=config.output_quality, optimize=True)
    output.seek(0)
    return output
