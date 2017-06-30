import wx
import wx.dataview as dv
import cPickle
import wx.gizmos
import TreeCtrl
from collections import defaultdict
import multiplierz.mzAPI as mzAPI
import SpecViewLite_build2 as svl
import RICviewLite as rvl
import RICviewLite_multi as rvlm
try:
    import MSO
    import win32com
except:
    pass
import time
import BlaisPepCalc




import os
install_dir = os.path.dirname(__file__)

class SpecBase():
    def __init__(self, rootname):
        print "New Spec Base created!"
        self.data = []
        self.rootname = rootname
        self.rootname = rootname
        self.td = None
        self.pid = 0
        self.experiments = []
        self.sequences = defaultdict(list)

    def __str__(self):
        for member in self.data:
            print member

    def Rebuild_Order_from_tree(self, parent):
        save = parent.tc.tree.SaveItemsToList(parent.tc.root)
        self.experiments = []
        self.sequences = defaultdict(list)
        for member in save:
            #print member['label'] #PROJECT NAME
            if 'children' in member.keys():
                for submember in member['children']:
                    #print submember['label'] #EXPERIMENT
                    self.experiments.append(submember['label'])
                    for subsub in submember['children']:
                        #print subsub['label'] #PEPTIDES
                        #print "REBUILT ID"
                        #print subsub['data']['id']
                        self.sequences[submember['label']].append([subsub['label'], subsub['columnLabel'], subsub['data']['id']])

    def addProtein(self, experiment, title, filename):
        self.pid += 1
        self.data.append(ProteinEntry(pid=self.pid, experiment=experiment, title=title, filename=filename))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append(["Protein Coverage Map", title, self.pid])
        #print self.sequences[experiment]
        
    def addFile(self, experiment, title, filename):
        self.pid += 1
        self.data.append(FileEntry(pid=self.pid, experiment=experiment, title=title, filename=filename))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append(["Auxiliary File", title, self.pid])

    def addFolder(self, experiment, title, folder):
        self.pid += 1
        self.data.append(FolderEntry(pid=self.pid, experiment=experiment, title=title, folder=folder))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append(["Folder", title, self.pid])
                        
    def addItem(self, experiment, sequence, title, scan, rawfile, scan_data, full_range, mass_ranges, charge, filter, cent_data, vendor, detector, profile, scan_type, varmod='', fixedmod ='', mascot_score=None, processed_scan_data=None):
        self.pid += 1
        self.data.append(BaseEntry(experiment=experiment, sequence=sequence, filter=filter, title=title, charge=charge, full_range=full_range, mass_ranges=mass_ranges, pid=self.pid, scan=scan, rawfile=rawfile, scan_data=scan_data, cent_data=cent_data, vendor=vendor, detector=detector, profile=profile, scan_type=scan_type, varmod=varmod, fixedmod=fixedmod, mascot_score=mascot_score, processed_scan_data=processed_scan_data))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append([sequence, title, self.pid])
        #print self.sequences[experiment]

    def addXICItem(self, experiment, sequence, title, rawfile, data, xr, time_range, xic_mass_ranges, xic_filters, notes):
        self.pid += 1
        self.data.append(RICentry(experiment=experiment, sequence=sequence, title=title, pid=self.pid, rawfile=rawfile, data=data, xr=xr, time_range=time_range, xic_mass_ranges=xic_mass_ranges, xic_filters=xic_filters, notes=notes))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append([sequence, title, self.pid])
        #print self.sequences[experiment]
        
    def add_multi_XICItem(self, experiment, sequence, title, rawfile, data, xr, time_range, xic_mass_ranges, xic_filters, notes, active_xic, xic_view, xic_scale, xic_max):
        self.pid += 1
        self.data.append(multiRICentry(experiment=experiment, sequence=sequence, title=title, pid=self.pid, rawfile=rawfile, data=data, xr=xr, time_range=time_range, xic_mass_ranges=xic_mass_ranges, xic_filters=xic_filters, notes=notes, active_xic=active_xic, xic_view=xic_view, xic_scale=xic_scale, xic_max=xic_max))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append([sequence, title, self.pid])
        #print self.sequences[experiment]    

    def addAnalysisItem(self, experiment, title, file_data, display):
        self.pid += 1
        self.data.append(AnalysisEntry(self.pid, experiment=experiment, title=title, file_data=file_data, display=display))
        if experiment not in self.experiments:
            self.experiments.append(experiment)
        self.sequences[experiment].append(["Analysis Context", title, self.pid])

    def getExperimentNames(self):
        names = set()
        for member in self.data:
            names.add(member.experiment)
        return names

    def getSequences(self, experiment):
        seqs = []
        for member in self.data:
            if member.experiment == experiment:
                seqs.append((member.sequence, member.title))
        return seqs

    def DumpLabels(self):
        for member in self.td:
            print member['label'] #PROJECT NAME
            for submember in member['children']:
                print submember['label'] #EXPERIMENT
                for subsub in submember['children']:
                    print subsub['label'] #PEPTIDES

    def get_title_from_id(self, pid):
        title = None
        for member in self.data:
            if member.pid == pid:
                title=member.title
        if title == None:
            print pid
            raise ValueError("id not found!")
        return title

    def get_type_from_id(self, pid):
        type = None
        for member in self.data:
            if member.pid == pid:
                try:
                    type=member.type
                except:
                    member.type = "Spectrum"
                    type = member.type
        if type == None:
            print pid
            raise ValueError("id not found!")
        return type

    def get_spectrum_from_id(self, pid):
        spectrum = None
        for member in self.data:
            if member.pid == pid:
                spectrum=member
                break
        if spectrum == None:
            print pid
            raise ValueError("id not found!")
        return member

    def delete_entry_from_id(self, pid):
        '''
        Deletion of an entry is a 3-step process.  First, the entry is removed from sef.data.
        Next, the experiment is removed if this is the only element of the experiment.
        Finally, the element is removed from self.sequences.  If the deleted element represents the only
        element for the experiment, the key is delected from the self.sequences dictionary.
        '''
        delete_index = -1
        experiment = None
        for i, member in enumerate(self.data):
            if member.pid == pid:
                delete_index = i
                experiment = member.experiment
                break
        if delete_index > -1:
            print "DELETING!!!"
            del self.data[delete_index]
            found = False
            for member in self.data:
                if member.experiment == experiment:
                    found = True
                    print "FOUND EXP, LEAVING..."
                    break
            if not found:
                print "DELETING EXP!"
                for j, member in enumerate(self.experiments):
                    if member == experiment:
                        del self.experiments[j]
            if len(self.sequences[experiment]) == 1:
                print "DEL FROM SEQS!"
                del self.sequences[experiment]
            else:
                print "DEL SEQ ENTRY"
                for k, member in enumerate(self.sequences[experiment]):
                    if member[2] == pid:
                        del self.sequences[experiment][k]
        if delete_index > -1:
            return True
        else:
            return False
                        
    def get_base_entry_from_id(self, pid):
        #print self.data
        #print str(pid) + " looking"
        entry = None
        for member in self.data:
            #print "Current" + str(member.pid)
            #print pid
            if member.pid == pid:
                entry = member
                break
        if entry == None:
            print pid
            raise ValueError("id not found!")
        return entry

    def CreateTree(self):
        tree = []
        tree.append({'icon-expanded': -1, 'label': db.rootname, 'icon-selected': -1, 'icon-selectedexpanded': -1, 'icon-normal': 0, 'columnLabel': u'', 'data': {'type': 'container'},
         'children':[]})
        for member in self.getExperimentNames():
            tree[0]['children'].append

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
    def __init__(self, pid, sequence='', varmod='', fixedmod='', rawfile='', charge=0, filter='', title='', detector="IT", display_range=[], full_range=[], mass_ranges=[] ,axes=1, experiment='', scan=1, notes='', massList='', scan_data=None, cent_data = None, vendor='Thermo',profile=False, scan_type="MS2", mascot_score=None, processed_scan_data=None):
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
        self.processed_scan_Data = processed_scan_data
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
        print "ID assigned: " + str(self.pid)

    def __str__(self):
        print "Sequence: " +str(self.sequence)
        print "Rawfile: " + str(self.rawfile)
        print "ID: " + str(self.pid)

class SpecFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'SpecBase', size =(650,660), pos = (50,50))
        panel = wx.Panel(self)
        self.panel = panel
        self.CreateMenuBar()
        self.db = None
        #self.CreateTree()
        self.tc = tc = TreeCtrl.TestTreeCtrlPanel(panel, -1, self)
        self.created = False
        self.TreeSizer = wx.BoxSizer()
        self.TreeSizer.Add(tc, 1, wx.EXPAND)
        self.panel.SetSizerAndFit(self.TreeSizer)
        self.tc.tree.DeleteAllItems()
        #self.Bind(wx.EVT_, self.OnBeginDrag, self.dvtc)
        #self.Bind(wx.EVT_DATAVIEW_ITEM_END_DRAG, self.OnDrag, self.dvtc)
        #self.Bind(wx.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnEdit, self.dvtc)
        self.NameFile = None
        self.bpc = None

    def UpdateSpecBaseData(self):
        self.db.td = self.tc.tree.SaveItemsToList(self.tc.root)
        #print self.db.td

    def CreateMenuBar(self):
            menuBar = wx.MenuBar()
            for eachMenuData in self.menuData():
                menuLabel = eachMenuData[0]
                #print menuLabel
                menuItems = eachMenuData[1:]
                #print menuItems
                menuBar.Append(self.createMenu(menuItems), menuLabel)
            self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu=wx.Menu()
        #print menuData
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator(self)
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

    def menuData(self):
        return  (("&File",
                  ("&Create SpecBase", "Create SpecBase", self.OnCreate),
                    ("&Open", "Open Template", self.OnLoad),
                    ("&Save", "Save Template", self.OnSave),
                    ("&Save As...", "Save Template", self.OnSaveAs)),
                 ("&Add",
                    ("&Add Spectrum", "Add Spectrum", self.OnAdd),
                    ("&Add Protein", "Add Protein", self.OnAddProtein),
                    ("&Add Auxiliary File", "Add Auxiliary File", self.OnAddAux),
                    ("&Add Folder", "Add Folder", self.OnAddFolder)),
                 ("&Edit",
                    ("&Edit", "Edit", self.OnEdit),
                    ("&Delete Entry", "Delete Entry", self.OnDelete)),
                ("&Export",
                    ("&Export to PPT", "Export to PPT", self.OnPPT),
                    ("&Export current to PPT", "Export current to PPT", self.CurrentSlidetoPPT)),
                ("&BPC",
                    ("&Open BPC", "Open BPC", self.OnOpenBPC)))                

    def OnOpenBPC(self, event):
        self.bpc = BlaisPepCalc.BlaisPepCalc(parent=self, id=-1)
        self.bpc.Show()

    def OnDelete(self, event):
        item=self.tc.tree.GetSelection()
        pid = self.tc.tree.GetPyData(item)["id"]
        self.db.delete_entry_from_id(pid)
        self.TreeRefresh()

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
        pid = self.tc.tree.GetPyData(item)["id"]     
        if self.db.get_type_from_id(pid) == "XIC":
            xic = self.db.get_spectrum_from_id(pid)
            frame = rvl.RICviewLitePanel(None, xic)
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
        LabelMascotScore = False
        filename, dir = get_single_file("Select file...", wx_wildcard = "PPT files (*.ppt)|*.ppt")
        if not filename.endswith('ppt'):
            filename += '.ppt'
        tmp = os.path.join(install_dir, r'image\Temp.png')
        App = win32com.client.Dispatch("PowerPoint.Application")
        Pres = App.Presentations.Add()
        exp = self.db.experiments
        seqs = self.db.sequences   
        for member in exp:
            for y in range(len(seqs[member])):
                print y
                print "********************************"
                print self.db.get_type_from_id(seqs[member][y][2])
                if self.db.get_type_from_id(seqs[member][y][2]) == "Spectrum":
                    print "SLIDES"
                    spectrum = self.db.get_spectrum_from_id(seqs[member][y][2])
                    print spectrum.sequence
                    frame = svl.SpecViewLitePanel(None, spectrum)
                    frame.Show()
                    frame.Refresh()
                    #frame.RefreshRect()
                    #frame.SetFocus()
                    #frame.ProcessEvent()
                    wx.Yield()
                    print "TIME1:"
                    time.sleep(0.5)
                    print "TIME2:"
                    frame.SpecWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
                    print "SAVED!"
                    frame.Destroy()
                    Slide = Pres.Slides.Add(1,12)
                    Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
                    print "ADDED!"
                    
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
                if self.db.get_type_from_id(seqs[member][y][2]) == "XIC":
                    xic = self.db.get_spectrum_from_id(seqs[member][y][2])
                    frame = rvl.RICviewLitePanel(None, xic)
                    frame.Show()
                    frame.Refresh()
                    wx.Yield()
                    print "TIME1:"
                    time.sleep(0.5)
                    print "TIME2:"
                    frame.XICWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
                    print "SAVED!"
                    frame.Destroy()
                    Slide = Pres.Slides.Add(1,12)
                    Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
                    print "ADDED!"
                if self.db.get_type_from_id(seqs[member][y][2]) == "multiXIC":
                    xic = self.db.get_spectrum_from_id(seqs[member][y][2])
                    frame = rvlm.RICviewLitePanel(None, xic)
                    frame.Show()
                    frame.Refresh()
                    wx.Yield()
                    print "TIME1:"
                    time.sleep(0.5)
                    print "TIME2:"
                    frame.XICWindow.img.SaveFile(tmp,wx.BITMAP_TYPE_PNG)
                    print "SAVED!"
                    frame.Destroy()
                    Slide = Pres.Slides.Add(1,12)
                    Slide.Shapes.AddPicture(FileName = tmp, LinkToFile=False, SaveWithDocument=True, Left=10, Top=50, Width=490, Height=490)
                    print "ADDED!"
                    shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=40, Width = 750, Height = 40 )
                    shape.TextFrame.TextRange.Text = xic.title   
                    shape.TextFrame.TextRange.Font.Size=10                    
                                    #shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientat                
                    #shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=10, Width = 750, Height = 40 )
                    #shape.TextFrame.TextRange.Text = spectrum.sequence + "  Mascot Score: " + str(spectrum.mascot_score) #+' (' + spectrum.title + ')' 
                    #shape.TextFrame.TextRange.Font.Size=10
                    #shape = Slide.Shapes.AddTextbox(MSO.constants.msoTextOrientationHorizontal, Left=10, Top=40, Width = 750, Height = 40 )
                    #shape.TextFrame.TextRange.Text = spectrum.notes   
                    #shape.TextFrame.TextRange.Font.Size=10                    
                  
                
        #shape = Slide.Shapes.AddTextbox(1, 10, 10, Width = 600, Height = 40)
        #shape.TextFrame.TextRange.Font.Name = "Arial"
        #shape.TextFrame.TextRange.Font.Size = 24
        #shape.TextFrame.TextRange.Text = "Unique Peptides: " + str(len(main[member]["pepset"]))
        #shape = Slide.Shapes.AddTextbox(1, 10, 40, Width = 600, Height = 40)
        #shape.TextFrame.TextRange.Font.Name = "Arial"
        #shape.TextFrame.TextRange.Font.Size = 24
        #shape.TextFrame.TextRange.Text = "Total Spectra: " + str(main[member]["pepcount"])
        Pres.SaveAs(filename)
        Pres.Close()
        App.Quit()        
    

    def OnTest(self,event):
        #save = self.tc.tree.SaveItemsToList(self.tc.root)
        #self.UpdateSpecBaseData()
        #print self.db.DumpLabels()
        exp = "2012-04-12"
        seq = 'DASLVSSRPSpSPEPD'
        title = "Olig2-S14"
        scan = 2888
        rawfile = r'\\Glu\Userland\SBF\DataMain\Collaborations\Stiles\2012-06-22-Olig2\2012-06-22-Olig2-Cos-AspN-Targ-1.raw'
        m = mzAPI.mzFile(rawfile)
        scan_data = m.scan(int(scan))
        #display_range=(200,1650), full_range=(200,1650), mass_ranges=[((200,1650))]
        self.db.addItem(exp, seq, title, scan, rawfile, scan_data, (100,1650), [((200,1650))], 2)
        self.TreeRefresh()
        #self.Destroy()

    def OnCreate(self, event):
        dialog = wx.TextEntryDialog(None, "Project Name", "Project Name", "", style=wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_OK:
            sb = SpecBase(dialog.GetValue())
            self.db = sb
            self.TreeRefresh()

    def OnAdd(self, event):
        Addit = AddFrame(self, id=-1, db=self.db)
        Addit.Show()

    def OnAddProtein(self,event):
        Addit = AddProteinFrame(self, id=-1, db=self.db)
        Addit.Show()

    def OnAddAux(self,event):
        Addit = AddAuxFrame(self, id=-1, db=self.db)
        Addit.Show()

    def OnAddFolder(self,event):
        Addit = AddFolderFrame(self, id=-1, db=self.db)
        Addit.Show()

    def TreeRefresh(self):
        self.tc.tree.DeleteAllItems()
        isz = (16,16)
        il = wx.ImageList(*isz)
        fldridx     = il.AddIcon(wx.ArtProvider.GetIcon(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.AddIcon(wx.ArtProvider.GetIcon(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
        fileidx     = il.AddIcon(wx.ArtProvider.GetIcon(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        self.tc.tree.SetImageList(il)
        self.il = il

        self.tc.root = self.tc.tree.AddRoot(self.db.rootname)
        self.tc.tree.SetPyData(self.tc.root, {"type":"container", "flag":"root"})
        self.tc.tree.SetItemImage(self.tc.root, fldridx, wx.TreeItemIcon_Normal)
        self.tc.tree.SetItemImage(self.tc.root, fldropenidx, wx.TreeItemIcon_Expanded)
        exp = self.db.experiments
        seqs = self.db.sequences
        #print exp
        for member in exp:
            child = self.tc.tree.AppendItem(self.tc.root, member)
            self.tc.tree.SetPyData(child, {"type":"container", "flag":"experiment"})
            self.tc.tree.SetItemImage(child, fldridx, wx.TreeItemIcon_Normal)
            self.tc.tree.SetItemImage(child, fldropenidx, wx.TreeItemIcon_Expanded)
            #seqs = self.db.getSequences(member)
            for y in range(len(seqs[member])):
                #print seqs[member][y]
                last = self.tc.tree.AppendItem(child, seqs[member][y][0])
                #print "id"
                #print seqs[member][y][2]
                if self.db.get_type_from_id(seqs[member][y][2]) == "Spectrum":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "scan_data":self.db.get_base_entry_from_id(seqs[member][y][2]).scan_data, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                if self.db.get_type_from_id(seqs[member][y][2]) == "XIC":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "xic_data":self.db.get_base_entry_from_id(seqs[member][y][2]).data, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                if self.db.get_type_from_id(seqs[member][y][2]) == "multiXIC":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "xic_data":self.db.get_base_entry_from_id(seqs[member][y][2]).data, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                                                    
                if self.db.get_type_from_id(seqs[member][y][2]) == "Protein Coverage Map":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "protein_data":self.db.get_base_entry_from_id(seqs[member][y][2]).filename, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                if self.db.get_type_from_id(seqs[member][y][2]) == "AuxFile":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "file_data":self.db.get_base_entry_from_id(seqs[member][y][2]).filename, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                if self.db.get_type_from_id(seqs[member][y][2]) == "Folder":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "folder":self.db.get_base_entry_from_id(seqs[member][y][2]).folder, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                if self.db.get_type_from_id(seqs[member][y][2]) == "Analysis":
                    self.tc.tree.SetPyData(last,{"type":"container", "flag":"entry", "id":seqs[member][y][2], "file_data":self.db.get_base_entry_from_id(seqs[member][y][2]).file_data, "obj":self.db.get_spectrum_from_id(seqs[member][y][2])})
                self.tc.tree.SetItemImage(last, fldridx, wx.TreeItemIcon_Normal)
                self.tc.tree.SetItemImage(last, fldropenidx,wx.TreeItemIcon_Expanded)
                self.tc.tree.SetItemText(last, seqs[member][y][1], 1)
        self.tc.tree.Expand(self.tc.root)
        self.Refresh()

    def OnBeginDrag(self,event):
        print "Begin!"
        event.Allow()

    def OnDrag(self,event):
        print "Drag!"

    def OnEdit(self,event):
        print "Edit!"
        #item = event.GetItem()
        item=self.tc.tree.GetSelection()
        #self.tc.tree.EditLabel(item)
        #self.tc.tree.SetItemText(item, "CG", 1)
        #self.TreeRefresh()
        #print item
        #print self.tc.tree.GetItemText(item)
        #print self.tc.tree.GetPyData(item)["id"]
        id = self.tc.tree.GetPyData(item)["id"]
        cur_obj = self.db.get_base_entry_from_id(id)
        #print cur_obj.title
        #print cur_obj.sequence
        if cur_obj.type == "Spectrum":
            Edit = EditFrame(self, id=-1, obj=cur_obj, item=item)
            Edit.Show()
        if cur_obj.type == "multiXIC":
            Edit = EditXICFrame(self, id=-1, obj=cur_obj, item=item)
            Edit.Show()            
        #if item:
            #self.tc.
            #self.tc.EditLabel(item)

    def OnLoad(self, event):
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.OPEN, wildcard = "SpecBrary files (*.sbr)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            #os.chdir(dir)
        dlg.Destroy()
        self.loaddir = dir
        self.loadfilename = filename
        print dir
        print filename
        pickle_file = open(dir + '\\' + filename, "r")
        self.db = cPickle.load(pickle_file)
        print self.db.rootname
        pickle_file.close()
        #self.tc.tree.DeleteAllItems()
        self.TreeRefresh()
        self.NamedFile = dir + '\\' + filename 

    def OnSave(self, event):
        if self.NamedFile:
            pickle_file = open(self.NamedFile, "w")
            cPickle.dump(self.db, pickle_file)
            pickle_file.close()
        else:
            self.OnSaveAs(None)

    def OnSaveAs(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "SpecBrary files (*.sbr)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            #os.chdir(dir)
        dlg.Destroy()
        self.savedir = dir
        self.savefilename = filename
        print dir
        print filename
        if not filename.endswith(".sbr"):
            filename += '.sbr'
        pickle_file = open(dir +'\\' + filename, "w")
        cPickle.dump(self.db, pickle_file)
        pickle_file.close()
        self.NamedFile = dir +'\\' + filename

    def OnHelp(self, event):
        pass

class AddFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Spectrum', size =(300,500), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Sequence', 'Title', 'Varmods', 'Rawfile', 'Scan', 'Axes', 'Display Range', 'Filter', 'Fixedmods', 'Mascot Score']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        grab_spec_btn = wx.Button(panel, -1, 'Grab Spectrum')
        gbs.Add( add_files_btn,
                 (11,0) )
        gbs.Add( grab_spec_btn,
                 (12,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        grab_spec_btn.Bind(wx.EVT_BUTTON, self.on_click_grab)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.db = db
        self.parent = parent
        self.db.Rebuild_Order_from_tree(parent)
        self.scan_data = None
        self.display_range = []
        self.mass_ranges = []
        self.charge = 0

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
        self.db.addItem(exp, seq, title, scan, rawfile, self.scan_data, self.display_range, self.mass_ranges, self.charge, filter, self.cent_data, self.vendor, self.detector, self.profile, self.scan_type, varmod=varmod, fixedmod=fixedmod, mascot_score=mascot_score, processed_scan_data = self.processed_scan_data)
        #self.db.addItem(exp, seq, title, scan, rawfile, scan_data, (100,1650), [((200,1650))], 2)
        self.parent.TreeRefresh()
        self.Destroy()

    def on_click_grab(self, event):
        rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        scan = self.FindWindowByName("Scan").GetValue().strip()
        m = mzAPI.mzFile(rawfile)
        scan_data = m.scan(int(scan))
        dlg = wx.MessageDialog(None, "Scan data was read!", "", wx.OK)
        retCode = dlg.ShowModal()
        if (retCode == wx.ID_OK):
            #print "Scan data read"
            self.scan = scan_data

class EditFrame(wx.Frame):
    def __init__(self, parent, id, obj, item):
        wx.Frame.__init__(self, parent, id, 'Edit Entry', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value=obj.experiment, choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Sequence', 'Title', 'Varmods', 'Rawfile', 'Scan', 'Axes', 'Display Range', 'Filter']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#size=(250, 25) 
        add_files_btn = wx.Button(panel, -1, 'Update')
        #grab_spec_btn = wx.Button(panel, -1, 'Grab Spectrum')
        gbs.Add( add_files_btn,
                 (9,0) )
        #gbs.Add( grab_spec_btn,
        #        (10,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_update)
        #grab_spec_btn.Bind(wx.EVT_BUTTON, self.on_click_grab)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        #self.db = db
        self.parent = parent
        #self.db.Rebuild_Order_from_tree(parent)
        self.FindWindowByName("Experiment").SetValue(obj.experiment)
        self.FindWindowByName("Sequence").SetValue(obj.sequence)
        self.FindWindowByName("Title").SetValue(obj.title)
        self.FindWindowByName("Scan").SetValue(obj.scan)
        self.FindWindowByName("Filter").SetValue(obj.filter)
        self.FindWindowByName("Rawfile").SetValue(obj.rawfile)
        self.FindWindowByName("Varmods").SetValue(obj.varmod)
        self.obj = obj
        self.item = item
        
    def on_click_update(self, event):
        self.obj.experiment = self.FindWindowByName("Experiment").GetValue().strip()
        self.obj.sequence = self.FindWindowByName("Sequence").GetValue().strip()
        self.obj.title = self.FindWindowByName("Title").GetValue().strip()
        self.obj.scan = self.FindWindowByName("Scan").GetValue().strip()
        self.obj.filter = self.FindWindowByName("Filter").GetValue().strip()
        self.obj.rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        self.obj.varmod = self.FindWindowByName("Varmods").GetValue().strip()
        pid = self.obj.pid
        self.parent.tc.tree.SetLabel(self.obj.sequence)#self.item, 
        self.parent.tc.tree.SetItemText(self.item, self.obj.title, 1)
        #self.db.addItem(exp, seq, title, scan, rawfile, self.scan, self.display_range, self.mass_ranges, self.charge, filter)
        #self.db.addItem(exp, seq, title, scan, rawfile, scan_data, (100,1650), [((200,1650))], 2)
        for i, member in enumerate(self.parent.db.sequences[self.obj.experiment]):
            #print member
            if member[2]==pid:
                index = i
                break
        self.parent.db.sequences[self.obj.experiment][index][0] = self.obj.sequence
        self.parent.db.sequences[self.obj.experiment][index][1] = self.obj.title
        #.append([sequence, title, self.pid])
        self.parent.TreeRefresh()
        self.Destroy()
    
    def on_click_grab(self, event):
        rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        scan = self.FindWindowByName("Scan").GetValue().strip()
        m = mzAPI.mzFile(rawfile)
        scan_data = m.scan(int(scan))
        dlg = wx.MessageDialog(None, "Scan data was read!", "", wx.OK)
        retCode = dlg.ShowModal()
        if (retCode == wx.ID_OK):
            #print "Scan data read"
            self.scan = scan_data
        
class EditXICFrame(wx.Frame):
    def __init__(self, parent, id, obj, item):
        wx.Frame.__init__(self, parent, id, 'Edit XIC Entry', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT), (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value=obj.experiment, choices=list(parent.db.getExperimentNames())), (0, 1), (1,8) )
        for i,c in enumerate(['Sequence', 'Title', 'Rawfile', 'Filter']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT), (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c), (i+1, 1), (1,8))#size=(250, 25) 
        add_files_btn = wx.Button(panel, -1, 'Update')
        gbs.Add( add_files_btn, (9,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_update)
        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.parent = parent
        self.FindWindowByName("Experiment").SetValue(obj.experiment)
        self.FindWindowByName("Sequence").SetValue(obj.sequence)
        self.FindWindowByName("Title").SetValue(obj.title)
        self.FindWindowByName("Filter").SetValue(obj.filter)
        self.FindWindowByName("Rawfile").SetValue(obj.rawfile)
        self.obj = obj
        self.item = item    

    def on_click_update(self, event):
        self.obj.experiment = self.FindWindowByName("Experiment").GetValue().strip()
        self.obj.sequence = self.FindWindowByName("Sequence").GetValue().strip()
        self.obj.title = self.FindWindowByName("Title").GetValue().strip()
        self.obj.filter = self.FindWindowByName("Filter").GetValue().strip()
        self.obj.rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        pid = self.obj.pid
        self.parent.tc.tree.SetLabel(self.obj.sequence)#self.item, 
        self.parent.tc.tree.SetItemText(self.item, self.obj.title, 1)
        #self.db.addItem(exp, seq, title, scan, rawfile, self.scan, self.display_range, self.mass_ranges, self.charge, filter)
        #self.db.addItem(exp, seq, title, scan, rawfile, scan_data, (100,1650), [((200,1650))], 2)
        for i, member in enumerate(self.parent.db.sequences[self.obj.experiment]):
            #print member
            if member[2]==pid:
                index = i
                break
        self.parent.db.sequences[self.obj.experiment][index][0] = self.obj.sequence
        self.parent.db.sequences[self.obj.experiment][index][1] = self.obj.title
        #.append([sequence, title, self.pid])
        self.parent.TreeRefresh()
        self.Destroy()

    def on_click_grab(self, event):
        rawfile = self.FindWindowByName("Rawfile").GetValue().strip()
        scan = self.FindWindowByName("Scan").GetValue().strip()
        m = mzAPI.mzFile(rawfile)
        scan_data = m.scan(int(scan))
        dlg = wx.MessageDialog(None, "Scan data was read!", "", wx.OK)
        retCode = dlg.ShowModal()
        if (retCode == wx.ID_OK):
            #print "Scan data read"
            self.scan = scan_data


class AddAnalysisFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Analysis', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Experiment', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Title']):
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
        self.file_data = defaultdict(dict)
        self.display= []

    def on_click_add(self, event):
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        self.db.addAnalysisItem(experiment=exp, title=title, file_data=self.file_data, display=self.display)
        self.parent.TreeRefresh()
        self.Destroy()

class AddXICFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add XIC', size =(300,500), pos = (50,50))
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
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetPath()
        dir = dlg.GetDirectory()
        print filename
        print dir
    dlg.Destroy()
    return filename, dir

class AddProteinFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Protein Coverage map', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Experiment', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Filename', 'Title']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        select_prot_btn = wx.Button(panel, -1, 'Select prt file')
        gbs.Add( add_files_btn,
                 (10,0) )
        gbs.Add( select_prot_btn,
                 (11,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        select_prot_btn.Bind(wx.EVT_BUTTON, self.on_select_prot)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.db = db
        self.parent = parent
        self.db.Rebuild_Order_from_tree(parent)
        self.scan_data = None
        self.display_range = []
        self.mass_ranges = []
        self.charge = 0

    def on_click_add(self, event):
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        filename = self.FindWindowByName("Filename").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        self.db.addProtein(exp, title, filename)
        self.parent.TreeRefresh()
        self.Destroy()

    def on_select_prot(self, event):
        filename, dir = get_single_file("Select .prt file...", wx_wildcard = "PRT files (*.prt)|*.prt")
        self.FindWindowByName("Filename").SetValue(filename)

class AddAuxFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Auxiliary File', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Experiment', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Filename', 'Title']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        select_file_btn = wx.Button(panel, -1, 'Select file')
        gbs.Add( add_files_btn,
                 (10,0) )
        gbs.Add( select_file_btn,
                 (11,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        select_file_btn.Bind(wx.EVT_BUTTON, self.on_select_file)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.db = db
        self.parent = parent
        self.db.Rebuild_Order_from_tree(parent)
        self.scan_data = None
        self.display_range = []
        self.mass_ranges = []
        self.charge = 0

    def on_click_add(self, event):
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        filename = self.FindWindowByName("Filename").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        self.db.addFile(exp, title, filename)
        self.parent.TreeRefresh()
        self.Destroy()

    def on_select_file(self, event):
        filename, dir = get_single_file("Select file...", wx_wildcard = "Auxiliary Files (*.ppt,*.pptx,*.xls,*.xlsx)|*.ppt;*.pptx;*.xls;*.xlsx") #xls files (*.xls,*.xlsx)|*.xls;*.xlsx'
        self.FindWindowByName("Filename").SetValue(filename)

class AddFolderFrame(wx.Frame):
    def __init__(self, parent, id, db):
        wx.Frame.__init__(self, parent, id, 'Add Folder', size =(580,660), pos = (50,50))
        panel = wx.Panel(self)
        gbs = wx.GridBagSizer(11, 5)
        gbs.Add( wx.StaticText(panel, -1, 'Folder', style=wx.ALIGN_RIGHT),
                     (0, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
        gbs.Add( wx.ComboBox(panel, -1, name='Experiment', value='', choices=list(parent.db.getExperimentNames())),
                     (0, 1), (1,8) )
        for i,c in enumerate(['Directory', 'Title']):
            gbs.Add( wx.StaticText(panel, -1, c, style=wx.ALIGN_RIGHT),
                     (i+1, 0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
            gbs.Add( wx.TextCtrl(panel, -1, '', name = c),
                     (i+1, 1), (1,8))#, size=(250, 25)
        add_files_btn = wx.Button(panel, -1, 'Add')
        select_file_btn = wx.Button(panel, -1, 'Select folder')
        gbs.Add( add_files_btn,
                 (10,0) )
        gbs.Add( select_file_btn,
                 (11,0) )
        add_files_btn.Bind(wx.EVT_BUTTON, self.on_click_add)
        select_file_btn.Bind(wx.EVT_BUTTON, self.on_select_file)

        box = wx.BoxSizer()
        box.Add(gbs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizerAndFit(box)
        self.db = db
        self.parent = parent
        self.db.Rebuild_Order_from_tree(parent)
        self.scan_data = None
        self.display_range = []
        self.mass_ranges = []
        self.charge = 0

    def on_click_add(self, event):
        exp = self.FindWindowByName("Experiment").GetValue().strip()
        filename = self.FindWindowByName("Directory").GetValue().strip()
        title = self.FindWindowByName("Title").GetValue().strip()
        self.db.addFolder(exp, title, filename)
        self.parent.TreeRefresh()
        self.Destroy()

    def on_select_file(self, event):
        dlg = wx.DirDialog(self, "Choose Directory")
        if dlg.ShowModal() == wx.ID_OK:
            dir = dlg.GetPath()
        dlg.Destroy()
        self.FindWindowByName("Directory").SetValue(dir)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = SpecFrame(parent=None, id=-1)
    frame.Show()
    app.MainLoop()
