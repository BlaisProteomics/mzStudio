import wx
import wx.grid




class SingleID_Grid(wx.grid.Grid):  #, glr.GridWithLabelRenderersMixin
    def __init__(self, parent, row, *args, **kw):
        wx.grid.Grid.__init__(self, parent, id=-1, size=(950,200), pos=(0,0))
        #glr.GridWithLabelRenderersMixin.__init__(self)
        self.CreateGrid(len(row.keys()) + 1,2)  #ROWS, COLUMNS
        
        for i, setting in enumerate([("Attribute", 100), ("Value", 250)]):
            self.SetColLabelValue(i, setting[0])
            self.SetColSize(i, setting[1])
            
        for i, key in enumerate(row.keys()):
            self.SetCellValue(i, 0, key)
            self.SetCellValue(i, 1, str(row[key]))
            

class SingleID_Frame(wx.Frame):
    def __init__(self, parent, currentFile, fileID, row, organizer, header):
        wx.Frame.__init__(self, parent, -1, "Single ID Frame", size=(400,300))
        self.panel = SingleID_Panel(self, currentFile, fileID, row, organizer, header)

class SingleID_Panel(wx.Panel):
    '''
    
    Shows results from single spectrum search.
    
    '''
    def __init__(self, parent, currentFile, fileID, psm, organizer, header, searchMode):
        
        self.key_dict = {'Mascot': (u'--------------------------------------------------', 'Header'),
                    'Comet': (u'Data', u'Program')}
        
        self.organizer = organizer
        if organizer:
            organizer.addObject(self)
        self.currentFile = currentFile
        self.fileID = fileID
        self.parent = parent
        wx.Panel.__init__(self, parent, size =(280,670), pos = (50,50))
        self.psm = psm
        self.searchMode = searchMode
        header_dict = {}
        
        if header:
            for _dict in header:
                _val = _dict[self.key_dict[searchMode][0]]
                _key = _dict[self.key_dict[searchMode][1]]
                header_dict[_key]=_val
            
        self.header_dict = header_dict
        
        #self.panel = wx.Panel(self, -1)
    
        self.grid = SingleID_Grid(self, psm)
        #self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        #self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        
        #self.XICbtn = wx.Button(self, -1, "XIC", size=(25,25), pos = (0, 210))
        #self.Bind(wx.EVT_BUTTON, self.OnXICbtn, self.XICbtn)
        self.saveButton = wx.Button(self, -1, "Export", size=(40,25), pos = (35, 210))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.saveButton)
        self.BPCButton = wx.Button(self, -1, "PepCalc", size=(60,25), pos = (85, 210))
        self.Bind(wx.EVT_BUTTON, self.OnBPCButton, self.BPCButton)
        #self.defaultButton = wx.Button(self.panel, -1, "Delete", size=(40,25), pos = (130, 210))
        #self.Bind(wx.EVT_BUTTON, self.OnDefault, self.defaultButton)        
        #self.ToggleWindowStyle(wx.STAY_ON_TOP)
        #self.scanButton = wx.Button(self.panel, -1, "Scan Filters", size=(150,25), pos = (355, 210))
        #self.Bind(wx.EVT_BUTTON, self.OnScan, self.scanButton)             
        
        
        #for j in range(counter, 150):
        #    self.mark_base.append({})
        #self.radiobox = wx.RadioBox(self.panel, -1, label='Parameters', pos=(150, 210), size=wx.DefaultSize, choices=['Start\Stop', 'Center\Width'], majorDimension=2, style=wx.RA_SPECIFY_COLS | wx.NO_BORDER) #
        #self.radiobox.Hide()
        #self.Bind(wx.EVT_RADIOBOX, self.OnRadio, self.radiobox)
        #self.type = "SS"
    
    def update_header(self, new_header):
        header_dict = {}
        for _dict in new_header:
            _val = _dict[self.key_dict[self.searchMode][0]]
            _key = _dict[self.key_dict[self.searchMode][1]]
            header_dict[_key]=_val
                
        self.header_dict = header_dict    
    
    def OnXICbtn(self, evt):
        pass
    
    def OnSave(self, event):
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "Excel files (*.xlsx)|")
        
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()            
            self.savedir = dir
            self.savefilename = filename
            if not filename.endswith('xlsx'): filename += '.xlsx'
            import multiplierz.mzReport as mzReport
            
            wtr = mzReport.writer(dir + '\\' + filename, columns=self.psm.keys(), sheet_name='Data')
            
            wtr.write(self.psm)
            
            wtr.close()
            wx.MessageBox("Done!", 'mzStudio')
            dlg.Destroy()
        else:
            return
        
    
    def OnBPCButton(self, evt):
        
        mod_dict = {'iTRAQ4plex': 'iTRAQ',
                    'TMT6plex': 'TMT',
                    'TMT': 'cTMT',
                    'iTRAQ8plex': 'iTRAQ8plex',
                    'Acetyl': 'Acetyl',
                    'Propionyl': 'Propionyl',
                    'Phenylisocyanate': 'Phenylisocyanate'}        
        
        
        import BlaisPepCalcSlim_aui2
        if not self.organizer.containsType(BlaisPepCalcSlim_aui2.MainBPC):
            import wx.lib.agw.aui as aui
            bpc = BlaisPepCalcSlim_aui2.MainBPC(self.parent, -1, self.organizer)         
            self.parent._mgr.AddPane(bpc, aui.AuiPaneInfo().Left().MaximizeButton(True).MinimizeButton(True).Caption("PepCalc"))
            self.parent._mgr.Update()
        else:
            bpc = self.organizer.getObjectOfType(BlaisPepCalcSlim_aui2.MainBPC)
            
        sequence = self.psm['Peptide Sequence']
        varmod = self.psm['Variable Modifications']
        if self.searchMode == 'Mascot':
            fixedmod = self.header_dict['Fixed modifications']
            for mod in fixedmod.split(","):
                mod = mod.strip()
                if mod.find("N-term") > -1:
                    mod = mod.split(" ")[0]
                    mod = mod.strip()
                    bpc.b.FindWindowByName("nTerm").SetValue(mod_dict[mod])             
        elif self.searchMode == 'Comet': 
            aamods = ['add_A_alanine','add_C_cysteine','add_D_aspartic_acid','add_E_glutamic_acid','add_F_phenylalanine','add_G_glycine','add_H_histidine','add_I_isoleucine','add_K_lysine','add_L_leucine','add_M_methionine','add_N_asparagine','add_P_proline','add_Q_glutamine','add_R_arginine','add_S_serine','add_T_threonine','add_V_valine','add_W_tryptophan','add_Y_tyrosine'] #'add_Cterm_peptide','add_Cterm_protein', 'add_Nterm_peptide','add_Nterm_protein'
            fixedmod =  dict((x, '[' + str(y) + ']') for x, y in [(x[4], y) for x, y in zip(self.header_dict.keys(), self.header_dict.values()) if x in aamods and y > 0])
        
        if fixedmod == None: fixedmod = ''        
        
        import mz_workbench.mz_core as mz_core
        peptide_container = mz_core.create_peptide_container(sequence, varmod, fixedmod)
        
        current_sequence = ''
        for member in peptide_container:
            current_sequence += member        
        
        bpc.b.FindWindowByName("sequence").SetValue(current_sequence)
        bpc.b.OnCalculate(None)
    
    def OnSelectCell(self, evt):  
        pass
          
        
    def OnDefault(self, event):
        pass
                
    
    def OnClick(self, event): #WINDOW, START, STOP, FILTER, REMOVE, SCALE, ACTIVE, VIEW
        '''
        
        Apply grid entries to make XICs.
        
        '''
        pass
    

if __name__ == '__main__':
    app = wx.App(False) 
    row = {u'Protein Description': u'ENO2 SGDID:S000001217, Chr VIII from 451327-452640, Verified ORF, ""Enolase II, a phosphopyruvate hydratase that catalyzes the conversion of 2-phosphoglycerate to phosphoenolpyruvate during glycolysis and the reverse reaction during gluconeogenesis; ', u'Missed Cleavages': 0, u'Charge': 3, u'Preceding Residue': u'R', u'Peptide Sequence': u'IGSEVYHNLK', u'Following Residue': u'S', u'Peptide Rank': 1, u'End Position': 195, u'Delta': 0.00487, u'Protein Matches': 1, u'Accession Number': u'YHR174W', u'Variable Modifications': '', u'Protein Mass': 46942, u'Peptide Score': 17.07, u'Start Position': 186, u'Protein Database': u'2::Marto_FR_Yeast', u'Protein Rank': 1, u'Protein Score': 17, u'Predicted mr': 1158.603302, u'Spectrum Description': u'FTMS + p NSI d Full ms2 442.74@hcd30.00 [100.00-900.00]', u'Experimental mz': 387.21, u'Query': 1}
    frame = SingleID_Frame(None, None, None, row, None, [])
    frame.Show()
    app.MainLoop()