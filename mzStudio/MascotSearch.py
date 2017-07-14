import os
import sys
import tempfile
import wx
import wx.lib.fancytext as FT

from multiplierz import myData, logger_message
from multiplierz.mzSearch.mascot.interface import MascotSearcher
from multiplierz.mzSearch import MascotSearch as Searcher
from multiplierz import settings
from multiplierz.mgf import write_mgf
from multiplierz.mzReport import reader


username = None
password = None


class TextVal(wx.PyValidator):
    def Clone(self):
        return TextVal()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        if not val:
            wx.MessageBox("%s cannot be empty" % tc.GetName(), "Error")
            tc.SetBackgroundColour("YELLOW")
            tc.SetFocus()
            tc.Refresh()
            return False
        else:
            tc.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            tc.Refresh()
            return True

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True

class ProtMassVal(wx.PyValidator):
    def Clone(self):
        return ProtMassVal()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if not val:
            tc.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            tc.Refresh()
            return True

        try:
            if float(val) > 1000.0:
                wx.MessageBox("Upper limit on protein mass cannot exceed 1,000 kDa", "Error")
            else:
                tc.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                tc.Refresh()
                return True
        except:
            wx.MessageBox("Precursor mass is not a valid number", "Error")

        tc.SetBackgroundColour("YELLOW")
        tc.Clear()
        tc.SetFocus()
        tc.Refresh()
        return False

class ErrorTolVal(wx.PyValidator):
    def Clone(self):
        return ErrorTolVal()

    def Validate(self, win):
        cb = self.GetWindow()
        cbVal = cb.GetValue()
        dVal = win.FindWindowByName("DECOY").GetValue()
        enzVal = win.FindWindowByName("CLE").GetStringSelection()
        quantVal = win.FindWindowByName("QUANTITATION").GetSelection()

        if cbVal and dVal:
            wx.MessageBox("Cannot select both error tolerant and decoy", "Error")
        elif cbVal and enzVal.startswith('semi'):
            wx.MessageBox("Cannot combine error tolerant with a semi-specific enzyme", "Error")
        elif cbVal and quantVal != 0:
            wx.MessageBox("Cannot combine error tolerant with quantitation", "Error")
        else:
            return True

        cb.SetValue(0)
        return False

class TolValidator(wx.PyValidator):
    def Clone(self):
        return TolValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        unit = win.FindWindowByName(tc.GetName() + "U").GetStringSelection()

        unit_max = { 'Da':10.0, 'mmu':10000.0, '%':1.0, 'ppm':10000.0 }

        try:
            v = float(val)
            if v <= 0.0:
                wx.MessageBox("Mass tolerance must be positive", "Error")
            elif v > unit_max[unit]:
                wx.MessageBox("Mass tolerance must be less than %d %s" % (unit_max[unit], unit), "Error")
            else:
                tc.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                tc.Refresh()
                return True
        except:
            wx.MessageBox("Mass tolerance is not a valid number", "Error")

        tc.SetBackgroundColour("YELLOW")
        tc.Clear()
        tc.SetFocus()
        tc.Refresh()
        return False

class PreValidator(wx.PyValidator):
    def Clone(self):
        return PreValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        # formats that require a precursor
        nopre = ['PerSeptive (*.PKS)','Sciex API III','Bruker (*.XML)']

        if not val:
            wx.MessageBox("Please enter a precursor mass", "Error")
            return False
        try:
            float(val)
        except ValueError as err:
            wx.MessageBox("Percursor mass is not a valid floating-point number: %s" % val)
            return False

        return True

class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Mascot Login")

        gbs = wx.GridBagSizer(10, 5)

        pos = iter([(0,0), (0,1), (1,0), (1,1), (2,0), (2,1)])

        gbs.Add( wx.StaticText(self, -1, "Login:", style=wx.ALIGN_RIGHT), pos.next(), flag=wx.EXPAND )
        gbs.Add( wx.TextCtrl(self, -1, "", size=(75,21),
                             name="Login", validator=TextVal()), pos.next() )

        gbs.Add( wx.StaticText(self, -1, "Password:", style=wx.ALIGN_RIGHT), pos.next(), flag=wx.EXPAND )
        gbs.Add( wx.TextCtrl(self, -1, "", style=wx.PASSWORD, size=(75,21),
                             name="Password", validator=TextVal()), pos.next() )

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        gbs.Add( btn, pos.next() )
        gbs.Add( wx.Button(self, wx.ID_CANCEL), pos.next() )

        box = wx.BoxSizer()
        box.Add(gbs, 0, wx.ALL, 10)

        self.SetSizerAndFit(box)

class MascotSearch(wx.Dialog):
    # file formats supported by mascot
    wildcard = ('Mascot generic (*.MGF)|*.mgf|'
                'Sequest (*.DTA)|*.dta|'
                'Finnigan (*.ASC)|*.asc|'
                'Micromass (*.PKL)|*.pkl|'
                'PerSeptive (*.PKS)|*.pks|'
                'Sciex API III|*.*|'
                'Bruker (*.XML)|*.xml|'
                'mzData (*.XML)|*.xml')

    # dictionary to translate filter index to the input value that the search form wants
    formats = {0:'Mascot generic',
               1:'Sequest (*.DTA)',
               2:'Finnigan (*.ASC)',
               3:'Micromass (*.PKL)',
               4:'PerSeptive (*.PKS)',
               5:'Sciex API III',
               6:'Bruker (*.XML)',
               7:'mzData (*.XML)'}

    def __init__(self, parent, login='', password='', targetdata = None):
        """Instantiate the MascotSearch class. This creates a window for submitting to Mascot via Multiplierz.

        The basic workflow of this editor is:
        1. Select file(s)
        2. Customize settings via the GUI
        3. Submit to Mascot server
        4. Wait (or do other things) while the search runs
        """
        assert targetdata
        self.scan = targetdata[0]
        self.filter = targetdata[1]
        self.mz = targetdata[2]
        self.psm_results = None
        self.header_results = None
        
        wx.Dialog.__init__(self, None, -1, "Mascot MS/MS Ions Search", style=wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
        pane = wx.Panel(self, -1, style = wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN)

        self.login = login
        self.password = password

        ms = MascotSearcher(settings.mascot_server)
        if settings.mascot_security:
            err = ms.login(self.login, self.password)
            if err:
                raise RuntimeError, "Mascot login error: %s" % err

        fields = ms.get_fields(settings.mascot_version)
        #fields = ms.get_fields_better()
        ms.close()

        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        load_par = wx.MenuItem(file_menu, -1, "&Open PAR File\tCtrl+O")
        file_menu.AppendItem(load_par)
        self.Bind(wx.EVT_MENU, self.OnLoadPar, load_par)

        save_par = wx.MenuItem(file_menu, -1, "&Save Parameters\tCtrl+S")
        file_menu.AppendItem(save_par)
        self.Bind(wx.EVT_MENU, self.OnSavePar, save_par)

        menu_bar.Append(file_menu, "&File")

        output_menu = wx.Menu()
        self.open_tabs = wx.MenuItem(output_menu, -1, "&Open Results in Browser", kind=wx.ITEM_CHECK)
        output_menu.AppendItem(self.open_tabs)

        self.getIDs = wx.MenuItem(output_menu, -1, "&Send IDs to Mascot Downloader", kind=wx.ITEM_CHECK)
        output_menu.AppendItem(self.getIDs)
	
        #if settings.mascot_server.find('www.matrixscience.com') != -1 or self.mascot_tab is None:
            #self.getIDs.Enable(False)
            #self.open_tabs.Check() # set default to open a browser
        #else:
            #self.getIDs.Check() # for non-public server, default to report-downloader

        menu_bar.Append(output_menu, "&Output")

        #self.SetMenuBar(menu_bar)

        gbs = wx.GridBagSizer(10, 5)

        # parameter hash stores the values
        self.parameters = {'USERNAME':'',
                           'USEREMAIL':'',
                           'COM':'',
                           'DB':'',
                           'TAXONOMY':'',
                           'CLE':'',
                           'PFA':'',
                           'MODS':'',
                           'IT_MODS':'',
                           'TOL':'',
                           'TOLU':'',
                           'PEP_ISOTOPE_ERROR':'',
                           'ITOL':'',
                           'ITOLU':'',
                           'CHARGE':'',
                           'MASS':'',
                           'FILE':'',
                           'FORMAT':'',
                           'PRECURSOR':'',
                           'INSTRUMENT':'',
                           'REPORT':''
                           }

        if settings.mascot_version == '2.1':
            self.parameters.update( { 'SEG':'', 'ICAT':'', 'OVERVIEW':'' } )
        elif settings.mascot_version >= '2.2':
            self.parameters.update( { 'QUANTITATION':'', 'ERRORTOLERANT':'', 'DECOY':'', } )

        # labels
        labels = (zip(range(6) + range(7,11) + [0,4,5,7,10,11],
                      [0 for i in range(10)] + [5 for i in range(6)],
                      ['Name',
                       'Search title',
                       'Database',
                       'Taxonomy',
                       'Enzyme',
                       'Fixed\nModifications',
                       u'Peptide tol. \xb1',
                       'Peptide Charge',
                       '',
                       'Instrument',
                       'Email',
                       'Missed\nCleavages',
                       'Variable\nModifications',
                       u'MS/MS tol. \xb1',
                       'Precursor',
                       '']))

        if settings.mascot_version == '2.1':
            labels += (6, 0, 'Protein Mass'),
            gbs.Add( wx.StaticText(pane, -1, 'kDa'), (6,3), flag=wx.EXPAND )
        elif settings.mascot_version >= '2.2':
            labels += (6, 0, 'Quantitation'),
            # one fancytext label (for superscript)
            gbs.Add( FT.StaticFancyText(pane, -1, '# <sup>13</sup>C', style=wx.ALIGN_RIGHT),
                     (7,3), flag=wx.EXPAND )

        else:
            wx.MessageBox("This version of Mascot may not be supported correctly.")

        # ----- add labels -----
        for x,y,lbl in labels:
            gbs.Add( wx.StaticText(pane, -1, lbl, style=wx.ALIGN_RIGHT), (x,y), flag=wx.EXPAND )

        gbs.Add( wx.StaticText(pane, -1, 'm/z'), (10,8), flag=wx.EXPAND )

        # ----- add controls -----

        # name
        gbs.Add( wx.TextCtrl(pane, -1, "Your name here", name="USERNAME"), (0,1), (1,4), flag=wx.EXPAND )
        # email
        gbs.Add( wx.TextCtrl(pane, -1, "", name="USEREMAIL"), (0,6), (1,4), flag=wx.EXPAND )

        # title
        gbs.Add( wx.TextCtrl(pane, -1, "", name="COM"), (1,1), (1,7), flag=wx.EXPAND )

        # database
        if settings.mascot_version < '2.3':
            gbs.Add( wx.Choice(pane, -1, choices=fields['DB'], name="DB"), (2,1), (1,4), flag=wx.EXPAND )
        else:
            dbSelector = wx.CheckListBox(pane, -1, choices=fields['DB'], size=(228,81), name="DB")
            gbs.Add(dbSelector, (2,1), (1,4), flag=wx.EXPAND )
            self.Bind(wx.EVT_CHECKLISTBOX, self.onDatabaseSelect, dbSelector)

        # taxonomy
        gbs.Add( wx.Choice(pane, -1, choices=fields['TAXONOMY'], name="TAXONOMY"), (3,1), (1,8) )

        # enzyme
        gbs.Add( wx.Choice(pane, -1, choices=fields['CLE'], name="CLE"), (4,1), (1,4), flag=wx.EXPAND )
        # missed cleavages
        pfa_min = min(int(s) for s in fields['PFA'])
        pfa_max = max(int(s) for s in fields['PFA'])
        gbs.Add( wx.SpinCtrl(pane, -1, min=pfa_min, max=pfa_max, initial=int(fields['PFA'][0]), size=(40,21),
                             style=wx.SP_WRAP|wx.SP_ARROW_KEYS, name="PFA"), (4,6) )

        # fixed and variable modifications
        mods = wx.CheckListBox(pane, -1, choices=fields['MODS'], size=(228,81), name="MODS")
        gbs.Add( mods, (5,1), (1,4), flag=wx.EXPAND )
        mods.Bind(wx.EVT_CHECKLISTBOX, self.OnModSelect)

        it_mods = wx.CheckListBox(pane, -1, choices=fields['IT_MODS'], size=(228,81), name="IT_MODS")
        gbs.Add( it_mods, (5,6), (1,4), flag=wx.EXPAND )
        it_mods.Bind(wx.EVT_CHECKLISTBOX, self.OnModSelect)

        if settings.mascot_version == '2.1':
            gbs.Add( wx.TextCtrl(pane, -1, "", name="SEG", validator=ProtMassVal()), (6,1), (1,2), flag=wx.EXPAND )
            gbs.Add( wx.CheckBox(pane, -1, "ICAT", style=wx.ALIGN_RIGHT, name="ICAT"), (6,6), (1,2) )
        elif settings.mascot_version >= '2.2':
            # quantitation
            gbs.Add( wx.Choice(pane, -1, choices=fields['QUANTITATION'], name="QUANTITATION"), (6,1), (1,4), flag=wx.EXPAND )

        # peptide tolerance
        gbs.Add( wx.TextCtrl(pane, -1, "1.2", size=(40,21), validator=TolValidator(), name="TOL"), (7,1) )
        # pep tol units
        gbs.Add( wx.Choice(pane, -1, choices=fields['TOLU'], name="TOLU"), (7,2) )

        if settings.mascot_version >= '2.2':
            # isotope error (# 13C)
            pie_min = min(int(s) for s in fields['PEP_ISOTOPE_ERROR'])
            pie_max = max(int(s) for s in fields['PEP_ISOTOPE_ERROR'])
            gbs.Add( wx.SpinCtrl(pane, -1, min=pie_min, max=pie_max, initial=int(fields.selected['PEP_ISOTOPE_ERROR']),
                                 size=(40,21), style=wx.SP_WRAP|wx.SP_ARROW_KEYS, name="PEP_ISOTOPE_ERROR"), (7,4) )

        # MS/MS tolerance
        gbs.Add( wx.TextCtrl(pane, -1, "0.6", size=(40,21), validator=TolValidator(), name="ITOL"), (7,6) )
        # MS/MS tol units
        gbs.Add( wx.Choice(pane, -1, choices=fields['ITOLU'], name="ITOLU"), (7,7) )

        # peptide charge
        gbs.Add( wx.Choice(pane, -1, choices=fields['CHARGE'], name="CHARGE"), (8,1), (1,4) )

        # monoisotopic/average radiobox
        gbs.Add( wx.RadioBox( pane, -1, choices=['Monoisotopic','Average'], style=wx.ALIGN_RIGHT, name="MASS"), (8,6), (2,4) )

        ## file control
        #self.fname = wx.TextCtrl(pane, -1, "", style=wx.TE_READONLY)
        #self.fname.BackgroundColour = wx.NamedColour("LIGHT GREY")
        #gbs.Add( self.fname, (9,1), (1,4), flag=wx.EXPAND )
        #self.fname.Bind(wx.EVT_LEFT_UP, self.OnChooseFile)
        
        self.fname = wx.StaticText(pane, -1, self.filter)
        gbs.Add(self.fname, (9, 1), (1, 4), flag = wx.EXPAND)

        #fbutton = wx.Button(pane, -1, "Browse...")
        #gbs.Add( fbutton, (9,5) )
        #fbutton.Bind(wx.EVT_BUTTON, self.OnChooseFile)

        # instrument
        gbs.Add( wx.Choice(pane, -1, choices=fields['INSTRUMENT'], name="INSTRUMENT"), (10,1), (1,4), flag=wx.EXPAND )

        # precursor
        gbs.Add( wx.TextCtrl(pane, -1, "", size=(60,21), name="PRECURSOR", validator=PreValidator()),
                 (10,6), (1,2), flag=wx.EXPAND )

        if settings.mascot_version == '2.1':
            gbs.Add( wx.CheckBox(pane, -1, "Overview", style=wx.ALIGN_RIGHT, name="OVERVIEW"), (11,1), (1,2) )
        elif settings.mascot_version >= '2.2':
            # decoy/error tolerant checkboxes
            gbs.Add( wx.CheckBox(pane, -1, "Decoy", style=wx.ALIGN_RIGHT, name="DECOY"), (11,1), (1,2) )
            gbs.Add( wx.CheckBox(pane, -1, "Error Tolerant",
                                 style=wx.ALIGN_RIGHT, name="ERRORTOLERANT", validator=ErrorTolVal()), (11,3), (1,2) )

        # report top hits
        #gbs.Add( wx.Choice(pane, -1, choices=fields['REPORT'], name="REPORT"), (11, 6), (1,2) )

        cancel = wx.Button(pane, -1, "Cancel")
        gbs.Add(cancel, (12, 0), (1, 5), flag = wx.EXPAND)
        cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        
        # Submit button
        submit = wx.Button(pane, -1, "Submit")
        gbs.Add( submit, (12,5), (1,5), flag=wx.EXPAND )
        submit.Bind(wx.EVT_BUTTON, self.OnSubmit)

        box = wx.BoxSizer()
        box.Add(gbs, 0, wx.ALL, 10)

        for child in pane.GetChildren():
            if isinstance(child,wx.Choice):
                if child.GetName() in fields.selected:
                    child.SetSelection(child.FindString(fields.selected[child.GetName()]))
                else:
                    child.SetSelection(0)

        pane.SetSizerAndFit(box)
        self.SetClientSize(pane.GetSize())
        
        self.FindWindowByName('PRECURSOR').SetValue(str(self.mz))
        
        if os.path.exists(os.path.join(myData, '.mzB_Mascot.par')):
            self.ParsePar(os.path.join(myData, '.mzB_Mascot.par'))

    def OnLoadPar(self, event):
        wildcard = 'PAR file (*.par)|*.par'
        dialog = wx.FileDialog(self, "Load a .par file", myData, "", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            par = dialog.GetPath()
            self.ParsePar(par)
        dialog.Destroy()

    def OnSavePar(self, event):
        wildcard = 'PAR file (*.par)|*.par'
        dialog = wx.FileDialog(self, "Save parameter settings to a file", myData, "", wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            par = dialog.GetPath()
            self.WritePar(par)
        dialog.Destroy()

    def OnModSelect(self, event):
        '''It shouldn't be possible (and doesn't make sense) to select a mod as both
        fixed and potential, so this callback enforces exclusion'''
        sel = event.GetSelection()
        obj = event.GetEventObject()
        if obj.GetName() == 'MODS':
            other = self.FindWindowByName('IT_MODS')
        else:
            other = self.FindWindowByName('MODS')
        other.Check(sel, False)

        obj.SetToolTip(wx.ToolTip('\n'.join(sorted(obj.GetCheckedStrings()))))
        other.SetToolTip(wx.ToolTip('\n'.join(sorted(other.GetCheckedStrings()))))

    def onDatabaseSelect(self, event):
        # Only bound if Mascot version > 2.2.
        selector = self.FindWindowByName('DB')
        selector.SetToolTip(wx.ToolTip('\n'.join(sorted(selector.GetCheckedStrings()))))

        
    #def OnChooseFile(self, event):
        #if self.parameters['FILE']:
            #curpath = os.path.commonprefix(self.parameters['FILE'])
        #else:
            #curpath = myData
        #dialog = wx.FileDialog(self, "Choose data file(s) to submit", curpath, "", MascotSearch.wildcard, wx.OPEN | wx.MULTIPLE)
        #if dialog.ShowModal() == wx.ID_OK:
            #self.parameters['FILE'] = dialog.GetPaths()
            #self.parameters['FORMAT'] = MascotSearch.formats[dialog.GetFilterIndex()]
            #self.fname.SetValue(', '.join(os.path.basename(f) for f in self.parameters['FILE']))
            #self.fname.SetToolTip(wx.ToolTip('\n'.join(os.path.basename(f) for f in self.parameters['FILE'])))
        #dialog.Destroy()


    def OnCancel(self, event):
        self.Close()

    def OnSubmit(self, event):
        if not self.Validate():
            return

        wx.BeginBusyCursor()
        tempdir = None
        resultfile = None
        try:
            self.UpdateValues()
            self.parameters['MULTI_SITE_MODS'] = '1'
            self.parameters['ion_cutoff'] = '0'
            self.parameters['show_query_data'] = '1'
            self.parameters['show_same_set'] = '0'
            self.parameters['show_sub_set'] = '0'
            self.parameters['rank_one'] = '1'
            self.parameters['bold_red'] = '1'
            
            targetFile, parFile, tempdir = self.writeSearchFiles()
            
            searchObj = Searcher(parFile)
            resultfile = searchObj.run_search(targetFile,
                                              user = self.login,
                                              password = self.password)
            psms = reader(resultfile)
            self.psm_results = list(psms)
            psms.close()
            header = reader(resultfile, sheet_name = 'Mascot_Header')
            self.header_results = list(header)
            header.close()
            try:
                os.remove(resultfile)
            except:
                print "Count not remove result file"
            self.Close()
        finally:
            wx.EndBusyCursor()    
            if tempdir:
                os.remove(targetFile)
                os.remove(parFile)
                if resultfile and os.path.exists(resultfile):
                    try:
                        os.remove(resultfile)
                    except:
                        print "Could not remove mfg result"
                try:
                    os.rmdir(tempdir)
                except:
                    print "Could not remove temp dir"
                
        self.WritePar(os.path.join(myData, '.mzB_Mascot.par'))

    def writeSearchFiles(self):
        tempdir = tempfile.mkdtemp()
        parfile = os.path.join(tempdir, 'PARFILE.par')
        mgffile = os.path.join(tempdir, 'MGFFILE.mgf')
        
        self.WritePar(parfile)
        
        chgset = self.FindWindowByName('CHARGE')
        precset = self.FindWindowByName('PRECURSOR')
        
        mgfData = [{'title':self.filter,
                    'charge':chgset.GetString(chgset.GetCurrentSelection()),
                    'pepmass':precset.GetValue(),
                    'spectrum':self.scan}]
        write_mgf(mgfData, mgffile)
        
        assert os.path.exists(parfile)
        assert os.path.exists(mgffile)
        
        return mgffile, parfile, tempdir
        


    def UpdateValues(self):
        for name in self.parameters.keys():
            c = self.FindWindowByName(name)
            if isinstance(c,wx.CheckListBox):
                self.parameters[name] = c.GetCheckedStrings()
            elif isinstance(c,(wx.Choice, wx.RadioBox)):
                self.parameters[name] = c.GetStringSelection()
            elif isinstance(c,(wx.TextCtrl, wx.SpinCtrl)):
                self.parameters[name] = str(c.GetValue())
            elif isinstance(c,wx.CheckBox):
                if c.GetValue():
                    if settings.mascot_version == '2.1':
                        self.parameters[name] = 'On'
                    else:
                        self.parameters[name] = '1'
                else:
                    self.parameters[name] = ''

    def ParsePar(self, fname):
        f = open(fname, 'r')
        try:
            for line in f:
                if '=' in line:
                    (key, value) = line.rstrip().split('=',1)
                    if key in self.parameters and value:
                        try:
                            win = self.FindWindowByName(key)
                            if isinstance(win,wx.CheckListBox):
                                win.SetCheckedStrings([s for s in value.split(',') if s in win.GetStrings()])
                                win.SetToolTip(wx.ToolTip('\n'.join(sorted(win.GetCheckedStrings()))))
                            elif isinstance(win,(wx.Choice, wx.RadioBox)):
                                win.SetStringSelection(value)
                            elif isinstance(win,wx.TextCtrl):
                                win.SetValue(value)
                            elif isinstance(win,wx.SpinCtrl):
                                win.SetValueString(value)
                            elif isinstance(win,wx.CheckBox):
                                if value in ('On','1'):
                                    win.SetValue(True)
                                else:
                                    win.SetValue(False)
                        except:
                            wx.MessageBox("Couldn't parse field '%s' in %s" % (key, os.path.basename(fname)))
        except:
            wx.MessageBox("Couldn't parse %s" % os.path.basename(fname))
        finally:
            f.close()

    def WritePar(self, fname):
        self.UpdateValues()
        f = open(fname, 'w')
        for (k,v) in self.parameters.items():
            if k in ('FILE','FORMAT'): continue
            if k == 'DB' and settings.mascot_version >= '2.3':
                v = ','.join(v)
            if k in ('MODS','IT_MODS'):
                v = ','.join(v)
            f.write('%s=%s\n' % (k,v))
        f.close()


def runMascotSearch(targetdata):
    global username
    global password 
    
    if settings.mascot_security and username == None and password == None:
        dlg = LoginDialog(None)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            username, password = (dlg.FindWindowByName("Login").GetValue(),
                                  dlg.FindWindowByName("Password").GetValue())        
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

    try:
        mascot_frame = MascotSearch(wx.GetActiveWindow(), username, password, targetdata)
    except RuntimeError as err:
        username = None
        password = None
        wx.MessageBox(str(err))
        raise err
        

    #mascot_icon_file = os.path.normpath(os.path.join(install_dir, 'images', 'icons', 'multiplierz.ico'))
    #mascot_icon = wx.Icon(mascot_icon_file, wx.BITMAP_TYPE_ICO)
    #mascot_frame.SetIcon(mascot_icon)

    wx.Log_EnableLogging(False)
    mascot_frame.ShowModal()
    wx.Log_EnableLogging(True)
    return mascot_frame.psm_results, mascot_frame.header_results
    
    
