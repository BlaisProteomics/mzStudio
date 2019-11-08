__author__ = 'Scott Ficarro'
__version__ = '1.0'


import wx
import wx.grid as grid
try:
    from agw import pybusyinfo as PBI
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.pybusyinfo as PBI
#import BlaisPepCalcSlim_aui as BlaisPepCalc
import DatabaseOperations as db    
#import QueryBuilder    
import os
import mzStudio as BlaisBrowser
import re    
import mz_workbench.mz_core as mz_core
from collections import defaultdict
import wx.lib.agw.aui as aui
import copy
from multiplierz.mgf import standard_title_parse

from autocomplete import AutocompleteTextCtrl, list_completer

def peaks_modseq_to_pepcalc_modseq(seq):
    parts = [x[0] for x in re.findall(r'([A-Z](\([\+][0-9]*.[0-9]*\))?)', seq)]
    calcseq = []
    for part in parts:
        if len(part) == 1:
            calcseq.append(part)
        else:
            assert part[0].isalpha() and part[-1] == ')', part
            mod = part[1:].replace('(', '[').replace(')', ']').replace('+', '')
            calcseq.append(mod + part[0])
    return ''.join(calcseq)


class dbGrid(wx.grid.Grid):
    def __init__(self, parent, rows):
        self.parent = parent
        wx.grid.Grid.__init__(self, parent, -1, pos=(0,40), size =(1200, 550))#
        self.CreateGrid(rows,len(self.parent.cols))
        for i, col in enumerate(self.parent.cols):
            self.SetColLabelValue(i, col)
            self.SetColSize(i, len(col)*10)
        for i, member in enumerate(self.parent.rows):
            if i % 1000 == 0:
                print i
            for k, column in enumerate(self.parent.cols):
                self.SetCellValue(i, k, str(member[column]))
        #self.AutoSize()
        #size = self.GetClientSize()
        #self.SetSize(size)
        #self.ForceRefresh()
        #self.Refresh()  
        #a = 1

class dbFrame(wx.Panel):
    def __init__(self, parent, id, bpc):
        #PARENT = AUI FRAME
        #busy = PBI.PyBusyInfo("Building grid...", parent=None, title="Processing...")
        wx.Yield()
        #self.parent = parent
        wx.Panel.__init__(self,parent,id=id, name='mzResult', pos = (50,50))  #, size =(1250,400)      
        self.ordering = "desc"
        self.reverse = False
        self.currentPage = parent.ctrl.GetPage(parent.ctrl.GetSelection())
        self.currentFile = self.currentPage.msdb.files[self.currentPage.msdb.Display_ID[self.currentPage.msdb.active_file]]
        self.ActiveFileNumber = self.currentPage.msdb.active_file
        self.fileName = self.currentPage.msdb.Display_ID[self.ActiveFileNumber]
        self.parent = parent #THIS IS AUI FRAME OBJECT
        self.parentFileName = self.currentFile.FileAbs
        self.bpc = bpc
        
        #------------------------GET DATA FOR GRID
        
        self.rows, self.cols = db.pull_data_dict(self.currentFile.database, 'select * from "peptides"')
        
       
        
            
        
        #-----------------------BUTTONS AND TEXT CONTROLS
        
        #self.query = wx.TextCtrl(self, -1, "select * from peptides;", pos=(60,20)) #, size=(1120,20)
                
        autoTerms = (['"%s"' % x for x in self.currentFile.mzSheetcols] +
                     ['SELECT', 'FROM', 'peptides', 'WHERE', 'DISTINCT',
                      'LIKE', 'GROUP', 'BY', 'ORDER', 'BY', 'COUNT', 'HAVING', 'LIMIT'])
        self.query = AutocompleteTextCtrl(self, completer = list_completer(autoTerms))
        self.query.SetValue('select * from "peptides"')
        
        self.btn = wx.Button(self, -1, "Submit", pos = (40, 20), size= (60,23))
        #self.builder = wx.Button(self, -1, "B", pos = (20, 20), size= (20,20))
        
        #-----------------------CREATE GRID
        self.grid = dbGrid(self, len(self.rows))            
        self.current_cell = wx.TextCtrl(self, -1, self.grid.GetCellValue(0,0), pos=(0,0))#, size=(1120,20)
        #----------------------EVENTS IN DB FRAME
        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelClick)        
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.grid.EnableEditing(False) #Turn off cell editing so cells cannot be overwritten.
        #self.Bind(wx.EVT_BUTTON, self.OnBuilder, self.builder)
        #------------------------------------------------------------Peptigram not yet ready for release.
        #self.peptigram = wx.Button(self, -1, "Peptogram", pos = (0, 20), size= (75,23))
        #self.Bind(wx.EVT_BUTTON, self.OnPeptigram, self.peptigram)
        #------------------------------------------------------------Hide functionality for now.
        self.query.Bind(wx.EVT_KEY_UP, self.OnQKeyUp)
        
        #------------------------FRAME SIZERS
        self.SizeFrame()
        
        self.currentFileNamesSet = set()
        self.curdir = os.path.dirname(self.currentFile.FileAbs).lower()
        self.currentFileNamesSet.add(self.currentFile.Filename.lower())
       
        #self.topSizer = topSizer
        #self.gridSizer = gridSizer
       
        if "File" in self.currentFile.mzSheetcols:
            if self.currentFile.SearchType=="Mascot":
                for row in self.currentFile.rows:
                    if self.currentFile.vendor=='Thermo':
                        currentFileName = self.curdir + '\\' + row["Spectrum Description"].split(".")[0] + '.raw'
                    elif self.currentFile.vendor=='ABI':
                        currentFileName = self.curdir + '\\' + os.path.basename(row["File"])[:-8]
                    self.currentFileNamesSet.add(currentFileName)
        elif 'Source File' in self.currentFile.mzSheetcols:
            # Assumes PEAKS report.
            # Also assumes all files in the report are in the same directory.
            mainfiledir = os.path.dirname(self.currentFile.FileAbs)
            for row in self.currentFile.rows:
                newfile = os.path.join(mainfiledir, row['Source File'])
                self.currentFileNamesSet.add(newfile)
                
            
        self.Check_diff = False
        if len(self.currentFileNamesSet) > 1:
            self.Check_diff = True
        
        self.sub_bank = BlaisBrowser.MS_Data_Manager(self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection()))
        
        #self.sub_bank.addFile(self.currentFile.FileAbs)
        
        #-----------------------------Manually add the existing file to the "sub-bank"
        display_key = self.sub_bank.getFileNum()        
        self.currentFile.FileAbs= self.currentFile.FileAbs.lower()
        self.sub_bank.Display_ID[display_key]=self.currentFile.FileAbs.lower()
        self.sub_bank.files[self.currentFile.FileAbs.lower()]=self.currentFile
    
        self.sub_bank.files[self.currentFile.FileAbs.lower()].mzSheetcols = self.currentFile.mzSheetcols
        self.sub_bank.files[self.currentFile.FileAbs.lower()].rows = self.currentFile.rows
        self.sub_bank.files[self.currentFile.FileAbs.lower()].ID_Dict = self.currentFile.ID_Dict
        self.sub_bank.files
        
        #------------------------------Are there additional files to load?
        if "File" in self.currentFile.mzSheetcols:
            file_set = set()
            if self.currentFile.settings['multiFileOption'] == 'LOAD ALL':
                for row in self.currentFile.rows:
                    file_set.add((self.curdir + '\\' + re.compile('(\S+?.raw)').match(os.path.basename(row['File'])).groups()[0]).lower())
                for name in list(file_set):
                    if name not in [x.lower() for x in self.sub_bank.files.keys()]:
                        print "Loading additional file!"
                        #Current file is not loaded, need to load
                        #currentName=self.curdir + '\\' + re.compile('(\S+?.raw)').match(name).groups()[0] #Gets the rawfilename from the file column
                        print name
                        self.sub_bank.addFile(name)
                        #Need to update sheet information; copy direct from currentObject
                        self.sub_bank.files[name].mzSheetcols = self.currentFile.mzSheetcols
                        self.sub_bank.files[name].rows = self.currentFile.rows
                        self.sub_bank.files[name].fixedmod = self.currentFile.fixedmod
                        self.sub_bank.files[name].database = self.currentFile.database
                        self.sub_bank.files[name].SearchType = self.currentFile.SearchType
                        #print currentGridFilename
                        self.sub_bank.files[name].ID_Dict = self.currentPage.build_ID_dict(self.currentFile.rows, self.currentFile.mzSheetcols, os.path.basename(name))
                        #print "DUMPING"
                        #self.currentPage.dump_ID_Dict(self.sub_bank.files[name]["ID_Dict"])
                        #self.sub_bank.files[currentGridFileName]["ID_Dict"] = self.currentFileObject["ID_Dict"]                    
        
        self.dump_bank()
        self.current_col = 0
        self.current_row = 0
        self.grid.SetRowAttr(0, self.get_active())
        #self.grid.SetColAttr(0, self.get_active())
        self.grid.Refresh()
        #del busy
        self.parent._mgr.Update()
        #----------------TRANSLATIONS TO ALLOW SHORTCUTS IN QUERY BOX
        self.qtrans = {'[var]':'"Variable Modifications"', '[scr]':'"Peptide Score"',
                       '[lk]':'like "%%"', '[pdesc]':'"Protein Description"',
                       '[set1]':'"Accession Number", "Protein Description", "Peptide Sequence", "Variable Modifications", "Experimental mz", "Charge", "Predicted mr", "Delta", "Peptide Score", "Spectrum Description", "Scan", "GeneName"',
                       '~vm':'"Variable Modifications"', '~lk':'like "%%"', '~pepd':'order by "Peptide Score" desc', '~gn':'"GeneName"', '~var':'"Variable Modifications"',
                       '~xc':'"Cross-Correlation"', '~sc':'"Peptide Score"', '~ex':'"Expect"', '~ac':'"Accession"', '~de':'"Protein Description"', '~seq':'"Peptide Sequence"'}

    def OnClose(self, event):
        #if self.aui_pane.name != event.pane.name:
        #    print "%s got event but isn't being closed." % self.aui_pane.name
        #    event.Skip()
        #    return 
    
        self.currentFile.xlsSource=''
        self.currentFile.SearchType = None  
        self.currentFile.database = None
        
        
        self.currentFile.rows, self.currentFile.mzSheetcols = [], []
        self.currentFile.header={}
        
        self.currentFile.fixedmod=""
        self.currentFile.varmod=""
        self.currentFile.ID_Dict={}
        
        self.currentFile.mascot_ID = {}
        
        
        self.currentFile.SILAC={"mode":False, "peaks":(), "method":None} 
        
        self.currentFile.datLink = False
        self.currentFile.viewMascot = False
        self.currentFile.ID=False
        self.currentFile.label_dict={}
        currentPage = self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
        currentPage.Window.UpdateDrawing()        
        
        self.parent.parentFrame.ObjectOrganizer.removeObject(self)
                
        
        print "Db frame close!"


    def SizeFrame(self):
        topSizer = wx.BoxSizer(wx.VERTICAL)        
        gridSizer   = wx.BoxSizer(wx.HORIZONTAL)
        querySizer   = wx.BoxSizer(wx.HORIZONTAL)
        valueSizer   = wx.BoxSizer(wx.HORIZONTAL)
        
        valueSizer.Add(self.current_cell, 1, wx.ALL|wx.EXPAND, 5)
        querySizer.Add(self.btn, 0, wx.ALL, 5)
        #querySizer.Add(self.builder, 0, wx.ALL, 5)
        #-----------------------------------------------------Hide peptigram functionality
        #querySizer.Add(self.peptigram, 0, wx.ALL, 5)
        querySizer.Add(self.query, 1, wx.ALL|wx.EXPAND, 5)
        gridSizer.Add(self.grid, 1, wx.ALL|wx.EXPAND, 5)
        
        topSizer.Add(valueSizer, 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(querySizer, 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(gridSizer, 0, wx.ALL|wx.EXPAND, 5)

        self.SetSizer(topSizer)
        topSizer.Fit(self)               

    #-------------------THIS EVENT CHECKS QUERY BOX WITH EACH KEY PRESS FOR SHORTCUT
    
    def OnQKeyUp(self, evt):
        found = False
        current = self.query.GetValue()
        for key in self.qtrans.keys():
            if current.find(key) > -1:
                found = True
                orig_pos = self.query.GetInsertionPoint()
                current = current.replace(key, self.qtrans[key])
                typed = len(key)
                replaced = len(self.qtrans[key])
                newpoint = orig_pos - typed + replaced
        if found:
            self.query.SetValue(current)
            self.query.SetInsertionPoint(newpoint)
        evt.Skip()
        

    def OnPeptigram(self, evt):
        #Go through self.rows
        #Make peptigram for each unique seq/mod/cg; if more than one seq/mod/cg, make peptigram from most intense
        #Run analysis first?
        pep_dict = {} #Key to max intensity
        max_dict = {} #Key to scan of max intensity
        all_scans = defaultdict(list) #All scans for key
        mz_dict = {} #Key to decal mass
        for row in self.rows:
            seq = row["Peptide Sequence"]
            cg = int(row["Charge"])
            varmod = row["Variable Modifications"]
            spec = row['Spectrum Description']
            if 'MultiplierzMGF' in spec:
                ms1 = standard_title_parse(spec)['scan']
            else:
                ms1 = int(spec.split('.')[1])
            try:
                decal = float(spec.split('|')[1])
            except:
                decal = float(row['Experimental mz'])
            if not varmod:
                varmod = "None"
            key = seq + "|" + str(cg) + '|' + varmod 
            start, stop, scan_array = mz_core.derive_elution_range_by_C12_C13(self.currentFile.m, self.currentFile.scan_dict, int(ms1), decal, int(cg), 0.02, 200)
            scan_array.sort(key=lambda t:t[1], reverse = True)
            intensity = scan_array[0][1] 
            if key in pep_dict.keys(): #KEY ALREADY FOUND
                current_inten = pep_dict[key]
                if intensity > current_inten:
                    pep_dict[key] = intensity
                    max_dict[key] = ms1
                    mz_dict[key] = decal
                    all_scans[key].append(ms1)
                else: #NOT MORE INTENSE; just add to list of all MS2
                    all_scans[key].append(ms1)
            else: #NEW KEY
                pep_dict[key] = intensity
                max_dict[key] = ms1
                mz_dict[key] = decal
                all_scans[key].append(ms1)                
        #Open XIC frame
        self.currentPage = self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
        #self.currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]] 
        self.frm = BlaisBrowser.xicFrame(self.currentPage, self.currentFile, self.currentPage.msdb.active_file) 
        self.frm.Show()
        winMax = self.frm.get_next_available_window()   
        currentRow = self.frm.GetXICEntries()
        trace = 0
        print key
        for key in pep_dict.keys():
            self.frm.grid.SetCellValue(currentRow, 0, str(winMax)) #WINDOW
            self.frm.grid.SetCellValue(currentRow, 1, str(mz_dict[key]-0.02)) #START
            self.frm.grid.SetCellValue(currentRow, 2, str(mz_dict[key]+0.02)) #STOP
            self.frm.grid.SetCellValue(currentRow, 3, "Full ms ") #FILTER
            self.frm.grid.SetCellValue(currentRow, 5, "Auto")
            self.frm.grid.SetCellValue(currentRow, 6, '1')
            self.frm.grid.SetCellValue(currentRow, 7, '1')
            self.frm.grid.SetCellValue(currentRow, 8, 'p')
            
            #SEQ MZ CG SCAN
            self.frm.grid.SetCellValue(currentRow, 9, key.split('|')[0])
            self.frm.grid.SetCellValue(currentRow, 10, str(mz_dict[key]))
            self.frm.grid.SetCellValue(currentRow, 11, key.split('|')[1])
            self.frm.grid.SetCellValue(currentRow, 12, str(max_dict[key]))
            mark_dict = {}
            for scan in all_scans[key]:
                mark_dict[scan]=BlaisBrowser.XICLabel(self.currentFile.m.timeForScan(int(scan)), int(scan), key.split('|')[0], None, cg=int(key.split('|')[1]), fixedmod=self.currentFile.fixedmod, varmod=key.split('|')[2])
                #{9187:XICLabel(current.m.timeForScan(9187), 9187, "Peptide", current.xic[1][1])}
            self.frm.mark_base.append(mark_dict)
            currentRow += 1
        self.frm.OnClick(None)
        self.frm.Destroy()

    def get_default(self):
        activeL = wx.grid.GridCellAttr()
        activeL.SetBackgroundColour(self.grid.GetDefaultCellBackgroundColour())
        activeL.SetTextColour(self.grid.GetDefaultCellTextColour())
        activeL.SetFont(self.grid.GetDefaultCellFont())
        return activeL

    def get_active(self):
        activeL = wx.grid.GridCellAttr()
        activeL.SetBackgroundColour("pink")
        activeL.SetTextColour("black")
        activeL.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        return activeL

    def dump_bank(self):
        #print "---------------------------"
        for member in self.sub_bank.files.keys():
            print self.sub_bank.files[member].FileAbs.lower()

    def OnBuilder(self, event):
        self.QB = QueryBuilder.QueryBuilder(self, id=-1)
        self.QB.Show(True)

    def OnClick(self, event): ####################EXECUTING QUERY
        '''
        
        This function is the event handler for Entering a new Query.
        
        '''
        #busy = PBI.PyBusyInfo("Executing Query...", parent=None, title="Processing...")
        #wx.Yield()
        #try:
        
        #-------------------------------------------------------
        query = self.query.GetValue()
        if query.find("~set1")>-1:
            query = query.replace("~set1", '"Protein Description", "Peptide Sequence", "Variable Modifications" , "Charge" ,"Peptide Score", "Spectrum Description", "Scan"')
        #-------------------------------------------------------
        #self.rows = db.pull_data_dict(self.currentFile.database, query)
        
        #self.cols = db.get_columns(self.currentFile.database, table='peptides' if self.currentFile.SearchType=='Mascot' else 'fdr')
        #if self.currentFile.SearchType=="Mascot":
        try:
            self.rows, self.cols = db.pull_data_dict(self.currentFile.database, query)
            self.currentFile.mzSheetcols = self.cols
        except:
            wx.MessageBox("There was an error processing\nthe query!")
            return
        
        if len(self.rows)==0:
            wx.MessageBox("Query returned no results.")
            return
        
        #if self.currentFile.SearchType=="Pilot":
        #    self.rows = db.pull_data_dict(self.currentFile.database, "select * from fdr;", table='fdr')        
        
        #self.rows, self.cols = db.construct_data_dict(self.currentFile.database, query)
        print self.cols
        self.grid.Destroy()
        self.grid = dbGrid(self, len(self.rows))
        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect)
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelClick)
        self.grid.EnableEditing(False)
        self.SizeFrame()
        self.grid.Refresh()
        self.parent._mgr.Update()        
        #del busy
        #except:
            #del busy
            #dlg = wx.MessageDialog(self, 'There was an error executing the query...!',
                                           #'Alert',
                                           #wx.OK | wx.ICON_INFORMATION
                                           ##wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                           #)
            #dlg.ShowModal()
            #dlg.Destroy() 

    def OnSelect(self, event):
        '''
        
        Highlights a row with light red when selected.
        
        '''
        if event.GetRow() != self.current_row:
            self.grid.SetRowAttr(self.current_row, self.get_default())
            self.grid.SetRowAttr(event.GetRow(), self.get_active())
        #    self.grid.SetColAttr(self.current_col, self.get_active())

        self.grid.Refresh()
        self.current_col = event.GetCol()
        self.current_row = event.GetRow()
        self.current_cell.SetValue(self.grid.GetCellValue(event.GetRow(), event.GetCol()))

    def OnLabelClick(self,event):
        #-----------------------------------
        #----------This code handles clicking on row or column.
        #----------Column click handles sorting by adding sort command to query
        #----------Row click --> if combined, check if different file
        #----------Lookup scan.  Build ID.  Send sequence to BPC.
        self.dump_bank()
        row = event.GetRow()
        col = event.GetCol()
        
        '''
        
        CLICKED ON COLUMN
        
        '''
        
        if col > -1:
            if self.ordering == "desc":
                self.ordering = 'asc'
            else:
                self.ordering = 'desc'
            curQ = self.query.GetValue()
            #select * from peptides where "X" like "%%";
            q = curQ.find("order by")
            if  q > -1:
                if curQ.endswith(';'):
                    curQ= curQ[:(q-1)]
                else:
                    curQ = curQ[:q]
            else:
                if curQ.endswith(';'):
                    curQ=curQ[:-1]
            curQ += ' order by "' + self.cols[col] + '" ' + self.ordering #+ ';' 
            #print curQ
            self.query.SetValue(curQ)
            self.OnClick(None)
                
                
        '''
        
        CLICKED ON ROW
        
        '''        
        if row > -1:
            if row != self.current_row:
                #------------------HIGHLIGHT SELECTED ROW
                self.grid.SetRowAttr(self.current_row, self.get_default())
                self.grid.SetRowAttr(row, self.get_active())
                self.current_row = row
                #self.grid.SelectRow(row)
                self.grid.SetGridCursor(row, self.current_col)
                self.grid.Refresh()
            currentGridFileName = None
            if self.Check_diff:
                #print self.currentFile.SearchType
                if self.currentFile.SearchType=='Mascot':
                    spec_lookup = "Spectrum Description"
                    spec_index = 0
                elif self.currentFile.SearchType == "PEAKS":
                    spec_lookup = 'Source File'
                    spec_index = 0
                else:
                    spec_lookup = "Spectrum" #???
                    spec_index = 3
                #spec_lookup = "Spectrum Description" if self.currentFile.SearchType=='Mascot' else "Spectrum"
                spec_index = 0 if self.currentFile.SearchType=='Mascot' else 3
                if self.currentFile.SearchType == "PEAKS":
                    currentGridFileName = os.path.join(self.curdir, self.grid.GetCellValue(row, self.cols.index("Source File"))).lower()
                elif self.currentFile.vendor=='Thermo':
                    currentGridFileName = (self.curdir + '\\' + self.grid.GetCellValue(row, self.cols.index("Spectrum Description")).split(".")[0] + '.raw' if self.currentFile.SearchType=='Mascot' else self.curdir + '\\' + self.grid.GetCellValue(row, self.cols.index("File")).split(".")[0].replace("_RECAL",'') + '.raw').lower()
                #elif self.currentFile.vendor=='ABI':
                #    currentGridFileName = self.curdir + '\\' + os.path.basename(self.grid.GetCellValue(row, self.cols.index("File")))[:-8]
                if self.currentFile.FileAbs.lower() != currentGridFileName:
                    #Switched files, need to update self and parent
                    if currentGridFileName.lower() not in [x.lower() for x in self.sub_bank.files.keys()]:
                        #Current file is not loaded, need to load
                        self.sub_bank.addFile(currentGridFileName)
                        #Need to update sheet information; copy direct from currentObject
                        self.sub_bank.files[currentGridFileName].mzSheetcols = self.currentFile.mzSheetcols
                        self.sub_bank.files[currentGridFileName].rows = self.currentFile.rows
                        self.sub_bank.files[currentGridFileName].fixedmod = self.currentFile.fixedmod
                        self.sub_bank.files[currentGridFileName].database = self.currentFile.database
                        self.sub_bank.files[currentGridFileName].SearchType = self.currentFile.SearchType
                        #print currentGridFileName
                        self.sub_bank.files[currentGridFileName].ID_Dict = self.currentPage.build_ID_dict(self.currentFile.rows,
                                                                                                          self.currentFile.mzSheetcols,
                                                                                                          os.path.basename(currentGridFileName),
                                                                                                          file_object = self.currentFile)
                        #print "DUMPING"
                        self.currentPage.dump_ID_Dict(self.sub_bank.files[currentGridFileName].ID_Dict)
                        self.parent.ctrl.GetPageInfo(0).caption = os.path.basename(currentGridFileName)
                        #self.sub_bank.files[currentGridFileName]["ID_Dict"] = self.currentFileObject["ID_Dict"]
                    #To switch, need to delete dictionary entry in parent msdb
                    ##print "Attempting delete..."
                    ##print self.parent.msdb.files[self.currentFile.FileAbs]
                    del self.currentPage.msdb.files[self.currentFile.FileAbs.lower()]
                    #Need to update with currentFile
                    ##print currentGridFileName
                    self.currentPage.msdb.files[currentGridFileName] = self.sub_bank.files[currentGridFileName]
                    self.currentPage.msdb.Display_ID[self.ActiveFileNumber]=currentGridFileName
                    self.currentFile = self.sub_bank.files[currentGridFileName]
            if not currentGridFileName:
                currentGridFileName = self.currentFile.FileAbs.lower()
            
            # mzSheetcols is also set somewhere else, but only sometimes, and not
            # reliably reset when a new file is loaded.
            self.currentFile.mzSheetcols = [self.grid.GetColLabelValue(x) for x in range(self.grid.GetNumberCols())]
            
            #--------------LOOK UP SCAN NUMBER    
            if self.currentFile.vendor=='Thermo':
                if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                    if "Spectrum Description" in self.currentFile.mzSheetcols:
                        desc = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Spectrum Description"))
                    else:
                        wx.MessageBox("No spectrum description column!\nCan't get scan number!", "mzStudio")
                        return
                    if 'MultiplierzMGF' in desc:
                        scan = int(standard_title_parse(desc)['scan'])
                    elif 'Locus' in desc:
                        #scan = (int(desc.split('.')[3]) * self.currentFile.m.exp_num) + int(desc.split('.')[4].split()[0])-1# MAY NOT BE CORRECT
                        scan = self.currentFile.m.make_implicit[int(desc.split('.')[3]),
                                                                   int(desc.split('.')[4].split()[0])]
                    else:
                        scan = int(desc.split(".")[1])
                elif self.currentFile.SearchType == "PEAKS":
                    if "Precursor Id" in self.currentFile.mzSheetcols:
                        prec_num = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Precursor Id"))
                        scan = self.currentFile.m.scan_for_precursor(prec_num)
                    else:
                        scan = int(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("scan")))
                else:
                    # Proteome Discoverer
                    if self.currentFile.FileAbs.lower().endswith(".wiff"):
                        scan = int(float(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("scan"))))
                    if self.currentFile.FileAbs.lower().endswith(".raw"):
                        scan = int(float(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("First Scan"))))
                    #scan = int(self.currentFile.mzSheetcols.index("First Scan"))
            elif self.currentFile.vendor=='mgf':
                rowdesc = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Spectrum Description"))
                try:
                    rowscannum = standard_title_parse(rowdesc)['scan']
                except:
                    rowscannum = rowdesc.split(".")[1]
                                
                scan = self.currentFile.scan_dict[int(rowscannum)] # I assume its not an X-to-X dict in non-MGF cases.                 
            elif self.currentFile.vendor=='ABI':
                scan = int(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Spectrum Description")).split(".")[3])-1
                try:
                    exp = str(int(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Spectrum Description")).split(".")[4].strip())-1)
                except:
                    exp = str(int(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Spectrum Description")).split(".")[4].split(" ")[0].strip())-1)                        

            self.currentFile.scanNum = scan
            if self.currentFile.vendor=='ABI':
                self.currentFile.experiment = exp
            self.currentPage.msdb.set_scan(scan, self.ActiveFileNumber)
           
            #--------------BUILD CURRENT ID
            if self.currentFile.vendor=='Thermo':
                self.currentPage.msdb.build_current_ID(currentGridFileName, scan, 'Thermo')
                if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Peptide Sequence"))
                elif self.currentFile.SearchType == "PEAKS":
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Peptide"))
                    #sequence = sequence.replace('(', '[').replace(')', ']').replace('+', '')
                    sequence = peaks_modseq_to_pepcalc_modseq(sequence)
                else: # Proteome Discoverer
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Annotated Sequence")).upper()                
            if self.currentFile.vendor=='mgf':
                self.currentPage.msdb.build_current_ID(currentGridFileName, scan, 'mgf')
                if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Peptide Sequence"))
                else:
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Annotated Sequence"))                
            if self.currentFile.vendor=='ABI':
                exp = self.currentFile.experiment
                #self.currentPage.msdb.build_current_ID(currentGridFileName, (scan-1, str(int(exp)-1)), 'ABI')
                self.currentPage.msdb.build_current_ID(currentGridFileName, (scan, exp), 'ABI')
                if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Peptide Sequence"))
                else: # Proteome Discoverer
                    sequence = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Annotated Sequence")).upper()
            try:
                if self.currentPage.msdb.files[currentGridFileName]['fd']['reaction'] == 'etd':
                    self.bpc.b.FindWindowByName('ions').SetValue('c/z')
                else:
                    self.bpc.b.FindWindowByName('ions').SetValue('b/y')
            except AttributeError:
                pass
            
            try:
                if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                    score = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Peptide Score"))
                else:
                    score = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("XCorr"))
                self.currentFile.score = score
            except ValueError:
                pass # Input dummy value 
            pa = re.compile('([a-z]*[A-Z]+?)')
            peptide = pa.findall(sequence)
            fixedmod = self.currentFile.fixedmod
            if self.currentFile.SearchType in ['Mascot', 'X!Tandem', 'COMET']:
                varmod = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Variable Modifications"))
            elif self.currentFile.SearchType == "PEAKS":
                varmod = ''
            else:
                varmod = self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Modifications"))
            if not varmod:
                varmod = ''
            #print "---***"
            #print sequence
            #print varmod
            #print fixedmod
            peptide_container = mz_core.create_peptide_container(sequence, varmod, fixedmod)
            #print peptide_container
            current_sequence = ''
            for member in peptide_container:
                current_sequence += member
            self.bpc.b.FindWindowByName("sequence").SetValue(current_sequence)
            c_mod_dict = {"C-Term(Methyl)" : "methyl ester",
                          'Methyl:2H(3)' : "d3 methyl ester"}
            mod_dict = {'iTRAQ4plex': 'iTRAQ',
                      'TMT6plex': 'TMT',
                      'TMT': 'cTMT',
                      'iTRAQ8plex': 'iTRAQ8plex',
                      'HGly-HGly': 'HCGlyHCGly',
                      'HCGly-HCGly': 'HCGlyHCGly',
                      'HCGly-HCGly-HCGly-HCGly': 'HCGlyHCGlyHCGlyHCGly',
                      'HNGly-HNGly-HNGly-HNGly': 'HNGlyHNGlyHNGlyHNGly',
                      'HNGly-HNGly': 'HNGlyHNGly',
                      'LbA-LbA': 'LbALbA',
                      'HbA-HbA': 'HbAHbA',
                      'LbA-HbA': 'LbAHbA',
                      'Acetyl': 'Acetyl',
                      'Propionyl': 'Propionyl',
                      'Phenylisocyanate': 'Phenylisocyanate'}
            #print self.currentFile.SearchType
            if self.currentFile.SearchType in ["Mascot", "Proteome Discoverer"]:
                #print "NTERM MODS!"
                if fixedmod == None:
                    fixedmod = ''
                for mod in fixedmod.split(","):
                    mod = mod.strip()
                    #print mod
                    if mod.lower().find("n-term") > -1:
                        mod = mod.split(" ")[0]
                        mod = mod.strip()
                        #print mod_dict[mod]
                        self.bpc.b.FindWindowByName("nTerm").SetValue(mod_dict[mod])
                for mod in fixedmod.split(","):
                    mod = mod.strip()
                    #print mod
                    if mod.lower().find("c-term") > -1:
                        mod = mod.split(" ")[0]
                        mod = mod.strip()
                        #print mod_dict[mod]
                        self.bpc.b.FindWindowByName("cTerm").SetValue(c_mod_dict[mod])         
                        
                for mod in varmod.split(";"): #N-term: Acetyl
                    mod = mod.strip()
                    #print mod
                    if mod.lower().find("n-term") > -1:
                        mod = mod.split(" ")[1]
                        mod = mod.strip()
                        #print mod_dict[mod]
                        self.bpc.b.FindWindowByName("nTerm").SetValue(mod_dict[mod])
                    if mod.lower().find("c-term") > -1:
                        if self.currentFile.SearchType == "Mascot":
                            mod = mod.split(" ")[1]
                            mod = mod.strip()
                            #print mod_dict[mod]
                            self.bpc.b.FindWindowByName("cTerm").SetValue(c_mod_dict[mod])   
                        if self.currentFile.SearchType == 'Proteome Discoverer':
                            self.bpc.b.FindWindowByName("cTerm").SetValue(c_mod_dict[mod]) 
                       
                
            self.bpc.b.OnCalculate(None)
            #----------------------IF SILAC MODE, UPDATE SILAC PEAKS
            if self.currentFile.SILAC["mode"]:
                #calc peaks for SILAC!
                #light medium heavy
                multimod = False
                if self.currentFile.SILAC["method"]=='SILAC K+4 K+8 R+6 R+10 [MD]':
                    charge = int(float(self.grid.GetCellValue(row, self.currentFile.mzSheetcols.index("Charge"))))
                    light = ''
                    for member in peptide_container:
                        if member[-1:] not in ["R","K"]:
                            light += member
                        else:
                            if member in ['pK', 'pdK', 'pseK']:
                                light += ['pK']
                                multimod = True
                            else:
                                light += member[-1:]
                    #light = ''.join([x[-1:] for x in peptide_container])
                    if not multimod:
                        medium = light.replace("K", "deutK").replace("R", "silacR")
                        heavy = light.replace("K", "seK").replace("R", "sR")
                    else:
                        #NEED TO ACCOUNT FOR POSSIBILITY OF MIXED pK and regular K.
                        #ONLY CONVERT pK
                        # K would go to deutK or seK while prK would go to pdK or pseK
                        medium = ''
                        heavy = ''
                        for member in peptide_container:
                            if member == 'K':
                                medium += 'deutK'
                                heavy += 'seK'
                            elif member == 'pK':
                                medium += 'pdK'
                                heavy += 'pseK'
                            else:
                                medium += member
                                heavy += member
                                
                        medium = medium.replace("R", "silacR")
                        heavy = heavy.replace("R", "sR")
                        
                    light_mz, b ,y  = mz_core.calc_pep_mass_from_residues(light, cg=charge)
                    medium_mz, b, y = mz_core.calc_pep_mass_from_residues(medium, cg=charge)
                    heavy_mz, b, y = mz_core.calc_pep_mass_from_residues(heavy, cg=charge)
                    self.currentFile.SILAC["peaks"]=(light_mz, medium_mz, heavy_mz)
            self.currentPage.Refresh()
            self.dump_bank()
            self.currentPage.Window.UpdateDrawing()
            