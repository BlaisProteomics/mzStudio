__author__ = 'Scott'
__lastRevision__ = '2016-12-24'
__version__ = "0.3.2-mzStudio"

import pylab
import sys
import os

global FILES_DIR
FILES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')

import sqlite3 as sql
import dcv
import os, math
import re
import numpy
import csv
import wx

import multiplierz.mass_biochem as mzF
import multiplierz.mzReport as mzR
import multiplierz.mzAPI as mzAPI
import multiplierz.mzSearch.mascot as mascot
from collections import defaultdict

Ntranslate = {'iTRAQ4plex (N-term)': 'iTRAQ',
                      'TMT6plex (N-term)': 'TMT',
                      'TMT (N-term)': 'cTMT',
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
                      'HNGly-HNGly-HNGly-HNGly (N-term)':'HNGlyHNGlyHNGlyHNGly',
                      'Phenylisocyanate (N-term)':'Phenylisocyanate'}
NvTranslate = {'N-term: Acetyl': 'Acetyl',
               'N-term: Propionyl': 'Propionyl',
               'iTRAQ8plex@N-term': 'iTRAQ8plex',
               'N-term: HNGly-HNGly': 'HNGlyHNGly',
               'N-term: HCGly-HCGly': 'HCGlyHCGly',
               'N-term: HbA-HbA': 'HbAHbA',
               'N-term: LbA-HbA': 'LbAHbA',
               'N-term: LbA-LbA': 'LbALbA',
               'N-term: HNGly-HNGly-HNGly-HNGly': 'HNGlyHNGlyHNGlyHNGly',
               'N-term: HCGly-HCGly-HCGly-HCGly': 'HCGlyHCGlyHCGlyHCGly',
               'N-term: TMT': 'cTMT',
               'N-term: TMT6plex': 'TMT'}
Ctranslate = {}


def get_single_file(caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
    app = wx.PySimpleApp()
    dlg = wx.FileDialog(None, caption, pos = (2,2), wildcard = wx_wildcard) #defaultDir = default_dir, 
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetPath()
        dir = dlg.GetDirectory()
        print filename
        print dir
    dlg.Destroy()
    return filename, dir

def get_multiple_files(caption="Select multiplierz files...", wx_wildcard = "XLS files (*.xls)|*.xls", use_default_dir=False):
    '''
    
    Returns filenames, dir
    filenames is a list of base filenames.
    To access file use dir + '\\' + filename
    
    '''
    app = wx.PySimpleApp()
    if use_default_dir:
        dlg = wx.FileDialog(None, caption, pos = (2,2), style = wx.FD_MULTIPLE, wildcard = wx_wildcard) #defaultDir = default_dir, 
    else:
        dlg = wx.FileDialog(None, caption, pos = (2,2), style = wx.FD_MULTIPLE, wildcard = wx_wildcard)
    if dlg.ShowModal() == wx.ID_OK:
        filenames=dlg.GetFilenames()
        dir = dlg.GetDirectory()
    dlg.Destroy()
    return filenames, dir

def derive_elution_range(m, scan_dict, scan, mz, cg, tolerance, threshold):
    raise ValueError("Method Deprecated.  Use derive_elution_range_by_C12_C13")
    start = scan
    stop = scan
    last_scan = scan
    current_scan = scan
    go = True
    scan_array = [scan]
    print "Scanning elution range for ... " + str(mz) + " around scan " + str(scan) + '\n'
    while go:
        next_scan = find_MS1(scan_dict, current_scan, "Forward")
        deiso = get_MS(m, next_scan)
        found_mz, found = look_for_mz_cg(deiso, mz, cg, tolerance)
        if not found:
            stop = current_scan
            go = False
        else:
            scan_array.append(next_scan)
            current_scan = next_scan
    current_scan = scan
    go = True
    while go:
        next_scan = find_MS1(scan_dict, current_scan, "Reverse")
        deiso = get_MS(m, next_scan)
        found_mz, found = look_for_mz_cg(deiso, mz, cg, tolerance)
        if not found:
            start = current_scan
            go = False
        else:
            scan_array.append(next_scan)
            current_scan = next_scan
    scan_array.sort()
    return start, stop, scan_array

def derive_elution_range_by_C12_C13(m, scan_dict, scan, mz, cg, tolerance, threshold, searchAlgorithm=0, debug=False, ignore_error=False):
    '''
    version 0.2; 2014-02-15
    searchAlgorithm: 0 = look_for_mz_return_most_intense_in_window
    If debug True, prints mz and focus scan
    If ignore error will stop if scan not found in scan dict but returns result
    '''
    if searchAlgorithm == 0:
        search_algorithm = look_for_mz_return_most_intense_in_window
    start = scan
    stop = scan
    last_scan = scan
    found_mz, found, intensity = search_algorithm(m.cscan(scan), mz, tolerance)
    scan_array = [[scan, intensity]]
    isotope_step = float(mass_dict['mi']["H+"])/float(cg)
    #find = [mz, mz + isotope_step, mz + (2*isotope_step)]
    find = [mz + isotope_step, mz + (2*isotope_step), mz]
    if debug:
        print "Scanning elution range for ... " + str(mz) + " around scan " + str(scan) + '\n'
    task = ["Forward", "Reverse"]
    for subtask in task:
        current_scan = scan
        go = True
        while go:
            try:
                fa = [False, False, False]
                all_found = False
                next_scan = find_MS1(scan_dict, current_scan, subtask)
                scan_data = m.cscan(next_scan)
                for i, member in enumerate(find):
                    found_mz, found, intensity = search_algorithm(scan_data, member, tolerance)
                    fa[i] = found
                all_found = reduce(lambda x, y: x & y, fa)
                if not all_found:
                    stop = current_scan
                    go = False
                else:
                    scan_array.append([next_scan, intensity])
                    current_scan = next_scan
            except:
                if not ignore_error:
                    raise ValueError("Could not find scan in scan_dict!!  Check to see if went out of bounds.")
                else:
                    go = False
    scan_array.sort()
    return start, stop, scan_array

#---------------------------------------------------------------------------
#-----------------------------------------FUNCTIONS FOR SEARCHING MASS LISTS

def look_for_mz_cg(current_MS1, mz, cg, tolerance = 0.02):
    '''
    Version 0.1
    Given a "cscan" list, looks for matches of m/z, cg, tolerance.  Returns first matching value found during iteration.
    "cscan": [(mz, inten, noise, cg), (...)]
    returns found_mz, found
    '''
    found = False
    found_mz = None
    lo = mz - tolerance
    hi = mz + tolerance
    for member in current_MS1:
        if member[0] > lo and member[0] < hi and cg == member[3]:
            found = True
            found_mz = member[0]
            break
    return found_mz, found

def look_for_mz_return_intensity(current_MS1, mz, tolerance = 0.02, inten=0):
    '''
    Version 0.1
    Given a "scan" list, looks for matches of m/z, tolerance.  Returns first matching value found during iteration.
    If intensity specified, looks only at mz values with intensities greater than specified values.
    "scan": [(mz, inten), (...)]
    returns found_mz, found, intensity
    '''    
    found = False
    found_mz = None
    lo = mz - tolerance
    hi = mz + tolerance
    intensity = 0
    for member in current_MS1:
        if not inten:
            if member[0] > lo and member[0] < hi:
                found = True
                found_mz = member[0]
                intensity = member[1]
                break
        else:
            if member[0] > lo and member[0] < hi:
                if member[1] > inten:
                    found = True
                    found_mz = member[0]
                    intensity = member[1]
                    break
    return found_mz, found, intensity

def look_for_mz_return_most_intense_in_window(current_MS1, mz, tolerance = 0.005, inten=0):
    '''
    Version 0.1
    Given a "scan" list, looks for matches of m/z, tolerance.  
    If intensity specified, looks only at mz values with intensities greater than specified values.
    All entries in list passing these criteria are placed in a "found list".  The member with the greatest intensity
    member[1] is returned.
    "scan": [(mz, inten), (...)]
    returns found_mz, found (True or False), intensity
    '''      
    found = False
    found_mz = None
    lo = mz - tolerance
    hi = mz + tolerance
    intensity = 0
    found_array = []
    for member in current_MS1:
        if not inten:
            if member[0] > lo and member[0] < hi:
                found = True
                found_array.append(member)
                
        else:
            if member[0] > lo and member[0] < hi:
                if member[1] > inten:
                    found = True
                    found_array.append(member)
    if found_array:
        found_array.sort(key=lambda t:t[1],reverse=True)
        intensity = found_array[0][1]
        found_mz = found_array[0][0]
    return found_mz, found, intensity

def look_for_mz(current_MS1, mz, tolerance = 0.02, inten=0):
    '''
    Version 0.1
    RELATED FUNCTION: look_for_mz_return_intensity (same thing except also returns intensity for "found" mz)
    Given a "scan" list, looks for matches of m/z, tolerance.  Returns first matching value found during iteration.
    If intensity specified, looks only at mz values with intensities greater than specified values.
    "scan": [(mz, inten), (...)]
    returns found_mz, found
    '''        
    found = False
    found_mz = None
    lo = mz - tolerance
    hi = mz + tolerance
    for member in current_MS1:
        if not inten:
            if member[0] > lo and member[0] < hi:
                found = True
                found_mz = member[0]
                break
        else:
            if member[0] > lo and member[0] < hi:
                if member[1] > inten:
                    found = True
                    found_mz = member[0]
                    break
    return found_mz, found

def get_closest_intensity(ms1, pMZ, tolerance = 0.02):
    '''
    
    Version 0.1
    Author: James Webber
    
    Given a "cscan" list (argument ms1), looks for matches of m/z (pMZ), within tolerance.  Returns closest mz match (or 0).
    "cscan": [(mz, inten, noise, cg), (...)]
    
    The list comprehension filters for mz within specified tolerance, followed by min function using a key filtering by delta mz.
    
    '''    
    return min([(mz,s,n,z) for (mz,s,n,z) in ms1 if abs(mz-pMZ) <= tolerance] or [(pMZ,0,0.0,0.0)],key=lambda x: (abs(x[0]-pMZ)))

def get_intensity(ms1, pMZ, tolerance = 0.02):
    '''

    Version 0.1
    Author: James Webber
    
    Given a "cscan" list (argument ms1), looks for matches of m/z (pMZ), within tolerance.  Returns most intense (or 0).
    "cscan": [(mz, inten, noise, cg), (...)]
    
    The list comprehension filters for mz within specified tolerance, followed by max function using a key filtering by second element (intensity).
    
    '''
    return max([(mz,s,n,z) for (mz,s,n,z) in ms1 if abs(mz-pMZ) <= tolerance] or [(pMZ,0,0.0,0.0)],key=lambda x: (x[1],x[0]))

def get_short_intensity(ms1, pMZ, tolerance = 0.02):
    '''
    
    Version 0.1
    Author: James Webber
    
    RELATED TO: get_intensity (takes 4 element "cscan")
    
    Given a "scan" list (argument ms1), looks for matches of m/z (pMZ), within tolerance.  Returns most intense (or 0).
    "scan": [(mz, inten), (...)]
    
    The list comprehension filters for mz within specified tolerance, followed by max function using a key filtering by second element (intensity).
    
    '''    
    return max([(mz,s) for (mz,s) in ms1 if abs(mz-pMZ) <= tolerance] or [(pMZ,0)],key=lambda x: (x[1],x[0]))

def look_for_mass(mass_list, target, tolerance = 0.5):
    '''
    
    Version 0.1
    Given a mass_list [(mz, int), + ...], looks for mz values within tolerance
    RETURNS INTENSITY OF LAST PEAK PASSING TOLERANCE
    returns [True/False, intensity]
    
    '''
    found = [False, 0.0]
    lo = target - tolerance
    hi = target + tolerance
    for member in mass_list:
        if member[0] > lo and member[0] < hi:
            found = [True, member[1]]
    return found

#-----------------------------------------FUNCTIONS FOR SEARCHING MASS LISTS
#---------------------------------------------------------------------------

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
    print "mz_core: Building scan dictionaries...;---"
    B = m.scan_info()
    C = m.filters() # WIFF FORMAT: (0.019966666666666667, u'Precursor + p NSI Full ms [410-1000]')
    scan_dict = {}
    rt_dict = {}
    filter_dict = {}
    rt2scan = {}
    #if m.file_type == 'raw':
    for entry in B:
        scan_dict[entry[2]] = entry[3]
        rt_dict[entry[2]] = entry[0]
        rt2scan[entry[0]] = entry[2]
    #rt2scan = dict((v,k) for k, v in rt_dict.iteritems())

    for entry in C:
        scan = rt2scan[entry[0]]
        filter_dict[scan] = entry[1]
    #elif m.file_type == 'wiff':
        
        #for entry in B:
            #scan_dict[(entry[2][2],entry[2][1])] = entry[3]
            #rt_dict[(entry[2][2],entry[2][1])] = (entry[0], entry[2][1])
        #rt2scan = dict((v,k) for k, v in rt_dict.iteritems())
              
        #for entry in C:
            #scan = rt2scan[entry[0]]
            #filter_dict[scan] = entry[1]
            
    return scan_dict, rt_dict, filter_dict, rt2scan

def find_MS1(scan_dict, scan, direction):
    '''
    
    Version 0.1
    Given a scan_dict (from funciton create_dicts) and a scan, walks forward or back until an MS1 scan is found.
    If direction is "Forward", increments by 1, anything else, -1.
    
    '''
    top_scan = max(scan_dict.values())
    found = 0
    while not found:
        if direction == "Forward":
            scan += 1
        else:
            scan -= 1
        if scan_dict.get(scan, None) == "MS1":
            found = scan
        if scan <= 0:
            found = min(scan_dict.keys())
            break
        elif scan >= top_scan:
            found = top_scan
            break            
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

def get_MS(m, scan):
    '''
    
    Given mzAPI.mzFile and scan, gets cscan and returns deisotoped scan (dcv.deistope).
    Relies on charge state info.
    
    m=rawfile object (Thermo)
    scan = integer of scan number (FT-MS1)
    Returns deisotoped scan
    
    '''
    C=m.cscan(scan)
    D = []
    for line in C:
        if line[3] > 0:
            D.append(line)
    D.sort(key=lambda t:t[1],reverse=True)
    E = dcv.deisotope(D, 1, 99, 500)
    return E

def get_cal_mass(DataFile):
    print "Performing precalibration..."
    B=DataFile.scan_info(12,12.5,start_mz=0, stop_mz=99999)
    tolerance=0.05
    a=445.120025
    low = a-tolerance
    hi = a+tolerance
    cal = []
    for scan in B:
        if scan[3]=='MS1':
            C=DataFile.cscan(scan[2])
            for mass in C:
                if mass[0] > low and mass[0] < hi and mass[3] == 1.0:
                    cal.append(mass)
                if mass[0] > hi:
                    break
    print cal
    mass_int = 0
    int_sum = 0
    for mass in cal:
        mass_int += mass[0]*mass[1]
        int_sum += mass[1]
    try:
        cal_mass = float(mass_int)/float(int_sum)
    except:
        print "Could not find cal mass..."
        cal_mass = 445.120025
    print cal_mass

    delta = abs(a-cal_mass)
    if delta > 0.05:
        print "WARNING... CAL MASS NOT THERE OR OUTSIDE WINDOW!"
        cal_mass = a
        raise ValueError

    return cal_mass

def grab_cal_mass(C, lastcal, main_cal):
    tolerance=0.003
    a=main_cal
    low = a-tolerance
    hi = a+tolerance
    cal = 0
    calibration = "INTERNAL"
    for mass in C:
        if mass[0] > low and mass[0] < hi and mass[3] == 1.0:
            cal = mass[0]
        if mass[0] > hi:
            break
    if not cal:
        cal = lastcal
        calibration = "EXTERNAL"

    return cal, calibration


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

    return mass_dict

def read_new_mass_def():
    '''
    This is the same as read_mass_def in mz_masses (read_mass_def in this module is deprecated)    
    Version 0.2
    Mass Dict = dictionary of dictionaries, ['mi'] or ['av'] then element, atom, or ion to mass
    i.e. ['mi]['H']: 1.007825, ['mi']['O']: 15.994915000000001
    Monoisotopic and average
    
    '''    
    new_mass_dict = {}
    av = {}
    mi = {}
    
    file = open(os.path.join(FILES_DIR, r'mzBPTk_Mass_Definitions.txt'), 'r')
    
    definitions = file.readlines()
    file.close()

    for i in range(2, len(definitions), 4):
        mi[definitions[i].strip()] = float(definitions[i+1].strip())
        av[definitions[i].strip()] = float(definitions[i+2].strip())
        
    new_mass_dict['mi'] = mi
    new_mass_dict['av'] = av
    new_mass_dict['proton'] = new_mass_dict['mi']['H'] - new_mass_dict['mi']['e-']
    new_mass_dict['H+'] = new_mass_dict['mi']['H'] - new_mass_dict['mi']['e-']
    new_mass_dict['water'] = 2 * new_mass_dict['mi']['H'] + new_mass_dict['mi']['O']
    new_mass_dict['hydronium'] = 2 * new_mass_dict['mi']['H'] + new_mass_dict['mi']['O'] + new_mass_dict['proton']
    new_mass_dict['H3O+'] = 2 * new_mass_dict['mi']['H'] + new_mass_dict['mi']['O'] + new_mass_dict['proton']
    new_mass_dict['NH3+'] = 2 * new_mass_dict['mi']['H'] + new_mass_dict['mi']['N'] + new_mass_dict['proton']
    new_mass_dict['cneutron']=new_mass_dict['mi']['C13']-new_mass_dict['mi']['C']
    new_mass_dict['nneutron']=new_mass_dict['mi']['N15']-new_mass_dict['mi']['N']

    return new_mass_dict

new_mass_dict = read_new_mass_def()



def read_Nterm_mod_return_dict():
    Nterm = {}
    Nterm_dict = defaultdict(dict)
    res_convert = ['C', 'H', 'N', 'O', 'P', 'S', 'F', 'D', 'C13', 'N15', 'S35', 'O18']
    dir = os.getcwd()
    file = open(dir + r'\Residues.txt', 'r')
    res = file.readlines()
    file.close()

    for i in range(0, len(res), 13):
        residue = []
        for j in range(0, 12):
            residue.append(int(res[i + j + 1].replace('"', '').strip()))
        residues[res[i].replace('"', '').strip()] = residue
        for k, member in enumerate(residue):
            Nterm_dict[res[i].replace('"', '').strip()][res_convert[k]] = residue[k]

    return Nterm_dict








def read_new_res_dict():
    file_r = open(os.path.join(FILES_DIR, r"new_res_list.txt"), 'r')
    data = file_r.readlines()
    file_r.close()
    res_dict = defaultdict(dict)
    for member in data:
        sub_data = member.split('|')
        residue_name = sub_data[0].strip()
        residue_data_list = sub_data[2].split(',')
        for element in residue_data_list:
            atom = element.split(":")[0].strip()
            number = int(element.split(":")[1].strip())
            res_dict[residue_name][atom]=number
    return res_dict

def read_new_Nterm_dict():
    file_r = open(os.path.join(FILES_DIR, r"new_NTermMod.txt"), 'r')
    data = file_r.readlines()
    file_r.close()
    Nterm_dict = defaultdict(dict)
    for member in data:
        sub_data = member.split('|')
        residue_name = sub_data[0].strip()
        residue_data_list = sub_data[2].split(',')
        for element in residue_data_list:
            atom = element.split(":")[0].strip()
            number = int(element.split(":")[1].strip())
            Nterm_dict[residue_name][atom]=number
    return Nterm_dict
    #print res_dict
#read_new_res_dict()
def read_new_Cterm_dict():
    file_r = open(os.path.join(FILES_DIR, r"new_CTermMod.txt"), 'r')
    data = file_r.readlines()
    file_r.close()
    Cterm_dict = defaultdict(dict)
    for member in data:
        sub_data = member.split('|')
        residue_name = sub_data[0].strip()
        residue_data_list = sub_data[2].split(',')
        for element in residue_data_list:
            atom = element.split(":")[0].strip()
            number = int(element.split(":")[1].strip())
            Cterm_dict[residue_name][atom]=number
    return Cterm_dict
        
def merge_multi_mods(varmod):
    modlist = defaultdict(list)
    #R14: Label:13C(6)15N(4); R14: Methyl
    #R14: Label:13C(6)15N(4), Methyl
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
                    pa = pattern.match(member)
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

def convert_mods(varmod, switch_dict):
    '''
    
    VERSION 0.1 (2014-06-26)
    The purpose of this script is to convert a Mascot varmod string containing SILAC labels to a different analogue
    switch dict = {FIND:REPLACE}
    For example, if: 
    >>>varmod = 'K1: Label:2H(4); K12: Label:2H(4); N-term: Propionyl; K1: Propionyl; K12: Propionyl'
    >>>switch_dict = {'Label:2H(4)' : 'Label:13C(6)15N(2)'}
    >>>convert_mods(varmod, switch_dict)
    >>>'K1: Label:13C(6)15N(2); K12: Label:13C(6)15N(2); N-term: Propionyl; K1: Propionyl; K12: Propionyl'
    
    '''
    converted = ''
    mods = varmod.split(';')
    for mod in mods:
        mod = mod.strip()
        for key in switch_dict.keys(): 
            if mod.find('Label') > -1:
                sub_mod = mod.split(" ")[1]
                if key == sub_mod:
                    mod = mod.split(" ")[0] + ' ' + switch_dict[key]
        if converted:
            converted += '; '
        converted += mod
    return converted

def remove_Nterms(varmod):
    mods = []
    for mod in varmod.split(';'):
        mod = mod.strip()
        if not mod.find('N-term') > -1:
            mods.append(mod)
    return '; '.join(mods)

def create_peptide_container(seq, varmod, fixedmod, keepLabels=True, switch_labels={}, search_multi_mods=False):
    '''
    VERSION: 0.7 (2017-08-15)
    Added compatibility with variable N-term mods.
    
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
    fixedMassAdds=None
    
    if fixedmod == None:
        fixedmod = ''    
    
    if isinstance(fixedmod, basestring):
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
    
    elif isinstance(fixedmod, dict):
        fixedMassAdds = fixedmod
        fixedmod = []
    
    for i, member in enumerate(fixedmod):
        if member.find('N-term') > -1:  # N-terminal modifications are dealt with in the mass calculator
            del fixedmod[i]
    
    varmod = remove_Nterms(varmod)        
    
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
    
    mascot = re.compile('([A-Z])([0-9]+?)[:] (\S+)')
    comet_tandem = re.compile('([A-Z])([0-9]+?)[:] ([0-9]+.[0-9]+)')
    discoverer = re.compile('([A-Z])([0-9]+?)\((\S+)\)')
    
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
            
            pa = comet_tandem.match(mod)
            if pa:
                peptide[int(pa.groups()[1]) - 1] = '[' + pa.groups()[2] + ']' + peptide[int(pa.groups()[1]) - 1]
            
            if not pa:
                pa = mascot.match(mod)
                if pa:
                    peptide[int(pa.groups()[1]) - 1] = var_mod_dict[pa.groups()[0] + '|' + pa.groups()[2]]
            
            if not pa:  
                pa = discoverer.match(mod)
                if pa:
                    peptide[int(pa.groups()[1]) - 1] = var_mod_dict[pa.groups()[0] + '|' + pa.groups()[2]] 
                
            assert pa
            
    if fixedMassAdds:
        for j, member in enumerate(peptide):
            if len(member)==1 and member in fixedMassAdds.keys():
                peptide[j] = fixedMassAdds[member] + member
            
    
    return peptide

def calc_CHNOPS_deprecated(seq, varmod='', fixedmod='', cg = 0):
    '''
    
    Version 0.1
    Old, deprecated version of calc_CHNOPS
    
    '''
    CHNOPS = []
    for i in range(0, 14):
        CHNOPS.append(0)

    peptide = create_peptide_container(seq, varmod, fixedmod)
    for member in peptide:
        current = res_dict[member]
        for i, entry in enumerate(CHNOPS):
            CHNOPS[i] += current[i]
    CHNOPS[1] += 2 #Add two hydrogens
    CHNOPS[1] += cg #Adds additional protons (actually, hydrogens but this doesn't matter for calculation of the distribution)
    CHNOPS[3] += 1 #Add one water
    return CHNOPS

def calc_CHNOPS(seq, varmod='', fixedmod='', cg = 0):
    CHNOPS = {}
    peptide = create_peptide_container(seq, varmod, fixedmod)
    for member in peptide:
        current = res_dict[member]
        for key in current.keys():
            if current[key] > 0:
                if key not in CHNOPS.keys():
                    CHNOPS[key] = current[key]
                else:
                    CHNOPS[key] += current[key]        
    CHNOPS['H'] += 2 #Add two hydrogens
    CHNOPS['H'] += cg #Adds additional protons (actually, hydrogens but this doesn't matter for calculation of the distribution)
    CHNOPS['O'] += 1 #Add one water
    return CHNOPS

def CHNOPS_to_sim(CHNOPS):
    sim=[0,0,0,0,0,0]
    ret = 'CHNOPS'
    for i, member in enumerate(ret):
        try:
            sim[i] = CHNOPS[member]
        except:
            sim[i] = 0
    return sim

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

def calc_pep_mass(sequence, cg):
    CHNOPS = calc_CHNOPS(sequence)
    mass_dict = read_mass_def()
    print CHNOPS
    mass = 0
    atom_d = {0:'C', 1:'H', 2: 'N', 3: 'O', 4: 'P', 5:'S'}
    for i in range(0,6):
        mass += CHNOPS[i]*mass_dict[atom_d[i]]
    if cg > 0:
        mass = (mass + (float(cg)*mass_dict['proton']))/float(cg)
    return mass

def CHNOPS2dict(CHNOPS):
    atom_d = {0:'C', 1:'H', 2: 'N', 3: 'O', 4: 'P', 5:'S'}
    CHNOPS_dict = {}
    for i in range(0,6):
        CHNOPS_dict[atom_d[i]]=CHNOPS[i]
    return CHNOPS_dict

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
    return NL_ions

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

def calc_pep_mass_from_residues(sequence, cg = 1, varmod = '', fixedmod = '', Nterm='', Cterm='', round_flag=False, keepLabels=True, ret_pros = False, ions='b/y', calcType='mi', switch_labels={}, search_multi_mods=False):
    '''
    
    Version 0.2 (2017-06-06)
    Added compatibility to add mass to aa's in brackets i.e. PEP[43.01]TIDE
    
    Version 0.1
    Returns mz, b_series, y_series
    
    '''
    
    currentDict = None
    
    #resadd = re.compile('\[([0-9]+.[0-9]+)\]([A-Z])')
    resadd = re.compile('\[([0-9]+.?[0-9]*)\]([A-Z])')
    
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


mass_dict = read_mass_def()
res_dict = read_new_res_dict()
#Nterm_dict = read_Nterm_mod_return_dict()
Nterm_dict = read_new_Nterm_dict()
Cterm_dict = read_new_Cterm_dict()
#print Nterm_dict
#print Cterm_dict
#dump_Nterm_dict()
#dump_Cterm_dict()
#Cterm_dict = read_Cterm_mod_return_dict()

#print Nterm_dict
#print Cterm_dict

def read_isotopes():
    dir = os.getcwd()
    csvReader = csv.reader(open(os.path.join(FILES_DIR, r'Isotopes.csv')), delimiter=',', quotechar='|')
    isotopes = []

    for i, row in enumerate(csvReader):
        #print row
        isotopes.append(row)
    Atoms = set()
    temp = ""
    NumDict = {}
    for entry in isotopes:
        Atoms.add(entry[2])
        temp += entry[2]
    for entry in Atoms:
        current_atom = str(entry)
        NumDict[current_atom] = temp.count(current_atom)
    Iso_Dict = {}
    for entry in Atoms:
        current_atom = str(entry)
        current_line = []
        for row in isotopes:
            if row[2] == current_atom:
                current_line.append([float(row[3]),float(row[4])])
        Iso_Dict[current_atom] = current_line


    NATOM = len(Atoms)

    At = Atoms
    Atoms = []
    for member in At:
        Atoms.append(member)

    return Atoms, NATOM, NumDict, Iso_Dict

Atoms, NATOM, NumDict, Iso_Dict = read_isotopes()


def make_array():
    x = numpy.array(range(1000), 'float')
    for i in range(0, 1000):
        x[i] = 0
    return x

def dump_d(D):
    line = 'D:'
    for z in range(0,5):
        line += str(D[z]) + ' '
    print line

def simulate(CHNOPS, PREC):
    print "SIMULATION IN PROGRESS...."
    CPATT = make_array()
    D = make_array()
    P = 0
    Q = 0
    NATOM = 6
    CPATT[0] = float(1.0)
    print Atoms
    for j in range(0, len(Atoms)):
        current_atom = Atoms[j]
        print "Working through... " + current_atom
        for i in range(0, CHNOPS[j]): #NUMBER OF ATOMS IN MOLECULE
            del D
            D = make_array()
            for k in range(P, Q + 1): #CALCULATION OF NEW PATTERN;
                for l in range(0, NumDict[current_atom]): #NUMBER OF HEAVIEST ISOTOPE
                    D[k+l] = D[k+l] + (CPATT[k] * Iso_Dict[current_atom][l][1])
            Q = Q + NumDict[current_atom] -1  #NUMBER OF HEAVIEST ISOTOPE OF PATTERN
            MAX = max(D)
            for k in range(P, Q+1):
                D[k]=float(D[k])/float(MAX)
            counter = 0
            current = D[counter]
            while current < PREC:
                counter += 1
                current = D[counter]
            left = counter
            counter = left
            current = D[counter]
            while current > PREC:
                counter += 1
                current = D[counter]
            right = counter
            CPATT = make_array()
            for k in range(left, right+1):
                CPATT[k]=D[k]
    return CPATT

def simulate2(CHNOPS_Dict, PREC=.0001):
    print "SIMULATION IN PROGRESS...."
    CHNOPS = [CHNOPS_Dict['C'], 0, CHNOPS_Dict['N'], CHNOPS_Dict['O'], CHNOPS_Dict['H'], 0, CHNOPS_Dict['S']]
    CPATT = make_array()
    D = make_array()
    P = 0
    Q = 0
    NATOM = 6
    CPATT[0] = float(1.0)
    print Atoms
    for j in range(0, len(Atoms)):
        current_atom = Atoms[j]
        print "Working through... " + current_atom + ' ' + str(CHNOPS[j])
        for i in range(0, CHNOPS[j]): #NUMBER OF ATOMS IN MOLECULE
            del D
            D = make_array()
            for k in range(P, Q + 1): #CALCULATION OF NEW PATTERN;
                for l in range(0, NumDict[current_atom]): #NUMBER OF HEAVIEST ISOTOPE
                    D[k+l] = D[k+l] + (CPATT[k] * Iso_Dict[current_atom][l][1])
            Q = Q + NumDict[current_atom] -1  #NUMBER OF HEAVIEST ISOTOPE OF PATTERN
            MAX = max(D)
            for k in range(P, Q+1):
                D[k]=float(D[k])/float(MAX)
            counter = 0
            current = D[counter]
            while current < PREC:
                counter += 1
                current = D[counter]
            left = counter
            counter = left
            current = D[counter]
            while current > PREC:
                counter += 1
                current = D[counter]
            right = counter
            CPATT = make_array()
            for k in range(left, right+1):
                CPATT[k]=D[k]
    return CPATT

def approximate_averagine_distribution_from_mass(mass):
    aa = int(round(float(mass)/float(111.1254), 0)) # Number of amino acids
    C = int(round(float(aa)*float(4.9384), 0))
    N = int(round(float(aa)*float(7.7583), 0))
    H = int(round(float(aa)*float(1.3577), 0))
    O = int(round(float(aa)*float(1.4773), 0))
    S = int(round(float(aa)*float(0.0417), 0))
    p = simulate2({'C':C, 'H':H, 'N':N, 'O':O, 'S':S})
    ptn = extract_pattern(p)
    return ptn
    
def extract_pattern(A):
    B= [0]
    counter = 0
    current=A[counter]
    while current > 0.000001:
        B.append(A[counter])
        counter += 1
        current = A[counter]
    return B[1:]

def graph_pattern(A):
    dump_d(A)
    B= [0]
    counter = 0
    current=A[counter]
    while current > 0.000001:
        B.append(A[counter])
        counter += 1
        current = A[counter]
    pylab.bar(range(0, len(B)), B, width = 0.1)
    print B
    pylab.show()


def extract_gi(filename, sheetname, outfile, gi_sheet_name = 'gi'):
    print "WARNING: Deprecated, use method in protein_cose"
    gi_set = set()
    rdr = mzR.reader(filename, sheet_name = sheetname)
    counter = 0
    pa = re.compile('(gi\|[0-9]+?)\|')
    for row in rdr:
        if counter % 100 == 0:
            print str(counter)
        counter += 1
        gi_row = row["Accession Number"]
        gis = gi_row.split(";")
        for gi in gis:
            gi = gi.strip()
            id = pa.match(gi)
            if id:
                current_gi = id.groups()[0]
                gi_set.add(current_gi)
    rdr.close()
    wtr = mzR.writer(outfile, sheet_name = gi_sheet_name, columns=["Accession Number"])
    row = {}
    for member in gi_set:
        row["Accession Number"] = member
        wtr.write(row)
    wtr.close()

def pull_mods_from_mascot_header(filename):
    '''
    
    Version 0.1
    Reads Mascot_Header sheet from multiplierz report.  Builds and returns a dictionary of parameters.
    This is a bit slow.  Consider making into a csv file or using xlrd for faster access.
    
    '''
    try:
        rdr = mzR.reader(filename, sheet_name = "Mascot_Header")
        header = {}
        for row in rdr:
            header[row['Header']] = row['--------------------------------------------------']
        
        rdr.close()
        return header
    except:
        import wx
        wx.MessageBox('Could not load header info.\nDoes this file have a Mascot_Header sheet?')
    

def pull_mods_from_comet_header(filename):
    '''
    
    Version 0.1
    Reads Comet_Header sheet from multiplierz report.  Builds and returns a dictionary of parameters.
    This is a bit slow.  Consider making into a csv file or using xlrd for faster access.
    
    '''
    rdr = mzR.reader(filename, sheet_name = "Comet_Header")
    header = {}
    for row in rdr:
        header[row['Program']] = row['Data']
    rdr.close()
    return header

#filename = r'D:\SBF\mzStudio\comet_wiff2.xlsx'
#a = pull_mods_from_comet_header(filename)
#print a

def derive_SILAC_correction_factor(filename, sheetname, ignore_ones=True):
    raise ValueError("Moved to SILAC_Scripts.py")

def annonate_xls_with_iTRAQ_figures(filename, sheetname):
    pass
    

def top_20_annotater_itms(filename, sheetname):
    '''
    Given xls file and sheetname, looks up each spectrum and returns top 20 ions
    '''
    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename, sheet_name = sheetname, columns=rdr.columns + ['Top20'])
    for row in rdr:
        seq = row['Peptide Sequence']
        print seq
        desc = row['Spectrum Description']
        print desc
        scan = int(desc.split('.')[1].strip())
        print scan
        scan_type = row['Scan Type']
        if scan_type == 'HCD':
            scan = scan - 1
        print scan
        mgf = row['File']
        dir = os.path.dirname(mgf)
        file = desc.split('.')[0].strip() + '.raw'
        file_path = dir + '\\' + file
        top20 = pick_top_20(file_path, scan)
        print top20
        row['Top20'] = str(top20)
        wtr.write(row)
    rdr.close()
    wtr.close()

def top_20_annotater_matcher_itms(filename, sheetname):
    '''
    Given xls file and sheetname, looks up each spectrum and returns top 20 ions
    '''
    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename, sheet_name = sheetname, columns=rdr.columns + ['Top20', 'matches'])
    for row in rdr:
        seq = row['Peptide Sequence']
        var_mod = row['Variable Modifications']
        mz, b_ions, y_ions = calc_pep_mass_from_residues(seq, cg = 1, varmod = var_mod, fixedmod = 'Carbamidomethyl (C),iTRAQ4plex (K),iTRAQ4plex (N-term)', Nterm='', Cterm='')
        print seq
        desc = row['Spectrum Description']
        print desc
        scan = int(desc.split('.')[1].strip())
        print scan
        scan_type = row['Scan Type']
        if scan_type == 'HCD':
            scan = scan - 1
        print scan
        try:
            mgf = row['File']
            dir = os.path.dirname(mgf)
        except:
            dir = os.path.dirname(filename)
        file = desc.split('.')[0].strip() + '.raw'
        file_path = dir + '\\' + file
        top20 = pick_top_20(file_path, scan)
        print top20
        row['Top20'] = str(top20)
        matches = []
        pep_len = len(seq)
        for i, member in enumerate(b_ions):
            found = look_for_mass(top20, member)
            if found[0]:
                matches.append(['b' + str(i+1), found[1]])
        for i, member in enumerate(y_ions):
            found = look_for_mass(top20, member)
            if found[0]:
                matches.append(['y' + str(i+1), found[1]])
        matches.sort(key=lambda t:t[1],reverse=True)
        print matches
        row['Matches'] = str(matches)
        wtr.write(row)

    rdr.close()
    wtr.close()

def pick_top_20(file, scan):
    '''
    Given raw file and scan, returns top 20 ions in spectrum
    '''
    m = mzAPI.mzFile(file)
    spec = m.scan(scan)
    size = len(spec)
    spec.sort(key=lambda t:t[1], reverse = True)
    top20 = []
    count = 0
    counter = 0
    while count < 20 and counter < size:
        current = spec[counter][0]
        inten = spec[counter][1]
        if current > 145:
            top20.append([current, inten])
            count += 1
        counter += 1
    top20.sort()
    print top20
    m.close()
    return top20

def find_MS2(file, mz, cg, rt_start=0, rt_stop=99999, tolerance=0.02, scan_type="CAD", steps = 0, only_dep=False):
    target = [mz]
    if steps:
        for i in range(0, steps):
            target.append(mz + (mass_dict['H+']/cg))
    m = mzAPI.mzFile(file)
    pa = re.compile('.*?ms2 ([\d.]+?)@')
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m)
    """ Scan dict[scan_number] = MS1 or MS2;
        rt dict [scan_number] = retention time
        filter dict [scan_number] = filter
        rt2scan [retention time] = scan """
    hits = []
    for key, value in scan_dict.iteritems():
        if value == "MS2":
            filter = filter_dict[key]
            prec = float(pa.match(filter).groups()[0])
            go = False
            if only_dep == False:
                go = True
            else:
                if filter[13] == 'd':
                    go = True
            if go:
                for member in target:
                    lo = member - tolerance
                    hi = member + tolerance
                    rt = rt_dict[key]
                    if prec > lo and prec < hi and rt > rt_start and rt < rt_stop:
                        hits.append([key, prec, rt])
    hits.sort()
    for member in hits:
        print member


def make_CF_csv(csv_filename, cf):
    labels = []    
    if len(cf)==4:
        labels = [114.11, 115.11, 116.11, 117.11]
    elif len(cf)==6:
        labels = [126.12, 127.12, 128.12, 129.12, 130.12, 131.12]
    elif len(cf)==8:
        labels = [113.11, 114.11, 115.11, 116.11, 117.11, 118.11, 119.115, 121.12]
    rows = zip(labels, cf)
    csvWriter = csv.writer(open(csv_filename, 'wb'), delimiter=',', quotechar='|')
    csvWriter.writerows(rows)

def derive_CF_median(filename, sheetname="Data",  labels = 't6', type='summed', all_non_zero=True, ignore_cRAP=True, channels=[]):
    if type.lower() == 'summed':
        prefix = 'Summed '
    elif type.lower() == 'max':
        prefix = 'Max '    
    if labels not in ['t6', 'i8', 'i6of8', 'i4']:
        raise ValueError("Label not supported.")
    if labels=='i4':
        cols = ['114', '115', '116', '117']
        reps = [0,0,0,0]     
        reduced_data = [[],[],[],[]]
    if labels=='t6':
        cols = ['126', '127', '128', '129', '130', '131']
        reps = [0,0,0,0,0,0]    
        reduced_data = [[],[],[],[],[],[]]
    if labels=='i8':
        cols = ['113', '114', '115', '116', '117', '118', '119', '121']
        reps = [0,0,0,0,0,0,0,0]    
        reduced_data = [[],[],[],[],[],[], [], []]
    if labels=='i6of8':
        cols = ['113', '114', '115', '117', '118', '119']
        reps = [0,0,0,0,0,0]   
        reduced_data = [[],[],[],[],[],[]]
    for i, member in enumerate(cols):
        cols[i] = prefix + member    
    
    filtered = []
    rdr = mzR.reader(filename, sheet_name = sheetname)
    prots = "Protein Description" if 'Protein Description' in rdr.columns else "Names"
    if prots == "Names":
        print "WARNING... PILOT DATA DETECTED. cRAP not ignored from UNIPROT databases"    
    for row in rdr:
        get_it = True
        #desc = row['Protein Description']
               
        desc = row[prots]
        if ignore_cRAP:
            if desc.find("cRAP") > -1:
                get_it = False
        if all_non_zero:
            for member in cols:
                if int(row[member]) > 0:
                    pass
                else:
                    get_it = False
        current_vals = [float(row[x]) for x in cols]
        lowest = min(current_vals)
        count = 0
        for member in current_vals:
            if member == lowest:
                count += 1
        if count > 1:
            get_it = False
        if get_it:
            filtered.append(row)
    
    for row in filtered:
        for j, col in enumerate(cols):
            reduced_data[j].append(row[col])
    medians = [numpy.median(x) for x in reduced_data]
    print medians
    rdr.close()
    min_r = min(medians)
    cf = []
    
    for i in medians:
        cf.append(float(min_r)/float(i))

    return medians, cf    
    
def derive_CF(filename, sheetname="Data", labels='i4', type='summed', all_non_zero=True, ignore_cRAP=True, channels=[], intensity_thresh=0):
    '''
    Returns reps, cf
    '''
    if type.lower() == 'summed':
        prefix = 'Summed '
    elif type.lower() == 'max':
        prefix = 'Max '
    if labels=='i4':
        cols = ['114', '115', '116', '117']
        reps = [0,0,0,0]
    if labels=='t6':
        cols = ['126', '127', '128', '129', '130', '131']
        reps = [0,0,0,0,0,0]
    if labels=='i6of8':
        cols = ['113', '114', '115', '117', '118', '119']
        reps = [0,0,0,0,0,0]
    if labels=='i8':
        cols = ['113', '114', '115', '116', '117', '118', '119', '121']
        reps = [0,0,0,0,0,0,0,0]
    if not cols:
        print "Unsupported label type!"
        raise ValueError
    for i, member in enumerate(cols):
        cols[i] = prefix + member
    rdr = mzR.reader(filename, sheet_name = sheetname)
    prots = "Protein Description" if 'Protein Description' in rdr.columns else "Names"
    if prots == "Names":
        print "WARNING... PILOT DATA DETECTED. cRAP not ignored from UNIPROT databases"
    for row in rdr:
        get_it = True
        #desc = row['Protein Description']
        desc = row[prots]
        if ignore_cRAP:
            if desc.find("cRAP") > -1:
                get_it = False
        if all_non_zero:
            for member in cols:
                if int(row[member]) > 0:
                    pass
                else:
                    get_it = False
        if intensity_thresh:
            if min([row[x] for x in cols]) < intensity_thresh:
                get_it = False
        if get_it:
            for i, member in enumerate(cols):
                reps[i] += int(row[member])

    rdr.close()
    print reps
    min_r = min(reps)
    cf = []
    if not channels:
        for i in reps:
            cf.append(float(min_r)/float(i))
        if labels=='i6of8':
            reps = [reps[0], reps[1], reps[2], 0, reps[3], reps[4], reps[5], 0]
            cf = [cf[0], cf[1], cf[2], 0, cf[3], cf[4], cf[5], 0]
    else:
        r_list = []
        for i, member in enumerate(cols):
            if channels[i]:
                r_list.append(reps[i])
            else:
                reps[i]=0
        min_r = min(r_list)
        for i in reps:
            try:
                cf.append(float(min_r)/float(i))
            except:
                cf.append(0)

    return reps, cf

def apply_CF(filename, sheetname, cf, type='summed'):
    if type.lower() == 'summed':
        prefix = 'Summed '
    elif type.lower() == 'max':
        prefix = 'Max '

    if len(cf)==4:
        rcols = ['c114', 'c115', 'c116', 'c117']
    if len(cf)==6:
        rcols = ['c126', 'c127', 'c128', 'c129', 'c130', 'c131']
    if len(cf)==8:
        rcols = ['c113', 'c114', 'c115', 'c116', 'c117', 'c118', 'c119', 'c121']

    val_dict = {}
    for i, member in enumerate(rcols):
        sub_dict = {}
        sub_dict[member]=cf[i]
        val_dict[prefix + member[1:]] = sub_dict

    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename, sheet_name = sheetname, columns = rdr.columns + rcols)
    for row in rdr:
        for key, v in val_dict.iteritems():
            row[v.keys()[0]] = float(row[key]) * float(v[v.keys()[0]])
        wtr.write(row)
    rdr.close()
    wtr.close()

def MS3_extract(filename, sheetname):
    rdr = mzR.reader(filename, sheet_name = sheetname)
    file_re = re.compile('(.+?)[.]')
    for row in rdr:
        rawname = os.path.dirname(filename) + '\\' + file_re.match(row['Spectrum Description']).group(1) + '.raw'
        break
    m = mzAPI.mzFile(rawname)
    print rawname
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, start=0, stop=99999)
    cols = ['r114', 'r115', 'r116', 'r117']
    scans = ['Scan1 ', 'Scan2 ']
    rcols = []
    for scan in scans:
        for col in cols:
            rcols.append(scan + col)
    rcols += ['Complete1', 'Complete2']
    wtr = mzR.writer(filename, sheet_name = sheetname, columns = rdr.columns + rcols)
    scan_info = re.compile('.+?[.](\d+?)[.]')
    filtermz = re.compile('.+?(\d+?[.]\d+?)[@]')
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print counter
        counter += 1
        type = row['Scan Type']
        desc = row['Spectrum Description']
        scan = int(scan_info.match(desc).group(1))
        if type == 'CID':
            offset = 1
        else:
            offset = 0
        scan1 = scan + 1 + offset
        scan2 = scan + 2 + offset
        filter = filter_dict[scan]
        mz = filtermz.match(filter).group(1)
        get_scan1 = False
        get_scan2 = False
        scan1filter = filter_dict[scan1]
        scan2filter = filter_dict[scan2]
        try:
            scan1mz = filtermz.match(scan1filter).group(1)
        except:
            scan1mz = None
        try:
            scan2mz = filtermz.match(scan2filter).group(1)
        except:
            scan2mz = None
        if counter % 100 == 0:
            print scan
            print scan1
            print scan2
            print filter
            print scan1filter
            print scan2filter
        if mz == scan1mz:
            get_scan1 = True
            if mz == scan2mz:
                get_scan2 = True
        for col in rcols:
            if col.find("Complete") == -1:
                row[col] = 0
            else:
                row[col] = False
        if get_scan1:
            scan = m.cscan(scan1)
            reps = get_reps(scan)
            sub_scan = ['Scan1 r114', 'Scan1 r115', 'Scan1 r116', 'Scan1 r117']
            for i, member in enumerate(sub_scan):
                row[member] = reps[i]
            if reps[0] > 0 and reps[1] > 0 and reps[2] > 0 and reps[3] > 0:
                row['Complete1'] = True
        if get_scan2:
            scan = m.cscan(scan2)
            reps = get_reps(scan)
            sub_scan = ['Scan2 r114', 'Scan2 r115', 'Scan2 r116', 'Scan2 r117']
            for i, member in enumerate(sub_scan):
                row[member] = reps[i]
            if reps[0] > 0 and reps[1] > 0 and reps[2] > 0 and reps[3] > 0:
                row['Complete2'] = True
        wtr.write(row)
    rdr.close()
    wtr.close()
    m.close()

def get_reps(scan, tolerance = 0.02):
    intensities = []
    reps = [114.11, 115.11, 116.11, 117.11]
    for member in reps:
        inten = get_intensity(scan, member, tolerance)
        intensities.append(inten[1])
    return intensities

def mz_trim(filename, sheetname, tolerance):
    '''
        Purpose: given a mulitplierz sheet, removes rows with a greater than specified tolerance (ppm)
    '''
    header = pull_mods_from_mascot_header(filename)
    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename[:-4]+'_trimmed.xls', columns = rdr.columns, sheet_name = sheetname)
    counter = 0
    ppm = 0
    for row in rdr:
        if counter % 1000 == 0:
            print counter
            print ppm
        counter += 1
        seq = row['Peptide Sequence']
        cg = int(row['Charge'])
        varmods = row['Variable Modifications']
        calc, b_ions, y_ions = calc_pep_mass_from_residues(seq, cg, varmod = varmods, fixedmod = header['Fixed modifications'])
        meas = float(row['Experimental mz'])
        ppm = (abs(meas-float(calc))/float(calc))*float(1000000)
        if ppm <= tolerance:
            wtr.write(row)
    rdr.close()
    wtr.close()

def find_peak(MSfile, mz, tolerance=0.01, cg=2):
    '''
        Looks through raw file for particular mz and charge state
    '''
    m = mzAPI.mzFile(MSfile)
    start, stop = m.scan_range()
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)

    counter = 0
    found = []
    for i in range(start, stop):
        if counter % 500 == 0:
            print str(i)
            print filter_dict[i]
        counter += 1
        if scan_dict[i]=="MS1":
            E = get_MS(m, i)
            for member in E:
                if member[0] > (mz-tolerance) and member[0] < (mz+tolerance):
                    if cg == int(member[3]):
                        found.append([i, member[0], member[1], member[3]])
    found.sort()
    return found

def find_MS2(MSfile, mz, tolerance=0.01, inst=["FTMS", "ITMS"], mode=["c","p"], act=["hcd", "cid"]):
    '''
        inst=["FTMS", "ITMS"]
    '''
    print "warning currently not compatible with targeted..."
    m = mzAPI.mzFile(MSfile)
    start, stop = m.scan_range()
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)
    """ Scan dict[scan_number] = MS1 or MS2;
        rt dict [scan_number] = retention time
        filter dict [scan_number] = filter
        rt2scan [retention time] = scan """
    # FTMS + c NSI Full ms2 679.53@hcd35.00 [100-2000]
    pa = re.compile('.*?([FI]TMS) [+] ([cp]) NSI d Full ms2 (\d+?.\d+?)@(hcd|cid)')
    counter = 0
    found = []
    for i in range(start, stop):
        if counter % 500 == 0:
            print str(i)
            print filter_dict[i]
        counter += 1
        if scan_dict[i]=="MS2":
            filt = filter_dict[i]
            id = pa.match(filt)
            if id:
                if id.groups()[0] in inst and id.groups()[1] in mode and id.groups()[3] in act:
                    prec = float(id.groups()[2])
                    if mz > prec - tolerance and mz < prec + tolerance:
                        found.append([i, id.groups()[2], id.groups()[3], filt])
    found.sort()
    print "warning currently not compatible with targeted..."
    return found

def find_peak_in_hcd(file, mz, tolerance = .005, threshold=200, verbose=False):
    '''
    
    Version 0.2 2014-07-19
    If verbose, prints scan every 1000 scans
    Uses "look_for_mz" i.e. returns first value found, not necessarily most intense in window
    '''
    m = mzAPI.mzFile(file)
    start, stop = m.scan_range()
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)
    scan_list = set()
    counter = 0
    for i in range(start, stop):
        if counter % 1000 == 0:
            if verbose:
                print str(i)
                print filter_dict[i]
        counter += 1
        if filter_dict[i].find('Full ms2') > -1:
            if filter_dict[i].find('hcd') > -1:
                scan = m.cscan(i)
                found_mz, found = look_for_mz(scan, mz, tolerance, threshold)
                if found:
                    scan_list.add(i)
    scan_set = list(scan_list)
    scan_set.sort()
    return scan_set

def acetyl(file):
    m = mzAPI.mzFile(file)
    start, stop = m.scan_range()
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)
    scan_list = set()
    counter = 0
    for i in range(start, stop):
        if counter % 500 == 0:
            print str(i)
            print filter_dict[i]
        counter += 1
        if filter_dict[i].find('Full ms2') > -1:
            if filter_dict[i].find('hcd') > -1:
                scan = m.cscan(i)
                found_mz, found = look_for_mz(scan, 126.0919, 0.005, 200)
                if found:
                    scan_list.add(i)
    scan_set = list(scan_list)
    scan_set.sort()
    return scan_set

def acetyl_check(filename, sheetname):
    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename, columns = rdr.columns + ["Imm AcK?"], sheet_name = sheetname)
    dir = os.path.dirname(filename)
    for row in rdr:
        file = dir + "\\" + row["Spectrum Description"].split(".")[0] + '.raw'
        break
    print file
    m = mzAPI.mzFile(file)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print counter
        counter += 1
        scannum = int(row["Spectrum Description"].split(".")[1])
        if row["Scan Type"] == "CID":
            scannum += 1
        scan = m.cscan(scannum)
        found_mz, found = look_for_mz(scan, 126.0919, 0.005, 200)
        if found:
            row["Imm AcK?"] = "YES"
        else:
            row["Imm AcK?"] = "NO"
        wtr.write(row)
    rdr.close()
    wtr.close()

def internal_lys_check(filename, sheetname):
    pa = re.compile('.*?([KC])(\d+?)[:] Acetyl')
    rdr = mzR.reader(filename, sheet_name = sheetname)
    try:
        wtr = mzR.writer(filename, columns = rdr.columns + ["Int Lys?"], sheet_name = sheetname)
    except:
        wtr = mzR.writer(filename, columns = rdr.columns, sheet_name = sheetname)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print counter
        counter += 1
        seq = row["Peptide Sequence"]
        print seq
        varmod = row['Variable Modifications']
        if not varmod:
            varmod = ''
        mods = varmod.split(";")
        acet_list = []
        acet = False
        for mod in mods:
            print mod
            id = pa.match(mod)
            if id:
                print "FOUND!"
                acet = True
                acet_list.append(int(id.groups()[1]))
        print acet
        print acet_list
        print len(seq)
        int_lys = "NA"
        if acet:
            if len(seq) in acet_list:
                int_lys = False
            else:
                int_lys = True
        print int_lys
        row["Int Lys?"] = int_lys
        wtr.write(row)
    rdr.close()
    wtr.close()

def derive_intensities(filename, sheetname, tolerance = 0.02, threshold=200, alt_dir=None):
    rdr = mzR.reader(filename, sheet_name = sheetname)
    wtr = mzR.writer(filename, columns = rdr.columns + ["Peak Intensity","Profile"], sheet_name = sheetname)
    if not alt_dir:
        dir = os.path.dirname(filename)
    else:
        dir = alt_dir
    for row in rdr:
        file = dir + "\\" + row["Spectrum Description"].split(".")[0] + '.raw'
        break
    print file
    m = mzAPI.mzFile(file)
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print counter
        counter += 1
        spec = row["Spectrum Description"]
        rawfilename = os.path.dirname(filename) + '\\' + spec.split(".")[0] + '.raw'
        decal = float(spec.split("|")[1])
        sid = int(spec.split(".")[1])
        cg = int(row["Charge"])
        ms1 = find_MS1(scan_dict, sid, "Reverse")
        print ms1
        start, stop, scan_array = derive_elution_range_by_C12_C13(m, scan_dict, ms1, decal, cg, tolerance, threshold)
        print start
        print stop
        print scan_array
        start_scan = scan_array[0][0]
        end_scan = scan_array[len(scan_array)-1][0]
        start_rt = rt_dict[start_scan]
        end_rt = rt_dict[end_scan]
        profile = str(start_scan) + ', ' + str(end_scan) + '|' + str(start_rt) + ', ' + str(end_rt)
        print profile
        scan_array.sort(key=lambda t:t[1], reverse = True)
        print scan_array
        row["Profile"] = profile
        row["Peak Intensity"] = scan_array[0][1]
        wtr.write(row)
    rdr.close()
    wtr.close()

def raw_to_sql(filename):
    rawname = os.path.basename(filename)
    m = mzAPI.mzFile(filename)
    titles = dict(map(lambda (x,y): (x+1,y), list(enumerate(m.filters()))))
    (start,stop) = m.scan_range()
    print filename[:-4] + '.db'
    conn = sql.connect(filename[:-4] + '.db')
    c = conn.cursor()
    line = 'create table if not exists mz (id integer primary key, filename text, scan integer, rt real, mz real, intensity real, "c_int" real, cg integer);'
    line2 = 'create table if not exists scan_dict (scan integer primary key, rt real, mode text, type text);'
    c.execute(line)
    c.execute(line2)
    conn.commit()
    print "creating scan dict..."
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m, 0, 999999)
    counterr = 0
    counter = 0
    for sid in range(start,stop):
        (time,title) = titles[sid]
        if title.find("Full ms ") > -1:
            C = m.cscan(sid)
            line2 = 'insert into scan_dict values (' + str(sid) + ', ' + str(rt_dict[sid]) + ', "MS1", "p");'
            c.execute(line2)
            stat = counterr % 100
            if stat == 0:
                print stat
                #print "X-tract... " + str(sid) + " " + str(counterr) + " of " + str(B) + " = " + str(round(float(float(counterr)/float(B))*100,1)) + "%"
            counterr += 1
            for val in C:
                line = 'insert into mz values(' + str(counter) + ', "' + rawname + '", ' + str(sid) + ', ' + str(rt_dict[sid]) + ', ' + str(val[0]) + ', ' + str(val[1]) + ', ' + str(val[2]) + ', ' + str(val[3]) + ');'
                counter += 1
                c.execute(line)
    conn.commit()
    print "Building index..."
    line = 'create index ind1 on mz(scan)'
    c.execute(line)

    
def protein_deconvolute():
    #Needs tweaking.  Meant to deconvolute protein MW (simple algorithm)
    start = 15
    end = 150
    list = [938.88, 923.6, 909.25, 894.88]
    list = [1154.4, 1116.2, 1080.1, 1046.4]
    result = {}
    for i in range(start, end):
        dist = []
        for j, k in enumerate(list):
            current = (k * (i+j)) - (i+j-1)
            dist.append(current)
        av = average(dist)
        res = resid_sum(dist, av)
        result[i] = res
        print res

    best = [9999999, 0]
    for member in result.keys():
        current = result[member]
        if current < best[0]:
            best = [current, member]
    print best

    for i, member in enumerate(list):
        current = (member * (best[1]+i)) - (best[1]+i-1)
        print str(i) + ' ' + str(current)

def average(list):
    '''
    
    Version 0.1
    Should use numpy.average
    list is a type and bad form to use as a variable name
    
    '''
    raise ValueError("Deprecated Function.  Use numpy.average.")
    count = 0
    for member in list:
        count += member
    average = float(count)/float(len(list))
    return average

def resid_sum(dist, av):
    error = 0
    for member in dist:
        error += abs(member - av)
    return error

def count_MS2_spectra(file):
    m = mzAPI.mzFile(file)
    scan_dict, rt_dict, filter_dict, rt2scan = create_dicts(m)
    MS2_count = 0
    for filt in filter_dict.values():
        if filt.find('ms2') > -1:
            MS2_count += 1
    m.close()
    return MS2_count


def make_zscore_csv_for_R(filename, output_filename, sheetname='Data', reps='i8', logs=False):
    '''
    
    Version 0.1 2014-07-11
    Makes a csv file
    Key z1...zx
    
    '''
    if reps=='i4':
        rcols = ['c114', 'c115', 'c116', 'c117']
    if reps=='t6':
        rcols = ['c126', 'c127', 'c128', 'c129', 'c130', 'c131']
    if reps=='i8':
        rcols = ['c113', 'c114', 'c115', 'c116', 'c117', 'c118', 'c119', 'c121']
    if reps=='i6of8':
        rcols = ['c113', 'c114', 'c115', 'c117', 'c118', 'c119']    
    if not logs:
        zs = [x.replace('c','z') for x in rcols]
    else:
        zs = [x.replace('c','z.log2c') for x in rcols]
    rdr = mzR.reader(filename, sheet_name = sheetname)
    data = [['Key'] + zs]
    for row in rdr:
        key = row['Filter Key']
        zvals = [row[x] for x in zs]
        data.append([key]+zvals)
    rdr.close()
    wtr = csv.writer(open(output_filename, 'wb'), delimiter=',', quotechar='"')
    for row in data:
        wtr.writerow(row)

def zscore(filename, sheetname='Data', reps='i8', add_log=False):
    '''
    Version 0.2 2014-07-11
    If add_log true, calculates z-score on log2 reporter ions
    Uses population standard deivation
    Calculates z-scores for quant experiments.
    zscore(filename, sheetname='Data', reps='i8')
    reps = 'i4', 't6', 'i8', or 'i6of8'
    '''    
    if reps=='i4':
        rcols = ['c114', 'c115', 'c116', 'c117']
    if reps=='t6':
        rcols = ['c126', 'c127', 'c128', 'c129', 'c130', 'c131']
    if reps=='i8':
        rcols = ['c113', 'c114', 'c115', 'c116', 'c117', 'c118', 'c119', 'c121']
    if reps=='i6of8':
        rcols = ['c113', 'c114', 'c115', 'c117', 'c118', 'c119']    
    zs = [x.replace('c','z') for x in rcols]
    if add_log:
        logzs = [x.replace('c','z.log2c') for x in rcols]
    rdr = mzR.reader(filename, sheet_name = sheetname)
    if not add_log:
        wtr = mzR.writer(filename, sheet_name = sheetname, columns = rdr.columns + zs)
    else:
        wtr = mzR.writer(filename, sheet_name = sheetname, columns = rdr.columns + zs + logzs)
    for row in rdr:
        vals = [row[col] for col in rcols]
        ok_log = False
        if add_log:
            if all(vals):
                logvals = [math.log(row[col], 2) for col in rcols]
                ok_log = True
            else:
                logvals = ['NA' for col in rcols]
        av = numpy.average(vals)
        st = numpy.std(vals)
        if add_log and ok_log:
            log_av = numpy.average(logvals)
            log_st = numpy.std(logvals)        
        if st > 0:
            for z, c in zip(zs, rcols):
                row[z]= float(row[c]-av)/float(st)
            if add_log:
                for z, c in zip(logzs, logvals):
                    row[z]= float(c-log_av)/float(log_st)
        else:
            for z, c in zip(zs, rcols):
                row[z]=0
            if add_log:
                for z, c in zip(logzs, rcols):
                    row[z]=0
        wtr.write(row)
    rdr.close()
    wtr.close()

def neutral_loss_analysis(file, loss_cg=2, tolerance = .005, threshold=200):
    pass

def get_MS2_intensity(ms2, pMZ, tolerance = 0.02):
    return max([(mz,s) for (mz,s) in ms2 if abs(mz-pMZ) <= tolerance] or [(pMZ,0)],key=lambda x: (x[1],x[0]))

def estimate_gas_phase_purity(scan, sequence, charge, mz, varmod, fixedmod):
    # Prune scan: remove ions less than 175 (discard immonium), remove potential water loss peaks or water adduct peaks
    scan = [x for x in scan if (x[0] > 175 and (x[0] < (mz - (float(37)/float(charge))) or x[0] > (mz + (float(19)/float(charge))))) ]
    #print scan
    # Create hit list of ions to count as assigned ion current
    hit_list = []
    for i in range(1, charge+1):
        mz, b, y = calc_pep_mass_from_residues(sequence, cg=i, varmod=varmod, fixedmod=fixedmod)
        hit_list+=y
        hit_list+=b
        for member in b:
            hit_list.append(member-28) # add a type ions
        water_losses = []
        for member in hit_list:
            water_losses.append(member-(float(18)/float(charge))) # water loss
            water_losses.append(member-(float(17)/float(charge))) # ammonia loss
        hit_list += water_losses

    #print "1"
    #print hit_list
    total_ion_current = sum([x[1] for x in scan])

    assigned_ion_current = 0
    for member in hit_list:
        entry = get_MS2_intensity(scan, member, tolerance = 0.5)
        if entry[1]>0: #If found,
            assigned_ion_current += entry[1] #add intensity to assigned ion current
            scan.remove(entry) # then remove from list, so it can't be counted again
            keep_going = True #Then, look for isotopes
            while keep_going:
                member += 1 #Incremement mass by 1
                entry = get_MS2_intensity(scan, member, tolerance = 0.5)
                if entry[1]>0:
                    assigned_ion_current += entry[1]
                    scan.remove(entry)
                else:
                    keep_going = False

    assigned_pct = float(assigned_ion_current)/float(total_ion_current)
    return assigned_pct

def estimate_noise(scan):
    if len(scan)>50:
        scan.sort(key=lambda t:t[1])
        length = len(scan)
        if length % 2 == 0:
            noise1 = scan[(int(length/2))-1][1]
            noise2 = scan[(int(length/2))][1]
            noise = float(noise1 + noise2)/float(2.0)
        else:
            noise = scan[(int(length/2))][1]
    else:
        noise = 0
    return noise

def generate_write_string(entry):
    write_string = ''
    for member in entry:
        write_string += str(member) + '\t'
    write_string = write_string[:-1]
    write_string += '\n'
    return write_string

def recalibrate_spectrum_from_text(filename, slope, intercept):
    file_r = open(filename, 'r')
    data = file_r.readlines()
    file_r.close()
    mass_list = []
    for i in range(2, len(data)):
        items = data[i].split('\t')
        recal = [float(x.strip()) for x in items]
        recal[0] = recal[0] + (recal[0] * slope + intercept)
        mass_list.append(recal)
    file_w = open(filename[:-4] + '_RECAL.txt', 'w')
    file_w.write(generate_write_string(['m\z', 'Intensity', 'Relative'])) 
    for entry in mass_list:
        file_w.write(generate_write_string(entry)) 
    file_w.close()



def add_ppm_error_to_multiplierz_sheet(filename):
    '''

    Input = multiplierz xls sheet
    Adds 'ppm' column
    
    '''    
    counter = 0
    rdr = mzR.reader(filename)
    wtr = mzR.writer(filename, columns=rdr.columns + ['ppm'], sheet_name="Data")
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        th = row['Predicted mr']
        delta = row['Delta']
        error = (abs(float(delta))/float(th)) * 1000000
        row['ppm'] = error
        wtr.write(row)
    rdr.close()
    wtr.close()
    
def export_mass_error_csv(filename, outputfilename):
    '''
    
    Input = multiplierz xls sheet
    Outputs a csv file of mass errors
    
    '''
    counter = 0
    mass_errors = [['ppm']]
    rdr = mzR.reader(filename)
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        th = row['Predicted mr']
        delta = row['Delta']
        error = (abs(float(delta))/float(th)) * 1000000
        mass_errors.append([error])
    rdr.close()   
    csvWriter = csv.writer(open(outputfilename, 'wb'), delimiter=',', quotechar='|')
    print mass_errors
    csvWriter.writerows(mass_errors)    
    
def add_quant_flag_to_xls(filename):
    '''

    Input = multiplierz xls sheet
    Adds 'Quant' column
    Needs spectrum desc with original quant data,
    
    '''    
    counter = 0
    rdr = mzR.reader(filename)
    wtr = mzR.writer(filename, columns=rdr.columns + ['Quant'], sheet_name="Data")
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        spec = row['Spectrum Description']
        flag = True if spec.split('|')[18] == 'YES' else False
        row['Quant'] = flag
        wtr.write(row)
    rdr.close()
    wtr.close()
    
def make_iTRAQ_plot(filename, reps):
    '''
    
    Reps = ['c119', 'c121']
    
    
    '''
    
    spec_list = []
    all_reps = [ 'Summed ' + str(x) for x in range(113,120)] + ['Summed 121']

    def check_flag(current_reps):
        flag = False
        min_rep = min(current_reps)
        occurances = 0
        for member in current_reps:
            if member == min_rep:
                occurances += 1
        if occurances > 1:
            flag = True
            #print "Exclude"
        return flag
    
    counter = 0
    print "READING..."
    rdr = mzR.reader(filename)
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1        
        current_reps = [row[x] for x in all_reps]
        result = check_flag(current_reps)
        if result == False:
            entry=(row[reps[0]],row[reps[1]])
            spec_list.append(entry)
    print "Done."
    
    points = []
    print "Gathering points..."
    for member in spec_list:
        if member[0] != 0 and member[1] != 0:
            ln_gm_reps = math.log(math.sqrt(member[0] * member[1]))
            ratio = math.log(float(member[0])/float(member[1]))
            points.append([ratio, ln_gm_reps])
    
    logIntens, logRatios = zip(*points)
        
    #--------------------------------MAIN GRAPH
    xmin = min(logRatios)
    xmax = max(logRatios)
    ymin = min(logIntens)
    ymax = max(logIntens)
    
    pylab.axis([xmin, xmax, ymin, ymax])
    #print points
    print "Graphing..."
    for member in points:
        pylab.plot(member[1], member[0], marker='o', markersize=2, color='blue')
    
    #pylab.plot(3.5, 0)
    pylab.axis([xmin, xmax, ymin, ymax])
    
    pylab.title('iTRAQ ratios ')
    pylab.xlabel('Ln Geo Mean Intensity')
    pylab.ylabel('Ln Ratio (' + reps[0][1:] + '\\' + reps[1][1:] + ')')
    
    pylab.axhline(y=0, linewidth = 1, color = 'b')
    pylab.axhline(y=.693, linewidth = 1, color = 'r')
    pylab.axhline(y=-.693, linewidth = 1, color = 'r')
    print "Saving..."
    pylab.savefig(os.path.dirname(filename) + '\\iTRAQ_plot_' + reps[0][1:] + '_' + reps[1][1:] + '.png')


