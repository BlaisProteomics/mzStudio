__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx.lib.agw.flatmenu as FM
from wx.lib.agw.artmanager import ArtManager, RendererBase, DCSaver
from wx.lib.agw.fmresources import ControlFocus, ControlPressed
from wx.lib.agw.fmresources import FM_OPT_SHOW_CUSTOMIZE, FM_OPT_SHOW_TOOLBAR, FM_OPT_MINIBAR

import os, sys

try:
    dirName = os.path.dirname(os.path.abspath(__file__))
except:
    dirName = os.path.dirname(os.path.abspath(sys.argv[0]))

bitmapDir = os.path.join(dirName, 'bitmaps')
sys.path.append(os.path.split(dirName)[0])

import multiplierz.mzAPI
import multiplierz.mzReport as mzReport
import wx
import subprocess
import multiplierz.mzReport.mzSpreadsheet as mzSpreadsheet
import collections
import os
import sys
import re
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('.') + '\\Extraction')
import shutil

from collections import defaultdict

import mz_workbench.mz_core as mz_core
#import mz_workbench.ABSciex_core as ABSciex_core
#from multiplierz.mzAPI.raw import mzFile
import mz_workbench.mz_masses as mz_masses
print sys.path
print os.path.abspath(os.getcwd())
sys.path.append(".")

import glob
import sqlite3 as sql
import csv
try:
    import win32com.client
except:
    pass
import mz_workbench.protein_core as protein_core
import cPickle
import multiplierz.mzGUI_standalone as mzGUI
import  wx.lib.mixins.listctrl  as  listmix

import wx.lib.agw.flatmenu as FM
from wx.lib.agw.artmanager import ArtManager, RendererBase, DCSaver
from wx.lib.agw.fmresources import ControlFocus, ControlPressed
from wx.lib.agw.fmresources import FM_OPT_SHOW_CUSTOMIZE, FM_OPT_SHOW_TOOLBAR, FM_OPT_MINIBAR

bitmapDir = os.path.dirname(os.path.realpath(__file__)) + '\\bitmaps'

class PageOne(wx.Panel):
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent)

class PageTwo(wx.Panel):
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent)

listctrldata = {
1 : ("Hey!", "You can edit"),
2 : ("Try changing the contents", "by"),
}

class NoEditListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin):  #

    def __init__(self, parent, ID, size = (300,200), pos=(0,0), style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, "Sequence")
        self.InsertColumn(1, "Title")
        self.SetColumnWidth(0, 250)
        self.SetColumnWidth(1, 100)
        self.bank_num = 0
        

    def Populate(self, seq, title):
        # for normal, simple columns, you can add them like this:
        self.bank_num += 1
        index = self.InsertStringItem(sys.maxint, seq)
        self.SetStringItem(index, 1, title)
            
        self.SetItemData(index, self.bank_num)
        
        
    def SetStringItem(self, index, col, data):
            if col in range(2):
                wx.ListCtrl.SetStringItem(self, index, col, data)
                #wx.ListCtrl.SetStringItem(self, index, 3+col, str(len(data)))
            else:
                try:
                    datalen = int(data)
                except:
                    return
    
                wx.ListCtrl.SetStringItem(self, index, col, data)
    
                data = self.GetItem(index, col-3).GetText()
                wx.ListCtrl.SetStringItem(self, index, col-3, data[0:datalen]) 

class TestListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):  #

    def __init__(self, parent, panel, ID, size = (450,200), pos=(0,30), style=0):
        self.parent = parent
        wx.ListCtrl.__init__(self, panel, ID, pos, size, style)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        #self.Populate()
        listmix.TextEditMixin.__init__(self)
        self.editor.Disable()
        #self.editor.RemoveSelection()
        #self.editor.Destroy()
        #self.editor.SetCanFocus(False)
        self.InsertColumn(0, "Sequence")
        self.InsertColumn(1, "Title")
        self.SetColumnWidth(0, 300)
        self.SetColumnWidth(1, 150)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
        #self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.LeftD)
        self.bank_num = 0
        #self.Select(0,0)
        #self.editor.Hide()
    

    def OnRightUp(self, evt):
        self.parent.memory_bank.Hide()

    def LeftD(self, evt):
        print "D"
        if self.editable:
            evt.Skip()

    def OnLeft(self, evt):
        if not self.editable:
            for i in range(0, self.GetItemCount()):
                #self.SetItemState(i, 0)
                self.Select(i, 0)
            print evt.GetPosition()
            print evt.GetEventObject()
            print evt.GetButton()
            print self.HitTest(evt.GetPosition())
            
            self.Select(self.HitTest(evt.GetPosition())[0])
        else:
            evt.Skip()

    def Populate(self, seq, title):
        # for normal, simple columns, you can add them like this:
        self.bank_num += 1
        index = self.InsertStringItem(sys.maxint, seq)
        self.SetStringItem(index, 1, title)
            
        self.SetItemData(index, self.bank_num)
        
        
    def SetStringItem(self, index, col, data):
            if col in range(2):
                wx.ListCtrl.SetStringItem(self, index, col, data)
                #wx.ListCtrl.SetStringItem(self, index, 3+col, str(len(data)))
            else:
                try:
                    datalen = int(data)
                except:
                    return
    
                wx.ListCtrl.SetStringItem(self, index, col, data)
    
                data = self.GetItem(index, col-3).GetText()
                wx.ListCtrl.SetStringItem(self, index, col-3, data[0:datalen])        

class ListBank(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self,parent,id, 'List Bank', size =(450,270), pos = (50,50))
        self.panel = wx.Panel(self)
        #minibarPanel = wx.Panel(self)
        #self._mtb = FM.FlatMenuBar(self.panel, wx.ID_ANY, 20, 6, options = FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)
        #self.bank = wx.ListBox(self.panel, -1, choices=[], size = (300,200), pos=(0,0))
        #self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.bank)
        
        
        #self.canned = wx.ComboBox(self.panel, -1, "", size = (600,20), pos=(0,25), choices=['select * from peptides;'])

        #self.Bind(wx.EVT_COMBOBOX, self.Build, self.builder)
        #self.Bind(wx.EVT_COMBOBOX, self.SendCanned, self.canned)
        
        #self.CreateMinibar(self.panel)
        #miniSizer = wx.BoxSizer(wx.VERTICAL)
        #miniSizer.Add(self._mtb, 0, wx.EXPAND)
        #self.SetSizer(miniSizer)  
        #self._mtb = FM.FlatMenuBar(minibarPanel, wx.ID_ANY, 30, 6, options = FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)
        #bankBmp = wx.Bitmap(os.path.join(bitmapDir, "OpenBank.bmp"), wx.BITMAP_TYPE_BMP)
        #bankBmp2 = wx.Bitmap(os.path.join(bitmapDir, "bank2.bmp"), wx.BITMAP_TYPE_BMP)
        #self._mtb.AddTool(toolId=2120, label="Mem", bitmap1=bankBmp, bitmap2=wx.NullBitmap, shortHelp="Open Memory Bank", longHelp="Open Memory Bank")       
        #self._mtb.Refresh()        
        #miniSizer = wx.BoxSizer(wx.VERTICAL)
        #miniSizer.Add(self._mtb, 0, wx.EXPAND)
        #self.SetSizer(miniSizer)    
        #self._mtb.Refresh()
        #if not self.editable:
        self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING) 
        #else:
        #self.listb = NoEditListCtrl(self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING) 
        self.listb.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        self.listb.editable=False
        #self.listb.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnAct)
        self.Save = wx.Button(self.panel, -1, "Save", pos=(0,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.Save)
        self.Load = wx.Button(self.panel, -1, "Load", pos=(30,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnLoad, self.Load)
        self.Delete = wx.Button(self.panel, -1, "Delete", pos=(60,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.Delete)
        self.Clear = wx.Button(self.panel, -1, "Clear All", pos=(90,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.Clear)
        self.Stds = wx.Button(self.panel, -1, "Standards", pos=(150,0), size=(60,25))
        self.Bind(wx.EVT_BUTTON, self.OnStds, self.Stds)     
        ebutton = wx.Button(self.panel, -1, "Edit", (120, 0), (25,25))
        self.Bind(wx.EVT_BUTTON, self.OnEdit, ebutton)        
        self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.listb.Bind(wx.EVT_RIGHT_DOWN, self.OnRightUp)
        self.listb.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        self.Refresh()
        self.Update()
        self.Refresh()
        
        
    def OnColClick(self, evt):
        print "COLCLICK"
        evt.Skip()
        
    def OnRightUp(self, evt):
        self.Hide()
        
    def OnAct(self, event):
        pass
        
    def OnEdit(self, event):
        self.listb.editable=not self.listb.editable
        print "Editable"
        print self.listb.editable
        if self.listb.editable:
            self.listb.editor.Enable()
        else:
            self.listb.editor.Disable()
            #wx.PostEvent(self.OnColClick, wx.EVT_LIST_COL_CLICK)
            #wx.EVT_LIST_COL_CLICK
        
    def CreateMinibar(self, parent):
        # create mini toolbar
        self._mtb = FM.FlatMenuBar(self, wx.ID_ANY, 20, 6, options = FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)
        bankBmp = wx.Bitmap(os.path.join(bitmapDir, "OpenBank.bmp"), wx.BITMAP_TYPE_BMP)
        #bankBmp2 = wx.Bitmap(os.path.join(bitmapDir, "bank2.bmp"), wx.BITMAP_TYPE_BMP)

        self._mtb.AddTool(toolId=2120, label="Mem", bitmap1=bankBmp, bitmap2=wx.NullBitmap, shortHelp="Open Memory Bank", longHelp="Open Memory Bank")       
        
    def OnSelected(self, event):
        item = event.GetItem()
        print item.GetText()
        data = item.GetText().split('-')
        #data = self.bank.GetStringSelection().split('-')
        nterm = data[0]
        seq = data[1]
        cterm = data[2]
        if nterm == "H":
            nterm = "None"
        if cterm == "OH":
            cterm = "None"
        self.parent.FindWindowByName("sequence").SetValue(seq)
        self.parent.FindWindowByName("nTerm").SetValue(nterm)
        self.parent.FindWindowByName("cTerm").SetValue(cterm)
        self.parent.OnCalculate(None)        
        event.Skip()
        
    def RadioBoxData(self):
        return (("Masses", ['monoisotopic', 'average'], 'masses', (10, 190), wx.DefaultSize),) #, 'average'        
    
    def OnStds(self, event):
        file_r = open(os.path.join(os.path.dirname(__file__), r'PeptideStandards.txt', 'r'))
        lines = file_r.readlines()
        self.bank.Clear()
        for line in lines:
            self.bank.Append(line.strip())
        file_r.close()        

    def OnSave(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.savedir = dir
        self.savefilename = filename
        print dir
        print filename
        if filename.find(".txt") == -1:
            filename += ".txt"
            self.savefilename = filename
        file_w = open(dir + '\\' + filename, 'w')
        for i in range(0, self.listb.ItemCount):
            file_w.write(self.listb.GetItemText(i,0) + '\t' + self.listb.GetItemText(i,1) + '\n')        
        file_w.close()

    def OnLoad(self, event):
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.OPEN, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.loaddir = dir
        self.loadfilename = filename
        print dir
        print filename
        file_r = open(dir + '\\' + filename, 'r')
        lines = file_r.readlines()
        self.listb.ClearAll()
        for line in lines:
            print line
            print line.split('\t')[0].strip()
            print line.split('\t')[1].strip()
            self.listb.Populate(line.split('\t')[0].strip(), line.split('\t')[1].strip())
            
        file_r.close()

    def OnDelete(self, event):
        #self.bank.Delete(self.bank.GetSelection())
        #self.listb.listmix.TextEditMixin.__init__(self)
        self.listb.editor.Enable()

    def OnClear(self, event):
        #self.bank.Clear()
        index = self.listb.InsertStringItem(sys.maxint, "A")
        self.listb.SetStringItem(index, 1, "B")
        #self.SetStringItem(index, 2, data[2])
        #self.listb.GetItems
        self.listb.SetItemData(index, 3)        
        #self.listb.Append(entry)
    
    def OnSelect(self, event):
        data = self.bank.GetStringSelection().split('-')
        nterm = data[0]
        seq = data[1]
        cterm = data[2]
        if nterm == "H":
            nterm = "None"
        if cterm == "OH":
            cterm = "None"
        self.parent.FindWindowByName("sequence").SetValue(seq)
        self.parent.FindWindowByName("nTerm").SetValue(nterm)
        self.parent.FindWindowByName("cTerm").SetValue(cterm)
        self.parent.OnCalculate(None)    
        

class MemoryBank(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self,parent,id, 'Memory Bank', size =(400,250), pos = (50,50))
        self.panel = wx.Panel(self)
        self.bank = wx.ListBox(self.panel, -1, choices=[], size = (300,200), pos=(0,0))
        self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.bank)
        self.Save = wx.Button(self.panel, -1, "S", pos=(310,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.Save)
        self.Load = wx.Button(self.panel, -1, "L", pos=(310,30), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnLoad, self.Load)
        self.Delete = wx.Button(self.panel, -1, "D", pos=(340,0), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.Delete)
        self.Clear = wx.Button(self.panel, -1, "C", pos=(340,30), size=(25,25))
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.Clear)
        self.Stds = wx.Button(self.panel, -1, "Standards", pos=(310,60), size=(60,25))
        self.Bind(wx.EVT_BUTTON, self.OnStds, self.Stds)        
        #self.canned = wx.ComboBox(self.panel, -1, "", size = (600,20), pos=(0,25), choices=['select * from peptides;'])

        #self.Bind(wx.EVT_COMBOBOX, self.Build, self.builder)
        #self.Bind(wx.EVT_COMBOBOX, self.SendCanned, self.canned)

    def RadioBoxData(self):
        return (("Masses", ['monoisotopic', 'average'], 'masses', (10, 190), wx.DefaultSize),) #, 'average'        

    def OnStds(self, event):
        file_r = open(os.path.join(os.path.dirname(__file__), r'PeptideStandards.txt', 'r'))
        lines = file_r.readlines()
        self.bank.Clear()
        for line in lines:
            self.bank.Append(line.strip())
        file_r.close()        

    def OnSave(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.savedir = dir
        self.savefilename = filename
        print dir
        print filename
        if filename.find(".txt") == -1:
            filename += ".txt"
            self.savefilename = filename
        file_w = open(dir + '\\' + filename, 'w')
        Choices = self.bank.GetItems()
        for member in Choices:
            file_w.write(member + '\n')
        file_w.close()

    def OnLoad(self, event):
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.OPEN, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.loaddir = dir
        self.loadfilename = filename
        print dir
        print filename
        file_r = open(dir + '\\' + filename, 'r')
        lines = file_r.readlines()
        self.bank.Clear()
        for line in lines:
            self.bank.Append(line.strip())
        file_r.close()

    def OnDelete(self, event):
        self.bank.Delete(self.bank.GetSelection())

    def OnClear(self, event):
        self.bank.Clear()

    def OnSelect(self, event):
        data = self.bank.GetStringSelection().split('-')
        nterm = data[0]
        seq = data[1]
        cterm = data[2]
        if nterm == "H":
            nterm = "None"
        if cterm == "OH":
            cterm = "None"
        self.parent.FindWindowByName("sequence").SetValue(seq)
        self.parent.FindWindowByName("nTerm").SetValue(nterm)
        self.parent.FindWindowByName("cTerm").SetValue(cterm)
        self.parent.OnCalculate(None)


class CHNOPS_Frame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'CHNOPS', size =(180,660), pos = (50,50))
        panel = wx.Panel(self)
        atoms = [x for x in 'CHNOPS'] + ['C13', 'N15', 'Cl', 'Br', 'Fe']
        gbs = wx.GridBagSizer(len(atoms)+3, 5)
        #gbs.Add( wx.StaticText(panel, -1, 'Experiment', style=wx.ALIGN_RIGHT),
        #             (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        #gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
        #             (0, 1), (1,8) )
        for i, atom in enumerate(atoms):
            print atom
            gbs.Add( wx.StaticText(panel, -1, atom, style=wx.ALIGN_RIGHT,  size=(50,25)),
                     (i, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
            gbs.Add( wx.TextCtrl(panel, -1, '', name = atom,  size=(30,25)),
                     (i, 1), (1,8))#, size=(250, 25)
        calc_btn = wx.Button(panel, -1, 'Calc',  size=(50,25))
        gbs.Add( calc_btn,
                 (len(atoms)+1,0) )
       
        calc_btn.Bind(wx.EVT_BUTTON, self.on_calc)
        
        mass_type_radio = wx.RadioBox(panel, -1, label="Masses", choices=['monoisotopic', 'average'], name='masses', pos=(10, 190), majorDimension=1, size=wx.DefaultSize, style=wx.RA_SPECIFY_COLS)
        
        gbs.Add(mass_type_radio, (len(atoms)+3,0))
        
        result = wx.TextCtrl(panel, -1, '', name = "result",  size=(120,25))
        gbs.Add( result,
                 (len(atoms)+2,0) )        
        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.parent = parent
        self.atoms = atoms
        
    def on_calc(self, event):
        CHNOPS_list = {}
        calcType = 'mi' if self.FindWindowByName("masses").GetStringSelection() == 'monoisotopic' else 'av'
        for member in self.atoms:
            val = self.parent.FindWindowByName(member).GetValue().strip()
            if val:
                CHNOPS_list[member]=int(val)
        mass = mz_masses.calc_mass(CHNOPS_list, calcType)
        self.FindWindowByName("result").SetValue(str(mass))

class BlaisPepCalc(wx.Frame):
    def __init__(self, parent, id, organizer):
        self.parent = parent
        wx.Frame.__init__(self,parent,id, 'BlaisPepCalc', size =(580,660), pos = (50,50))
        
        organizer.addObject(self) # Allows only one BlaisPepCalc object to exist in a session.
        self.organizer = organizer
        
        panel = wx.Panel(self)
        nb = wx.Notebook(panel, size=(600,600), pos= (10,10))
        self.page1 = PageOne(nb)
        self.page2 = PageTwo(nb)
        nb.AddPage(self.page1, "Main")
        nb.AddPage(self.page2, "Settings")
        self.createButtons(self.page1)
        #--------------------------POPUP MEM BANK BUTTON
        abutton = wx.Button(self.page1, -1, "M2", (260, 5), (25,25))
        self.Bind(wx.EVT_BUTTON, self.ActMem, abutton)        
                        
        #self.createCheckBoxes(self.page1)
        self.createLabels(self.page1)
        self.createTextBoxes(self.page1)
        self.dir = ''
        self.createRadioBoxes(self.page1)
        self.createListBoxes(self.page1)
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText("Ready")
        self.Nterm_mods = mz_core.Nterm_dict.keys()
        self.Nterm_mods.sort()
        self.Cterm_mods = mz_core.Cterm_dict.keys()
        self.Cterm_mods.sort()
        self.createComboBoxes(self.page1)
        self.createSpinBoxes(self.page1)
        #self.createCheckListBoxes(self.page1)
        self.CreateMenuBar()
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.PrecClick, self.FindWindowByName('precursorListBox'))
        self.memory_bank = ListBank(self, -1)
        self.CreateMinibar(self.page1)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    
    def OnEdit(self, event):
        pass
    
    
    def CreateMinibar(self, parent):
        # create mini toolbar
        self._mtb = FM.FlatMenuBar(parent, wx.ID_ANY, 16, 6, options = FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)

        checkCancelBmp = wx.Bitmap(os.path.join(bitmapDir, "ok-16.png"), wx.BITMAP_TYPE_PNG)
        viewMagBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-16.png"), wx.BITMAP_TYPE_PNG)
        viewMagFitBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmagfit-16.png"), wx.BITMAP_TYPE_PNG)
        viewMagZoomBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-p-16.png"), wx.BITMAP_TYPE_PNG)
        viewMagZoomOutBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-m-16.png"), wx.BITMAP_TYPE_PNG)

        self._mtb.AddCheckTool(wx.ID_ANY, "Check Settings Item", checkCancelBmp)
        self._mtb.AddCheckTool(wx.ID_ANY, "Check Info Item", checkCancelBmp)
        self._mtb.AddSeparator()
        self._mtb.AddRadioTool(wx.ID_ANY, "Magnifier", viewMagBmp)
        self._mtb.AddRadioTool(wx.ID_ANY, "Fit", viewMagFitBmp)
        self._mtb.AddRadioTool(wx.ID_ANY, "Zoom In", viewMagZoomBmp)
        self._mtb.AddRadioTool(wx.ID_ANY, "Zoom Out", viewMagZoomOutBmp)    
    
    def PrecClick(self, event):
        print self.FindWindowByName('precursorListBox').GetStringSelection()
        
        self.popupID1 = wx.NewId()
        self.popupID2 = wx.NewId()

        self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
        self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)        
        
        # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupID1,"XIC")
        menu.AppendItem(item)
        # add some other items
        menu.Append(self.popupID2, "FIND PRECURSORS")
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()        
        
        event.Skip()
        
    def OnPopupOne(self, event):
        print "One"
        print "XIC for " + self.FindWindowByName('precursorListBox').GetStringSelection()
        
    def OnPopupTwo(self, event):
        print "Two"
        
    def ActMem(self, event):
        self.memory_bank.listb.Populate(self.return_mem_seq(), '')
        event.Skip()
    
    def RadioBoxData(self):
        return (("Masses", ['monoisotopic', 'average'], 'masses', (10, 190), wx.DefaultSize),) #, 'average'

    def ListBoxData(self):
        return (([], 'productListBox', (10, 270), (180,250)),
                ([], 'precursorListBox', (200, 270), (140,110)))

    def OnHelp(self, panel):
        word = win32com.client.Dispatch('Word.Application')
        word.Documents.Open(r"\Data Manager.doc")

        #subprocess.Popen()
        word.Visible=1

    def menuData(self):
        return  (("&File",
                    ("&Open", "Open Template", self.OnLoad),
                    ("&Save", "Save Template", self.OnSave)),
                ("&Actions",
                    ("&CHNOPS", "CHNOPS", self.OnCHNOPS)
                    ),
                ("&View",
                    ("&Memory Bank", "Memory Bank", self.OnViewMemoryBank)
                    ),
                ("&Help",
                    ("&Help", "Help", self.OnHelp)))

    def OnLoad(self):
        pass
    def OnSave(self):
        pass
    def OnCHNOPS(self, event):
        c_frame = CHNOPS_Frame(self, -1)
        c_frame.Show()

    def CreateMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            print menuLabel
            menuItems = eachMenuData[1:]
            print menuItems
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu=wx.Menu()
        print menuData
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator(self)
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

    def ComboBoxData(self):
        return (('nTerm', (200, 400), (140,20), ["None"] + self.Nterm_mods, 0, False, None, self.page1),
                ('cTerm', (200, 440), (140,20), ["None"] + self.Cterm_mods, 0, False, None, self.page1),
                ('ions', (200, 480), (140,20), ["b/y", "c/z"], 0, False, None, self.page1))

    def createComboBoxes(self, panel):
        for eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel in self.ComboBoxData():
            ComboBox = self.BuildOneComboBox(panel, eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel)

    def BuildOneComboBox(self, panel, eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel):
        ComboBox = wx.ComboBox(eachPanel, -1, size=eachSize, pos=eachPos, name=eachName, value=eachList[eachInit], choices=eachList)
        if eachEvent:
            self.Bind(wx.EVT_COMBOBOX, eachHandler, ComboBox)
        return ComboBox
        
    def ButtonData(self):
        return (("OnCalculate", self.OnCalculate, (300, 35), (120,25), self.page1),
                ("C", self.OnClear, (180, 35), (25,25), self.page1),
                ("P", self.OnPrint, (220, 35), (25,25), self.page1),
                ("M", self.OnMemoryBank, (260, 35), (25,25), self.page1),
                ("->", self.OnXFer, (140, 35), (25,25), self.page1)
                )

    def CheckData(self):
        return (("Same Set/Sub Set", (300, 190), (150,20), "sameSetsubSet", True, self.page1),
            )

    def LabelData(self):
        return (("Enter Sequence Here", (10, 40), (120,20), self.page1),
                ("Charge States to Calculate:", (10, 130), (145,20), self.page1),
                (r"Charge State of b\y pairs:", (200, 130), (140,20), self.page1),
                (r"Decimals:", (10, 160), (50,20), self.page1),
                ("N-term", (200, 385), (140,15), self.page1),
                ("C-term", (200, 425), (140,15), self.page1),
                ("Ions", (200, 465), (140,15), self.page1))

    def SpinBoxData(self):
        return (("", (155, 130), (40,20), "cgStatesCalc", self.page1, (1,100),6),
                ("", (340, 130), (40,20), "cgStatesProduct", self.page1, (1, 100),1),
                ("", (70, 160), (40,20), "decimals", self.page1,(1,100),4))

    def TextBoxData(self):
        return (("", (10,65), (450,50), "sequence", self.page1),
                )

    def CheckListBoxData(self):
        return (([], 'filesListBox', (10, 70), (200,150)),
                )

    def createSpinBoxes(self, panel):
        for eachLabel, spinPos, spinSize, eachName, eachPanel, eachRange, eachVal in self.SpinBoxData():
            SpinBox = self.BuildOneSpinBox(eachPanel, eachLabel, spinSize, spinPos, eachName, eachRange, eachVal)

    def BuildOneSpinBox(self, eachPanel, eachLabel, boxSize, boxPos, eachName, eachRange, eachVal):
        spinBox = wx.SpinCtrl(eachPanel, -1, eachLabel, pos = boxPos, size=boxSize, name=eachName)
        spinBox.SetRange(*eachRange)
        spinBox.SetValue(eachVal)
        return spinBox

    def BuildOneCheckListBox(self, panel, eachList, eachName, eachPos, eachSize):
        CheckListBox = wx.CheckListBox(panel, -1, size=eachSize, pos=eachPos, name=eachName, choices = eachList, style=wx.LB_HSCROLL)
        return CheckListBox
    
    def createCheckListBoxes(self, panel):
        for eachList, eachName, eachPos, eachSize in self.CheckListBoxData():
            CheckListBox = self.BuildOneCheckListBox(panel, eachList, eachName, eachPos, eachSize)

    def createListBoxes(self, panel):
        for eachList, eachName, eachPos, eachSize in self.ListBoxData():
            ListBox = self.BuildOneListBox(panel, eachList, eachName, eachPos, eachSize)

    def createRadioBoxes(self, panel):
        for eachLabel, eachList, eachName, eachPos, eachSize in self.RadioBoxData():
            RadioBox = self.BuildOneRadioBox(panel, eachLabel, eachList, eachName, eachSize, eachPos)

    def createTextBoxes(self, panel):
        for eachLabel, boxPos, boxSize, eachName, eachPanel in self.TextBoxData():
            TextBox = self.MakeOneTextBox(eachPanel, eachLabel, boxSize, boxPos, eachName)

    def createLabels(self, panel):
        print self.LabelData()
        for eachLabel, labelPos, labelSize, eachPanel in self.LabelData():
            label = self.MakeOneLabel(panel, eachLabel, labelPos, labelSize, eachPanel)
    
    def createButtons(self, panel):
        for eachLabel, eachHandler, pos, size, eachPanel in self.ButtonData():
            button = self.BuildOneButton(eachPanel, eachLabel, eachHandler, pos, size)
            
    def createCheckBoxes(self, panel):
        for eachLabel, pos, size, eachName, eachValue, eachPanel in self.CheckData():
            check = self.CreateOneCheck(eachPanel, eachLabel, pos,size, eachName, eachValue)

    def BuildOneListBox(self, panel, eachLabel, eachName, eachPos, eachSize):
        ListBox = wx.ListBox(panel, -1, size=eachSize, pos=eachPos, name=eachName, style=wx.LB_HSCROLL)
        return ListBox

    def BuildOneRadioBox(self, panel, eachLabel, eachList, eachName, eachSize, eachPos):
        RadioBox = wx.RadioBox(panel, -1, label=eachLabel, pos=eachPos, size=eachSize, choices=eachList, majorDimension=1, style=wx.RA_SPECIFY_COLS, name=eachName)
        return RadioBox

    def MakeOneTextBox(self, eachPanel, eachLabel, boxSize, boxPos, eachName):
        textBox = wx.TextCtrl(eachPanel, -1, eachLabel, pos = boxPos, size=boxSize, name = eachName, style=wx.TE_MULTILINE)
        return textBox

    def MakeOneLabel(self, panel, label, labelPos, labelSize, eachPanel):        
        label = wx.StaticText(eachPanel, -1, label, pos=labelPos, size=labelSize, name = label)
        return label

    def BuildOneButton(self, eachPanel, label, handler, pos, size):
        button = wx.Button(eachPanel, -1, label, pos, size)
        self.Bind(wx.EVT_BUTTON, handler, button)
        return button

    def CreateOneCheck(self, eachPanel, label, pos, size, boxname, eachValue):
        checkbox = wx.CheckBox(eachPanel, -1, label, pos, size, name = boxname)
        if eachValue:
            checkbox.SetValue(eachValue)
        return checkbox

    def OnCalculate(self, event):
        calcType = 'mi' if self.FindWindowByName("masses").GetStringSelection() == 'monoisotopic' else 'av'
        nterm = self.FindWindowByName("nTerm").GetValue().strip()
        cterm = self.FindWindowByName("cTerm").GetValue().strip()
        _ions = self.FindWindowByName("ions").GetValue().strip()
        if nterm == "None":
            nterm = ''
        if cterm == "None":
            cterm = ''
        cg_calc = self.FindWindowByName("cgStatesCalc").GetValue()
        cg_by = self.FindWindowByName("cgStatesProduct").GetValue()
        dec = self.FindWindowByName("decimals").GetValue()
        self.FindWindowByName("productListBox").Clear()
        self.FindWindowByName("precursorListBox").Clear()
        seq = self.FindWindowByName("sequence").GetValue()
        #First, precursor.  
        zerocg, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = 0, Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        #Calc +1, then the rest.
        mz, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = 1, Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        charge_states = []
        for i in range(0, int(cg_calc)):
            current = float((mz + (i*mz_core.mass_dict["H+"])))/float(i +1)
            charge_states.append(current)
        charge_states.insert(0, zerocg)
        for i, member in enumerate(charge_states):
            self.FindWindowByName("precursorListBox").Append('+' + str(i) + ' = ' + str(round(member, dec)))
        mz, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = int(cg_by), Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        length = len(b_ions)
        peptide = []
        pa = re.compile('([a-z]*[A-Z]+?)')
        peptide = pa.findall(seq)
        for i, member in enumerate(b_ions):
            line = "b" + str(i+1) + ' ' + str(round(b_ions[i],dec)) + '  ' + peptide[i] + '  ' + str(round(y_ions[length-1-i],dec)) + ' ' + "y" + str(length-i)
            self.FindWindowByName("productListBox").Append(line)
        self.b_ions = b_ions
        self.y_ions = y_ions

    def OnClear(self, event):
        pass
    def OnPrint(self, event):
        pass

    def OnViewMemoryBank(self, event):
        print "M"
        #self.memory_bank = MemoryBank(self, -1)
        self.memory_bank.Show()
        
        

    def return_mem_seq(self):
        nterm = self.FindWindowByName("nTerm").GetValue().strip()
        print nterm
        cterm = self.FindWindowByName("cTerm").GetValue().strip()
        seq = self.FindWindowByName("sequence").GetValue()
        print seq
        if nterm == "None":
            nterm = 'H'
        if cterm == "None":
            cterm = 'OH'
        return nterm + "-" + seq + "-" + cterm

    def OnMemoryBank(self,event):
        #try:
            #self.memory_bank.bank.Append(self.return_mem_seq())
        #except:
        #self.memory_bank = ListBank(self, -1)
        self.memory_bank.Show()
        #self.memory_bank.bank.Append(self.return_mem_seq())

    def OnXFer(self, event):
        currentFile = self.parent.msdb.files[self.parent.msdb.Display_ID[self.parent.msdb.active_file]]
        scanNum = currentFile["scanNum"]
        currentFile["overlay"][scanNum]=[self.y_ions, self.b_ions]
        currentFile['overlay_sequence']=self.FindWindowByName("sequence").GetValue()
        self.parent.msdb.build_current_ID(currentFile["FileAbs"],scanNum)
        self.parent.Window.UpdateDrawing()
        self.parent.Refresh()
        
    def OnClose(self, event):
        self.organizer.removeObject(self)
        self.Destroy()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = BlaisPepCalc(parent=None, id=-1)
    frame.Show()
    app.MainLoop()
        
