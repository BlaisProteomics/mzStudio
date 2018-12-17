import wx
import os
from collections import defaultdict

from multiplierz.mzSearch import CometSearch
from multiplierz.settings import settings
from multiplierz.mzGUI_standalone import file_chooser
from multiplierz.mass_biochem import unimod


cometExe = settings.get_comet()
mod_list = sorted(unimod.site_form_mod_names())

class idlookup(object):
    def __init__(self):
        pass
    def __getitem__(self, key):
        return key
no_convert = idlookup()

bool_convert = {True:'1',False:'0',
                '1':True,'0':False}
unit_convert = {'amu':'0', '0':'amu',
                'mmu':'1', '1':'mmu',
                'ppm':'2', '2':'ppm'}
mass_type_convert = {'Average':'0', '0':'Average',
                     'Monoisotopic':'1', '1':'Monoisotopic'}
isotope_err_convert = {'None':'0', '0':'None',
                       '-1, 0, 1, +2, +3':'1', '1':'-1, 0, 1, +2, +3',
                       '-8, -4, 0, +4, +8':'2', '2':'-8, -4, 0, +4, +8'}
termini_convert = {'1': 'Semi-Enzymatic',
                   '2': 'Fully Enzymatic',
                   '8': 'Req. N-Term Enzymatic',
                   '9': 'Req. C-Term Enzymatic',
                   'Fully Enzymatic': '2',
                   'Req. C-Term Enzymatic': '9',
                   'Req. N-Term Enzymatic': '8',
                   'Semi-Enzymatic': '1'}



NameToParameter = [('Database', 'database_name', no_convert),
                   ('Run Decoy Search', 'decoy_search', bool_convert),
                   ('Precursor Tolerance', 'peptide_mass_tolerance', no_convert),
                   ('Precursor Units', 'peptide_mass_units', unit_convert),
                   ('Precursor Mass Type', 'mass_type_parent', mass_type_convert),
                   ('Fragment Mass Type', 'mass_type_fragment', mass_type_convert),
                   ('Allowed Isotope Error', 'isotope_error', isotope_err_convert),
                   ('Enzyme', 'search_enzyme_number', 'enzyme_special'),
                   ('Termini', 'num_enzyme_termini', termini_convert),
                   ('Missed Cleavages', 'allowed_missed_cleavage', no_convert),
                   ('Fragment Bin Width', 'fragment_bin_tol', no_convert),
                   ('a ions', 'use_A_ions', bool_convert),
                   ('b ions', 'use_B_ions', bool_convert),
                   ('c ions', 'use_C_ions', bool_convert),
                   ('x ions', 'use_X_ions', bool_convert),
                   ('y ions', 'use_Y_ions', bool_convert),
                   ('z ions', 'use_Z_ions', bool_convert),
                   ('H2O/NH3 Loss ions', 'use_NL_ions', bool_convert),
                   ('Decoy String', 'decoy_prefix', no_convert),
                   ('Minimum Peaks Filter', 'minimum_peaks', no_convert),
                   ('Minimum Intensity Filter', 'minimum_intensity', no_convert),
                   ('Remove +/- Precursor MZ', 'remove_precursor_tolerance', no_convert),
                   ('Max Fragment Charge', 'max_fragment_charge', no_convert),
                   ('Max Precursor Charge', 'max_precursor_charge', no_convert)]

# Ignoring parameters with convenient default values.
AutomaticallySetParameters = [('remove_precursor_peak', '1')]



FixModFields = [('G', 'add_G_glycine'),
                ('A', 'add_A_alanine'),
                ('S', 'add_S_serine'),
                ('P', 'add_P_proline'),
                ('V', 'add_V_valine'),
                ('T', 'add_T_threonine'),
                ('C', 'add_C_cysteine'),
                ('L', 'add_L_leucine'),
                ('I', 'add_I_isoleucine'),
                ('N', 'add_N_asparagine'),
                ('D', 'add_D_aspartic_acid'),
                ('Q', 'add_Q_glutamine'),
                ('K', 'add_K_lysine'),
                ('E', 'add_E_glutamic_acid'),
                ('M', 'add_M_methionine'),
                ('O', 'add_O_ornithine'),
                ('H', 'add_H_histidine'),
                ('F', 'add_F_phenylalanine'),
                ('R', 'add_R_arginine'),
                ('Y', 'add_Y_tyrosine'),
                ('W', 'add_W_tryptophan'),
                ('C-term', 'add_Cterm_peptide'),
                ('N-term', 'add_Nterm_peptide')]







class ModWidget(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        
        #self.title = wx.StaticText(self, -1, "Modifications")
        self.fixmods = wx.ListCtrl(self, -1, name = "Fixed",
                                   style = wx.LC_REPORT)
        self.varmods = wx.ListCtrl(self, -1, name = "Variable",
                                   style = wx.LC_REPORT)
        self.modSelector = wx.ListCtrl(self, -1, name = "Unimods",
                                       style = wx.LC_REPORT,
                                       size = (250, -1))
        self.addFixed = wx.Button(self, -1, '->', size = (25, -1))
        self.addVar = wx.Button(self, -1,  '->', size = (25, -1))
        self.clearFix = wx.Button(self, -1, 'Clr', size = (25, -1))
        self.clearVar = wx.Button(self, -1, 'Clr', size = (25, -1))
        self.searchBar = wx.TextCtrl(self, -1, '')
        
        self.fixLabel = wx.StaticText(self, -1, "Fixed Modifications")
        self.varLabel = wx.StaticText(self, -1, "Variable Modifications")
        
        self.modSelector.AppendColumn('Mod')
        self.modSelector.AppendColumn('Site')
        self.full_mod_data = []
        for modname in mod_list:
            words = modname.split(' ')
            basename = ' '.join(words[:-1])
            site = words[-1].strip('()')
            self.modSelector.Append([basename, site])
            self.full_mod_data.append((basename, site))
        sitecolsize = self.modSelector.GetColumnWidth(1)
        self.modSelector.SetColumnWidth(0, 250 - sitecolsize)
            
        
        self.fixmods.AppendColumn('Site')
        self.fixmods.AppendColumn('Delta')
        self.varmods.AppendColumn('Site')
        self.varmods.AppendColumn('Delta')    
        # Append blank rows to avoid annoying popup error.
        self.fixmods.Append(['', ''])
        self.varmods.Append(['', ''])
    
        gbs = wx.GridBagSizer(5, 5)
        gbs.Add(self.searchBar, (0, 0), flag = wx.EXPAND)
        gbs.Add(self.modSelector, (1, 0), span = (7, 1), flag = wx.EXPAND)
        gbs.Add(self.addFixed, (1, 1))
        gbs.Add(self.addVar, (5, 1))
        gbs.Add(self.clearFix, (3, 1), flag = wx.ALIGN_CENTER)
        gbs.Add(self.clearVar, (7, 1), flag = wx.ALIGN_CENTER)
        gbs.Add(self.fixLabel, (0, 2), flag = wx.ALIGN_BOTTOM)
        gbs.Add(self.varLabel, (4, 2), flag = wx.ALIGN_BOTTOM)
        gbs.Add(self.fixmods, (1, 2), span = (3, 1), flag = wx.EXPAND)
        gbs.Add(self.varmods, (5, 2), span = (3, 1), flag = wx.EXPAND)
        
        gbs.AddGrowableRow(3)
        gbs.AddGrowableRow(6)
        
        self.Bind(wx.EVT_BUTTON, self.assignFix, self.addFixed)
        self.Bind(wx.EVT_BUTTON, self.assignVar, self.addVar)
        self.Bind(wx.EVT_BUTTON, self.clearFixed, self.clearFix)
        self.Bind(wx.EVT_BUTTON, self.clearVariable, self.clearVar)
        self.Bind(wx.EVT_TEXT, self.filterMods, self.searchBar)
        
        self.SetSizerAndFit(gbs)
        
        self.oldFilterString = None
        
        self.Show()
    
    def updateFromModSelections(self, targetCtrl):    
        index = self.modSelector.GetFirstSelected()
        siteDeltas = []
        while index != -1:
            modname = self.modSelector.GetItem(index, 0).GetText()
            sitename = self.modSelector.GetItem(index, 1).GetText()
            delta = unimod.get_mod_delta(modname)
            
            if sitename == 'C-term':
                findsites = ['C-term']
            elif sitename == 'N-term':
                findsites = ['N-term']
            else:
                findsites = sitename.split() 
            
            siteDeltas.append((findsites, float(delta)))
            
            index = self.modSelector.GetNextSelected(index)
        
        index = targetCtrl.GetTopItem()
        ctrlDeltas = defaultdict(float)
        while index != -1:
            site = targetCtrl.GetItem(index, 0).GetText()
            delta = targetCtrl.GetItem(index, 1).GetText()
            if delta:
                ctrlDeltas[site] = float(delta)
            index = targetCtrl.GetNextItem(index)
        
        for sites, delta in siteDeltas:
            for site in sites:
                ctrlDeltas[site] += delta
        
        #targetCtrl.ClearAll()
        #targetCtrl.AppendColumn('Site')
        #targetCtrl.AppendColumn('Delta')
        targetCtrl.DeleteAllItems()
        for site, delta in sorted(ctrlDeltas.items()):
            targetCtrl.Append((site, str(delta)))
        
        
    def assignFix(self, event):
        self.updateFromModSelections(self.fixmods)
    def assignVar(self, event):
        self.updateFromModSelections(self.varmods)
        
    def clearFixed(self, event):
        self.fixmods.ClearAll()
        self.fixmods.AppendColumn('Site')
        self.fixmods.AppendColumn('Delta') 
        self.fixmods.Append(['', ''])
    def clearVariable(self, event):
        self.varmods.ClearAll()
        self.varmods.AppendColumn('Site')
        self.varmods.AppendColumn('Delta')        
        self.varmods.Append(['', ''])
        
    def filterMods(self, event):
        filterstring = self.searchBar.GetValue().lower()
        self.modSelector.ClearAll()
        self.modSelector.AppendColumn('Mod')
        self.modSelector.AppendColumn('Site')        
        for name, site in self.full_mod_data:
            if filterstring in name.lower():
                self.modSelector.Append([name, site])
        sitecolsize = self.modSelector.GetColumnWidth(1)
        self.modSelector.SetColumnWidth(0, 250 - sitecolsize)
        
    def readmods(self):
        varmods = []
        for i in range(self.varmods.GetItemCount()):
            site = self.varmods.GetItem(i, 0).GetText()
            delta = self.varmods.GetItem(i, 1).GetText()
            varmods.append((site, delta))
        fixmods = []
        for i in range(self.fixmods.GetItemCount()):
            site = self.fixmods.GetItem(i, 0).GetText()
            delta = self.fixmods.GetItem(i, 1).GetText()
            fixmods.append((site, delta))        
        return varmods, fixmods
    
    def write_varmods(self, modlist):
        self.varmods.ClearAll()
        self.varmods.AppendColumn('Site')
        self.varmods.AppendColumn('Delta')
        if not modlist:
            self.varmods.Append(['', ''])
        for modsite, modmass in modlist:
            self.varmods.Append((modsite, modmass))
            
    def write_fixmods(self, modlist):
        self.fixmods.ClearAll()
        self.fixmods.AppendColumn('Site')
        self.fixmods.AppendColumn('Delta')
        if not modlist:
            self.fixmods.Append(['', ''])
        for modsite, modmass in modlist:
            self.fixmods.Append((modsite, modmass))    
        
        

class CometGUI(wx.Dialog):
    def textCtrl(self, name, defaultVal = ''):
        label = wx.StaticText(self.pane, -1, name)
        ctrl = wx.TextCtrl(self.pane, -1, str(defaultVal),
                           name = name.replace('\n', ''), size = (70, -1))
        return label, ctrl
    def fileCtrl(self, name, bind = True):
        label = wx.StaticText(self.pane, -1, name)
        ctrl = wx.TextCtrl(self.pane, -1, '', name = name.replace('\n', ''))
        button = wx.Button(self.pane, -1, "Browse")
        if bind:
            def browse(event):
                filename = file_chooser('Select %s' % name, mode = 'r')
                if filename:
                    ctrl.SetValue(filename)
            self.Bind(wx.EVT_BUTTON, browse, button)
        return label, ctrl, button
    def checkCtrl(self, label, choices, size = None):
        return (wx.StaticText(self.pane, -1, label),
                wx.CheckListBox(self.pane, -1, choices = choices,
                                name = label.replace('\n', ' '),
                                size = size, style = wx.LB_HSCROLL))  
    def choiceCtrl(self, label, choices):
        return (wx.StaticText(self.pane, -1, label),
                wx.Choice(self.pane, -1, choices = choices,
                          name = label.replace('\n', ' ')))     
    def checkBox(self, label):
        return wx.CheckBox(self.pane, -1, label, name = label)
    
    def __init__(self, parent, ident, datafile, *etc, **etcetc):
        wx.Dialog.__init__(self, parent, ident, *etc, **etcetc)
        
        assert os.path.exists(cometExe), ('Comet not found at %s; please '
                                          'update multiplierz settings to '
                                          'indicate the directory of a copy '
                                          'of Comet.' % cometExe)
        self.pane = wx.Panel(self, -1)
  
         
        
        topLabel = wx.StaticText(self.pane, -1, "Comet Search Utility")
        topLabel.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        
        dataLabel, self.dataCtrl, self.dataBrowse = self.fileCtrl('Data File')
        
        # Modification for mzStudio.
        self.dataCtrl.SetValue(datafile)
        for ctrl in [dataLabel, self.dataCtrl, self.dataBrowse]:
            ctrl.Enable(False)
            ctrl.Show(False)
            
            
        dbaseLabel, self.dbaseCtrl, self.dbaseBrowse = self.fileCtrl('Database')
        parfileLabel, self.parfileCtrl, self.parfileBrowse = self.fileCtrl('Parameter File', bind = False)
        
        #varmodText, self.varmodCtrl = self.checkCtrl('Variable Modifications', mod_list, (300, -1))
        #fixmodText, self.fixmodCtrl = self.checkCtrl('Fixed Modifications', mod_list, (300, -1))
        
        precTolLabel, self.precTolCtrl = self.textCtrl('Precursor Tolerance')
        fragTolLabel, self.fragTolCtrl = self.textCtrl('Fragment Bin Width')
        precUnitLabel, self.precUnitCtrl = self.choiceCtrl('Precursor Units', ['amu', 'mmu', 'ppm'])
        precUnitLabel.Show(False)
        fragUnitLabel = wx.StaticText(self.pane, -1, 'amu')
        #fragUnitLabel, self.fragUnitCtrl = choiceCtrl('', ['amu', 'mmu', 'ppm'])
        isoErrLabel, self.isoErrCtrl = self.choiceCtrl('Allowed Isotope Error',
                                                       ['None',
                                                        '-1, 0, 1, +2, +3',
                                                        '-8, -4, 0, +4, +8'])
        enzymeLabel, self.enzymeCtrl = self.choiceCtrl('Enzyme', [])
        terminiLabel, self.terminiCtrl = self.choiceCtrl('Termini', ['Fully Enzymatic', # 2
                                                                     'Semi-Enzymatic', # 1
                                                                     'Req. N-Term Enzymatic', # 8
                                                                     'Req. C-Term Enzymatic']) # 9
        missedCleLabel, self.missedCleCtrl = self.choiceCtrl('Missed\nCleavages', map(str, range(10)))
        precTypeLabel, self.precTypeCtrl = self.choiceCtrl('Precursor Mass Type', ['Monoisotopic', 'Average'])
        fragTypeLabel, self.fragTypeCtrl = self.choiceCtrl('Fragment Mass Type', ['Monoisotopic', 'Average'])
        
        topFragChargeLabel, self.topFragChargeCtrl = self.choiceCtrl('Max Fragment Charge', map(str, range(1, 9)))
        topPrecChargeLabel, self.topPrecChargeCtrl = self.choiceCtrl('Max Precursor Charge', map(str, range(1, 9)))
        #self.overrideCharge = self.checkBox('Ignore MGF Charge')
        
        #self.decoyCtrl = self.checkBox('Run Decoy Search')
        #decoyStringLabel, self.decoyStringCtrl = self.textCtrl('Decoy String')
        
        # mass_offsets control?  Neutral loss?
        
        minPeakLabel, self.minPeakCtrl = self.textCtrl('Minimum Peaks Filter')
        minIntLabel, self.minIntCtrl = self.textCtrl('Minimum Intensity Filter')
        removePrecLabel, self.removePrecCtrl = self.textCtrl('Remove +/- Precursor MZ')
        # remove_precursor_peak should be a different setting for ETD spectra; add control?
        
        reportOptLabel = wx.StaticText(self.pane, -1, 'Output Options')
        reportOptLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        maxRankLabel, self.maxRankCtrl = self.textCtrl('Rank Cutoff', defaultVal = 1)
        maxExpLabel, self.maxExpCtrl = self.textCtrl('Expectation Value Cutoff', defaultVal = 0.01)
        
        self.saveButton = wx.Button(self.pane, -1, "Save Parameters")
        self.goButton = wx.Button(self.pane, -1, 'Run Search')
        
        ### Peptide Ion Controls
        self.ionBox = wx.StaticBox(self.pane, -1, label = 'Ions')
        ionSizer = wx.StaticBoxSizer(self.ionBox)
        for ion in ['a','b','c','x','y','z','H2O/NH3 Loss']:
            ionctrl = wx.CheckBox(self.pane, -1, ion, name = '%s ions' % ion)
            if ion in ['b', 'y']:
                ionctrl.SetValue(True)
            ionSizer.Add(ionctrl, 0, wx.ALL, 5)        
        
        self.modWidget = ModWidget(self.pane)
        
        gbs = wx.GridBagSizer(10, 10)
        
        #modSizer = wx.GridBagSizer(10, 10)
        #modSizer.Add(fixmodText, (0, 0), flag = wx.ALIGN_LEFT)
        #modSizer.Add(self.fixmodCtrl, (1, 0), span = (1, 2), flag = wx.EXPAND)
        #modSizer.Add(varmodText, (0, 2), flag = wx.ALIGN_LEFT)
        #modSizer.Add(self.varmodCtrl, (1, 2), span = (1, 2), flag = wx.EXPAND)
        #modSizer.Add(ionSizer, (2, 0), span = (1, 4), flag = wx.ALIGN_CENTRE)
        #modSizer.Add(wx.StaticLine(self.pane, -1, style = wx.LI_VERTICAL),
                     #(0, 4), span = (3, 1), flag = wx.EXPAND)
        
        scanSizer = wx.GridBagSizer(5, 5)
        scanBox = [(precTolLabel, (0, 0), wx.ALIGN_RIGHT), (self.precTolCtrl, (0, 1), wx.EXPAND),
                   (self.precUnitCtrl, (0, 2), wx.ALIGN_LEFT),
                   (fragTolLabel, (1, 0), wx.ALIGN_RIGHT), (self.fragTolCtrl, (1, 1), wx.ALIGN_LEFT),
                   (fragUnitLabel, (1, 2), wx.ALIGN_LEFT),
                   (isoErrLabel, (2, 0), wx.ALIGN_RIGHT), (self.isoErrCtrl, (2, 1), wx.ALIGN_LEFT, (1, 2)),
                   
                   (wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (3, 0), wx.EXPAND, (1, 3)),
                   
                   (precTypeLabel, (4, 0), wx.ALIGN_RIGHT), (self.precTypeCtrl, (4, 1), wx.ALIGN_LEFT, (1, 2)),
                   (fragTypeLabel, (5, 0), wx.ALIGN_RIGHT), (self.fragTypeCtrl, (5, 1), wx.ALIGN_LEFT, (1, 2)),
                   
                   (wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (6, 0), wx.EXPAND, (1, 3)),                  
                   
                   (topFragChargeLabel, (7, 0), wx.ALIGN_RIGHT), (self.topFragChargeCtrl, (7, 1), wx.ALIGN_LEFT),
                   (topPrecChargeLabel, (8, 0), wx.ALIGN_RIGHT), (self.topPrecChargeCtrl, (8, 1), wx.ALIGN_LEFT),
                   
                   (wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (9, 0), wx.EXPAND, (1, 3)),                   
                   
                   (minPeakLabel, (10, 0), wx.ALIGN_RIGHT), (self.minPeakCtrl, (10, 1), wx.ALIGN_LEFT),
                   (minIntLabel, (11, 0), wx.ALIGN_RIGHT), (self.minIntCtrl, (11, 1), wx.ALIGN_LEFT),
                   (removePrecLabel, (12, 0), wx.ALIGN_RIGHT), (self.removePrecCtrl, (12, 1), wx.ALIGN_LEFT)]
        
        pepSizer = wx.GridBagSizer(5, 5)
        pepBox = [(wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (0, 0), wx.EXPAND, (1, 2)),
                  (enzymeLabel, (1, 0), wx.ALIGN_RIGHT), (self.enzymeCtrl, (1, 1), wx.ALIGN_LEFT),
                  (terminiLabel, (2, 0), wx.ALIGN_RIGHT), (self.terminiCtrl, (2, 1), wx.ALIGN_LEFT),
                  (missedCleLabel, (3, 0), wx.ALIGN_RIGHT), (self.missedCleCtrl, (3, 1), wx.ALIGN_LEFT),
                  (wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (4, 0), wx.EXPAND, (1, 2))]
        
        #searchSizer = wx.GridBagSizer(5, 5)
        #searchBox = [(self.decoyCtrl, (0, 0), wx.ALIGN_RIGHT), (decoyStringLabel, (0, 1), wx.ALIGN_RIGHT),
                     #(self.decoyStringCtrl, (0, 2), wx.ALIGN_LEFT)]
        
        reportSizer = wx.GridBagSizer(5, 5, )
        reportBox = [(reportOptLabel, (0, 0), wx.ALIGN_CENTRE | wx.BOTTOM, (1, 5)),
                     (maxRankLabel, (1, 0), wx.ALIGN_RIGHT), (self.maxRankCtrl, (1, 1), wx.ALIGN_LEFT | wx.RIGHT),
                     (maxExpLabel, (1, 3), wx.ALIGN_RIGHT | wx.LEFT), (self.maxExpCtrl, (1, 4), wx.ALIGN_LEFT)]
        
        fileSizer = wx.GridBagSizer(5, 5)
        fileBox = [(dataLabel, (0, 0), wx.ALIGN_RIGHT), (self.dataCtrl, (0, 1), wx.EXPAND, (1, 2)),
                   (self.dataBrowse, (0, 3), wx.ALIGN_LEFT),
                   (dbaseLabel, (1, 0), wx.ALIGN_RIGHT), (self.dbaseCtrl, (1, 1), wx.EXPAND, (1, 2)),
                   (self.dbaseBrowse, (1, 3), wx.ALIGN_LEFT),
                   (parfileLabel, (2, 0), wx.ALIGN_RIGHT), (self.parfileCtrl, (2, 1), wx.EXPAND, (1, 2)),
                   (self.parfileBrowse, (2, 3), wx.ALIGN_LEFT),
                   (self.saveButton, (3, 0), wx.EXPAND, (1, 2)), (self.goButton, (3, 2), wx.EXPAND, (1, 2))]
        
        for sizer, box in [(pepSizer, pepBox), (scanSizer, scanBox),
                           (fileSizer, fileBox), (reportSizer, reportBox)]:
            for element in box:
                if len(element) == 3:
                    widget, pos, flag = element
                    span = (1, 1)
                elif len(element) == 4:
                    widget, pos, flag, span = element
                sizer.Add(widget, pos = pos, span = span, flag = flag)            
        
        #modSizer.AddGrowableRow(1)
        fileSizer.AddGrowableCol(1)        
        fileSizer.AddGrowableCol(2)
        
        #topSizer.Add(modSizer)
        #topSizer.Add()
        gbs.Add(topLabel, (0, 0), span = (1, 3), flag = wx.ALIGN_CENTRE)
        #gbs.Add(modSizer, (1, 0), span = (3, 2), flag = wx.EXPAND | wx.RIGHT)
        gbs.Add(self.modWidget, (1, 0), span = (3, 2), flag = wx.EXPAND | wx.RIGHT)
        gbs.Add(ionSizer, (3, 2), flag = wx.ALIGN_RIGHT)
        gbs.Add(scanSizer, (1, 2), flag = wx.EXPAND | wx.LEFT)
        #gbs.Add(ionSizer, (2, 0), flag = wx.EXPAND)
        gbs.Add(pepSizer, (2, 2), flag = wx.ALIGN_CENTRE | wx.LEFT)
        #gbs.Add(searchSizer, (3, 2), flag = wx.EXPAND)
        gbs.Add(wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (4, 0),
                span = (1, 3), flag = wx.EXPAND)
        gbs.Add(reportSizer, (5, 0), span = (1, 3), flag = wx.ALIGN_CENTRE)
        gbs.Add(wx.StaticLine(self.pane, -1, style = wx.LI_HORIZONTAL), (6, 0),
                span = (1, 3), flag = wx.EXPAND)
        gbs.Add(fileSizer, (7, 0), span = (1, 3), flag = wx.EXPAND)
        
        overBox = wx.BoxSizer()
        overBox.Add(gbs, 0, wx.ALL, 10)
        self.pane.SetSizerAndFit(overBox)
        self.SetClientSize(self.pane.GetSize())
        
        
        self.Bind(wx.EVT_BUTTON, self.load_parameters, self.parfileBrowse)
        self.Bind(wx.EVT_BUTTON, self.run_search, self.goButton)
        self.Bind(wx.EVT_BUTTON, self.save_parameters, self.saveButton)
        
        # Load default values (stored in comet_search.py.)
        self.parToGui(CometSearch())
        
        self.did_run = False
        
        self.Show()


    def guiToPar(self):
        searchObj = CometSearch() # Does this get reasonable default parameters?
        for ctrlname, parname, convert in NameToParameter:
            ctrl = self.FindWindowByName(ctrlname)
            if not ctrl:
                continue
            
            if parname == 'search_enzyme_number':            
                enzyme = ctrl.GetString(ctrl.GetSelection())
                try:
                    num = [k for k, v in searchObj.enzymes.items() if v['name'] == enzyme][0]
                except IndexError:
                    raise NotImplementedError, "Invalid enzyme string: %s" % enzyme
                searchObj['search_enzyme_number'] = num
                continue
            
            
            if isinstance(ctrl, wx.CheckBox):
                parval = convert[ctrl.GetValue()]
            elif isinstance(ctrl, wx.Choice):
                parval = convert[str(ctrl.GetString(ctrl.GetSelection())).strip()]                
            else:
                parval = convert[ctrl.GetValue().strip()]
            searchObj[parname] = parval

        #varmodstrs = self.varmodCtrl.GetCheckedStrings()
        #fixmodstrs = self.fixmodCtrl.GetCheckedStrings()
        varmodvalues, fixmodvalues = self.modWidget.readmods()
        if len(varmodvalues) > 9:
            wx.MessageBox("Comet only supports up to 9 separate variable modifications.")
            # Fixed mods don't havet his limitation, being site-based.
            return
            
        searchObj.varmods = []
        for site, modmass in varmodvalues:
            if not modmass: continue
            modmass = float(modmass.strip())
            mod = {'mass' : float(modmass),
                   'residues' : site,
                   'binary' : '0',
                   'max_mods_per_peptide' : '5',
                   'term_distance' : '-1',
                   'N/C-term' : '0',
                   'required' : '0'}
            searchObj.varmods.append(mod)
                
        fixmodMassBySite = defaultdict(float)
        for site, modmass in fixmodvalues:
            modmass = float(modmass)
            fixmodMassBySite[site] += modmass
        
        for sitename, parname in FixModFields:
            searchObj[parname] = fixmodMassBySite[sitename]
        
        return searchObj
        
    def parToGui(self, searchObj):
        for ctrlname, parname, convert in NameToParameter:
            ctrl = self.FindWindowByName(ctrlname)
            if not ctrl:
                continue # Not included in mzStudio version.
            
            if parname == 'search_enzyme_number':
                ctrl.Set(sorted([x['name'] for x in searchObj.enzymes.values()]))
                enzymeNum = str(searchObj[parname])         
                enzymeName = searchObj.enzymes[enzymeNum]['name']
                ctrlNum = ctrl.FindString(enzymeName)
                assert ctrlNum >= 0, "Enzyme not found."
                ctrl.Select(ctrlNum)
                continue
            
            if isinstance(ctrl, wx.CheckBox):
                ctrl.SetValue(convert[str(searchObj[parname])])
            elif isinstance(ctrl, wx.Choice):
                num = ctrl.FindString(convert[str(searchObj[parname])])
                ctrl.SetSelection(num)
            else:
                ctrl.SetValue(convert[str(searchObj[parname])])
         
        varmodlist = []
        for varmod in searchObj.varmods:
            modmass = str(varmod['mass'])
            modsites = varmod['residues']
            varmodlist.append((modsites, modmass))
            #modsites = modsites.replace('n', 'N-Term').replace('c', 'C-Term')
            #modstr = '%s (%s)' % (modmass, modsites)
            #self.varmodCtrl.Insert(modstr, 0)
            #self.varmodCtrl.Check(0)     
        
        #fixedMassSites = defaultdict(list)
        fixmodlist = []
        for site, fixmodpar in FixModFields:
            parvalue = searchObj[fixmodpar]
            if parvalue and float(parvalue):
                fixmodlist.append((site, parvalue))
            #fixedMassSites[parvalue].append(site)
        self.modWidget.write_varmods(varmodlist)
        self.modWidget.write_fixmods(fixmodlist)
            
        #for mass, sitelist in fixedMassSites.items():
            #if float(mass):
                #modstr = '%s (%s)' % (mass, ''.join(sitelist))
                #self.fixmodCtrl.Insert(modstr, 0)
                #self.fixmodCtrl.Check(0)
        
    def load_parameters(self, event):
        loadfile = file_chooser(title = 'Open parameter file:',
                                mode = 'r')
        if loadfile:
            self.parfileCtrl.SetValue(loadfile)
            if os.path.exists(loadfile):
                self.parToGui(CometSearch(loadfile))
        
    def save_parameters(self, event):
        searchObj = self.guiToPar()
        parfile = self.parfileCtrl.GetValue()
        if parfile:
            savefile = file_chooser(title = 'Save parameter file to:',
                                    default_path = os.path.dirname(parfile),
                                    default_file = os.path.basename(parfile),
                                    mode = 'w')
        else:
            savefile = file_chooser(title = 'Save parameter file to:',
                                    mode = 'w')
        
        searchObj.write(savefile)
        
    def run_search(self, event):
        datafile = self.dataCtrl.GetValue()
        if not datafile:
            wx.MessageBox('No data file selected.')
            return
        
        
        
        rankval = self.maxRankCtrl.GetValue().strip()
        expval = self.maxExpCtrl.GetValue().strip()
        try:
            if rankval:
                most_rank = int(rankval)
            else:
                most_rank = None
        except ValueError:
            wx.MessageBox('Invalid value for rank cutoff (must be int): %s' % rankval)
            return
        try:
            if expval:
                most_exp = float(expval)
            else:
                most_exp = None
        except ValueError:
            wx.MessageBox('Invalid value for expectation value cutoff (must be decimal number): %s' % expval)
            return
        
        searchObj = self.guiToPar()        
        
        # Async-ify this?
        outputfile = searchObj.run_search(datafile, most_rank = most_rank, most_exp = most_exp)
        #wx.MessageBox('Search complete: output written to %s' % outputfile)
        
        self.output = outputfile
        self.did_run = True
        
        self.Close()
        
            
        
        
        
                

            
def run_GUI_from_app(parent, spectrum, pepmass):
    from multiplierz.mgf import write_mgf
    from multiplierz.mzReport import reader
    
    tempfile = 'comet.temp.mgf'
    write_mgf([{'spectrum':spectrum,
                'pepmass':pepmass,
                'title':'test_spectrum'}],
              tempfile)
    
    #searchObj = CometGUI('foo','bar','baz')
       
    searchObj = CometGUI(parent, -1, tempfile)
    searchObj.ShowModal()
    if searchObj.did_run == True:
        outputfile = searchObj.output
        return list(reader(outputfile, sheet_name = 'Data')), list(reader(outputfile, sheet_name = 'Comet_Header'))
    else:
        return None, None

if __name__ == '__main__':
    foo = wx.App(0)
    bar = CometGUI(None, -1, '')
    foo.MainLoop()
    