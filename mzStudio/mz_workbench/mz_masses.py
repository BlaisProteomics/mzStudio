from collections import defaultdict
import re 
import sys
import os

global FILES_DIR

FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')

# dict_names = [FILES_DIR + r"\new_res_list.txt", FILES_DIR + r"\new_NTermMod.txt", FILES_DIR + r"\new_CTermMod.txt"]
dict_names = [os.path.join(FILES_DIR, filename) for filename in
              ['new_res_list.txt', 'new_NTermMod.txt', 'new_CTermMod.txt']]

def read_dict_from_file(filename):
    '''
    Version 0.1
    Reads appropriately formatted text file and returns data as a dictionary.
    
    new_res_list
    D|Aspartic Acid|C:4, H:5, O:3, N:1
    
    new_NtermMod
    TMT| |C:7, H:21, O:2, N:2, C13:5
    
    '''
    file_r = open(filename, 'r')
    data = file_r.readlines()
    file_r.close()    
    new_dict = defaultdict(dict)
    for member in data:
        sub_data = member.split('|')
        residue_name = sub_data[0].strip()
        residue_data_list = sub_data[2].split(',')
        for element in residue_data_list:
            atom = element.split(":")[0].strip()
            number = int(element.split(":")[1].strip())
            new_dict[residue_name][atom]=number
    return new_dict   

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
    mfile = open(os.path.join(FILES_DIR, r'mzBPTk_Mass_Definitions.txt'), 'r')
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

    # Hacky.
    mass_dict[True] = mass_dict['mi']
    mass_dict[False] = mass_dict['av']

    return mass_dict

def read_translations():
    '''
    Version 0.1
    This translates Mascot N-term, lys modifications to pep calc style names
    
    '''
    file_r = open(os.path.join(FILES_DIR, r'Translations.txt'), 'r')
    data = file_r.readlines()
    Ntranslate = {}
    Ctranslate = {}
    NvTranslate = {}
    for member in data:
        data_list = member.split("|")
        if data_list[0].find("(N-term)") > -1:
            Ntranslate[data_list[0]]=data_list[1]
        elif data_list[0].find("(C-term") > -1:
            Ctranslate[data_list[0]]=data_list[1]
        elif data_list[0].find("N-term:") > -1:
            NvTranslate[data_list[0]]=data_list[1]
    return Ntranslate, Ctranslate, NvTranslate
            

def calc_pep_mass_from_residues(sequence, cg = 1, varmod = '', fixedmod = '', Nterm='', Cterm='', round_flag=False, keepLabels=True, ret_pros = False, ions='b/y', calcType='mi', switch_labels={}, search_multi_mods=False):
    '''
    
    Version 0.2 (2017-06-06)
    Added compatibility to add mass to aa's in brackets i.e. PEP[43.01]TIDE
    
    Version 0.1
    Returns mz, b_series, y_series
    
    '''
    
    currentDict = None
    
    resadd = re.compile('\[([0-9]+.[0-9]+)\]([A-Z])')
    
    if calcType=='mi':
        currentDict=mass_dict['mi']
    if calcType=='av':
        currentDict=mass_dict['av']    
    
    if cg > -1:
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
            cmod = calc_mass(Cterm_dict[Cterm], calcType)
            y_base = cmod
            y_base += (currentDict['H+'] + currentDict['H'])
        else:
            y_base = currentDict['H3O+']
        b_series = []
        y_series = []
        pros = []
        if Nterm:
            nmod = calc_mass(Nterm_dict[Nterm], calcType) - currentDict['H'] + currentDict['proton']
            b_base = nmod
        else:
            b_base = currentDict['proton']
        if ions=='c/z':
            b_base += currentDict['NH3+']
            y_base -= (currentDict['N'] + (2 * currentDict['H']))
        for i in range(0, len(pep)):
            
            current_b_res = pep[i]
            
            add_b_mass = 0
            match_add_mass = resadd.match(current_b_res)
            if match_add_mass:
                add_b_mass = float(match_add_mass.groups()[0])
                current_b_res = match_add_mass.groups()[1]
            
            current_y_res = pep[len(pep)-1-i]
            
            add_y_mass = 0
            match_add_mass = resadd.match(current_y_res)
            if match_add_mass:
                add_y_mass = float(match_add_mass.groups()[0])
                current_y_res = match_add_mass.groups()[1]            
            
            current_b_mass = calc_mass(res_dict[current_b_res], calcType) + add_b_mass
            b_base += current_b_mass
            b_series.append(b_base)
            current_y_mass = calc_mass(res_dict[current_y_res], calcType) + add_y_mass
            y_base += current_y_mass
            y_series.append(y_base)
            if current_y_res == "P":
                pros.append(y_base)
        if Cterm:
            b_series[len(pep)-1] += cmod
        else:
            b_series[len(pep)-1] += currentDict['water']
        if Nterm:
            y_series[len(pep)-1] += nmod - currentDict['proton']

        if ions=='c/z':
            b_series[len(pep)-1] -= currentDict['NH3+']
            y_series[len(pep)-1] += (currentDict['N'] + (2 * currentDict['H']))

        mz = y_series[len(pep)-1]
        if cg == 0:
            b_series = []
            y_series = []
            mz = mz - currentDict['proton']
        if cg > 0:
            mz = (mz + ((cg - 1)* currentDict['proton']))/ float(cg)
        if cg > 1:
            for i in range(0, len(pep)):
                b_series[i] = (b_series[i] + ((cg - 1)* currentDict['proton']))/ float(cg)
                y_series[i] = (y_series[i] + ((cg - 1)* currentDict['proton']))/ float(cg)
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
        print "Charge should be =>0"
        raise ValueError

def calc_mass(CHNOPS_data, massType='mi'):
    '''
    Version 0.1
    Give this routine a dictionary of atom:number of this atom and mass will be returned.
    
    Example: p = {'H':3, 'P':1, 'O':4}
    
    returns 97.976897000000008
    
    '''
    currentDict = None
    if massType == 'mi':
        currentDict=mass_dict['mi']
    if massType == 'av':
        currentDict=mass_dict['av']    
    mass = 0
    for key in CHNOPS_data.keys():
        mass += currentDict[key]*CHNOPS_data[key]
    return mass

def read_translation_dicts():
    '''
    Version 0.1
    Returns fixed_mod_dict and var_mod_dict
    
    Fixed mod dict: {'Carbamidomethyl (C)':['C', 'caC'], 'HGly-HGly (K)':['K', 'cgK'],
    
    Var mod dict: {'S|Fucosylation':'fucS', 'S|Fringe':'gfS',
    
    Purpose:  Allow translation of residues given in Mascot notation to tokens for calculating mass
    variable~S|Fucosylation:fucS
    
    '''

    file_r = open(os.path.join(FILES_DIR, r'ModDicts.txt'), 'r')
    data = file_r.readlines()
    file_r.close()
    
    fixed_mod_dict = {}
    var_mod_dict = {}
    
    for member in data:
        if member.startswith('fixed'):
            t = member.split('~')[1]
            u = t.split(':')
            v = u[1]
            contents = [x.strip() for x in v.split(',')]
            fixed_mod_dict[u[0].strip()]=contents
        if member.startswith('variable'):
            t = member.split('~')[1].split(":")
            var_mod_dict[t[0].strip()]=t[1].strip()
    return fixed_mod_dict, var_mod_dict
        
def merge_multi_mods(varmod):
    '''
    
    Version 0.1
    The purpose of this function is to combine mutliple modifications of the same residue into a single, multi-mod definition.
    Input is "varmod" a Mascot style variable modification definition.
    >>> merge_multi_mods('R14: Label:13C(6)15N(4); R14: Methyl')
    >>> 'R14: Label:13C(6)15N(4), Methyl'
    
    '''
    modlist = defaultdict(list)
    pattern = re.compile('([A-Z])([0-9]+?)[:].([\w:() -]+)')
    if varmod:
        varmodlist = varmod.split(';')
        #print varmodlist
        for mod in varmodlist:
            mod = mod.strip()
            #print mod
            if not mod.startswith("No"):
                pa = pattern.match(mod)
                if pa:
                    modlist[int(pa.groups()[1]) - 1].append(mod)
    returnmod = ''
    modres = [x for x in modlist.keys()]
    modres.sort()
    for res in modres:
        current = modlist[res]
        if len(current) == 1:
            if returnmod:
                returnmod += '; '
            returnmod += modlist[res][0]
        else: # found multimod
            multimod = ''
            for member in current:
                if not multimod:
                    multimod += member
                else:
                    multimod += '-'
                    pa = pattern.match(mod)
                    multimod += pa.groups()[2]
            if returnmod:
                returnmod += '; '
            returnmod += multimod
    return returnmod

def read_fixed_translations():
    '''
    
    Version 0.1
    Allows conversion of Mascot style fixded modifications to PepCalc style tokens.
    
    '''
    fixed_mod_dict = {}
    file_r = open(os.path.join(FILES_DIR, r'Fixed_translations.txt'))
    #Carbamidomethyl (C):C, caC
    #{'Carbamidomethyl (C)':['C', 'caC']
    data = file_r.readlines()
    file_r.close()
    for line in data:
        mod = line.split(':')[0].strip()
        a = line.split(':')[1]
        trans = [x.strip() for x in a.split(',')]
        fixed_mod_dict[mod]=trans
    return fixed_mod_dict
    
def read_variable_translations():
    '''
        
    Version 0.1
    Allows conversion of Mascot style variable modifications to PepCalc style tokens.
    
    '''    
    var_mod_dict = {}
    file_r = open(os.path.join(FILES_DIR, r'Variable_translations.txt'))
    #C|Pip:pipC
    #'C|Pip':'pipC'
    data = file_r.readlines()
    file_r.close()  
    for line in data:
        trans = line.split(':')
        var_mod_dict[trans[0].strip()]=trans[1].strip()
    return var_mod_dict

global var_mod_dict
var_mod_dict = read_variable_translations()

global fixed_mod_dict
fixed_mod_dict = read_fixed_translations()

def create_peptide_container(seq, varmod, fixedmod, keepLabels=True, switch_labels={}, search_multi_mods=False):
    '''
    VERSION: 0.6 (2017-06-06)
    Added compatibility with COMET, Discoverer, and X!Tandem style varmods
    
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
    pa = re.compile('([\[\].a-z0-9\-\,]*[A-Z]+?)')
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
    
    mascot = re.compile('([A-Z])([0-9]+?)[:] ([A-Za-z]+)')
    comet_tandem = re.compile('([A-Z])([0-9]+?)[:] ([0-9]+.[0-9]+)')
    discoverer = re.compile('([A-Z])([0-9]+?)\(([A-Za-z]+)\)')
    
    #R14: Label:13C(6)15N(4); R14: Methyl
    
    #-------------------------------
    # Translating Varmods
    # COMET: M2: 16.0; M9: 16.0
    # Discoverer: M2(Oxidation); M5(Oxidation)
    # X!Tandem: C5: 57.02100; M4: 16.0032
    # Mascot: S5: Phospho; M3: Oxidation
    
    if varmod:
        if search_multi_mods:
            varmod = merge_multi_mods(varmod)
        varmodlist = varmod.split(';')
        #print varmodlist
        for mod in varmodlist:
            mod = mod.strip()
            
            pa = mascot.match(mod)
            if pa:
                peptide[int(pa.groups()[1]) - 1] = var_mod_dict[pa.groups()[0] + '|' + pa.groups()[2]]
                
            pa = discoverer.match(mod)
            if pa:
                peptide[int(pa.groups()[1]) - 1] = var_mod_dict[pa.groups()[0] + '|' + pa.groups()[2]] 
                
            pa = comet_tandem.match(mod)
            if pa:
                peptide[int(pa.groups()[1]) - 1] = '[' + pa.groups()[2] + ']' + peptide[int(pa.groups()[1]) - 1]
            
                
    return peptide

### Read in base information
#---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------
res_dict, Nterm_dict, Cterm_dict = [read_dict_from_file(x) for x in dict_names]
mass_dict = read_mass_def()
Ntranslate, Ctranslate, NvTranslate = read_translations()
fixed_mod_dict, var_mod_dict = read_translation_dicts()
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#**************************************************Tesing
#print mass_dict
#print fixed_mod_dict
#print var_mod_dict

#mz, b_series, y_series = calc_pep_mass_from_residues('DRVYIHPFHL', calcType='mi', cg=0)
#print mz
#print b_series
#print y_series

#cytc = {'C':560, 'H':876, 'N':148, 'O':156, 'S':4, 'Fe':1}

#mass = calc_mass(cytc, 'av')
#print mass
