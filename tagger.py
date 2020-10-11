import cv2
import sys
import webcolors
from PIL import Image
import glob
import os

Image.MAX_IMAGE_PIXELS = None


def ResizeWithAspectRatio(image, width=None, height=None):
    dim = None
    (w, h) = image.size

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return image.resize(dim)


def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = abs(r_c - requested_colour[0])
        gd = abs(g_c - requested_colour[1])
        bd = abs(b_c - requested_colour[2])
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name

def getMinSize(x, y, h, w):
    a = min(x*h, y*w)
    a = int(a)
    return (a, a)

def getFaceNum(imagePath):
    # Get user supplied values
    cascPath = "get_face2.xml"

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)

    # Read the image
    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    (x0, y0) = image.shape[:2]
    # Detect faces in the image
    faces = faceCascade.detectMultiScale(
        gray,
        minNeighbors=1,
        minSize=(20,20),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return len(faces)

def getMainColor(imagePath):
    im = Image.open(imagePath)
    im = ResizeWithAspectRatio(im, width=1000)
    im = im.convert("P", palette=Image.ADAPTIVE, colors=3)
    im = im.convert("RGB", palette=Image.ADAPTIVE)
    rgb = max(im.getcolors(im.size[0]*im.size[1]))[1]
    actual_name, closest_name = get_colour_name(rgb)
    return closest_name

def faceNum2Tag(faceNum):
    if (faceNum == 1):
        return 'single'
    elif (faceNum > 1):
        return 'multiple'
    else:
        return 'environment'

def complex2Descrip(complexity):
    if (complexity < 30):
        return 'simple'
    elif (complexity < 50):
        return 'normal'
    elif (complexity < 80):
        return 'medium'
    else:
        return 'complexed'

def getComplexity(imagePath):
    im = Image.open(imagePath)
    imOrig = ResizeWithAspectRatio(im, width=1000)
    imNew = imOrig.convert("P", palette=Image.ADAPTIVE, colors=10)
    imNew = imNew.convert("RGB", palette=Image.ADAPTIVE)
    w, h = imOrig.size
    devi = 0
    for x in range(w):
        for y in range(h):
            orig = imOrig.getpixel((x, y))
            new = imNew.getpixel((x, y))
            devi += abs(orig[0] - new[0]) + \
                abs(orig[1] - new[1]) + abs(orig[2] - new[2])

    complexity = devi / float(w*h)
    return complex2Descrip(complexity)

path = sys.argv[1]
print("path: {}".format(path))
data_path = os.path.join(path, '*g')
files = glob.glob(data_path)
print('there are {} files'.format(len(files)))
i = 1
for f in files:
    try:
        faceNum = getFaceNum(f)
        mainColor = getMainColor(f)
        complexity = getComplexity(f)

        print('Image {} face number is: {}, Main color is: {}'.format(i, faceNum, mainColor))
        filename, file_extension = os.path.splitext(f)
        parentPath = os.path.dirname(f)
        newName = '{} {} {}'.format(faceNum2Tag(faceNum), mainColor, complexity)
        numCount = ' (0)'
        c = 0
        newNameAbs = parentPath + '\\' + newName + numCount + file_extension
        while(os.path.isfile(newNameAbs)):
            c += 1
            numCount = ' ({})'.format(c)
            newNameAbs = parentPath + '\\' + newName + numCount + file_extension
        os.rename(f, newNameAbs)
    except Exception:
        print('Image {} cannot be converted'.format(i))
    i += 1
