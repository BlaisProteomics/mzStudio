import wxversion
#wxversion.select('3')
#import wx.gizmos as dataview
import wx
#from wx.dataview import TreeListCtrl
from wx.lib.agw.customtreectrl import CustomTreeCtrl as TreeListCtrl
import wx.lib.agw.flatmenu as flatmenu
import os
import cPickle as pickle
from wx.lib.mixins import treemixin
imgDir = os.path.join(os.path.dirname(__file__), 'bitmaps')
import SpecViewLite_build2 as svl
import RICviewLite_multi as rvlm




def image_for_data(data):
    assert 'Type' in data, 'Tree item data must have a "Type" member!'
    objtype = data['Type'].lower()
    if objtype == 'folder':
        openImg = 1
        closeImg = 0
    elif objtype == 'spectrum':
        openImg = closeImg = 3
    elif objtype == 'xic':
        openImg = closeImg = 7
    elif objtype == 'file':
        assert 'Filetype' in data, 'Tree item data of "File" type must have "Filetype" member!'
        ext = data['Filetype'].lower()
        if ext == 'py':
            openImg = closeImg = 6
        elif ext == 'ppt':
            openImg = closeImg = 5
        else: # 'th' image for some reason?
            openImg = closeImg = 2
    else:
        raise NotImplementedError, objtype
    return openImg, closeImg

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


def writePPT(filename, nodes_data):
    if not filename.lower().endswith('ppt'):
        filename += '.ppt'
        
    App = win32com.client.Dispatch("PowerPoint.Application")
    Pres = App.Presentations.Add()    
    
    for node_data in nodes_data:
        if node_data['Type'] == 'spectrum':
            spectrum_object = node_data['object']
            raise NotImplementedError, 'Write spectrum slide here.'
        elif node_data['Type'] == 'xic':
            xic_object = node_data['object']
            raise NotImplementedError, 'Write XIC slide here.'
        
    Pres.SaveAs(filename)
    Pres.Close()
    App.Quit()


#class Mixins(treemixin.DragAndDrop):
    #def __init__(self, *args, **kwargs):
        #super(Mixins, self).__init__(*args, **kwargs)

class SpectrumTree(treemixin.DragAndDrop,
                   TreeListCtrl):
    def __init__(self, parent, id):
        super(SpectrumTree, self).__init__(parent, id)
    
    
    def OnDrop(self, dropTarget, dragItem):
        self.MoveItem(dragItem, dropTarget)
    
    def MoveItem(self, itemToMove, newItemParent):
        print "MOVING " + itemToMove.GetText()
        movedItem = self.add_object(newItemParent, 
                                    text = itemToMove.GetText(),
                                    data = itemToMove.GetData())
        if itemToMove.GetChildrenCount() > 0:
            print "%s HAS %d CHILDREN %s" % (itemToMove.GetText(), itemToMove.GetChildrenCount(),
                                             [x.GetText() for x in itemToMove.GetChildren()])
            childlist = list(itemToMove.GetChildren())
            for childItem in childlist:
                self.MoveItem(childItem, movedItem)
        self.Delete(itemToMove)    
                
    def Create(self, parent):
        self.base = None # Base element, different from tree root.  None if not active.
        
        self.filename = None
        
        images = ([wx.ArtProvider.GetIcon(art_ptr, wx.ART_OTHER, (16, 16)) for art_ptr 
                   in [wx.ART_FOLDER, wx.ART_FOLDER_OPEN, wx.ART_NORMAL_FILE]]
                  +
                  [wx.Bitmap(os.path.join(imgDir, img), wx.BITMAP_TYPE_PNG) for img
                   in ["spectrum.png", "th.png", "ppt.png", "py.png", "x2.png"]])
        self.imagelist = wx.ImageList(16, 16)
        for image in images:
            self.imagelist.Add(image)
        self.AssignImageList(self.imagelist)
        
        #self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.foobar)
        #self.Bind(wx.EVT_LEFT_DCLICK, self.edit_item)
        self.Bind(wx.EVT_RIGHT_UP, self.edit_item)
        self.Bind(wx.EVT_LEFT_DCLICK, self.open_specViewLite)

        self.dragitem = None
        
        self.new_specbase(None) 
        # No reason to have an empty specbase widget open.  Could have separate
        # main-window menu controls for opening a new specbase versus loading 
        # a pre-existing one.
    
    
    def edit_item(self, event):
        target = self.GetSelection()
        self.EditLabel(target)
        event.Skip()
        
    def open_specViewLite(self, event):
        target = self.GetSelection()
        data = target.GetData()
        
        #########
        #wx.MessageDialog(self, "SpecViewLite showing %s goes here!" % data['Object'], style = wx.OK).ShowModal()
        
        if data['Object'].type == 'Spectrum':
            frame = svl.SpecViewLitePanel(None, data['Object'])
        elif data['Object'].type == "XIC":
            frame = rvlm.RICviewLitePanel(None, data['Object'])
        frame.Show()
        #########
        
        event.Skip()
    
    def raiseObjection(self, message):
        messdog = wx.MessageDialog(self, message,
                                   'An error has occurred', style = wx.OK)
        messdog.ShowModal()
        messdog.Destroy()        
    
    def onEdit(self, event):
        node = self.GetSelection()
        if node.IsOk():
            textdog = wx.TextEntryDialog(None, "Enter new title:", "Blais Spectrum Database",
                                         "", style=wx.OK|wx.CANCEL)  
            if textdog.ShowModal() == wx.ID_OK and textdog.GetValue():
                self.SetItemText(node, textdog.GetValue())
                
        
    def new_specbase(self, event):
        textdog = wx.TextEntryDialog(None, "Project Name:", "Blais Spectrum Database",
                                     "New_SpecBase", style=wx.OK|wx.CANCEL)
        if textdog.ShowModal() == wx.ID_OK:
            self.DeleteAllItems()
            #self.base = self.InsertItem(self.GetRootItem(), 
                                        #str(textdog.GetValue()),
                                        #0, 0,
                                        #{'Type':'Folder'})
            self.base = self.AddRoot(str(textdog.GetValue()),
                                     data = {'Type':'Folder'})
    
    def load(self, event):
        self.DeleteAllItems()
        filedog = wx.FileDialog(self, "Load Spectrum Database:", style = wx.FD_OPEN)
        if filedog.ShowModal() != wx.ID_OK:
            return
        filepath = filedog.GetPath()
        
        def add_children_nodes(node, subdata):
            for index, (text, nodedata, childdata) in sorted(subdata.items()):        
                childnode = self.add_object(node, text, data = nodedata)
                add_children_nodes(childnode, childdata)
        
        data = pickle.load(open(filepath, 'r'))
        roottext, rootdata, treedata = data
        rootitem = self.AddRoot(str(roottext), data = rootdata)
        add_children_nodes(rootitem, treedata)
        
        self.RefreshItemWithWindows(self.GetRootItem())
            
    def save_to_filename(self, filename):
        def get_children_data(node):
            subnode, cookie = self.GetFirstChild(node)
            childdata = {}
            i = 0
            while subnode and subnode.IsOk():
                childdata[i] = (self.GetItemText(subnode),
                                self.GetItemData(subnode),
                                get_children_data(subnode))
                i += 1
                subnode = self.GetNextSibling(subnode)
            return childdata
        treedata = (self.GetItemText(self.GetRootItem()),
                    self.GetItemData(self.GetRootItem()),
                    get_children_data(self.GetRootItem()))
        output = open(filename, 'w')
        pickle.dump(treedata, output)
        output.close()
            
    
    def save(self, event):
        if self.filename:
            self.save_to_filename(self.filename)
        else:
            self.saveAs(None)
    def saveAs(self, event):
        filedog = wx.FileDialog(None, "Save SpecBase As...", style = wx.FD_SAVE,
                                wildcard = "SpecBase|*.sbr|Any|*")
        if filedog.ShowModal() == wx.ID_OK:
            self.filename = filedog.GetPath()
            self.save_to_filename(self.filename)
    
    def addFolder(self, event):
        if not self.base:
            self.raiseObjection("Create a new project first!")
            return
        
        textdog = wx.TextEntryDialog(None, "Folder Name:", "Blais Spectrum Database",
                                     "New Folder", style=wx.OK|wx.CANCEL)        
        if not textdog.ShowModal() == wx.ID_OK:
            return
        foldername = textdog.GetValue()
        
        node = self.GetSelection()
        if not node.IsOk():
            node = self.base
            
        self.add_object(parent = node,
                        text = foldername,
                        data = {'Type':'Folder'})
    
    def addFile(self, event):
        if not self.base:
            self.raiseObjection("Create a new project first!")
            return
        filedog = wx.FileDialog(self, "Select file:", style = wx.FD_OPEN)
        if filedog.ShowModal() != wx.ID_OK:
            return
        
        filepath = filedog.GetPath()
        filename = os.path.basename(filepath)
        ext = filename.split('.')[-1]
        
        node = self.GetSelection()
        if not (node and node.IsOk()):
            node = self.base
        self.add_object(node, filename, filepath, data = {'Type':'file',
                                                          'Filetype':ext,
                                                          'Fullpath':filepath})
    
    def add_spectrum(self, spec_object): # Also currently should handle XICs.
        # SOME CODE HERE takes all the relevant data out of the
        # spectrum data object and puts it into the scanData dict.
        scanData = {'Type':spec_object.type,
                    'Object':spec_object}
        # Also get a suitable name for the scan here, to be shown in the tree.
        if spec_object.type == 'Spectrum':
            scanName = spec_object.filter  
        else:
            rangestring = ', '.join(['%.3f-%.3f' % intervals[0] for intervals
                                     in spec_object.xic_mass_ranges])
            scanName = 'Chrom. MZ(%s)  RT(%.3f-%.3f)' % ((rangestring,) + 
                                                         tuple(spec_object.full_time_range))
        # Also scanData['Type'] should be either 'spectrum' or 'xic', as appropriate.
    
        self.add_object(None, scanName, data = scanData)    
    
    
    def add_object(self, parent = None, text = None, infotext = None,
                   data = {}):
        if (parent and parent != self.GetRootItem()) and not self.base:
            self.raiseObjection("Create a new project first!")
            return
        if not text:
            self.raiseObjection("Can't create title-less object.")
            return
        if not parent:
            parent = self.GetSelection()
            while parent and parent.IsOk() and self.GetItemData(parent)['Type'] != 'Folder':
                parent = self.GetItemParent(parent)
            if not (parent and parent.IsOk()):
                parent = self.base
                
        imageClosed, imageOpened = image_for_data(data)
        newnode = self.AppendItem(parent, text = text,
                                  image = imageClosed, selImage = imageOpened, 
                                  data = data) 
        #if infotext:
            #self.SetItemText(newnode, 1, infotext)
        
        #if self.base == None: # This crashes for some reason.
        if type(self.base) == type(None):
            self.base = newnode
        return newnode
    
    def iterate_over_tree(self):
        item = self.GetFirstItem()
        while item.IsOk():
            yield item
            item = self.GetNextItem()
    
    def onDelete(self, evt):
        node = self.GetSelection()
        if node.IsOk() and node != self.base:
            item, junk = self.GetFirstChild(node)
            if item and item.IsOk():
                makesure = wx.MessageBox("Really remove %s and all sub-items from SpecBase?" % self.GetItemText(node),
                                         style = wx.OK|wx.CANCEL)                
            else:
                makesure = wx.MessageBox("Really remove %s from SpecBase?" % self.GetItemText(node),
                                         style = wx.OK|wx.CANCEL)
            if makesure == wx.OK:
                self.Delete(node)
                
    def exportAllPPT(self, evt):
        if not self.base:
            self.raiseObjection("No initialized SpecBase.")
        
        writePPT(list(iterate_over_tree))
    def exportToPPT(self, evt):
        if not self.base:
            self.raiseObjection("No initialized SpecBase.")
        
        node = self.GetSelection()
        writePPT([node])
        
    def makeSpectralDatabase(self, evt):
        if not self.base:
            self.raiseObjection("Create a new project first!")
            return        
        filedialog = wx.FileDialog(self, 'Save MSP file as...', style = wx.FD_SAVE)
        if filedialog.ShowModal() == wx.ID_OK:
            outputfile = filedialog.GetPath()
        else:
            return        
        
        scanData = []
        for item in self.iterate_over_tree():
            itemdata = self.GetItemData(item)
            if itemdata['Type'] == 'Spectrum':
                specobj = itemdata['Object']
                scan = specobj.scan_data
                seq = specobj.sequence
                name = specobj.filter
                details = {'Comment': '%s|%s' % (seq, name)}
                scanData.append((name, details, scan))      
        if scanData:
            writeMSP(scanData)
        else:
            print "No spectra found; file not written."
        
        
        
        
        

# This handles drops from outside the SpecBase control.
class SBDropTarget(wx.DropTarget):
    def __init__(self, window):
        wx.DropTarget.__init__(self)
        self.dataComp = wx.DataObjectComposite()
        self.fileData = wx.FileDataObject()
        self.scanData = wx.CustomDataObject("scan_data")
        self.dataComp.Add(self.fileData)
        self.dataComp.Add(self.scanData)
        self.SetDataObject(self.dataComp)
        self.window = window

    def OnData(self, x, y, defResult):
        if self.GetData():
            droptype = self.dataComp.GetReceivedFormat().GetType()
            if droptype == wx.DF_FILENAME:
                for filepath in self.fileData.GetFilenames():
                    filename = os.path.basename(filepath)
                    ext = filename.split('.')[-1]
                    self.window.tree.add_object(None, filename,
                                                filepath,
                                                data = {'Type':'file',
                                                        'Filetype':ext,
                                                        'Fullpath':filepath})
            else:
                # CustomDataObject has an inconsistent droptype identifier.
                try:
                    data = pickle.loads(self.scanData.GetData().tobytes())
                except (EOFError, TypeError, AttributeError) as err:
                    print "Invalid drop. " + repr(err)
                    return defResult
                self.window.tree.add_spectrum(data)
                

        return defResult
                

class SpecFrame(wx.Panel, wx.DropTarget):
    def __init__(self, parent, id, organizer):
        wx.Panel.__init__(self, parent, id=id, name='Spectrum Database')

        if organizer:
            self.organizer = organizer
            self.organizer.addObject(self)
        self.aui_pane_obj = None # Set by DrawPanel after initialization.

        self.tree = SpectrumTree(self, -1) # Not wrapped in an extra wx.Panel?   
        self.tree.Create(self)
        self.dropHandler = SBDropTarget(self)
        self.SetDropTarget(self.dropHandler)

        self.menuBar = flatmenu.FlatMenuBar(self, -1)
        (fileMenu, addMenu, editMenu,
         imageMenu, pepCMenu,  dataMenu) = [flatmenu.FlatMenu(self.menuBar) for _ in xrange(6)]
        # File
        for title, helpText, handler in [("New", "Create New SpecBase File", self.tree.new_specbase),
                                         ("Load", "Load a SpecBase File", self.tree.load),
                                         ("Save", "Save SpecBase File", self.tree.save),
                                         ("Save As", "Save SpecBase File As", self.tree.saveAs)]:
            self.Bind(wx.EVT_MENU, handler,
                      fileMenu.Append(-1, title, helpText))
        # Add
        for title, helpText, handler in [("New Folder", "Add Folder", self.tree.addFolder),
                                         ("New File", "Add New File (.PPT/.XLS/.PY)", self.tree.addFile)]:
            self.Bind(wx.EVT_MENU, handler,
                      addMenu.Append(-1, title, helpText)) 
        # Edit
        for title, helpText, handler in [("Edit", "Edit entry", self.tree.onEdit),
                                         ("Delete Entry", "Delete entry", self.tree.onDelete)]:
            self.Bind(wx.EVT_MENU, handler,
                      editMenu.Append(-1, title, helpText))   
        # Export Image
        for title, helpText, handler in [("Export to PPT", "Export all spectra to ppt", self.tree.exportAllPPT),
                                         ("Export current to PPT", "Export only current slide to ppt", 
                                          self.tree.exportToPPT)]:
            self.Bind(wx.EVT_MENU, handler,
                      imageMenu.Append(-1, title, helpText))        
        # PepCalc
        for title, helpText, handler in [("Open PepCalc", "Open PepCalc", self.openPepCalc)]:
            self.Bind(wx.EVT_MENU, handler,
                      pepCMenu.Append(-1, title, helpText)) 
        # Spectrum
        for title, helpText, handler in [("Make Spectral Database", "Make spectral database from all MS2 spectra",
                                          self.tree.makeSpectralDatabase)]:
            self.Bind(wx.EVT_MENU, handler,
                      dataMenu.Append(-1, title, helpText))
            
        for menuname, menu in (('File', fileMenu), ('Add', addMenu), ('Edit', editMenu),
                     ('Images', imageMenu), ('PepCalc', pepCMenu),  ('Database', dataMenu)):
            self.menuBar.Append(menu, menuname)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.menuBar, 0, wx.EXPAND)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer)
    
    def openPepCalc(self, evt):
        # It seems sort of unnecessary- the main BPC button is right there.
        import BlaisPepCalcSlim_aui2
        if not self.organizer.containsType(BlaisPepCalcSlim_aui2.MainBPC):
            import wx.aui as aui
            bpc = BlaisPepCalcSlim_aui2.MainBPC(self.GetParent(), -1, self.organizer)         
            self.GetParent()._mgr.AddPane(bpc, aui.AuiPaneInfo().Left().MaximizeButton(True).MinimizeButton(True).Caption("PepCalc"))
            self.GetParent()._mgr.Update()   
        else:
            bpc = self.organizer.getObjectOfType(BlaisPepCalcSlim_aui2.MainBPC)
            bpc.SetFocus()
    
    def OnClose(self, evt):
        self.organizer.removeObject(self)
        #self.Destroy()
        
if __name__ == "__main__":
    app = wx.App(0)
    window = wx.Frame(None)	
    specbase = SpecFrame(window, -1, None)
    window.Show()
    app.MainLoop()