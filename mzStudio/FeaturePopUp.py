__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx, os, sys, re

import  wx.lib.mixins.listctrl  as  listmix

import mz_workbench.mz_masses as mz_masses

from collections import defaultdict
import mzStudio as bb

class TestListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   #listmix.TextEditMixin,
                   listmix.ColumnSorterMixin):  #

    def __init__(self, parent, panel, ID, size = (475,160), pos=(0,50), style=0):
        self.parent = parent
        wx.ListCtrl.__init__(self, panel, ID, pos, size, style)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        #listmix.ColumnSorterMixin.__init__(self, 5)
        #self.Populate()
        #listmix.TextEditMixin.__init__(self)
        #self.editor.Disable()
        #self.editor.RemoveSelection()
        #self.editor.Destroy()
        #self.editor.SetCanFocus(False)
        self.InsertColumn(0, "Sequence")
        self.InsertColumn(1, "Variable Modifications")
        self.InsertColumn(2, "Scan")
        self.InsertColumn(3, "Gene Name")
        self.InsertColumn(4, "Score")
        self.SetColumnWidth(0, 120)
        self.SetColumnWidth(1, 150)
        self.SetColumnWidth(2, 50)
        self.SetColumnWidth(3, 80)
        self.SetColumnWidth(4, 70)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
        #self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.LeftD)
        self.bank_num = 0
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        #self.Select(0,0)
        #self.editor.Hide()
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 5)
        #self.Bind(wx.EVT_LIST_CO, self.LeftD)
    
    def GetListCtrl(self):
        return self
    
    def OnColClick(self, evt):
        print "COL CLICK"
        evt.Skip()
    
    def OnRightUp(self, evt):
        self.parent.memory_bank.Hide()

    def LeftD(self, evt):
        evt.Skip()
        #if self.editable:
        #    evt.Skip()

    def OnLeft(self, evt):
        evt.Skip()
        #if not self.editable:
            #for i in range(0, self.GetItemCount()):
                #self.Select(i, 0)
            #print evt.GetPosition()
            #print evt.GetEventObject()
            #print evt.GetButton()
            #print self.HitTest(evt.GetPosition())
            
            #self.Select(self.HitTest(evt.GetPosition())[0])
        #else:
            #evt.Skip(

    def GetListCtrl(self):
        return self

    def Populate(self, sequence, varmod, scan, geneName, peptide_score):
        # for normal, simple columns, you can add them like this:
        self.bank_num += 1
        index = self.InsertStringItem(sys.maxint, sequence)
        #index = self.InsertStringItem(0, seq)
        self.SetStringItem(index, 1, varmod)
        self.SetStringItem(index, 2, scan) # str(composition)
        self.SetStringItem(index, 3, geneName)
        self.SetStringItem(index, 4, peptide_score)
        #self.SetStringItem(index, 5, group)
        print self.bank_num
        self.SetItemData(index, self.bank_num)
        #self.itemDataMap[self.bank_num]=(token, title, self.convertToComp(token), float(mz_masses.calc_mass(mz_masses.res_dict[token], massType='mi')), float(mz_masses.calc_mass(mz_masses.res_dict[token], massType='av')), group)
        
        
        #if self.bank_num == 10:
        #    print "A"
        #self.GetItemCount()
        #self.GetItem(9,2).GetText()
        
    def SetStringItem(self, index, col, data):
        if col in range(6):
            wx.ListCtrl.SetStringItem(self, index, col, data)
        else:
            try:
                datalen = int(data)
            except:
                return
            wx.ListCtrl.SetStringItem(self, index, col, data)
            data = self.GetItem(index, col-3).GetText()
            wx.ListCtrl.SetStringItem(self, index, col-3, data[0:datalen])

class FeaturePopUp(wx.Frame):
    def __init__(self, parent, id, feature, psms, pos=(50,50), peaks=None):
        self.parent = parent
        self.peaks = peaks
        self.feature = feature # feature number
        self.psms = psms #[{AAATK		4512	HIST1H1B	73.12},...]
        wx.Frame.__init__(self, parent, -1, "Feature", pos=pos, 
                                 size =(480,220), style = wx.STAY_ON_TOP)
                                   #wx.SIMPLE_BORDER
                                 #| wx.FRAME_NO_TASKBAR
                                 #| wx.STAY_ON_TOP
                                 #)        
        #wx.Frame.__init__(self,parent,id, 'Mod Manager', size =(810,340), pos = (50,50), style=wx.STAY_ON_TOP|wx.CAPTION) #, style=wx.STAY_ON_TOP|wx.FRAME_EX_METAL|wx.FRAME_NO_TASKBAR
        self.panel = wx.Panel(self, size =(810,340))
        
        #self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING)
        self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING) 
         
        self.listb.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        #self.listb.editable=False
       
        self.XIC = wx.Button(self.panel, -1, "XIC", pos=(350, 15), size=(75,25))
        self.Bind(wx.EVT_BUTTON, self.OnXIC, self.XIC)
        #self.Load = wx.Button(self.panel, -1, "L", pos=(30,2), size=(25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnLoad, self.Load)
        #self.Delete = wx.Button(self.panel, -1, "D", pos=(60,2), size=(25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnDelete, self.Delete)

        self.actionChoice = wx.RadioBox(self.panel, -1, "Upon selection", (5,0), wx.DefaultSize, ['Go To Scan', 'bpc'], 2, wx.RA_SPECIFY_COLS)
        
        self.jump2ms2 = wx.ComboBox(self.panel, -1, "", (200,15), wx.DefaultSize, [], wx.CB_DROPDOWN)
        
        #self.NewEntry = wx.Button(self.panel, -1, "N", pos=(220,2), size=(25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnNew, self.NewEntry)        
        self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        #self.listb.Bind(wx.EVT_RIGHT_DOWN, self.OnRightUp)
        self.listb.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        
        for psm in psms:
            sequence = psm["Peptide Sequence"]
            varmod = psm["Variable Modifications"]
            if not varmod:
                varmod = ''
            score = str(psm["Peptide Score"])
            geneName = psm.get('GeneName', 'NA')
            scan = psm['Spectrum Description'].split(".")[1]
            self.listb.Populate(sequence, varmod, scan, geneName, score)
    
        self.Refresh()
        self.Update()
        self.Refresh()
        self.selected = None
        
    def OnXIC(self, evt):
        print "1"
        print "One"
        xic_mz = self.peaks[0][0]
        tolerance = 0.02
        toler = float(tolerance)/float(2.0)
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
        frm.mark_base.append({})
        
        frm.OnClick(None)
        frm.Destroy()        
        
        currentPage.Window.UpdateDrawing()
        currentPage.Refresh() 
        
                
    def OnNew(self, evt):
        self.listb.Populate('', '', '', '')
        
    def OnSelect(self, evt):
        print "EVENT SELECT"
        self.BuildList(self.groupSelection.GetValue())
    
    def OnMouse(self, event):
        print "Mouse ve"
        """implement dragging"""
        if not event.Dragging():
            self._dragPos = None
            return
        self.CaptureMouse()
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            displacement = self._dragPos - pos
            self.SetPosition( self.GetPosition() - displacement )        
        
    def OnColClick(self, evt):
        print "COLCLICK"
        for x in range(0, self.listb.ItemCount):
            self.listb.SetItemBackgroundColour(x, "white")
            if x % 2 == 1:
                #print "Set blue..."
                self.listb.GetItemPosition(x)
          
                self.listb.SetItemBackgroundColour(x, "white")         
        evt.Skip()
        
    def OnRightUp(self, evt):
        self.Destroy()
        
    def OnAct(self, event):
        pass
        
    def OnSelected(self, event):
        item = event.GetItem()
        self.selected=item.GetId() #-------Id is the index within the list.  Keep track of this for other commands
        data = item.GetText()  #.split('-')
        print "Selected."
        scan = int(self.listb.GetItem(self.selected, 2).GetText()) # Row, col
        currentPage = self.parent.parent.parent.ctrl.GetPage(self.parent.parent.parent.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]
        currentFile['scanNum']=scan
        
        currentFile["spectrum_style"] = "single scan"
        currentPage.msdb.set_scan(currentFile["scanNum"], currentPage.msdb.active_file)
        if currentFile['vendor']=='Thermo':
            currentPage.msdb.build_current_ID(currentPage.msdb.Display_ID[currentPage.msdb.active_file], currentFile["scanNum"])
        if currentFile['vendor']=='ABI':
            currentPage.msdb.build_current_ID(currentPage.msdb.Display_ID[currentPage.msdb.active_file], (currentFile["scanNum"], currentFile['experiment']), 'ABI')        
        self.parent.Window.UpdateDrawing()
        self.parent.Refresh()        
        #self.actionChoice.GetSelection()
        
        #nterm = data[0]
        #seq = data[1]
        #cterm = data[2]
        #if nterm == "H":
            #nterm = "None"
        #if cterm == "OH":
            #cterm = "None"
        #self.parent.FindWindowByName("sequence").SetValue(seq)
        #self.parent.FindWindowByName("nTerm").SetValue(nterm)
        #self.parent.FindWindowByName("cTerm").SetValue(cterm)
        #self.parent.OnCalculate(None)        
        event.Skip()
        
    def RadioBoxData(self):
        return (("Masses", ['monoisotopic', 'average'], 'masses', (10, 190), wx.DefaultSize),) #, 'average'         
        
        
if __name__ == '__main__':
    app = wx.App(False)
    a = FeaturePopUp(None, -1, 5761, [{"Peptide Sequence":"AAAAAATR", "Variable Modifications": "None", "GeneName":"HIST1H1B", "Peptide Score":38.1, "Spectrum Description": "1523"}])
    a.Show()
    app.MainLoop()