__author__ = 'Scott Ficarro'
__version__ = '1.0'

#import fit
# Area window
try:
    import fit
    module_works = True
except ImportError:
    module_works = False
import wx
#import matplotlib
#matplotlib.use('WXAgg', force=True)
#import pylab
#import matplotlib.pyplot as pyt
import math
import numpy
import os

import plot_patched as plot

#import wx.lib.plot as plot
    

def get_bars(data, multiplier=1):
    bars = []
    for i in range(0, len(data)-1):
        mz1, int1 = data[i]
        mz2, int2 = data[i+1]
        width = mz2 - mz1
        height = (int1 + int2) / 2
        #total += width * height
        center = float(width)/float(2.0)
        bars.append([(mz1, 0), (mz1, int1), (mz2, int2), (mz2,0)])
    return bars

def calc_peak_area(data, multiplier = 1):
    total = 0
    for i in range(0, len(data)-1):
        mz1, int1 = data[i]
        mz2, int2 = data[i+1]
        width = mz2 - mz1
        height = (int1 + int2) / 2
        total += width * height
    return total

def calc_peak_area_guassian(data, multiplier=60.0):
    # Get Gaussian Fit Peak Area
    params = (numpy.mean([y for (x,y) in data]),
              numpy.median([x for (x,y) in data]),
              0.3, 0)
    (f,p,R2) = fit.fit_data(data=data, parameters=params, function=fit.gauss)

    # Use integral of gaussian
    a = float(p[0])
    c = float(p[2])
    return abs(a * c * multiplier * math.sqrt(2*math.pi))

        

class AreaWindow(wx.Frame):
    def __init__(self, parent, id, xic, method="SUM"):
        
        wx.Frame.__init__(self,parent,id, 'Area Window', size =(800,550))
        panel = wx.Panel(self)
        self.panel = panel
        img = wx.EmptyImage(400,400)
        self.bm1 = wx.StaticBitmap(panel, -1, wx.BitmapFromImage(img), pos=(0, 0))
        self.panel.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        x = []
        y = []

        if len(xic) < 4:
            print "Insufficiently long XIC window (%s timepoints)." % len(xic)
            self.valid = False
            return
        else:
            self.valid = True
        
        for entry in xic:
            x.append(entry[0])
            y.append(entry[1])
            
        plotter = plot.PlotCanvas(self.panel)
        plotter.SetInitialSize(size=(800, 500))
        line = plot.PolyLine(xic, colour='black', width=1)
        
            
        if method=='SUM':
            if len(xic) > 2:
                area = calc_peak_area(xic)
                bars = get_bars(xic)
                bar_plots = []
                for member in bars:
                    bar_plots.append(plot.PolyLine(member, colour='red', width=1))
                #bar_plots = [line] + [plot.PolyLine(x, colour='black', width=1) for x in bars]
                    
                print area
                self.area = "%.1e" % area                
               
                gc = plot.PlotGraphics([line] + bar_plots, 'Area Window: ' + str(self.area), 'Time (min)', 'Intensity')
                
                plotter.Draw(gc)  #xAxis=(0,15), yAxis=(0,15)   
                
            else:
                print "No Data Detected"
        else:
            if len(xic) > 2:
                try:
                    (f, p, R2) = fit.fit_data(data=xic, function=fit.gauss)
                except:
                    self.valid = False
                    wx.MessageBox("Error calling fit.\nIs scipy installed?", 'mzStudio')
                    return
                
                area = calc_peak_area_guassian(xic)
                
                print area
                self.area = "%.1e" % area               
                
                gauss_line = plot.PolyLine(zip(x, list(f)), colour='red', width=1)
                gc = plot.PlotGraphics([line, gauss_line], 'Area Window: ' + str(self.area), 'Time (min)', 'Intensity')
                plotter.Draw(gc)
            
            else:
                print "No Data Detected" 

    def OnContextMenu(self, evt):
        if not hasattr(self, "PopUpID1"):
            self.PopUpID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnPopUp1, id = self.PopUpID1)
        menu = wx.Menu()
        item = wx.MenuItem(menu, self.PopUpID1, "Copy to Clipboard")
        menu.AppendItem(item)
        self.panel.PopupMenu(menu)
        menu.Destroy()
        
    def OnPopUp1(self, evt):
        data = wx.TextDataObject()
        data.SetText(str(self.area))
        #if wx.Clipboard.Open():
        if wx.TheClipboard.Open():
            yo = wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
    
    
if __name__ == '__main__':
    xic = [(22.765981666666669, 43326.0546875), (22.816895000000002, 148095.123046875), (22.867786666666667, 116020.9453125), (22.918616666666665, 61602.265625), (22.969233333333335, 473938.3125), (23.019886666666668, 3233170.5), (23.070638333333335, 1518784.875), (23.121554999999997, 20428157.5390625), (23.172296666666668, 77530489.375), (23.222820000000002, 33785018.3203125), (23.273486666666667, 7279730.365234375), (23.324263333333334, 2133839.75), (23.375080000000001, 1033855.1875)]
    app = wx.App(False)
    a = AreaWindow(None, -1, xic, "SUM")
    a.Show()
    app.MainLoop()
    
    
