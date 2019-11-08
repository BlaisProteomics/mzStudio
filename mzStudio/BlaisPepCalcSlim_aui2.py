__author__ = 'Scott Ficarro, William Max Alexander'
__version__ = '1.0'


import wx.lib.agw.aui as AUI
AuiPaneInfo = AUI.AuiPaneInfo
AuiManager = AUI.AuiManager

import wx.lib.agw.aui as aui

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
import multiplierz.mzTools as mzTools
import multiplierz.mzSearch.mascot as mascot
import PopUpWins
from collections import defaultdict

#import mz_workbench.mz_core as mz_core
from mz_workbench.mz_core import read_new_res_dict

# import mz_workbench.ABSciex_core as ABSciex_core
from multiplierz.mzAPI.raw import mzFile
import mz_workbench.mz_masses as mz_masses
#print sys.path
#print os.path.abspath(os.getcwd())
sys.path.append(".")

import glob
import sqlite3 as sql
import csv
try:
    import win32com.client
except ImportError:
    pass
import mz_workbench.protein_core as protein_core
import cPickle
import multiplierz.mzGUI_standalone as mzGUI
import os
import mzStudio as bb
#import wx.lib.agw.flatmenu as FM
import flatmenu_patched as FM
from wx.lib.agw.artmanager import ArtManager, RendererBase, DCSaver
from wx.lib.agw.fmresources import ControlFocus, ControlPressed
from wx.lib.agw.fmresources import FM_OPT_SHOW_CUSTOMIZE, FM_OPT_SHOW_TOOLBAR, FM_OPT_MINIBAR

import ModManager

import ListBank as lb

import wx.lib.scrolledpanel as ScrolledPanel

bitmapDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bitmaps')
mz_settings_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'mz_workbench', 'files')

TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            #| wx.TB_TEXT
            #| wx.TB_HORZ_LAYOUT
            )




from multiplierz.mass_biochem import fragment, mw, protonMass, AminoAcidMasses, chemicalDataMass, AW#, unimod

def replace(foo, bar, baz):
    foo[baz] = foo[bar]
    del foo[bar]
    

mod_lookup_table = {}
mod_file = open(os.path.join(mz_settings_dir, 'new_res_list.txt'))
for line in mod_file:
    key, name, formstr = line.split('|')[:3] # Omitting 'source' column because Chris forgot to add those.
    if not key:
        continue
    forms = [mol.strip().split(':') for mol in formstr.split(', ')]
    fla = dict((x[0], int(x[1])) for x in forms)

    lkey = key[:-1]
    hkey = key[-1:]
    if 'N15' in fla:
        replace(fla, 'N15', '15N')
    if 'D' in fla:
        replace(fla, 'D', '2H')
    if 'C13' in fla:
        replace(fla, 'C13', '13C')
    if 'S35' in fla:
        continue
    mass = chemicalDataMass(fla)
    if mass and hkey in AminoAcidMasses:
        mod_lookup_table[lkey, hkey] = mass - AminoAcidMasses[hkey][0]

class PageOne(wx.Panel):
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent)

class PageTwo(wx.Panel):
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent)

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

class MainBPC(wx.Panel):
#class MainBPC(ScrolledPanel):
    def __init__(self, parent, id, organizer):
        
        organizer.addObject(self) # Allows only one BlaisPepCalc object to exist in a session.
        self.organizer = organizer         
        wx.Panel.__init__(self, parent, id=id, name='BlaisPepCalc', size =(290,670), pos = (50,50))
        self._CreateMenu()
        self.parent = parent
        self.b = BlaisPepCalc(self, -1, organizer)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.menubar, 0, wx.EXPAND)
        main_sizer.Add(self.b, 1, wx.EXPAND)        
        
        self.labelOverwrite = False
        
        self.SetSizer(main_sizer)
        main_sizer.Layout()
        #self.Refresh()
        #self.Update()        
        #self.parent._mgr.Update()   
        
        self.aui_pane = None
        
        self.bpc_tb = None
        #
        #self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnClose(self, event):
        #if self.aui_pane.name != event.pane.name:
        #    print "%s got event but isn't being closed." % self.aui_pane.name
        #    event.Skip()
        #    return
            
        self.organizer.removeObject(self)
        assert not self.organizer.containsType(self)
        print "PepCalc Close event!"
        #event.Skip()
        
        
    def _CreateMenu(self):
        
        self.menubar = FM.FlatMenuBar(self, -1, 30, 6, options=FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)

        clr = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'clear_img.bmp'), wx.BITMAP_TYPE_BMP)
        open = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'open_bank.bmp'), wx.BITMAP_TYPE_BMP)
        add = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'add_img.bmp'), wx.BITMAP_TYPE_BMP)
        mod = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'mod_img.bmp'), wx.BITMAP_TYPE_BMP)
        overlay = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'overlay_img.bmp'), wx.BITMAP_TYPE_BMP)
        convert = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'convert_img.bmp'), wx.BITMAP_TYPE_BMP)
        clear_and_add = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'Clear and add overlay.bmp'), wx.BITMAP_TYPE_BMP)
        repl = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'repl_img.bmp'), wx.BITMAP_TYPE_BMP)
        overlay_label = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'overlaylabel_img.bmp'), wx.BITMAP_TYPE_BMP)
        removeOverlay =  wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_TOOLBAR, (24,24))
        copyToClipboard = wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR, (24,24))
        #overlaylabel_img
        #(150, "XIC", wx.Image(installdir + r'\image\Add new trace.png'), "XIC adds to new window", "XIC adds to new window'", 150))
        #--------------Adds drop box to flatmenu
        #control = wx.Choice(self.menubar, -1, choices=["Add Labels", "Replace Lables"])
        #self.menubar.AddControl(control)
        #------------------------------------
        #self.menubar.AddCheckTool(70, "Clear and Replace Labels", repl)
        
        self.menubar.AddTool(10, "Clear Sequence", clr)
        self.menubar.AddTool(20, "Open Memory Bank", open)
        self.menubar.AddTool(30, "Add Sequence to Memory Bank", add)
        self.menubar.AddTool(40, "Open Mod Manager", mod)
        self.menubar.AddTool(50, "Overlay ions on spectrum", overlay)
        self.menubar.AddTool(80, "Remove spectrum overlay", removeOverlay)
        self.menubar.AddTool(90, "Copy To Clipboard", copyToClipboard)
        
        #self.menubar.AddTool(60, "Convert mods", convert)
        
        
        #self.menubar.AddTool(70, "Overlay ions", clear_and_add)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 10)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 20)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 30)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 40)  
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 50)
        #self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 60)
        #self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 70)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 80)
        self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 90)
        
    def OnToolClick(self, evt):
        if evt.GetId() == 10:
            self.b.OnClear(evt)
        if evt.GetId() == 20:
            self.b.OnViewMemoryBank(evt)
        if evt.GetId() == 30:
            self.b.ActMem(evt)
        if evt.GetId() == 40:
            self.b.OnModManager(evt)        
        if evt.GetId() == 50:
            self.b.OnXFer(evt)
        #if evt.GetId() == 60:
            #self.b.tbar(evt)   
        #if evt.GetId() == 70:
            ##self.labelOverwrite = not self.labelOverwrite
            #pass
        if evt.GetId() == 80:
            self.b.removeOverlay(evt) 
        if evt.GetId() == 90:
            self.b.OnCopyToClipboard(evt)         
                     
class BlaisPepCalc(wx.Panel):
    def __init__(self, parent, id, organizer):
        self.parent = parent
        wx.Panel.__init__(self, parent, id=id, name='BlaisPepCalc', size =(290,670), pos = (50,50))
        
        self.b = self # !!
        
        self.createButtons(self)
        self.createLabels(self)
        self.createTextBoxes(self)
        self.dir = ''
        self.createRadioBoxes(self)
        self.createListBoxes(self)
        self.Nterm_mods = mz_masses.Nterm_dict.keys()
        self.Nterm_mods.sort()
        self.Cterm_mods = mz_masses.Cterm_dict.keys()
        self.Cterm_mods.sort()
        self.createComboBoxes(self)
        self.createSpinBoxes(self)
        
        self.memory_bank = lb.ListBank(self, -1)
        #self.memory_bank = MemoryBank(self, -1)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.PrecPopUp, self.FindWindowByName('precursorListBox'))
        
        self.y_ions = self.b_ions = None
        
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)        
        
        self.Bind(wx.EVT_COMBOBOX, self.OnCalculate, self.FindWindowByName('ions'))
        
        self.bpc_tb = None
        prodList = self.FindWindowByName("productListBox")
        precList = self.FindWindowByName("precursorListBox")        
        prodList.Bind(wx.EVT_CONTEXT_MENU, self.OnProdContextMenu)
        precList.Bind(wx.EVT_CONTEXT_MENU, self.OnPrecContextMenu)
        
        
    def OnProdContextMenu(self, evt):
        if not hasattr(self, "popupID1"):
            self.popupCID1 = wx.NewId()
            self.popupCID2 = wx.NewId()
            self.popupCID3 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnContextPopupOne, id=self.popupCID1)
            self.Bind(wx.EVT_MENU, self.OnContextPopupTwo, id=self.popupCID2)
            self.Bind(wx.EVT_MENU, self.OnContextPopupThree, id=self.popupCID3)

        # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupCID1, "Copy b ion to Clipboard")
        menu.AppendItem(item)
        # add some other items
        menu.Append(self.popupCID2, "Copy y ion to Clipboard")
        menu.Append(self.popupCID3, "Copy all product ions to Clipboard")
        
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def sendTextToClipboard(self, text):
        text_data = wx.TextDataObject(text)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(text_data)
            wx.TheClipboard.Close()        
        
    def OnContextPopupOne(self, event):
        entry = self.FindWindowByName("productListBox").GetStringSelection()
        if entry:
            bion = entry.split(' ')[1]
            self.sendTextToClipboard(bion)

    def OnContextPopupTwo(self, event):
        entry = self.FindWindowByName("productListBox").GetStringSelection()
        if entry:
            yion = entry.split(' ')[5]
            self.sendTextToClipboard(yion)
    
    def OnContextPopupThree(self, event):
        prodList = self.FindWindowByName("productListBox")
        if prodList:
            prods = [prodList.GetString(x) for x in xrange(0, prodList.GetCount())]
            text = '\n'.join(prods)
            self.sendTextToClipboard(text)
        
    def OnContextPopupFour(self, event):
        entry = self.FindWindowByName("precursorListBox").GetStringSelection()
        if entry: 
            precursorIon = entry.split(' ')[2]
            self.sendTextToClipboard(precursorIon)    
        
    def OnContextPopupFive(self, event):
        precList = self.FindWindowByName("precursorListBox")  
        if precList:
            precs = [precList.GetString(x) for x in xrange(0, precList.GetCount())]
            text = '\n'.join(precs)
            self.sendTextToClipboard(text)    
    
    def OnPrecContextMenu(self, evt):
        if not hasattr(self, "popupID4"):
            self.popupCID4 = wx.NewId()
            self.popupCID5 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnContextPopupFour, id=self.popupCID4)
            self.Bind(wx.EVT_MENU, self.OnContextPopupFive, id=self.popupCID5)

        # make a menu
        menu = wx.Menu()
        # Show how to put an icon in the menu
        item = wx.MenuItem(menu, self.popupCID4, "Copy precursor ion to Clipboard")
        menu.AppendItem(item)
        # add some other items
        menu.Append(self.popupCID5, "Copy all precursor ions to Clipboard")
        
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def OnCopyToClipboard(self, evt):
        seq = self.FindWindowByName("sequence").GetValue()
        prodList = self.FindWindowByName("productListBox")
        precList = self.FindWindowByName("precursorListBox")
        
        if seq and prodList and precList:
            prods = [prodList.GetString(x) for x in xrange(0, prodList.GetCount())]
            precs = [precList.GetString(x) for x in xrange(0, precList.GetCount())]
            
            text = '\n'.join([seq]+ ['\n'] + prods + ['\n'] + precs)
            text_data = wx.TextDataObject(text)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(text_data)
                wx.TheClipboard.Close()
        
    def SetToolBar(self, tb):
        tsize = (24,24)
        self.AddToolBarItems(tb)
        tb.SetToolBitmapSize(tsize)
        tb.Realize() 
        
    def AddToolBarItems(self, tb):
        tsize = (24,24)
        for pos, label, art, short_help, long_help, evt_id  in self.ToolBarData():
            if pos != "sep":
                try:
                    new_bmp = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, tsize)
                except:
                    art.Rescale(*tsize)
                    new_bmp = wx.BitmapFromImage(art)
                tb.AddLabelTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=evt_id)
            else:
                tb.AddSeparator()
            
    def ToolBarData(self):
        return ((10, "Open", wx.ART_FILE_OPEN, "Open", "Long help for 'Open'", 10),
            (20, "Close", wx.ART_CLOSE, "Close", "Long help for 'Close'", 20),
            ("sep", 0, 0, 0, 0, 0),
            (150, "XIC", wx.Image(installdir + r'\image\Add new trace.png'), "XIC adds to new window", "XIC adds to new window'", 150))              
         
    def PrecPopUp(self, event):
        print "EV"
        # Show the popup right below or above the button
        # depending on available screen space...
        btn = event.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        win = PopUpWins.TestFrame(self, pos=(pos[0]+100, pos[1]))
        #win.Position(pos, (0, sz[1]))
        
        win.Show()        
    
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
        
        self.PopupMenu(menu)
        menu.Destroy()        
        
        event.Skip()
                
    def OnPopupOne(self, event):
        print "One"
        xic_mz = float(self.FindWindowByName('precursorListBox').GetStringSelection().split('=')[1].strip())
        lo = xic_mz - 0.02
        hi = xic_mz + 0.02
        currentPage = self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
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
        
    def OnPopupTwo(self, event):
        print "Two"            
    
    def RadioBoxData(self):
        return (("", ['monoisotopic', 'average'], 'masses', (10, 160), wx.DefaultSize),) #, 'average'

    def ListBoxData(self):
        return (([], 'productListBox', (10, 240), (180,250)),
                ([], 'precursorListBox', (10, 500), (140,110)))

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
        return (('nTerm', (180, 140), (100,20), ["None"] + self.Nterm_mods, 0, False, None, self),
                ('cTerm', (180, 170), (100,20), ["None"] + self.Cterm_mods, 0, False, None, self),
                ('ions', (180, 200), (70,20), ["b/y", " b/y - H2O", " b/y - phos", " b/y - 2 phos", " b/y - 3 phos", " b/y - 4 phos", "c/z"], 0, False, None, self))

    def createComboBoxes(self, panel):
        for eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel in self.ComboBoxData():
            ComboBox = self.BuildOneComboBox(panel, eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel)

    def BuildOneComboBox(self, panel, eachName, eachPos, eachSize, eachList, eachInit, eachEvent, eachHandler, eachPanel):
        ComboBox = wx.ComboBox(eachPanel, -1, size=eachSize, pos=eachPos, name=eachName, value=eachList[eachInit], choices=eachList)
        if eachEvent:
            self.Bind(wx.EVT_COMBOBOX, eachHandler, ComboBox)
        return ComboBox
        
    def ButtonData(self):
        return (("Calc", self.OnCalculate, (130, 3), (50,25), self),
                )
    
    def tbar(self,event):
        self.MakeToolBar(None)


    def MakeToolBar(self, evt):
        par = self
        par.bpc_tb = aui.AuiToolBar(self.parent.parent, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        par.bpc_tb.convertButton = wx.Button(par.bpc_tb, -1, "Convert")#,, size=(50,20)
        par.bpc_tb.Bind(wx.EVT_BUTTON, self.OnConvert, par.bpc_tb.convertButton)  
        par.bpc_tb.AddControl(par.bpc_tb.convertButton)
        par.bpc_tb.pa = re.compile('([a-z0-9\-\,]*[KR]+?)')
        par.bpc_tb.convert_dict = {"SILAC K+0 R+0":{"R":"R","K":"K"},
                                   "SILAC K+6 R+10":{"R":"sR","K":"sK"},
                                   "SILAC K+8 R+10":{"R":"sR","K":"eK"},
                                   "SILAC K+4 R+6":{"R":"silacR","K":"deutK"}
                                   }
        par.bpc_tb.choice = wx.Choice(par.bpc_tb, -1, choices=["TMT", "iTRAQ(4-plex)", "iTRAQ(8-plex)", "SILAC K+0 R+0", "SILAC K+6 R+10", "SILAC K+4 R+6", "SILAC K+8 R+10"])
        par.bpc_tb.choice.SetStringSelection("SILAC K+6 R+10")
        par.bpc_tb.AddControl(par.bpc_tb.choice)        
        par.bpc_tb.Realize()  
        self.parent.parent._mgr.AddPane(par.bpc_tb, 
                                        aui.AuiPaneInfo().Name("bpc_tb").Caption("Mod Conversion").ToolbarPane().Top().Row(2).LeftDockable(False).RightDockable(False))  
        self.parent.parent.Update()       
        self.Update()

    def OnConvert(self, evt):
        seq = self.FindWindowByName("sequence").GetValue()
        par = self
        found = par.bpc_tb.pa.findall(seq)
        if found:
            for match in found:
                res = match[-1:]
                convert_to = par.bpc_tb.convert_dict[par.bpc_tb.choice.GetStringSelection()][res]
                seq = seq.replace(match, convert_to)
            self.FindWindowByName("sequence").SetValue(seq)
        

    def CheckData(self):
        return (("Same Set/Sub Set", (300, 190), (150,20), "sameSetsubSet", True, self),
            )

    def LabelData(self):
        return (("Enter Sequence Here", (10, 10), (120,20), self),
                ("Charge States to Calculate:", (10, 115), (145,20), self),
                (r"Charge State of b\y pairs:", (10, 90), (140,20), self),
                (r"Decimals:", (10, 140), (50,20), self),
                ("N-term", (130, 140), (40,15), self),
                ("C-term", (130, 170), (40,15), self),
                ("Ions", (130, 200), (40,15), self))

    def SpinBoxData(self):
        return (("", (155, 115), (40,20), "cgStatesCalc", self, (1,100),6),
                ("", (155, 90), (40,20), "cgStatesProduct", self, (1, 100),1),
                ("", (70, 140), (40,20), "decimals", self,(1,100),4))

    def TextBoxData(self):
        return (("", (10,35), (200,50), "sequence", self),
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
    
    def is_number(self, s):
        #code from https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float
        try:
            float(s)
            return True
        except ValueError:
            return False

    def OnCalculate(self, event):
        calcType = self.FindWindowByName("masses").GetStringSelection() == 'monoisotopic'
        nterm = self.FindWindowByName("nTerm").GetValue().strip()
        cterm = self.FindWindowByName("cTerm").GetValue().strip()
        _ions = self.FindWindowByName("ions").GetValue().strip()
        
        cg_calc = self.FindWindowByName("cgStatesCalc").GetValue()
        cg_by = self.FindWindowByName("cgStatesProduct").GetValue()
        dec = self.FindWindowByName("decimals").GetValue()
        self.FindWindowByName("productListBox").Clear()
        self.FindWindowByName("precursorListBox").Clear()
        seq = self.FindWindowByName("sequence").GetValue()

        if not seq.strip():
            return

        _sub = 0
        if _ions == "b/y - H2O" or _ions.find("phos")>-1:
            if _ions == "b/y - H2O":
                _sub = (mz_masses.mass_dict[calcType]['water']/float(int(cg_by)))
            elif _ions == "b/y - phos":
                _sub = (3* mz_masses.mass_dict[calcType]['H'] + mz_masses.mass_dict[calcType]['P'] + 4* mz_masses.mass_dict[calcType]['O'])/float(int(cg_by))
            elif _ions == "b/y - 2 phos":
                _sub = (2*(3* mz_masses.mass_dict[calcType]['H'] + mz_masses.mass_dict[calcType]['P'] + 4* mz_masses.mass_dict[calcType]['O']))/float(int(cg_by)) 
            elif _ions == "b/y - 3 phos":
                _sub = (3*(3* mz_masses.mass_dict[calcType]['H'] + mz_masses.mass_dict[calcType]['P'] + 4* mz_masses.mass_dict[calcType]['O']))/float(int(cg_by))
            elif _ions == "b/y - 4 phos":
                _sub = (4*(3* mz_masses.mass_dict[calcType]['H'] + mz_masses.mass_dict[calcType]['P'] + 4* mz_masses.mass_dict[calcType]['O']))/float(int(cg_by))
            _ions = 'b/y'
        iontypes = ['b','y'] if _ions == 'b/y' else ['c','z']
        
        if nterm == "None":
            nterm = ''
        if cterm == "None":
            cterm = ''        
        
        aminos = ''.join([x for x in list(seq) if x.isupper()])        
    
        mods = []
        pa = re.compile('([a-z0-9\-.\]\[]*[A-Z]+?)')        
        modtokens = pa.findall(seq)
        for pos, segment in enumerate(modtokens, start = 1):
            if any(x.isalpha() for x in segment[:-1]) and any(x for x in segment if x.islower()):
                token = segment[:-1].strip('[]')
                aa = segment[-1:]
                if not token:
                    continue
                else:
                    assert len(aa) == 1
                    try:
                        mass = mod_lookup_table[token, aa]
                    except KeyError:
                        wx.MessageBox("No known modification %s of %s." % (token, aa))
                        return
                    mods.append((pos, mass))
            #elif segment[0] == '[' and segment[-2] == ']':
                #modstr = segment[1:-2]
                #try:
                    #mass = float(segment[:-1].strip('[]'))
                #except ValueError:
                    #mass = unimod.get_mod_delta(modstr)
                    #mods.append((pos, mass))

            elif any(x.isdigit() for x in segment):
                mass = float(segment[:-1].strip('[]'))
                mods.append((pos, mass))
            elif not len(segment)==1:
                raise ValueError, 'Parsing error on or around %s' % segment            
        
        modstrs = ['%s%d: %f' % (aminos[i-1], i, mass) for i, mass in mods]
        
        if nterm:
            if nterm.isdigit() or self.is_number(nterm):
                nmod = float(nterm)
            else:
                nmod = mz_masses.calc_mass(mz_masses.Nterm_dict[nterm])
            mods.append((0, nmod - AW['H'])) # Only one *-term mod at at time.
            nmodstr = 'N-term: %.5f' % (nmod - AW['H'])
            modstrs.append(nmodstr)
        if cterm:
            if cterm.isdigit() or self.is_number(cterm):
                cmod = float(cterm)
            else:
                cmod = mz_masses.calc_mass(mz_masses.Cterm_dict[cterm])            
            mods.append((len(aminos)+1, cmod  - (AW['H'] + AW['O'])))
            cmodstr = 'C-term: %.5f' % (cmod - (AW['H'] + AW['O']))
            modstrs.append(cmodstr)
        
        totalModMass = sum(zip(*mods)[1]) if mods else 0
        
        precmass = mw(aminos, use_monoisotopic=calcType) + totalModMass
        chgmass = ((precmass + (protonMass * cg_by)) / cg_by) 
        chgfrags = fragment(aminos, modstrs, ions = iontypes, charges = [cg_by],
                            use_monoisotopic=calcType)
        frags = {}
        for k, v in chgfrags.items():
            frags[k.strip('+')] = v
        
        if any(frags.values()):
            if _ions == 'b/y':
                b_ions = sorted(zip(*frags['b'])[1]) + [chgmass]
                y_ions = sorted(zip(*frags['y'])[1]) + [chgmass]
            elif _ions == 'c/z':
                b_ions = sorted(zip(*frags['c'])[1]) + [chgmass]
                y_ions = sorted(zip(*frags['z'])[1]) + [chgmass]            
                # Assuming that the replacement is implicit, since there's not a
                # set of c_ions and z_ions variables in the rest of the code.
            else:
                raise Exception
        else:
            b_ions = []
            y_ions = []
                
        charge_states = [precmass] + [(precmass + (protonMass*c))/c for c in range(1, int(cg_calc)+1)]
        
        
        ##First, precursor.  
        #zerocg, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = 0, Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        ##Calc +1, then the rest.
        #mz, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = 1, Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        #charge_states = []
        #for i in range(0, int(cg_calc)):
            #current = float((mz + (i*mz_masses.mass_dict["mi"]['H+'])))/float(i +1)
            #charge_states.append(current)
        #charge_states.insert(0, zerocg)
        for i, member in enumerate(charge_states):
            self.FindWindowByName("precursorListBox").Append('+' + str(i) + ' = ' + str(round(member, dec)))
        #mz, b_ions, y_ions = mz_masses.calc_pep_mass_from_residues(seq, cg = int(cg_by), Nterm=nterm, Cterm=cterm, ions=_ions, calcType=calcType)
        length = len(b_ions)
        peptide = []
        
        #peptide = pa.findall(seq)
        peptide = modtokens
        Nt = None
        Ct = None
        if _ions in ['b/y', "b/y - H2O"] or _ions.find("phos")>-1:
            Nt = 'b'
            Ct = 'y'
        elif _ions == 'c/z':
            Nt = 'c'
            Ct = 'z'
        for i, member in enumerate(b_ions):
            line = Nt + str(i+1) + ' ' + str(round(b_ions[i] - _sub,dec)) + '  ' + peptide[i] + '  ' + str(round(y_ions[length-1-i] - _sub,dec)) + ' ' + Ct + str(length-i)
            self.FindWindowByName("productListBox").Append(line)
        self.b_ions = b_ions
        self.y_ions = y_ions

    def OnClear(self, event):
        self.FindWindowByName("sequence").SetValue('')
        self.FindWindowByName("productListBox").Clear()
        self.FindWindowByName("precursorListBox").Clear()        
    
    def OnPrint(self, event):
        pass

    def OnModManager(self, event):
        self.mod_manager = ModManager.ModBank(self, -1)
        self.mod_manager.Show()

    def OnViewMemoryBank(self, event):
        #self.memory_bank = MemoryBank(self, -1)
        #self.memory_bank = lb.ListBank(self, -1)
        self.memory_bank.Show()

    #def return_mem_seq(self):
        #nterm = self.FindWindowByName("nTerm").GetValue().strip()
        #print nterm
        #cterm = self.FindWindowByName("cTerm").GetValue().strip()
        #seq = self.FindWindowByName("sequence").GetValue()
        #print seq
        #if nterm == "None":
            #nterm = 'H'
        #if cterm == "None":
            #cterm = 'OH'
        #return nterm + "-" + seq + "-" + cterm

    #def OnViewMemoryBank(self, event):
        #self.memory_bank.Show()

    def ActMem(self, event):
        if self.memory_bank:
            self.memory_bank.listb.Populate(self.return_mem_seq(), '')
        else:
            mesdog = wx.MessageDialog(self, 'Cannot import peptide to the Memory Bank when it is not active.', 
                                      'Error', wx.OK)
            mesdog.ShowModal()
            mesdog.Destroy()
        event.Skip()
        
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
        self.memory_bank.bank.Append(self.return_mem_seq())
        #except:
        #    self.memory_bank = MemoryBank(self, -1)
        #    self.memory_bank.Show()
        #    #self.memory_bank.bank.Append(self.return_mem_seq())
            
    def OnBank(self, event):
        pass

    def removeOverlay(self, event):
        currentPage = self.parent.parent.ctrl.GetPage(self.parent.parent.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]   
        scanNum = currentFile.scanNum
        if scanNum in currentFile.overlay.keys():
            del currentFile.overlay[scanNum]
            del currentFile.overlay_sequence[scanNum]
            currentFile.label_dict = {}
            currentPage.msdb.build_current_ID(currentFile.FileAbs,scanNum)
            currentPage.Window.UpdateDrawing()
            currentPage.Window.Refresh()
            currentPage.Refresh()             
            
    def OnXFer(self, event):
        if not self.y_ions and self.b_ions:
            print "Invalid command; no sequence stored."
            return
        if self.parent.parent.ctrl.GetSelection() == -1:
            print "Invalid command; no data selected."
            return
        
        currentPage = self.parent.parent.ctrl.GetPage(self.parent.parent.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]
        
        if currentFile.spectrum_style != 'AVERAGE':
            currentFilter = currentFile.filter_dict[currentFile.scanNum]
        else:
            currentFilter = currentFile.filter_dict[int(currentFile.scanNum.split('-')[0])]
            
        if 'ms2' not in currentFilter and 'ms3' not in currentFilter and 'msms' not in currentFilter:
            wx.MessageBox("Not an MS2/MS3 scan, cannot label!")
            return
        nterm = self.FindWindowByName("nTerm").GetValue().strip()
        ntermToken = None
        if nterm == u'None':
            ntermToken = 'H-'
        else:
            ntermToken = nterm
        if self.parent.labelOverwrite:      
            scanNum = currentFile.scanNum
            if scanNum not in currentFile.overlay.keys():
                currentFile.overlay[scanNum]=[self.y_ions, self.b_ions]
                currentFile.overlay_sequence[scanNum]=ntermToken + '-' + self.FindWindowByName("sequence").GetValue() + '-OH'
            else:
                orig_y = currentFile.overlay[scanNum][0]
                orig_b = currentFile.overlay[scanNum][1]
                currentFile.overlay[scanNum]=[self.y_ions + orig_y, self.b_ions + orig_b]
                currentFile.overlay_sequence[scanNum]=ntermToken + '-' + self.FindWindowByName("sequence").GetValue()+ '-OH'
            currentPage.msdb.build_current_ID(currentFile.FileAbs,scanNum)
            currentPage.Window.UpdateDrawing()
            currentPage.Window.Refresh()
            currentPage.Refresh()                
        else:
            currentPage = self.parent.parent.ctrl.GetPage(self.parent.parent.ctrl.GetSelection())
            currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]         
            scanNum = currentFile.scanNum
            currentFile.overlay[scanNum]=[self.y_ions, self.b_ions]
            currentFile.overlay_sequence[scanNum]=ntermToken + '-' + self.FindWindowByName("sequence").GetValue()+ '-OH'
            currentPage.msdb.build_current_ID(currentFile.FileAbs,scanNum)
            currentPage.Window.UpdateDrawing()
            currentPage.Window.Refresh()
            currentPage.Refresh()
        
    def OnAddIons(self, event):
        currentPage = self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]         
        scanNum = currentFile.scanNum
        currentFile.overlay[scanNum]=[self.y_ions, self.b_ions]
        currentFile.overlay_sequence=self.FindWindowByName("sequence").GetValue()
        currentPage.msdb.build_current_ID(currentFile.FileAbs,scanNum)
        currentPage.Window.UpdateDrawing()
        currentPage.Window.Refresh()
        currentPage.Refresh()    
    
    def OnClose(self, event):
        #self.organizer.removeObject(self)
        self.Destroy()    

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = BlaisPepCalc(parent=None, id=-1)
    frame.Show()
    app.MainLoop()
        