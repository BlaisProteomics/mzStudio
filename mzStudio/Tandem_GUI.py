from multiplierz.mzReport import reader, writer
from multiplierz.mzReport.formats.xtandem import format_XML
from multiplierz.mass_biochem import unimod, mod_masses
from multiplierz import myData
from multiplierz.mzSearch import TandemSearch

import wx
import os, sys
import re
from collections import defaultdict

from mzStudio import dirName
persistent_data = os.path.join(dirName, r'persistent_settings.dat')

xmlData = ['START ENZYMES',
           '[R]|[A-Z] is Arg-C',
           '[A-Z]|[D] is Asp-N',
           '[KAY]|[A-Z] is Bromelain',
           '[M]|[A-Z] is CNBr_HSer',
           '[M]|[A-Z] is CNBr_HSerLac',
           '[R]|[A-Z] is Cathepsin B',
           '[LF]|{VAG} is Cathepsin D',
           '[YWF]|[A-Z] is Cathepsin G',
           '[YWFL]|[A-Z] is Chymotrypsin',
           '[R]|[P] is Clostripain',
           '[AVLIGS]|[A-Z] is Elastase',
           '[E]|[A-Z] is Glu-C_Bic',
           '[ED]|[A-Z] is Glu-C_Phos',
           '[N]|[G] is Hydroxylamine',
           '[K]|[A-Z] is Lys-C',
           '[A-Z]|[K] is Lys-N',
           '[RK]|[A-Z] is Papain',
           '[LF]|{VAG} is Pepsin',
           '[YWF]|[A-Z] is Proteinase K',
           '{RHK}|[A-Z] is Subtilisin',
           '[LFIVMA]|{P} is Thermolysin',
           '[KR]|{P} is Trypsin',
           'END ENZYMES',
           'START MODS',
           'Acetyl (K)',
           'Acetyl (N-term)',
           'Carbamidomethyl (C)',
           'Guanidinyl (K)',
           'Methyl (C-term)',
           'Methyl (DE)',
           'Oxidation (M)',
           'Oxidation (W)',
           'Phospho (ST)',
           'Phospho (Y)',
           'deamidation (NQ)',
           'iTRAQ4plex (K)',
           'iTRAQ4plex (N-term)',
           'iTRAQ4plex (Y)',
           'iTRAQ8plex (K)',
           'iTRAQ8plex (N-term)',
           'iTRAQ8plex (Y)',
           'END MODS']


enzymeList = {}
fixmods = ['Uninitialized']
varmods = ['Uninitialized']
mzUnits = ['Da','ppm','mmu']
taxonList = ['All']

stdTxtCtrlSize = (50, -1)



nameToHelptext = {'Enzyme':('Enzyme used to calculate peptides from the target '
                            'database.'),
                  'Unanticipated Cleavage':('Number of times per peptide that cleavage '
                                      'on the enzyme site may be omitted.'),
                  'Precursor Tol.':('+/- tolerance from the ideal m/z that is '
                                    'considered a match for an MS1 precursor ion.'),
                  'Fragment Tol.':('+/- tolerance from the ideal m/z that is '
                                    'considered a match for an MS2 fragment ion.'),
                  'Accept C13 Mass':('Often MS2 spectra are obtained from the'
                                     'non-monoisotopic precursor peak with a single'
                                     'C13 atom, because this can be a stronger'
                                     'signal; this results in a precursor mass'
                                     'inaccuracy of about 1 Dalton.  Select this'
                                     'option to include peptides corresponding'
                                     'to non-monoisotopic precursors in the'
                                     'spectrum model search.'),
                  'Mass Type':('Whether peaks are expected to match the monoisotopic'
                               'm/z or the weighted average mass of all C13-containing'
                               'isotopic forms.'),
                  'Maximum Expectation Value':('"Expectation Value" refers to the'
                                               'statistical chance a given peptide'
                                               'identification would be made by'
                                               'chance.  Peptide matches with an'
                                               'expectation value higher than this'
                                               'setting are omitted from the'
                                               'results.'),
                  'Fixed Modifications':('Amino acid modifications that are present'
                                         'in all instances of the corresponding site.'),
                  'Variable Modifications':('Amino acid modifications that may or may '
                                            'not be present on the corresponding site.'),
                  'Ions':('Ion types to include in the spectrum score.'),
                  'Include Reverse':('Automatically perform a "decoy search" with'
                                     'decoy peptide seqeunces made by reversing'
                                     'the peptide sequences from the database,'
                                     'for False Discovery Rate analysis.'),
                  'Cyclic Permutation':('XTandem uses the statistical distribution '
                                        'of all potential peptide scores to determine '
                                        'the strength of a spectrum match; for searches '
                                        'against small protein databases, there may '
                                        'not be a large enough collection of peptides '
                                        'to obtain accurate results.  This option '
                                        'includes cyclic permutations of all peptides '
                                        'matching a spectrum precursor mass, resulting '
                                        'in larger score distribution.'),
                  'Min. Ion Count':('Minimum number of scored ions required for'
                                   'a valid spectrum.'),
                  'Protein C-Term Mass':('Mass modification to apply to the C-terminal '
                                      'residue of the protein, for terminal peptides.'),
                  'Protein N-Term Mass':('Mass modification to apply to the N-terminal '
                                      'residue of the protein, for terminal peptides.'),
                  'Peptide N-Term Mass':('Expected mass modification on the N-terminal '
                                         'residue of individual peptides.  Typically '
                                         'this will be the mass of a single hydrogen '
                                         'atom.\n\nNote: If there are fixed N-terminal '
                                         'modifications specified, this parameter '
                                         'will be ignored in favor of the modification '
                                         'mass.'),
                  'Peptide C-Term Mass':('Expected mass modification on the C-terminal '
                                         'residue of individual peptides.  Typically '
                                         'this will be the mass of an OH group. '
                                         '\n\nNote: If there are fixed C-terminal '
                                         'modifications specified, this parameter '
                                         'will be ignored in favor of the modification '
                                         'mass.'),
                  'Semi-Enzymatic Cleavage':('Peptides may be cleaved by contaminating '
                                             'proteolytic enzymes; to account for this,'
                                             'this option includes peptides where only'
                                             'one terminus corresponds to a site of the'
                                             'specified enzyme, and the other terminus'
                                             'is arbitrary.'),
                  'Use Annotation File':('Tandem allows a protein database file to be '
                                         'supplemented with an annotation file, which '
                                         'specifies which modifications are present '
                                         'on a by-protein basis.  This controls whether'
                                         'such a file is used.'),
                  'Refine With Annotation File':('Tandem allows a protein database file to be '
                                                 'supplemented with an annotation file, which '
                                                 'specifies which modifications are present '
                                                 'on a by-protein basis.  This controls whether'
                                                 'such a file is used.'),
                  'Total Peaks':('The maximum number of peaks from a given spectrum'
                                 '(chosen in order of most intense) that will be used'
                                 'for scoring.'),
                  'Minimum Fragment m/z':('Fragment peaks below this value will '
                                          'be ignored.'),
                  'Dynamic Range':('Fragment ion intensities will be linearly '
                                   'scaled to this value.'),
                  'Noise Suppression':('This enables a number of methods by which '
                                       'spectra that are likely to not correspond '
                                       'to true peptides are omitted from the '
                                       'search.  This improves search speed but'
                                       'may miss some peptide spectra.'),
                  'Minimum Peaks':('A noise suppression method; spectra with fewer '
                                   'peaks than this are discarded.'),
                  'Minimum Precursor m+h':('A noise suppression method; spectra '
                                           'derived from precursors of lower than '
                                           'this mass are discarded.'),
                  'Remove Similar Spectra':('There are often redundant MS2 acquisitions '
                                            'of the same peptide precursor, particularly '
                                            'for notably intense precursors; this omits '
                                            'spectra that are too similar (determined'
                                            'via the specified contrast angle) from'
                                            'the search.'),
                  'Min. Contrast Angle':('To determine if two spectra with matching precursor'
                                         'masses are likely to be derived from the same '
                                         'peptide, the opening angle between both spectra '
                                         'is determined; an opening angle of 0 will always '
                                         'register a duplicate, while an angle of 90 will '
                                         'always register both spectra as unique.'),
                  'Remove Neutral Loss':('The fragmentation process may chemically '
                                         'modify a portion of the product ions, '
                                         'resulting in redundant peaks that are '
                                         'shifted from the true fragment mass by '
                                         'some amount.  This removes potential '
                                         'neutral loss ions from the spectra prior '
                                         'to scoring, in order to prevent statistical ' 
                                         'interference.'),
                  'Mass':('The mass that is expected to be lost in the neutral '
                          'loss peaks of fragment ions.'),
                  'Window':('+/- tolerance window for fragment neutral loss '
                            'ions; all peaks within this range of the theoretical '
                            'neutral loss ion will be removed.'),
                  'Enable Refinement Step':('Tandem is capable of a two-stage search '
                                            'process which will often speed up search '
                                            'for complex peptide specifications.  If '
                                            'this is unchecked, the other given parameters '
                                            'are used as usual.  If this is selected, '
                                            'most of the above parameters are used only '
                                            'for an initial search, and then a second '
                                            '"refinement" search is done using the sequences'
                                            'identified from the first.  The refinement '
                                            'search may include more modifications or '
                                            'more permissive settings than the first-'
                                            'pass search.'),
                  'Use For Full Refinement':('Use variable modification settings '
                                             'identicical to the first-stage search '
                                             'in the refinement step.'),
                  'Point Mutations':('Test for possible point mutations in the '
                                     'sequences identified from the first-stage '
                                     'search.'),
                  'Spectrum Synthesis':('When scoring a spectrum, this will take '
                                        'into account the probability of fragmentation '
                                        'at each amino acid bond.'),
                  'Data File':('The target MGF file for this run.'),
                  'Parameter File':('XML parameter file that these settings have '
                                    'been loaded from and/or will be saved to.'),
                  'FASTA Files':('FASTA databases that will be searched.  '
                                 '\n\n'
                                 'XTandem natively maintains a list of FASTA '
                                 'files by taxon, but the mzDesktop search '
                                 'utility does not make use of this feature.'),
                  'Output File':('Destination for the search results.')}




nameToParameter = {'Enzyme':'protein, cleavage site',
                   'Missed Cleavages':'scoring, maximum missed cleavage sites',
                   #'Fixed Modifications':'residue, modification mass',
                   #'Variable Modifications':'residue, potential modification mass',
                   'Precursor Tol.':'spectrum, parent monoisotopic mass error plus',
                   #'Precursor Tol.':'spectrum, parent monoisotopic mass error minus',
                   'Precursor Tol. Units':'spectrum, parent monoisotopic mass error units',
                   'Fragment Tol.':'spectrum, fragment monoisotopic mass error',
                   'Fragment Tol. Units':'spectrum, fragment monoisotopic mass error units',
                   'Maximum Expectation Value':'output, maximum valid expectation value',
                   'Accept C13 Mass':'spectrum, parent monoisotopic mass isotope error',
                   'Mass Type':'spectrum, fragment mass type',
                   'Include Reverse':'scoring, include reverse',
                   'Cyclic Permutation':'scoring, cyclic permutation',
                   'Min. Ion Count':'scoring, minimum ion count',
                   'Peptide C-Term Mass':'protein, cleavage C-terminal mass change',
                   'Peptide N-Term Mass':'protein, cleavage N-terminal mass change',
                   'Protein C-Term Mass':'protein, C-terminal residue modification mass',
                   'Protein N-Term Mass':'protein, N-terminal residue modification mass',
                   'Semi-Enzymatic Cleavage':'protein, cleavage semi',
                   #'Use Annotation File':'protein, use annotations',
                   'Minimum Fragment m/z':'spectrum, minimum fragment m/z',
                   'Dynamic Range':'spectrum, dynamic range',
                   'Total Peaks':'spectrum, total peaks',
                   'Minimum Peaks':'spectrum, minimum peaks',
                   'Noise Suppression':'spectrum, use noise suppression',
                   'Minimum Precursor m+h':'spectrum, minimum parent m+h',
                   'Use Contrast Angle':'spectrum, use contrast angle',
                   'Neutral Loss':'spectrum, use neutral loss window',
                   'Mass':'spectrum, neutral loss mass',
                   'Window':'spectrum, neutral loss window',
                   'Enable Refinement Step':'refine',
                   'Fixed Modifications':'refine, modification mass',
                   #'Variable Modifications':'refine, potential modification mass',
                   #'Maximum Expected Value': 'refine, maximum valid expectation value',
                   'Use For Full Refinement':'refine, use potential modifications for full refinement',
                   #'Semi-Enzymatic Cleavage':'refine, cleavage semi', # Repeat.
                   'Point Mutations':'refine, point mutations',
                   'Unanticipated Cleavage':'refine, unanticipated cleavage',
                   'Spectrum Synthesis':'refine, spectrum synthesis'}
                   #'Refine With Annotation File':'refine, use annotations'}

#parameterToName = dict([(v, k) for k, v in nameToParameter.items()])

specialCaseParameters = ['Fixed Modifications',
                         'Variable Modifications',
                         'Data File',
                         'FASTA Files',
                         'Parameter File',
                         'Refine Maximum Expectation Value',
                         'Precursor Tol.',
                         'Enzyme']

def modNamesToAADeltaStr(mods):
    # Mods should be in 'Phospho (T)'-ish format.
    aashifts = defaultdict(float)
    for mod in mods:
        aas = mod.split()[-1].strip('() ')
        modname = mod.split()[0]
        try:
            shift = mod_masses[modname]
        except KeyError:
            try:
                shift = float(modname)
            except ValueError:            
                shift = unimod.get_mod_delta(modname)
        
        for aa in aas:
            assert aa
            aashifts[aa] += shift
    
    
    modstrs = []
    for aa, shift in aashifts.items():
        substr = '%.3f@%s' % (shift, aa)
        modstrs.append(substr)
        
    return ','.join(modstrs)

# There's no information about the actual source of the mod
# masses in the xtandem parameter file!
def aaDeltaStrToMods(deltaStr):
    if not deltaStr:
        return []
    
    mods = []
    for substr in deltaStr.split(','):
        substr = substr.strip()
        mass, site = substr.split('@')
        mods.append((float(mass), site))
    
    return mods
    
    
    


class XTandemSearch(wx.Dialog):
    def label(self, control):
        text = wx.StaticText(self.pane, -1, control.GetName())
        name = control.GetName()
        name = name.replace('\n', ' ')
        try:
            text.SetToolTip(wx.ToolTip(nameToHelptext[name]))
        except KeyError:
            print "No tooltip: %s" % name
        return text
    
    def addWithLabel(self, gbs, ctrl, xy, **kwargs):
        gbs.Add(self.label(ctrl), xy, flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        #flags = wx.ALIGN_RIGHT | kwargs['flag'] if 'flag' in kwargs else wx.ALIGN_RIGHT
        kwargs['flag'] = kwargs.get('flag', 0) | wx.ALIGN_CENTER_VERTICAL
        gbs.Add(ctrl, (xy[0], xy[1]+1), **kwargs)
    
    def __init__(self, parent, datafile):
        """
        XTandem Search GUI.
        """
        # Going based on the old GUI, there are five main sections:
        # - Main FASTA/tolerances/mods/files/etc selection, as 
        #   per any search setup GUI.
        # - Scoring controls; y, b, etc ions being counted
        # - C- and N-term mass changes.
        # - Spectrum controls.
        # - "Refine" parameters, which I'm not sure what that means.
        #
        # Each will be implemented in its own sizer, though I won't likely
        # deal with the pop-in controls from the last one.
        
        wx.Dialog.__init__(self, parent, -1, "X! Tandem Search Utility",
                          style = wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.pane = pane = wx.Panel(self, -1,
                                    style = wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN)
        
        self.loadData()
        
        #menu_bar = wx.MenuBar()
        #file_menu = wx.Menu()
        
        #load_xml = wx.MenuItem(file_menu, -1, "&Open XML Template File...\tCtrl+O")
        #file_menu.AppendItem(load_xml)
        #self.Bind(wx.EVT_MENU, self.on_load_XML, load_xml)
    
        #save_xml = wx.MenuItem(file_menu, -1, "&Save Parameters As...\tCtrl+S")
        #file_menu.AppendItem(save_xml)
        #self.Bind(wx.EVT_MENU, self.on_save_XML, save_xml)        
        #menu_bar.append(file_menu)
        
        #self.SetMenuBar(menu_bar)
        
        

        mainLabel = wx.StaticText(pane, -1, "X!Tandem Search Utility")
        ionLabel = wx.StaticText(pane, -1, "Scoring")
        proteinLabel = wx.StaticText(pane, -1, "Protein")
        spectrumLabel = wx.StaticText(pane, -1, "Spectrum")
        refineLabel = wx.StaticText(pane, -1, "Refine")
        
        mainLabel.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        ionLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        proteinLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        spectrumLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        refineLabel.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD))
        

        
        # Use self.label (above) instead!
        #self.taxonLabel = wx.TextBox(self, -1, 'Taxonomy')
        #self.taxonCtrl = wx.ComboBox(pane, -1, choices = taxonList, value = taxonList[0],
                                     #size = (80, -1),
                                     #name = 'Taxonomy')
        
        #self.enzymeLabel = wx.TextBox(self, -1, "Enzyme")
        self.enzymeCtrl = wx.ComboBox(pane, -1, choices = enzymeList.keys(),
                                      value = 'Trypsin',
                                      size = (80, -1),
                                      name = 'Enzyme')
        
        #self.fixmodLabel = wx.TextBox(self, -1, "Fixed Modifications")
        self.fixmodCtrl = wx.CheckListBox(pane, -1, choices = fixmods,
                                          #style = wx.LB_SORT,
                                          name = 'Fixed\nModifications',
                                          size = (-1, 100))
        #self.varmodLabel = wx.TextBox(self, -1, "Variable Modifications")
        self.varmodCtrl = wx.CheckListBox(pane, -1, choices = varmods,
                                          #style = wx.LB_SORT,
                                          name = 'Variable\nModifications',
                                          size = (-1, 100))
        
        self.Bind(wx.EVT_CHECKLISTBOX, self.copyModsToRefine, self.fixmodCtrl)
        self.Bind(wx.EVT_CHECKLISTBOX, self.copyModsToRefine, self.varmodCtrl)
        
        #self.cleavageLabel = wx.TextBox(self, -1, "Missed Cleavages")
        self.cleavageBox = wx.TextCtrl(pane, -1, value = "2", 
                                       name = "Missed\nCleavages",
                                       size = stdTxtCtrlSize)
        
        self.precursorTol = wx.TextCtrl(pane, -1, value = '25', size = (45, -1),
                                        name = 'Precursor Tol.')
        # Old GUI alludes to XTandem taking separate values for positive
        # and negative precursor error- does it?
        self.precursorUnit = wx.ComboBox(pane, -1, choices = mzUnits,
                                         value = 'ppm',
                                         name = 'Precursor Tol. Units',
                                         size = (55, -1))
        
        self.fragmentTol = wx.TextCtrl(pane, -1, value = '0.025', size = (45, -1),
                                       name = 'Fragment Tol.')
        self.fragmentUnit = wx.ComboBox(pane, -1, choices = mzUnits,
                                        value = 'Da',
                                        name = 'Fragment Tol. Units',
                                        size = (55, -1))
        
        # Expected value threshold for a peptide to be recorded.
        self.maxExpectationValue = wx.TextCtrl(pane, -1, value = '0.1',
                                               name = 'Maximum Expectation Value',
                                               size = stdTxtCtrlSize)
        
        self.isotopeError = wx.CheckBox(pane, -1, label = 'Accept C13 Mass',
                                        name = 'Accept C13 Mass')
        
        self.massType = wx.ComboBox(pane, -1,
                                    choices = ['Monoisotopic', 'Average'],
                                    name = 'Mass Type',
                                    value = 'Monoisotopic')
        
        self.primaryControls = [self.enzymeCtrl, self.fixmodCtrl,
                                self.varmodCtrl, self.cleavageBox, self.precursorTol,
                                self.precursorUnit, self.fragmentTol, self.fragmentUnit,
                                self.maxExpectationValue, self.isotopeError,
                                self.massType]
        
        
        ### Peptide Ion Controls
        self.ionBox = wx.StaticBox(pane, -1, label = 'Ions')
        self.ionBox.SetToolTip(wx.ToolTip(nameToHelptext['Ions']))
        self.ionSizer = wx.StaticBoxSizer(self.ionBox)
        for ion in ['a','b','c','x','y','z']:
            ionctrl = wx.CheckBox(pane, -1, ion, name = '%s ions' % ion)
            if ion in ['b', 'y']:
                ionctrl.SetValue(True)
            ionctrl.SetToolTip(wx.ToolTip(nameToHelptext['Ions']))
            self.ionSizer.Add(ionctrl, 0, wx.ALL, 5)

        
        
        self.includeRevCtrl = wx.CheckBox(pane, -1, label = 'Include Reverse',
                                          name = 'Include Reverse')
        self.cyclicPerCtrl = wx.CheckBox(pane, -1, label = 'Cyclic Permutation',
                                         name = 'Cyclic Permutation')
        
        self.minIonCount = wx.TextCtrl(pane, -1, value = '1', size = stdTxtCtrlSize, 
                                       name = 'Min. Ion Count')
        
        self.peptideControls = [self.ionBox, self.includeRevCtrl,
                                self.cyclicPerCtrl, self.minIonCount]
        
        
        ### Protein Mass Controls
        

        self.ntermPepmassCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize,
                                            name = 'Peptide N-Term Mass')
        self.ctermPepmassCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize,
                                            name = 'Peptide C-Term Mass')
        
        self.ntermModmassCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize,
                                            name = 'Protein N-Term Mass')
        self.ctermModmassCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, 
                                            name = 'Protein C-Term Mass')
        
        self.semienzymeCleavage = wx.CheckBox(pane, -1, 'Semi-Enzymatic Cleavage',
                                              name = 'Semi-Enzymatic Cleavage')
        #self.useAnnotationsCtrl = wx.CheckBox(pane, -1, 'Use Annotation File',
                                              #name = 'Use Annotation File')
        
        self.proteinControls = [self.ntermModmassCtrl, self.ntermPepmassCtrl,
                                self.ctermModmassCtrl, self.ctermPepmassCtrl,
                                self.semienzymeCleavage]#, self.useAnnotationsCtrl]
        
        
        ### Spectrum Controls
        
        self.minimumFragCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Minimum Fragment m/z')
        self.totalPeaksCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Total Peaks')
        self.dynamicRangeCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Dynamic Range')
        self.minimumPeaksCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Minimum\nPeaks')
        self.minimumParMH = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Minimum\nPrecursor m+h')
        
        self.noiseSuppresionCheck = wx.CheckBox(pane, -1, 'Noise Suppression',
                                                name = 'Noise Suppression')
        self.contrastAngleCheck = wx.CheckBox(pane, -1, 'Remove Similar Spectra',
                                              name = 'Use Contrast Angle')
        self.neutralLossCheck = wx.CheckBox(pane, -1, 'Remove Neutral Loss',
                                            name = 'Neutral Loss')
        
        self.Bind(wx.EVT_CHECKBOX, self.toggleNoiseSup, self.noiseSuppresionCheck)
        self.Bind(wx.EVT_CHECKBOX, self.toggleAngleCheck, self.contrastAngleCheck)
        self.Bind(wx.EVT_CHECKBOX, self.toggleNeutralLoss, self.neutralLossCheck)
        
        self.angleCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Min. Contrast Angle')
        self.massCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Mass')
        self.windowCtrl = wx.TextCtrl(pane, -1, size = stdTxtCtrlSize, name = 'Window')
        
        # Non-exhaustive, just for checkbox tooltips.
        self.spectrumControls = [self.noiseSuppresionCheck, self.contrastAngleCheck,
                                 self.neutralLossCheck]
        
        ### Refine Step Controls
        
        self.refineCheck = wx.CheckBox(pane, -1, 'Enable Refinement Step',
                                       name = 'Enable Refinement Step')
        self.Bind(wx.EVT_CHECKBOX, self.toggleRefine, self.refineCheck)
        
        # Dunno WHY XTandem allows refinement-specific fixed modifications, but it does.
        self.refineFixMods = wx.CheckListBox(self, -1, choices = fixmods,
                                             name = 'Refinement Fixed\nModifications',
                                             size = (-1, 100))
        self.refineVarMods = wx.CheckListBox(self, -1, choices = varmods,
                                             name = 'Refinement Variable\nModifications',
                                             size = (-1, 100))
        
        self.refineFixLabel = wx.StaticText(pane, -1, "Refinement Fixed\nModifications")
        self.refineVarLabel = wx.StaticText(pane, -1, "Refinement Variable\nModifications")
        
        self.refineMaxExpLabel = wx.StaticText(pane, -1, 'Maximum Expectation Value')
        self.refineMaxExpLabel.SetToolTip(wx.ToolTip(nameToHelptext['Maximum Expectation Value']))
        self.refineMaxExpVal = wx.TextCtrl(pane, -1, name = 'Refine Maximum Expectation Value',
                                           size = stdTxtCtrlSize)

        self.refineSemiEznyme = wx.CheckBox(pane, -1, 'Semi-Enzymatic Cleavage',
                                            name = 'Semi-Enzymatic Cleavage')
        self.refineUnanticiaptedClvg = wx.CheckBox(pane, -1, 'Unanticipated Cleavage',
                                                   name = 'Unanticipated Cleavage')
        self.refinePtMutations = wx.CheckBox(pane, -1, 'Point Mutations',
                                             name = 'Point Mutations')
        self.refineSpectrumSynth = wx.CheckBox(pane, -1, 'Spectrum Synthesis',
                                               name = 'Spectrum Synthesis')
        #self.refineUseAnnotations = wx.CheckBox(pane, -1, 'Refine With Annotation File',
                                                #name = 'Refine With Annotation File')
        
        self.refineFixed = wx.CheckBox(pane, -1, "Use Main Fixed Mod List",
                                       name = "Use For Full Refinement, Fixed")
        self.refineFull = wx.CheckBox(pane, -1, 'Use Main Variable Mod List',
                                      name = 'Use For Full Refinement')
        
        self.Bind(wx.EVT_CHECKBOX, self.modBindToggle, self.refineFixed)
        self.Bind(wx.EVT_CHECKBOX, self.modBindToggle, self.refineFull)
        
        self.refineControls = [self.refineFixMods, self.refineVarMods,
                               self.refineFixLabel, self.refineVarLabel,
                               self.refineMaxExpVal, self.refineSemiEznyme,
                               self.refineUnanticiaptedClvg, self.refinePtMutations,
                               self.refineSpectrumSynth, self.refineFixed,
                               self.refineFull, #self.refineUseAnnotations,
                               self.refineMaxExpLabel]
        self.toggleRefine(None)
        self.toggleNoiseSup(None)
        self.toggleAngleCheck(None)
        self.toggleNeutralLoss(None)
        
        
        #### Parameter File Controls
        self.dataCtrl = wx.TextCtrl(pane, -1, name = 'Data File')
        self.dataButton = wx.Button(pane, -1, "Browse")
        self.Bind(wx.EVT_BUTTON, self.browse, self.dataButton)    
        
        self.outputCtrl = wx.TextCtrl(pane, -1, name = "Output File")
        self.outputButton = wx.Button(pane, -1, "Browse")        
        
        # Modification for mzStudio. Also see not placing self.dataCtrl in
        # sizer (to avoid intializing the StaticText label)
        self.dataCtrl.SetValue(datafile)
        for ctrl in [self.dataCtrl, self.dataButton,
                     self.outputCtrl, self.outputButton]:
            ctrl.Enable(False)
            ctrl.Show(False)
            
        
        self.fastaCtrl = wx.TextCtrl(pane, -1, name = 'FASTA Files')
        self.fastaButton = wx.Button(pane, -1, "Browse")
        self.Bind(wx.EVT_BUTTON, self.browseFasta, self.fastaButton)
        
        self.parCtrl = wx.TextCtrl(pane, -1, name = 'Parameter File',
                                   value = '<Unsaved Parameters>')
        self.parButton = wx.Button(pane, -1, "Browse")
        self.Bind(wx.EVT_BUTTON, self.openParameterFile, self.parButton)
        
        self.saveParFileButton = wx.Button(pane, -1, 'Save Parameters')
        self.runSearchButton = wx.Button(pane, -1, "Run Search")
        

        
        self.Bind(wx.EVT_BUTTON, self.saveParameterFile, self.saveParFileButton)
        self.Bind(wx.EVT_BUTTON, self.runSearch, self.runSearchButton)
        
        
        
        
        
        
        
        
        primarySizer = wx.GridBagSizer(5, 5)
        
        primarySizer.Add(mainLabel, (0, 0), span = (1, 3), border = 10,
                         flag = wx.ALIGN_CENTRE | wx.BOTTOM)
        
        topMain = wx.GridBagSizer(2, 2)  
        topMain.Add(wx.StaticText(pane, -1, 'Fixed\nModifications'),
                    (0, 0), flag = wx.ALIGN_LEFT)
        topMain.Add(self.fixmodCtrl, (1, 0), flag = wx.EXPAND)
        topMain.Add(wx.StaticText(pane, -1, "Variable\nModifications"),
                    (0, 1), flag = wx.ALIGN_LEFT)
        topMain.Add(self.varmodCtrl, (1, 1), flag = wx.EXPAND)
        

        tolSizer = wx.GridBagSizer(5, 2)
        self.addWithLabel(tolSizer, self.precursorTol, (0, 0))
        tolSizer.Add(self.precursorUnit, (0, 2))
    
        self.addWithLabel(tolSizer, self.fragmentTol, (1, 0))
        tolSizer.Add(self.fragmentUnit, (1, 2))
    
    
        subprimary = wx.GridBagSizer(10, 10)
        
        self.addWithLabel(subprimary, self.massType, (0, 0))
        subprimary.Add(self.isotopeError, (1, 1), span = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)              
        subprimary.Add(tolSizer, (2, 0), span = (2, 2))

        self.addWithLabel(subprimary, self.enzymeCtrl, (0, 2))

        subprimary.Add(wx.StaticText(pane, -1, 'Missed\nCleavages'),
                       (1, 2), span = (2, 1), flag = wx.ALIGN_RIGHT)
        subprimary.Add(self.cleavageBox, (1, 3), span = (2, 1), 
                       flag = wx.ALIGN_LEFT)
        
        maxExpLabel = wx.StaticText(pane, -1, "Maximum Expectation Value")
        maxExpLabel.SetToolTip(wx.ToolTip(nameToHelptext['Maximum Expectation Value']))
        subprimary.Add(maxExpLabel,
                       (4, 0), span = (1, 2), flag = wx.ALIGN_RIGHT)
        subprimary.Add(self.maxExpectationValue,
                       (4, 2), flag = wx.ALIGN_LEFT)
        #subprimary.Add()
        
        primarySizer.Add(topMain, (1, 0), span = (2, 1), border = 5, flag = wx.RIGHT | wx.EXPAND)
        primarySizer.Add(subprimary, (1, 1), span = (1, 2), border = 5, flag = wx.LEFT | wx.EXPAND)

        
        ionCtrlSizer = wx.GridBagSizer(5, 5)
        ionCtrlSizer.Add(ionLabel, (0, 0), span = (1, 3), border = 10,
                         flag = wx.ALIGN_CENTRE | wx.BOTTOM)
        ionCtrlSizer.Add(self.ionSizer, (1, 0), span = (3, 3), flag = wx.EXPAND)
        ionCtrlSizer.Add(self.includeRevCtrl, (4, 0))
        ionCtrlSizer.Add(self.cyclicPerCtrl, (4, 1))
        
        self.addWithLabel(ionCtrlSizer, self.minIonCount, (5, 0))

        
        proteinSizer = wx.GridBagSizer(5, 5)
        proteinSizer.Add(proteinLabel, (0, 0), span = (1, 3), border = 10,
                         flag = wx.ALIGN_CENTRE | wx.BOTTOM)
        self.addWithLabel(proteinSizer, self.ntermModmassCtrl, (1, 0),
                          border = 20, flag = wx.RIGHT)
        self.addWithLabel(proteinSizer, self.ctermModmassCtrl, (2, 0),
                          border = 20, flag = wx.RIGHT)
        self.addWithLabel(proteinSizer, self.ntermPepmassCtrl, (1, 2))
        self.addWithLabel(proteinSizer, self.ctermPepmassCtrl, (2, 2))
        proteinSizer.Add(self.semienzymeCleavage, (3, 1), span = (1, 3),
                         border = 10,
                         flag = wx.ALIGN_LEFT | wx.TOP)
        #proteinSizer.Add(self.useAnnotationsCtrl, (4, 1), span = (1, 3),
                         #flag = wx.ALIGN_LEFT )
        
        
        spectrumSizer = wx.GridBagSizer(5, 5)
        spectSetSizer = wx.GridBagSizer(5, 5)

        spectSetSizer.Add(self.noiseSuppresionCheck, (0, 0))
        self.addWithLabel(spectSetSizer, self.minimumPeaksCtrl, (0, 1))
        self.addWithLabel(spectSetSizer, self.minimumParMH, (0, 3))
        spectSetSizer.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL),
                          (1, 0), span = (1, 5), flag = wx.ALL | wx.EXPAND)
        spectSetSizer.Add(self.contrastAngleCheck, (2, 0))
        self.addWithLabel(spectSetSizer, self.angleCtrl, (2, 1))
        spectSetSizer.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL),
                          (3, 0), span = (1, 5), flag = wx.ALL | wx.EXPAND)
        spectSetSizer.Add(self.neutralLossCheck, (4, 0))
        self.addWithLabel(spectSetSizer, self.massCtrl, (4, 1))
        self.addWithLabel(spectSetSizer, self.windowCtrl, (4, 3))
        
        
        self.addWithLabel(spectrumSizer, self.totalPeaksCtrl, (0, 0))
        self.addWithLabel(spectrumSizer, self.minimumFragCtrl, (1, 0))
        self.addWithLabel(spectrumSizer, self.dynamicRangeCtrl, (2, 0))
        
        spectrumSizer.Add(wx.StaticLine(pane, -1, style = wx.LI_VERTICAL),
                          (0, 2), span = (3, 1), border = 20, flag = wx.LEFT | wx.RIGHT | wx.EXPAND)
        spectrumSizer.Add(spectSetSizer, (0, 3), span = (4, 3))
        spectrumSizer.AddGrowableCol(2)
        
        
 
        refModSizer = wx.GridBagSizer(5, 5)
        refModSizer.Add(self.refineFixLabel, (0, 0))
        refModSizer.Add(self.refineFixed, (1, 0))
        refModSizer.Add(self.refineFixMods, (2, 0), flag = wx.EXPAND)
        refModSizer.Add(self.refineVarLabel, (0, 1))
        refModSizer.Add(self.refineFull, (1, 1))
        refModSizer.Add(self.refineVarMods, (2, 1), flag = wx.EXPAND)
        
        subRefine = wx.GridBagSizer(10, 10)
        #subRefine.Add(self.refineFull, (0, 0))
        subRefine.Add(self.refineSemiEznyme, (0, 0))
        subRefine.Add(self.refineUnanticiaptedClvg, (1, 0))
        subRefine.Add(self.refinePtMutations, (2, 0))
        subRefine.Add(self.refineSpectrumSynth, (3, 0))
        #subRefine.Add(self.refineUseAnnotations, (4, 0))
        
        subRefine.Add(self.refineMaxExpLabel, (5, 0), flag = wx.ALIGN_RIGHT)
        subRefine.Add(self.refineMaxExpVal, (5, 1))
        
        refineSizer = wx.GridBagSizer(5, 5)
        refineSizer.Add(self.refineCheck, (0, 0), span = (1, 4), border = 10,
                        flag = wx.ALIGN_CENTRE | wx.BOTTOM)
        refineSizer.Add(refModSizer, (1, 1))
        refineSizer.Add(subRefine, (1, 2), border = 10, flag = wx.ALL)
        
        refineSizer.AddGrowableCol(0)
        refineSizer.AddGrowableCol(3)
        
        
        buttonSizer = wx.GridBagSizer(5, 5)
        self.addWithLabel(buttonSizer, self.dataCtrl, (0, 0), span = (1, 2), flag = wx.EXPAND)
        buttonSizer.Add(self.dataButton, (0, 3))
        self.addWithLabel(buttonSizer, self.parCtrl, (1, 0), span = (1, 2), flag = wx.EXPAND)
        buttonSizer.Add(self.parButton, (1, 3))
        self.addWithLabel(buttonSizer, self.fastaCtrl, (2, 0), span = (1, 2), flag = wx.EXPAND)
        buttonSizer.Add(self.fastaButton, (2, 3))
        self.addWithLabel(buttonSizer, self.outputCtrl, (3, 0), span = (1, 2), flag = wx.EXPAND)
        buttonSizer.Add(self.outputButton, (3, 3))
        buttonSizer.Add(self.saveParFileButton, (4, 1), flag = wx.EXPAND)
        buttonSizer.Add(self.runSearchButton, (4, 2), flag = wx.EXPAND)
        buttonSizer.AddGrowableCol(1)
        buttonSizer.AddGrowableCol(2)
        

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(primarySizer, 0, wx.ALL | wx.EXPAND, 5)
        box.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL), 0, wx.ALL | wx.EXPAND, 5)
        subbox = wx.BoxSizer(wx.HORIZONTAL)
        subbox.Add(ionCtrlSizer, 0, wx.ALL, 5)
        subbox.Add(wx.StaticLine(pane, -1, style = wx.LI_VERTICAL), 0, wx.ALL | wx.EXPAND, 5)
        subbox.Add(proteinSizer, 0, wx.ALL, 5)
        box.Add(subbox, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
        box.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL), 0, wx.ALL | wx.EXPAND, 5)
        box.Add(spectrumLabel, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        box.Add(spectrumSizer, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
        box.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL), 0, wx.ALL | wx.EXPAND, 5)
        box.Add(refineLabel, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 5)
        box.Add(refineSizer, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
        box.Add(wx.StaticLine(pane, -1, style = wx.LI_HORIZONTAL), 0, wx.ALL | wx.EXPAND, 5)
        box.Add(buttonSizer, 0, wx.ALL | wx.EXPAND, 5) 
        box.Layout()
        
        overBox = wx.BoxSizer()
        overBox.Add(box, 0, wx.ALL, 10)
        
        pane.SetSizerAndFit(overBox)
        self.SetClientSize(pane.GetSize())
        
        leftsize, rightsize = self.fixmodCtrl.GetSize(), self.varmodCtrl.GetSize()
        equalwidth = (leftsize[0] + rightsize[0]) / 2
        self.fixmodCtrl.SetSize((equalwidth, leftsize[1]))
        self.varmodCtrl.SetSize((equalwidth, rightsize[1]))
        
        overBox.Layout()
        #self.Fit()
        self.Centre()
        self.Refresh()
        
        self.did_run = False
        
        for ctrl in (self.primaryControls + self.proteinControls +
                     self.peptideControls + self.spectrumControls +
                     self.refineControls):
            if isinstance(ctrl, wx.CheckBox):
                try:
                    ctrl.SetToolTip(wx.ToolTip(nameToHelptext[ctrl.Label]))
                except KeyError:
                    pass
                
        if os.path.exists(persistent_data):
            persistence = open(persistent_data, 'r').readlines()
            for line in persistence:
                key, val = line.split('=')
                if 'tandem_database' in key:
                    self.fastaCtrl.SetValue(val.strip())
        self.Bind(wx.EVT_CLOSE, self.onClose)
    
    def onClose(self, event):
        if os.path.exists(persistent_data):
            persistence = open(persistent_data, 'r').readlines()
            output = open(persistent_data, 'w')
            wrote_database = False
            for line in persistence:
                key, val = line.split('=')
                if 'tandem_database' in key:
                    wrote_database = True
                    fasta = self.fastaCtrl.GetValue().strip()
                    if fasta:
                        output.write('%s=%s\n' % (key, os.path.abspath(fasta)))
                else:
                    output.write('%s=%s\n' % (key, val))
            if not wrote_database and self.fastaCtrl.GetValue().strip():
                output.write('%s=%s\n' % ('tandem_database', self.fastaCtrl.GetValue().strip()))
            output.close()
        elif self.fastaCtrl.GetValue().strip():
            output = open(persistent_data, 'w')
            output.write('%s=%s\n' % ('tandem_database', self.fastaCtrl.GetValue().strip()))
            output.close()
        
        event.Skip()
                
    
    def loadData(self):
        global enzymeList
        global fixmods
        global varmods
        
        enzymeList = {}
        fixmods = []
        varmods = []
        
        mode = None
        for line in xmlData:
            if '#' in line:
                line = line[:line.index('#')]
            line = line.strip()
            if not line:
                continue
            
            if line == 'START ENZYMES':
                mode = 'enzyme'
            elif line == 'END ENZYMES':
                mode = None
            elif line == 'START MODS':
                mode = 'mod'
            elif line == 'END MODS':
                mode = None
            else:
                assert mode, "Incorrect formatting of XTandem settings- missing 'END ENZYMES' or 'END MODS'?"
                if mode == 'enzyme':
                    regex, label = [x.strip() for x in line.split(' is ')]
                    enzymeList[label] = regex
                elif mode == 'mod':
                    fixmods.append(line)
                    varmods.append(line)
                else:
                    assert mode, "Incorrect formatting of XTandem settings- missing 'END ENZYMES' or 'END MODS'?"
                    if mode == 'enzyme':
                        regex, label = [x.strip() for x in line.split(' is ')]
                        enzymeList[label] = regex
                    elif mode == 'mod':
                        fixmods.append(line)
                        varmods.append(line)
                    else:
                        raise Exception
        fixmods.sort()
        varmods.sort()
    
    
    def browse(self, event):
        filedialog = wx.FileDialog(parent = self, message = "Choose MS Data File",
                                   style = wx.FD_OPEN,
                                   wildcard = 'RAW|*.raw|WIFF|*.wiff|All|*.*') # What is the actual target format?
        
        filedialog.ShowModal()
        newfile = filedialog.GetPath()
        
        self.dataCtrl.Clear()
        self.dataCtrl.SetValue(newfile)
        
        if not self.outputCtrl.GetValue():
            self.outputCtrl.SetValue(newfile + '.xlsx')
        
    def browseFasta(self, event):
        filedialog = wx.FileDialog(parent = self, message = "Choose MS Data File",
                                   style = wx.FD_OPEN | wx.FD_MULTIPLE,
                                   wildcard = 'FASTA|*.fasta|FASTA-Pro|*.pro|All|*.*') # What is the actual target format?
        
        filedialog.ShowModal()
        newfiles = filedialog.GetPaths()
        
        self.fastaCtrl.Clear()
        self.fastaCtrl.SetValue('; '.join(newfiles))        
    
    
    def toggleRefine(self, event):
        refine = self.refineCheck.GetValue()
        for control in self.refineControls:
            control.Enable(refine)
        self.copyModsToRefine()
            
    def toggleNoiseSup(self, event):
        toggle = self.noiseSuppresionCheck.GetValue()
        for control in [self.minimumPeaksCtrl, self.minimumParMH]:
            control.Enable(toggle)
            
    def toggleAngleCheck(self, event):
        toggle = self.contrastAngleCheck.GetValue()
        self.angleCtrl.Enable(toggle)        
    
    def toggleNeutralLoss(self, event):
        toggle = self.neutralLossCheck.GetValue()
        for control in [self.massCtrl, self.windowCtrl]:
            control.Enable(toggle)
            control.Show()
    

    def modBindToggle(self, event):
        # "Bind" as in we're binding the state of the refine fix/var mods
        # ctrls to the state of the main fix/var mod ctrls, NOT as
        # in fiddling with WX event bindings.  Don't worry!
        
        bindfixed = self.refineFixed.GetValue()
        bindvar = self.refineFull.GetValue()
        
        self.refineFixMods.Enable(not bindfixed)
        self.refineVarMods.Enable(not bindvar)
        
        if bindfixed or bindvar:
            self.copyModsToRefine()
        
    def copyModsToRefine(self, event = None):
        if self.refineCheck.GetValue():
            if self.refineFixed.GetValue():
                self.refineFixMods.Clear()
                self.refineFixMods.AppendItems(self.fixmodCtrl.GetStrings())
                self.refineFixMods.SetCheckedStrings(self.fixmodCtrl.GetCheckedStrings())
            if self.refineFull.GetValue():
                self.refineVarMods.Clear()
                self.refineVarMods.AppendItems(self.varmodCtrl.GetStrings())
                self.refineVarMods.SetCheckedStrings(self.varmodCtrl.GetCheckedStrings())
    
    
    def openParameterFile(self, event):
        filedialog = wx.FileDialog(parent = self, message = "Choose MS Data File",
                                   style = wx.FD_OPEN,
                                   wildcard = 'XML|*.xml|All|*.*')
        
        filedialog.ShowModal()
        newfile = filedialog.GetPath()
        self.parCtrl.SetValue(newfile)
        
        if os.path.exists(newfile):
            self.parObjToGUI(newfile)
            print "Loaded %s" % newfile
        else:
            print "New file: %s" % newfile
        
    
    def saveParameterFile(self, event):
        # Should probably have a confirmation dialog!
        
        searchObj = TandemSearch()
        self.GUItoParObj(searchObj)
        
        saveFileName = self.parCtrl.GetValue()
        if os.path.exists(saveFileName):
            originalObject = TandemSearch(saveFileName)
        else:
            originalObject = None
        
        if dict(searchObj) != originalObject:
            if not os.path.exists(saveFileName):
                searchObj.write(outputfile = saveFileName)  
                wx.MessageBox("Wrote %s ." % saveFileName)
            else:
                messdog = wx.MessageDialog(self, "Overwrite %s?" % saveFileName,
                                           style = wx.OK|wx.CANCEL)
                if messdog.ShowModal() == wx.ID_OK:
                    searchObj.write(outputfile = saveFileName)
                    wx.MessageBox("Wrote %s ." % saveFileName)
        else:
            messdog = wx.MessageDialog(self, "Parameter file unchanged.",
                                       style = wx.OK)
            messdog.ShowModal()
    
     
    def parObjToGUI(self, parameterfile):
        searchObj = TandemSearch(parameterfile)
        
        for ctrlname, parname in nameToParameter.items():
            if ctrlname in specialCaseParameters:
                continue
            
            try:
                category, parameter = [x.strip() for x in parname.split(',')]
            except ValueError:
                category = parname # 'refine' in particular.
                parameter = ''
            
            ctrl = self.FindWindowByName(ctrlname)
            if not ctrl:
                spaces = ctrlname.count(' ')
                for i in range(1, spaces+1):
                    ctrl = self.FindWindowByName(ctrlname.replace(' ', '\n', i))
                    if ctrl: break
            
            assert ctrl     
            
            try:
                parvalue = searchObj[category][parameter]
            except KeyError:
                print "Value for %s-%s not found." % (category, parameter)
                continue
            if parvalue:
                parvalue = parvalue.strip()
            
            if parvalue:
                if isinstance(ctrl, wx.CheckBox):
                    assert parvalue in ['yes', 'no']
                    parvalue = parvalue == 'yes'
                ctrl.SetValue(parvalue)
            elif isinstance(ctrl, wx.TextCtrl):
                ctrl.SetValue('')
            elif isinstance(ctrl, wx.Checkbox):
                ctrl.SetValue(False)
            else:
                print "No value for %s (%s, %s)" % (ctrlname, category, parameter)
        
        plustol = float(searchObj['spectrum']['parent monoisotopic mass error plus'])
        minustol = float(searchObj['spectrum']['parent monoisotopic mass error minus'])
        self.FindWindowByName('Precursor Tol.').SetValue(str(plustol + minustol))
        
        fixmodstr = searchObj['residue']['modification mass']
        varmodstr = searchObj['residue']['potential modification mass']
        #if searchObj['refine']['']:
            #refinefixmodstr = searchObj['refine'].get('modification mass', '')
            #refinevarmodstr = searchObj['refine'].get('potential modification mass')
        
        fixmods = aaDeltaStrToMods(fixmodstr)
        varmods = aaDeltaStrToMods(varmodstr)
        if searchObj['refine']['']:
            refinefixmodstr = searchObj['refine'].get('modification mass', '')
            refinefixmods = aaDeltaStrToMods(refinefixmodstr) 
            refinevarmodstr = searchObj['refine'].get('potential modification mass', '')
            refinevarmods = aaDeltaStrToMods(refinevarmodstr)
        else:
            refinefixmods = []
            refinevarmods = []
            
        for mass, site in fixmods:
            modstring = '%f (%s)' % (mass, site)
            self.fixmodCtrl.Insert(modstring, 0)
            self.fixmodCtrl.Check(0)
        for mass, site in varmods:
            modstring = '%f (%s)' % (mass, site)
            self.varmodCtrl.Insert(modstring, 0)
            self.varmodCtrl.Check(0)
        if refinefixmods: # Can be None
            for mass, site in refinefixmods:
                modstring = '%f (%s)' % (mass, site)
                self.refineFixMods.Insert(modstring, 0)
                self.refineFixMods.Check(0)
        if refinevarmods:
            for mass, site in refinevarmods:
                modstring = '%f (%s)' % (mass, site)
                self.refineVarMods.Insert(modstring, 0)        
                self.refineVarMods.Check(0)
        
        self.maxExpectationValue.SetValue(searchObj['output']['maximum valid expectation value'])
        self.refineMaxExpVal.SetValue(searchObj['refine']['maximum valid expectation value'])
        
            
            
    
    
    def GUItoParObj(self, searchobj):
        for ctrlname, parname in nameToParameter.items():
            if ctrlname in specialCaseParameters:
                continue
            
            try:
                category, parameter = [x.strip() for x in parname.split(',')]
            except ValueError:
                category = parname # 'refine' in particular.
                parameter = ''            
            
            ctrl = self.FindWindowByName(ctrlname)
            if not ctrl:
                spaces = ctrlname.count(' ')
                for i in range(1, spaces+1):
                    ctrl = self.FindWindowByName(ctrlname.replace(' ', '\n', i))
                    if ctrl: break
            
            assert ctrl
            if isinstance(ctrl, wx.CheckBox):
                value = 'yes' if ctrl.GetValue() else 'no'
                searchobj[category][parameter] = value
            else:
                value = ctrl.GetValue()
                searchobj[category][parameter] = value
        
        #searchobj['refine'][''] = 'yes' if self.FindWindowByName('Refine').GetValue()) else 'no'
        
        enzymename = self.FindWindowByName('Enzyme').GetValue()
        cleavage = enzymeList[enzymename]
        searchobj['protein']['cleavage site'] = cleavage
        
        totalprectol = self.FindWindowByName('Precursor Tol.').GetValue()
        halftol = float(totalprectol) / 2
        searchobj['spectrum']['parent monoisotopic mass error minus'] = halftol
        searchobj['spectrum']['parent monoisotopic mass error plus'] = halftol
        
        fixmods = self.fixmodCtrl.GetCheckedStrings()
        varmods = self.varmodCtrl.GetCheckedStrings()
        searchobj['residue']['modification mass'] = modNamesToAADeltaStr(fixmods)
        searchobj['residue']['potential modification mass'] = modNamesToAADeltaStr(varmods)
        if self.refineCheck.GetValue():
            refinefixmods = self.refineFixMods.GetCheckedStrings()
            refinevarmods = self.refineVarMods.GetCheckedStrings()
            searchobj['refine']['modification mass'] = modNamesToAADeltaStr(refinefixmods)
            searchobj['refine']['potential modification mass'] = modNamesToAADeltaStr(refinevarmods)
            
        searchobj.fasta_files = self.fastaCtrl.GetValue().split('; ')
        
        parfilename = self.parCtrl.GetValue()
        if not parfilename.strip() or parfilename == u'<Unsaved Parameters>':
            parfilename = 'temp_tandem_parameters.xml'
        searchobj.file_name = parfilename
        
    def runSearch(self, event):
        searchObj = TandemSearch()
        self.GUItoParObj(searchObj)
        searchObj.write(outputfile = self.dataCtrl.GetValue() + '.searchRecord.xml')
        
        datafile = self.dataCtrl.GetValue()
        
        outputfile = self.outputCtrl.GetValue()
        if not len(outputfile.split('.')) >= 2:
            outputfile = datafile + '.xlsx'
            self.outputCtrl.SetValue(outputfile)
            
        outputfile = searchObj.run_search(datafile,
                                          outputfile,
                                          self.fastaCtrl.GetValue().split('; '))
        
        self.output = outputfile
        self.did_run = True
        
        self.Close()
        
        
            

def run_GUI_from_app(parent, spectrum, pepmass):
    from multiplierz.mgf import write_mgf
    from multiplierz.mzReport import reader

    tempfile = 'tandem.temp.mgf'
    write_mgf([{'spectrum':spectrum,
                'pepmass':pepmass,
                'title':'test_spectrum',
                'charge':2}],
              tempfile)
    
    frame = XTandemSearch(parent, tempfile)
    frame.ShowModal()
    if frame.did_run == True:
        outputfile = frame.output
        return list(reader(outputfile)), None
    else:
        return None, None
        
    
        
        
    
if __name__ == '__main__':
    foo = wx.App(0)
    bar = XTandemSearch(None, '')
    bar.Show()
    foo.MainLoop()