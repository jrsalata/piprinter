import base64
from io import BytesIO

from PIL import Image
from escpos.printer import Dummy

# Fallback max image width (in dots) used when the printer's profile doesn't
# declare a media width (e.g. the default profile, or no `profile:` set in
# config.yaml). Matches the printable width of common 58mm thermal printers.
# Without some cap, an oversized image is sent to the printer with a raster
# width the hardware doesn't expect, and many printers respond by dumping the
# raw image bytes as garbled text instead of rendering the image.
DEFAULT_MAX_IMAGE_WIDTH = 384

# Style properties that get reset back to a sane default after a block
# that requested a one-off style, so later blocks aren't affected by it.
STYLE_RESET_DEFAULTS = {
    'align': 'left',
    'font': 'a',
    'bold': False,
    'underline': 0,
    'invert': False,
    'smooth': False,
    'flip': False,
    'double_width': False,
    'double_height': False,
    'custom_size': False,
    'normal_textsize': True,
}

# Default style for title blocks, overridable per-key by a block's own style.
TITLE_DEFAULT_STYLE = {
    'align': 'center',
    'bold': True,
    'double_width': True,
    'double_height': True,
}

# PreprocessBuilder is a class that will take
# commands to build parts of a print job before sending
# it to the printer
# This allows for dynamically building a print job based on user input
# The output is going to be the raw commands from our dummy printer
# Users should be able to build
# - titles
# - dividers
# - images
# - text blocks
# - qr codes
class PreprocessBuilder:
    # profile, if given, should be an already-resolved escpos printer profile
    # object (e.g. the real printer's `.profile`), not a profile name string -
    # it's assigned directly rather than re-resolved by name so callers can
    # hand over whatever profile instance the actual printer is using.
    def __init__(self, profile=None):
        self.printer = Dummy()
        if profile is not None:
            self.printer.profile = profile

    def add_title(self, title):
        self.printer.textln(title)

    def set_properties(self, align=None, font=None, bold=None, underline=None, width=None, height=None, density=None, invert=None, smooth=None, flip=None, normal_textsize=None, double_width=None, double_height=None, custom_size=None):
        self.printer.set(align=align, font=font, bold=bold, underline=underline, width=width, height=height, density=density, invert=invert, smooth=smooth, flip=flip, normal_textsize=normal_textsize, double_width=double_width, double_height=double_height, custom_size=custom_size)

    def reset_properties(self, style):
        reset = {k: v for k, v in STYLE_RESET_DEFAULTS.items() if k in style}
        if reset:
            self.printer.set(**reset)

    # note that this will error if count < 0
    # we will let it silently fail
    def add_newline(self, count=1):
        if count < 0:
            return
        self.printer.ln(count=count)

    def add_divider(self):
        self.printer.textln("-" * 24)

    def add_text_block(self, text):
        self.printer.textln(text)

    # Note that image_path should be a PIL image object, not a file path
    def add_image(self, image_path, center = True):
        image_path = self._fit_image_to_printer(image_path)
        self.printer.image(image_path, center=center)

    # Downscale an image to the printer's known media width, preserving
    # aspect ratio, so it never gets sent to the printer wider than the
    # hardware can render.
    def _fit_image_to_printer(self, image):
        max_width = self._max_image_width()
        if image.width <= max_width:
            return image
        new_height = max(1, round(image.height * (max_width / image.width)))
        return image.resize((max_width, new_height), Image.LANCZOS)

    def _max_image_width(self):
        try:
            return int(self.printer.profile.profile_data["media"]["width"]["pixels"])
        except (KeyError, ValueError):
            return DEFAULT_MAX_IMAGE_WIDTH

    def add_qr_code(self, data, size=3, center = True):
        self.printer.qr(data, size=size, center=center)

    # Builds a print job from an ordered list of block dicts, e.g.:
    # {"type": "text", "text": "hello", "style": {"align": "center", "bold": true}}
    # Supported types: title, divider, text, newline, qr, image
    # "style" is optional on any block and accepts the same keys as set_properties().
    # The style is applied before the block and reset back to defaults after it,
    # so it never bleeds into later blocks.
    def build_from_blocks(self, blocks):
        for block in blocks:
            block_type = block.get('type')
            style = block.get('style') or {}

            if block_type == 'title':
                style = {**TITLE_DEFAULT_STYLE, **style}

            if style:
                self.set_properties(**style)

            if block_type == 'title':
                self.add_title(block.get('text', ''))
            elif block_type == 'divider':
                self.add_divider()
            elif block_type == 'text':
                self.add_text_block(block.get('text', ''))
            elif block_type == 'newline':
                self.add_newline(count=block.get('count', 1))
            elif block_type == 'qr':
                self.add_qr_code(block.get('data', ''), size=block.get('size', 3), center=block.get('center', True))
            elif block_type == 'image':
                image = self._decode_image(block.get('image', ''))
                if image is not None:
                    self.add_image(image, center=block.get('center', True))
            else:
                raise ValueError(f"Unknown block type: {block_type}")

            if style:
                self.reset_properties(style)

        return self

    @staticmethod
    def _decode_image(data_url):
        if not data_url:
            return None
        if ',' in data_url:
            data_url = data_url.split(',', 1)[1]
        return Image.open(BytesIO(base64.b64decode(data_url)))

    def get_commands(self):
        self.printer.cut()
        return self.printer.output
