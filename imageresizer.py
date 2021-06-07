#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from PIL import Image

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

def main():
    print("Test: Image resizer")
    imageresize("test.jpg")
    imageresize("test.png")

    return 0

if __name__ == '__main__':
    main()
