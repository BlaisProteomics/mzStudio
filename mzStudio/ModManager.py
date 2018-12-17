__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx, os, sys, re

import  wx.lib.mixins.listctrl  as  listmix

import mz_workbench.mz_masses as mz_masses

from collections import defaultdict

class TestListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin,
                   listmix.ColumnSorterMixin):  #

    def __init__(self, parent, panel, ID, size = (800,280), pos=(0,30), style=0):
        self.parent = parent
        wx.ListCtrl.__init__(self, panel, ID, pos, size, style)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        #listmix.ColumnSorterMixin.__init__(self, 5)
        #self.Populate()
        listmix.TextEditMixin.__init__(self)
        #self.editor.Disable()
        #self.editor.RemoveSelection()
        #self.editor.Destroy()
        #self.editor.SetCanFocus(False)
        self.InsertColumn(0, "Token")
        self.InsertColumn(1, "Title")
        self.InsertColumn(2, "Composition")
        self.InsertColumn(3, "MonoIsotopic")
        self.InsertColumn(4, "Average")
        self.InsertColumn(5, "Group")
        self.SetColumnWidth(0, 80)
        self.SetColumnWidth(1, 150)
        self.SetColumnWidth(2, 250)
        self.SetColumnWidth(3, 100)
        self.SetColumnWidth(4, 100)
        self.SetColumnWidth(5, 100)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeft)
        #self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.LeftD)
        self.bank_num = 0
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        #self.Select(0,0)
        #self.editor.Hide()
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 6)
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
            #evt.Skip()

    def convertToComp(self, token):
        compstring = ''
        res_dict = mz_masses.res_dict[token]
        res_order = ['C', 'H', 'N', 'O', 'P', 'S', 'C13', 'N15']
        for key in res_dict.keys():
            if res_dict[key] > 0:
                compstring += key + '(' + str(res_dict[key]) + ') '
        return compstring
    
    def convertFromComp(self, comp):
        return comp.replace('(', ':').replace(')',',').strip()[:-1]

    def GetListCtrl(self):
        return self

    def Populate(self, token, title, composition, group):
        # for normal, simple columns, you can add them like this:
        self.bank_num += 1
        index = self.InsertStringItem(sys.maxint, token)
        #index = self.InsertStringItem(0, seq)
        self.SetStringItem(index, 1, title)
        self.SetStringItem(index, 2, self.convertToComp(token)) # str(composition)
        self.SetStringItem(index, 3, str(mz_masses.calc_mass(mz_masses.res_dict[token], massType='mi')))
        self.SetStringItem(index, 4, str(mz_masses.calc_mass(mz_masses.res_dict[token], massType='av')))
        self.SetStringItem(index, 5, group)
        print self.bank_num
        self.SetItemData(index, self.bank_num)
        self.itemDataMap[self.bank_num]=(token, title, self.convertToComp(token), float(mz_masses.calc_mass(mz_masses.res_dict[token], massType='mi')), float(mz_masses.calc_mass(mz_masses.res_dict[token], massType='av')), group)
        
        
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

class ModBank(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self,parent,id, 'Mod Manager', size =(810,340), pos = (50,50), style=wx.CAPTION|wx.CLOSE_BOX) #, style=wx.STAY_ON_TOP|wx.FRAME_EX_METAL|wx.FRAME_NO_TASKBAR
        self.panel = wx.Panel(self, size =(810,340))
        
        #self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING)
        self.listb = TestListCtrl(self.parent, self.panel, -1, style=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_SORT_ASCENDING) 
         
        self.listb.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        #self.listb.editable=False
       
        self.Save = wx.Button(self.panel, -1, "Save", pos=(0,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.Save)
        #self.Load = wx.Button(self.panel, -1, "L", pos=(30,2), size=(25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnLoad, self.Load)
        self.Delete = wx.Button(self.panel, -1, "Delete", pos=(45,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self.Delete)
        #self.Clear = wx.Button(self.panel, -1, "C", pos=(90,2), size=(25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnClear, self.Clear)
        #self.Stds = wx.Button(self.panel, -1, "Standards", pos=(150,2), size=(60,25))
        #self.Bind(wx.EVT_BUTTON, self.OnStds, self.Stds)  
        
        #ComboBox = wx.ComboBox(self.panel, -1, pos=(120, 2), size=(25,25), value=eachList[eachInit], choices=eachList)
        
        #ebutton = wx.Button(self.panel, -1, "E", (120, 2), (25,25))
        #self.Bind(wx.EVT_BUTTON, self.OnEdit, ebutton)        
        self.NewEntry = wx.Button(self.panel, -1, "New", pos=(90,2), size=(40,25))
        self.Bind(wx.EVT_BUTTON, self.OnNew, self.NewEntry)        
        self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.listb.Bind(wx.EVT_RIGHT_DOWN, self.OnRightUp)
        self.listb.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
        #self.listb.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.BeginEdit)
        self.listb.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.EndEdit)
        #self.panel.Bind(wx.EVT_MOTION, self.OnMouse)
        self.pa = re.compile('([A-Z]+[a-z]*)[ ]*\(*([0-9]+)\)*')
        
        
        file_r = open(os.path.join(os.path.dirname(__file__), r'mz_workbench\files\new_res_list.txt'), 'r')
        lines = file_r.readlines()
        #self.listb.DeleteAllItems()

        groupsSet = set()
        groupsSet.add('All')
        
        data_dict = defaultdict(dict)
        for line in lines:
            entry = line.split('|')
            token = entry[0].strip()
            title = entry[1].strip()
            composition = entry[2].strip()
            try:
                group = entry[3].strip()
            except IndexError:
                group = "Unknown"
            groupsSet.add(group)
            #print composition
            data_dict[token]={"title":title, "comp":composition, "group":group}
        self.data_dict = data_dict
        choiceList = list(groupsSet)
        choiceList.sort()
        self.groupSelection = wx.ComboBox(self.panel, -1, pos=(260, 2), size=(200,50), value='All', choices=choiceList)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect, self.groupSelection)        
        self.BuildList(self.groupSelection.GetValue())
        #------------------------------Original code that built list directly from text file.  Now above reads
        #------------------------------To data dictionary
        #for line in lines:
            #entry = line.split('|')
            #token = entry[0].strip()
            #title = entry[1].strip()
            #composition = entry[2].strip()
            #group = entry[3].strip()
            #groupsSet.add(group)
            #print composition
            #self.listb.Populate(token, title, composition, group)
            
        file_r.close()          
    
        self.Refresh()
        self.Update()
        self.Refresh()
        self.selected = None
        
    def BuildList(self, select_group):
        self.listb.DeleteAllItems()
        self.listb.bank_num=0
        for key in self.data_dict.keys():
            token = key
            title = self.data_dict[key]["title"]
            composition = self.data_dict[key]["comp"]
            group = self.data_dict[key]["group"]
            print composition
            print token
            if (select_group == 'All') or (select_group == group):
                self.listb.Populate(token, title, composition, group) 
        for x in range(0, self.listb.ItemCount):
            if x % 2 == 1:
                #print "Set blue..."
                self.listb.SetItemBackgroundColour(x, "light blue")            
        
    def OnNew(self, evt):
        self.listb.Populate('', '', '', '')
        
    def OnSelect(self, evt):
        print "EVENT SELECT"
        self.BuildList(self.groupSelection.GetValue())
        
    def OLD_EndEdit(self, evt):
        '''

        This is the old version.
        
        '''
        print "End Edit event"
        item = evt.GetItem()
        selected=item.GetId()     
        print item.GetText()
        print selected
        #self.GetItemCount()
        #self.GetItem(9,2).GetText()  
        if evt.Column == 2:
            new_CHNOPS_dict = dict([(x, int(y)) for (x, y) in self.pa.findall(item.GetText())])
            self.listb.SetStringItem(selected, 3, str(mz_masses.calc_mass(new_CHNOPS_dict, massType='mi')))
            self.listb.SetStringItem(selected, 4, str(mz_masses.calc_mass(new_CHNOPS_dict, massType='av')))            
            #self.result.SetValue(str(mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in self.pa.findall(self.CHNOPSdata.GetValue())]))))
            
            
    def BeginEdit(self, evt):
        item = evt.GetItem()
        selected=item.GetId()         
        self.startEditToken = self.listb.GetItem(selected, 0).GetText()
        evt.Skip()
        
    def EndEdit(self, evt):
        print "End Edit event"
        item = evt.GetItem()
        selected=item.GetId()     
        print item.GetText()
        print selected
        #self.GetItemCount()
        #self.GetItem(9,2).GetText()  
        
        if evt.Column == 0:
            print "EDIT token"
            print "Original"
            print self.listb.GetItem(selected, 0).GetText()
            #print self.startEditToken
            print "New"
            print item.GetText()
            
            print "Make new entry"
            entry = self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            print entry
            self.data_dict[item.GetText()]=entry
            
            print "Delete old entry"
            del self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            
            print self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            print self.data_dict[item.GetText()]
            #entry = self.data_dict[self.startEditToken]
            
            #print self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            #self.data_dict[self.listb.GetItem(selected, 0).GetText()]['title']=item.GetText()
            #print "To"
            #print self.data_dict[self.listb.GetItem(selected, 0).GetText()]              
        
        if evt.Column == 1:
            print "EDIT TITLE"
            print self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            self.data_dict[self.listb.GetItem(selected, 0).GetText()]['title']=item.GetText()
            print "To"
            print self.data_dict[self.listb.GetItem(selected, 0).GetText()]                
            
        if evt.Column == 2:
            print "EDIT COMPOSITION"
            
            new_mod_data = item.GetText()
            
            
            new_CHNOPS_dict = dict([(x, int(y)) for (x, y) in self.pa.findall(item.GetText())])
            self.listb.SetStringItem(selected, 3, str(mz_masses.calc_mass(new_CHNOPS_dict, massType='mi')))
            self.listb.SetStringItem(selected, 4, str(mz_masses.calc_mass(new_CHNOPS_dict, massType='av')))
            print "Change From"
            print self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            self.data_dict[self.listb.GetItem(selected, 0).GetText()]['comp']=self.listb.convertFromComp(item.GetText())
            print "To"
            print self.data_dict[self.listb.GetItem(selected, 0).GetText()]
            #self.result.SetValue(str(mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in self.pa.findall(self.CHNOPSdata.GetValue())]))))  
            
        if evt.Column == 5:
            print "EDIT GROUP"            
            self.data_dict[self.listb.GetItem(selected, 0).GetText()]['group']=item.GetText()
            
        evt.Skip()
    
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
        #data = item.GetText().split('-')
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

    def ValidateList(self):
        file_w = open(os.path.join(os.path.dirname(__file__), r'mz_workbench\files\temp_list.txt'), 'w')
        for key in [x for x in self.data_dict.keys() if x]:
            entry = self.data_dict[key]
            line = key + '|' + entry['title'] + '|' + entry['comp'] + '|' + entry['group'] + '\n'
            file_w.write(line)
        file_w.close()        

    def OnSave(self, event):
            #dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "text files (*.txt)|")
            #if dlg.ShowModal() == wx.ID_OK:
                #filename=dlg.GetFilename()
                #dir = dlg.GetDirectory()
                #os.chdir(dir)
            #dlg.Destroy()
            #self.savedir = dir
            #self.savefilename = filename
            #print dir
            #print filename
            #if filename.find(".txt") == -1:
                #filename += ".txt"
                #self.savefilename = filename
                
            file_w = open(os.path.join(os.path.dirname(__file__), r'mz_workbench\files\new_res_list.txt'), 'w')
                
            #file_w = open(dir + '\\' + filename, 'w')
            
            for key in [x for x in self.data_dict.keys() if x]:
                entry = self.data_dict[key]
                line = key + '|' + entry['title'] + '|' + entry['comp'] + '|' + entry['group'] + '\n'
                file_w.write(line)
        
            file_w.close()

    def OLD_OnSave(self, event):
        '''
        
        This is the old Save command.  This went from the list.  The issue with this is that it required the entire list to be displayed.
        The new one saves from the data_dictionary directly
        
        '''
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
            file_w.write(self.listb.GetItemText(i,0) + '|' + self.listb.GetItemText(i,1) + '|' + self.listb.GetItemText(i,2).replace('(', ':').replace(')',',')[:-2] + '|' + self.listb.GetItemText(i,5) + '\n')      
            #a[1:-1].replace("'", '')
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
        self.listb.DeleteAllItems()
        for i, line in enumerate(lines):
            self.listb.Populate(line.split('\t')[0].strip(), line.split('\t')[1].strip())
            
        file_r.close()

    def OnDelete(self, event):
        if self.selected:
            self.listb.DeleteItem(self.selected)
            self.selected=None
        else:
            wx.MessageBox("Select a row to delete.\nEntire row should be highlighted.")

    def OnClear(self, event):
        self.listb.DeleteAllItems()
        
        
if __name__ == '__main__':
    app = wx.App(False)
    a = ModBank(None, -1)
    a.Show()
    app.MainLoop()