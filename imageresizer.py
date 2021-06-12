#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from PIL import Image
import telegram, logging

def imageresize(immagine):
    img = Image.open(immagine)
    basewidth = 512
    baseheight = 512
    wpercent = (basewidth / float(img.size[0]))
    hpercent = (baseheight / float(img.size[1]))
    if hpercent < wpercent:
        wsize = int((float(img.size[0]) * float(hpercent)))
        img = img.resize((wsize, baseheight), Image.ANTIALIAS)
    else:
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    imageresized = immagine+"_resized.png"
    img.save(imageresized, "PNG")
    return imageresized

def botimageresize(update, context):
    user = update.message.from_user
    if hasattr(update.message, 'photo'):
        immagine = update.message.photo[-1].file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(immagine + ".jpg")
        logging.info("Photo of %s: %s", user.first_name, immagine + '.jpg')
        immagine = immagine + ".jpg"
    else:
        immagine = update.message.document.file_id
        photo_file = context.bot.get_file(immagine)
        photo_file.download(update.message.document.file_name)
        logging.info("File: %s", update.message.document.file_name)
        immagine = update.message.document.file_name

    imageresized = [imageresize(immagine), immagine]

    return imageresized

def main():
    print("Test: Image resizer")
    imageresize("test.jpg")
    imageresize("test.png")

    return 0

if __name__ == '__main__':
    main()
