__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx
import mz_workbench.mz_core as mz_core
from collections import defaultdict
import re

def derive_IDd_Ions(currentFile):
    pa = re.compile('([yb])([0-9]+)')
    IDd_Ions = defaultdict(list)
    key = None
    if currentFile['vendor']=='Thermo':
        key = currentFile["scanNum"]
    elif currentFile['vendor']=='ABI':
        key = (currentFile['scanNum'], currentFile['experiment'])
    if currentFile["SearchType"]=="Mascot":
        seq = currentFile["ID_Dict"][key]["Peptide Sequence"]
        fixedmod = currentFile["fixedmod"]
        varmod = currentFile["ID_Dict"][key]["Variable Modifications"]
    print currentFile["label_dict"].values()
    for member in currentFile["label_dict"].values():
        for sub_member in member.split(", "):
            cg = 1
            id = pa.match(sub_member)
            if sub_member.find("+") > -1:
                cg = int(sub_member[-2])
            if sub_member.find("y") > -1:
                IDd_Ions["y" + "+".join(['' for i in range(0,cg+1)])].append(int(id.groups()[1]))
            if sub_member.find("b") > -1:
                IDd_Ions["b" + "+".join(['' for i in range(0,cg+1)])].append(int(id.groups()[1]))
    return IDd_Ions
            

class CoveragePanel(wx.Frame):

    def __init__(self, parent, sequence, fixedmod, varmod, IDd_Ions, SHOWMASSES = True, DRAWLINES = True):
        '''
        
        EXAMPLE USE:
        
        frame = CoveragePanel(None, "DRVYIHPCFHLDRVYIH", "Carbamidomethyl (C)", "Y4: Phospho", {"y+":[1,2,3], "b+":[5,6,7], "b++":[5,6,7], "y++":[1,2,3,5,6,7]})
        
        '''
        wx.Frame.__init__(self, parent , -1, "Coverage", size=(800,350))
        self.Panel = wx.Panel(self, -1)
        self.Panel.SetBackgroundColour(wx.WHITE)
        self.svg = defaultdict(list)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.sequence = sequence
        self.fixedmod = fixedmod
        self.varmod = varmod
        self.IDd_Ions = IDd_Ions
        self.SHOWMASSES = SHOWMASSES
        self.DRAWLINES = DRAWLINES
        self.createMenuBar()
    
    def OnSaveImage(self,event):
        pass
    
    def get_single_file(self, caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
        dlg = wx.FileDialog(None, caption, pos = (2,2), wildcard = wx_wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath()
            dir = dlg.GetDirectory()
            #print filename
            #print dir
        dlg.Destroy()
        return filename, dir    
    
    def OnSaveSVG(self, event):
        svgfile, dir = self.get_single_file("Select image file...", "SVG files (*.svg)|*.svg")
        #busy = PBI.PyBusyInfo("Saving SVG, please wait...", parent=None, title="Processing...")
        #wx.Yield()
        self.svgDC = wx.SVGFileDC(svgfile)
        print self.svg
        for line in self.svg["lines"]:
            if len(line)==4:
                self.svgDC.DrawLine(*line)
            else:
                self.svgDC.SetPen(line[4])
                self.svgDC.DrawLine(line[0], line[1], line[2], line[3])
        for text in self.svg["text"]:
            if len(text)==4:
                self.svgDC.DrawRotatedText(*text)
            else:
                self.svgDC.SetTextForeground(text[4])
                self.svgDC.SetFont(text[5])
                self.svgDC.DrawRotatedText(text[0],text[1],text[2],text[3])  
        self.svgDC.Destroy()
        #del busy
    
    def menuData(self):
        return [("Image", (
            ("Save &PNG", "Save PNG", self.OnSaveImage),
            ("Save &SVG", "Save SVG", self.OnSaveSVG)))              
        ]        
    
    def createMenuItem(self, menu, label, status, handler, kind = wx.ITEM_NORMAL):
        if not label:
            menu.AppendSeparator()
            return
        menuItem = menu.Append(-1, label, status, kind)
        self.Bind(wx.EVT_MENU, handler, menuItem)

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachItem in menuData:
            if len(eachItem) == 2:
                label = eachItem[0]
                subMenu = self.createMenu(eachItem[1])
                menu.AppendMenu(wx.NewId(), label, subMenu)
            else:
                self.createMenuItem(menu, *eachItem)
        return menu
    
    
    def OnPaint(self,e):
        del self.svg
        self.svg = defaultdict(list)        
        dc = wx.PaintDC(self.Panel)
        dc.SetPen(wx.Pen(wx.BLACK,2))
        dc.SetTextForeground("BLACK")
        dc.SetFont(wx.Font(28, wx.ROMAN, wx.NORMAL, wx.NORMAL, False, faceName="Consolas"))        
        spacing = dc.GetTextExtent("A ")[0]
        v_spacing = dc.GetTextExtent("A")[1]
        dc.DrawText(' '.join(self.sequence),20,55)
        self.svg["text"].append((' '.join(self.sequence),20,55, 0.00001, wx.BLACK, wx.Font(36, wx.ROMAN, wx.NORMAL, wx.NORMAL, False, faceName="Consolas")))
        mz, b_series, y_series = mz_core.calc_pep_mass_from_residues(self.sequence, 1, self.varmod, self.fixedmod)
        #dc.DrawLine(50,60,190,60)
        dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False, faceName="Consolas"))
        
        for i, member in enumerate(b_series):
            if self.SHOWMASSES:
                dc.SetPen(wx.Pen(wx.BLACK,2))
                b_len = dc.GetTextExtent(str(round(b_series[i], 1)))[0]
                dc.DrawRotatedText(str(round(b_series[i], 1)), 10 + (spacing*i), 45-b_len, -45)
                self.svg["text"].append((str(round(b_series[i], 1)), 10 + (spacing*i), 45-b_len, -45, wx.BLACK, wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False, faceName="Consolas")))
                dc.DrawLine(45+(spacing*i), 60, 45+(spacing*i), 50)
                self.svg["lines"].append((45+(spacing*i), 60, 45+(spacing*i), 50, wx.Pen(wx.BLACK,2)))
                dc.DrawLine(45+(spacing*i), 50, 45+(spacing*i)-5, 45)
                self.svg["lines"].append((45+(spacing*i), 50, 45+(spacing*i)-5, 45))
                dc.DrawLine(20+(spacing*i), 60 + v_spacing, 20+(spacing*i), 50 + v_spacing)
                self.svg["lines"].append((20+(spacing*i), 60 + v_spacing, 20+(spacing*i), 50 + v_spacing))
                dc.DrawLine(20+(spacing*i), 60 + v_spacing, 20+(spacing*i)+5, 65 + v_spacing)
                self.svg["lines"].append((20+(spacing*i), 60 + v_spacing, 20+(spacing*i)+5, 65 + v_spacing))
                dc.DrawRotatedText(str(round(y_series[len(y_series)-i-1], 1)), 10+(spacing*i)+25, 60 + v_spacing, -45)
                self.svg["text"].append((str(round(y_series[len(y_series)-i-1], 1)), 10+(spacing*i)+25, 60 + v_spacing, -45))
            if self.DRAWLINES:
                if "b+" in self.IDd_Ions.keys():
                    dc.SetPen(wx.Pen(wx.BLUE,6))
                    if i in self.IDd_Ions["b+"]:
                        dc.DrawLine(35+(spacing*i), 60, 25+(spacing*i), 60)
                        self.svg["lines"].append((35+(spacing*i), 60, 25+(spacing*i), 60, wx.Pen(wx.BLUE,6)))
                if "b++" in self.IDd_Ions.keys():
                    dc.SetPen(wx.Pen("medium blue",6))
                    if i in self.IDd_Ions["b++"]:
                        dc.DrawLine(35+(spacing*i), 50, 25+(spacing*i), 50)
                        self.svg["lines"].append((35+(spacing*i), 50, 25+(spacing*i), 50, wx.Pen("light blue",6)))
                if "y+" in self.IDd_Ions.keys():
                    dc.SetPen(wx.Pen(wx.RED,6))
                    if len(y_series) - i - 1 in self.IDd_Ions["y+"]:
                        dc.DrawLine(35+(spacing*i), 50 + v_spacing, 25+(spacing*i), 50 + v_spacing)
                        self.svg["lines"].append((35+(spacing*i), 50 + v_spacing, 25+(spacing*i), 50 + v_spacing, wx.Pen(wx.RED,6)))
                if "y++" in self.IDd_Ions.keys():
                    dc.SetPen(wx.Pen("pink",6))
                    if len(y_series) - i - 1 in self.IDd_Ions["y++"]:
                        dc.DrawLine(35+(spacing*i), 60 + v_spacing, 25+(spacing*i), 60 + v_spacing)     
                        self.svg["lines"].append((35+(spacing*i), 60 + v_spacing, 25+(spacing*i), 60 + v_spacing, wx.Pen("pink",6)))
        #print self.svg

if __name__ == '__main__':
    app = wx.App(False)
    frame = CoveragePanel(None, "DRVYIHPCFHLDRVYIH", "Carbamidomethyl (C)", "Y4: Phospho", {"y+":[1,2,3], "b+":[5,6,7], "b++":[5,6,7], "y++":[1,2,3,5,6,7]})
    #frame = CoveragePanel(None, "DRVYIHPCFHLDRVYIH", "Carbamidomethyl (C)", "Y4: Phospho", derive_IDd_Ions({1:"y4",2:"y3",3:"y5",4:"b3",5:"b4",6:"y4 2+"}))
    frame.Show()
    app.MainLoop()