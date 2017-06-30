__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx
import mz_workbench.mz_core as mz_core
import  wx.lib.editor    as  editor
import os
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
        print "Paint"
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
        if event.Dragging() and event.LeftIsDown():
            if self.found:
                pdc = wx.BufferedDC(wx.ClientDC(self.parent_window), self._Buffer)
                dc = wx.GCDC(pdc)
                odc = wx.DCOverlay(self.overlay, pdc)
                odc.Clear()
                pos = event.GetPositionTuple()
                found, grid = self.HitTest(pos)
                if grid == self.grid:
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
                del odc
                self.Refresh()
                self.Update()
        event.Skip()    

    def OnSize(self,event):
        # The Buffer init is done here, to make sure the buffer is always
        # the same size as the Window
        #Size  = self.GetClientSizeTuple()
        Size  = self.ClientSize

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
        self.sp = wx.SplitterWindow(self)
        self.p1 = wx.Panel(self.sp, style=sty)
        self.p2 = wx.Panel(self.sp, style=sty)
        self.p1.SetBackgroundColour("white")
        #wx.StaticText(self.p1, -1, "", (5,5))

        self.p2.SetBackgroundColour("sky blue")
        #wx.StaticText(self.p2, -1, "Panel Two", (5,5))
        self.xic = xic
        self.sp.SetMinimumPaneSize(20)
        self.sp.SplitHorizontally(self.p1, self.p2, -125)
        self.t4 = wx.TextCtrl(self.p2, -1, xic.notes,
                        size=(800, 200), style=wx.TE_MULTILINE|wx.TE_RICH2)
        tb = self.CreateToolBar( TBFLAGS )
        dir = os.path.join(os.path.dirname(__file__), 'image')
        
        self.bmp = [wx.Bitmap(dir +'\\' + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP) for iconName in ["select",'line','text','SVG', 'PNG']]
        self.tb = tb
        
        self.SetToolBar(tb)
        self.XICWindow = RICWindow(self.p1, -1, xic, parent_window=self)

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
                tb.AddCheckLabelTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
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

    def ToolBarData(self):
        return ((10, "Select", self.bmp[0], "Select", "Long help for 'Open'", 10),
            (20, "Line", self.bmp[1], "Draw Line", "Long help for 'Close'", 20),
            (30, "Text", self.bmp[2], "Insert Text", "Long help for 'Save'", 30),
            ("sep", 0, 0, 0, 0, 0),
            (40, "SVG", self.bmp[3], "Save SVG", "Long help for 'Save'", 40),
            (60, "PNG", self.bmp[4], "Save PNG", "Long help for 'Save'", 60),
            ("sep", 0, 0, 0, 0, 0),
            (50, "Save", wx.ART_FILE_SAVE, "Save Annotations", "Long help for 'Save'", 50))    

    def OnSave(self, event):
        self.xic.lines = self.XICWindow.lines
        self.xic.text = self.XICWindow.text

    def OnSVG(self,event):
        self.XICWindow.OnSaveSVG(None)    
    def OnSavePNG(self, event):
        self.XICWindow.OnSavePNG(None)    
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
        self.LeftDown=None
        self.text = []
        self.selected = None
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
        BufferedWindow.__init__(self, parent, parent, size=(600,700))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)   
        
    def Draw(self, dc):
        self.OnDraw(dc)     

    def HitTest(self, pos):
        hitx = pos[0]
        hity = pos[1]
        found = False
        grid = None
        for k, coord in enumerate(self.xic_axco):
            print coord
            currentx1 = coord[0][0]
            currentx2 = coord[0][2]
            currenty1 = coord[1][1]
            currenty2 = coord[1][3]
            if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                found = True
                grid = k
                break
        print grid
        print found
        return found, grid

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
        pos = event.GetPositionTuple()
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
        pos = event.GetPositionTuple()
        found, grid = self.HitTest(pos)
        self.found = found
        self.grid = grid
        self.xic.time_range = (self.xic.full_time_range[0],self.xic.full_time_range[1])
        self.Refresh()

    def OnLeftUp(self,event):
        pos = event.GetPositionTuple()
        found, grid = self.HitTest(pos)
        if self.LeftDown:
            key = self.LeftDown[1]
        if found:
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
            if self.parent_window.tb.GetToolState(10):
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
        if found and pos != self.postup and not self.parent_window.tb.GetToolState(30) and not self.parent_window.tb.GetToolState(20) and not self.parent_window.tb.GetToolState(10):
            time = self.ConvertPixelToTime(pos[0])
            print "Time: " + str(time)
            try:
                self.new_stopTime = time
                self.xic.time_range=(self.new_startTime,self.new_stopTime)
            except:
                pass
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
        self.Refresh()

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
            if member[1]>startTime and member[1]<stopTime and key == member[7]:
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
        self.img.SaveFile(pngfile,wx.BITMAP_TYPE_PNG)          

    def OnSaveSVG(self, event):
        svgfile, dir = self.get_single_file("Select image file...", "SVG files (*.svg)|*.svg")
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

    def GetMaxSignal(self, startTime, stopTime, key):
        sub_xic = []
        for member in self.xic.data[key]:
            if member[0]>=startTime and member[0]<=stopTime:
                sub_xic.append(member)
        try:
            return max(t[1] for t in sub_xic)
        except:
            return 0

    def myRound(self, x, base=5):
        return int(base*round(float(x)/base))

    def set_axes(self):
        space = 40
        y_marg = 25
        indent = 50
        width = 600
        xic_total_height = 0
        number_xics = len(self.xic.data)
        self.xic_axco = []
        height = (float(550)/float(number_xics))-(5*number_xics)
        for k in range(0, number_xics):
            yco = y_marg+(space*k)+(height*k)+(xic_total_height)
            self.xic_axco.append(((indent,yco+height,indent + width,yco+height),(indent,yco,indent,yco+height)))
            #self.xic_axco.append(((50,yco+height,500,yco+height),(50,yco,50,yco+height)))
        print self.xic_axco

    def DrawXic(self, dc, key):
        startTime = self.xic.time_range[0]
        stopTime = self.xic.time_range[1]
        xaxis = self.xic_axco[key][0]
        yaxis = self.xic_axco[key][1]
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
        max_signal = self.GetMaxSignal(startTime, stopTime, key)
        tr = stopTime-startTime
        print "tr:" + str(tr)
        px = float(width)/float(tr)
        try:
            py = float(height)/float(max_signal)
        except:
            py = 0
        self.xic_width = width
        x1 = yaxis[0]
        y1 = yaxis[3]
        dc.SetTextForeground("BLACK")
        dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
        dc.DrawText("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7)
        self.svg["text"].append(("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7,0.00001))

        points = []
        print "building"
        for member in self.xic.data[key]:
            if member[0]>startTime and member[0]<stopTime:
                x2 = yaxis[0] + px*(member[0]-startTime)
                y2 = yaxis[1] + (height - member[1]*py)
                points.append(wx.Point(x2, y2))
        print "drawing"
        dc.DrawLines(points)
        self.svg["pointLists"].append(points)

        xticks = []
        if tr >= 0.5:
            if tr >= 100:
                scale = 20
            if tr >= 50 and tr < 100:
                scale = 10
            if tr >= 20 and tr < 50:
                scale = 5
            if tr >= 5 and tr < 20:
                scale = 2
            if tr >= 0 and tr < 5:
                scale = 0.5
            if scale >= 1:
                firstlabel = self.myRound(startTime, scale)
                lastlabel = self.myRound(stopTime, scale)
            if scale >= 0.1:
                firstlabel = float(self.myRound(startTime*10, scale*10))/float(10)
                lastlabel = float(self.myRound(stopTime*10, scale*10))/float(10)
            if firstlabel < startTime:
                firstlabel += scale
            if lastlabel > stopTime:
                lastlabel -= scale
            if scale >= 1:
                for i in range (firstlabel, lastlabel + scale, scale):
                    xticks.append(i)
            if scale >= .1 and scale < 1:
                for i in range (firstlabel*10, lastlabel*10 + scale*10, scale*10):
                    xticks.append(float(i)/float(10))
        else:
            xticks.append(round(startTime, 1))
            xticks.append(round(stopTime, 1))
        for member in xticks:
            x1 = self.xic_axco[key][0][0] + px*((member-startTime))
            dc.DrawText(str(member), x1-8,yaxis[3]+5)
            self.svg["text"].append((str(member), x1-8,yaxis[3]+5,0.00001))
            dc.DrawLine(x1, yaxis[3], x1, yaxis[3]+2)
            self.svg["lines"].append((x1, yaxis[3], x1, yaxis[3]+2))
        dc.DrawText("mz " + str(self.xic.xic_mass_ranges[key][0]) + '-'+ str(self.xic.xic_mass_ranges[key][1]) + ' (' + self.xic.xic_filters[key].strip() + ')', self.xic_axco[key][1][0], self.xic_axco[key][1][1] - 20)
        self.svg["text"].append(("mz " + str(self.xic.xic_mass_ranges[key][0]) + '-'+ str(self.xic.xic_mass_ranges[key][1]), self.xic_axco[key][1][0], self.xic_axco[key][1][1] - 20,0.00001))
#            if currentFile['vendor']=='Thermo':
#                rt = currentFile['rt_dict'][currentFile['scanNum']]
#            elif currentFile['vendor']=='ABI':
#                rt = currentFile['rt_dict'][(currentFile['scanNum'], currentFile['experiment'])]
#            current_x = currentFile['xic_axco'][key][0][0] + ((rt-startTime)*px)
#            dc.SetPen(wx.Pen(wx.RED,2))
#            dc.DrawLine(current_x, yaxis[1], current_x, yaxis[3])
        #self.msdb.svg["lines"].append((current_x, yaxis[1], current_x, yaxis[3]))
        dc.SetPen(wx.Pen(wx.BLACK,1))