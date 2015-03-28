import wx

class DrawCanvas(wx.Window):
   def __init__(self, *args, **kwargs):
      super(DrawCanvas, self).__init__(*args, **kwargs)
      
      self.Bind(wx.EVT_PAINT, self.OnPaint)
      
   def OnPaint(self, evt):
      dc = wx.PaintDC(self)
      self.Render(dc)
      
   def Render(self, dc):
      dc.DrawText("Testing", 40, 60)
      dc.SetBrush(wx.GREEN_BRUSH)
      dc.SetPen(wx.Pen(wx.Colour(255,0,0), 5))
      dc.DrawCircle(200,100,25)
      
      # draw rect
      dc.SetBrush(wx.BLUE_BRUSH)
      dc.SetPen(wx.Pen(wx.Colour(255,175,175), 10))
      dc.DrawRectangle(300, 100, 400, 200)
      
      # draw line
      dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
      dc.DrawLine(300,100,700,300)

class MainWindow(wx.Frame):
   def __init__(self, *args, **kwargs):
      super(MainWindow, self).__init__(*args, **kwargs)
      
      self.InitUi()
      
   def InitUi(self):
      # init menu
      menubar = wx.MenuBar()
      fileMenu = wx.Menu()
      fitem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
      menubar.Append(fileMenu, '&File')
      self.SetMenuBar(menubar)
      
      # init canvas
      canvas = DrawCanvas(self, -1)
      
      # bind menu events
      self.Bind(wx.EVT_MENU, self.OnQuit, fitem)
      
      # init geometry
      self.SetSize((800, 600))
      self.SetTitle('Simple menu')
      self.Center()
      self.Show(True)
        
   def OnQuit(self, e):
      self.Close()

app = wx.App()
wnd = MainWindow(None)
app.MainLoop()