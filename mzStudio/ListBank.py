import wx, os, sys, glob

import  wx.lib.mixins.listctrl  as  listmix

install_dir = os.path.dirname(__file__)

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
        if self.editable:
            evt.Skip()

    def OnLeft(self, evt):
        if not self.editable:
            for i in range(0, self.GetItemCount()):
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
        #index = self.InsertStringItem(0, seq)
        self.SetStringItem(index, 1, title)
            
        self.SetItemData(index, self.bank_num)
        
    def SetStringItem(self, index, col, data):
            if col in range(2):
                wx.ListCtrl.SetStringItem(self, index, col, data)
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
        wx.Frame.__init__(self,parent,id, 'List Bank   (Right click to hide)', size =(460,240), pos = (50,50), style=wx.CAPTION| wx.CLOSE_BOX |wx.STAY_ON_TOP) #, style=wx.STAY_ON_TOP|wx.FRAME_EX_METAL|wx.FRAME_NO_TASKBAR  
        self.panel = wx.Panel(self, size =(460,260))
        
        #self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING)
        self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING) 
         
        self.listb.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        self.listb.editable=False
       
        self.Save = wx.Button(self.panel, -1, "Save", pos=(0,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.Save)
        self.Load = wx.Button(self.panel, -1, "Load", pos=(45,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnLoad, self.Load)
        self.Delete = wx.Button(self.panel, -1, "Delete", pos=(90,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.Delete)
        self.Clear = wx.Button(self.panel, -1, "Clear", pos=(135,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.Clear)
        self.Stds = wx.Button(self.panel, -1, "Standards", pos=(225,2), size=(60,25))
        self.Bind(wx.EVT_BUTTON, self.OnStds, self.Stds)     
        ebutton = wx.Button(self.panel, -1, "Edit", (180, 2), (40,25))
        self.Bind(wx.EVT_BUTTON, self.OnEdit, ebutton)        
        self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.listb.Bind(wx.EVT_RIGHT_DOWN, self.OnRightUp)
        self.listb.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        
        user_defined = glob.glob(os.path.join(install_dir, r'settings\*_bpc.txt'))
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.user_dict = {}
        pos = 305
        for i, file_name in enumerate(user_defined):
            id = wx.NewId()
            btn = wx.Button(self.panel, id, os.path.basename(file_name).split('_bpc')[0][:3], pos=(pos + (30 * i),2), size=(25,25))
            self.Bind(wx.EVT_BUTTON, self.OnUser, btn)
            self.user_dict[id]=file_name
        
        #self.panel.Bind(wx.EVT_MOTION, self.OnMouse)
        self.Refresh()
        self.Update()
        self.Refresh()
        self.selected = None
        
    def OnClose(self, event):
        self.Hide()
        
    def OnUser(self, event):
        filename = self.user_dict[event.Id]
        self.loaddir = os.path.dirname(filename)
        self.loadfilename = os.path.basename(filename)
        file_r = open(filename, 'r')
        lines = file_r.readlines()
        self.listb.DeleteAllItems()
        for i, line in enumerate(lines):
            self.listb.Populate(line.split('\t')[0].strip(), line.split('\t')[1].strip())
            
        file_r.close()        
        
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
        self.selected=item.GetId() #-------Id is the index within the list.  Keep track of this for other commands
        data = item.GetText()
        if not data:
            return        
        hresult = [i for i, x in enumerate(data) if x == '-']
        indices = (hresult[0], hresult[-1])
        
        nterm = data[0:indices[0]]
        seq = data[indices[0]+1:indices[1]]
        cterm = data[indices[1]+1:]
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
        file_r = open(os.path.join(install_dir, r'PeptideStandards.txt'), 'r')
        lines = file_r.readlines()
        self.listb.DeleteAllItems()
        for line in lines:
            self.listb.Populate(line.strip(), '')
        file_r.close()        

    def OnSave(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.FD_SAVE, wildcard = "text files (*.txt)|")
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
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.FD_OPEN, wildcard = "text files (*.txt)|")
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
        self.listb.DeleteAllItems()
        try:
            for i, line in enumerate(lines):
                self.listb.Populate(line.split('\t')[0].strip(), line.split('\t')[1].strip())
        except:
            wx.MessageBox("Error parsing file.  Format should be\nH-PEPTIDER-OH{tab}Title.\n\nCheck all tabs are in place.")
            
            
        file_r.close()

    def OnDelete(self, event):
        self.listb.DeleteItem(self.selected)
        self.selected=None

    def OnClear(self, event):
        self.listb.DeleteAllItems()
        
        
if __name__ == '__main__':
    app = wx.App(False)
    a = ListBank(None, -1)
    a.Show()
    app.MainLoop()