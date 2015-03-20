import pygame
import struct
import os

#===============================================================================
# DEFINES
#===============================================================================

MIN_DEPTH = 8 # minimum bits for pixel for a pygame Surface
MIN_DEPTH_ALPHA = 16

BLACK = pygame.Color('black')
BLACK_TRANSPARENT = pygame.Color(0,0,0,0)
WHITE = pygame.Color('white')


#===============================================================================
# CLASS DEFINITIONS
#===============================================================================

class Province:
   def __init__(self, name=u"Unnamed", id=-1, mapColor = BLACK, pixels = None, offset = (0,0)):
      self.name = name
      self.id = id
      self.mapColor = mapColor
      self.pixels = pixels
      self.offset = offset

#===============================================================================
# MAIN PROGRAM 
#===============================================================================

mapfile = "C:\\Temp\\EU4\\map\\provinces.bmp"

img = PIL.Image.open(mapfile)
px = img.load()
size_x, size_y = img.size

print "Loaded '%s' (%dx%d px)." % ( mapfile, size_x, size_y )

colorHashToPixels = {}

numPixels = size_x*size_y
count = 0

for i in range(size_x):
   for j in range(size_y):
      color = px[i, j]
      #colorHash = 256**2 * color[0] + 256 * color[1] + color[2]
      colorHash = color[0] << 16 | color[1] << 8 | color[2]
      
      if colorHash in colorHashToPixels:
         colorHashToPixels[colorHash].append((i,j))
      else:
         colorHashToPixels[colorHash] = [(i,j), ]
      
      count += 1
      if(count % (numPixels//10) == 0):
         print "%.0f%%" % (100.0 * count / numPixels)
         
numProvinces = len(colorHashToPixels.keys())         
print "Number of provinces: %d" % numProvinces

print "Saving color/pixel dictionary..."

bin = True
save = False

if bin and save:
   with open('clrpixel.dmp','wb') as f:
      f.write( struct.pack('I',numProvinces) )
      for clrHash,pixels in colorHashToPixels.items():
         f.write( struct.pack('I',clrHash) )
         f.write( struct.pack('I',len(pixels)))
         for px in pixels:
            f.write( struct.pack('HH', px[0], px[1]))
elif save:
   with open('clrpixel.dat','w') as f:
      f.write('number_of_provinces: %d\n' % numProvinces)
      for clrHash,pixels in colorHashToPixels.items():
         f.write('%d : ' % clrHash)
         f.write(' '.join(['(%d,%d)' % (px[0], px[1]) for px in pixels]))
         f.write('\n')
         
count = 0
for clrHash,pixels in colorHashToPixels.items():
   color = clrHash >> 16, clrHash%(256**2) >> 8, clrHash%256 >> 0
   
   srf = pygame.Surface((size_x,size_y), depth=MIN_DEPTH_ALPHA, flags=pygame.SRCALPHA)
   srf.fill(BLACK_TRANSPARENT)
   for px in pixels:
      srf.set_at(px, WHITE)
   
   bndRect = srf.get_bounding_rect()
   smallSrf = pygame.Surface(bndRect.size, depth=MIN_DEPTH_ALPHA, flags=pygame.SRCALPHA)
   smallSrf.blit(srf, dest=(0,0), area=bndRect)
   
   del srf
   count += 1
   pygame.image.save(smallSrf, os.path.join('C:\\','Temp','EU4','out','%04d.bmp' % count))
   
   offset = bndRect.topleft
   #print offset
   
   prv = Province(mapColor=color, pixels=pixels, offset=offset)


# export mask bitmaps for every province
# print "Writing mask files..."
#
# count = 0
# for clrHash,pixels in colorHashToPixels.items():
#    #mask = pygame.mask.Mask((size_x, size_y))
#    #mask.clear()
#    #for p in pixels: mask.set_at(p, True)
#    
#    srf = pygame.Surface((size_x,size_y), depth=MIN_DEPTH)
#    for px in pixels:
#       srf.set_at(px, WHITE)
#       
#    count += 1
#    pygame.image.save(srf, os.path.join('C:\\','Temp','EU4','out','%04d.bmp' % count))