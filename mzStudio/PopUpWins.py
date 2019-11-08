import wx, os

import mzStudio as bb

#class OverlayFrame(wx.Frame):
    #def __init__(self, parent, pos=(0,0)):
        #wx.Frame.__init__(self, parent, -1, "Shaped Window", pos=pos,
                         #style =
                           #wx.FRAME_SHAPED
                         #| wx.SIMPLE_BORDER
                         #| wx.FRAME_NO_TASKBAR
                         #| wx.STAY_ON_TOP
                         #)
        #self.parent = parent
        #self.hasShape = False
        #self.delta = (0,0)
        ##self.bmp = images.Vippi.GetBitmap()
        #self.bmp = wx.Bitmap(os.path.join(os.path.dirname(__file__), r'win2.bmp'))
        
        #w, h = self.bmp.GetWidth(), self.bmp.GetHeight()
        #self.SetClientSize( (w, h) )

        
        #self.SetWindowShape()

        #dc = wx.ClientDC(self)
        #dc.DrawBitmap(self.bmp, 0,0, True)
        ##panel = wx.Panel(self)
        #panel = self
        
        #clearbtn = wx.Button(panel, -1, "Clear")
        #clearbtn.SetBackgroundColour("white")
        #clearbtn.Bind(wx.EVT_BUTTON, self.OnXIC)
        
        #overlaybtn = wx.Button(panel, -1, "Overlay (Clear)")
        #overlaybtn.SetBackgroundColour("white")
        #overlaybtn.Bind(wx.EVT_BUTTON, self.OnPrec)
        
        #xic_mz = float(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        #st2 = wx.StaticText(panel, -1, str(xic_mz))
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #sizer.Add(xicbtn, 0, wx.ALL, 5)
        #sizer.Add(precbtn, 0, wx.ALL, 5)
        #sizer.Add(st, 0, wx.ALL, 5)
        #sizer.Add(self.tolerance, 0, wx.ALL, 5)
        #sizer.Add(st2, 0, wx.ALL, 5)
        #st2.SetBackgroundColour("white")
        #panel.SetSizer(sizer)

        #sizer.Fit(panel)
        #sizer.Fit(self)
        #self.Layout()        
        
        #self.Bind(wx.EVT_LEFT_DCLICK,   self.OnDoubleClick)
        #self.Bind(wx.EVT_LEFT_DOWN,     self.OnLeftDown)
        #self.Bind(wx.EVT_LEFT_UP,       self.OnLeftUp)
        #self.Bind(wx.EVT_MOTION,        self.OnMouseMove)
        #panel.Bind(wx.EVT_RIGHT_UP,      self.OnExit)
        #self.Bind(wx.EVT_PAINT,         self.OnPaint)        

    #def OnXIC(self, evt): 
        #print "1"
        #print "One"
        #xic_mz = float(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        #toler = float(self.tolerance.GetStringSelection())/float(2.0)
        #lo = xic_mz - toler
        #hi = xic_mz + toler
        #currentPage = self.parent.parent.ctrl.GetPage(self.parent.parent.ctrl.GetSelection())
        #currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]

        #frm = bb.xicFrame(currentPage, currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]], currentPage.msdb.active_file)
        #win = frm.get_next_available_window()
        #i = frm.GetXICEntries()
        #frm.grid.SetCellValue(i, 0, str(win))
        #frm.grid.SetCellValue(i, 1, str(lo))
        #frm.grid.SetCellValue(i, 2, str(hi))
        #frm.grid.SetCellValue(i, 3, 'Full ms ')
        #frm.grid.SetCellValue(i, 5, 'Auto')
        #frm.grid.SetCellValue(i, 6, '1')
        #frm.grid.SetCellValue(i, 7, '1')
        #frm.grid.SetCellValue(i, 8, 'x')
        #frm.mark_base.append({})
        
        #frm.OnClick(None)
        #frm.Destroy()        
        
        #currentPage.Window.UpdateDrawing()
        #currentPage.Refresh()   
    
    #def OnPrec(self, evt):
        #fr = bb.findFrame(self.parent.parent)
        #fr.prec.SetValue(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        #toler = float(self.tolerance.GetStringSelection())/float(2.0)
        #fr.tol.SetValue(str(toler))
        #fr.OnClick(None)
    
    #def SetWindowShape(self, *evt):
        ## Use the bitmap's mask to determine the region
        #r = wx.RegionFromBitmap(self.bmp)
        #self.hasShape = self.SetShape(r)


    #def OnDoubleClick(self, evt):
        #if self.hasShape:
            #self.SetShape(wx.Region())
            #self.hasShape = False
        #else:
            #self.SetWindowShape()


    #def OnPaint(self, evt):
        #dc = wx.PaintDC(self)
        #dc.DrawBitmap(self.bmp, 0,0, True)

    #def OnExit(self, evt):
        #self.Close()


    #def OnLeftDown(self, evt):
        #self.CaptureMouse()
        #x, y = self.ClientToScreen(evt.GetPosition())
        #originx, originy = self.GetPosition()
        #dx = x - originx
        #dy = y - originy
        #self.delta = ((dx, dy))
        #evt.Skip()


    #def OnLeftUp(self, evt):
        #if self.HasCapture():
            #self.ReleaseMouse()
        #evt.Skip()


    #def OnMouseMove(self, evt):
        #if evt.Dragging() and evt.LeftIsDown():
            #x, y = self.ClientToScreen(evt.GetPosition())
            #fp = (x - self.delta[0], y - self.delta[1])
            #self.Move(fp)
        #evt.Skip()

class TestFrame(wx.Frame):
    '''
    
    This frame is used by PepCalc so that after calculating peptitide masses, XICs and MS/MS spectra can be located within rawfiles.
    
    
    '''
    def __init__(self, parent, pos=(0,0)):
        wx.Frame.__init__(self, parent, -1, "Shaped Window", pos=pos,
                         style =
                           wx.FRAME_SHAPED
                         | wx.SIMPLE_BORDER
                         | wx.FRAME_NO_TASKBAR
                         | wx.STAY_ON_TOP
                         )
        self.parent = parent
        self.hasShape = False
        self.delta = (0,0)
        #self.bmp = images.Vippi.GetBitmap()
        self.bmp = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', r'win2.bmp'))
        
        w, h = self.bmp.GetWidth(), self.bmp.GetHeight()
        self.SetClientSize( (w, h) )

        
        self.SetWindowShape()

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)
        #panel = wx.Panel(self)
        panel = self
        st = wx.StaticText(panel, -1, "Tolerance")
        st.SetBackgroundColour("white")
        xicbtn = wx.Button(panel, -1, "XIC")
        xicbtn.SetBackgroundColour("white")
        precbtn = wx.Button(panel, -1, "Find Precursors")
        precbtn.SetBackgroundColour("white")
        #self.tolerance = wx.TextCtrl(panel, -1, "0.01")
        self.tolerance = cb = wx.ComboBox(panel, 501, "0.02", choices=['0.01', '0.02', '0.1', '0.2','0.5','1', '3', '5', '10'], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.tolerance.SetStringSelection('0.01')
        xicbtn.Bind(wx.EVT_BUTTON, self.OnXIC)
        precbtn.Bind(wx.EVT_BUTTON, self.OnPrec)
        xic_mz = float(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        st2 = wx.StaticText(panel, -1, str(xic_mz))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(xicbtn, 0, wx.ALL, 5)
        sizer.Add(precbtn, 0, wx.ALL, 5)
        sizer.Add(st, 0, wx.ALL, 5)
        sizer.Add(self.tolerance, 0, wx.ALL, 5)
        sizer.Add(st2, 0, wx.ALL, 5)
        st2.SetBackgroundColour("white")
        panel.SetSizer(sizer)

        sizer.Fit(panel)
        sizer.Fit(self)
        self.Layout()        
        
        self.Bind(wx.EVT_LEFT_DCLICK,   self.OnDoubleClick)
        self.Bind(wx.EVT_LEFT_DOWN,     self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP,       self.OnLeftUp)
        self.Bind(wx.EVT_MOTION,        self.OnMouseMove)
        panel.Bind(wx.EVT_RIGHT_UP,      self.OnExit)
        self.Bind(wx.EVT_PAINT,         self.OnPaint)        

    def OnXIC(self, evt): 
        print "1"
        print "One"
        xic_mz = float(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        toler = float(self.tolerance.GetStringSelection())/float(2.0)
        lo = xic_mz - toler
        hi = xic_mz + toler
        currentPage = self.parent.parent.parent.ctrl.GetPage(self.parent.parent.parent.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]

        frm = bb.xicFrame(currentPage, currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]], currentPage.msdb.active_file)
        win = frm.get_next_available_window()
        i = frm.GetXICEntries()
        frm.grid.SetCellValue(i, 0, str(win))
        frm.grid.SetCellValue(i, 1, str(lo))
        frm.grid.SetCellValue(i, 2, str(hi))
        frm.grid.SetCellValue(i, 3, 'Full ms ')
        frm.grid.SetCellValue(i, 5, 'Auto')
        frm.grid.SetCellValue(i, 6, '1')
        frm.grid.SetCellValue(i, 7, '1')
        frm.grid.SetCellValue(i, 8, 'x')
        frm.grid.SetCellValue(i, 14, self.parent.FindWindowByName("sequence").GetValue() + ' ' + str(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[0].strip()))
        frm.mark_base.append({})
        
        frm.OnClick(None)
        frm.Destroy()        
        
        currentPage.Window.UpdateDrawing()
        currentPage.Refresh()   
    
    def OnPrec(self, evt):
        fr = bb.findFrame(self.parent.parent.parent)
        fr.prec.SetValue(self.parent.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        
        toler = float(self.tolerance.GetStringSelection())/float(2.0)
        
        fr.tol.SetValue(str(toler))
        fr.OnClick(None)
    
        self.Destroy()
    
    def SetWindowShape(self, *evt):
        # Use the bitmap's mask to determine the region
        #r = wx.RegionFromBitmap(self.bmp)
        r = wx.Region(self.bmp)
        self.hasShape = self.SetShape(r)


    def OnDoubleClick(self, evt):
        if self.hasShape:
            self.SetShape(wx.Region())
            self.hasShape = False
        else:
            self.SetWindowShape()


    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)

    def OnExit(self, evt):
        self.Close()


    def OnLeftDown(self, evt):
        self.CaptureMouse()
        x, y = self.ClientToScreen(evt.GetPosition())
        originx, originy = self.GetPosition()
        dx = x - originx
        dy = y - originy
        self.delta = ((dx, dy))
        evt.Skip()


    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.ReleaseMouse()
        evt.Skip()


    def OnMouseMove(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            x, y = self.ClientToScreen(evt.GetPosition())
            fp = (x - self.delta[0], y - self.delta[1])
            self.Move(fp)
        evt.Skip()

class TestTransientPopup(wx.PopupTransientWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""
    def __init__(self, parent, style, log):
        wx.PopupTransientWindow.__init__(self, parent, style)
        panel = wx.Panel(self)
        panel.SetBackgroundColour("#FFB6C1")
        
        st = wx.StaticText(panel, -1, "Tolerance")
        xicbtn = wx.Button(panel, -1, "XIC")
        precbtn = wx.Button(panel, -1, "Find Precursors")
        #spin = wx.SpinCtrl(panel, -1, "Hello", size=(100,-1))
        #self.tolerance = wx.TextCtrl(panel, -1, "0.01")
        self.tolerance = cb = wx.ComboBox(panel, 501, "default value", choices=['A', 'B'], style=wx.CB_DROPDOWN)
        xicbtn.Bind(wx.EVT_BUTTON, self.OnXIC)
        precbtn.Bind(wx.EVT_BUTTON, self.OnPrec)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(xicbtn, 0, wx.ALL, 5)
        sizer.Add(precbtn, 0, wx.ALL, 5)
        sizer.Add(st, 0, wx.ALL, 5)
        sizer.Add(self.tolerance, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        sizer.Fit(panel)
        sizer.Fit(self)
        self.Layout()
        
        
    def OnXIC(self, evt):
        pass
    
    def OnPrec(self, evt):
        pass
        
    def ProcessLeftDown(self, evt):
        
        return wx.PopupTransientWindow.ProcessLeftDown(self, evt)

    def OnDismiss(self):
        pass

    def OnButton(self, evt):
        btn = evt.GetEventObject()
        if btn.GetLabel() == "Press Me":
            btn.SetLabel("Pressed")
        else:
            btn.SetLabel("Press Me")
            
if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = TestFrame(parent=None, pos=(100,100))
    frame.Show()
    app.MainLoop()