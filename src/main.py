import pygame
import PIL.Image
import PdxParse
import cPickle, csv, json, struct
import math, os, sys

#===============================================================================
# DEFINES
#===============================================================================

BITS_PER_BYTE = 8
SIZEOF_INT = 4
SIZEOF_SHORT = 2

MIN_DEPTH = 8 # minimum bits for pixel for a pygame Surface
MIN_DEPTH_ALPHA = 16

BLACK = pygame.Color('black')
BLACK_TRANSPARENT = pygame.Color(0,0,0,0)
WHITE = pygame.Color('white')

PRV_UNKNOWN = 0
PRV_LAND = 1
PRV_WASTELAND = 2
PRV_OCEAN = 3
PRV_LAKE = 4


#===============================================================================
# CLASS DEFINITIONS
#===============================================================================

class Province:
   def __init__(self, name=u"Unnamed", id=-1, mapColor = BLACK, hash = None, pixels = None, bndRect = None,
                prvType=PRV_UNKNOWN):
      self.name = name
      self.id = id
      self.mapColor = mapColor
      self.hash = hash if hash is not None else hash_color(mapColor)
      self.pixels = pixels
      self.borderPixels = []
      self.bndRect = bndRect
      self.prvType = PRV_UNKNOWN
      
   def serialize(self):
      s = b""

      colorTpl = self.mapColor.r, self.mapColor.g, self.mapColor.b, self.mapColor.a
      bndRectTpl = self.bndRect.left, self.bndRect.top, self.bndRect.width, self.bndRect.height
      
      DATAFMT = [ (self.name, "s"),
                  (self.id, "I"),
                  (colorTpl, "B", len(colorTpl)),
                  (self.pixels, "B", len(self.pixels)),
                  (self.borderPixels, "B", len(self.borderPixels)),
                  (bndRectTpl, "I", len(bndRectTpl)),
                  (self.prvType, "I") ]
      
      for d in DATAFMT:
         length = -1
         if len(d) == 3:
            var, fmt, length = d
         elif len(d) == 2:
            var, fmt = d
         else: raise "Invalid data in serialize method!", d
         
         if length == 0: continue # empty data
         elif length == -1: # single variable
            s += struct.pack( fmt, var )
            print s
         elif length >= 1: # list of variables
            s += struct.pack("I", length)
            s += struct.pack( fmt*length, *var )
            print s
            
      return s
   
   def deserialize(self, s):
      # unpack
      offset = 0
      self.name = struct.unpack_from("s", s, offset)[0]
      offset += len(self.name)
      
      self.id = struct.unpack_from("I", s, offset)[0]
      offset += SIZEOF_INT
      
      colorTpl = struct.unpack_from("BBBB", s, offset)[0]
      offset += 4
      
      lenPixels = struct.unpack_from("I", s, offset)[0]
      offset += SIZEOF_INT
      self.pixels = struct.unpack_from("B"*lenPixels, s, offset)[0]
      offset += 1 * lenPixels
      
      lenBorderPixels = struct.unpack_from("I", s, offset)[0]
      offset += SIZEOF_INT
      self.borderPixels = struct.unpack_from("B"*lenBorderPixels, s, offset)[0]
      offset += 1 * lenBorderPixels
      
      bndRectTpl = struct.unpack_from("IIII", s, offset)[0]
      offset += 4 * SIZEOF_INT
      
      self.prvType = struct.unpack_from("I", s, offset)[0]
      offset += SIZEOF_INT
      
      # postprocessing
      self.mapColor = pygame.Color(*colorTpl)
      self.bndRect = pygame.Rect(*bndRectTpl)
      self.hash = hash_color(self.mapColor)
      
      # test
      print self.id, self.name, self.mapColor, self.prvType, self.bndRect
      print self.pixels, self.borderPixels
      
      
#===============================================================================
# GLOBAL FUNCTIONS
#===============================================================================

def hash_color(*args):
   if(len(args)==1):
      r,g,b = args[0][0], args[0][1], args[0][2]
   elif(len(args)==3):
      r,g,b = args[0], args[1], args[2]
   else:
      raise ValueError("Invalid arguments for hash_color:", args) 
   
   assert(0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255)
   hash = r << 16 | g << 8 | b << 0
   return hash

def unhash_color(hash):
   r,g,b = hash >> 16, hash%(256**2) >> 8, hash%256 >> 0
   return r,g,b

#===============================================================================
# MAIN PROGRAM 
#===============================================================================

def main():
   euDir = os.path.join("C:\\","Program Files (x86)","Steam","steamapps","common","Europa Universalis IV")
   
   mapFile = os.path.join(euDir, "map", "provinces.bmp")
   deffile = os.path.join(euDir, "map", "definition.csv")
   defaultMap = os.path.join(euDir, "map", "default.map")
   
   # read definition.csv
   sys.stdout.write("Building provinces... ")
   provinces = [None] * 2954
   colorHashToProvince = {}
   count = 0
   with open(deffile, 'r') as f:
      rdr = csv.reader(f, delimiter=';')
      
      for row in rdr:
         if len(row) < 5:
            print "Invalid line in definition.csv: %s" % row
            continue
         
         if not row[0].isdigit(): # or not row[5] == 'x': # probably the first line, just skip it
            continue
         
         try:
            id = int(row[0])
            color = int(row[1]), int(row[2]), int(row[3])
         except ValueError:
            print "Invalid line in definition.csv: %s" % row
            continue
         
         try:
            if(row[4]!=''): name = str(row[4])
            else: name = str(row[5])
         except ValueError:
            print "Invalid line in definition.csv: %s" % row
            continue
            
         hash = hash_color(color)
         prv = Province(name=name, id=id, mapColor=pygame.Color(color[0], color[1], color[2], 255), hash=hash)
         assert(id < len(provinces))
         provinces[id] = prv
         colorHashToProvince[hash] = prv
         count += 1
   print "%d ok" % count
   
   
   # read default.map
   sys.stdout.write("Parsing default map... ")
   prs = PdxParse.Parser(defaultMap)
   print "ok"
   print prs.read()   
      
   return

   # check if dump file exists
   if os.path.isfile("clrpixel.dmp"):
      sys.stdout.write("Loading dump file 'clrpixel.dmp'... ")
      # load dump
      colorHashToPixels = {}
      with open("clrpixel.dmp","rb") as f:
         bytes = f.read(SIZEOF_INT)
         
         numProvinces = struct.unpack('I', bytes)[0]
         assert(0 < numProvinces <= 2954)
         
         for i in range(numProvinces):
            bytes = f.read(2 * SIZEOF_INT)
            colorHash, numPixels = struct.unpack('II', bytes)
            assert(0 <= colorHash <= 256**3 and 0 <= numPixels <= 1000000)
            
            pixels = []
            for j in range(numPixels):
               bytes = f.read(2 * SIZEOF_SHORT)
               px = struct.unpack('HH', bytes)
               pixels.append(px)
               
            colorHashToPixels[colorHash] = pixels
            if colorHash == 0:
               print colorHash, ":", pixels
      print "ok"
   
   else:
      # read world map
      print("Building from world map... ")
      img = PIL.Image.open(mapFile)
      px = img.load()
      size_x, size_y = img.size
      
      print "Loaded '%s' (%dx%d px)." % ( mapFile, size_x, size_y )
      
      colorHashToPixels = {}
      
      numPixels = size_x*size_y
      count = 0
      
      for i in range(size_x):
         for j in range(size_y):
            color = px[i, j]
            colorHash = hash_color(color)
            
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
      save = True
      
      if bin and save:
         with open('clrpixel.dmp','wb') as f:
            f.write( struct.pack('I',numProvinces) )
            for clrHash,pixels in colorHashToPixels.items():
               f.write( struct.pack('II',clrHash, len(pixels)) )
               for px in pixels:
                  f.write( struct.pack('HH', px[0], px[1]))
      elif save:
         with open('clrpixel.dat','w') as f:
            f.write('number_of_provinces: %d\n' % numProvinces)
            for clrHash,pixels in colorHashToPixels.items():
               f.write('%d : ' % clrHash)
               f.write(' '.join(['(%d,%d)' % (px[0], px[1]) for px in pixels]))
               f.write('\n')
      
   
   sys.stdout.write("Populating provinces... ")
   count = 0
   totalBytes = 0
   for clrHash,pixels in colorHashToPixels.items():
      color = unhash_color(clrHash)
      
      xMin = min([px[0] for px in pixels])
      xMax = max([px[0] for px in pixels])
      yMin = min([px[1] for px in pixels])
      yMax = max([px[1] for px in pixels])

      bndRect = pygame.Rect(xMin, yMin, xMax-xMin+1, yMax-yMin+1)
      offset = bndRect.topleft
      
      prv = colorHashToProvince[clrHash]
      prv.bndRect = bndRect
      
      # build pixels bytearray
      lenB = int( math.ceil(1. * bndRect.width * bndRect.height / BITS_PER_BYTE ))
      b = bytearray(lenB)
      
      for p in pixels:
         px, py = p[0] - offset[0], p[1] - offset[1]
         index = py * bndRect.width + px
         
         byte = index // BITS_PER_BYTE
         shift = index % BITS_PER_BYTE
         
         b[byte] |= (1 << shift) # set bit in array
      
      prv.pixels = b
      prv.borderPixels = bytearray(lenB)
      
      # determine border pixels
      for byte in range(len(prv.pixels)):
         for bit in range(BITS_PER_BYTE):
            # skip all pixels which are not alive in the full province mask anyway
            if not prv.pixels[byte] & (1 << bit): continue
            
            idx = byte*BITS_PER_BYTE + bit
            border = False
            px = idx % bndRect.width
            py = idx // bndRect.width

            if(idx >= bndRect.width * bndRect.height): continue # leftover pixels? ignore
            elif(px == 0 or py == 0 or px == bndRect.width-1 or py == bndRect.height-1): # pixels bordering the bndRect? border!
               border = True
            else: # not on border? then we should have pixels in all directions ...
               last = idx - 1
               next = idx + 1
               top = idx - bndRect.width
               btm = idx + bndRect.width
               
               for adjIdx in (last,next,top,btm):
                  adjByte = adjIdx // BITS_PER_BYTE
                  adjBit = adjIdx % BITS_PER_BYTE
                  
                  if( not prv.pixels[adjByte] & (1<<adjBit) ):
                     border = True
                     break
                  
            if border:
               prv.borderPixels[byte] |= (1 << bit) # set bit in array
               
      totalBytes += lenB
      count += 1
      
   print "%d ok (%d KB)" % (count, totalBytes / 1024)
   
   
   testprv = provinces[125]

   print testprv.name, testprv.bndRect
   #[sys.stdout.write('{0:08b}'.format(testprv.pixels[i])) for i in range(len(testprv.pixels))]
   surf = pygame.Surface((testprv.bndRect.size))
   surf.fill(BLACK)
   brdSurf = pygame.Surface((testprv.bndRect.size))
   brdSurf.fill(BLACK)
   
   for byte in range(len(testprv.pixels)):
      for bit in range(BITS_PER_BYTE):
         active = (1 << bit) & testprv.pixels[byte]
         border = (1 << bit) & testprv.borderPixels[byte]
         x = (byte * BITS_PER_BYTE + bit) % testprv.bndRect.width
         y = (byte * BITS_PER_BYTE + bit) // testprv.bndRect.width
         if active: surf.set_at((x,y), WHITE)
         if border: brdSurf.set_at((x,y), WHITE)
   pygame.image.save(surf, 'test.bmp')
   pygame.image.save(brdSurf, 'testBrd.bmp')
   
   testprv.serialize()
   
   worldmap = pygame.Surface((5632,2048))
   for p in provinces:
      if p is None: continue
      for byte in range(len(p.pixels)):
         for bit in range(BITS_PER_BYTE):
            border = (1 << bit) & p.borderPixels[byte]
            if not border:
               active = (1 << bit) & p.pixels[byte]
            
            x = (byte * BITS_PER_BYTE + bit) % p.bndRect.width
            y = (byte * BITS_PER_BYTE + bit) // p.bndRect.width
            
            if border: pass
               #worldmap.set_at((x+p.bndRect.left,y+p.bndRect.top), BLACK)
            elif active:
               worldmap.set_at((x+p.bndRect.left,y+p.bndRect.top), pygame.Color(34,190,240,255))
      print p.id
   pygame.image.save(worldmap,'world.bmp')
         
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
   
if __name__=='__main__':
   main()