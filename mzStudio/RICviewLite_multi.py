__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx
import mz_workbench.mz_core as mz_core
import  wx.lib.editor    as  editor
import os, sys, math
from collections import defaultdict

USE_BUFFERED_DC = True

try:
    from agw import pybusyinfo as PBI
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.pybusyinfo as PBI

TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            #| wx.TB_TEXT
            #| wx.TB_HORZ_LAYOUT
            )


def floatrange(fromnum, tonum, step = 1):
    assert step
    assert step * (tonum - fromnum) >= 0 # To prevent infinite loops.
    
    i = fromnum
    while i < tonum:
        yield i
        i += step
        
        
class BufferedWindow(wx.Window):

    """

    A Buffered window class.

    To use it, subclass it and define a Draw(DC) method that takes a DC
    to draw to. In that method, put the code needed to draw the picture
    you want. The window will automatically be double buffered, and the
    screen will be automatically updated when a Paint event is received.

    When the drawing needs to change, you app needs to call the
    UpdateDrawing() method. Since the drawing is stored in a bitmap, you
    can also save the drawing to file by calling the
    SaveToFile(self, file_name, file_type) method.

    """
    def __init__(self, parent, *args, **kwargs):
        # make sure the NO_FULL_REPAINT_ON_RESIZE style flag is set.
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Window.__init__(self, *args, **kwargs)
        self.parent = parent
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_MOTION(self, self.OnMotion)
        wx.EVT_ERASE_BACKGROUND(self, self.OnErase)
        self.draw_selection = False
        self.draw_co = None
        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        self.OnSize(None)
        self.paint_count = 0
        self.overlay=wx.Overlay()

    def Draw(self, dc):
        ## just here as a place holder.
        ## This method should be over-ridden when subclassed
        pass

    def OnErase(self, event):
        pass

    def OnPaint(self, event):
        # All that is needed here is to draw the buffer to screen
        if USE_BUFFERED_DC:
            dc = wx.BufferedPaintDC(self, self._Buffer)
            dc.SetBackground(wx.Brush("white"))
        else:
            dc = wx.PaintDC(self)
            dc.DrawBitmap(self._Buffer, 0, 0)

    def ClearOverlay(self):
        dc = wx.ClientDC(self)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()
        del odc
        self.overlay.Reset()

    def OnMotion(self, event):
        if event.Dragging() and event.LeftIsDown() and not self.parent_window.tb.GetToolState(10):
            if self.found:
                pdc = wx.BufferedDC(wx.ClientDC(self.parent_window), self._Buffer)
                dc = wx.GCDC(pdc)
                odc = wx.DCOverlay(self.overlay, pdc)
                odc.Clear()
                pos = event.GetPosition()
                found, grid = self.HitTest(pos)
                if grid == self.grid:
                    if self.parent_window.tb.GetToolState(20):
                        dc.DrawLine(self.postup[0], self.postup[1], pos[0], pos[1])
                    else:
                        dc.DrawLine(self.postup[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                        dc.SetPen(wx.Pen(wx.BLUE,2))
                        dc.DrawLine(self.postup[0], self.yaxco[1], self.postup[0], self.yaxco[3])
                        dc.DrawLine(pos[0], self.yaxco[1], pos[0], self.yaxco[3])  
                        brushclr = wx.Colour(255,0,0,8)
                        dc.SetBrush(wx.Brush(brushclr))
                        if self.postup[0] < pos[0]:
                            dc.DrawRectangle(self.postup[0], self.yaxco[1], pos[0] - self.postup[0], self.yaxco[3]- self.yaxco[1])
                        else:
                            dc.DrawRectangle(pos[0], self.yaxco[1], self.postup[0] - pos[0], self.yaxco[3]- self.yaxco[1])                                
                else:
                    dc.DrawLine(self.postup[0], self.postup[1], pos[0], pos[1])
                    dc.DrawRectangle(pos[0],pos[1], 100, 50)
                    dc.DrawText("XIC",pos[0]+50, pos[1]+25)                
                del odc
                self.Refresh()
                self.Update()

        if event.Dragging() and event.LeftIsDown() and self.selected and self.parent_window.tb.GetToolState(10):  #self.parent.Parent.Parent.selection
            pdc = wx.BufferedDC(wx.ClientDC(self.parent_window), self._Buffer)
            dc = wx.GCDC(pdc)
            odc = wx.DCOverlay(self.overlay, pdc)
            odc.Clear()
            pos = event.GetPosition()
            print pos
            if self.selected[0] == 'LINE':
                self.DrawALineOnMotion(self.lines[self.selected[1]], dc, pos, 'LINE')
            if self.selected[0] == 'TEXT':
                self.DrawALineOnMotion(self.text[self.selected[1]], dc, pos, 'TEXT')            
            del odc
            self.Refresh()
            self.Update()            
                                

        event.Skip()    


    def DrawALineOnMotion(self, member, dc, pos, item):
        found, key = self.HitTest(pos)
        if found:
            if item == 'LINE' and self.lines[self.selected[1]][8]==key:
                startTime = self.xic.time_range[0]
                endTime = self.xic.time_range[1]
                
                xaxis = self.xic_axco[key][0]
                yaxis = self.xic_axco[key][1]
                height = yaxis[1]-yaxis[3]
                width = xaxis[2]-xaxis[0]
                max_int = self.GetMaxSignal(startTime, endTime, key)
                tr = endTime-startTime
                print "LINE...."
                
                # These are the original x, y coords of the line
                # pos = (x, y) is the NEW position moved to
                # self.postup is where the button was clicked.
                # So where to draw?
                # Calculate offset, and add to original coords.
                # Convert from time, intensity to x, and y coords.
                if max_int > 0:
                    x1 = yaxis[0] + width*((member[0]-startTime)/float(tr))
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                    x2 = yaxis[0] + width*((member[2]-startTime)/float(tr))
                    y2 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[3]/float(max_int))
                    
                    offsetx = self.postup[0]-pos[0]
                    offsety = self.postup[1]-pos[1]
                    self.drop_coords = (x1 - offsetx, y1-offsety, x2 - offsetx, y2 - offsety)
                    dc.DrawLine(*self.drop_coords)
                
            if item == 'TEXT' and self.text[self.selected[1]][7] == key:
                startTime = self.xic.time_range[0]
                endTime = self.xic.time_range[1]
                xaxis = self.xic_axco[key][0]
                yaxis = self.xic_axco[key][1]
                height = yaxis[1]-yaxis[3]
                width = xaxis[2]-xaxis[0]
                max_int = self.GetMaxSignal(startTime, endTime, key)
                tr = endTime-startTime
                
                x1 = yaxis[0] + width*((member[1]-startTime)/float(tr))
                if max_int > 0:
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[2]/float(max_int))
                
                    dc.DrawRotatedText(member[0], x1,y1,.0001)
                
                    offsetx = self.postup[0]-pos[0]
                    offsety = self.postup[1]-pos[1]
                    
                    self.drop_coords = (member[0], x1 - offsetx, y1-offsety, .0001)
                    
                    dc.DrawRotatedText(*self.drop_coords)    

    def OnSize(self,event):
        # The Buffer init is done here, to make sure the buffer is always
        # the same size as the Window
        #Size  = self.GetClientSizeTuple()
        Size  = self.ClientSize
        print Size
        # Make new offscreen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self._Buffer = wx.EmptyBitmap(*Size)
        self.UpdateDrawing()

    def SaveToFile(self, FileName, FileType=wx.BITMAP_TYPE_PNG):
        ## This will save the contents of the buffer
        ## to the specified file. See the wxWindows docs for 
        ## wx.Bitmap::SaveFile for the details
        self._Buffer.SaveFile(FileName, FileType)

    def UpdateDrawing(self):
        """
        This would get called if the drawing needed to change, for whatever reason.

        The idea here is that the drawing is based on some data generated
        elsewhere in the system. If that data changes, the drawing needs to
        be updated.

        This code re-draws the buffer, then calls Update, which forces a paint event.
        """
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        self.Draw(dc)
        del dc # need to get rid of the MemoryDC before Update() is called.
        self.Refresh()
        self.Update()

class RICviewLitePanel(wx.Frame):
    def __init__(self, parent, xic):
        wx.Frame.__init__(self, parent, -1, title="RICview Lite", size=(800, 800))
        sty = wx.BORDER_SUNKEN
        
        self.sp = wx.SplitterWindow(self, size=(700, 750))
        self.p1 = wx.Panel(self.sp, style=sty)
        self.p2 = wx.Panel(self.sp, style=sty)
        self.p1.SetBackgroundColour("white")
        #wx.StaticText(self.p1, -1, "", (5,5))

        self.p2.SetBackgroundColour("white")
        
        #This sizer is for panel 2, such that the text control can expand to fill the lower splitter window.
        p2Sizer = wx.GridSizer(rows=1, cols=1, hgap=1, vgap=1)        
        
        #wx.StaticText(self.p2, -1, "Panel Two", (5,5))
        self.xic = xic
        self.sp.SetMinimumPaneSize(20)
        self.sp.SplitHorizontally(self.p1, self.p2, -75)
        self.t4 = wx.TextCtrl(self.p2, -1, xic.notes, size=(800, 200), style=wx.TE_MULTILINE|wx.TE_RICH2)
        
        #Add the text control to the Sizer.
        p2Sizer.Add(self.t4, 0, wx.EXPAND)
        self.p2.SetSizer(p2Sizer)
        self.p2.Fit()        
        
        tb = self.CreateToolBar( TBFLAGS )
        dir = os.path.join(os.path.dirname(__file__), 'image')
        
        self.bmp = [wx.Bitmap(dir +'\\' + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP) for iconName in ["select",'line','text','SVG', 'PNG', 'PDF']]
        self.tb = tb
        
        self.SetToolBar(tb)
        self.XICWindow = RICWindow(self.p1, -1, xic, parent_window=self)
        
        #This sizer is for the entire splitter window, so it can fill the available space.
        sizer = wx.GridSizer(rows=1, cols=1, hgap=1, vgap=1)
        sizer.Add(self.sp, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()        
        
        #On Sizing event, call Update Drawing
        self.p1.Bind(wx.EVT_SIZE, self.OnSize)
        
        #Size to window
        self.XICWindow.set_axes()
        self.XICWindow.UpdateDrawing()
        
        self.p1.SetMaxSize((1000, 800))
        self.SetMaxSize((1000,900))
        self.p1.SetMinSize((400, 400))
        self.SetMinSize((400,400))       
        
    def OnSize(self, event):
        # Size event from SpecViewLite Panel
        self.XICWindow.set_axes()
        self.XICWindow.UpdateDrawing()
        
        event.Skip()

    def AddToolBarItems(self, tb):
        tsize = (24,24)
        for pos, label, art, short_help, long_help, evt_id  in self.ToolBarData():
            if pos != "sep":
                try:
                    new_bmp = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, tsize)
                except:
                    try:
                        #art.Rescale(*tsize)
                        #new_bmp = wx.BitmapFromImage(art)
                        new_bmp = art
                    except:
                        new_bmp = wx.ArtProvider.GetBitmap(wx.ART_CLOSE)
                tb.AddCheckTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=evt_id)
            else:
                tb.AddSeparator()

    def SetToolBar(self, tb):
        tsize = (24,24)
        self.AddToolBarItems(tb)
        tb.SetToolBitmapSize(tsize)
        tb.Realize()

    def OnToolClick(self, event):
        if event.GetId() == 10:
            self.OnSelect(None)
        if event.GetId() == 20:
            self.OnLine(None)
        if event.GetId() == 30:
            self.OnText(None)
        if event.GetId() == 40:
            self.OnSVG(None)
        if event.GetId() == 50:
            self.OnSave(None)
        if event.GetId() == 60:
            self.OnSavePNG(None) 
        if event.GetId() == 70:
            self.OnPdf(None) 
            
    
        
        
        

    def ToolBarData(self):
        return ((10, "Select", self.bmp[0], "Select", "Long help for 'Open'", 10),
            (20, "Line", self.bmp[1], "Draw Line", "Long help for 'Close'", 20),
            (30, "Text", self.bmp[2], "Insert Text", "Insert text", 30),
            ("sep", 0, 0, 0, 0, 0),
            (40, "SVG", self.bmp[3], "Save SVG", "Save SVG", 40),
            (60, "PNG", self.bmp[4], "Save PNG", "Save PNG", 60),
            (70, "PDF", self.bmp[5], "Save PDF", "Save PDF", 70),
            ("sep", 0, 0, 0, 0, 0),
            (50, "Save", wx.ART_FILE_SAVE, "Save Annotations", "Long help for 'Save'", 50))    

    def OnSave(self, event):
        self.xic.lines = self.XICWindow.lines
        self.xic.text = self.XICWindow.text
        self.tb.ToggleTool(50, False)

    def OnPdf(self, evt):
        self.tb.ToggleTool(70, False)    
        self.XICWindow.OnSavePdf(None)

    def OnSVG(self,event):
        self.XICWindow.OnSaveSVG(None)    
        self.tb.ToggleTool(40, False)
        
    def OnSavePNG(self, event):
        self.XICWindow.OnSavePNG(None)    
        self.tb.ToggleTool(60, False)
        
    def OnSelect(self,event):
        self.tb.ToggleTool(20, False)
        self.tb.ToggleTool(30, False)
        
    def OnLine(self,event):
        self.tb.ToggleTool(10, False)
        self.tb.ToggleTool(30, False)
        
    def OnText(self,event):
        self.tb.ToggleTool(10, False)
        self.tb.ToggleTool(20, False)
        print self.tb.GetToolState(30)
    

    def OnKeyDown(self,event):
        print"key"

class RICWindow(BufferedWindow):
    def __init__(self, parent, ID, xic, parent_window):
        self.parent_window = parent_window
        #wx.Window.__init__(self,parent,ID, size=(800, 650))
        #self.SetBackgroundColour("White")
        #self.e = None
        self.found = False
        self.parent = parent
        #size = self.ClientSize
        #self._buffer = wx.EmptyBitmap(*size)
        #self.f = lambda a, l:min(l,key=lambda x:abs(x-a)) #function used later
        #self.createMenuBar()
        self.xic = xic
        self.grid = None
        self.LeftDown=None
        self.text = []
        self.selected = None
        self.drop_coords= None
        self.postup = None
        self.lines = [] 
        try:
            if self.xic.lines:
                self.lines = self.xic.lines
        except:
            pass
        try:
            if self.xic.text:
                self.text = self.xic.text
        except:
            pass                
        self.set_axes()
        BufferedWindow.__init__(self, parent, parent, size=(1000,1000))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)   
        
    def Draw(self, dc):
        self.OnDraw(dc)
        
    def HitTestXICBox(self, pos, offset):
        hitx = pos[0]
        hity = pos[1]
        found = False
        grid = None
        trace = None      
        for k, coord in enumerate(self.xic_axco): #COORD = Coordinates for each "Window" or XIC
            traces = len(self.xic.xr[k]) #TRACES DISPLAYED in each window
            if traces > 1:
                for j in range(0, traces):
                    currentx1 = coord[0][0] - offset
                    currentx2 = currentx1 + 10
                    currenty1 = (coord[1][1] + 10) + (20 * j)
                    currenty2 = currenty1 + 10
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                #print "HIT!" + str(i)
                        found = True
                        trace = j
                        grid = k
                        break
        if not found:
            grid = -1
            trace = -1
        return found, trace, grid    

    def HitTest(self, pos):
        hitx = pos[0]
        hity = pos[1]
        found = False
        grid = None
        for k, coord in enumerate(self.xic_axco):
            #traces = len(self.xic.xr[k]) #TRACES DISPLAYED in each window
            #if traces > 1:
                #for j in range(0, traces):
            currentx1 = coord[0][0]
            currentx2 = coord[0][2]
            currenty1 = coord[1][1]
            currenty2 = coord[1][3]                                
            if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                found = True
                #trace = j
                grid = k
                print "HIT"
                #print trace
                print grid                        
                break
        if not found:
            grid = -1
            #trace = -1
        return found, grid #, trace             

    def ConvertPixelToTime(self, pixel):
        stop_time = self.xic.time_range[1]
        start_time = self.xic.time_range[0]
        time = (((pixel - self.xic_axco[0][0][0])/float(self.xic_axco[0][0][2]-self.xic_axco[0][0][0])) * float(stop_time-start_time)) + start_time
        return time
    
    def ConvertTimeToPixel(self, time):
        stop_time = self.xic.time_range[1]
        start_time = self.xic.time_range[0] 
        pixel = self.xic_axco[0][0][0] + (self.xic_axco[0][0][2] - self.xic_axco[0][0][0]) * (float((time - start_time))/float((stop_time-start_time)))
        #pixel = ((float(time - start_time))/(float(stop_time-start_time)))+((self.xic_axco[0][0][0])/(float(self.xic_axco[0][0][2]-self.xic_axco[0][0][0])))
        return pixel
    
    def ConvertIntensityToPixel(self, intensity, key):
        yaxis = self.xic_axco[key][1]
        height = yaxis[3]-yaxis[1]
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        max_signal = self.GetMaxSignal(startTime, stopTime, key)        
        try:
            py = float(height)/float(max_signal)
        except:
            py = 0
        pixel = yaxis[1] + (height - intensity * py) 
        return pixel
    
    def ConvertPixelToIntensity(self, pixel, key):
        yaxis = self.xic_axco[key][1]
        height = yaxis[3]-yaxis[1]
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        max_signal = self.GetMaxSignal(startTime, stopTime, key)         
        try:
            py = float(height)/float(max_signal)
        except:
            py = 0        
        intensity = -float((pixel - yaxis[1] - height)/float(py))
        return intensity

    def OnLeftDown(self,event):
        self.SetFocus()
        self.xic.notes = self.parent_window.t4.GetValue()
        pos = event.GetPosition()
        self.postup = pos
        found, grid = self.HitTest(pos)
        self.found = found
        self.grid = grid
        self.LeftDown = (found, grid)
        self.yaxco = self.xic_axco[grid][1]
        print pos
        if found:
            time = self.ConvertPixelToTime(pos[0])
            self.new_startTime = time
            print time

    def OnRightDown(self,event):
        pos = event.GetPosition()
        found, grid = self.HitTest(pos)
        self.found = found
        self.grid = grid
        self.xic.time_range = (self.xic.full_time_range[0],self.xic.full_time_range[1])
        self.Refresh()

    def OnLeftUp(self,event):
        pos = event.GetPosition()
        tfound, ttrace, tgrid = self.HitTestXICBox(pos, 40)
        if tfound:
            #JUST HIT EXTRACT A TRACE.
            #WHICH WINDOW?  WHICH TRACE?  NOT ACTIVE.
            #SEPARATE OUT
            #[[[0,1,2],[0,1,2]],[0,1,2]] to [[[0,1,2]]
            
            #TRANSFER CURRENT TRACE TO TEMP & delete info from lists
            t_xic_axco = self.xic_axco[tgrid]  #- there is one for each window only, this should get copied
            t_active_xic = 0 # will go to new trace, will automatically be assigned as active
            t_filters = self.xic.xic_filters[tgrid].pop(ttrace)
            t_x_mr = self.xic.xic_mass_ranges[tgrid].pop(ttrace)
            t_xic_view = 1 # will go to new trace, will automatically be assigned to view
            t_xic_scale = self.xic.xic_scale[tgrid].pop(ttrace)
            if str(t_xic_scale).lower().startswith("s"):
                t_xic_scale = -1 #If this trace was scaled to another, set to Auto
            t_xr = self.xic.xr[tgrid].pop(ttrace)
            t_xic = self.xic.data[tgrid].pop(ttrace)
            
            #INSERT TEMP PAST ACTIVE WINDOW
            self.xic.xic_filters.insert(tgrid + 1, [t_filters])
            self.xic_axco.insert(tgrid + 1, t_xic_axco)
            self.xic.active_xic.insert(tgrid + 1, t_active_xic)
            self.xic.xic_view.insert(tgrid + 1, [t_xic_view])
            self.xic.xic_scale.insert(tgrid +1, [t_xic_scale])
            self.xic.xr.insert(tgrid +1, [t_xr])
            self.xic.data.insert(tgrid + 1, [t_xic])
            self.xic.xic_mass_ranges.insert(tgrid +1, [t_x_mr])
            self.set_axes()
            #self.Window.UpdateDrawing()
            self.Refresh()      
        
        #-------------------------------------CHECK TO SEE IF ACTIVE TRACE BUTTON HIT
        #tfound, ttrace, tgrid, tfile = self.msdb.HitTestActiveTrace(pos)
        tfound, ttrace, tgrid = self.HitTestXICBox(pos, 10)
        if tfound:
            self.xic.active_xic[tgrid] = ttrace
            print "TRACE GRID HIT!"
            if not self.xic.xic_view[tgrid][ttrace]:
                self.xic.xic_view[tgrid][ttrace] = True
            #self.Window.UpdateDrawing()
            self.Refresh()            
        #-------------------------------------CHECK TO SEE IF TRACE ON_OFF HIT
        #tfound, ttrace, tgrid, tfile = self.msdb.HitTestTraceOnOff(pos)
        tfound, ttrace, tgrid = self.HitTestXICBox(pos, 25)
        if tfound:
            if self.xic.active_xic[tgrid] != ttrace:
                self.xic.xic_view[tgrid][ttrace] = not self.xic.xic_view[tgrid][ttrace]
            print "CONTROL GRID HIT!"
            #self.Window.UpdateDrawing()
            self.Refresh()                 
        
        found, grid = self.HitTest(pos)
        if self.LeftDown:
            key = self.LeftDown[1]
        if found:
            #------------------------------------------------------
            # DRAWING TEXT
            #------------------------------------------------------
            if self.parent_window.tb.GetToolState(30):
                if self.LeftDown[1]==grid:
                    dlg = wx.TextEntryDialog(None, "Text", "Annotate XIC", style=wx.OK|wx.CANCEL)
                    if dlg.ShowModal()==wx.ID_OK:
                        time = self.ConvertPixelToTime(pos[0])
                        yaxis = self.xic_axco[grid][1]
                        startTime = self.xic.time_range[0]
                        stopTime = self.xic.time_range[1]
                        max_int = self.GetMaxSignal(startTime, stopTime, key)
                        inten = (float(yaxis[3]-pos[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                        print inten
                        print "INTEN"
                        print max_int
                        self.text.append([dlg.GetValue(), time, inten,0,0,0,0, grid])
                event.Skip()
            #------------------------------------------------------
            # DRAWING LINE
            #------------------------------------------------------
            if self.parent_window.tb.GetToolState(20):
                print "LINES"
                if self.LeftDown[1]==grid:
                    print grid
                    print "ENTER"
                    timeL = self.ConvertPixelToTime(pos[0])
                    timeF = self.ConvertPixelToTime(self.postup[0])
                    yaxis = self.xic_axco[grid][1]
                    startTime = self.xic.time_range[0]
                    stopTime = self.xic.time_range[1]
                    max_int = self.GetMaxSignal(startTime, stopTime, key)
                    intenf = (float(yaxis[3]-self.postup[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                    intenl = (float(yaxis[3]-pos[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                    self.lines.append([timeF, intenf, timeL, intenl,0,0,0,0,grid])
                event.Skip()
            #--------------------------------------------------------
            # SELECT AN OBJECT
            #--------------------------------------------------------
            if self.parent_window.tb.GetToolState(10) and not self.drop_coords:
                print "SELECT"
                found = False
                for i, member in enumerate(self.text):
                    if pos[0] > member[3] and pos[1] > member[4] and pos[0] < member[5] and pos[1] < member[6]:
                        self.selected = ("TEXT", i)
                        found = True
                    if found:
                        break
                for i, member in enumerate(self.lines):
                    if pos[0] > member[4] and pos[1] > member[5] and pos[0] < member[6] and pos[1] < member[7]:
                        self.selected = ("LINE", i)
                        found = True
                    if found:
                        break                
                if not found:
                    self.selected = None
                    
                event.Skip()
            
            # JUST FINISHED A DRAG OF AN OBJECT.  NEED TO RE-LOCATE    
            if self.parent_window.tb.GetToolState(10) and self.drop_coords:
                                
                obj = self.selected
                drop_coords = self.drop_coords
                
                if self.selected:
                    if self.selected[0] == 'LINE':
                
                        # Need to convert drop coords to mz, inten.
                        stopTime = self.ConvertPixelToTime(drop_coords[2])
                        startTime = self.ConvertPixelToTime(drop_coords[0])
                        intStart = self.ConvertPixelToIntensity(drop_coords[1], key)
                        intStop = self.ConvertPixelToIntensity(drop_coords[3], key)
                        #mzl = self.ConvertPixelToMass(drop_coords[2], grid)
                        #mzf = self.ConvertPixelToMass(drop_coords[0], grid)
                        yaxis = self.xic_axco[grid][1]
                        xicStart = self.xic.time_range[0]
                        xicStop = self.xic.time_range[1]
                        max_int = self.GetMaxSignal(startTime, stopTime, key)
                        timef = (float(yaxis[3]-drop_coords[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                        timel = (float(yaxis[3]-drop_coords[3])/float((yaxis[3]-yaxis[1])))*float(max_int)                
                        print "Drop object"
                        self.lines[obj[1]][0]=startTime
                        self.lines[obj[1]][1]=intStart
                        self.lines[obj[1]][2]=stopTime
                        self.lines[obj[1]][3]=intStop
                        
                        self.selected = None
                        self.drop_coords = None
                        self.drop_object = None                
                        
                        event.Skip()
                if self.selected:        
                    if self.selected[0] == 'TEXT':
                    
                        time = self.ConvertPixelToTime(self.drop_coords[1])
                        inten = self.ConvertPixelToIntensity(self.drop_coords[2], key)
                        
                        self.text[obj[1]][1] = time
                        self.text[obj[1]][2] = inten
                        
                        self.selected = None
                        self.drop_coords = None
                        self.drop_object = None                
                        
                        event.Skip()            
                
        if found and pos != self.postup and not self.parent_window.tb.GetToolState(30) and not self.parent_window.tb.GetToolState(20) and not self.parent_window.tb.GetToolState(10):
            if grid == self.grid:
                time = self.ConvertPixelToTime(pos[0])
                print "Time: " + str(time)
                try:
                    self.new_stopTime = time
                    self.xic.time_range=(self.new_startTime,self.new_stopTime)
                except:
                    pass
            elif self.grid: #CHANGED 2014-08-02
                print "DRAG AND DROP XIC"
                #self.grid = source
                #grid = target
                #TRANSFER CURRENT TRACE TO TEMP & delete info from lists
                tgrid = self.grid
                t_xic_axco = self.xic_axco.pop(tgrid)  #- entire trace removed
                t_active_xic = self.xic.active_xic.pop(tgrid) # need to remove from list
                t_filters = self.xic.xic_filters.pop(tgrid) # need to remove filters for all traces
                t_x_mr = self.xic.xic_mass_ranges.pop(tgrid)
                t_xic_view = self.xic.xic_view.pop(tgrid)
                t_xic_scale = self.xic.xic_scale.pop(tgrid)
                for i, member in enumerate(t_xic_scale):
                    if str(member).lower().startswith("s"):
                        t_xic_scale[i] = -1 #If this trace was scaled to another, set to Auto
                t_xr = self.xic.xr.pop(tgrid)
                t_xic = self.xic.data.pop(tgrid)
                
                #INSERT INTO EXISTING TRACES
                self.xic.xic_filters[grid].extend(t for t in t_filters)
                #Same axco applies, no need to copy self.xic_axco.insert(tgrid + 1, t_xic_axco)
                #Keep the original trace active - no need to copy self.xic.active_xic[grid].append(t_active_xic)
                self.xic.xic_view[grid].extend(t for t in t_xic_view)
                self.xic.xic_scale[grid].extend(t for t in t_xic_scale)
                self.xic.xr[grid].extend(t for t in t_xr)
                self.xic.data[grid].extend(t for t in t_xic)
                self.xic.xic_mass_ranges[grid].extend(t_x_mr)
                self.set_axes()
                #self.Window.UpdateDrawing()
                self.Refresh()                      
        self.ClearOverlay()
        self.UpdateDrawing()

    def OnRightUp(self,event):
        self.UpdateDrawing()

    def OnKeyDown(self,event):
        key = event.GetKeyCode()
        if key == 127:
            print "DEL"
            if self.selected:
                #or member in self.selected:
                if self.selected[0]=="TEXT":
                    del self.text[self.selected[1]]
                if self.selected[0]=="LINE":
                    del self.lines[self.selected[1]]
                self.selected=None
        if key == 91 or key == 47:
            if self.selected:
                if self.selected[0]=="TEXT":
                    current = self.text[self.selected[1]] # 1=mz, 2= inten, coords = 3, 4, 5, 6, key =7
                    currenti = current[2]
                    current_key = current[7]
                    current_pixel = self.ConvertIntensityToPixel(currenti, current_key)
                    if key == 91:
                        current_pixel -= 5
                    else:
                        current_pixel += 5
                    new_inten = self.ConvertPixelToIntensity(current_pixel, current_key)
                    self.text[self.selected[1]][2]=new_inten
                if self.selected[0]=="LINE":
                    current = self.lines[self.selected[1]] # 0=x1, 1=y1, 2=x2, 3=y2, coords = 4,5,6,7 key=8
                    currenti1 = current[1]
                    currenti2 = current[3]
                    current_key = current[8]
                    current_pixel1 = self.ConvertIntensityToPixel(currenti1, current_key)
                    current_pixel2 = self.ConvertIntensityToPixel(currenti2, current_key)
                    if key == 91:
                        current_pixel1 -= 5
                        current_pixel2 -= 5
                    else:
                        current_pixel1 += 5
                        current_pixel2 += 5
                    new_inten1 = self.ConvertPixelToIntensity(current_pixel1, current_key)
                    new_inten2 = self.ConvertPixelToIntensity(current_pixel2, current_key)
                    self.lines[self.selected[1]][1]=new_inten1 
                    self.lines[self.selected[1]][3]=new_inten2 
        if key == 59 or key == 39:
            print "LR"
            if self.selected:
                if self.selected[0]=="TEXT":
                    print "LR2"
                    tst = self.ConvertTimeToPixel(34.0)
                    print tst
                    tst2 = self.ConvertPixelToTime(tst)
                    print tst2
                    current = self.text[self.selected[1]] # 1=mz, 2= inten, coords = 3, 4, 5, 6, key =7
                    currentm = current[1]
                    print currentm
                    current_key = current[7]
                    current_pixel = self.ConvertTimeToPixel(currentm)
                    print current_pixel
                    if key == 59:
                        current_pixel -= 5
                    else:
                        current_pixel += 5
                    new_mz = self.ConvertPixelToTime(current_pixel)
                    print new_mz
                    print "----"
                    self.text[self.selected[1]][1]=new_mz    
                if self.selected[0]=="LINE":
                    current = self.lines[self.selected[1]] # 0=x1, 1=y1, 2=x2, 3=y2, coords = 4,5,6,7 key=8
                    currentm1 = current[0]
                    currentm2 = current[2]
                    current_key = current[8]
                    current_pixel1 = self.ConvertTimeToPixel(currentm1)
                    current_pixel2 = self.ConvertTimeToPixel(currentm2)
                    if key == 59:
                        current_pixel1 -= 5
                        current_pixel2 -= 5
                    else:
                        current_pixel1 += 5
                        current_pixel2 += 5
                    new_mz1 = self.ConvertPixelToTime(current_pixel1)
                    new_mz2 = self.ConvertPixelToTime(current_pixel2)
                    self.lines[self.selected[1]][0]=new_mz1 
                    self.lines[self.selected[1]][2]=new_mz2         
        #self.Refresh()
        self.UpdateDrawing()

    def MarkSelected(self, dc, key):
        if self.selected:
            cur = self.selected
            if cur[0]=="TEXT":
                if self.text[cur[1]][7]==key:
                    dc.DrawCircle(self.text[cur[1]][3], self.text[cur[1]][4], 3)
                    dc.DrawCircle(self.text[cur[1]][3], self.text[cur[1]][6], 3)
                    dc.DrawCircle(self.text[cur[1]][5], self.text[cur[1]][4], 3)
                    dc.DrawCircle(self.text[cur[1]][5], self.text[cur[1]][6], 3)
            if cur[0]=="LINE":
                if self.lines[cur[1]][8]==key:
                    dc.DrawCircle(self.lines[cur[1]][4], self.lines[cur[1]][5], 3)
                    dc.DrawCircle(self.lines[cur[1]][4], self.lines[cur[1]][7], 3)
                    dc.DrawCircle(self.lines[cur[1]][6], self.lines[cur[1]][5], 3)
                    dc.DrawCircle(self.lines[cur[1]][6], self.lines[cur[1]][7], 3)     

    def AnnotateText(self, dc, key):
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        xaxis = self.xic_axco[key][0]
        yaxis = self.xic_axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        max_int = self.GetMaxSignal(startTime, stopTime, key)
        tr = stopTime-startTime
        for member in self.text:
            if member[1]>startTime and member[1]<stopTime and key == member[7] and max_int > 0:
                x1 = yaxis[0] + width*((member[1]-startTime)/float(tr))
                y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[2]/float(max_int))
                dc.DrawRotatedText(member[0], x1,y1,.0001)
                self.svg["text"].append((member[0], x1,y1,.0001))
                ext = dc.GetTextExtent(member[0])
                member[3]=x1
                member[4]=y1
                member[5]=x1+ext[0]
                member[6]=y1+ext[1]    

    def AnnotateLines(self, dc, key):
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        if startTime > stopTime:
            tmp = startTime
            startTime = stopTime
            stopTime = tmp
        xaxis = self.xic_axco[key][0]
        yaxis = self.xic_axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        max_int = self.GetMaxSignal(startTime, stopTime, key)
        tr = stopTime-startTime
        print "LINES...."
        for member in self.lines:
            print member
            print "ON KEY"
            print key
            if member[0]>startTime and member[0]<stopTime and key == member[8]:
                x1 = yaxis[0] + width*((member[0]-startTime)/float(tr))
                y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                x2 = yaxis[0] + width*((member[2]-startTime)/float(tr))
                y2 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[3]/float(max_int))
                dc.DrawLine(x1,y1,x2,y2)
                self.svg["lines"].append((x1,y1,x2,y2))
                #This code checks to see if the line is hoz or vertical - if so, expand the selection block
                #So that it is easier to select                
                if abs(x2-x1) < 10:
                    if x2 > x1:
                        x2 += 10
                        x1 -= 10
                    else:
                        x1 += 10
                        x2 -= 10
                if abs(y2-y1) < 10:
                    if y2 > y1:
                        y2 += 10
                        y1 -= 10
                    else:
                        y1 += 10
                        y2 -= 10                    
                member[4]=min(x1,x2)
                member[5]=min(y1,y2)
                member[6]=max(x1,x2)
                member[7]=max(y1,y2)      

    def OnDraw(self, dc):
        try:
            del self.svg
        except:
            pass        
        size = self.GetClientSize()
        dc.SetBackground( wx.Brush("White") )
        #dc.SetBackgroundColour("White")
        dc.Clear()   
        #buffer = wx.EmptyBitmap(size.width, size.height)
        self.svg = defaultdict(list)
        #dc = wx.BufferedDC(None, buffer)
        #dc = wx.BufferedDC(None, buffer)
        #dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK,1))
        for k in range(0, len(self.xic_axco)):
            print "DRAWING... ric axis " + str(k)
            self.DrawXic(dc, k)
            self.AnnotateLines(dc,k)
            self.AnnotateText(dc,k)
            self.MarkSelected(dc,k)
        self.storeImage(dc)
        #bpd = wx.BufferedPaintDC(self, buffer)

    def storeImage(self, dc):
        size = dc.Size
        bmp = wx.EmptyBitmap(size.width, size.height)
        memDC = wx.MemoryDC()
        memDC.SelectObject(bmp)
        memDC.Blit(0,0,size.width,size.height,dc,0,0)
        memDC.SelectObject(wx.NullBitmap)
        img = bmp.ConvertToImage()
        self.img = img    

    def get_single_file(self, caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
        dlg = wx.FileDialog(None, caption, pos = (2,2), wildcard = wx_wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath()
            dir = dlg.GetDirectory()
            print filename
            print dir
            dlg.Destroy()
            return filename, dir
        dlg.Destroy()
        return None, None
            
    def OnSavePNG(self, event):
        pngfile, dir = self.get_single_file("Select image file...", "PNG files (*.png)|*.png")
        if pngfile:
            self.img.SaveFile(pngfile,wx.BITMAP_TYPE_PNG)          

    def OnSavePdf(self, evt):
        
        pdffile, dir = self.get_single_file("Select image file...", "PDF files (*.pdf)|*.pdf")
        if not pdffile:
            return        
        
        tempsvg = pdffile + 'TEMP.svg'        
        
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF
        except ImportError:
            wx.MessageBox("PDF creation requires ReportLab and svglib to be installed.")
            return
        
        busy = PBI.PyBusyInfo("Saving PDF, please wait...", parent=None, title="Processing...")
        wx.Yield()
        self.svgDC = wx.SVGFileDC(tempsvg)
        
        print "SAVING...(lines)"
        for line in self.svg["lines"]:
            if len(line)==4:
                self.svgDC.DrawLine(*line)
            else:
                self.svgDC.SetPen(line[4])
                self.svgDC.DrawLine(line[0], line[1], line[2], line[3])
        print "SAVING...(text)"
        for text in self.svg["text"]:
            if len(text)==4:
                self.svgDC.DrawRotatedText(*text)
            else:
                self.svgDC.SetTextForeground(text[4])
                self.svgDC.SetFont(text[5])
                self.svgDC.DrawRotatedText(text[0],text[1],text[2],text[3])
        print "Saving drawlines..."
        for pointList in self.svg["pointLists"]:
            self.svgDC.DrawLines(pointList)  #.DrawLine(*line)
        print "DONE."
        self.svgDC.Destroy()
        
        svgdata = svg2rlg(tempsvg)
        renderPDF.drawToFile(svgdata, pdffile)
        os.remove(tempsvg)    

    def OnSaveSVG(self, event):
        svgfile, dir = self.get_single_file("Select image file...", "SVG files (*.svg)|*.svg")
        
        if svgfile:
            busy = PBI.PyBusyInfo("Saving SVG, please wait...", parent=None, title="Processing...")
            wx.Yield()
            self.svgDC = wx.SVGFileDC(svgfile)
            #currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
            print "SAVING...(lines)"
            for line in self.svg["lines"]:
                if len(line)==4:
                    self.svgDC.DrawLine(*line)
                else:
                    self.svgDC.SetPen(line[4])
                    self.svgDC.DrawLine(line[0], line[1], line[2], line[3])
            print "SAVING...(text)"
            for text in self.svg["text"]:
                if len(text)==4:
                    self.svgDC.DrawRotatedText(*text)
                else:
                    self.svgDC.SetTextForeground(text[4])
                    self.svgDC.SetFont(text[5])
                    self.svgDC.DrawRotatedText(text[0],text[1],text[2],text[3])
            print "Saving drawlines..."
            for pointList in self.svg["pointLists"]:
                self.svgDC.DrawLines(pointList)  #.DrawLine(*line)
            print "DONE."
            self.svgDC.Destroy()
            del busy    

    def GetMaxSignal(self, startTime, stopTime, key, xic=0):
        sub_xic = []
        for member in self.xic.data[key][xic]:
            if member[0]>=startTime and member[0]<=stopTime:
                sub_xic.append(member)
        try:
            return max(t[1] for t in sub_xic)
        except:
            return 0

    def myRound(self, x, base=5):
        return int(base*round(float(x)/base))

    def set_axes(self):
        
        sz = self.parent_window.p1.GetClientSize()
        
        space = 40
        y_marg = 25
        indent = 50
        width = 600
        xic_total_height = 0
        number_xics = len(self.xic.data)
        self.xic_axco = []
        g = {0:10, 1:10, 2:10, 3:10, 4:8, 5:7, 6:6, 7:5, 8:4.5, 9:4.5, 10:4.5}
        height =  (float(sz[1]-100)/float(number_xics))-(g[number_xics]*number_xics)
        #height =  (float(sz[1]-100)/float(num_rawFiles)/float(number_xics))-(g[number_xics]*number_xics)
        for k in range(0, number_xics):
            yco = y_marg+(space*k)+(height*k)+(xic_total_height)
            self.xic_axco.append(((indent,yco+height,indent + (float(sz[0])/float(1.05))-50,yco+height),(indent,yco,indent,yco+height)))
            
            #s.append(((_set['y_marg'],yco+height,(float(sz[0])/float(2))-50,yco+height),(_set['y_marg'],yco,_set['y_marg'],yco+height)))
            #self.xic_axco.append(((50,yco+height,500,yco+height),(50,yco,50,yco+height)))
        print self.xic_axco

    def get_xic_color(self, xic, dc):
        if xic == 0:
            dc.SetPen(wx.Pen(wx.BLACK,1))
            col = wx.BLACK
        elif xic == 1:
            dc.SetPen(wx.Pen(wx.RED,1))
            col = wx.RED
        elif xic == 2:
            dc.SetPen(wx.Pen(wx.BLUE,1)) 
            col = wx.BLUE
        elif xic == 3:
            dc.SetPen(wx.Pen(wx.GREEN,1)) 
            col = wx.GREEN    
        elif xic == 4:
            dc.SetPen(wx.Pen(wx.GREEN,1)) 
            col = wx.YELLOW        
        return col    

    def DrawXic(self, dc, key):
        scaling = False
        active_xic = self.xic.active_xic[key]
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        
        maxTable = []
        for xic in range(0, len(self.xic.xr[key])):
            maxTable.append(self.GetMaxSignal(startTime, stopTime, key, xic))
        xics = len(self.xic.xr[key])
        for xic in range(0, len(self.xic.xr[key])):
            xaxis = self.xic_axco[key][0]
            yaxis = self.xic_axco[key][1]
            col = self.get_xic_color(xic, dc)        
            if xics > 1:
                dc.SetBrush(wx.Brush(col, wx.TRANSPARENT))
                dc.DrawRectangle(xaxis[0]-25, (yaxis[1]+10)+ (20*xic),10,10) 
                dc.DrawRectangle(xaxis[0]-40, (yaxis[1]+10)+ (20*xic),10,10)
                dc.DrawText('>', xaxis[0]-40+2, (yaxis[1]+10)+ (20*xic)-3)
                dc.DrawText('+' if self.xic.xic_view[key][xic] else '-', xaxis[0]-25+2, (yaxis[1]+10)+ (20*xic)-3)
                dc.SetBrush(wx.Brush(col, wx.SOLID))
                dc.DrawRectangle(xaxis[0]-10, (yaxis[1]+10)+ (20*xic),10,10) 
            if self.xic.xic_view[key][xic]:
                currentActive=False
                if active_xic == xic:
                    currentActive = True
                scale = self.xic.xic_scale[key][xic]
                dc.SetPen(wx.Pen(wx.BLACK,1))            
                dc.DrawLine(*xaxis)
                self.svg["lines"].append(xaxis)
                dc.DrawLine(*yaxis)
                self.svg["lines"].append(yaxis)
                print xaxis[0]-5
                print yaxis[1]
                print xaxis[0]
                print yaxis[1]
                dc.DrawLine(xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1])
                self.svg["lines"].append((xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1]))
                height = yaxis[3]-yaxis[1]
                width = xaxis[2]-xaxis[0]
                max_signal = maxTable[xic]
                #max_signal = self.GetMaxSignal(startTime, stopTime, key)
                if scale == -1:
                    #max_signal = self.msdb.GetMaxSignal(startTime, stopTime, key, self.msdb.Display_ID[rawID], xic)
                    max_signal = maxTable[xic]
                elif str(scale).lower().startswith("s"):
                    #Scale to a trace
                    max_signal = maxTable[int(str(scale)[1:])]
                    scaling = True
                else:
                    print "SCALING"
                    max_signal = scale
                    scaling = True                
                tr = stopTime-startTime
                print "tr:" + str(tr)
                try:
                    px = float(width)/float(tr)
                except:
                    px = 0
                try:
                    py = float(height)/float(max_signal)
                except:
                    py = 0
                self.xic_width = width
                x1 = yaxis[0]
                y1 = yaxis[3]
                dc.SetTextForeground("BLACK")
                dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                if currentActive:
                    dc.DrawText("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7)
                    self.svg["text"].append(("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7,0.00001))
        
                points = []
                print "building"
                for member in self.xic.data[key][xic]:
                    if member[0]>startTime and member[0]<stopTime:
                        x2 = yaxis[0] + px*(member[0]-startTime)
                        if not scaling:
                            y2 = yaxis[1] + (height - member[1]*py)
                        else:
                            y2 = (yaxis[1] + (height - member[1]*py)) if member[1] < max_signal else (yaxis[1] + (height - max_signal*py))       
                        points.append(wx.Point(x2, y2))
                print "drawing"
                col = self.get_xic_color(xic, dc)
                dc.DrawLines(points)
                self.svg["pointLists"].append(points)
        
                xticks = []
                startTime = float(startTime)
                stopTime = float(stopTime) # Not doing these casts can have hilarious effects.                
                if tr >= 0.1:
                    if tr > 10:
                        scale = int(round(round(tr, -1 * int(math.floor(math.log10(tr)))) / 10))
                        assert scale
                    else:
                        scale = tr/10.0
                    
                    if self.GetClientSize()[0] < 600:
                        scale = scale * 3
                    elif self.GetClientSize()[0] < 800:
                        scale = scale * 2                    
                    if scale >= 1:
                        firstlabel = self.myRound(startTime, scale)
                        lastlabel = self.myRound(stopTime, scale)
                    if scale >= 0.1:
                        firstlabel = float(self.myRound(startTime*10, scale*10))/float(10)
                        lastlabel = float(self.myRound(stopTime*10, scale*10))/float(10)
                    else:
                        firstlabel = float(self.myRound(startTime*100, scale*100))/float(100)
                        lastlabel = float(self.myRound(stopTime*100, scale*100))/float(100)
                    
                    if firstlabel < startTime:
                        firstlabel += scale
                    if lastlabel > stopTime:
                        lastlabel -= scale
                    if scale >= 1:
                        # Replace with float-compatible range equivalent?
                        #for i in range (int(firstlabel), int(lastlabel + scale), int(scale)):
                        for i in floatrange(firstlabel, lastlabel + scale, scale):
                            if i%1 == 0:
                                i = int(i)
                            xticks.append(i)
                    if scale >= .1 and scale < 1:
                        #for i in range (int(firstlabel)*10, int(lastlabel)*10 + int(scale)*10, int(scale)*10):
                        for i in floatrange(firstlabel*10, lastlabel*10 + scale*10, scale*10):
                            xticks.append(float(i)/float(10))
                    if scale < 0.1:
                        for i in floatrange(firstlabel*100, lastlabel*100 + scale*100, scale*100):
                            xticks.append(float(i)/float(100))   
                else:
                    xticks.append(startTime)
                    xticks.append(stopTime)                    
                    
                    
                    
                for member in xticks:
                    if tr > 0.01: 
                        memberstr = "%.2f" % member if isinstance(member, float) else str(member)
                    else:
                        memberstr = "%.4f" % member if isinstance(member, float) else str(member)
                    x1 = self.xic_axco[key][0][0] + px*((member-startTime))
                    dc.DrawText(memberstr, x1-8,yaxis[3]+5)
                    self.svg["text"].append((memberstr, x1-8,yaxis[3]+5,0.00001))
                    dc.DrawLine(x1, yaxis[3], x1, yaxis[3]+2)
                    self.svg["lines"].append((x1, yaxis[3], x1, yaxis[3]+2))
                    
                if len(xticks) == 2:
                    if xticks[0] == xticks[1]:
                        dc.DrawText("Can't display!\nZoom Out!", x1,yaxis[3]-50)                
                    
                if currentActive:
                    col = self.get_xic_color(xic, dc)
                    dc.SetTextForeground(col)                
                    dc.DrawText("mz " + str(self.xic.xic_mass_ranges[key][xic][0]) + '-'+ str(self.xic.xic_mass_ranges[key][xic][1]) + ' (' + self.xic.xic_filters[key][xic].strip() + ')', self.xic_axco[key][1][0], self.xic_axco[key][1][1] - 20)
                    self.svg["text"].append(("mz " + str(self.xic.xic_mass_ranges[key][xic][0]) + '-'+ str(self.xic.xic_mass_ranges[key][xic][1]), self.xic_axco[key][1][0], self.xic_axco[key][1][1] - 20,0.00001))
        #            if currentFile['vendor']=='Thermo':
        #                rt = currentFile['rt_dict'][currentFile['scanNum']]
        #            elif currentFile['vendor']=='ABI':
        #                rt = currentFile['rt_dict'][(currentFile['scanNum'], currentFile['experiment'])]
        #            current_x = currentFile['xic_axco'][key][0][0] + ((rt-startTime)*px)
        #            dc.SetPen(wx.Pen(wx.RED,2))
        #            dc.DrawLine(current_x, yaxis[1], current_x, yaxis[3])
                #self.msdb.svg["lines"].append((current_x, yaxis[1], current_x, yaxis[3]))
                dc.SetPen(wx.Pen(wx.BLACK,1))
                dc.SetTextForeground("BLACK")
    
if __name__ == '__main__':
    ID_Dict = {}
    app = wx.App(False)
    if len(sys.argv) > 1:
        frame = RICviewLitePanel(sys.argv[1], 1)
    else:
        import XICObject
        data = [[[(10.0, 100), (11, 200), (12, 100), (14,300), (20, 500)]]]
        a = XICObject.XICObject("Arawfile", data, [[(100,2000)]], (10,20), [[(100,2000)]], 'Full ms ', [[(-1)]], [[(200)]], [[(0)]], [[(1)]])
        a.notes = ''
        #a.axes = 1
        #a.full_range = (300,2000)
        
        frame = RICviewLitePanel(None, a)
    frame.Show()
    app.MainLoop()