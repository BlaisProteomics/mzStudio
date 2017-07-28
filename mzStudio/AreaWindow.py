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


#def calc_peak_area(data, multiplier=60.0):
    ## Get Gaussian Fit Peak Area
    #params = (numpy.mean([y for (x,y) in data]),
              #numpy.median([x for (x,y) in data]),
              #0.3, 0)
    #(f,p,R2) = fit.fit_data(data=data, parameters=params, function=fit.gauss)

    ## Use integral of gaussian
    #a = float(p[0])
    #c = float(p[2])
    #return abs(a * c * multiplier * math.sqrt(2*math.pi))
    

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
        #if not module_works:
            #wx.MessageBox('XIC quantification window is disabled in this version of mzStudio.  Check https://github.com/blaisproteomics/mzstudio for a new version soon.')
            #raise NotImplementedError
        
        print xic
        wx.Frame.__init__(self,parent,id, 'Area Window', size =(800,500))
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
            
        #if method=='SUM':
            #if len(xic) > 2:
                ##(f, p, R2) = fit.fit_data(data=xic, function=fit.gauss)
                ##p1 = pyt.plot(x, list(f), color = 'r', linewidth = 2)
                #pyt.plot(x, y, color = 'b')        
                #area = calc_peak_area(xic)
                #pyt.text(min(x), max(y), "Area %.1e" % area)#, {'color':'k','fontsize':14}
                #tempfig = os.path.join(os.path.dirname(__file__), 'temp.png')
                #pyt.savefig(tempfig)
                #img1 = wx.Image(tempfig, wx.BITMAP_TYPE_ANY)
                #w = 500
                #h = 470
                #img2 = img1.Scale(w,h)
                #self.bm1.SetBitmap(wx.BitmapFromImage(img2))        
                #pyt.cla()
                #print area
                #self.area = "%.1e" % area
            #else:
                #print "No Data Detected"
        #else:
            #if len(xic) > 2:
                #try:
                    #(f, p, R2) = fit.fit_data(data=xic, function=fit.gauss)
                #except:
                    #wx.MessageBox("Error calling fit.\nIs scipy installed?", 'mzStudio')
                    #return
                #p1 = pyt.plot(x, list(f), color = 'r', linewidth = 2)
                #pyt.plot(x, y, color = 'b')        
                #area = calc_peak_area(xic)
                #pyt.text(min(x), max(y), "Area %.1e" % area)#, {'color':'k','fontsize':14}
                #tempfig = os.path.join(os.path.dirname(__file__), 'temp.png')
                #pyt.savefig(tempfig)
                #img1 = wx.Image(tempfig, wx.BITMAP_TYPE_ANY)
                #w = 500
                #h = 470
                #img2 = img1.Scale(w,h)
                #self.bm1.SetBitmap(wx.BitmapFromImage(img2))        
                #pyt.cla()
                #print area
                #self.area = "%.1e" % area
            #else:
                #print "No Data Detected" 
        
        plotter = plot.PlotCanvas(self.panel)
        plotter.SetInitialSize(size=(800, 500))
        line = plot.PolyLine(xic, colour='black', width=1)
        
            
        if method=='SUM':
            if len(xic) > 2:
                area = calc_peak_area(xic)
                print area
                self.area = "%.1e" % area                
                #(f, p, R2) = fit.fit_data(data=xic, function=fit.gauss)
                #p1 = pyt.plot(x, list(f), color = 'r', linewidth = 2)
                
                
                # enable the zoom feature (drag a box around area of interest)
                #plotter.SetEnableZoom(True)
                
                # list of (x,y) data point tuples
                #data = [(1,2), (2,3), (3,5), (4,6), (5,8), (6,8), (12,10), (13,4)]
                # draw points as a line
                #nxic = [(round(x[0],1), x[1]) for x in xic]
                
                # also draw markers, default colour is black and size is 2
                # other shapes 'circle', 'cross', 'square', 'dot', 'plus'
                #marker = plot.PolyMarker(xic, marker='triangle')
                # set up text, axis and draw
                gc = plot.PlotGraphics([line], 'Area Window: ' + str(self.area), 'Time (min)', 'Intensity')
                plotter.Draw(gc)  #xAxis=(0,15), yAxis=(0,15)   
                
                             
                
                #, xAxis=(round(x[0],1), round(x[len(x)-1], 1))
                #pyt.plot(x, y, color = 'b')        
                
                #pyt.text(min(x), max(y), "Area %.1e" % area)#, {'color':'k','fontsize':14}
                #tempfig = os.path.join(os.path.dirname(__file__), 'temp.png')
                #pyt.savefig(tempfig)
                #img1 = wx.Image(tempfig, wx.BITMAP_TYPE_ANY)
                #w = 500
                #h = 470
                #img2 = img1.Scale(w,h)
                #self.bm1.SetBitmap(wx.BitmapFromImage(img2))        
                #pyt.cla()
                
            else:
                print "No Data Detected"
        else:
            if len(xic) > 2:
                #try:
                (f, p, R2) = fit.fit_data(data=xic, function=fit.gauss)
                #except:
                #    wx.MessageBox("Error calling fit.\nIs scipy installed?", 'mzStudio')
                #    return
                
                area = calc_peak_area_guassian(xic)
                
                print area
                self.area = "%.1e" % area               
                
                gauss_line = plot.PolyLine(zip(x, list(f)), colour='red', width=1)
                gc = plot.PlotGraphics([line, gauss_line], 'Area Window: ' + str(self.area), 'Time (min)', 'Intensity')
                plotter.Draw(gc)
                
                #p1 = pyt.plot(x, list(f), color = 'r', linewidth = 2)
                #pyt.plot(x, y, color = 'b')        
                
                
                
                #pyt.text(min(x), max(y), "Area %.1e" % area)#, {'color':'k','fontsize':14}
                #tempfig = os.path.join(os.path.dirname(__file__), 'temp.png')
                #pyt.savefig(tempfig)
                #img1 = wx.Image(tempfig, wx.BITMAP_TYPE_ANY)
                #w = 500
                #h = 470
                #img2 = img1.Scale(w,h)
                #self.bm1.SetBitmap(wx.BitmapFromImage(img2))        
                #pyt.cla()
                
                
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
    a = AreaWindow(None, -1, xic, "GUASSIAN")
    a.Show()
    app.MainLoop()
    
    
