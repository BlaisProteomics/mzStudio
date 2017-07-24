#XIC palette

import wx
import mzStudio as bb

class XICPalette(wx.Frame):
    def __init__(self, parent, currentFile, key, id=-1):
        wx.Frame.__init__(self,parent,id, 'XIC Palette', pos=(0,25),size =(50,(len(currentFile["xic_params"][key]*40)+10)))
        #self.SetSize((10,(len(currentFile["xic_params"][key]*40)+10)))
        self.SetBackgroundColour("White")
        #panel = wx.Panel(self)
        self.currentFile = currentFile
        self.parent = parent
        self.key = key
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        size = self.ClientSize
        self._buffer = wx.EmptyBitmap(*size)      
        self.hit_xtract = []
        self.hit_active = []
        self.hit_view = []
        
    def OnLeftUp(self, evt):
        pos = evt.GetPositionTuple()
        found, trace = self.HitTestXICBox(pos,10)
        if found:
            self.currentFile['active_xic'][self.key] = trace
            if not self.currentFile['xic_view'][self.key][trace]:
                self.currentFile['xic_view'][self.key][trace] = True
            self.parent.Window.UpdateDrawing()
            self.parent.Refresh()  
            self.Refresh()
                    
        found, trace = self.HitTestXICBox(pos,25)
        if found:
            if self.currentFile['active_xic'][self.key] != trace:
                self.currentFile['xic_view'][self.key][trace] = not self.currentFile['xic_view'][self.key][trace]
            self.parent.Window.UpdateDrawing()
            self.parent.Refresh()  
            self.Refresh()
            
        found, trace = self.HitTestXICBox(pos,40)
        if found:
            self.frm = bb.xicFrame(self.parent, self.currentFile, self.parent.msdb.active_file)
            winmax = 0
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0):
                    curWin = int(self.frm.grid.GetCellValue(k, 0))
                    if curWin > winmax:
                        winmax = curWin
            winmax += 1
            #print winmax
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0) == str(self.key):
                    self.frm.grid.SetCellValue(k + trace, 0, str(winmax))
                    self.frm.OnClick(None)
                    self.frm.Destroy()
                    break
            self.parent.Window.UpdateDrawing()
            self.parent.Refresh()         
            self.Refresh()
            if len(self.currentFile["xic_params"][self.key]) < 4:
                self.Destroy()
        
    def HitTestXICBox(self, pos, offset):
        hitx = pos[0]
        hity = pos[1]
        found = False
        trace = None
        traces = len(self.currentFile['xic_params'][self.key]) #TRACES DISPLAYED in each window
        for j in range(0, traces):
            currentx1 = 50 - offset
            currentx2 = currentx1 + 10
            currenty1 = 10 + (30 * j)
            currenty2 = currenty1 + 10
            if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                found = True
                trace = j
                break
        return found, trace               
        
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
            dc.SetPen(wx.Pen(wx.YELLOW,1)) 
            col = wx.YELLOW    
        elif xic == 5:
            dc.SetPen(wx.Pen(wx.CYAN,1)) 
            col = wx.CYAN
        elif xic ==6:
            dc.SetPen(wx.Pen(wx.Colour(255, 128, 128,255)))
            col = wx.Colour(255, 128, 128,255)
        elif xic ==7:
            dc.SetPen(wx.Pen(wx.Colour(128, 64, 64,255)))
            col = wx.Colour(128, 64, 64,255)    
        elif xic ==8:
            dc.SetPen(wx.Pen(wx.Colour(128, 0, 0,255)))
            col = wx.Colour(128, 0, 0,255) 
        elif xic ==9:
            dc.SetPen(wx.Pen(wx.Colour(64, 0, 0,255)))
            col = wx.Colour(64, 0, 0,255)   
        elif xic ==10:
            dc.SetPen(wx.Pen(wx.Colour(255, 128, 64,255)))
            col = wx.Colour(255, 128, 64, 255)   
        elif xic ==11:
            dc.SetPen(wx.Pen(wx.Colour(0, 128, 128,255)))
            col = wx.Colour(0, 128, 128, 255) 
        elif xic ==12:
            dc.SetPen(wx.Pen(wx.Colour(0, 64, 128,255)))
            col = wx.Colour(0, 64, 128, 255)  
        elif xic ==13:
            dc.SetPen(wx.Pen(wx.Colour(0, 64, 128,255)))
            col = wx.Colour(0, 64, 128, 255) 
        elif xic ==14:
            dc.SetPen(wx.Pen(wx.Colour(128, 0, 64,255)))
            col = wx.Colour(128, 0, 64, 255)            
        #(255, 128, 128), (128, 64, 64), (128, 0, 0), (64, 0, 0), (255, 128, 64), 
        else:
            if xic > 14 and xic <25:
                dc.SetPen(wx.Pen(wx.Colour(xic*10,255-(xic*10),255,0)))
                col = wx.Colour(xic*5,255,255,0)
            elif xic >24 and xic <100:
                dc.SetPen(wx.Pen(wx.Colour(255-(xic-25)*5,(xic-25)*5,255-(xic-25)*5,0)))
                col = wx.Colour(255,xic*5,255,0)       
        return col    
        
    def OnPaint(self, event=None):
        self.SetSize((50,(len(self.currentFile["xic_params"][self.key]*40)+10)))
        currentFile = self.currentFile
        key = self.key
        dc = wx.PaintDC(self)
        dc.Clear()
        yaxis = (0,0)
        xaxis = (50,0)
        active_xic = currentFile['active_xic'][self.key]
        xics = len(currentFile["xic_params"][key])        
        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
        self.hit_coord = []
        for xic in range(0, len(currentFile["xic_params"][key])):         
            col = self.get_xic_color(xic, dc)
            dc.SetTextForeground(col)
            dc.SetFont(wx.Font(6, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
            ex = dc.GetTextExtent(str(currentFile['xic_mass_ranges'][key][xic][0]))
            dc.DrawText(str(currentFile['xic_mass_ranges'][key][xic][0])+'-', xaxis[0]-1-ex[0], (yaxis[1]+18)+ (30*xic))
            ex = dc.GetTextExtent(str(currentFile['xic_mass_ranges'][key][xic][1]))
            dc.DrawText(str(currentFile['xic_mass_ranges'][key][xic][1]), xaxis[0]-1-ex[0], (yaxis[1]+28)+ (30*xic))
            dc.SetTextForeground("BLACK")
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
            dc.SetBrush(wx.Brush(col, wx.TRANSPARENT))
            dc.DrawRectangle(xaxis[0]-25, (yaxis[1]+10)+ (30*xic),10,10) 
            self.hit_view.append((xaxis[0]-25, (yaxis[1]+10)+ (30*xic)))
            dc.DrawRectangle(xaxis[0]-40, (yaxis[1]+10)+ (30*xic),10,10)
            self.hit_xtract.append((xaxis[0]-40, (yaxis[1]+10)+ (30*xic)))
            dc.DrawText('>', xaxis[0]-40+2, (yaxis[1]+10)+ (30*xic)-3)
            dc.DrawText('+' if currentFile['xic_view'][key][xic] else '-', xaxis[0]-25+2, (yaxis[1]+10)+ (30*xic)-3)
            dc.SetBrush(wx.Brush(col, wx.SOLID))
            dc.DrawRectangle(xaxis[0]-10, (yaxis[1]+10)+ (30*xic),10,10)  
            self.hit_active.append((xaxis[0]-10, (yaxis[1]+10)+ (30*xic)))
            
            
            
#----------------------------------------SIMULATES A DATAFILE FOR TESTING PALETTE FUNCTION
class testFile():
    def __init__(self):
        current={}
        current["xic_params"] = [[(300, 2000, u'Full ms ')], [(571.3, 572.3, u'Full ms '), (495.3, 496.3, u'Full ms '), (644, 646, u'Full ms ')], [(913.96900-.02, 913.96900+0.02, u'TVAGGAWTYNTTSAVTVK +2')]]
        current["xic_mass_ranges"] = [[(300, 2000)], [(571.3, 572.3),(495.3, 496.3), (644, 646)], [(913.96900-.02, 913.96900+0.02)]]
        current["xic_scale"] = [[-1],[-1,'s0','s0'], [-1]]
        current["xic_type"] = [['x'], ['x', 'x', 'x'], ['p']]
        current["xic_mass"] = [[None], [None, None, None], [913.96900]]  
        current["xic_charge"] = [[None], [None, None, None], [2]]
        current["xic_sequence"] = [[None], [None, None, None], ["TVAGGAWTYNTTSAVTVK"]]
        current['xic_scan'] = [[None], [None, None, None], [8353]]
        current["active_xic"] = [0,1,0]
        current["xic_view"] = [[1],[1,1,1],[1]]
        self.files = current

if __name__ == '__main__':
    app = wx.PySimpleApp()
    test = testFile()
    frame = XICPalette(parent=None, currentFile=test.files, key=1)
    frame.Show()
    app.MainLoop()