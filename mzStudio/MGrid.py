#Mark grid

import wx
import wx.grid as grid
import wx.lib.mixins.gridlabelrenderer as glr
import mzStudio as bb

class MGrid(grid.Grid, glr.GridWithLabelRenderersMixin):
    def __init__(self, parent, *args, **kw):
        grid.Grid.__init__(self, parent.panel, id=-1, size=(360,200), pos=(0,0))
        glr.GridWithLabelRenderersMixin.__init__(self)
        self.CreateGrid(15,2)  #ROWS, COLUMNS
        for i, setting in enumerate([("Scan to mark", 100), ("Annotation", 150)]):
            self.SetColLabelValue(i, setting[0])
            self.SetColSize(i, setting[1])
        
class MFrame(wx.Frame):
    '''
    
    This grid allows users to enter specific scans to mark in an XIC.
    Mouse over then reveals annotation.
    
    
    '''
    def __init__(self, parent=None, currentMarks=None, currentXIC=None, index=None, dataFile=None):
        #currentMarks = {46.303022:["PEPTIDE", 9188], ...}
        self.currentMarks = currentMarks
        self.currentXIC = currentXIC
        self.parent = parent
        self.index = index
        self.m = dataFile
        wx.Frame.__init__(self, parent, -1, "XIC Marks", size=(370,260))
        self.panel = wx.Panel(self, -1)
        
        self.btn = wx.Button(self.panel, -1, "OK", size=(25,25), pos = (0, 210))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.grid = MGrid(self)
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        
        if currentMarks:
            for counter, m in enumerate(currentMarks.keys()):
                self.grid.SetCellValue(counter, 0, str(m))
                self.grid.SetCellValue(counter, 1, str(currentMarks[m].label))
                #self.grid.SetCellValue(counter, 2, str(currentMarks[m][1]))   
            
    #def get_closest_time(self, time, xic):
    #    times_and_deltas = [(x[0], abs(time-x[0])) for x in xic]
    #    times_and_deltas.sort(key=lambda t: t[1])
    #    return times_and_deltas[0][0]
            
    def OnClick(self, event): 
        self.Hide()
        updated_marks = {}
        for i in range(0, 15):
            if self.grid.GetCellValue(i, 0) != '':
                scan = int(self.grid.GetCellValue(i, 0))
                updated_marks[scan] = bb.XICLabel(self.m.timeForScan(scan), scan, self.grid.GetCellValue(i, 1), self.currentXIC)
        self.parent.mark_base[self.index] = updated_marks
        self.parent.Show()
        self.Destroy()
        
if __name__ == '__main__':
    app = wx.App(False)
    g = MFrame()
    g.Show()
    app.MainLoop()
    