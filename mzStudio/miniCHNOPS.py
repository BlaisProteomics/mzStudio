__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx
import re
import mz_workbench.mz_masses as mz_masses

class miniCHNOPS(wx.Panel):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Panel.__init__(self,parent,id=id, name='miniCHNOPS', size=(355, 20), pos=(700,5))
        self.CHNOPSdata = wx.TextCtrl(self, -1, '', size = (150,20), pos=(0, 0))
        self.result = wx.TextCtrl(self, -1, '', size = (150,20), pos=(230, 0))
        self.calcButton = wx.Button(self, -1, "Calc", pos = (170, 0), size=(50,20))
        self.Bind(wx.EVT_BUTTON, self.OnClickCalc, self.calcButton)
        #self.pa = re.compile('([A-Z]+[a-z]*)([0-9]+)')
        self.pa = re.compile('([A-Z]+[a-z]*)[ ]*\(*([0-9]+)\)*')
        
    def OnClickCalc(self, event):
        self.result.SetValue(str(mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in self.pa.findall(self.CHNOPSdata.GetValue())]))))
        
class toolbarCHNOPS(wx.Panel):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Panel.__init__(self,parent,id=id, name='miniCHNOPS')
        self.CHNOPSdata = wx.TextCtrl(self, -1, '', size = (150,20), pos=(0, 0))
        self.result = wx.TextCtrl(self, -1, '', size = (150,20), pos=(230, 0))
        self.calcButton = wx.Button(self, -1, "Calc", pos = (170, 0), size=(50,20))
        self.Bind(wx.EVT_BUTTON, self.OnClickCalc, self.calcButton)
        #self.pa = re.compile('([A-Z]+[a-z]*)([0-9]+)')
        self.pa = re.compile('([A-Z]+[a-z]*)[ ]*\(*([0-9]+)\)*')
        
    def OnClickCalc(self, event):
        self.result.SetValue(str(mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in self.pa.findall(self.CHNOPSdata.GetValue())]))))
        

class windowCHNOPS(wx.Panel):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Panel.__init__(self, parent, id=id, size=(300,50), name='miniCHNOPS')
        self.CHNOPSdata = wx.TextCtrl(self, -1, '', size = (150,20), pos=(0, 0))
        self.result = wx.TextCtrl(self, -1, '', size = (150,20), pos=(230, 0))
        self.calcButton = wx.Button(self, -1, "Calc", pos = (170, 0), size=(50,20))
        self.Bind(wx.EVT_BUTTON, self.OnClickCalc, self.calcButton)
        #self.pa = re.compile('([A-Z]+[a-z]*)([0-9]+)')
        self.pa = re.compile('([A-Z]+[a-z]*)[ ]*\(*([0-9]+)\)*')
        
    def OnClickCalc(self, event):
        self.result.SetValue(str(mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in self.pa.findall(self.CHNOPSdata.GetValue())]))))
        
def create_CHNOPS_in_toolbar(tb):
    pass