#!/usr/bin/env python
import argparse
import asyncio
import logging
import sys
import os
import numpy as np

from catprinter import logger
from catprinter import cmds
from catprinter.ble import run_ble
from catprinter.img import read_img, show_preview

import xkcd
import tempfile
from PIL import Image, ImageDraw, ImageFont

# config
LOG_LEVEL = "info"
DITHERING_ALGO = "floyd-steinberg"
SHOW_PREVIEW = False
TOP_FIRST = False
DEVICE = ""
INTENSITY = 0x5D

XKCD_NO = 3115

def configure_logger(log_level):
    logger.setLevel(log_level)
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(log_level)
    logger.addHandler(h)


def add_info_to_image(image_path, comic, comic_no):
    # Add comic number, title, and release date to the top of the image, and alt text to the bottom.
    # Example:
    # XKCD #1234: Example Title
    # |    [original image]    |
    # |                        |
    # Comic alt text goes here.
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    # use the Lucida font if available, otherwise default
    try:
        header_font = ImageFont.truetype("LSANSD.ttf", 18)
        alt_font = ImageFont.truetype("LSANSI.ttf", 14)
    except IOError:
        logger.warning("Lucida font not found. Using default font.")
        header_font = ImageFont.load_default(18)
        alt_font = ImageFont.load_default(14)

    header_text = f"XKCD #{comic_no}\n{comic.getTitle()}" #\n(released {comic.getDate()}, resolution {img.width}x{img.height})"
    alt_text = comic.getAltText()
    # resize image to fit printer exactly
    img = img.resize((cmds.PRINTER_WIDTH_PIXELS, int(img.height * (cmds.PRINTER_WIDTH_PIXELS / img.width))))
    # compute text wrapping for alt text
    wrapped_alt_text = wrap_text(draw, alt_font, alt_text)
    # add size to image to fit header and alt text
    (_, _, header_w, header_h) = draw.multiline_textbbox((0, 0), header_text, font=header_font)
    (_, _, alt_w, alt_h) = draw.multiline_textbbox((0, 0), wrapped_alt_text, font=alt_font)
    new_img = Image.new("RGB", (img.width, int(img.height + header_h + alt_h + 10)), "white")
    new_img.paste(img, (0, int(header_h + 5)))
    draw = ImageDraw.Draw(new_img)
    draw.multiline_text((cmds.PRINTER_WIDTH_PIXELS/2, 0), header_text, anchor="ma", align="center", fill="black", font=header_font)
    draw.multiline_text((0, img.height + header_h + 5), wrapped_alt_text, fill="black", font=alt_font)
    output_path = os.path.join(tempfile.gettempdir(), "comic_with_info.png")
    new_img.save(output_path)

def wrap_text(draw, alt_font, alt_text):
    max_width = cmds.PRINTER_WIDTH_PIXELS
    words = alt_text.split(' ')
    wrapped_alt_text = ""
    line = ""
    for word in words:
        test_line = line + word + " "
        w = draw.textlength(test_line, font=alt_font)
        if w <= max_width:
            line = test_line
        else:
            wrapped_alt_text += line + "\n"
            line = word + " "
    wrapped_alt_text += line
    return wrapped_alt_text

def print_xkcd(xkcd_no=None):

    log_level = getattr(logging, LOG_LEVEL.upper())
    configure_logger(log_level)

    comic_no = xkcd_no if xkcd_no is not None else xkcd.getLatestComicNum()

    logger.info(f"Fetching xkcd comic #{xkcd_no if xkcd_no is not None else str(comic_no) + ' (latest)'}...")

    comic = xkcd.getComic(comic_no)
    comic.download(output=tempfile.gettempdir(), outputFile="comic.png", silent=False)

    filename = os.path.join(tempfile.gettempdir(), "comic.png")
    logger.info(f"Downloaded comic to {filename}")
    add_info_to_image(filename, comic, comic_no)
    logger.info("Added comic info to image.")
    filename = os.path.join(tempfile.gettempdir(), "comic_with_info.png")

    if not os.path.exists(filename):
        logger.info("🛑 File not found. Exiting.")
        raise

    try:
        bin_img_bool = read_img(
            filename,
            cmds.PRINTER_WIDTH_PIXELS,
            DITHERING_ALGO,
        )
        logger.info(f"✅ Read image: {bin_img_bool.shape} (h, w) pixels")

        # Preview the image before potential rotation
        if SHOW_PREVIEW:
            preview_img_uint8 = (~bin_img_bool).astype(np.uint8) * 255
            show_preview(preview_img_uint8)

        # Rotate image 180 degrees unless --top-first is specified
        if not TOP_FIRST:
            logger.info("🔄 Rotating image 180 degrees (to print the bottom first).")
            bin_img_bool = np.rot90(bin_img_bool, k=2)
        else:
            logger.info("ℹ️  Printing image top-first as requested.")
    except RuntimeError as e:
        logger.error(f"🛑 {e}")
        raise
    except Exception as e:
        logger.error(f"🛑 Unexpected error during image processing: {e}", exc_info=True)
        raise

    try:
        logger.info("Preparing image data buffer for MXW01...")
        image_data_buffer = cmds.prepare_image_data_buffer(bin_img_bool)
        logger.info(
            f"✅ Generated MXW01 image data buffer: {len(image_data_buffer)} bytes"
        )

        asyncio.run(
            run_ble(image_data_buffer, device=DEVICE, intensity=INTENSITY)
        )

    except ValueError as e:
        logger.error(f"🛑 Error preparing image buffer: {e}")
        raise
    except Exception as e:
        logger.error(
            f"🛑 Unexpected error during command prep or BLE execution: {e}",
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    print_xkcd(XKCD_NO)
