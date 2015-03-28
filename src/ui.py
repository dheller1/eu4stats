import sys
from PyQt4 import QtCore, QtGui


class MainWindow(QtGui.QMainWindow):
   def __init__(self, parent=None):
      QtGui.QMainWindow.__init__(self, parent)
      
      self.resize(640,480)
      self.setWindowTitle("EU4 Stats")
      
      sa = QtGui.QScrollArea()
      self.mapWidget = MapWidget()
      
      sa.setWidget(self.mapWidget)
      self.setCentralWidget(sa)

class MapWidget(QtGui.QWidget):
   def __init__(self, parent=None):
      QtGui.QWidget.__init__(self, parent)
      
      self.setBackgroundRole(QtGui.QPalette.Base)
      self.setAutoFillBackground(True)
      self.resize(5632,2048)
      
   def Fill(self, provinces, tags):
      ptr = QtGui.QPainter(self)
      
      for prv in provinces:
         if prv is None: continue
         bmp = prv.ToQBitmap()
         brush = QtGui.QBrush(bmp)
         
         c = tags[prv.history.children['owner'].data].color
         brush.setColor(QtGui.QColor(c.r, c.g, c.b))
         
         ptr.setBrush(brush)
         
         r = prv.bndRect
         ptr.drawRect(r.left, r.top, r.w, r.h)
         
      
def main():
   app = QtGui.QApplication(sys.argv)
   
   wnd = MainWindow()
   wnd.show()
   
   sys.exit(app.exec_())
   
if __name__ == '__main__':
   main()