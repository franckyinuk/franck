import os
from PIL import Image
import datetime
from pathlib import Path


def GetStaticImage():
  return "colour-wheel.jpg"

def ConvertColours(imageObject):
  # convert to greyscale
  return imageObject.convert(mode="L")

def PixeliseImage(imageFile, desiredSizeTuple):
  imageObject = Image.open(imageFile)
  imageSize = imageObject.size
  imageRatio = imageSize[0]/imageSize[1]

  newImageRatio = desiredSizeTuple[0]/desiredSizeTuple[1]
  croppedSize = list(imageSize)
  if imageRatio > newImageRatio:
    # the old image is wider than required
    croppedSize[0] = int(imageSize[1] * newImageRatio)
  else:
    croppedSize[1] = int(imageSize[0] / newImageRatio)

  cropBox = (int((imageSize[0] - croppedSize[0]) / 2),
             int((imageSize[1] - croppedSize[1]) / 2),
             int((imageSize[0] - croppedSize[0]) / 2 + croppedSize[0]),
             int((imageSize[1] - croppedSize[1]) / 2 + croppedSize[1])
            )
  # FMTODO we should probably to the resize first and then the crop, as the resize would more quickly reduce the size of the object so the other op will will be faster
  # crop the image to remove the unwanted pixels
  newImageObject = imageObject.crop(cropBox)
  # resize to the number of wanted pixel
  newImageObject = newImageObject.resize(desiredSizeTuple)
  # scale up the image to compare it to the original (debug only)
  newImageObject = newImageObject.resize(croppedSize, resample=Image.Resampling.BOX)

  return newImageObject


def ProcessSpecificImage(imageFilePath, desiredSizeTuple):
  print("Processing new image")

  
  newImageObject = PixeliseImage(imageFilePath, desiredSizeTuple)
  newImageObject = ConvertColours(newImageObject)

  fileName = os.path.basename(imageFilePath)
  [fileNameNoExtension, extension] = fileName.rsplit(".")
  #timestamp = str(int(datetime.datetime.now().timestamp()))
  newImageFolder = os.path.join(".", "compressedFiles")
  newImagePath = os.path.join(newImageFolder, "{}_{}x{}.{}".format(fileNameNoExtension, desiredSizeTuple[0], desiredSizeTuple[1], extension))  
  Path(newImageFolder).mkdir(parents=True, exist_ok=True)
  newImageObject.save(newImagePath)

  return

if __name__ == "__main__":
  sizeSamples = [(45, 30), (60, 40), (75, 50), (100, 66), (120, 80), (150, 100)]
  for file in os.listdir("./samples"):
    for size in sizeSamples:
      ProcessSpecificImage(os.path.join("./samples", file), size)
  