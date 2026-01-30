from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_circular_mask(size):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)
    return mask


def create_rounded_mask(size, radius=20):
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def get_font(size, weight='regular'):
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:\\Windows\\Fonts\\arial.ttf',
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_flyer(config, user_photo, text_values: dict) -> BytesIO:
    template = Image.open(config.template_image.path).convert('RGBA')
    template = template.resize((config.output_width, config.output_height), Image.Resampling.LANCZOS)

    if user_photo:
        photo = Image.open(user_photo).convert('RGBA')
        photo = ImageOps.fit(photo, (config.photo_width, config.photo_height), Image.Resampling.LANCZOS)

        if config.photo_shape == 'CIRCLE':
            mask = create_circular_mask((config.photo_width, config.photo_height))
            photo.putalpha(mask)
        elif config.photo_shape == 'ROUNDED':
            mask = create_rounded_mask((config.photo_width, config.photo_height), radius=20)
            photo.putalpha(mask)

        if config.photo_border_width > 0:
            border_color = hex_to_rgb(config.photo_border_color)
            border_size = (
                config.photo_width + config.photo_border_width * 2,
                config.photo_height + config.photo_border_width * 2
            )
            border_layer = Image.new('RGBA', border_size, (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(border_layer)

            if config.photo_shape == 'CIRCLE':
                border_draw.ellipse((0, 0, border_size[0], border_size[1]), fill=border_color + (255,))
            elif config.photo_shape == 'ROUNDED':
                border_draw.rounded_rectangle((0, 0, border_size[0], border_size[1]), radius=20, fill=border_color + (255,))
            else:
                border_draw.rectangle((0, 0, border_size[0], border_size[1]), fill=border_color + (255,))

            border_layer.paste(photo, (config.photo_border_width, config.photo_border_width), photo)
            template.paste(border_layer, (config.photo_x - config.photo_border_width, config.photo_y - config.photo_border_width), border_layer)
        else:
            template.paste(photo, (config.photo_x, config.photo_y), photo)

    draw = ImageDraw.Draw(template)
    for field in config.text_fields.all():
        text = text_values.get(str(field.id), '') or text_values.get(field.label, '')
        if not text:
            continue

        font = get_font(field.font_size, field.font_weight)
        color = hex_to_rgb(field.font_color)

        if field.text_align == 'CENTER':
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = field.x - text_width // 2
        elif field.text_align == 'RIGHT':
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = field.x - text_width
        else:
            x = field.x

        draw.text((x, field.y), text, font=font, fill=color)

    output = BytesIO()
    template = template.convert('RGB')
    template.save(output, format='JPEG', quality=config.output_quality, optimize=True)
    output.seek(0)
    return output
