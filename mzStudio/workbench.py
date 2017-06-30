import os








def read_mass_def():
    '''
            
    Version 0.2
    Mass Dict = dictionary of dictionaries, ['mi'] or ['av'] then element, atom, or ion to mass
    i.e. ['mi]['H']: 1.007825, ['mi']['O']: 15.994915000000001
    Monoisotopic and average
    
    '''        
    mass_dict = {}
    av = {}
    mi = {}
    def_file = os.path.join(os.path.dirname(__file__), 'mzBPTk_Mass_Definitions.txt')
    #mfile = open(FILES_DIR + r'\mzBPTk_Mass_Definitions.txt', 'r')
    mfile = open(def_file, 'r')
    definitions = mfile.readlines()
    mfile.close()

    for i in range(2, len(definitions), 4):
        mi[definitions[i].strip()] = float(definitions[i+1].strip())
        av[definitions[i].strip()] = float(definitions[i+2].strip()) 
    mass_dict['mi'] = mi
    mass_dict['av'] = av
    mass_dict['mi']['proton'] = mass_dict['mi']['H'] - mass_dict['mi']['e-']
    mass_dict['av']['proton'] = mass_dict['av']['H'] - mass_dict['mi']['e-']
    #mass_dict['av']['proton'] = mass_dict['mi']['H'] - mass_dict['mi']['e-']
    mass_dict['mi']['H+'] = mass_dict['mi']['proton']
    mass_dict['av']['H+'] = mass_dict['av']['proton']
    #mass_dict['av']['H+'] = mass_dict['mi']['proton']
    mass_dict['mi']['water'] = 2 * mass_dict['mi']['H'] + mass_dict['mi']['O']
    mass_dict['av']['water'] = 2 * mass_dict['av']['H'] + mass_dict['av']['O']
    #mass_dict['av']['water'] = mass_dict['mi']['water']
    mass_dict['mi']['hydronium'] = 2 * mass_dict['mi']['H'] + mass_dict['mi']['O'] + mass_dict['mi']['proton']
    mass_dict['av']['hydronium'] = 2 * mass_dict['av']['H'] + mass_dict['av']['O'] + mass_dict['av']['proton']
    #mass_dict['av']['hydronium'] = mass_dict['mi']['hydronium']
    mass_dict['mi']['H3O+'] = 2 * mass_dict['mi']['H'] + mass_dict['mi']['O'] + mass_dict['mi']['proton']
    mass_dict['mi']['NH3+'] = 2 * mass_dict['mi']['H'] + mass_dict['mi']['N'] + mass_dict['mi']['proton']
    mass_dict['av']['H3O+'] = mass_dict['av']['hydronium']
    #mass_dict['av']['H3O+'] = mass_dict['mi']['H3O+']
    mass_dict['mi']['cneutron']=mass_dict['mi']['C13']-mass_dict['mi']['C']
    mass_dict['mi']['nneutron']=mass_dict['mi']['N15']-mass_dict['mi']['N']

    return mass_dict



# From mz_core
def create_dicts(m, start=0, stop=99999, check_corrupted_scans= False):
    """ 
    Version 0.2; 2014-04-15
    Given an mzAPI object (m), returns several dictionaries useful for exploration of the data.
    Scan dict[scan_number] = MS1 or MS2;
    rt dict [scan_number] = retention time
    filter dict [scan_number] = filter
    rt2scan [retention time] = scan 
    Thermo (raw: Orbitrap XL, Velos, Fusion) and ABSciex (wiff: Elite, 5600, QTRAP) have been tested
    """
    print "mz_core: Building scan dictionaries..."
    B = m.scan_info(start, stop, start_mz=0, stop_mz=99999)
    C = m.filters() # WIFF FORMAT: (0.019966666666666667, u'Precursor + p NSI Full ms [410-1000]')
    scan_dict = {}
    rt_dict = {}
    filter_dict = {}
    if m.file_type == 'raw':
        for entry in B:
            scan_dict[entry[2]] = entry[3]
            rt_dict[entry[2]] = entry[0]
        rt2scan = dict((v,k) for k, v in rt_dict.iteritems())

        for entry in C:
            scan = rt2scan[entry[0]]
            filter_dict[scan] = entry[1]
    elif m.file_type == 'wiff':
        
        for entry in B:
            scan_dict[(entry[2][2],entry[2][1])] = entry[3]
            rt_dict[(entry[2][2],entry[2][1])] = (entry[0], entry[2][1])
        rt2scan = dict((v,k) for k, v in rt_dict.iteritems())
              
        for entry in C:
            scan = rt2scan[entry[0]]
            filter_dict[scan] = entry[1]
            
    return scan_dict, rt_dict, filter_dict, rt2scan






# From mz_core
def get_fragment_neutral_losses(sequence, b_ions, y_ions, varmod, cg):
    '''
    Neutral losses are derived from varmods like phosphorylation
    '''
    NL_residues = {'gfS':'Fringe', 'gfT':'Fringe' ,'pS':'Phospho', 'pT':'Phospho', 'fucS':'Fucose', 'fucT':'Fucose', 'galS':'Hexose', 'galT':'Hexose', 'gS':'HexNAc', 'gT':'HexNAc', 'xxgS':'XylXylGal', 'xxgT':'XylXylGal', 'smlC':'SML'}
    NL_dict = {'Fringe':{'C':14, 'H':23,'N':1,'O':9}, 'Phospho':{'H':3, 'P':1, 'O':4}, 'Fucose':{'C':6, 'H':10, 'O':4}, 'Hexose':{'C':6, 'H':10, 'O':5}, 'HexNAc':{'C':8, 'H':13, 'O':5, 'N':1}, 'XylXylGal':{'C':16, 'H':26, 'O':13}, 'SML':{'C':10, 'H':15, 'N':5, 'O':11, 'P':2}}
    pep = create_peptide_container(sequence, varmod, '')
    NL_bank = [] # This keeps a running total of losses to occur from the ion {97.98:'Phospho'}
    NL_masses = {}
    NL_ions = {} # This is the list that gets returned {344.2:'y4-Phospho'}
    if cg > 0:
        temp = pep
        b_ions = b_ions[:-1]
        pep = pep[:-1]
    for i, (residue, b_ion) in enumerate(zip(pep, b_ions)):
        if residue in NL_residues.keys(): #Does the current residue lead to a neutral loss?
            NL_bank.append(calc_mass(NL_dict[NL_residues[residue]])) #If so, convert residue to type (Phospho); Convert Type to formula; calc mass & append
            NL_masses[calc_mass(NL_dict[NL_residues[residue]])] = NL_residues[residue] #Add mass to NL_Masses {98:'Phospho'}
        current_mz = b_ion
        current_tag = ''
        for nloss in NL_bank:
            NL_ions[current_mz-(float(nloss)/float(cg))]= 'b' + str(i+1) + '-' + NL_masses[nloss][0] + current_tag
            current_mz -= float(nloss)/float(cg)
            current_tag += '-' + NL_masses[nloss][0]
    if cg > 0:
        pep = temp
        pep.reverse()
        y_ions = y_ions[:-1]    
        pep=pep[:-1]
    NL_bank = []    
    #pep.reverse()
    for i, (residue, y_ion) in enumerate(zip(pep, y_ions)):
        if residue in NL_residues.keys(): #Does the current residue lead to a neutral loss?
            NL_bank.append(calc_mass(NL_dict[NL_residues[residue]])) #If so, convert residue to type (Phospho); Convert Type to formula; calc mass & append
            NL_masses[calc_mass(NL_dict[NL_residues[residue]])] = NL_residues[residue] #Add mass to NL_Masses {98:'Phospho'}
        current_mz = y_ion
        current_tag = ''
        for nloss in NL_bank:
            NL_ions[current_mz-(float(nloss)/float(cg))]= 'y' + str(i+1) + '-' + NL_masses[nloss][0] + current_tag
            current_mz -= float(nloss)/float(cg)
            current_tag += '-' + NL_masses[nloss][0]    
    return NL_ions


# From mz_core
def get_precursor_neutral_losses(mz, cg, varmod):
    NL_bank = [] # This keeps a running total of losses to occur from the ion {97.98:'Phospho'}
    NL_dict = {'Fringe':{'C':14, 'H':23,'N':1,'O':9}, 'Phospho':{'H':3, 'P':1, 'O':4}, 'SML':{'C':10, 'H':15, 'N':5, 'O':11, 'P':2},'Fucosylation':{'C':6, 'H':10, 'O':4}, 'Hex':{'C':6, 'H':10, 'O':5}, 'HexNAc':{'C':8, 'H':13, 'O':5, 'N':1}, 'XylXylGal':{'C':16, 'H':26, 'O':13}}
    NL_ions = {} #This is the list that gets returned {544.2:'[M+2H]2+ dP'}
    NL_masses={}
    mods = varmod.split(';')
    for mod in mods:
        for key in NL_dict.keys():
            if mod.find(key) > -1:
                NL_bank.append(calc_mass(NL_dict[key]))
                NL_masses[calc_mass(NL_dict[key])]=key
    current_mz = mz
    for nloss in NL_bank:
        NL_ions[current_mz-((float(nloss)/float(cg)))]='M-' + NL_masses[nloss][0] + ' ' + str(cg) + '+'
        current_mz -= float(nloss)/float(cg)
    return NL_ionsx



# From mz_core
def create_peptide_container(seq, varmod, fixedmod, keepLabels=True, switch_labels={}, search_multi_mods=False):
    '''
    VERSION: 0.5 (2014-05-29)
    The purpose of this function is to convert a string that represents a potentially modified peptide to a list of "tokens" that represent particular amino acids.
    The token ends at a capital letter.  Any number of lowercase letters may be used in the token name, but the total token length should be kept as short as possible.
    
    **UPDATE: 2014-05-28 Tokens may now include numbers, commas, and dashes to support clear nomenclature for certain workflows (i.e. SILAC)
    
    For example, "AAAPEPTIDEpYK" will convert to ['A', 'A','A', 'P','E', 'P','T', 'I','D', 'E','pY', 'K']
    
    Switch labels was created for SILAC.  The purpose is to switch heavy labels for medium ones, or vice versa.
    For example, if your peptide has K16: Label:13C(6)15N(2), and you want to calculate the medium version, set: 
    switch_labels={'K|Label:13C(6)15N(2)':'deutK', 'R|Label:13C(6)15N(4)']='silacR'}
    or vice versa:
    switch_labels={'K|Label:2H(4)':'seK', 'R|Label:13C(6)']='sR'}
    
    Keep labels was created for SILAC.  If False, any SILAC label is converted to a light 'R' or 'K'.
    
    
    '''
    pa = re.compile('([a-z0-9\-\,]*[A-Z]+?)')
    if fixedmod == None:
        fixedmod = ''    
    if fixedmod.find(",") > -1:
        temp = fixedmod
        fixedmod = []
        fixedmods = temp.split(',')
        for mod in fixedmods:
            fixedmod.append(mod.strip())
    else:
        if not fixedmod:
            fixedmod = []
        else:
            fixedmod = [fixedmod]
    for i, member in enumerate(fixedmod):
        if member.find('N-term') > -1:  # N-terminal modifications are dealt with in the mass calculator
            del fixedmod[i]
    
    if keepLabels:
        var_mod_dict['K|Label:2H(4)']='deutK'
        var_mod_dict['K|Label:13C(6)']='sK'
        var_mod_dict['K|Label:13C(6)15N(2)']='seK'
        var_mod_dict['R|Label:13C(6)']='silacR'
        var_mod_dict['R|Label:13C(6)15N(4)']='sR'
        var_mod_dict['R|Label:13C(6)15N(4)-Methyl'] = 'smR'
        var_mod_dict['R|Methyl-Label:13C(6)15N(4)'] = 'smR'
        var_mod_dict['R|Label:13C(6)15N(4)-Dimethyl']='sdR'
        var_mod_dict['R|Dimethyl-Label:13C(6)15N(4)'] = 'sdR'
        var_mod_dict['K|Label:2H(4)-Propionyl'] = 'pdK'
        var_mod_dict['K|Propionyl-Label:2H(4)'] = 'pdK'
        var_mod_dict['K|Label:13C(6)15N(2)-Propionyl'] = 'pseK'
        var_mod_dict['K|Propionyl-Label:13C(6)15N(2)'] = 'pseK'
    else:
        var_mod_dict['K|Label:2H(4)']='K'
        var_mod_dict['K|Label:13C(6)']='K'
        var_mod_dict['K|Label:13C(6)15N(2)']='K'
        var_mod_dict['R|Label:13C(6)']='R'
        var_mod_dict['R|Label:13C(6)15N(4)']='R'
        var_mod_dict['R|Label:13C(6)15N(4)-Methyl'] = 'mmR'
        var_mod_dict['R|Methyl-Label:13C(6)15N(4)'] = 'mmR'
        var_mod_dict['R|Label:13C(6)15N(4)-Dimethyl']='dmR'
        var_mod_dict['R|Dimethyl-Label:13C(6)15N(4)'] = 'dmR'
        var_mod_dict['K|Label:2H(4)-Propionyl'] = 'pK'
        var_mod_dict['K|Propionyl-Label:2H(4)'] = 'pK'
        var_mod_dict['K|Label:13C(6)15N(2)-Propionyl'] = 'pK'
        var_mod_dict['K|Propionyl-Label:13C(6)15N(2)'] = 'pseK'
    if switch_labels:
        for key in switch_labels.keys():
            var_mod_dict[key] = switch_labels[key]
    peptide = []
    # Breakdown peptide
    #for member in seq:
    #    peptide.append(member)
    peptide = pa.findall(seq)
    # Add fixed modifications
    #print fixedmod
    if fixedmod:
        for mod in fixedmod:
            translation = fixed_mod_dict[mod]
            for i, member in enumerate(seq):
                if member == translation[0]:
                    peptide[i] = translation[1]
    pattern = re.compile('([A-Z])([0-9]+?)[:].([\w:() -]+)')
    #R14: Label:13C(6)15N(4); R14: Methyl
    if varmod:
        if search_multi_mods:
            varmod = merge_multi_mods(varmod)
        varmodlist = varmod.split(';')
        #print varmodlist
        for mod in varmodlist:
            mod = mod.strip()
            #print mod
            if not mod.startswith("No"):
                pa = pattern.match(mod)
                if pa:
                    peptide[int(pa.groups()[1]) - 1] = var_mod_dict[pa.groups()[0] + '|' + pa.groups()[2]]
                else:
                    if mod.find("N-term") == -1:
                        pilot_pattern = re.compile('([a-zA-Z0-9]+?)\(([A-Z])\)\@([0-9]+)')
                        pa = pilot_pattern.match(mod)
                        if pa:
                            peptide[int(pa.groups()[2]) - 1] = var_mod_dict[pa.groups()[1] + '|' + pa.groups()[0]]
    return peptide


# From mz_core
def pull_mods_from_mascot_header(filename):
    '''
    
    Version 0.1
    Reads Mascot_Header sheet from multiplierz report.  Builds and returns a dictionary of parameters.
    This is a bit slow.  Consider making into a csv file or using xlrd for faster access.
    
    '''
    print "Pulling header..."
    rdr = mzR.reader(filename, sheet_name = "Mascot_Header")
    header = {}
    for row in rdr:
        header[row['Header']] = row['--------------------------------------------------']
    print "Pulled!"
    return header
    rdr.close()
    
    
# From mz_core
def find_MS1(scan_dict, scan, direction):
    '''
    
    Version 0.1
    Given a scan_dict (from funciton create_dicts) and a scan, walks forward or back until an MS1 scan is found.
    If direction is "Forward", increments by 1, anything else, -1.
    
    '''
    found = 0
    while not found:
        if direction == "Forward":
            scan += 1
        else:
            scan -= 1
        if scan_dict[scan] == "MS1":
            found = scan
    return found

def find_filter(filter_dict, scan, direction, msfilter="MS1"):
    '''
        
    Version 0.1
    Given a filter_dict (from funciton create_dicts) and a scan, walks forward or back until filter matches msfilter argument.
    If direction is "Forward", increments by 1, anything else, -1.
    
    '''    
    found = 0
    while not found:
        if direction == "Forward":
            scan += 1
        else:
            scan -= 1
        if filter_dict[scan] == msfilter:
            found = scan
    return found

def find_MS1(scan_dict, scan, direction):
    '''
    
    Version 0.1
    Given a scan_dict (from funciton create_dicts) and a scan, walks forward or back until an MS1 scan is found.
    If direction is "Forward", increments by 1, anything else, -1.
    
    '''
    found = 0
    while not found:
        if direction == "Forward":
            scan += 1
        else:
            scan -= 1
        if scan_dict[scan] == "MS1":
            found = scan
    return found



def calc_pep_mass_from_residues(sequence, cg = 1, varmod = '', fixedmod = '', Nterm='', Cterm='', round_flag=False, keepLabels=True, ret_pros = False, ions='b/y', switch_labels={}, search_multi_mods=False):
    '''
    
    Returns mz, b_series, y_series
    
    '''
    if cg >0:
        Ntranslate = {'iTRAQ4plex (N-term)': 'iTRAQ',
                      'TMT6plex (N-term)': 'TMT',
                      'Propionyl (N-term)': 'Propionyl',
                      'iTRAQ8plex (N-term)': 'iTRAQ8plex',
                      'iTRAQ8plex@N-term': 'iTRAQ8plex',
                      'HGly-HGly (N-term)':'HCGlyHCGly',
                      'HCGly-HCGly (N-term)':'HCGlyHCGly',
                      'HNGly-HNGly (N-term)':'HNGlyHNGly',
                      'LbA-LbA (N-term)':'LbALbA',
                      'LbA-HbA (N-term)':'LbAHbA',
                      'HbA-HbA (N-term)':'HbAHbA',
                      'HCGly-HCGly-HCGly-HCGly (N-term)':'HCGlyHCGlyHCGlyHCGly',
                      'HNGly-HNGly-HNGly-HNGly (N-term)':'HNGlyHNGlyHNGlyHNGly'}
        NvTranslate = {'N-term: Acetyl': 'Acetyl',
                       'N-term: Propionyl': 'Propionyl',
                       'iTRAQ8plex@N-term': 'iTRAQ8plex',
                       'N-term: HNGly-HNGly': 'HNGlyHNGly',
                       'N-term: HCGly-HCGly': 'HCGlyHCGly',
                       'N-term: HbA-HbA': 'HbAHbA',
                       'N-term: LbA-HbA': 'LbAHbA',
                       'N-term: LbA-LbA': 'LbALbA',
                       'N-term: HNGly-HNGly-HNGly-HNGly': 'HNGlyHNGlyHNGlyHNGly',
                       'N-term: HCGly-HCGly-HCGly-HCGly': 'HCGlyHCGlyHCGlyHCGly'}
        Ctranslate = {}
        ### Translations from fixedmod and varmod
        if fixedmod:
            fm = fixedmod.split(',')
            for fmod in fm:
                fmod = fmod.strip()
                if fmod.find('N-term') > -1:
                    Nterm = Ntranslate[fmod]
                if fmod.find('C-term') > -1:
                    Cterm = Ctranslate[fmod]

        pep = create_peptide_container(sequence, varmod, fixedmod, keepLabels, switch_labels, search_multi_mods=search_multi_mods)

        if varmod:
            vm = varmod.split(';')
            for vmod in vm:
                vmod = vmod.strip()
                if vmod.find('N-term') > -1:
                    Nterm = NvTranslate[vmod]
                

        if Cterm:
            cmod = calc_mass(Cterm_dict[Cterm])
            y_base = cmod
            y_base += (mass_dict['H3O+']- mass_dict['H'])
        else:
            y_base = mass_dict['H3O+']
        b_series = []
        y_series = []
        pros = []
        if Nterm:
            nmod = calc_mass(Nterm_dict[Nterm]) - mass_dict['H'] + mass_dict['proton']
            b_base = nmod
        else:
            b_base = mass_dict['proton']
        if ions=='c/z':
            b_base += mass_dict['NH3+']
            y_base -= (mass_dict['N'] + (2 * mass_dict['H']))
        for i in range(0, len(pep)):
            current_b_res = pep[i]
            current_y_res = pep[len(pep)-1-i]
            current_b_mass = calc_mass(res_dict[current_b_res])
            b_base += current_b_mass
            b_series.append(b_base)
            current_y_mass = calc_mass(res_dict[current_y_res])
            y_base += current_y_mass
            y_series.append(y_base)
            if current_y_res == "P":
                pros.append(y_base)
        if Cterm:
            b_series[len(pep)-1] += (cmod + mass_dict['water']- mass_dict['H'])
        else:
            b_series[len(pep)-1] += mass_dict['water']
        if Nterm:
            y_series[len(pep)-1] += nmod - mass_dict['proton']

        if ions=='c/z':
            b_series[len(pep)-1] -= mass_dict['NH3+']
            y_series[len(pep)-1] += (mass_dict['N'] + (2 * mass_dict['H']))

        mz = y_series[len(pep)-1]

        mz = (mz + ((cg - 1)* mass_dict['proton']))/ float(cg)
        if cg > 1:
            for i in range(0, len(pep)):
                b_series[i] = (b_series[i] + ((cg - 1)* mass_dict['proton']))/ float(cg)
                y_series[i] = (y_series[i] + ((cg - 1)* mass_dict['proton']))/ float(cg)
        if round_flag:
            for i, member in enumerate(b_series):
                #b_series[i] = str(round(b_series[i],2))[:(str(round(b_series[i],2)).find('.')+2)]
                b_series[i] = round(b_series[i],1)
                #y_series[i] = str(round(y_series[i],2))[:(str(round(y_series[i],2)).find('.')+2)]
                y_series[i] = round(y_series[i],1)
        if not ret_pros:
            return mz, b_series, y_series
        else:
            return pros
    else:
        print "Charge should be >0"
        raise ValueError