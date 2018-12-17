
import wx
import mz_workbench.mz_core as mz_core
import  wx.lib.editor    as  editor
from collections import defaultdict
import re
import os,sys

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
from additions import floatrange


install_dir = os.path.dirname(__file__)

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
        self.drop_object = None
        self.drop_coords = None

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
        '''
        
         Main function that handles click & drag of mouse.  Performs "rubber banding" when selecting a mass range.
         Also draws text or lines when moving them to show where they would be repositioned.
         DC overlay is used for these purposes.
        
        '''
        if event.Dragging() and event.LeftIsDown() and not self.parent_window.tb.GetToolState(10):  #self.selected
            if self.found:
                pdc = wx.BufferedDC(wx.ClientDC(self.parent_window), self._Buffer)
                dc = wx.GCDC(pdc)
                odc = wx.DCOverlay(self.overlay, pdc)
                odc.Clear()
                pos = event.GetPosition()
                found, grid = self.HitTest(pos)
                #If on the same axis, draw the horizontal line across
                if not self.parent_window.tb.GetToolState(20):
                    if found and grid == self.grid:
                        dc.DrawLine(self.postup[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                        dc.SetPen(wx.Pen(wx.BLUE,2))
                        #This is the first position marking the OnLeftDown
                        dc.DrawLine(self.postup[0], self.yaxco[1], self.postup[0], self.yaxco[3])
                        #Draw vertical line marking the current position.
                        dc.DrawLine(pos[0], self.yaxco[1], pos[0], self.yaxco[3])
                        brushclr = wx.Colour(0,0,255,8)
                        dc.SetBrush(wx.Brush(brushclr))
                        if self.postup[0] < pos[0]:
                            dc.DrawRectangle(self.postup[0], self.yaxco[1], pos[0] - self.postup[0], self.yaxco[3]- self.yaxco[1])
                        else:
                            dc.DrawRectangle(pos[0], self.yaxco[1], self.postup[0] - pos[0], self.yaxco[3]- self.yaxco[1])
                    else:
                        if grid != None:
                            current = self.spectrum.axco[grid][1]
                            dc.SetPen(wx.Pen(wx.BLUE,2))
                            #This is the first position marking the OnLeftDown
                            dc.DrawLine(self.postup[0], self.yaxco[1], self.postup[0], self.yaxco[3])
                            #Draw vertical line marking the current position.
                            dc.DrawLine(pos[0], current[1], pos[0], current[3])                            
                else:
                    if found and grid == self.grid:
                        dc.DrawLine(self.postup[0], self.postup[1], pos[0], pos[1])
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
            if item == 'LINE':
                firstMass = self.spectrum.mass_ranges[key][0]
                lastMass = self.spectrum.mass_ranges[key][1]
                xaxis = self.spectrum.axco[key][0]
                yaxis = self.spectrum.axco[key][1]
                height = yaxis[1]-yaxis[3]
                width = xaxis[2]-xaxis[0]
                max_int = self.GetMaxInt(firstMass, lastMass)
                mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
                print "LINE...."
                
                # These are the original x, y coords of the line
                # pos = (x, y) is the NEW position moved to
                # self.postup is where the button was clicked.
                # So where to draw?
                # Calculate offset, and add to original coords.
                # Convert from Mass, intensity to x, and y coords.
                if max_int > 0:
                    x1 = yaxis[0] + width*((member[0]-firstMass)/float(mr))
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                    x2 = yaxis[0] + width*((member[2]-firstMass)/float(mr))
                    y2 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[3]/float(max_int))
                    
                    offsetx = self.postup[0]-pos[0]
                    offsety = self.postup[1]-pos[1]
                    self.drop_coords = (x1 - offsetx, y1-offsety, x2 - offsetx, y2 - offsety)
                    dc.DrawLine(*self.drop_coords)
                
            if item == 'TEXT':
                firstMass = self.spectrum.mass_ranges[key][0]
                lastMass = self.spectrum.mass_ranges[key][1]
                xaxis = self.spectrum.axco[key][0]
                yaxis = self.spectrum.axco[key][1]
                height = yaxis[1]-yaxis[3]
                width = xaxis[2]-xaxis[0]
                max_int = self.GetMaxInt(firstMass, lastMass)
                mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
                
                x1 = yaxis[0] + width*((member[1]-firstMass)/float(mr))
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

        # Make new offscreen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self._Buffer = wx.EmptyBitmap(*Size)
        self.set_axes()
        self.UpdateDrawing()
        #self.Refresh()
        if event:
            event.Skip()
        

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

class SpecViewLitePanel(wx.Frame):
    def __init__(self, parent, spectrum):
        wx.Frame.__init__(self, parent, -1, title="SpecView Lite", size=(1000, 1000))
        
       
        sty = wx.BORDER_SUNKEN
        self.sp = wx.SplitterWindow(self, size=(700, 750))
        
        self.p1 = wx.Panel(self.sp, style=sty)
        self.p2 = wx.Panel(self.sp, style=sty)
        self.p1.SetBackgroundColour("white")
        wx.StaticText(self.p1, -1, "", (5,5))

        self.p2.SetBackgroundColour("white")
        wx.StaticText(self.p2, -1, "Panel Two", (5,5))
        
        #This sizer is for panel 2, such that the text control can expand to fill the lower splitter window.
        p2Sizer = wx.GridSizer(rows=1, cols=1, hgap=1, vgap=1)
        
        
        self.spectrum = spectrum
        self.sp.SetMinimumPaneSize(20)
        self.sp.SplitHorizontally(self.p1, self.p2, -75)
    
        self.t4 = wx.TextCtrl(self.p2, -1, spectrum.notes, size=(800, 200), style=wx.TE_MULTILINE|wx.TE_RICH2)
        
        #Add the text control to the Sizer.
        p2Sizer.Add(self.t4, 0, wx.EXPAND)
        self.p2.SetSizer(p2Sizer)
        self.p2.Fit()
        
        tb = self.CreateToolBar( TBFLAGS )
        
        imdir = os.path.join(install_dir, r'image')
        #try:
        self.bmp = [wx.Bitmap(imdir +'\\' + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP) for iconName in ["select",'line','text','SVG', 'PNG', 'dial','pdf']]
        img = wx.Image(imdir +'\\MZRangeGraphic.png')
        tsize=(48,48)
        img.Rescale(*tsize)
        new_bmp = wx.BitmapFromImage(img)        
        self.bmp.append(new_bmp)
        self.tb = tb
        
        self.SetToolBar(tb)
        self.SpecWindow = SpecWindow(self.p1, -1, spectrum, parent_window=self)
        
        #This sizer is for the entire splitter window, so it can fill the available space.
        sizer = wx.GridSizer(rows=1, cols=1, hgap=1, vgap=1)
        sizer.Add(self.sp, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        
        #On Sizing event, call Update Drawing
        self.p1.Bind(wx.EVT_SIZE, self.OnSize)
        
        #Size to window
        self.SpecWindow.set_axes()
        self.SpecWindow.UpdateDrawing()
        
        self.p1.SetMaxSize((1000, 800))
        self.SetMaxSize((1000,900))
        self.p1.SetMinSize((400, 400))
        self.SetMinSize((400,400))
        
    def OnSize(self, event):
        # Size event from SpecViewLite Panel
        self.SpecWindow.set_axes()
        self.SpecWindow.UpdateDrawing()
        
        event.Skip()

    def AddToolBarItems(self, tb):
        tsize = (24,24)
        for pos, label, art, short_help, long_help, evt_id  in self.ToolBarData():
            if pos != "sep":
                try:
                    new_bmp = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, tsize)
                except:
                    try:
                        new_bmp = art
                    except:
                        new_bmp = wx.ArtProvider.GetBitmap(wx.ART_CLOSE)
                tb.AddCheckTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
                #tb.AddCheckLabelTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
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
            self.OnSetmz(None)  
        if event.GetId() == 80:
            self.OnSetLabelThreshold(None)
        if event.GetId() == 90:
            self.OnPdf(None)        

    def ToolBarData(self):
        return ((10, "Select", self.bmp[0], "Select", "Long help for 'Open'", 10),
            (20, "Line", self.bmp[1], "Draw Line", "Long help for 'Close'", 20),
            (30, "Text", self.bmp[2], "Insert Text", "Long help for 'Save'", 30),
            ("sep", 0, 0, 0, 0, 0),
            (40, "SVG", self.bmp[3], "Save SVG", "Long help for 'Save'", 40),
            (60, "PNG", self.bmp[4], "Save PNG", "Long help for 'Save'", 60),
            (90, "PDF", self.bmp[6], "Save PDF", "Long help for 'Save'", 90),
            ("sep", 0, 0, 0, 0, 0),
            (50, "Save", wx.ART_FILE_SAVE, "Save Annotations", "Long help for 'Save'", 50),
            ("sep", 0, 0, 0, 0, 0),
            (70, "Spectrum Range", self.bmp[7], "Specify mass range", "Mass Range'", 70),
            (80, "Adjust label threshold", self.bmp[5], "Adjust label threshold", "Adjust label threshold'", 80))     

    def OnPdf(self, evt):
        self.tb.ToggleTool(90, False)
        self.SpecWindow.OnSavePDF(None)
    
    def OnSetLabelThreshold(self, evt):
        self.tb.ToggleTool(80, False)
        if self.spectrum.scan_type in ['MS2' or 'etd']:
            dlg = wx.TextEntryDialog(self, 'Enter label threshold (Da) \n(0 to go by instrument default)', 'Set fragment ion label threshold')
            if dlg.ShowModal() == wx.ID_OK:
                if dlg.GetValue() != u'0':
                    try:
                        self.SpecWindow.adjusted_threshold = float(dlg.GetValue())
                        
                        if self.spectrum.scan_type in ['MS2', 'etd'] and self.spectrum.sequence:
                            self.spectrum.label_dict = {}
                            self.SpecWindow.build_label_dict(self.spectrum.charge) 
                        
                    except:
                        wx.MessageBox("Enter a value")
                else:
                    self.SpecWindow.adjusted_threshold = 0
                    if self.spectrum.scan_type in ['MS2', 'etd'] and self.spectrum.sequence:
                            self.spectrum.label_dict = {}
                            self.SpecWindow.build_label_dict(self.spectrum.charge) 
                
                self.SpecWindow.UpdateDrawing()            
                
    
            dlg.Destroy()        

    def OnSave(self,event):
        self.spectrum.lines = self.SpecWindow.lines
        self.spectrum.text = self.SpecWindow.text
        self.tb.ToggleTool(50, False)

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
    def OnSVG(self,event):
        self.SpecWindow.OnSaveSVG(None)
    def OnSavePNG(self, event):
        self.SpecWindow.OnSavePNG(None)
        
        
    def OnKeyDown(self,event):
        print"key"
        
    def OnSetmz(self,event):
        self.tb.ToggleTool(70, False)
        dlg = wx.TextEntryDialog(self, 'Start mz-Stop mz or Center, Width', 'Set mz range')
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.GetValue().find("-") > -1:
                entry = dlg.GetValue().split("-")
                low_mass = float(entry[0].strip())
                hi_mass = float(entry[1].strip())
            elif dlg.GetValue().find(",") > -1:
                entry = dlg.GetValue().split(",")
                center = float(entry[0].strip())
                width = float(entry[1].strip())
                hi_mass = center + width
                low_mass = center - width
            self.spectrum.newf = low_mass
            self.spectrum.newl = hi_mass
            step = float(self.spectrum.newl-self.spectrum.newf)/float(self.spectrum.axes)
            current_mz = self.spectrum.newf
            self.spectrum.mass_ranges=[]
            for i in range(0, self.spectrum.axes):
                self.spectrum.mass_ranges.append((current_mz, current_mz + step))
                current_mz += step
            print self.spectrum.mass_ranges
            #self.ClearOverlay()           
            self.SpecWindow.UpdateDrawing()            
            

        dlg.Destroy()

class SpecWindow(BufferedWindow):  #wx.Window
    def __init__(self, parent, ID, spectrum, parent_window):
        self.found = False
        self.adjusted_threshold = 0
        self.parent_window = parent_window
        self.spectrum = spectrum
        self.show_processed_data = self.spectrum.viewProcData
        #if self.spectrum.processed_scan_data:
        #    self.show_processed_data = True
        #else:
        #    self.show_processed_data = False
        print self.spectrum.filter
        print "S"
        self.set_axes()
        #self.set_mass_ranges()
        #self.spectrum.axco = [((50, 575.0, 650, 575.0), (50, 25.0, 50, 575.0))]
        self.spectrum.label_dict = {}
        self.spectrum.found2theor = {}
        self.text = []
        self.selected = None
        self.postup = None
        self.lines = []
        self.img = None
        self.spectrum.errorFlag = False
        self.spectrum.label_non_id = True
        self.spectrum.display_filename = False
        try:
            if self.spectrum.lines:
                self.lines = self.spectrum.lines
        except:
            pass
        try:
            if self.spectrum.text:
                self.text = self.spectrum.text
        except:
            pass        
        print self.spectrum.scan_type
        if self.spectrum.scan_type in ['MS2', 'etd'] and self.spectrum.sequence:
            self.build_label_dict(self.spectrum.charge)
        self.pa = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI d Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.etd = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI (t E d sa|d sa) Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #TOF MS p NSI Full ms2 540.032306122@0[100-1400][1375:4]
        self.tofms2 = re.compile('.*?(TOF MS) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(\d+?)\[(\d+?)-(\d+?)\]\[(\d+?):(\d+?)\]')
        self.ms1 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #TOF MS + p NSI Full ms [350-1500] TOF MS + p NSI Full ms [10-600]
        self.qms1 = re.compile('.*?(TOF MS) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.targ = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #targms3 FTMS + c NSI Full ms3 566.40@cid35.00 792.50@hcd50.00 [100.00-2000.00]
        self.targ_ms3 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms3 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.mr = re.compile('\[(\d+?[.]?\d*?)[-](\d+?[.]?\d*?)\]')
        self.mass_dict = {"Thermo_ms2":[self.pa, 5,6],
                              "Thermo_ms1":[self.ms1, 2,3],
                              "Thermo_targ_ms2":[self.targ, 5,6],
                              "Thermo_targ_ms3":[self.targ_ms3, 8,9],
                              "ABI_ms2":[self.tofms2, 4,5],
                              "ABI_ms1":[self.qms1, 2,3],
                              "Thermo_etd":[self.etd, 6,7]} 
        self._buffer = wx.EmptyBitmap(900,900)
        BufferedWindow.__init__(self, parent, parent, size=(1000,1000))
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
        self.right_down_pos = None

    def Draw(self, dc):
        self.OnDraw(dc)           
    
    def HitTest(self, pos):
        hitx = pos[0]
        hity = pos[1]
        found = False
        grid = None
        for k, coord in enumerate(self.spectrum.axco):
            currentx1 = coord[0][0]
            currentx2 = coord[0][2]
            currenty1 = coord[1][1]
            currenty2 = coord[1][3]
            if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                found = True
                grid = k
                break
        if not found:
            grid=-1
        print grid
        print found
        return found, grid

    def OnLeftUp(self,event):
        pass

    def ConvertIntensityToPixel(self, intensity, axis):
        yaxis = self.spectrum.axco[axis][1]
        firstMass = self.spectrum.mass_ranges[axis][0]
        lastMass = self.spectrum.mass_ranges[axis][1]        
        max_int = self.GetMaxInt(firstMass, lastMass)
        pixel = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(intensity/float(max_int))
        return pixel

    def ConvertMassToPixel(self, mass, axis):
        firstMass = self.spectrum.mass_ranges[axis][0]
        xaxis = self.spectrum.axco[axis][0]
        yaxis = self.spectrum.axco[axis][1]
        width = xaxis[2]-xaxis[0]
        mr = self.spectrum.mass_ranges[axis][1]-self.spectrum.mass_ranges[axis][0]
        pixel = yaxis[0] + width*((mass-firstMass)/float(mr))
        return pixel    

    def ConvertPixelToMass(self, pixel, axis):
        lm = self.spectrum.mass_ranges[axis][1]
        fm = self.spectrum.mass_ranges[axis][0]
        mr = lm - fm
        pr = self.spectrum.axco[0][0][2] - self.spectrum.axco[0][0][0]
        mpp = float(mr)/float(pr)
        #mass = (((pixel - currentFile["axco"][0][0][0])/float(currentFile["axco"][0][0][2])) * float(lm-fm)) + fm
        mass = ((pixel - self.spectrum.axco[0][0][0]) * mpp)+ fm
        return mass

    def ConvertPixelToIntensity(self, pixel, axis):
        yaxis = self.spectrum.axco[axis][1]
        firstMass = self.spectrum.mass_ranges[axis][0]
        lastMass = self.spectrum.mass_ranges[axis][1]
        max_int = self.GetMaxInt(firstMass, lastMass)
        inten = (float(yaxis[3]-pixel)/float((yaxis[3]-yaxis[1])))*float(max_int)
        return inten

    def OnLeftDown(self, event):
        self.SetFocus()
        self.spectrum.notes = self.parent_window.t4.GetValue()
        pos = event.GetPosition()
        self.postup = pos
        #if self.parent.tb.GetToolEnabled(30):
        #    event.Skip()
        #else:
        found, grid = self.HitTest(pos)
        self.LeftDown = (found, grid)
        self.found = found
        self.grid = grid
        print "ON LEFT DOWN"
        print grid
        print found
        print pos
        if grid > -1:
            self.yaxco = self.spectrum.axco[grid][1]
            print self.yaxco
            print "SET YAX"
            print pos
            if found:
                mz = self.ConvertPixelToMass(pos[0], grid)
                self.spectrum.newf = mz

    def OnLeftUp(self, event):
        
        try:
            print self.postup
        except:
            event.Skip()
        
        pos = event.GetPosition()
        found, grid = self.HitTest(pos)
        if found:
            #---------------------------
            #DRAWING TEXT
            if self.parent_window.tb.GetToolState(30):
                dlg = wx.TextEntryDialog(None, "Text", "Annotate Spectrum", style=wx.OK|wx.CANCEL)
                if dlg.ShowModal()==wx.ID_OK:
                    mz = self.ConvertPixelToMass(pos[0], grid)
                    yaxis = self.spectrum.axco[grid][1]
                    firstMass = self.spectrum.mass_ranges[grid][0]
                    lastMass = self.spectrum.mass_ranges[grid][1]
                    max_int = self.GetMaxInt(firstMass, lastMass)
                    #y1 = yaxis[1] + yaxis[3] - yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                    #y2 = yaxis[3]
                    inten = (float(yaxis[3]-pos[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                    print inten
                    print "INTEN"
                    print max_int
                    self.text.append([dlg.GetValue(), mz, inten,0,0,0,0,0])
                event.Skip()
                
            #----------------------------------    
            #DRAWLING A LINE
            if self.parent_window.tb.GetToolState(20):
                print "LINES"
                if self.LeftDown[1]==grid:
                    print "ENTER"
                    mzl = self.ConvertPixelToMass(pos[0], grid)
                    mzf = self.ConvertPixelToMass(self.postup[0], grid)
                    yaxis = self.spectrum.axco[grid][1]
                    firstMass = self.spectrum.mass_ranges[grid][0]
                    lastMass = self.spectrum.mass_ranges[grid][1]
                    max_int = self.GetMaxInt(firstMass, lastMass)
                    intenf = (float(yaxis[3]-self.postup[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                    intenl = (float(yaxis[3]-pos[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                    #-------------------First four list elems are coords, next 5 deal with selection range.
                    self.lines.append([mzf, intenf, mzl, intenl,0,0,0,0,0])
                event.Skip()
            
            #------------------------------------
            #SELECTING
            if self.parent_window.tb.GetToolState(10) and not self.drop_coords:
                #----------------------------------------------------------------------
                # Object not being dragged; select on, check for selecting an object
                #----------------------------------------------------------------------
                print "SELECT"
                found = False
                #-----------------------------------------------WAS TEXT SELECTED?
                for i, member in enumerate(self.text):
                    if pos[0] > member[3] and pos[1] > member[4] and pos[0] < member[5] and pos[1] < member[6]:
                        self.selected = ("TEXT", i)
                        found = True
                    if found:
                        break
                #-----------------------------------------------WAS A LINE SELECTED?
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
                        
                        mzl = self.ConvertPixelToMass(drop_coords[2], grid)
                        mzf = self.ConvertPixelToMass(drop_coords[0], grid)
                        yaxis = self.spectrum.axco[grid][1]
                        firstMass = self.spectrum.mass_ranges[grid][0]
                        lastMass = self.spectrum.mass_ranges[grid][1]
                        max_int = self.GetMaxInt(firstMass, lastMass)
                        intenf = (float(yaxis[3]-drop_coords[1])/float((yaxis[3]-yaxis[1])))*float(max_int)
                        intenl = (float(yaxis[3]-drop_coords[3])/float((yaxis[3]-yaxis[1])))*float(max_int)                
                        print "Drop object"
                        self.lines[obj[1]][0]=mzf
                        self.lines[obj[1]][1]=intenf
                        self.lines[obj[1]][2]=mzl
                        self.lines[obj[1]][3]=intenl
                        
                        self.selected = None
                        self.drop_coords = None
                        self.drop_object = None                
                        
                        event.Skip()
                if self.selected:        
                    if self.selected[0] == 'TEXT':
                    
                        mz = self.ConvertPixelToMass(self.drop_coords[1], grid)
                        yaxis = self.spectrum.axco[grid][1]
                        firstMass = self.spectrum.mass_ranges[grid][0]
                        lastMass = self.spectrum.mass_ranges[grid][1]
                        max_int = self.GetMaxInt(firstMass, lastMass)
                        
                        inten = (float(yaxis[3]-self.drop_coords[2])/float((yaxis[3]-yaxis[1])))*float(max_int)
                        
                        self.text[obj[1]][1] = mz
                        self.text[obj[1]][2] = inten
                        
                        self.selected = None
                        self.drop_coords = None
                        self.drop_object = None                
                        
                        event.Skip()                    
                
            tool_selected = False
            
            #-------------------------------------------------
            #ZOOM IN SPECTRUM
            if not self.parent_window.tb.GetToolState(30) and not self.parent_window.tb.GetToolState(20) and not self.parent_window.tb.GetToolState(10):
                if self.postup:
                    if pos != self.postup:
                        mz = self.ConvertPixelToMass(pos[0], grid)
                        print "UP:" + str(mz)
                        self.spectrum.newl = mz
                        if self.spectrum.newl < self.spectrum.newf:
                            temp = 0
                            temp = self.spectrum.newl
                            self.spectrum.newl = self.spectrum.newf
                            self.spectrum.newf = temp
                        step = float(self.spectrum.newl-self.spectrum.newf)/float(self.spectrum.axes)
                        current_mz = self.spectrum.newf
                        self.spectrum.mass_ranges=[]
                        for i in range(0, self.spectrum.axes):
                            self.spectrum.mass_ranges.append((current_mz, current_mz + step))
                            current_mz += step
                        print self.spectrum.mass_ranges
            self.ClearOverlay()           
            self.UpdateDrawing()

    def OnRightUp(self,event):
        pos = event.GetPosition()
        found, grid = self.HitTest(pos)
        if pos == self.right_down_pos:
            #self.set_mass_ranges()
            self.spectrum.mass_ranges=[(self.spectrum.full_range[0], self.spectrum.full_range[1])]
        self.set_axes()
        self.UpdateDrawing()

    def OnRightDown(self,event):
        pos = event.GetPosition()
        found, grid = self.HitTest(pos)
        self.right_down_pos = pos
        self.Refresh()

    def OnKeyDown(self,event):
        print "Key"
        key = event.GetKeyCode()
        if key == 81: # "Q"
            if self.spectrum.processed_scan_data:
                self.show_processed_data = not self.show_processed_data
        if key == 69: #"E"
            self.spectrum.errorFlag = not self.spectrum.errorFlag
        if key==70:
            self.spectrum.display_filename = not self.spectrum.display_filename
        if key == 85:
            self.spectrum.label_non_id = not self.spectrum.label_non_id
        if key == 49: #"1"
            self.spectrum.axes = 1
            self.set_axes()
        if key == 50: #"2"
            self.spectrum.axes = 2
            self.set_axes()
        if key == 51: #"3"
            self.spectrum.axes = 3
            self.set_axes()
        if key == 127:
            print "DEL"
            if self.selected:
                #or member in self.selected:
                if self.selected[0]=="TEXT":
                    del self.text[self.selected[1]]
                if self.selected[0]=="LINE":
                    del self.lines[self.selected[1]]
                self.selected=None
        print key
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
            if self.selected:
                if self.selected[0]=="TEXT":
                    current = self.text[self.selected[1]] # 1=mz, 2= inten, coords = 3, 4, 5, 6, key =7
                    currentm = current[1]
                    current_key = current[7]
                    current_pixel = self.ConvertMassToPixel(currentm, current_key)
                    if key == 59:
                        current_pixel -= 5
                    else:
                        current_pixel += 5
                    new_mz = self.ConvertPixelToMass(current_pixel, current_key)
                    self.text[self.selected[1]][1]=new_mz    
                if self.selected[0]=="LINE":
                    current = self.lines[self.selected[1]] # 0=x1, 1=y1, 2=x2, 3=y2, coords = 4,5,6,7 key=8
                    currentm1 = current[0]
                    currentm2 = current[2]
                    current_key = current[8]
                    current_pixel1 = self.ConvertMassToPixel(currentm1, current_key)
                    current_pixel2 = self.ConvertMassToPixel(currentm2, current_key)
                    if key == 59:
                        current_pixel1 -= 5
                        current_pixel2 -= 5
                    else:
                        current_pixel1 += 5
                        current_pixel2 += 5
                    new_mz1 = self.ConvertPixelToMass(current_pixel1, current_key)
                    new_mz2 = self.ConvertPixelToMass(current_pixel2, current_key)
                    self.lines[self.selected[1]][0]=new_mz1 
                    self.lines[self.selected[1]][2]=new_mz2                 
        self.UpdateDrawing()

    def set_mass_ranges(self):
        vendor = self.spectrum.vendor
        found = False
        for member in self.mass_dict.keys():
            pa = self.mass_dict[member][0]
            id = pa.match(self.spectrum.filter)
            if id:
                low_mass = id.groups()[self.mass_dict[member][1]]
                hi_mass = id.groups()[self.mass_dict[member][2]]
                found = True
                break
        if not found:
            raise ValueError("Filter not parsed!  Unrecognized file format!")
        self.spectrum.scan_low_mass = low_mass
        self.spectrum.scan_high_mass = hi_mass
        self.spectrum.mass_ranges=[(float(low_mass), float(hi_mass))]   

    def set_axes(self):
       
        sz = self.parent_window.p1.GetClientSize()
        
        space = 40
        y_marg =20
        indent = 0
        num_axes = self.spectrum.axes
        
        spec_total_height = 0 #float(550)
        height = (float(sz[1])-100)/float(num_axes)
        
        if num_axes == 2:
            height -= num_axes*20
        if num_axes == 3:
            height -= num_axes*15
        
        space = 60
        indent = 50
        width = (float(sz[0])/float(1.05))-100
        self.spectrum.axco = []
        mr = self.spectrum.mass_ranges
        fm = mr[0][0]
        current_fm = fm
        lm = mr[len(mr) - 1][1]
        step = float(lm - fm)/float(num_axes)
        self.spectrum.mass_ranges=[]
        for k in range(0, num_axes):
            yco = y_marg+(space*k)+(height*k)+(spec_total_height)
            self.spectrum.axco.append(((indent,yco+height,indent + width,yco+height),(indent,yco,indent,yco+height)))
            self.spectrum.mass_ranges.append((current_fm, current_fm + step))
            print str(k) + "-" + str((current_fm, current_fm + step))
            current_fm += step
        print self.spectrum.mass_ranges
        print self.spectrum.axco

    def OnDraw(self, dc):
        try:
            del self.svg
        except:
            pass
        self.svg = defaultdict(list)
        size = self.GetClientSize()
        dc.SetBackground( wx.Brush("White") )
                #dc.SetBackgroundColour("White")
        dc.Clear()        
        #buffer = wx.EmptyBitmap(size.width, size.height)
        #dc = wx.BufferedDC(None, buffer)
        #dc = wx.BufferedDC(None, buffer)
        #dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK,2))
        for k in range(0, self.spectrum.axes):
            print "DRAWING... spec axis " + str(k)
            self.DrawSpectrum(dc, k, self.spectrum.profile) #draws the centroid
            self.AnnotateText(dc, k)
            self.AnnotateLines(dc,k)
            self.MarkSelected(dc,k)
            if self.spectrum.profile and not (self.show_processed_data or self.spectrum.viewCent):      #if profFlag and not (currentFile["viewCentroid"] or currentFile['Processing']):
                self.DrawProfileSpectrum(dc, k)
        self.storeImage(dc)
        #bpd = wx.BufferedPaintDC(self, buffer)
        #self.svg.Destroy()

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
    
    def OnSavePDF(self, event):
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
        
        busy = PBI.PyBusyInfo("Saving SVG, please wait...", parent=None, title="Processing...")
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
        
        del busy        
    
                       

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

    def GetMaxInt(self, fm, lm):
        
        sub_scan = []
        
        if self.spectrum.processed_scan_data and self.show_processed_data:
            for member in self.spectrum.processed_scan_data:
                if member[0]>=fm and member[0]<=lm:
                    sub_scan.append(member)            
                    
        else:
            for member in self.spectrum.scan_data:
                if member[0]>=fm and member[0]<=lm:
                    sub_scan.append(member)
        
        try:
            return max(t[1] for t in sub_scan)
        except:
            return 0

    def CheckLabels(self, loc, labels):
        found = False
        for member in labels:
            if loc > member[0] and loc < member[1]:
                found = True
        return found

    def myRound(self, x, base=5):
        return int(base*round(float(x)/base))

    def search_for_mass(self, mz, scan, vendor = 'Thermo'): #scan is the list of mz, intensity
        tolerance = 0.02
        if self.spectrum.vendor == 'Thermo':
            if self.spectrum.filter.find('TOF')>-1:
                tolerance = 0.05
            if self.spectrum.detector == "IT":
                tolerance = 0.5
        elif self.spectrum.vendor == 'ABI':
            tolerance = 0.5
        elif self.spectrum.vendor == 'ABI-MALDI':
            tolerance = 0.5
        if self.adjusted_threshold: tolerance = self.adjusted_threshold
        found = False
        found_mz = 0
        found_int = 0
        
        
        
        #for j, member in enumerate(scan):
            #if mz > member[0] - tolerance and mz < member[0] + tolerance:
                #found = True
                #found_mz = member[0]
                #found_int = member[1]
                #break
            
        candidates = [x for x in scan if mz-tolerance < x[0] < mz+tolerance]
        try:
            found_mz, found_int = max(candidates, key = lambda x: x[1])[:2]
            found = True
        except:
            pass            
            
            
        return found, found_mz, found_int

    def GetNtermMod(self, fixedmods):
        
        mod_dict = {'iTRAQ4plex': 'iTRAQ',
                    'TMT6plex': 'TMT',
                    'TMT': 'cTMT',
                    'iTRAQ8plex': 'iTRAQ8plex',
                    'HGly-HGly': 'HCGlyHCGly',
                    'HCGly-HCGly': 'HCGlyHCGly',
                    'HCGly-HCGly-HCGly-HCGly': 'HCGlyHCGlyHCGlyHCGly',
                    'HNGly-HNGly-HNGly-HNGly': 'HNGlyHNGlyHNGlyHNGly',
                    'HNGly-HNGly': 'HNGlyHNGly',
                    'LbA-LbA': 'LbALbA',
                    'HbA-HbA': 'HbAHbA',
                    'LbA-HbA': 'LbAHbA',
                    'Acetyl': 'Acetyl',
                    'Propionyl': 'Propionyl',
                    'Phenylisocyanate': 'Phenylisocyanate'}        
        
        nTermMod = ''
        
        mods = fixedmods.split(',')
        
        for mod in mods:
            mod = mod.strip()
            if mod.find('N-term') > -1:
                submod = mod.split('(')[0].strip()
                nTermMod = mod_dict[submod]
                break
        return nTermMod
    

    def build_label_dict(self, cg):
        if self.spectrum.scan_type != "MS1":
            print "Labeling"
            _ions = 'b/y'
            if self.spectrum.scan_type=="etd":
                _ions = 'c/z'
            if self.spectrum.profile:
                scan_data = self.spectrum.cent_data
            else:
                scan_data = self.spectrum.scan_data
            for j in floatrange(1, cg+1):
                #-----------------NEEFD TO CHANGE PARSE RULES
                if self.spectrum.sequence.find('-') == -1:
                    sequence = self.spectrum.sequence
                    nterm = self.GetNtermMod(self.spectrum.fixedmod)
                    cterm = ''
                else:
                    _seq = self.spectrum.sequence
                    seqstart = _seq.find('-')
                    seqend = _seq.rfind('-')
                    sequence = _seq[seqstart+1:seqend]
                    nterm = _seq[0:seqstart]
                    cterm = _seq[seqend+1:]
                if nterm == "H":
                    nterm = ''
                if cterm == "OH":
                    cterm = ''
                print sequence
                print nterm
                print cterm
                _ions = 'b/y'
                if self.spectrum.filter.find("etd") > -1:
                    _ions = 'c/z'
                self.spectrum.mz, self.spectrum.b_ions, self.spectrum.y_ions = mz_core.calc_pep_mass_from_residues(sequence, j, ions=_ions, Nterm = nterm, Cterm=cterm)
                if self.spectrum.varmod.find("Fucosylation") > -1 or self.spectrum.varmod.find("Hex") > -1 or self.spectrum.varmod.find("Xyl") > -1 or self.spectrum.varmod.find("Phospho") >-1 or self.spectrum.sequence.find("p")>-1 or self.spectrum.varmod.find("Hex") > -1:
                    self.spectrum.NL_ions = mz_core.get_fragment_neutral_losses(sequence, self.spectrum.b_ions, self.spectrum.y_ions, self.spectrum.varmod, j)
                    self.spectrum.precNL_ions = mz_core.get_precursor_neutral_losses(self.spectrum.mz, j, self.spectrum.varmod)            
                else:
                    self.spectrum.NL_ions = {}
                    self.spectrum.precNL_ions = {}
                vendor = self.spectrum.vendor
                key = None
                print self.spectrum.mz
                y_label = 'y'
                b_label = 'b'
                if self.spectrum.scan_type=='etd':
                    y_label = 'z'
                    b_label = 'c'
                for i, member in enumerate(self.spectrum.y_ions):
                    found, found_mz, found_int = self.search_for_mass(member, scan_data, self.spectrum.vendor)
                    if found:
                        if found_mz in self.spectrum.label_dict.keys():
                            self.spectrum.label_dict[found_mz] += ', ' + y_label + str(i+1)
                            #self.files[filename]["found2theor"][found_mz] = member
                            if j > 1:
                                self.spectrum.label_dict[found_mz] += ' ' + str(j) + '+'
                        else:
                            self.spectrum.label_dict[found_mz] = y_label + str(i+1)
                            self.spectrum.found2theor[found_mz] = member
                            if j > 1:
                                self.spectrum.label_dict[found_mz] += ' ' + str(j) + '+'
                                
                for i, member in enumerate(self.spectrum.b_ions):
                    found, found_mz, found_int = self.search_for_mass(member, scan_data, self.spectrum.vendor)
                    if found:
                        if found_mz in self.spectrum.label_dict.keys():
                            self.spectrum.label_dict[found_mz] += ', ' + b_label + str(i+1)
                            if j > 1:
                                self.spectrum.label_dict[found_mz] += ' ' + str(j) + '+'
                        else:
                            self.spectrum.label_dict[found_mz] = b_label + str(i+1)
                            self.spectrum.found2theor[found_mz] = member
                            if j > 1:
                                self.spectrum.label_dict[found_mz] += ' ' + str(j) + '+'
                        
                for i, member in enumerate(self.spectrum.NL_ions.keys()):
                    found, found_mz, found_int = self.search_for_mass(member, scan_data, self.spectrum.vendor)
                    if found:
                        if found_mz in self.spectrum.label_dict.keys():
                            self.spectrum.label_dict[found_mz] += ', ' + self.spectrum.NL_ions[member]
                        else:
                            self.spectrum.label_dict[found_mz] = self.spectrum.NL_ions[member]
                            self.spectrum.found2theor[found_mz] = member
                                    
                for i, member in enumerate(self.spectrum.precNL_ions.keys()):
                    found, found_mz, found_int = self.search_for_mass(member, scan_data, self.spectrum.vendor)
                    if found:
                        if found_mz in self.spectrum.label_dict.keys():
                            self.spectrum.label_dict[found_mz] += ', ' + self.spectrum.precNL_ions[member]
                        else:
                            self.spectrum.label_dict[found_mz] = self.spectrum.precNL_ions[member]
                            self.spectrum.found2theor[found_mz] = member   
                
                
    def MarkSelected(self, dc, key):
        '''
        
        This function draws the little circles around the selected object to highlight the selected state.
        
        '''
        if self.selected:
            cur = self.selected
            if cur[0]=="TEXT":
                dc.DrawCircle(self.text[cur[1]][3], self.text[cur[1]][4], 3)
                dc.DrawCircle(self.text[cur[1]][3], self.text[cur[1]][6], 3)
                dc.DrawCircle(self.text[cur[1]][5], self.text[cur[1]][4], 3)
                dc.DrawCircle(self.text[cur[1]][5], self.text[cur[1]][6], 3)
            if cur[0]=="LINE":
                dc.DrawCircle(self.lines[cur[1]][4], self.lines[cur[1]][5], 3)
                dc.DrawCircle(self.lines[cur[1]][4], self.lines[cur[1]][7], 3)
                dc.DrawCircle(self.lines[cur[1]][6], self.lines[cur[1]][5], 3)
                dc.DrawCircle(self.lines[cur[1]][6], self.lines[cur[1]][7], 3)            
                
    def AnnotateText(self, dc, key):
        '''
        
        Draws user specified text.
                
        '''
        firstMass = self.spectrum.mass_ranges[key][0]
        lastMass = self.spectrum.mass_ranges[key][1]
        xaxis = self.spectrum.axco[key][0]
        yaxis = self.spectrum.axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        max_int = self.GetMaxInt(firstMass, lastMass)
        mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
        for i, member in enumerate(self.text):
            if member[1]>firstMass and member[1]<lastMass:
                x1 = yaxis[0] + width*((member[1]-firstMass)/float(mr))
                if max_int > 0:
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[2]/float(max_int))
                    dc.DrawRotatedText(member[0], x1,y1,.0001)
                    self.svg["text"].append((member[0], x1, y1,.0001))
                    ext = dc.GetTextExtent(member[0])
                    member[3]=x1
                    member[4]=y1
                    member[5]=x1+ext[0]
                    member[6]=y1+ext[1]
                    try:
                        member[7]=key
                    except:
                        self.text[i].append(key)

    def AnnotateLines(self, dc, key):
        '''
        
        This function draws user specified lines on the spectrum.
        
        '''
        firstMass = self.spectrum.mass_ranges[key][0]
        lastMass = self.spectrum.mass_ranges[key][1]
        xaxis = self.spectrum.axco[key][0]
        yaxis = self.spectrum.axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        max_int = self.GetMaxInt(firstMass, lastMass)
        mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
        print "LINES...."
        for i, member in enumerate(self.lines):
            print member
            if member[0]>firstMass and member[0]<lastMass and max_int > 0:
                x1 = yaxis[0] + width*((member[0]-firstMass)/float(mr))
                y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                x2 = yaxis[0] + width*((member[2]-firstMass)/float(mr))
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
                if len(member)==8:
                    self.lines[i].append(key)
            
    def DrawSpectrum(self, dc, key, profile=False, drawLines = True):
        '''
        This is the main drawing function for centroided data.
        
        '''
        if self.spectrum.vendor == 'Thermo':
            if self.spectrum.filter.find('FTMS')>-1:
                thresh = 200
            elif any([x in self.spectrum.filter for x in ['TOF', 'Q1', 'Q3']]):
                thresh = 10
            else:
                thresh = 10
        elif self.spectrum.vendor == 'ABI':
            thresh = 10
        elif self.spectrum.vendor == 'ABI-MALDI':
            thresh = 10
        else:
            thresh = 0
        
        firstMass = self.spectrum.mass_ranges[key][0]
        lastMass = self.spectrum.mass_ranges[key][1]
        print "Masses"
        print firstMass
        print lastMass
        xaxis = self.spectrum.axco[key][0]
        yaxis = self.spectrum.axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        px = width
        self.width = width
        self.indent = yaxis[0]
        dc.DrawLine(*xaxis)
        self.svg["lines"].append(xaxis)
        dc.DrawLine(*yaxis)
        self.svg["lines"].append(yaxis)
        dc.DrawLine(xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1])
        self.svg["lines"].append((xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1]))
        max_int = self.GetMaxInt(firstMass, lastMass)
        mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
        #mr = currentFile["mass_ranges"][key][1]-currentFile["mass_ranges"][key][0]
        if key == 0:
            x = self.spectrum.axco[0][0][2]
            subxx = self.spectrum.axco[0][0][0]
            y = self.spectrum.axco[0][1][1]
            dc.DrawText("Scan: " + str(self.spectrum.scan), x+5, y)
            try:
                if self.spectrum.mascot_score:
                    dc.DrawText("Score: " + str(round(float(self.spectrum.mascot_score), 1)), x+5, y+20)
            except:
                pass
            print "SUB"
            print subxx
            print self.spectrum.axco
            if self.spectrum.display_filename:
                dc.DrawText(os.path.basename(self.spectrum.rawfile)[:-4], subxx, self.spectrum.axco[len(self.spectrum.axco)-1][0][1]+45)
            try:
                dc.DrawText(self.spectrum.filter, subxx, self.spectrum.axco[len(self.spectrum.axco)-1][0][1]+25)
            except:
                pass
            if self.spectrum.sequence:
                dc.DrawText(self.spectrum.sequence, subxx, self.spectrum.axco[len(self.spectrum.axco)-1][0][1]+50)
            
            
        if max_int > 0:
            cutoff = 0.75 * float(max_int)
            dc.SetTextForeground("BLACK")
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
            dc.DrawText("%.1e"%max_int, xaxis[0]-50, yaxis[1]-7)
            self.svg["text"].append(("%.1e"%max_int, xaxis[0]-50, yaxis[1]-7,0.00001))
            labels = []
            scan_type = 'MS2'
            if self.spectrum.profile:
                scan_data = self.spectrum.cent_data
            else:
                scan_data = self.spectrum.scan_data
            if self.spectrum.processed_scan_data and self.show_processed_data:
                scan_data = self.spectrum.processed_scan_data
            scan_data.sort(key = lambda t:t[1], reverse = True)
            if self.spectrum.detector=='FT':
                rd = 3
            elif self.spectrum.detector=='IT':
                rd = 1
            else:
                rd = 1
            for member in scan_data:
                if member[0]>firstMass and member[0]<lastMass:
                    x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                    x2 = x1
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                    y2 = yaxis[3]
                    if member[0] not in self.spectrum.label_dict.keys():
                        dc.SetPen(wx.Pen(wx.BLACK,1))
                        pen = wx.Pen(wx.BLACK,1)
                        dc.DrawLine(x1, y1, x2, y2)
                        self.svg["lines"].append((x1, y1, x2, y2 , pen))
                    else:
                        if self.spectrum.label_dict[member[0]].find("y") > -1 or self.spectrum.label_dict[member[0]].find("z") >-1:
                            dc.SetPen(wx.Pen(wx.RED,2))
                            pen = wx.Pen(wx.RED,2)
                        elif self.spectrum.label_dict[member[0]].find("b") > -1 or self.spectrum.label_dict[member[0]].find("c")>-1:
                            dc.SetPen(wx.Pen(wx.BLUE,2))
                            pen = wx.Pen(wx.BLUE,2)
                        else:
                            pen = wx.Pen(wx.BLACK,2)
                        dc.DrawLine(x1, y1, x2, y2)
                        self.svg["lines"].append((x1, y1, x2, y2, pen))
                        dc.SetPen(wx.Pen(wx.BLACK,1))
                    if member[1] > thresh or member[0] in self.spectrum.label_dict.keys():
                        angle = 90
                        pt = 10
                        right_margin = 9
                        if member[1] > cutoff:
                            angle = 15
                            pt = 9
                            right_margin = 50
                        if self.spectrum.axes > 1:
                            pt = 9
                        dc.SetFont(wx.Font(pt, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                        font = wx.Font(pt, wx.ROMAN, wx.NORMAL, wx.BOLD, False)
                        found = self.CheckLabels(x1, labels)
                        if not found:
                            if member[0] not in self.spectrum.label_dict.keys():
                                dc.SetTextForeground("BLACK")
                                if scan_type == "MS1":
                                    if len(member) > 2:
                                        if member[3] > 0:
                                            dc.DrawRotatedText(str(round(member[0],rd)) + ' +' + str(int(member[3])),x1-7,y1-5,angle)
                                            self.svg["text"].append((str(round(member[0],rd)) + ' +' + str(int(member[3])),x1-7,y1-5,angle, "BLACK", font))
                                            labels.append([x1-9,x1+9])
                                    else:
                                        dc.DrawRotatedText(str(round(member[0],rd)),x1-7,y1-5,angle)
                                        self.svg["text"].append((str(round(member[0],rd)),x1-7,y1-5,angle, "BLACK", font))
                                        labels.append([x1-9,x1+9])

                                else:
                                    if self.spectrum.label_non_id:
                                        dc.DrawRotatedText(str(round(member[0],rd)),x1-7,y1-5,angle)
                                        self.svg["text"].append((str(round(member[0],rd)),x1-7,y1-5,angle, "BLACK", font))
                                        labels.append([x1-9,x1+9])
                            else:
                                #Peak is labeled
                                error = ''
                                if self.spectrum.detector=='FT':
                                    th = self.spectrum.found2theor[member[0]]
                                    exp = member[0]
                                    if self.spectrum.errorFlag:
                                        error = ' ' + str(round((float(abs(exp-th)/float(th)))*1000000,1)) + ' ppm'
                                if self.spectrum.label_dict[member[0]].startswith("y") or self.spectrum.label_dict[member[0]].startswith("z"):
                                    dc.SetTextForeground("RED")
                                    color = "RED"
                                elif self.spectrum.label_dict[member[0]].startswith("b") or self.spectrum.label_dict[member[0]].startswith("c"):
                                    dc.SetTextForeground("BLUE")
                                    color = "BLUE"
                                else:
                                    color = "BLACK"
                                if 1==3:
                                    dc.DrawRotatedText(str(round(member[0],rd)) + ' ' + currentFile["label_dict"][member[0]],x1-7,y1-5,angle)
                                    self.svg["text"].append((str(round(member[0],rd)) + ' ' + currentFile["label_dict"][member[0]],x1-7,y1-5,angle, color, font))
                                else:
                                    dc.DrawRotatedText(str(round(member[0],rd)) + '  (' + self.spectrum.label_dict[member[0]] + ')' + error,x1-7,y1-5,angle)
                                    self.svg["text"].append((str(round(member[0],rd)) + '  (' + self.spectrum.label_dict[member[0]] + ')'+ error,x1-7,y1-5,angle, color, font))
                                labels.append([x1-9,x1+right_margin])
        dc.SetTextForeground("BLACK")        
        xticks = []
        if mr >= 5:
            if mr >= 10000:
                scale = 2500
            if mr >= 5000 and mr < 10000:
                scale = 1000
            if mr >= 2000 and mr < 5000:
                scale = 500
            if mr >= 1000 and mr < 2000:
                scale = 200
            if mr >= 500 and mr < 1000:
                scale = 100
            if mr >= 200 and mr < 500:
                scale = 50
            if mr >= 20 and mr < 200:
                scale = 5
            if mr >= 5 and mr < 20:
                scale = 1
            firstlabel = self.myRound(firstMass, scale)
            #if firstlabel < currentFile["fm"]:
            if firstlabel < firstMass:
                firstlabel += scale
            lastlabel = self.myRound(lastMass, scale)
            #if lastlabel > currentFile["lm"]:
            if lastlabel > lastMass:
                lastlabel -= scale
            for i in range (firstlabel, lastlabel + scale, scale):
                xticks.append(i)
        else:
            xticks.append(round(firstMass, 1))
            xticks.append(round(lastMass, 1))
        for member in xticks:
            if mr == 0.0:
                mr = 0.1
            x1 = self.spectrum.axco[key][0][0] + px*((member-firstMass)/float(mr))
            dc.DrawRotatedText(str(member), x1-8,yaxis[3]+5,0.00001)
            self.svg["text"].append((str(member), x1-8,yaxis[3]+5,0.00001))
            dc.DrawLine(x1, yaxis[3], x1, yaxis[3]+2)
            self.svg["lines"].append((x1, yaxis[3], x1, yaxis[3]+2))        
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))

    def DrawProfileSpectrum(self, dc, key):
        '''
        
        This function draws profile data.
        
        '''
        firstMass = self.spectrum.mass_ranges[key][0]
        lastMass = self.spectrum.mass_ranges[key][1]
        print "Masses"
        print firstMass
        print lastMass
        xaxis = self.spectrum.axco[key][0]
        yaxis = self.spectrum.axco[key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        self.indent = yaxis[0]
        max_int = self.GetMaxInt(firstMass, lastMass)
        cutoff = 0.75 * float(max_int)
        dc.SetTextForeground("BLACK")
        dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
        mr = self.spectrum.mass_ranges[key][1]-self.spectrum.mass_ranges[key][0]
        print mr
        px = width
        self.width = width
        labels = []
        scan_type = 'MS2'
        if self.spectrum.vendor in ['Thermo', 'mgf', 'ABI-MALDI']:
            filter = self.spectrum.filter
        elif self.spectrum.vendor == 'ABI':
            #try:
            #    filter = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]
            #except:
            #    filter = currentFile["filter_dict"][(currentFile["scanNum"])]
            filter = self.spectrum.filter
        elif self.spectrum.vendor == 'ABSciex':
            filter = self.spectrum.filter
        print filter
        if (self.spectrum.detector=='FT' > -1 or self.spectrum.detector=='TOF' > -1) and self.spectrum.filter.find("Full ms ") > -1:
            scan_type = 'MS1'
        print scan_type
        scan_data = self.spectrum.scan_data
        scan_data.sort(key = lambda t:t[0])

        if len(scan_data) > 1:
            points = []
            dc.SetPen(wx.Pen(wx.BLACK,1))
            print "building"
            for member in scan_data:
                if member[0]>firstMass and member[0]<lastMass:
                    x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                    points.append(wx.Point(x1, y1))
            print "drawing"
            dc.DrawLines(points)
            self.svg["pointLists"].append(points)

if __name__ == '__main__':
    ID_Dict = {}
    app = wx.App(False)
    if len(sys.argv) > 1:
        frame = SpecViewLitePanel(sys.argv[1], 1)
    else:
        import SpecObject
        a = SpecObject.SpecObject("Thermo", False, "FTMS", "MS2", [(400.0, 10000), (450.0, 20000)], '', '', 'FTMS + c NSI Full ms [300.0-2000.0]]', (300, 2000), [(300,2000)], 0,
                 '', '', '', 1, 1, '1')
        a.notes = ''
        a.axes = 1
        a.full_range = (300,2000)
        a.charge
        frame = SpecViewLitePanel(None, a)
    frame.Show()
    app.MainLoop()