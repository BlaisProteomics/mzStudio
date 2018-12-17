import wx
#import wx.dataview as dv
import cPickle
import TreeCtrl2 as TreeCtrl
#import HTreeCtrl
from collections import defaultdict
import multiplierz.mzAPI as mzAPI
import SpecViewLite_build2 as svl
import RICviewLite_multi as rvlm

try:
    import MSO
    import win32com
except:
    pass

import time

import BlaisPepCalcSlim_aui2
import wx.lib.agw.aui as aui

import wx.lib.agw.flatmenu as FM
from wx.lib.agw.flatmenu import FlatMenu
#import flatmenu_patched as FM
#from flatmenu_patched import FlatMenu
from wx.lib.agw.artmanager import ArtManager, RendererBase, DCSaver
from wx.lib.agw.fmresources import ControlFocus, ControlPressed
from wx.lib.agw.fmresources import FM_OPT_SHOW_CUSTOMIZE, FM_OPT_SHOW_TOOLBAR, FM_OPT_MINIBAR

import os
install_dir = os.path.dirname(__file__)

global installdir
installdir = os.path.abspath(os.path.dirname(__file__))
try:
    dirName = os.path.dirname(os.path.abspath(__file__))
except:
    dirName = os.path.dirname(os.path.abspath(sys.argv[0]))

bitmapDir = os.path.join(dirName, 'bitmaps')


def writeMSP(scanData, outputPath):
    if not outputPath.lower().endswith('.msp'):
        outputPath += '.MSP'
    outputFile = open(outputPath, 'w')
    
    for specName, errata, scan in scanData:
        outputFile.write("NAME: %s\n" % specName)
        
        if errata:
            if 'Comment' in errata:
                outputFile.write("COMMENT: %s\n" % errata['Comment'])
            if 'Formula' in errata:
                outputFile.write("FORMULA: %s\n" % errata['Formula'])
            if 'MW' in errata:
                outputFile.write("MW: %s\n" % errata['MW'])
            if 'CAS' in errata:
                outputFile.write("CAS: %s\n" % errata['CAS'])
            if 'Synonym' in errata:
                synonyms = errata['Synonym']
                if isinstance(synonyms, list) or isinstance(synonyms, tuple):
                    for synonym in synonyms:
                        outputFile.write("SYNONYM: %s\n" % synonym)
                    else:
                        outputFile.write("SYNONYM: %s\n" % synonyms)
            if 'Precursor' in errata:
                outputFile.write("PRECURSORMZ: %s\n" % errata['Precursor'])
        
        outputFile.write("Num Peaks: %s\n" % str(len(scan)))
        
        prev = 0
        for mz, intensity in scan:
            outputFile.write("%s\t%s\n" % (str(mz), str(intensity)))
            #scanString = ';'.join([str(x) for x in scan[prev:index]])
            #outputFile.write(scanString + '\n')
            #prev = index
        #scanString = ';'.join([str(x) for x in scan[prev:]])
        #outputFile.write(scanString + '\n')
        print "Wrote %s" % specName
    
    outputFile.close()
    print "Complete."

class FolderEntry():
    def __init__(self, pid, experiment='', title='', folder=''):
        self.type = "Folder"
        self.pid = pid
        self.experiment = experiment
        self.title = title
        self.folder = folder

class AnalysisEntry():
    def __init__(self, pid, experiment='', title='', file_data=defaultdict(dict), display=[]):
        self.type = "Analysis"
        self.pid = pid
        self.experiment = experiment
        self.title = title
        self.file_data = file_data
        self.display=display

class RICentry():
    def __init__(self, pid, experiment='', rawfile='', data=None, sequence='', title='', xr=None, time_range=None, xic_mass_ranges=None, xic_filters=None, notes=''):
        self.type="XIC"
        self.pid = pid
        self.rawfile = rawfile
        self.title = title
        self.sequence = sequence
        self.experiment=experiment
        self.data = data
        self.xr = xr
        self.notes = notes
        self.time_range = time_range
        self.full_time_range = time_range
        self.xic_mass_ranges = xic_mass_ranges
        self.xic_filters = xic_filters
        self.lines = []
        self.text = []

class multiRICentry():
    def __init__(self, pid, experiment='', rawfile='', data=None, sequence='', title='', xr=None, time_range=None, xic_mass_ranges=None, xic_filters=None, notes='', xic_scale=[], xic_max=[], active_xic=[], xic_view=[]):
        self.type="multiXIC"
        self.pid = pid
        self.rawfile = rawfile
        self.title = title
        self.sequence = sequence
        self.experiment=experiment
        self.data = data
        self.xr = xr
        self.notes = notes
        self.time_range = time_range
        self.full_time_range = time_range
        self.xic_mass_ranges = xic_mass_ranges
        self.xic_filters = xic_filters
        self.lines = []
        self.text = []
        self.xic_scale= xic_scale
        self.xic_max = xic_max
        self.active_xic = active_xic
        self.xic_view = xic_view        

class ProteinEntry():
    def __init__(self, pid, experiment='', title='', filename=''):
        self.type="Protein Coverage Map"
        self.pid = pid
        self.title = title
        self.experiment=experiment
        self.filename = filename

class FileEntry():
    def __init__(self, pid, experiment='', title='', filename=''):
        self.type="AuxFile"
        self.pid = pid
        self.title = title
        self.experiment=experiment
        self.filename = filename

class BaseEntry():
    def __init__(self, pid, sequence='', varmod='', fixedmod='', rawfile='', charge=0, filter='', title='', detector="IT", display_range=[], full_range=[], mass_ranges=[] ,axes=1, experiment='', scan=1, notes='', massList='', scan_data=None, cent_data = None, vendor='Thermo',profile=False, scan_type="MS2", mascot_score=None, processed_scan_data=None, viewProcData=False, viewCent=False):
        self.type = "Spectrum"
        self.sequence = sequence
        self.varmod = varmod
        self.fixedmod=fixedmod
        self.rawfile = rawfile
        self.charge = charge
        self.display_range = display_range
        self.mass_ranges = mass_ranges
        self.axes = axes
        self.experiment = experiment
        self.scan = scan
        self.notes = notes
        self.massList = massList
        self.title=title
        self.pid = pid
        self.mascot_score = mascot_score
        self.scan_data = scan_data
        self.cent_data = cent_data
        self.profile = profile
        self.vendor = vendor
        self.full_range = full_range
        self.scan_type = scan_type
        self.detector = detector
        self.rxn_type = "CAD"
        self.notes = ""
        self.filter=filter
        self.scan_type = scan_type
        self.lines = []
        self.text = []
        self.processed_scan_data = processed_scan_data
        self.viewProcData = viewProcData
        self.viewCent = viewCent
        print "ID assigned: " + str(self.pid)

    def __str__(self):
        print "Sequence: " +str(self.sequence)
        print "Rawfile: " + str(self.rawfile)
        print "ID: " + str(self.pid)

class MyFileDropTarget(wx.FileDropTarget):
    '''
    
    Test for drag and drop.  Not used.  Use data composite instead.
    
    '''
    def __init__(self,window):
        wx.FileDropTarget.__init__(self)
        self.window=window
        
    def OnDropFiles(self, x, y, filenames):
        for filename in filenames:
            print filename

class MySpectrumDropTarget(wx.DropTarget):
    '''
        
    Test for drag and drop.  Not used.  Use data composite instead.
        
    '''    
    
    def __init__(self, window):
        wx.DropTarget.__init__(self)
        self.window = window
        self.data = wx.CustomDataObject("scan_data")
        self.SetDataObject(self.data)        
    
    def OnDrop(self, x, y):
        print "Data dropped"
        print x
        print y
        #print spectrum
        
    def OnData(self, x, y, d):
        
        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list of lines and give it to the viewer
            data = self.data.GetData()
            scan_data = cPickle.loads(data)
        
        print "Scan data received"    
        #print scan_data   
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d    

class YourDropTarget(wx.PyDropTarget):
    """Implements drop target functionality to receive files, bitmaps and text"""
    def __init__(self, window):
        wx.PyDropTarget.__init__(self)
        self.do = wx.DataObjectComposite()  # the dataobject that gets filled with the appropriate data
        self.filedo = wx.FileDataObject()
        self.textdo = wx.TextDataObject()
        self.bmpdo = wx.BitmapDataObject()
        self.specdo = wx.CustomDataObject("scan_data")
        self.do.Add(self.filedo)
        self.do.Add(self.bmpdo)
        self.do.Add(self.textdo)
        self.do.Add(self.specdo)
        self.SetDataObject(self.do)
        self.window = window


    def OnData(self, x, y, d):
        """
        Handles drag/dropping files/text or a bitmap
        """
        if self.GetData():
            df = self.do.GetReceivedFormat().GetType()
            print
            if df in [wx.DF_UNICODETEXT, wx.DF_TEXT]:

                text = self.textdo.GetText()

            elif df == wx.DF_FILENAME:
                for name in self.filedo.GetFilenames():
                    #Want to add file as a child to that node
                    node = self.window.tc.tree.GetSelection()
                    item = self.window.tc.tree.AppendItem(node, os.path.basename(name))
                    self.window.tc.tree.SetItemData(item, {"type":"auxfile", "flag":"experiment", "exp":'Title', 'full_path':name})
                    #Node should be added to node dict after treerefresh
                    
                    self.window.TreeRefresh()
                                   
                    #print name

            elif df == wx.DF_BITMAP:
                bmp = self.bmpdo.GetBitmap()

            #elif df == 50092 or df == 49894:
            else:
                # This part is structured to ensure that nothing happens if 
                # the drop doesn't have proper pyData or the '.type' member
                # isn't set appropriately.
                #---------------------------------TITLE = "mass spectrum""
                #---------------------------------'exp' = 'Title' - this is what appears in title bar.
                #---------------------------------This code sets item text as infobar, which is the sequence
                #---------------------------------InsertItems setlabeltext as 'label'
                #---------------------------------SaveItems Getlabeltext and saves as 'label'
                try:
                    print "SPECRUM DROP"
                    data = self.specdo.GetData()
                    dropped_obj = cPickle.loads(data)
                    node = self.window.tc.tree.GetSelection()
                    dropped_obj.type
                except (EOFError, TypeError, AttributeError):
                    return
                
                if dropped_obj.type == "Spectrum":
                    
                    infobar = dropped_obj.sequence 
                    item = self.window.tc.tree.AppendItem(node, infobar) 
                
                    be = BaseEntry(None, sequence=dropped_obj.sequence, filter=dropped_obj.filter, title="Mass Spectrum", charge=dropped_obj.charge, 
                               full_range=dropped_obj.display_range, mass_ranges=dropped_obj.mass_ranges, scan=dropped_obj.scan, 
                               scan_data=dropped_obj.scan_data, cent_data=dropped_obj.cent_data, vendor=dropped_obj.vendor, detector=dropped_obj.detector, profile=dropped_obj.profile, 
                               scan_type=dropped_obj.scan_type, varmod=dropped_obj.varmod, fixedmod=dropped_obj.fixedmod, mascot_score=dropped_obj.score, 
                               processed_scan_data=dropped_obj.processed_scan_data)
                
                    self.window.tc.tree.SetItemData(item, {"type":"specfile", "flag":"experiment", "exp": 'Title', "spectrum_data": be, "raw_spec": dropped_obj})  #self.window.tc.tree.GetItemText(node)
                    #Do we need a base entry?  Why not just pass the spec object?
                    self.window.TreeRefresh()
                
                if dropped_obj.type == "XIC":
                    #------------------------------Titlebar is data['exp']
                    #------------------------------xic_data.title = Infobar
                    item = self.window.tc.tree.AppendItem(node, "XIC") 
                    
                    mxe = multiRICentry(None, rawfile=dropped_obj.rawfile, data=dropped_obj.data, sequence='', title='XIC', xr=dropped_obj.xr, time_range=dropped_obj.time_range, 
                                        xic_mass_ranges=dropped_obj.xic_mass_ranges, xic_filters=dropped_obj.xic_filters, notes='', xic_scale=dropped_obj.xic_scale, 
                                        xic_max=dropped_obj.xic_max, active_xic=dropped_obj.active_xic, xic_view=dropped_obj.xic_view)
                    
                    self.window.tc.tree.SetItemData(item, {"type":"XIC", "flag":"experiment", "exp":'Title', "xic_data": mxe, "raw_xic": dropped_obj})
                    #Do we need a base entry?  Why not just pass the spec object?
                    self.window.TreeRefresh()                    
                
        return d  # you must return this

class SpecFrame(wx.Panel, wx.DropTarget):  #, wx.DropTarget
    def __init__(self, parent, id, organizer):
        wx.Panel.__init__(self, parent, id=id, name='SpecBase', size =(650,660), pos = (50,50))
             
        #-------------     
        #self.data = wx.CustomDataObject("scan data")
        #self.SetDataObject(self.data)
        
        #ft = MyFileDropTarget(self)
        #self.SetDropTarget(ft)
        
        #dt = MySpectrumDropTarget(self)
        #self.SetDropTarget(dt)        
        
        dt = YourDropTarget(self)
        self.SetDropTarget(dt)
        #-------------
        
        self.organizer = organizer
        self.organizer.addObject(self)
        self.NamedFile = None
        self.parent = parent
        
        self.aui_pane_obj = None # Set by DrawPanel after initialization.
        
        self.db = None
        self.NameFile = None
        self.bpc = None
        self.created = False
        
        self._CreateMenu()
        #self.panel = wx.Panel(self)       
        
        self.tc = tc = TreeCtrl.TestTreeCtrlPanel(self, -1, self) #Put tree control in "self" panel
        self.TreeSizer = wx.BoxSizer()
        self.TreeSizer.Add(tc, 1, wx.EXPAND)
        #self.panel.SetSizerAndFit(self.TreeSizer)
        self.tc.tree.DeleteAllItems()        
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.menubar, 0, wx.EXPAND)
        main_sizer.Add(self.TreeSizer, 1, wx.EXPAND)

        self.SetSizer(main_sizer)
        main_sizer.Layout()
        self.Refresh()
        self.Update()
        self.menubar.Refresh()
        
        self.Bind(wx.EVT_KEY_DOWN, self.interceptTwo)
        
        #self.panel.Update()
        #self.panel.Refresh()
        
        #self.Bind(wx.EVT_CLOSE, self.OnClose, self)
        #self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSED, self.OnClose, self)
        

    def interceptTwo(self, event):
        if key == 50:
            return
        else:
            event.Skip()

    def addMenuItem(self, menu, id, title, helpText, itemType, handler):
        item = menu.Append(id, title, helpText, itemType)
        self.Bind(wx.EVT_MENU, handler, item)

    def _CreateMenu(self):
    
        self.menubar = FM.FlatMenuBar(self, -1) #, options=FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR

        f_menu = FlatMenu()
        a_menu = FlatMenu()
        e_menu = FlatMenu()
        export_menu = FlatMenu()
        b_menu = FlatMenu()
        database_menu = FlatMenu()
        #close_menu = FlatMenu()
        # Append the menu items to the menus
        
        # Basic menu option doesn't seem to allow attaching the 
        # menu to a panel.
        #self.menubar = wx.MenuBar()
        #self.menubar.Attach(self)
        #f_menu = wx.Menu()
        #a_menu = wx.Menu()
        #e_menu = wx.Menu()
        #export_menu = wx.Menu()
        #b_menu = wx.Menu()
        #database_menu = wx.Menu()
        #close_menu = wx.Menu()        
        
        # (self.a_menu_data(), a_menu),
        for data in [(self.f_menu_data(), f_menu), (self.e_menu_data(), e_menu), (self.a_menu_data(), a_menu), 
                     (self.export_menu_data(), export_menu), 
                     (self.b_menu_data(), b_menu), (self.database_menu_data(), database_menu)]:
                     #(self.close_menu_data(), close_menu)]:
            
            for id, title, helpText, itemType, handler in data[0]:
                self.addMenuItem(data[1], id, title, helpText, itemType, handler)        
                
        
        # Append menus to the menubar
        self.menubar.Append(f_menu, "File")
        self.menubar.Append(a_menu, "Add")        
        self.menubar.Append(e_menu, "Edit")
        self.menubar.Append(export_menu, "Export Images")
        self.menubar.Append(b_menu, "PepCalc") 
        self.menubar.Append(database_menu, "Export Spectra")
        #self.menubar.Append(close_menu, "Close")
        
        #self.menubar.SetAcceleratorTable(wx.AcceleratorTable ([(wx.ACCEL_CTRL, ord('Q'), 231)]))
        #open = wx.Bitmap(os.path.join(os.path.dirname(__file__), 'image', 'open_bank.bmp'), wx.BITMAP_TYPE_BMP)
        #self.menubar.AddTool(20, "Open Memory Bank", open)
        #self.menubar.Bind(wx.EVT_TOOL, self.OnToolClick, id = 20)
        
    def OnToolClick(self, evt):
        if evt.GetId() == 20:
            print "tool click"   

    def UpdateSpecBaseData(self):
        self.db.td = self.tc.tree.SaveItemsToList(self.tc.root)
        #print self.db.td
        
    def f_menu_data(self):
        return [(-1, "New", "Text", None, self.OnCreate), (-1, "Load", "Load a specbase file", None, self.OnLoad),
                  (-1, "Save", "Save specbase file", None, self.OnSave), (-1, "Save as ...", "Save as a different Filename", None, self.OnSaveAs)]
    
    #def a_menu_data(self):
    #    return [(-1, "Add Spectrum", "Text", None, self.OnAdd), (-1, "Add Folder", "Load a specbase file", None, self.OnAddFolder),
    #              (-1, "Add Auxiliary File", "Save specbase file", None, self.OnAddAux), (-1, "Add Protein", "Save as a different Filename", None, self.OnAddFolder)]   
    
    def a_menu_data(self):
        return [(-1, "New Folder", "Add Folder", None, self.OnAddFolder), (-1, "Add New File (.PPT/.XLS/.PY)", "Add Auxiliary File", None, self.OnAddAux)]   #, (-1, "Add Database File", "Add database file", None, self.OnAddDb)
    
    def OnAddDb(self, evt):
        pass
    
    def OnAddScript(self, evt):
        pass
    
    def e_menu_data(self):
        return [(-1, "Edit", "Edit entry", None, self.OnEdit), (-1, "Delete Entry", "Delete entry", None, self.OnDelete)]

    def export_menu_data(self):
        return [(-1, "Export to PPT", "Export all spectra to ppt", None, self.OnPPT), (-1, "Export current to PPT", "Export only current slide to ppt", None, self.CurrentSlidetoPPT)]
        
    def b_menu_data(self):
        return [(-1, "Open PepCalc", "Open PepCalc", None, self.OnOpenBPC),]
    
    def close_menu_data(self):
        return [(-1, "Close", "Close", None, self.OnClose)]
    
    def database_menu_data(self):
        return [(-1, "Make Spectral Database", "Make spectral database from all MS2 spectra", None, self.OnMakeSpectralDatabase),]    

    def OnOpenBPC(self, event):
        if not self.organizer.containsType(BlaisPepCalcSlim_aui2.MainBPC):
            import wx.lib.agw.aui as aui
            bpc = BlaisPepCalcSlim_aui2.MainBPC(self.parent, -1, self.organizer)         
            self.parent._mgr.AddPane(bpc, aui.AuiPaneInfo().Left().MaximizeButton(True).MinimizeButton(True).Caption("PepCalc"))
            self.parent._mgr.Update()            
        else:
            wx.MessageBox("Pep calc already open!")
        

    def OnMakeSpectralDatabase(self, event):
        if not self.tc.tree.GetRootItem().IsOk():
            wx.MessageBox("No Items to make database from!")
            return
        #if event.GetInt() == 118: # 2 key?2
        #    event.Skip()
        #    return
        
        filedialog = wx.FileDialog(self, 'Save MSP file as...', style = wx.FD_SAVE)
        if filedialog.ShowModal() == wx.ID_OK:
            outputfile = filedialog.GetPath()
        else:
            print "Aborted MSP save."
            return
        
        data_items = self.tc.get_data_items()
        scanData = []
        for member in data_items:
            if member[0]=='specfile':
                 
                spectrum = member[1]
                 
                scan = spectrum.scan_data
                seq = spectrum.sequence
                name = member[2]['data']['exp']
                details = {'Comment': '%s|%s' % (seq, name)}
                scanData.append((name, details, scan))        
                 
        writeMSP(scanData, outputfile)
         
        print "Make Spectral Database"
        wx.MessageBox("Spectral database construction complete.", "Making Spectral Library")

    def OnDelete(self, event):
        item=self.tc.tree.GetSelection()
        if self.tc.tree.GetFirstChild(item)[0].IsOk():
            dlg = wx.MessageDialog(self, "Are you sure you want to delete Proceed to delete all sub-nodes?", 'Delete all nodes?', wx.YES_NO | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                if item != self.tc.tree.GetRootItem():
                    self.tc.tree.Delete(item)
                else:
                    self.tc.tree.DeleteAllItems()
            dlg.Destroy()
            return
        else:
            self.tc.tree.Delete(item)

    def OnEditItem(self, event):
        print "EDIT!"
        item=self.tc.GetSelection()
        #print item
        if item:
            self.tc.EditLabel(item)

    def CurrentSlidetoPPT(self, event):
        
        filename, dir = get_single_file("Select file...", wx_wildcard = "PPT files (*.ppt)|*.ppt")
        if not filename.endswith('ppt'):
            filename += '.ppt'
        tmp = os.path.join(install_dir, r'image\Temp.png')
        App = win32com.client.Dispatch("PowerPoint.Application")
        Pres = App.Presentations.Add()
             
        item=self.tc.tree.GetSelection()
        try:
            pid = self.tc.tree.GetItemData(item)['type']    
        except wx._core.PyAssertionError:
            messdog = wx.MessageDialog(self, 'No valid data is currently selected', 
                                       'Could access SpecBase data', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return            
        
        data_type = self.tc.tree.GetItemData(item)['type']
        if data_type == 'specfile':
            frame = svl.SpecViewLitePanel(None, self.tc.tree.GetItemData(item)['spectrum_data'])
            frame.Show()
            frame.Refresh()       
            wx.Yield()
            time.sleep(0.5) 
            frame.SpecWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
            print "SAVED!"
            frame.Destroy()
            Slide = Pres.Slides.Add(1,12)
            Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490) 
            Pres.SaveAs(filename)
            Pres.Close()
            App.Quit()                      
        
        if data_type == "XIC":
            frame = rvlm.RICviewLitePanel(None, self.tc.tree.GetItemData(item)['xic_data'])
            frame.Show()
            frame.Refresh()       
            wx.Yield()
            time.sleep(0.5)
            frame.XICWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
            frame.Destroy()
            Slide = Pres.Slides.Add(1,12)
            Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
            Pres.SaveAs(filename)
            Pres.Close()
            App.Quit()                

    def OnPPT(self, event):
        if not self.tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'There is no initialized SpecBase instance.', 
                                       'Could not access SpecBase data', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return
        
        
        LabelMascotScore = False
        filename, dir = get_single_file("Select file...", wx_wildcard = "PPT files (*.ppt)|*.ppt")
        if not filename:
            return
        if not filename.endswith('ppt'):
            filename += '.ppt'
        tmp = os.path.join(install_dir, r'image\Temp.png')
        App = win32com.client.Dispatch("PowerPoint.Application")
        Pres = App.Presentations.Add()
        
        data_items = self.tc.get_data_items()
        
        for member in data_items:
            if member[0]=='specfile':
                spectrum = member[1]
                frame = svl.SpecViewLitePanel(None, spectrum)
                frame.Show()
                frame.Refresh()
                wx.Yield()
                time.sleep(0.5)
                frame.SpecWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
                frame.Destroy()
                Slide = Pres.Slides.Add(1,12)
                Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
                
                if LabelMascotScore:
                    shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=10, Width = 750, Height = 40 )
                    shape.TextFrame.TextRange.Text = spectrum.sequence + "  Mascot Score: " + str(spectrum.mascot_score) #+' (' + spectrum.title + ')' 
                else:
                    shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=10, Width = 750, Height = 40 )
                    shape.TextFrame.TextRange.Text = spectrum.sequence
                    
                shape.TextFrame.TextRange.Font.Size=10
                shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=40, Width = 750, Height = 40 )
                shape.TextFrame.TextRange.Text = spectrum.notes   
                shape.TextFrame.TextRange.Font.Size=10                
    
            if member[0]=='XIC':
                xic=member[1]
                frame = rvlm.RICviewLitePanel(None, xic)
                frame.Show()
                frame.Refresh()
                wx.Yield()
                time.sleep(0.5)
                frame.XICWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
                frame.Destroy()
                Slide = Pres.Slides.Add(1,12)
                Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
                shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=40, Width = 750, Height = 40 )
                shape.TextFrame.TextRange.Text = xic.title   
                shape.TextFrame.TextRange.Font.Size=10                    
                                
        Pres.SaveAs(filename)
        Pres.Close()
        App.Quit()        

    def Create_Image_List(self):
        isz = (16,16)
        il = wx.ImageList(*isz)
        fldridx     = il.Add(wx.ArtProvider.GetIcon(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider.GetIcon(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider.GetIcon(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        spec = il.Add(wx.Bitmap(os.path.join(bitmapDir, "spectrum.png"), wx.BITMAP_TYPE_PNG))
        xl = il.Add(wx.Bitmap(os.path.join(bitmapDir, "th.png"), wx.BITMAP_TYPE_PNG))
        ppt = il.Add(wx.Bitmap(os.path.join(bitmapDir, "ppt.png"), wx.BITMAP_TYPE_PNG))
        py = il.Add(wx.Bitmap(os.path.join(bitmapDir, "py.png"), wx.BITMAP_TYPE_PNG))
        xic = il.Add(wx.Bitmap(os.path.join(bitmapDir, "x2.png"), wx.BITMAP_TYPE_PNG))
        #onenote = il.Add(wx.Bitmap(os.path.join(bitmapDir, "onenote.png"), wx.BITMAP_TYPE_PNG))
        onenote = il.Add(wx.Bitmap(os.path.join(bitmapDir, "x2.png"), wx.BITMAP_TYPE_PNG))
        
        self.tc.tree.SetImageList(il)
        self.il = il        

    def OnCreate(self, event):
        self.tc.tree.DeleteAllItems()
        dialog = wx.TextEntryDialog(None, "Project Name", "Project Name", "", style=wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_OK:
            #sb = SpecBase(dialog.GetValue())
            #self.db = sb
            self.Create_Image_List()
            #---------------------------------------------------------
            #Add the root
            #self.tc.root = self.tc.tree.AddRoot(dialog.GetValue())
            self.tc.tree.SetItemText(self.tc.tree.GetRootItem(), 0, dialog.GetValue())
            
            self.tc.tree.SetItemData(self.tc.tree.GetRootItem(), {"type":"root", "flag":"root"})
            self.tc.tree.SetItemImage(self.tc.tree.GetRootItem(), 0, wx.TreeItemIcon_Normal)
            self.tc.tree.SetItemImage(self.tc.tree.GetRootItem(), 1, wx.TreeItemIcon_Expanded)            
            
            #self.tc.tree.AddColumn("Info Bar")
            #self.tc.tree.AddColumn("Title")
            #self.tc.tree.AddColumn("Info")
            #self.tc.tree.SetMainColumn(0) # the one with the tree in it...
            self.tc.tree.SetColumnWidth(0, 250)
            self.tc.tree.SetColumnWidth(1, 250)                
            
            self.TreeRefresh()
        event.Skip()

    def OnAdd(self, event):
        if not self.tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'There is no initialized SpecBase instance.', 
                                       'Could not add to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return
            
        Addit = AddFrame(self, id=-1, db=self.db)
        Addit.Show()

    def OnAddAux(self,event):
        if not self.tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'There is no initialized SpecBase instance.', 
                                       'Could not add to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return
        
        Addit = AddAuxFrame(self, id=-1, db=self.db)
        Addit.Show()

    def OnAddFolder(self,event):
        if not self.tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'Create a new project first!', 
                                       'Could not add to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return
        node = self.tc.tree.GetSelection()
        item = self.tc.tree.AppendItem(node, "New folder")
        self.tc.tree.SetItemData(item, {"type":"container", "flag":"folder", "exp":'folder'}) 
        icon = 0
        self.tc.tree.SetItemImage(item, icon, wx.TreeItemIcon_Normal)        
        self.TreeRefresh()
        #Addit = AddFolderFrame(self, id=-1, db=self.db)
        #Addit.Show()

    def TreeRefresh(self):

        #--------------------------------------------------------
    
        a = self.tc.tree.SaveItemsToList(self.tc.tree.GetRootItem())
        self.tc.tree.DeleteAllItems()

        #self.root = self.tc.tree.AddRoot(a[0]['label'])
        self.root = self.tc.tree.GetRootItem()
        self.tc.tree.SetItemData(self.root, {"type":"root"})
        #self.tc.tree.SetItemImage(self.root, 0, wx.TreeItemIcon_Normal)
        #self.tc.tree.SetItemImage(self.root, 1, wx.TreeItemIcon_Expanded)
        #self.tree.SetItemText(self.root, "Sequence", 1)      
        self.tc.tree.Expand(self.root)
        self.tc.tree.expanditems = []
        self.tc.tree.selected = None
        #self.tree.first_vis = self.tree.GetFirstVisibleItem()
        #self.sp = self.GetScrollPos(0)
        new_items = self.tc.tree.InsertItemsFromList(a, self.root, insertafter=None, appendafter=False)
        #print new_items
        #print self.tree.expanditems
        #print 
        for member in self.tc.tree.expanditems:
            self.tc.tree.Expand(member)
        if self.tc.tree.selected:
            self.tc.tree.SelectItem(self.tc.tree.selected)        

    def OnBeginDrag(self,event):
        print "Begin!"
        event.Allow()

    def OnDrag(self,event):
        print "Drag!"

    def OnEdit(self,event):
        #-----------------------------------------------------
        # MAIN EDIT FRAME
        #-----------------------------------------------------
        item=self.tc.tree.GetSelection()
        if item.IsOk():
            data = self.tc.tree.GetItemData(item)
            if 'spectrum_data' in data.keys():
                cur_obj = data['spectrum_data']
                Edit = EditFrame(self, id=-1, obj=cur_obj, item=item)
                Edit.Show()
            if 'xic_data' in data.keys():
                cur_obj = data['xic_data']
                Edit = EditXICFrame(self, id=-1, obj=cur_obj, item=item)
                Edit.Show()         
            #if cur_obj.type == "AuxFile":
            #    Edit = EditAuxFrame(self, id=-1, obj=cur_obj, item=item)
            #    Edit.Show()                     
        else:
            wx.MessageBox("Cannot Edit Object!")

    def OnLoad(self, event):
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.FD_OPEN, wildcard = "SpecBrary files (*.sbr)|*.sbr|Any|*")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            self.loaddir = dir
            self.loadfilename = filename       
            pickle_file = open(dir + '\\' + filename, "r")
            data = cPickle.load(pickle_file)
            pickle_file.close()
            self.NamedFile = dir + '\\' + filename
            self.tc.tree.DeleteAllItems()
            self.Create_Image_List()
            self.root = self.tc.tree.AddRoot(data[0]['label'])
            self.tc.tree.SetItemData(self.root, {"type":"root"})     
            self.tc.tree.Expand(self.root)
            self.tc.tree.expanditems = []
            self.tc.tree.selected = None
            new_items = self.tc.tree.InsertItemsFromList(data, self.root, insertafter=None, appendafter=False)
           
            for member in self.tc.tree.expanditems:
                self.tc.tree.Expand(member)
            if self.tc.tree.selected:
                self.tc.tree.SelectItem(self.tc.tree.selected)                
        else:
            return
    

    def OnSave(self, event):
        if self.NamedFile:
            pickle_file = open(self.NamedFile, "w")
            data = self.tc.tree.SaveItemsToList(self.tc.tree.GetRootItem())
            cPickle.dump(data, pickle_file)
            pickle_file.close()
        else:
            self.OnSaveAs(None)

    def OnSaveAs(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "SpecBrary files (*.sbr)|")
        
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()            
            self.savedir = dir
            self.savefilename = filename
            if not filename.endswith(".sbr"): filename += '.sbr'
            pickle_file = open(dir +'\\' + filename, "w")
            data = self.tc.tree.SaveItemsToList(self.tc.tree.GetRootItem())
            cPickle.dump(data, pickle_file)
            pickle_file.close()
            self.NamedFile = dir +'\\' + filename
            dlg.Destroy()
        else:
            return

    def OnHelp(self, event):
        pass
    
    def OnClose(self, event):
        #try:
        #    del self.organizer.ActiveObjects[type(self)]
        #except:
        #    pass
        
        self.organizer.removeObject(self)
        assert not self.organizer.containsType(self)
        print "Process close from SpecStylus1"        
        
        #mgr = self.parent._mgr
        #mgr.ClosePane(self.aui_pane_obj)
        #self.Destroy()
        #mgr.Update()
        # Does this have to communicate with the AUI notebook?

class AddFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Spectrum', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.tc.get_folders())), (0, 1), (1,8) )
        for i,c in enumerate(['Sequence', 'Title', 'Varmods', 'Rawfile', 'Scan', 'Axes', 'Display Range', 'Filter', 'Fixedmods', 'Mascot Score']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT), (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c), (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        grab_spec_btn = wx.Button(panel, -1, 'Grab Spectrum')
        gbs.Add( add_files_btn, (11,0) )
        
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        
        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        
        self.parent = parent
        self.parent.TreeRefresh()
        self.display_range = []
        self.mass_ranges = []
        self.charge = 0
        self.cent_data = []
        
    def on_click_add(self, event):
        mod_dict = {'iTRAQ4plex': 'iTRAQ',
                    'TMT6plex': 'TMT',
                    'iTRAQ8plex': 'iTRAQ8plex',
                    'HGly-HGly': 'HCGlyHCGly',
                    'HCGly-HCGly': 'HCGlyHCGly',
                    'HCGly-HCGly-HCGly-HCGly': 'HCGlyHCGlyHCGlyHCGly',
                    'HNGly-HNGly': 'HNGlyHNGly',
                    'LbA-LbA': 'LbALbA',
                    'Acetyl': 'Acetyl'}
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        varmod = self.FindWindowByName("Varmods").GetValue().strip()
        fixedmod = self.FindWindowByName("Fixedmods").GetValue().strip()
        mascot_score = self.FindWindowByName("Mascot Score").GetValue().strip()
        nterm = "H-"
        cterm = '-OH'
        for mod in fixedmod.split(","):
            mod = mod.strip()
            if mod.find("N-term") > -1:
                mod = mod.split(" ")[0]
                mod = mod.strip()
                nterm = mod_dict[mod] + '-'
        for mod in varmod.split(";"): #N-term: Acetyl
            mod = mod.strip()
            if mod.find("N-term") > -1:
                mod = mod.split(" ")[1]
                mod = mod.strip()
                nterm = mod_dict[mod] + '-'
        if self.FindWindowByName("Sequence").GetValue().strip().find("None")>-1:
            seq = self.FindWindowByName("Sequence").GetValue().strip()
        else:
            seq = nterm + self.FindWindowByName("Sequence").GetValue().strip() + cterm
        title = self.FindWindowByName("Title").GetValue().strip()
        scan = self.FindWindowByName("Scan").GetValue().strip()
        filter = self.FindWindowByName("Filter").GetValue().strip()
        rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        self.db.addItem(exp, seq, title, scan, rawfile, self.scan_data,
                        self.display_range, self.mass_ranges, self.charge,
                        filter, self.cent_data, self.vendor, self.detector,
                        self.profile, self.scan_type, varmod=varmod, 
                        fixedmod=fixedmod, mascot_score=mascot_score, processed_scan_data=self.processed_scan_data)
        
        self.parent.TreeRefresh()
        self.Destroy()

class EditFrame(wx.Frame):
    def __init__(self, parent, id, obj, item):
        wx.Frame.__init__(self, parent, id, 'Edit Entry', size =(450,220), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(4, 2)
      
        for i,c in enumerate(['Sequence', 'Title', 'Varmods']):   #for i,c in enumerate(['Sequence', 'Title', 'Varmods', 'Rawfile', 'Scan', 'Axes', 'Display Range', 'Filter']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT), (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c, size = (350, 25)),(i+1, 1), (1,8))#size=(250, 25) 
        add_files_btn = wx.Button(panel, -1, 'Update')
        #grab_spec_btn = wx.Button(panel, -1, 'Grab Spectrum')
        gbs.Add( add_files_btn, (0,3))
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_update)
        #grab_spec_btn.Bind(wx.EVT_BUTTON, self.on_click_grab)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        #self.db = db
        self.parent = parent
        #self.db.Rebuild_Order_from_tree(parent)
        #self.FindWindowByName("Experiment").SetValue(obj.experiment)
        self.FindWindowByName("Sequence").SetValue(obj.sequence)
        data = self.parent.tc.tree.GetItemData(item)
        self.FindWindowByName("Title").SetValue(data['exp'])
        #self.FindWindowByName("Scan").SetValue(str(obj.scan))
        #self.FindWindowByName("Filter").SetValue(obj.filter)
        #self.FindWindowByName("Rawfile").SetValue(obj.rawfile)
        #self.FindWindowByName("Varmods").SetValue(obj.varmod)
        self.obj = obj
        self.item = item

    def on_click_update(self, event):
        #self.obj.experiment = self.FindWindowByName("Experiment").GetValue().strip()
        self.obj.sequence = self.FindWindowByName("Sequence").GetValue().strip()
        self.obj.title = self.FindWindowByName("Title").GetValue().strip()
        #self.obj.scan = self.FindWindowByName("Scan").GetValue().strip()
        #self.obj.filter = self.FindWindowByName("Filter").GetValue().strip()
        #self.obj.rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        self.obj.varmod = self.FindWindowByName("Varmods").GetValue().strip()
        pid = self.obj.pid
        data = self.parent.tc.tree.GetItemData(self.item)
        data['exp']=self.obj.title
        item = self.parent.tc.tree.GetSelection()
        self.parent.tc.tree.SetItemText(item, self.obj.sequence, 0)
        self.parent.TreeRefresh()
        self.Destroy()

class EditXICFrame(wx.Frame):
    def __init__(self, parent, id, obj, item):
        wx.Frame.__init__(self, parent, id, 'Edit XIC Entry', size =(400,180), pos = (50,50))   #obj.title = 'XIC' pydata['exp']='Title'
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(4, 4)
        #gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        #gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value=obj.experiment, choices=list(parent.db.getExperimentNames())), (0, 1), (1,8) )
        for i,c in enumerate(['Infobar', 'Title']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT), (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c, size=(350, 25) ), (i+1, 1), (1,8))#
        add_files_btn = wx.Button(panel, -1, 'Update')
        gbs.Add( add_files_btn, (0,3) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_update)
        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.parent = parent
        #------------------------------Titlebar is data['exp']
        #------------------------------xic_data.title = Infobar        
        #self.FindWindowByName("Experiment").SetValue(obj.experiment)
        info = self.parent.tc.tree.GetItemText(item, 0)
        #self.FindWindowByName("Sequence").SetValue(obj.sequence)
        self.FindWindowByName("Infobar").SetValue(obj.title)  #Infobar
        data = parent.tc.tree.GetItemData(item)
        self.FindWindowByName("Title").SetValue(data['exp']) # Titlebar
        #self.FindWindowByName("Filter").SetValue(obj.filter)
        #self.FindWindowByName("Rawfile").SetValue(obj.rawfile)
        self.obj = obj
        self.item = item
        
    def on_click_update(self, event):
        #self.obj.experiment = self.FindWindowByName("Experiment").GetValue().strip()
        #self.obj.sequence = self.FindWindowByName("Sequence").GetValue().strip()
        self.obj.title = self.FindWindowByName("Infobar").GetValue().strip()
        #self.obj.filter = self.FindWindowByName("Filter").GetValue().strip()
        #self.obj.rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        pid = self.obj.pid
        
        data = self.parent.tc.tree.GetItemData(self.item)
        data['exp']=self.FindWindowByName("Title").GetValue().strip()
        item = self.parent.tc.tree.GetSelection()
        self.parent.tc.tree.SetItemText(item, self.obj.title, 0)
        self.parent.TreeRefresh()
        self.Destroy()
        
class EditAuxFrame(wx.Frame):
    def __init__(self, parent, id, obj, item):
        wx.Frame.__init__(self, parent, id, 'Edit Entry', size =(300,300), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(3, 3)
        gbs.Add( wx.StaticText(panel, -1, 'Title', style=wx.ALIGN_RIGHT), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.TextCtrl(panel, -1, obj.title, name = 'Title'), (0, 1))
        gbs.Add( wx.StaticText(panel, -1, 'Path', style=wx.ALIGN_RIGHT), (1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.TextCtrl(panel, -1, obj.filename, name = 'Path'), (1, 1))        
        
        add_files_btn = wx.Button(panel, -1, 'Browse')
        gbs.Add( add_files_btn, (1,2) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.onBrowse)
        add_files_btn = wx.Button(panel, -1, 'Update')
        gbs.Add( add_files_btn, (2,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_update)        
        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.parent = parent
        
        self.obj = obj
        self.item = item
        
    def onBrowse(self, event):
        dlg = wx.FileDialog(None, "Select File...", pos = (2,2), style = wx.SAVE, wildcard = "Auxiliary Files (*.ppt,*.pptx,*.xls,*.xlsx, *.py)|*.ppt;*.pptx;*.xls;*.xlsx; *.py")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()  
        self.FindWindowByName("Path").SetValue(dir + '\\' + filename)
        
    def on_click_update(self, event):
        
        self.obj.title = self.FindWindowByName("Title").GetValue().strip()
        self.obj.filename = self.FindWindowByName("Path").GetValue().strip()
        
        pid = self.obj.pid
        self.parent.tc.tree.SetLabel(os.path.basename(self.obj.filename)) 
        self.parent.tc.tree.SetItemText(self.item, self.obj.title, 1)
        
        for i, member in enumerate(self.parent.db.sequences[self.obj.experiment]):
            
            if member[2]==pid:
                index = i
                break
        self.parent.db.sequences[self.obj.experiment][index][0] = self.obj.filename
        self.parent.db.sequences[self.obj.experiment][index][1] = self.obj.title
        
        self.parent.TreeRefresh()
        self.Destroy()
        
class AddXICFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add XIC', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Sequence', 'Title', 'Rawfile', 'Filter']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        gbs.Add( add_files_btn,
                 (9,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.db = db
        self.parent = parent
        self.db.Rebuild_Order_from_tree(parent)
        self.data=None
        self.xr = None
        self.notes = ''
        self.time_range = None
        self.full_time_range = None
        self.xic_mass_ranges = None
        self.xic_filters = None

    def on_click_add(self, event):
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        seq = self.FindWindowByName("Sequence").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        self.db.add_multi_XICItem(exp, seq, title, rawfile, data=self.data, xr=self.xr, notes=self.notes, time_range=self.time_range, xic_mass_ranges=self.xic_mass_ranges, xic_filters=self.xic_filters, xic_max = self.xic_max, xic_view=self.xic_view, active_xic=self.active_xic, xic_scale=self.xic_scale) #active_xic, xic_view, xic_scale, xic_max
        #self.db.addItem(exp, seq, title, scan, rawfile, scan_data, (100,1650), [((200,1650))], 2)
        self.parent.TreeRefresh()
        self.Destroy()

def get_single_file(self, caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
    dlg = wx.FileDialog(None, caption, pos = (2,2), wildcard = wx_wildcard)
    if not dlg:
        return
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetPath()
        dir = dlg.GetDirectory()
        print filename
        print dir
        dlg.Destroy()
        return filename, dir
    else:
        dlg.Destroy()
        return None, ''

class AddAuxFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Auxiliary File', size =(480,160), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(3, 3)
        gbs.Add( wx.StaticText(panel, -1, 'Experiment', style=wx.ALIGN_RIGHT), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=parent.tc.get_folders(), size=(250,25)), (0, 1), (1,8) ) #choices=parent.tc.get_folders()
        for i,c in enumerate(['Filename', 'Title']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT), (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c, size=(350,25)), (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        select_file_btn = wx.Button(panel, -1, 'Browse...')
        gbs.Add( add_files_btn,(3,1) )
        gbs.Add( select_file_btn,(3,2) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        select_file_btn.Bind(wx.EVT_BUTTON, self.on_select_file)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.parent = parent
        
    def on_click_add(self, event):
        folder = self.FindWindowByName("Experiment").GetValue().strip()
        filename = self.FindWindowByName("Filename").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        if filename:    
            #Existing node?
            if folder in self.parent.tc.get_folders():
                node = self.parent.tc.get_tree_item_from_folder_name(folder)
                item = self.parent.tc.tree.AppendItem(node, os.path.basename(filename))
                self.parent.tc.tree.SetItemData(item, {"type":"auxfile", "flag":"experiment", "exp":filename, "full_path":filename})
                self.parent.tc.tree.SetItemText(item, os.path.basename(filename))
                self.parent.TreeRefresh()
        self.Destroy()

    def on_select_file(self, event):
        filename, dir = get_single_file("Select file...", wx_wildcard = "Auxiliary Files (*.ppt,*.pptx,*.xls,*.xlsx, *.py)|*.ppt;*.pptx;*.xls;*.xlsx; *.py") #xls files (*.xls,*.xlsx)|*.xls;*.xlsx'
        if filename:
            self.FindWindowByName("Filename").SetValue(filename)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = SpecFrame(parent=None, id=-1, organizer=None)
    #frame=AddAuxFrame(None, -1, None)
    frame.Show()
    app.MainLoop()
