__author__ = 'Scott Ficarro, William Max Alexander'
__version__ = '0.9.9'

#----------------------------------------------------------------------------------------------------------------------
# WELCOME to mzStudio!
#----------------------------------------------------------------------------------------------------------------------


import wx, os

global installdir
installdir = os.path.abspath(os.path.dirname(__file__))
try:
    dirName = os.path.dirname(os.path.abspath(__file__))
except:
    dirName = os.path.dirname(os.path.abspath(sys.argv[0]))


if __name__ == '__main__':
    app = wx.App(False)    
    
    ID_Dict = {}
    
    bitmapDir = os.path.join(dirName, 'bitmaps')
    
    img = wx.Image(os.path.join(bitmapDir, "SplashScreen.png"), wx.BITMAP_TYPE_PNG)
    bmp=img.ConvertToBitmap()
    wx.SplashScreen(bmp, wx.SPLASH_CENTER_ON_SCREEN|wx.SPLASH_TIMEOUT, 1000, None, -1)
    wx.Yield()

try:
    import wxversion
    wxversion.select("3.0")
except:
    pass

import wx

if wx.__version__[0] != '3':
    print "WARNING- wxPython version %s may not be fully supported.  Please install wxPython 3." % wx.__version__


#-----------------SYSTEM IMPORTS                      
import os, re, sys, cPickle, platform, time, thread, csv, gc
from collections import defaultdict
from tempfile import mkdtemp
from random import seed
seed(1)
import math



#-----------------mzStudio IMPORTS
import ObjectOrganizer
import Filter_management as fm
import BlaisPepCalcSlim_aui2 as BlaisPepCalc2
import DatabaseOperations as db
import Peptigram
import QueryBuilder
import XICPalette
#import SpecBase
#-----------------------------------
import SpecBase_aui3
import AreaWindow
import Settings
import MGrid
import FeatureImport

from additions import floatrange

import BlaisPepCalcSlim_aui2
from customProcessing import ProcessorDialog
from textSpectrum import TextSpectrumDialog
import FeaturePopUp_new
import LabelCoverage
import dbFrame
import xls_extensions
import miniCHNOPS
import AdjustableProgress as AdjProg
import FeaturePopUp
import mgf
import SpecObject
import XICObject
#-----------------mzWorkbench
import mz_workbench.mz_core as mz_core
import mz_workbench.mz_masses as mz_masses

#-----------------multiplierz
import multiplierz.mzAPI as mzAPI
import multiplierz.mzReport as mzReport
from multiplierz.mgf import standard_title_parse, write_mgf
from multiplierz.spectral_process import centroid as mz_centroid
import mzGUI_standalone as mzGUI
import multiplierz.mzSearch.mascot as mascot
import multiplierz.mzTools.featureDetector as featureDetector
import multiplierz.mzTools.featureUtilities as featureUtilities
from multiplierz.mzTools.featureDetector import Feature

#----------------wxWidgets
import wx.lib.agw.aui as aui
import Progressgauge as pg
import wx.grid
import wx.lib.throbber as  throb

import sqlite3

#def sizeiter(thing, seen):
    #try:
        #thinghash = hash(thing)
    #except TypeError:
        #thinghash = len(seen)
        
    #if thinghash in seen:
        #return ('CIRCULARITY %s' % thinghash, 0)
    #s = sys.getsizeof(thing)
    #seenp = seen.copy()
    #seenp.add(thinghash)
    ##info = {thinghash: [(type(thing), s)]}
    #subinfo = [(thinghash, s)]
    #try:
        #len(thing)
        #if isinstance(thing, dict) or isinstance(thing, defaultdict):
            #iters = thing.values()
        #else:
            #iters = thing
        #for subthing in iters:
            #if isinstance(subthing, basestring):
                #subinfo.append((subthing[:50], sys.getsizeof(subthing)))
            #else:
                #subinfo.append(sizeiter(subthing, seenp))
    #except TypeError as err:
        #if hasattr(thing, '__iter__'): raise err
        #pass
    
    #hashes, sizes = zip(*subinfo)
    
    #info = (hashes, sum(sizes))
    
    #return info
           

def sizeprobe(thing, seen = None):
    if type(thing) == type(sys):
        return 0    
    if isinstance(thing, file):
        return 0
    if not seen:
        seen = set()
        
    try:
        label = hash(thing)
    except TypeError:
        label = id(thing)
    if label in seen:
        return 0
    else:
        seen = seen.copy()
        seen.add(label)
        
    s = sys.getsizeof(thing)
    try:
        if hasattr(thing, '__dict__'):
            iters = thing.__dict__.values()
        elif isinstance(thing, dict) or isinstance(thing, defaultdict):
            iters = thing.values()
        else:
            iters = thing
        for subthing in iters:
            s += sizeprobe(subthing, seen)
    except (TypeError, AttributeError) as err:
        if hasattr(thing, '__iter__'): raise err
        pass        
    
    return s

try:
    from agw import pygauge as PG
except ImportError: # if it's not there locally, try the wxPython lib.
    try:
        import wx.lib.agw.pygauge as PG
    except:
        raise Exception("mzStudio requires wxPython version greater than 2.9.0.0")
try:
    from agw import pyprogress as PP
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.pyprogress as PP
try:
    from agw import pybusyinfo as PBI
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.pybusyinfo as PBI
import wx.lib.mixins.gridlabelrenderer as glr
import wx.grid as grid

#-----------------Globals
global images 
USE_BUFFERED_DC = True

TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            )

class XICLabel:
    '''
    
    Is this class actually used?
    
    '''
    def __init__(self, time, scan, label, xic, cg=None, varmod=None, fixedmod=None, score=None):
        self.time = time
        self.scan = scan
        self.label = label
        self.xic = xic
        self.cg = cg
        self.varmod=varmod
        self.fixedmod = fixedmod
        self.score=score
        if xic:
            self.intensity = self.get_nearest_intensity(self.xic, time)
        else:
            self.intensity = None
        
    def get_nearest_intensity(self, xic, time):
        inten = None
        for i, member in enumerate(xic):
            if member[0] > time:
                index = i - 1
                inten = xic[index][1]
                break
        if not inten:
            inten = 0
        return inten    

class ScanDictThread:
    '''
    
    wx.Delayed Result - allows making ScanDict in a separate thread to keep GUI responsive.
    
    '''
    def __init__(self, m, start, stop):
        self.m = m
        self.start = start
        self.stop = stop
        self.scan_dict = None
        self.rt_dict = None
        self.filter_dict = None
        self.rt2scan = None
        
    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())
    
    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        print "Building Scan Dicts (Thread)"
        
        try:
            self.scan_dict, self.rt_dict, self.filter_dict, self.rt2scan = mz_core.create_dicts(self.m, start=self.start, stop=self.stop)
        except Exception as err:
            self.running = False
            raise err
        
        print "Done"
           
        self.running = False    
    
class XICThread:
    '''
        
    wx.Delayed Result - allows making XIC in a separate thread to keep GUI responsive.
    
    '''    
    def __init__(self, win, m, start_time, stop_time, start_mz, stop_mz, filter=''):
        self.win = win
        self.start_time = start_time
        self.stop_time = stop_time
        self.start_mz = start_mz
        self.stop_mz = stop_mz
        self.m = m
        self.result = None
        self.filter = filter.strip()

    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        print "Making XIC (Thread)"
        try:
            self.result = self.m.xic(self.start_time, self.stop_time, self.start_mz, self.stop_mz, self.filter)
        except Exception as err:
            print err
            print "XIC errror!"
            pass
        print "Done"
        self.running = False



class MS_Data_Manager():
    
    '''
    
    The MS Data manager is the main class that holds all the files currently being analyzed within a single notebook tab.
    
    Each tab holds a new instance.
    
    '''
    
    def __init__(self, parent=None):
        #assert isinstance(parent, DrawPanel)
        self.parent = parent
        self.files = {}
        self.isotope_labels=[]
        self.isotope_dict={}
        self.cf=[]
        self.cf_dict={}
        self.Display_ID = {}
        self.mass_extract = re.compile('.*?\[(\d+?.\d+?)-(\d+?.\d+?)\]')
        
        #-------------------------------------------------------------------------------------------------------------------
        #     FILTER LAND
        # Instructions for adding filter.
        # 1) Define regex.
        # 2) Add regex to the appropriate instrument bundle i.e. self.thermo_filters
        #    This couples to a handler defined in filter management.
        # 3) Add filter managment handler
        # 4) Add entry for title to Mass Dict so first/last mass can be parsed
        #--------------------------------------------------------------------------------------------------------------------
        
        #u'ITMS + p ESI SRM ms2 519.20@cid35.00 [278.50-283.50, 500.50-505.50]'
        self.srm = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI SRM ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?), (\d+?.\d+?)-(\d+?.\d+?)\]')
        self.pa = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI r? ?d Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.lockms2 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI r? ?d? ?Full lock ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')        
        self.etd = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI (t E d sa|d sa|d|r d) Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #self.etd_fusion = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI (t E d sa|d sa) Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #TOF MS p NSI Full ms2 540.032306122@0[100-1400][1375:4]
        self.tofms2 = re.compile('.*?(TOF PI) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #PI + p NSI Full ms [100-1250][50:0]
        self.pi = re.compile('.*?(PI) [+] ([cp]) [NE]SI Full ms2 \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')

        self.mgf = re.compile('.*?MGF ms2 (\d+?.\d+?) \[(\d+?):(\d+?)\] (\d+) *(etd)*')

        self.ms1 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.lockms1 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full lock ms \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.sim_ms1 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI d SIM ms \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #TOF MS + p NSI Full ms [350-1500] TOF MS + p NSI Full ms [10-600]
        self.qms1 = re.compile('.*?(TOF MS) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.qms2 = re.compile('.*?(TOF MS|TOF PI) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@\d+?.\d+? \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        #EPI + p NSI Full ms2 584.70423947@33.622501373291[100-1000][478:3]
        self.epi = re.compile('.*?(EPI) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')#\[(\d+?):(\d+?)\]')
        self.precursor = re.compile('.*?(Precursor) [+] ([cp]) [NE]SI Full ms2 \d+?.\d+?@\d+?.\d+? \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.precursor1 = re.compile('.*?(Precursor) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        #ER MS + p NSI Full ms [0-0]
        self.erms = re.compile('.*?(ER) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.q1ms = re.compile('.*?(Q1) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.q3ms = re.compile('.*?(Q3) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        self.ems = re.compile('.*?(EMS) [+] ([cp]) [NE]SI Full ms \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
        #self.targ = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #self.targ = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI r? ?Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.targ = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI (r|r sa)? ?Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #self.targ_etd = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI r Full ms2 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        #targms3 FTMS + c NSI Full ms3 566.40@cid35.00 792.50@hcd50.00 [100.00-2000.00]
        self.targ_ms3 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI Full ms3 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
        self.dd_ms3 = re.compile('.*?([FI]TMS) [+] ([cp]) [NE]SI k d Full ms3 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')        
        self.active_file = None
        self.svg = defaultdict(list)
        self.mr = re.compile('\[(\d+?[.]?\d*?)[-](\d+?[.]?\d*?)\]')
        
        self.Dms = re.compile(r'(GC|TOF) MS \+ NSI Full (ms[2]?) ((\d+.\d+)@\d+.\d+)?\[(\d+?.*\d*?)-(\d+?.*\d*?)\]')

        self.srm = re.compile(r'(.*SRM.*)')
        
        # TODO:  Add a filter pattern handler for "full lock ms2" scans?
        # Done.

        self.thermo_filters = [[self.ms1, fm.Onms1], [self.lockms1, fm.Onlockms1], 
                               [self.pa, fm.Onpa], [self.lockms2, fm.Onlockms2], [self.targ, fm.Ontarg], [self.etd, fm.Onetd], 
                               [self.targ_ms3, fm.Ontarg_ms3], [self.sim_ms1, fm.Onsim_ms1], 
                               [self.dd_ms3, fm.Ondd_ms3],
                               [self.Dms, fm.OnDms],
                               [self.srm, fm.OnSRM]]
        
        
        self.abi_filters = [[self.qms1, fm.Onqms1], [self.qms2, fm.Onqms2],
                            [self.pi, fm.Onpi], [self.tofms2, fm.Ontofms2], [self.erms, fm.Onerms],
                            [self.precursor, fm.Onprecursor], [self.precursor1, fm.Onprecursor],
                            [self.epi, fm.Onepi], [self.q3ms, fm.Onq3ms], [self.q1ms, fm.Onq3ms],
                            [self.ems, fm.Onems]]
        self.mgf_filters = [[self.mgf, fm.Onmgf]]
        
        # MASS DICT corresponds to the x in .groups()[x] where x gives back first and last mass
        self.mass_dict = {"Thermo_ms2":[self.pa, 5,6],
                          "Thermo_lock_ms2":[self.lockms2, 5,6],
                              "Thermo_ms1":[self.ms1, 2,3],
                              "Thermo_lock_ms1":[self.lockms1, 2, 3],
                              "Thermo_targ_ms2":[self.targ, 6,7], #"Thermo_targ_ms2":[self.targ, 5,6],
                              "Thermo_targ_ms3":[self.targ_ms3, 8,9],
                              "Thermo_dd_ms3":[self.dd_ms3, 8,9],
                              "MGF_ms2":[self.mgf, 1, 2],
                              "ABI_pi":[self.pi, 2, 3],
                              "ABI_ms2":[self.tofms2, 5,6],
                              "ABI_qms2":[self.qms2, 3, 4],
                              "ABI_ms1":[self.qms1, 2,3],
                              "ABI_q1ms":[self.q1ms, 2, 3],
                              "ABI_q3ms":[self.q3ms, 2,3],
                              "ABI_ems":[self.ems, 2,3],
                              "ABI_precursor":[self.precursor, 2,3],
                              "ABI_epi":[self.epi, 4,5],
                              "ABI_er":[self.erms, 2,3],
                              "Thermo_etd":[self.etd, 6,7],
                              "Thermo_sim_ms1":[self.sim_ms1,2,3],
                              "Agilent":[self.Dms, 4, 5],
                              "Thermo LTQ SRM":[self.srm, 5,8]}
        #svg.Blit(0,0,size.width,size.height,dc,0,0)

    def Match_Filter(self, filt, inst):
        match_filter = None 
        match_handler = None
        if inst == 'Thermo':
            for ms_filter, handler in self.thermo_filters:
                id = ms_filter.match(filt)
                if id:
                    match_filter = ms_filter
                    match_handler = handler
                    break
        return match_filter, match_handler
                
    def Create_Filter_Info(self, filt, inst):
        filter_dict = {}
        if inst == 'Thermo':
            for ms_filter, handler in self.thermo_filters + self.abi_filters:
                id = ms_filter.match(filt)
                if id:
                    filter_dict = handler(filter_dict, id)
                    break
        
        if inst == 'mgf':
            for ms_filter, handler in self.mgf_filters:
                id = ms_filter.match(filt)
                if id:
                    filter_dict = handler(filter_dict, id)
                    break      
                else:
                    wx.MessageBox("Could not parse MGF.")
                    raise ValueError("wrong format")
                
        elif inst == 'ABI-MALDI':
            print filt
            if filt.upper().find("_MS_") > -1 or filt.upper().find("_LINEAR_") >-1 or filt.upper().find("_LINEAR.") >-1 or filt.upper().find("_MS.") > -1:
                filter_dict['mode'] = "ms1"
                filter_dict['analyzer'] = 'TOF'
                filter_dict['data']="+cent"
                filter_dict["mr"]='[' + filt.split('|')[1].split(",")[0].strip() + '-' + filt.split('|')[1].split(",")[1].strip() + ']'
            else:
                filter_dict['mode'] = "ms2"
                filter_dict['analyzer'] = 'TOF MS2'
                filter_dict['precursor']=str(float(filt.split("_")[2]))
                filter_dict['data']="+cent"
                filter_dict['reaction']="TOF MS2"
                filter_dict["mr"]='[' + filt.split('|')[1].split(",")[0].strip() + '-' + filt.split('|')[1].split(",")[1].strip() + ']'
                filter_dict["energy"]="TOF-TOF"
            print filter_dict
        
        assert filter_dict, filt
        return filter_dict

    def getFileNum(self):
        return len(self.files.keys())

    def getActiveList(self):
        file_list = []
        for i in range(0, self.getFileNum()):
            if self.files[self.Display_ID[i]]["Display"]:
                file_list.append(i)
        return file_list

    def getDisplayWindows(self):
        counter = 0
        for i, key in enumerate(self.files.keys()):
            if self.files[key]["Display"]==True:
                counter += 1
        return counter

    def getNextActiveWindow(self, current, direction):
        next = None
        go = True
        counter = current
        if direction.lower() == "forward":
            while go:
                counter += 1
                if self.files[self.Display_ID[counter]]["Display"]==True:
                    go = False
                    next = counter
                if counter == self.getFileNum() - 1:
                    go = False
        elif direction.lower() == "reverse":
            while go:
                counter -= 1
                if self.files[self.Display_ID[counter]]["Display"]==True:
                    go = False
                    next = counter
                if counter == 0:
                    go = False
        return counter

    def set_mass_ranges(self, filename):
        if not self.files[filename]['Processing']:
            vendor = self.files[filename]["vendor"]
            if vendor != "ABI-MALDI":
                if not self.files[filename]["locked"]:
                    found = False
                    for member in self.mass_dict.keys():
                        pa = self.mass_dict[member][0]
                        if vendor == "Thermo":
                            
                            lookup = self.files[filename]["scanNum"]
                            
                            #lookup = int(self.files[filename]["scanNum"].split('-')[0])
                        if vendor == "mgf":
                            lookup = self.files[filename]["scanNum"]    #self.files[filename]["mgf_rev_dict"][    
                            if lookup not in self.files[filename]["filter_dict"].keys():
                                lookup = self.files[filename]["mgf_scan_dict"][self.files[filename]["scanNum"]]
                        if vendor == "ABI":
                            lookup = (self.files[filename]["scanNum"],self.files[filename]["experiment"])
                        if self.files[filename]['spectrum_style']=='single scan':
                            id = pa.match(self.files[filename]["filter_dict"][lookup])
                            if id:
                                low_mass = id.groups()[self.mass_dict[member][1]]
                                hi_mass = id.groups()[self.mass_dict[member][2]]
                                found = True
                                break
                        else: #AVERAGE SCAN
                            low_mass = self.files[filename]['average_mass_range'][0]
                            hi_mass = self.files[filename]['average_mass_range'][1]
                            found = True
                    if not found:
                        #raise ValueError("Filter not parsed!  Unrecognized file format!")
                        low_mass = 100.0
                        hi_mass = 101.0
                #else:
                #    low_mass = self.files[filename]["newl"]
                #    hi_mass = self.files[filename]['newf']
                    self.files[filename]["scan low mass"]=float(low_mass)
                    self.files[filename]["scan high mass"]=float(hi_mass)
                    self.files[filename]["mass_ranges"]=[(float(low_mass), float(hi_mass))]
            else: #--------------MALDI DATA
                self.files[filename]["scan low mass"]=self.files[filename]["m"].info()['Range'][0]
                self.files[filename]["scan high mass"]=self.files[filename]["m"].info()['Range'][1]
                self.files[filename]["mass_ranges"]=[self.files[filename]["m"].info()['Range']]
        else: #------------------PROCESSED SCAN
            self.files[filename]["scan low mass"]=float(self.files[filename]['processed_first'])
            self.files[filename]["scan high mass"]=float(self.files[filename]['processed_last'])
            self.files[filename]["mass_ranges"]=[(float(self.files[filename]['processed_first']), float(self.files[filename]['processed_last']))]        
            
    def _set_mass_ranges(self, filename):
        #Changes broke mass range lock.  Reverted to old code.
        if not self.files[filename]['Processing']:
            vendor = self.files[filename]["vendor"]
            if vendor != "ABI-MALDI":
                if not self.files[filename]["locked"]:
                    found = False
                    for member in self.mass_dict.keys():
                        pa = self.mass_dict[member][0]
                        if vendor == "Thermo":
                            lookup = self.files[filename]["scanNum"]
                        if vendor == "mgf":
                            lookup = self.files[filename]["scanNum"]    #self.files[filename]["mgf_rev_dict"][    
                            if lookup not in self.files[filename]["filter_dict"].keys():
                                lookup = self.files[filename]["scan_dict"][self.files[filename]["scanNum"]]
                        if vendor == "ABI":
                            lookup = (self.files[filename]["scanNum"],self.files[filename]["experiment"])
                        id = pa.match(self.files[filename]["filter_dict"][lookup])
                        if id:
                            low_mass = id.groups()[self.mass_dict[member][1]]
                            hi_mass = id.groups()[self.mass_dict[member][2]]
                            found = True
                            break
                    if not found:
                        #raise ValueError("Filter not parsed!  Unrecognized file format!")
                        low_mass = 100.0
                        hi_mass = 101.0
                    # If I understand the above, it can be done with a single more general regex.
#------------------------------------------------------------------------
                #filterstr = self.files[filename]["filter_dict"][self.files[filename]["scanNum"]]
                #mass_find = re.search('\[(\d+?.*\d*?)-(\d+?.*\d*?)\]', filterstr)
                #if mass_find:
                    #lowmass, highmass = map(float, mass_find.groups())
                #else:
                    #lowmass, highmass = 10, 2000
                #self.files[filename]["scan low mass"] = lowmass
                #self.files[filename]["scan high mass"] = highmass
                #self.files[filename]["mass_ranges"]= [(lowmass, highmass)]
#--------------------------------------------------------------------
                else:
                    low_mass = self.files[filename]["newl"]
                    hi_mass = self.files[filename]['newf']
                    self.files[filename]["scan low mass"]=float(low_mass)
                    self.files[filename]["scan high mass"]=float(hi_mass)
                    self.files[filename]["mass_ranges"]=[(float(low_mass), float(hi_mass))]
            else:
                self.files[filename]["scan low mass"]=self.files[filename]["m"].info()['Range'][0]
                self.files[filename]["scan high mass"]=self.files[filename]["m"].info()['Range'][1]
                self.files[filename]["mass_ranges"]=[self.files[filename]["m"].info()['Range']]
        else:
            self.files[filename]["scan low mass"]=float(self.files[filename]['processed_first'])
            self.files[filename]["scan high mass"]=float(self.files[filename]['processed_last'])
            self.files[filename]["mass_ranges"]=[(float(self.files[filename]['processed_first']), float(self.files[filename]['processed_last']))]            
    
    def GetHiMass(self, filename):
        return max(t[0] for t in self.files[filename]["scan"])

    def GetLoMass(self, filename):
        return min(t[0] for t in self.files[filename]["scan"])

    def GetMaxInt(self, fm, lm, filename):
        if not self.files[filename]["Processing"]:
            sub_scan = []
            for member in self.files[filename]["scan"]:
                if member[0]>=fm and member[0]<=lm:
                    sub_scan.append(member)
            try:
                return max(t[1] for t in sub_scan)
            except:
                return 0
        else:
            sub_scan = []
            for member in self.files[filename]["processed_data"]:
                if member[0]>=fm and member[0]<=lm:
                    sub_scan.append(member)
            try:
                return max(t[1] for t in sub_scan)
            except:
                return 0            
        
    def GetMaxIntScanData(self, fm, lm, filename, scan_data):
            sub_scan = []
            for member in scan_data:
                if member[0]>=fm and member[0]<=lm:
                    sub_scan.append(member)
            try:
                return max(t[1] for t in sub_scan)
            except:
                return 0    

    def GetMaxSignal(self, startTime, stopTime, key, filename, xic):
        sub_xic = []
        for member in self.files[filename]["xic"][key][xic]:
            if member[0]>=startTime and member[0]<=stopTime:
                sub_xic.append(member)
        try:
            return max(t[1] for t in sub_xic)
        except:
            return 0

    def GetScanDicts(self, m, start, stop):
        self.parent.parent.StartGauge(text="Building Scan Dictionaries...", color=wx.BLUE)
        t = ScanDictThread(m, start, stop)
        
        #print "NONTHREAD MODE"
        #t.Run()    
    
        # "Threaded mode"
        try:
            t.Start()
            while t.IsRunning():
                time.sleep(0.1)
                wx.Yield()
        except sqlite3.ProgrammingError:
            t.Run()        
            
        scan_dict = t.scan_dict
        rt_dict = t.rt_dict
        rt2scan = t.rt2scan
        filter_dict = t.filter_dict
        del t

        self.parent.parent.StopGauge() 
        return scan_dict, rt_dict, filter_dict, rt2scan        

    def GetAnXIC(self, win, m, params, filter_dict={}, rt2scan={}):
        '''
        
        Version 0.2 2017-07-04.
        For thermo files, the "filter" is processed within the XIC function of the COM object.
        For Agilent and ABSciex files, the XIC is first obtained, and then 'filtered' using a list comprehension.
        
        '''
        self.parent.parent.StartGauge(text="Building XIC...")
        _filter = ''
        #self.parent.parent.Parent.StartGauge(text="Building XIC...")
        params = list(params)
        if params[2] > params[3]:    
            params[2], params[3] = params[3], params[2]
        if 'SRM' in m.filters()[0][1]:
            params[-1] = 'SRM ms2'
        if m.file_type == '.d' or m.file_type == 'wiff':
            _filter = params[-1]
            params[-1] = 'Full ms' # Just to keep D.py happy.
        params = tuple(params)
        
        t = XICThread(win, m, *params)
        t.Start()
        while t.IsRunning():
            time.sleep(0.1)
            wx.Yield()
        result = t.result
        del t
        if not result:
            print "Threading failed, performing in-thread XIC."
            result = m.xic(*params)
        assert result
        
        self.parent.parent.StopGauge()
        if m.file_type != '.d' and (m.file_type != 'wiff' and 'Full ms' not in _filter):
            return result
        else:
            #Here is where the manual filtering is performed.
            #result = [j for j in result if filter_dict[rt2scan[j[0]]].find(_filter) > -1]
            result = [j for i, j in enumerate(result) if _filter in filter_dict[i]]
            return result



    def old_LoadSettings(self, current):
        '''
        
        Loads mzBrowzer settings file.
        
        '''
        settings = {}
        file_r = open(os.path.join(installdir, r'settings\settings.txt'), 'r')
        data = file_r.readlines()
        file_r.close()
        conv_int=['max_cg', 'min_cg', 'Thermo', 'ABI', 'ABI-MALDI', 'mgf','peak_min', 'threshold_cent_abi', 'space', 'inter_raw_space', 'y_marg', 'total_xic_height', 'total_spec_height', 'inter_axis_factor', 'inter_axis_space', 'spec_indent', 'spec_width', 'ric_spec_indent', 'ric_spec_width', 'inter_xic_space']     
        
        conv_float=['step_length','line width']
        for member in data:
            entry = member.split('\t')
            if len(entry)==2:
                entry[1]=entry[1].strip()
                if entry[1]=='False':
                    entry[1] = False
                elif entry[1]=='True':
                    entry[1] = True
                current[entry[0].strip()]=entry[1]
                settings[entry[0].strip()]=entry[1]
            elif len(entry)==3:
                entry[2]=entry[2].strip()
                if entry[2]=='False':
                    entry[2] = False
                elif entry[2]=='True':
                    entry[2] = True 
                try:
                    current[entry[0].strip()][entry[1].strip()]=entry[2]
                except:
                    current[entry[0].strip()] = {}
                    current[entry[0].strip()][entry[1].strip()]=entry[2]
                try:
                    settings[entry[0].strip()][entry[1]]=entry[2]      
                except:
                    settings[entry[0].strip()] = {}
                    settings[entry[0].strip()][entry[1]]=entry[2] 
                    
        for key in settings.keys():
            try:
                if settings[key].find('wx.')>-1:
                    settings[key] = eval(settings[key])
                    current[key] = eval(settings[key])
            except:
                pass
            try:
                if settings[key].find(',')>-1: #convert to list
                    settings[key] = [int(x) for x in settings[key].split(',')]
                    current[key] = [int(x) for x in settings[key].split(',')]
            except:
                pass
            if key in conv_int:
                settings[key] = int(settings[key])
                current[key] = int(settings[key])
            if key in conv_float:
                settings[key] = float(settings[key])
                current[key] = float(settings[key])                
            if type(settings[key])==dict:
                for subkey in settings[key]:
                    if settings[key][subkey].find('wx.')>-1:
                        settings[key][subkey] = eval(settings[key][subkey])
                        current[key][subkey] = eval(settings[key][subkey])   
                    if settings[key][subkey].find(',')>-1: #convert to list
                        settings[key][subkey] = [int(x) for x in settings[key][subkey].split(',')]
                        current[key][subkey] = [int(x) for x in settings[key][subkey].split(',')]                      
                    if subkey in conv_int:
                        settings[key][subkey] = int(settings[key][subkey])
                        current[key][subkey] = int(settings[key][subkey])  
                    if subkey in conv_float:
                        settings[key][subkey] = float(settings[key][subkey])
                        current[key][subkey] = float(settings[key][subkey])                    
        
        #wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False)
        #maintext	BLACK
        #mainfont	size	10
        #mainfont	font	ROMAN
        #mainfont	style	NORMAL
        #mainfont	weight	BOLD
        settings['font1'] = eval('wx.Font('+str(settings['mainfont']['size'])+', wx.' + settings['mainfont']['font'] + ', wx.' + settings['mainfont']['style']+', wx.' + settings['mainfont']['weight']+', False)')
        print settings        
        return settings

    def LoadSettings(self, current):
        settings = defaultdict(dict)
        settings_data = open(os.path.join(installdir, r'settings\settings.txt'), 'r')
        
        def interpret_val(val):
            if val.strip() in ['True', 'False']:
                return val.strip() == 'True'
            else:
                try: return int(val)
                except ValueError:
                    try: return float(val)
                    except ValueError:
                        return val.strip()
        
        for line in settings_data:
            words = line.split('\t')
            if len(words) == 2:
                key, val = words
                settings[key] = interpret_val(val)
            elif len(words) == 3:
                fkey, skey, val = words
                settings[fkey][skey] = interpret_val(val)
    
        settings['line color'] = [int(x) for x in settings['line color'].strip('[]').split(',')]
            
        for key, val in settings.items():
            if isinstance(val, dict):
                if key not in current:
                    current[key] = val
                else:
                    for subkey, subval in val.items():
                        current[key][subkey] = subval
            else:
                current[key] = val
        
        #Set Font
        settings['font1'] = eval('wx.Font('+str(settings['mainfont']['size'])+
                                 ', wx.' + settings['mainfont']['font'] + 
                                 ', wx.' + settings['mainfont']['style']+
                                 ', wx.' + settings['mainfont']['weight']+', False)')        
        
        return dict(settings)
    # Note that 'line color' gets eval()'d into a list, and
    # should therefore be parsable as such.  May want to enforce
    # this somewhere.
    def SaveSettings(self, current):
        saveKeys = [['viewCentroid'],
                    ['max_cg'],
                    ['min_cg'],
                    ['MALDIServer'],
                    ['label_res'],
                    ['label_threshold', 'Thermo'],
                    ['label_threshold', 'ABI'],
                    ['label_threshold', 'ABI-MALDI'],
                    ['label_threshold', 'mgf'],
                    ['maintext'],
                    ['mainfont', 'size'],
                    ['mainfont', 'font'],
                    ['mainfont', 'style'],
                    ['mainfont', 'weight'],
                    ['mainfont', 'face'],
                    ['mainfont', 'color'],
                    ['abi_centroid'],
                    ['eliminate_noise'],
                    ['step_length'],
                    ['peak_min'],
                    ['threshold_cent_abi'],
                    ['line color'],
                    ['line width'],
                    ['space'],
                    ['inter_raw_space'],
                    ['y_marg'],
                    ['total_xic_height'],
                    ['total_spec_height'],
                    ['inter_axis_factor'],
                    ['inter_xic_space'],
                    ['spec_indent'],
                    ['spec_width'],
                    ['ric_spec_indent'],
                    ['ric_spec_width'],
                    ['auto_resize'],
                    ['drawCentroid'],
                    ['xic_titles'],
                    ['searchAlgorithm'],
                    ['labelPeaks'],
                    ['multiFileOption'],
                    ['ionLabelThresh']]
        settingsfile = open(os.path.join(installdir, r'settings\settings.txt'), 'w')
        settings = current['settings']
        
        for keys in saveKeys:
            if len(keys) == 1:
                settingsfile.write('%s\t%s\n' % (keys[0], settings[keys[0]]))
            elif len(keys) == 2:
                settingsfile.write('%s\t%s\t%s\n' % (keys[0], keys[1],
                                                     settings[keys[0]][keys[1]]))
        settingsfile.close()
        
        
        

    def addFile(self,filename):
        '''        
        
        msdb.Display_ID is a dictionary of file display order to filename i.e. [0], or the first file to display, mapped to its filename.
        
        msdb.files[filename] is the dictionary containing all info about all files in the bank
        
        '''
        
        filename = filename.lower()
        gc.collect()
        
        display_key = self.getFileNum()
        self.Display_ID[display_key]=filename
        current = {}
        
        #---------------------EVALUATE VENDOR
        vendor = None
        if filename.lower().endswith(".raw") or filename.lower().endswith('.d') or filename.lower().endswith('mzml'):
            vendor = "Thermo"
        elif filename.lower().endswith(".wiff"):
            vendor = "ABI"
        elif filename.lower().endswith('.t2d'):
            vendor = "ABI-MALDI"
        elif filename.lower().endswith(".mgf"):
            vendor = "mgf"        
        current["vendor"] = vendor
        
        #current['multiFileOption'] = 'SEQUENTIAL' # SHOULD BE EITHER SEQUENTIAL, OR LOAD ALL.  For multifile searches. # NOW IN SETTINGS FILE
        #current['multiFileOption'] = 'LOAD ALL' 
        current["processed_data"] = None #-----Holds a processed scan for custom processing scripts
        current['processed_first'] = 100
        current['processed_last']=101
        current["spectrum_style"] = "single scan" # "single scan" or "average"
        current["features"] = False
        
        #-----------FOR SPECTRUM AVERAGING
        current["average_data"] = None
        current['average_range']=[]
        current['average_scan_range']=[]
        
        current["max_int"]={}
        current['intensity_scaling']=0
        current['labelThreshOverride']=0.5
        current['filterLock']=None # IF filter locked, when +/- through data will skip to the next scan with this filter
        current['score']=None # Database search score if there is an ID with this scan
        current['label_non_id']=True
        current['NL_ions']={}
        current['precNL_ions']={}
        current['errorFlag']=True #Display ppm error if accurate mass instrument
        current['currently_selected_filter']=None
        current['XICinfo']=None
        current["FileAbs"] = filename
        current["FeatureBoxes"] = []
        current["Filename"] = os.path.basename(filename)
        current["ID"] = False #Is the current scan identified
        current["img"] = None #Bitmap to be stored if command issued
        current["fixedmod"] = ""  #,iTRAQ4plex (K),iTRAQ4plex (N-term)
        current["header"] = {}
        current["mascot_ID"] = {}
        current["mode"] = "RIC-SPEC"
        current["ID_Dict"] = {}
        current["SILAC"]={"mode":False, "peaks":(), "method":None} 
        current["scanNum"] = 1
        current["datLink"] = False
        current["xic_style"] = 'NEWTRACE'
        current["viewMascot"] = False
        #current["viewCentroid"] = False
        current["settings"] = self.LoadSettings(current)
        current["locked"] = False
        current["mzSheetcols"] = []
        current["postup"] = (0,0) #temp position tuple
        #current["filters"] =[[""]]
        current["xic_title"]=[["TIC"]]
        current["rows"] = []
        current["overlay"]={}
        current["combo"] = []
        current["database"]=None
        current["Display"]=True
        current["SearchType"]=None
        current["axes"] = 1
        current["newf"] = 0
        current["newl"] = 0
        current["new_stopTime"] = 0
        current["new_startTime"] = 0
        current['Processing'] = None
        current['is_zooming'] = False
        current['processed_data'] = []
        current['unprocessed_data'] = []
        #print vendor
        t1 = time.time()
        if vendor == "Thermo":
            if filename.lower().endswith('.d'): busy = PBI.PyBusyInfo("Loading agilent File...", parent=None, title="Building Scan dictionary...")
            current["m"] = mzAPI.mzFile(filename, compatible_mode = True)
            if filename.lower().endswith('.d'): del busy
        elif vendor == 'mgf':
            current["m"] = mgf.mzFile(filename)
        elif vendor == "ABI":
            busy = PBI.PyBusyInfo("Loading wiff File...", parent=None, title="Building Scan dictionary...")
            current["m"] = mzAPI.mzFile(filename, compatible_mode = True)
            del busy
            vendor = "Thermo"
            current["vendor"] = "Thermo"  #Vendor is really ABI of course, but mzAPI structures wiff files like raw.
            
        elif vendor == "ABI-MALDI":
            '''
            m.info()
            {'Precursor': None, 'Range': (600.0, 5014.0), 'Collision Energy': -1.0, 'MS Level': 1}

            
            '''
            current['scanNum']=1
            current['mark_boxes'] = []
            current['filter_dict']={}
            current['m']=mzAPI.mzFile(filename)
            #current['m'].open_file(filename)
            current["mode"] = "SPEC"
            current["scan"] = current['m'].scan()
            current["label_dict"] = {}
            current["xic_labels"] = []
            current["found2theor"] = {}            
            current["svg"] = defaultdict(list)
            self.files[filename] = current
            self.files[filename]["scan low mass"]=current["m"].info()['Range'][0]
            self.files[filename]["scan high mass"]=current["m"].info()['Range'][1]
            self.files[filename]["mass_ranges"]=[current['m'].info()['Range']]
            self.set_axes()
            self.files[filename]["unzF"] = self.files[filename]["scan low mass"]
            self.files[filename]["unzL"] = self.files[filename]["scan high mass"]
            self.files[filename]["fm"] = self.files[filename]["scan low mass"]
            self.files[filename]["lm"] = self.files[filename]["scan high mass"]         
            self.files[filename]['filter_dict'][None]=' + p MALDI TOF: ' + current['Filename'] + '|' + str(self.files[filename]["scan low mass"]) + ',' + str(self.files[filename]["scan high mass"])
            self.files[filename]['fd'] = self.Create_Filter_Info(self.files[filename]['filter_dict'][None], 'ABI-MALDI')
            #current["scan_range"] = current['m'].info()['Range']
            current["scan_range"] = (None, None)
            self.files[filename]['viewCentroid']=False
            
        if vendor in ['Thermo', 'ABI', 'mgf']:
            #NEED TO ADD scan_range to mzAPI.t2d
            current["scan_range"] = current["m"].scan_range()
        
        current['scanNum'] = current['scan_range'][0]
        
        if current['vendor'] in ['Thermo', 'ABI', 'mgf']:
            dict_file = filename.replace(".raw", '').replace(".wiff", '') + '.dicts'
            if os.path.exists(dict_file) and current['vendor'] != 'mgf':
            #print "Ignoring possible dict file."
            #if False: 
                #pickle_list = [current["m"]._headers, current["m"].precursor_info, current["m"].MS1_data, current["m"].MS1_modes, current["m"].MS2_modes, current["m"].associated_MS2, current["m"].precursor_info]                
                pickle_file = open(dict_file, "r")
                current["scan_dict"] = cPickle.load(pickle_file)
                current["rt_dict"] = cPickle.load(pickle_file)
                current["filter_dict"] = cPickle.load(pickle_file)
                current["rt2scan"] = cPickle.load(pickle_file)
                if current['vendor'] in ['Thermo', 'ABI']:
                    current["m"]._headers = cPickle.load(pickle_file)
                if current["vendor"]=='ABI':
                    current["rt2exp"] = cPickle.load(pickle_file)
                    current["m"].precursor_info = cPickle.load(pickle_file)
                    current["m"].MS1_data = cPickle.load(pickle_file)
                    current["m"].MS1_modes = cPickle.load(pickle_file)
                    current["m"].MS2_modes = cPickle.load(pickle_file)
                    current["m"].associated_MS2 = cPickle.load(pickle_file)
                    current['rt2exp'] = cPickle.load(pickle_file)    
                
                pickle_file.close()
            else:
                #--------------NO DICTIONARY FILE FOUND, MUST CREATE DICTIONARY.
                #--------------THE SCAN DICTIONARY HELPS NAVIGATE A RAW FILE BY ALLOWING QUICK CONVERSION OF
                #--------------SCAN # to RT and vice versa and quick filter lookup.
                if current['vendor']=='Thermo':
                    current["scan_dict"], current["rt_dict"], current["filter_dict"], current["rt2scan"] = self.GetScanDicts(current["m"], start=0, stop=99999)                
                
                if current['vendor']=='mgf':
                    current['scan_dict']=dict([(i, i) for i in range(1, current['m'].scan_number+1)])
                    current["rt_dict"] = current['scan_dict']
                    current['rt2scan']=current['scan_dict']
                    current['filter_dict']=dict(current['m'].filters())
                    try:
                        current['scan_dict'] = dict([(int(x[1].split('] ')[1]), x[0]) for x in current['m'].filters()])
                    except ValueError:
                        current['scan_dict'] = dict([(int(multiplierz.mgf.standard_title_parse(x[1].split('] ')[1])['scan']), x[0]) for x in current['m'].filters()])
                    #current['mgf_rev_dict'] = dict([(x[0], int(x[1].split('] ')[1]) ) for x in current['m'].filters()])
                    current['mgf_rev_dict'] = dict([(v, k) for k, v in current['scan_dict'].items()]) # If you wanna reverse it, just reverse it.  Be honest!
                    
                
                #if current['vendor']=='ABI':
                    #current["scan_dict"], current["rt_dict"], current["filter_dict"], current["rt2scan"] = self.GetScanDicts(current["m"], start=0, stop=99999)
                    #rt2exp = {}
                    #for key in current["rt2scan"].keys():
                        #rt2exp[key[0]]=key[1]
                    #current['rt2exp']=rt2exp
                try:
                    pickle_file = open(dict_file, "w")
                    cPickle.dump(current["scan_dict"], pickle_file)
                    cPickle.dump(current["rt_dict"], pickle_file)
                    cPickle.dump(current["filter_dict"], pickle_file)
                    cPickle.dump(current["rt2scan"], pickle_file)
                    pickle_list = []
                    if current["vendor"]=='ABI':
                        cPickle.dump(current['rt2exp'], pickle_file)
                        pickle_list = [current["m"]._headers, current["m"].precursor_info, current["m"].MS1_data, current["m"].MS1_modes, current["m"].MS2_modes, current["m"].associated_MS2, current['rt2exp']]
                    elif current["vendor"]=='Thermo':
                        pickle_list = [current["m"].headers()]
                    for data in pickle_list:
                        cPickle.dump(data, pickle_file)
                    pickle_file.close()           
                except IOError:
                    print "Could not write dict cache.  Check that you have write permissions to this directory."
            current["ticname"] = filename[:-4]+'.tic'
            
            #--------------------------------------------------------------------------------------
            #  THIS CODE EVALUATES THE TYPE OF DATA FILE for the purposes of displaying a general TIC
            #  as well as the master scan for browsing through the data
            #
            #--------------------------------------------------------------------------------------
            
            t2 = time.time()
            
            minFilterKey = min(current['filter_dict'].keys())
            if vendor in ["Thermo", 'mgf']:
                if current["filter_dict"][minFilterKey].lower().find("full ms2") > -1:
                    current["master_scan"]="ms2"
                    current['master_filter']="Full ms2"
                elif current["filter_dict"][minFilterKey].lower().find("srm ms2") > -1:
                    current["master_scan"]="ms2"
                    current['master_filter']="SRM ms2"                
                elif current["filter_dict"][minFilterKey].lower().find("mgf ms2") > -1:
                    current["master_scan"]="ms2"
                    current['master_filter']="MGF ms2"                
                else:
                    current['master_scan']='ms1'
                    current['master_filter'] = u'Full ms '
                current["filters"] = [[current['master_filter']]]
            
                fd = self.Create_Filter_Info(current["filter_dict"][minFilterKey], vendor)
                id = self.mass_extract.match(fd['mr'])
            
                fm = float(id.groups()[0]) # Might revise encoding scheme
                lm = float(id.groups()[1])
                
            elif vendor == 'ABI':
                pass
                
            if vendor == "Thermo": #MARK_XIC
                current["filter"] = current["filter_dict"][minFilterKey]
                current["xic_params"] = [[(fm, lm, current['master_filter'])]]
                current["xic_mass_ranges"] = [[(fm, lm)]]
                current["xic_scale"] = [[-1]]
                current["xic_type"] = [['x']]
                current["xic_mass"] = [[None]]  
                current["xic_charge"] = [[None]]
                current["xic_sequence"] = [[None]]
                current['xic_scan'] = [[None]]
                current["active_xic"] = [0]
                current["xic_view"] = [[1]]                
                
            elif vendor == 'mgf':
                current['filters'] = [['MGF ms2']] # I think?
                
                current['filter_dict'] = dict(current['m'].filters())
                current["filter"] = current["filter_dict"][minFilterKey]
                fm = self.mgf.match(current['filter']).groups()[1]
                lm = self.mgf.match(current['filter']).groups()[0]
                
                current["xic_params"] = [[(fm, lm, u'Full ms ')]]
                current["xic_mass_ranges"] = [[(fm, lm)]]
                current["xic_scale"] = [[-1]]
                current["xic_type"] = [['x']]
                current["xic_mass"] = [[None]]  
                current["xic_charge"] = [[None]]
                current["xic_sequence"] = [[None]]
                current['xic_scan'] = [[None]]
                current["active_xic"] = [0]
                current["xic_view"] = [[1]] 
                
                current['master_scan'] = 'ms2'
                
            elif vendor == "ABI":
                #a= current["filter_dict"][(1,"0")]
                current["filter"] = current["filter_dict"][(1,"0")]
                
                for filt in [self.qms1, self.erms, self.precursor, self.epi, self.ems, self.q3ms, self.pi]:
                    match = filt.match(current["filter"])
                    if match:
                        fm = float(match.groups()[2])
                        lm = float(match.groups()[3])

                        break
                    
                current["filter"] = current["filter_dict"][(1, "0")]
                current["experiment"] = "0"
                current["xic_params"] = [[(fm, lm, u'Full ms ')]]
                current["xic_mass_ranges"] = [[(fm, lm)]]
                current["xic_scale"] = [[-1]]
                current["xic_view"] = [[1]]
                current["active_xic"] = [0]
                current["xic_params"] = [[(fm, lm, u'Full ms ')]]
                current["xic_type"] = [['x']]
                current["xic_mass"] = [[None]]  
                current["xic_charge"] = [[None]]
                current["xic_sequence"] = [[None]]
                current['xic_scan'] = [[None]]
                                   
            if 'master_filter' in current:
                current["xr"] = [[current["m"].time_range() + (fm, lm, current['master_filter'])]]
            #print current["xr"]
            if os.path.exists(current['ticname']):
                #print "loading xic..."
                pickle_file = open(current["ticname"], "r")
                current["xic"] = cPickle.load(pickle_file)
                pickle_file.close()
            else:
                print "Building xic..."
                   
                if vendor == "Thermo":
                    #--------------FOR TESTING-----------------TEST BLOCK
                    #current["xic"] = [[self.GetAnXIC(self, current["m"], current["xr"][0][0])], [self.GetAnXIC(self, current["m"], current["xr"][1][0]), self.GetAnXIC(self, current["m"], current["xr"][1][1]), self.GetAnXIC(self, current["m"], current["xr"][1][2])], [Peptigram.GetAPeptigram(current, 8353, 913.96900, 2, tolerance=0.02)]]
                    #current["xic_max"] = [[max([x[1] for x in current["xic"][0][0]])], [max([x[1] for x in current["xic"][1][0]]), max([x[1] for x in current["xic"][1][1]]), max([x[1] for x in current["xic"][1][2]])], [max([x[1] for x in current["xic"][2][0]])]]
                    ##current["xic_marks"] = {1:{1:{current["rt_dict"][9187]:"PEPTIDE", current["rt_dict"][4473]:"PEPTIDE"}}}
                    ##current["xic_marks"] = [[{}],[{},{current["rt_dict"][9187]:["PEPTIDE", 9188], current["rt_dict"][4473]:["PEPTIDE", 4474]},{}],[{}]]
                    #current["xic_marks"] = [[{}],[{},{9187:XICLabel(current['m'].timeForScan(9187), 9187, "Peptide", current['xic'][1][1])},{}],[{}]]
                    ##current["xic_marks"] = {1:{1:{current["rt_dict"][9187]:"PEPTIDE", current["rt_dict"][4473]:"PEPTIDE"}}}
                    #current['mark_boxes'] = []
                    #current["xic_dict"] = [[self.make_xic_dict(current['xic'][0][0])], [self.make_xic_dict(current['xic'][1][0]), self.make_xic_dict(current['xic'][1][1]), self.make_xic_dict(current['xic'][1][2])], [self.make_xic_dict(current['xic'][2][0])]]
                    #current['xic_lookup']=[]
                    #---------------------------------------------------------------------------------------------
                    
                    current["xic"] = [[self.GetAnXIC(self, current["m"], current["xr"][0][0], current["filter_dict"], current["rt2scan"])]]
                    current["xic_max"] = [[max([x[1] for x in current["xic"][0][0]])]]
                    current["xic_marks"] = [[{}]]
                    current['mark_boxes'] = []
                    current["xic_dict"] = [[self.make_xic_dict(current['xic'][0][0])]]
                    current['xic_lookup']=[]       
                    
                elif vendor == 'mgf':
                    current['xic'] = [[current['m'].xic(1, current['m'].scan_number, 0, 100000)]] 
                    current["xic_max"] = [[max([x[1] for x in current["xic"][0][0]])]]
                    current["xic_marks"] = [[{}]]
                    current['mark_boxes'] = []
                    current["xic_dict"] = [[self.make_xic_dict(current['xic'][0][0])]]
                    current['xic_lookup']=[]                    
                    
                elif vendor == "ABI":
                    print "ABI"
                    xic_params = current["m"].time_range() + (fm, lm)
                    current["m"].set_sample(0)
                    current["m"].set_experiment("0")
                    current["xic"] = [[self.GetAnXIC(self, current["m"], current["xr"][0][0])]]
                    
                    current["xic_max"] = [[max([x[1] for x in current["xic"][0][0]])]]
                    current["xic_marks"] = [[{}]]
                    current['mark_boxes'] = []
                    current["xic_dict"] = [[self.make_xic_dict(current['xic'][0][0])]]
                    current['xic_lookup']=[]          
                    print current["xic"]
                #pickle_file = open(current["ticname"], "w")
                #cPickle.dump(current["xic"], pickle_file)
                #pickle_file.close()
                #del busy
            #current["filterRe"] = self.pa.match(current["filter"])
            current["time_ranges"] = [current['m'].time_range()]
            if vendor == "Thermo":
                if current["viewCentroid"]:
                    try:
                        current["scan"] = current["m"].rscan(1)
                    except AttributeError:
                        
                        current['scan'] = mz_centroid(current["m"].scan(1))
                else:
                    current["scan"] = current["m"].scan(1)
            if vendor == 'mgf':
                current['scan']=current['m'].scan(current['m'].scan_range()[0])
            if vendor == "ABI":
                if current["viewCentroid"]: 
                    current["scan"] = current["m"].cscan(current["m"].scan_time_from_scan_name(1), current["experiment"], algorithm=current['settings']['abi_centroid'], eliminate_noise = current['settings']['eliminate_noise'], step_length = current['settings']['step_length'], peak_min = current['settings']['peak_min'], cent_thresh = current['settings']['threshold_cent_abi'])
                else:
                    current["scan"] = current["m"].scan(current["m"].scan_time_from_scan_name(1), current["experiment"])
            
            self.set_axes()
            
            current["unzStartTime"] = current["time_ranges"][0][0]
            current["unzStopTime"] = current["time_ranges"][0][1]
            current["xic_labels"] = []
            current["label_dict"] = {}
            current["found2theor"] = {}
            current["svg"] = defaultdict(list)
            
            #--------------CREATES FILTER DICTIONARY
            if current['vendor']=='Thermo':
                current['fd'] = self.Create_Filter_Info(current["filter_dict"][current["scanNum"]], 'Thermo')
            if current['vendor']=='mgf':
                current['fd'] = self.Create_Filter_Info(current["filter_dict"][current["scanNum"]], 'mgf')            
            if current['vendor']=='ABI':
                current['fd'] = self.Create_Filter_Info(current["filter_dict"][(current["scanNum"],current['experiment'])], 'ABI')
                
            self.files[filename] = current
            self.set_mass_ranges(filename)
            self.set_axes()
            
            #--------------------------------BUILDS CURRENT ID
            if current["vendor"]=='Thermo':
                self.build_current_ID(filename, self.files[filename]["scanNum"])
            if current["vendor"]=='mgf':
                self.build_current_ID(filename, self.files[filename]["scanNum"], 'mgf')            
            if current["vendor"]=='ABI':
                self.build_current_ID(filename, (self.files[filename]["scanNum"],self.files[filename]["experiment"]), 'ABI')
                
            self.files[filename]["unzF"] = self.files[filename]["scan low mass"]
            self.files[filename]["unzL"] = self.files[filename]["scan high mass"]
            self.files[filename]["fm"] = self.files[filename]["scan low mass"]
            self.files[filename]["lm"] = self.files[filename]["scan high mass"]
            self.files[filename]["targ_check"] = False
            self.files[filename]["targ_filt"] = []
            

            
    def make_xic_dict(self, xic):
        #start = time.time()
        xic_dict = {}
        if xic:
            for member in xic:
                xic_dict[member[0]] = member[1]
        #stop = time.time()
        #elapsed = stop-start
        #print elapsed
        return xic_dict
            

    def set_axes(self):
        '''
        Takes first mass and last mass from mass_ranges, and rebuilds mass ranges depending on number of axes.
        Rebuilds axis coordinates depending on number of axes and number of data files.
        '''
        #------------------------------------
        #just added a new file
        #first, determine main axes
        #------------------------------------
        
        num_rawFiles = self.getDisplayWindows()

        space = 40
        inter_raw_space = 20
        y_marg = 50 # 100
        #sz = self.parent.parent.ctrl.GetClientSize()  #
        sz = self.parent.parent.notebook.GetClientSize() #
        for c, i in enumerate(self.getActiveList()):
            print "R:" + str(c)
            _set = self.files[self.Display_ID[i]]['settings']
            _set["auto_resize"]=True
            if _set["auto_resize"]==True:
                #--------------------TOTAL HEIGHT OF THE XIC
                #-------------------------GETS MESSED UP WITH MORE THAN 2 RAWFILES!
                scale = (num_rawFiles-1) * 50 # FOR MULTIPLE RAWFILES, REDUCE THE TOTAL HEIGHT OF EACH XIC
                xic_total_height = (float(sz[1])-110)/float(num_rawFiles)
                xic_total_height -= scale
                #if num_rawFiles > 2:
                #    xic_total_height -= 90
                try:
                    number_xics = len(self.files[self.Display_ID[i]]["xic_params"])
                except:
                    number_xics = 1
                self.files[self.Display_ID[i]]["xic_axco"] = []
                #-----------------Height is PER XIC
                g = {0:10, 1:10, 2:10, 3:10, 4:8, 5:7, 6:6, 7:5, 8:4.5, 9:4.5, 10:4.5}
                height =  (float(sz[1]-100)/float(num_rawFiles)/float(number_xics))-(g[number_xics]*number_xics)  #1 = 15, 2=10, 3=5
                #if num_rawFiles > 2:
                #    height -= 5
                    #height =- 20
                #    pass
                for k in range(0, number_xics):
                    yco = 35+(_set['space']*k)+(height*k)+(xic_total_height*c)+(_set['inter_xic_space']*c)
                    #if num_rawFiles >2:
                    #    yco += (scale*c) * 1.2#/(float(1.2))
                    self.files[self.Display_ID[i]]["xic_axco"].append(((_set['y_marg'],yco+height,(float(sz[0])/float(2))-50,yco+height),(_set['y_marg'],yco,_set['y_marg'],yco+height)))
            else:
                xic_total_height = float(_set['total_xic_height'])/float(num_rawFiles)
                try:
                    number_xics = len(self.files[self.Display_ID[i]]["xic_params"])
                except:
                    number_xics = 1
                self.files[self.Display_ID[i]]["xic_axco"] = []
                height = (float(_set['total_xic_height'])/float(num_rawFiles)/float(number_xics))-(15*number_xics)
                for k in range(0, number_xics):
                    #YCO is the 'y-coordinate'
                    yco = _set['y_marg']+(_set['space']*k)+(height*k)+(xic_total_height*c)+(_set['inter_raw_space']*c)
                    self.files[self.Display_ID[i]]["xic_axco"].append(((_set['y_marg'],yco+height,500,yco+height),(_set['y_marg'],yco,_set['y_marg'],yco+height)))
        indent = 0
        for c, i in enumerate(self.getActiveList()):
            _set = self.files[self.Display_ID[i]]['settings']
            if _set["auto_resize"]==True:            
                num_axes = self.files[self.Display_ID[i]]["axes"]
                mode = self.files[self.Display_ID[i]]["mode"]
                spec_total_height = (float(sz[1])-100)/float(num_rawFiles)
                height = (float(sz[1])-100)/float(num_axes)/float(num_rawFiles)-50*(num_rawFiles-1)
                if num_axes > 0 and num_axes <3:
                    height -= num_axes*20
                elif num_axes > 2:
                    height -= num_axes*15        
                if num_rawFiles > 1:
                    height += 50
                space = 60 #40 originally, added extra space for labels
                if mode == "SPEC":
                    indent = 50
                    width = 900
                if mode == "RIC-SPEC":
                    indent = (float(sz[0])/float(2))
                    width = (float(sz[0])/float(2))-100
                self.files[self.Display_ID[i]]["axco"] = []
                mr = self.files[self.Display_ID[i]]["mass_ranges"]
                fm = mr[0][0]
                current_fm = fm
                lm = mr[len(mr) - 1][1]
                step = float(lm - fm)/float(num_axes)
                self.files[self.Display_ID[i]]["mass_ranges"]=[]
                for k in range(0, num_axes):
                    yco = y_marg+(space*k)+(height*k)+(inter_raw_space*c)+(spec_total_height*c)
                    self.files[self.Display_ID[i]]["axco"].append(((indent,yco+height,indent + width,yco+height),(indent,yco,indent,yco+height)))
                    self.files[self.Display_ID[i]]["mass_ranges"].append((current_fm, current_fm + step))
                    current_fm += step
            else:
                num_axes = self.files[self.Display_ID[i]]["axes"]
                mode = self.files[self.Display_ID[i]]["mode"]
                spec_total_height = float(_set['total_spec_height'])/float(num_rawFiles)
                height = float(_set['total_spec_height'])/float(num_axes)/float(num_rawFiles)
                if num_axes > 1:
                    height -= num_axes*10
                space = 60 #40 originally, added extra space for labels
                if mode == "SPEC":
                    indent = 50
                    width = 900
                if mode == "RIC-SPEC":
                    indent = 600
                    width = 550
                self.files[self.Display_ID[i]]["axco"] = []
                mr = self.files[self.Display_ID[i]]["mass_ranges"]
                fm = mr[0][0]
                current_fm = fm
                lm = mr[len(mr) - 1][1]
                step = float(lm - fm)/float(num_axes)
                self.files[self.Display_ID[i]]["mass_ranges"]=[]
                for k in range(0, num_axes):
                    yco = y_marg+(space*k)+(height*k)+(inter_raw_space*c)+(spec_total_height*c)
                    self.files[self.Display_ID[i]]["axco"].append(((indent,yco+height,indent + width,yco+height),(indent,yco,indent,yco+height)))
                    self.files[self.Display_ID[i]]["mass_ranges"].append((current_fm, current_fm + step))
                    current_fm += step

    def HitTestFeatures(self, pos):
            hitx = pos[0]
            hity = pos[1]
            num_rawFiles = self.getDisplayWindows()
            found = False
            feature = None
            index = None
            for i in self.getActiveList():  #NUMBER OF DISPLAYED FILES
                currentFile = self.files[self.Display_ID[i]]
                for j, feature_box in enumerate(currentFile["FeatureBoxes"]):
                    currentx1 = feature_box[0]
                    currentx2 = feature_box[2]
                    currenty1 = feature_box[1]
                    currenty2 = feature_box[3]
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        found = True
                        index = j
                        feature = feature_box[4]
                        break
                if not found:
                    index = -1
                    feature = -1
                return found, index, feature    

    def HitTestRemoveXIC(self, pos, offset, yoffset):
        hitx = pos[0]
        hity = pos[1]
        num_rawFiles = self.getDisplayWindows()
        found = False
        grid = None
        file = None
        for i in self.getActiveList():  #NUMBER OF DISPLAYED FILES
            currentFile = self.files[self.Display_ID[i]]
            if currentFile['mode'] != 'SPEC':
                for k, coord in enumerate(currentFile['xic_axco']): #COORD = Coordinates for each "Window" or XIC
                    currentx1 = coord[0][0] - offset
                    currentx2 = currentx1 + 10
                    currenty1 = coord[1][1] + yoffset
                    currenty2 = currenty1 + 10
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        found = True
                        grid = k
                        file = i
                        break
            if not found:
                grid = -1
                file = -1
            return found, grid, file           

    def HitTestXICBox(self, pos, offset):
        hitx = pos[0]
        hity = pos[1]
        num_rawFiles = self.getDisplayWindows()
        found = False
        grid = None
        file = None
        trace = None
        #xaxis[0]-10, (yaxis[1]+10)+ (20*xic),10,10
        #xaxis = currentFile['xic_axco'][key][0]
        #yaxis = currentFile['xic_axco'][key][1]        
        for i in self.getActiveList():  #NUMBER OF DISPLAYED FILES
            currentFile = self.files[self.Display_ID[i]]
            if currentFile['mode'] != 'SPEC':
                for k, coord in enumerate(currentFile['xic_axco']): #COORD = Coordinates for each "Window" or XIC
                    traces = len(currentFile['xic_params'][k]) #TRACES DISPLAYED in each window
                    if traces > 1:
                        for j in range(0, traces):
                            currentx1 = coord[0][0] - offset
                            currentx2 = currentx1 + 10
                            currenty1 = (coord[1][1] + 40) + (30 * j)
                            currenty2 = currenty1 + 10
                            if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        #print "HIT!" + str(i)
                                found = True
                                trace = j
                                grid = k
                                file = i
                                break
            if not found:
                grid = -1
                file = -1
            return found, trace, grid, file            
    
    def HitTestThr(self, pos):
        '''
        
        Hit Test for threshold box
        
        '''
        hitx = pos[0]
        hity = pos[1]
        num_rawFiles = self.getDisplayWindows()
        found = False
        grid = None
        file = None
        e = None
        for i in self.getActiveList():
            currentFile = self.files[self.Display_ID[i]]
            if currentFile['mode'] != 'SPEC':
                #----------------------------NEED TO FIND THRESHHOLD BOX COORDS
                currentx1, currenty1, currentx2, currenty2 = self.parent.thresh_box
                if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        print "HIT!"
                        found = True
                        file = i
                        e = "Thr"
                        break
            if currentFile['mode'] == 'SPEC':
                pass
        if not found:
            file = -1
        return found, e, file
          
    def HitTest(self, pos):
        '''
        
        Hit tests for Spectra and XICs
        returns found, e, grid, file
        file = Relevant Data File
        e = "XIC" or "SPEC"
        grid = which trace or spectrum axis
        Found = True or False
        
        '''
        hitx = pos[0]
        hity = pos[1]
        num_rawFiles = self.getDisplayWindows()
        found = False
        grid = None
        file = None
        e = None
        for i in self.getActiveList():
            currentFile = self.files[self.Display_ID[i]]
            if currentFile['mode'] != 'SPEC':
                for k, coord in enumerate(currentFile['xic_axco']):
                    #print coord
                    currentx1 = coord[0][0]
                    currentx2 = coord[0][2]
                    currenty1 = coord[1][1]
                    currenty2 = coord[1][3]
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        #print "HIT!" + str(i)
                        found = True
                        e = "RIC"
                        grid = k
                        file = i
                        break
                for k, coord in enumerate(currentFile['axco']):
                    currentx1 = coord[0][0]
                    currentx2 = coord[0][2]
                    currenty1 = coord[1][1]
                    currenty2 = coord[1][3]
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        found = True
                        e = "SPEC"
                        grid = k
                        file = i
                        break
            if currentFile['mode'] == 'SPEC':
                for k, coord in enumerate(currentFile['axco']):
                    currentx1 = coord[0][0]
                    currentx2 = coord[0][2]
                    currenty1 = coord[1][1]
                    currenty2 = coord[1][3]
                    if hitx > currentx1 and hitx < currentx2 and hity > currenty1 and hity < currenty2:
                        found = True
                        e = "SPEC"
                        grid = k
                        file = i
                        break
        
        if not found:
            grid = -1
            file = -1
        return found, e, grid, file

    def build_current_ID(self, filename, scan, vendor = 'Thermo'):
        '''
        This function builds the label dict.  For a given charge, adds y and b ions of charge 1 up to the precursor charge.
        Calls build_label_dict or build_mascot_label_dict
        '''
        
        #---------------------------------------------
        #If not overridden by "overlay", look in ID_Dict from search result
        if not self.files[filename]["scanNum"] in self.files[filename]["overlay"].keys():
            key = None
            if vendor in ['Thermo', 'mgf']:
                key = self.files[filename]["scanNum"]
            elif vendor == 'ABI':
                key = (self.files[filename]["scanNum"], self.files[filename]["experiment"])
            a= self.files[filename]["ID_Dict"]
            if key in self.files[filename]["ID_Dict"].keys():
                self.files[filename]["ID"] = True
                if self.files[filename]["SearchType"]=="Mascot":
                    # ID_Dict keys are ints when this is a RAW file.
                    seq = self.files[filename]["ID_Dict"][scan]["Peptide Sequence"]
                    cg = self.files[filename]["ID_Dict"][scan]["Charge"]
                    varmod = self.files[filename]["ID_Dict"][scan]["Variable Modifications"]
                    fixedmod = self.files[filename]["fixedmod"]
                elif self.files[filename]["SearchType"]=="COMET":
                    seq = self.files[filename]["ID_Dict"][scan]["Peptide Sequence"]
                    varmod = self.files[filename]["ID_Dict"][scan]["Variable Modifications"]
                    cg = self.files[filename]["ID_Dict"][scan]["Charge"]
                    fixedmod = ''
                elif self.files[filename]["SearchType"]=="X!Tandem":
                    seq = self.files[filename]["ID_Dict"][scan]["Peptide Sequence"]
                    varmod = self.files[filename]["ID_Dict"][scan]["Variable Modifications"]
                    cg = self.files[filename]["ID_Dict"][scan]["Charge"]
                    fixedmod = ''                
                elif self.files[filename]["SearchType"]=="Proteome Discoverer":
                    seq = self.files[filename]["ID_Dict"][scan]["Annotated Sequence"].upper()
                    varmod = self.files[filename]["ID_Dict"][scan]["Modifications"]
                    cg = self.files[filename]["ID_Dict"][scan]["Charge"]
                    fixedmod = ''                                
                else: #if not varmod:
                    varmod = ''
                self.files[filename]["seq"] = seq
                self.files[filename]["label_dict"]={}
                _ions = 'b/y'
                if self.files[filename]['fd']['mode']=='ms2':
                    if self.files[filename]['fd']['reaction']=='etd':
                        _ions = 'c/z'
                if not self.files[filename]["viewMascot"]:
                    for i in range(1, int(cg+1)):
                        self.files[filename]["mz"], self.files[filename]["b_ions"], self.files[filename]["y_ions"] = mz_core.calc_pep_mass_from_residues(seq, i, varmod, fixedmod, ions=_ions)
                        if varmod.find("Fucosylation") > -1 or varmod.find("Phospho") >-1 or varmod.find("Hex") > - 1 or varmod.find("Xyl") > -1 or seq.find("p") >-1 or varmod.find("SML") > -1:
                            self.files[filename]["NL_ions"] = mz_core.get_fragment_neutral_losses(seq, self.files[filename]["b_ions"], self.files[filename]["y_ions"], varmod, i)
                            self.files[filename]["precNL_ions"] = mz_core.get_precursor_neutral_losses(self.files[filename]["mz"], i, varmod) 
                            #print self.files[filename]["NL_ions"]
                        print "Building label dict"
                        self.build_label_dict(i, filename)
                else:
                    self.build_mascot_label_dict(filename)
            else:
                self.files[filename]["ID"] = False
        else:
            #If there is an overlay, apply it.
            self.files[filename]["label_dict"]={}
            self.files[filename]["y_ions"]=self.files[filename]["overlay"][self.files[filename]["scanNum"]][0]
            self.files[filename]["b_ions"]=self.files[filename]["overlay"][self.files[filename]["scanNum"]][1]
            self.build_label_dict(1, filename)

    def search_for_mass(self, mz, scan, filename, vendor = 'Thermo'): #scan is the list of mz, intensity
        '''
        
        Searches scan data for matches to fragment ions.
        Tolerance is either defined in settings, or if '0' uses instrument default
        
        
        '''
        #---------------------------------------------------------------------
        # Should clean up this code for cleaner instrument --> Default tolerance settings
        #---------------------------------------------------------------------
        labelTol = self.files[filename]['settings']['ionLabelThresh']
        if not labelTol:
            tolerance = 0.02
            if vendor == 'Thermo':
                if self.files[filename]["filter_dict"][self.files[filename]["scanNum"]].find("ITMS")>-1:
                    tolerance = 0.5
            elif vendor == 'mgf':
                tolerance = 0.5
            elif vendor == 'ABI-MALDI':
                tolerance = 0.5
        else:
            tolerance = labelTol
            
        found = False
        found_mz = 0
        found_int = 0
        #if self.files[filename]['labelThreshOverride']: tolerance=self.files[filename]['labelThreshOverride']
        for j, member in enumerate(scan):
            if mz > member[0] - tolerance and mz < member[0] + tolerance:
                found = True
                found_mz = member[0]
                found_int = member[1]
                break
        return found, found_mz, found_int

    def set_scan(self, scanNum, file_number):
        '''
        
        The purpose of set_scan is to retrieve the scan data based on centroid/profile and data data type.
        Sets mass range and axes.  Obtains fd (filter dictionary) from Create_Filter_Info.
        
        '''
        currentFile = self.files[self.Display_ID[file_number]]

        if currentFile['vendor'] == 'mgf':
            #assert scanNum in currentFile['m'].mgf_data
            scanNum = min(currentFile['m'].mgf_data.keys(), key = lambda x: abs(int(scanNum) - int(x)))
        
        
        currentFile["scanNum"] = scanNum
        if currentFile['vendor'] in ['Thermo']:
            filt = currentFile["filter_dict"][currentFile["scanNum"]]
        elif currentFile['vendor'] in ['mgf']:
            filt = currentFile["filter_dict"][currentFile["scanNum"]]  #[currentFile["mgf_scan_dict"]
        elif currentFile['vendor']=='ABI':
            filt = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]
        if filt.find("FTMS") > -1 or filt.find("TOF MS") > -1 or filt.find("TOF PI") > -1 or filt.find("Q3") >-1 or filt.find("EMS") > -1 or filt.find("PI ") > -1 or filt.find("ER MS ") > -1 or filt.find("ITMS + p ESI Full ms ") > -1 or filt.find("Precursor") > -1 or filt.find("EPI") > -1:
            if currentFile["viewCentroid"]:
                if currentFile['vendor']=='Thermo':
                    try:
                        currentFile["scan"] = currentFile["m"].rscan(currentFile["scanNum"])
                    except AttributeError:
                        if ' c ' not in filt and 'cent' not in filt:
                            try:
                                currentFile['scan'] = mz_centroid(currentFile['m'].scan(currentFile['scanNum']), threshold_scale = 2)
                            except:
                                currentFile['scan'] = currentFile['m'].scan(currentFile['scanNum'])
                        else:
                            currentFile['scan'] = currentFile['m'].scan(currentFile['scanNum'])
                #elif currentFile['vendor']=='ABI':
                    #currentFile["scan"] = currentFile["m"].cscan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'], algorithm=currentFile['settings']['abi_centroid'], eliminate_noise = currentFile['settings']['eliminate_noise'], step_length = currentFile['settings']['step_length'], peak_min = currentFile['settings']['peak_min'], cent_thresh = currentFile['settings']['threshold_cent_abi'])
                #print "Pulled cent!"
            else:
                if currentFile['vendor']=='Thermo':
                    currentFile["scan"] = currentFile["m"].scan(currentFile["scanNum"])
                elif currentFile['vendor']=='ABI':
                    currentFile["scan"] = currentFile["m"].scan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'])
        elif filt.find("MGF") > -1:        
            currentFile["scan"] = currentFile["m"].scan(currentFile["scanNum"])  #currentFile['mgf_scan_dict'][
        else:
            currentFile["scan"] = currentFile["m"].scan(currentFile["scanNum"])
        self.set_mass_ranges(self.Display_ID[file_number])
        self.set_axes()
        if currentFile['vendor']=='Thermo':
            currentFile['fd'] = self.Create_Filter_Info(currentFile["filter_dict"][currentFile["scanNum"]], 'Thermo')
        if currentFile['vendor']=='mgf':
            currentFile['fd'] = self.Create_Filter_Info(currentFile["filter_dict"][currentFile["scanNum"]], 'mgf')        
        if currentFile['vendor']=='ABI':
            currentFile['fd'] = self.Create_Filter_Info(currentFile["filter_dict"][(currentFile["scanNum"],currentFile['experiment'])], 'ABI')
        if currentFile['vendor']=='ABI-MALDI':
            currentFIle['fd']= self.Create_Filter_Info(urrentFile["filter_dict"][currentFile["scanNum"]], 'ABI-MALDI')

    def set_average_scan(self, start, stop, filt, file_number):
        currentFile = self.files[self.Display_ID[file_number]]
        try:
            startscan, stopscan = map(currentFile['m'].scanForTime, (start, stop))
            spectrum = currentFile['m'].average_scan(startscan, stopscan, filt)
        except AttributeError:
            wx.MessageBox('Averaged scan display is only supported for RAW-format files.')
            return False
        
        currentFile['scanNum'] = str(startscan) + '-' + str(stopscan) # Sort of arbitrary.
        #currentFile['fd'] = self.Create_Filter_Info(filt, 'Thermo')
        
        #if "ms1" in filt:
        #    currentFile['fd'] = {'mode':"ms1", 'analyzer':'average', 'data':'average' , 'mr':'[t1-t2]'}
        #elif "ms2" in filt:
        #    currentFile['fd'] = {'mode':"ms1", 'analyzer':'average', 'precursor':'average', 'data':'average', 'reaction':'average', 'mr':'[t1-t2]', 'energy':'average'}
        
        currentFile["spectrum_style"] ='AVERAGE'
        currentFile['scan'] = spectrum
        masses = [x[0] for x in spectrum]
        currentFile['average_mass_range']=[min(masses), max(masses)]
        
        return True
        
            

    def build_mascot_label_dict(self, filename):
        vendor = self.files[filename]["vendor"]
        scan_data = None
        scan = self.files[filename]["scanNum"]
        if vendor == 'ABI':
            exp = self.files[filename]['experiment']
        key = None
        if vendor == 'Thermo':
            key = scan
        if vendor == 'mgf':
            key = scan        
        if vendor == 'ABI':
            key = (scan, exp)
        if self.files[filename]["filter_dict"][key].find("+ p")>-1:
            if vendor == 'Thermo':
                scan_data = self.files[filename]['m'].rscan(self.files[filename]['scanNum'])
            if vendor == 'ABI':
                scan_data = self.files[filename]['m'].rscan(self.files[filename]['m'].scan_time_from_scan_name(scan), exp)
        else:
            scan_data = self.files[filename]['scan']        
        #((175.11825999999999, 'y(1) [175.12]'), (282.65723000000003, 'b(3)-98++ [282.66]'),
        ##print self.files[filename]["mascot_ID"]
        if vendor != "mgf":
            mascot_ID_dict = self.files[filename]["mascot_ID"][self.files[filename]["scanNum"]]#[self.files[filename]["scan"]]
        else:
            curfile = self.files[filename]
            scan_var = curfile["scanNum"]
            real_scan = curfile["mgf_rev_dict"][scan_var]
            mascot_ID_dict = curfile["mascot_ID"][real_scan]
        #print "BUILDING MASCOT"
        #print mascot_ID_dict
        for i, member in enumerate(mascot_ID_dict):
            #print "Search for"
            #print member[0]
            found, found_mz, found_int = self.search_for_mass(member[0], scan_data, filename)
            #print found
            #print found_mz
            if found:
                if found_mz in self.files[filename]["label_dict"].keys():
                    self.files[filename]["label_dict"][found_mz] += ', ' + member[1].split("[")[0].strip()
                else:
                    self.files[filename]["label_dict"][found_mz] = member[1].split("[")[0].strip()
                    self.files[filename]["found2theor"][found_mz] = float(member[1].split(" ")[1][1:-1])
        print self.files[filename]["label_dict"]

    def build_label_dict(self, cg, filename):
        '''
        Loops through y and b ions.  For each ion, look for it in the scan.  If it finds it, add it to the label_dict
        {225.43 : y5}
        '''
        vendor = self.files[filename]["vendor"]
        scan_data = None
        scan = self.files[filename]["scanNum"]
        
        if vendor == 'ABI':
            exp = self.files[filename]['experiment']
        key = None
        if vendor in ['Thermo', 'mgf']:
            key = scan
        if vendor == 'ABI':
            key = (scan, exp)
            print key
        if vendor == 'ABI-MALDI':
            key = 1
        
        currentFilter = self.files[filename]["filter_dict"][key]
        
        if currentFilter.find("+ p")>-1:
            if currentFilter.find("FTMS")>-1:
                scan_data = self.files[filename]['m'].rscan(self.files[filename]['scanNum'])
            elif currentFilter.find("TOF PI + p NSI Full ms2")>-1:
            #if vendor == 'ABI':
                #scan_data = self.files[filename]['m'].cscan(self.files[filename]['m'].scan_time_from_scan_name(scan), exp, algorithm="new", eliminate_noise = True, step_length = 0.025, peak_min = 3)
                scan_data = self.files[filename]['m'].scan(self.files[filename]['scanNum'], centroid=True)                
        else:
            scan_data = self.files[filename]['scan']
            
        if self.files[filename]['Processing']:
            scan_data = self.parent.parent.parent.custom_spectrum_process(scan_data)
        
            
        y_label = 'y'
        b_label = 'b'
        if self.files[filename]["fd"]['reaction']=='etd':
            y_label = 'z'
            b_label = 'c'
            
        for i, member in enumerate(self.isotope_labels):
            found, found_mz, found_int = self.search_for_mass(member[0], scan_data, filename, vendor)
            #print "LABEL ISOTOPE"
            #print member[0]
            if found:
                #print "FOUND"
                #print member[1]
                self.files[filename]["label_dict"][found_mz] = member[1]
                self.files[filename]["found2theor"][found_mz] = 0.0     
            
        for i, member in enumerate(self.files[filename]["y_ions"]):
            found, found_mz, found_int = self.search_for_mass(member, scan_data, filename, vendor)
            if found:
                if found_mz in self.files[filename]["label_dict"].keys():
                    self.files[filename]["label_dict"][found_mz] += ', ' + y_label + str(i+1)
                    #self.files[filename]["found2theor"][found_mz] = member
                    if cg > 1:
                        self.files[filename]["label_dict"][found_mz] += ' ' + str(cg) + '+'
                else:
                    self.files[filename]["label_dict"][found_mz] = y_label + str(i+1)
                    self.files[filename]["found2theor"][found_mz] = member
                    if cg > 1:
                        self.files[filename]["label_dict"][found_mz] += ' ' + str(cg) + '+'
                        
        for i, member in enumerate(self.files[filename]["b_ions"]):
            found, found_mz, found_int = self.search_for_mass(member, scan_data, filename, vendor)
            if found:
                if found_mz in self.files[filename]["label_dict"].keys():
                    self.files[filename]["label_dict"][found_mz] += ', ' + b_label + str(i+1)
                    if cg > 1:
                        self.files[filename]["label_dict"][found_mz] += ' ' + str(cg) + '+'
                else:
                    self.files[filename]["label_dict"][found_mz] = b_label + str(i+1)
                    self.files[filename]["found2theor"][found_mz] = member
                    if cg > 1:
                        self.files[filename]["label_dict"][found_mz] += ' ' + str(cg) + '+'
                        
        for i, member in enumerate(self.files[filename]["NL_ions"].keys()):
            found, found_mz, found_int = self.search_for_mass(member, scan_data, filename, vendor)
            if found:
                if found_mz in self.files[filename]["label_dict"].keys():
                    self.files[filename]["label_dict"][found_mz] += ', ' + self.files[filename]["NL_ions"][member]
                else:
                    self.files[filename]["label_dict"][found_mz] = self.files[filename]["NL_ions"][member]
                    self.files[filename]["found2theor"][found_mz] = member
                    
        for i, member in enumerate(self.files[filename]["precNL_ions"].keys()):
            found, found_mz, found_int = self.search_for_mass(member, scan_data, filename, vendor)
            if found:
                if found_mz in self.files[filename]["label_dict"].keys():
                    self.files[filename]["label_dict"][found_mz] += ', ' + self.files[filename]["precNL_ions"][member]
                else:
                    self.files[filename]["label_dict"][found_mz] = self.files[filename]["precNL_ions"][member]
                    self.files[filename]["found2theor"][found_mz] = member  
        print self.files[filename]["label_dict"]

class BufferedWindow(wx.Window):

    """

    A Buffered window class.

    To use it, subclass it and define a Draw(DC) method that takes a DC
    to draw to. In that method, put the code needed to draw the picture
    you want. The window will automatically be double buffered, and the
    screen will be automatically updated when a Paint event is received.

    When the drawing needs to change, you app needs to call the
    UpdateDrawing() method. Since the drawing is stored in a bitmap, you
    can also save the drawing to file by calling the
    SaveToFile(self, file_name, file_type) method.

    """
    def __init__(self, parent, *args, **kwargs):
        # make sure the NO_FULL_REPAINT_ON_RESIZE style flag is set.
        kwargs['style'] = kwargs.setdefault('style', wx.NO_FULL_REPAINT_ON_RESIZE) | wx.NO_FULL_REPAINT_ON_RESIZE
        #wx.Window.__init__(self, *args, **kwargs)
        wx.Window.__init__(self, parent, size=(2690, 1850))  #(1690, 850)
        
        self.parent = parent
        #self.statusbar = self.parent.parent.CreateStatusBar()
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_MOTION(self, self.OnMotion)
        wx.EVT_ERASE_BACKGROUND(self, self.OnErase)
        #wx.EVT_ENTER_WINDOW(self, self.OnEnter)
        self.draw_selection = False
        self.draw_co = None
        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        self.OnSize(None)
        self.paint_count = 0
        self.overlay=wx.Overlay()

    def Draw(self, dc):
        ## just here as a place holder.
        ## This method should be over-ridden when subclassed
        pass

    def OnErase(self, event):
        #'''
        #Very important - without this, there is alot of flicker!
        #'''
        #print 'ERASING??????'
        #event.Skip()
        pass

    def OnPaint(self, event):
        #print "Paint"
        # All that is needed here is to draw the buffer to screen
        if USE_BUFFERED_DC:
            dc = wx.BufferedPaintDC(self, self._Buffer)
            dc.SetBackground(wx.Brush("white"))
        else:
            dc = wx.PaintDC(self)
            dc.DrawBitmap(self._Buffer, 0, 0)

    def ClearOverlay(self):
        dc = wx.ClientDC(self)
        odc = wx.DCOverlay(self.overlay, dc)
        odc.Clear()
        del odc
        self.overlay.Reset()

    def OnEnter(self, event):
        pos = event.GetPosition()
        print pos
        found, e, grid, file = self.parent.msdb.HitTest(pos)

    def OnMotion(self, event):
        '''
        This event handler takes care of updating status text with current mz (mouse moves on spectrum), 
        and rubber banding (mouse motion with click and drag)
        
        A DC overlay is used, this way when the mouse moves, the original rectangle is deleted from the buffered image.
        In addition, a GCDC is used, to allow the rectangle to have alpha transparency.
        '''
        #event.Skip()        
        #pos = event.GetPositionTuple()
        pos = event.GetPosition()
        found, e, grid, file = self.parent.msdb.HitTest(pos)  
        if not found:
            event.Skip()
            return
        elif found:
            currentFile = self.parent.msdb.files[self.parent.msdb.Display_ID[file]]
            #----------------------------If a mark box is active, and the mouse has moved off, remove it
            for i, member in enumerate(currentFile['mark_boxes']):
                if pos[0] > member[1][0] and pos[0] < member[1][1] and pos[1] > member[1][2] and pos[1] < member[1][3]:
                    pass
                else:
                    member[0].Destroy()
                    del currentFile['mark_boxes'][i]   
            #---------------------------If the mouse moves over the spectrum, report mz and intensity
            if e == 'SPEC':
                current_mz = self.parent.ConvertPixelToMass(pos[0], grid, file)
                current_int = self.parent.ConvertPixelToIntensity(pos[1], grid, file)
                self.parent.parent.parent.statusbar.SetStatusText('Current mz: ' + str(current_mz) + '     Inten: %.1e' %current_int)
                #print current_mz
            #_---------------------------Check to see if over XIC mark.
            #----------------------------If over, make a popup window
            if e[1] == 'I':
                for member in currentFile['xic_lookup']:
                    x1 = member[0]-5
                    x2 = member[0]+5
                    y1 = member[1]-5
                    y2 = member[1]+5
                    box_already_there = False
                    for box in currentFile['mark_boxes']:
                        if (x1, x2, y1, y2) == box[1]:
                            box_already_there = True
                    if pos[0] > x1 and pos[0] <x2 and pos[1] > y1 and pos[1] < y2 and not box_already_there:
                        seq = member[2].label
                        varmod = member[2].varmod
                        fixedmod = member[2].fixedmod
                        peptide_container = mz_core.create_peptide_container(seq, varmod, fixedmod)
                        sequence = ''
                        for aa in peptide_container:
                            sequence += aa   
                        sequence += ' +' + str(member[2].cg)
                        win = TestPopup(self, wx.SIMPLE_BORDER, sequence, member)
                        win.Position((pos[0]+20,pos[1]-20), (0, 100))
                        win.Show(True)
                        currentFile['mark_boxes'].append([win, (x1, x2, y1, y2)])
        else:
            self.parent.parent.parent.statusbar.SetStatusText("")
        if event.Dragging() and event.LeftIsDown():
            try:
                if self.parent.found:
                    if self.parent.e in ['RIC', 'XIC', 'SPEC']:
                        #self.parent.found is the result of the OnLeftDown
                        #currentFile = self.parent.msdb.files[self.parent.msdb.Display_ID[self.parent.file]]['axco'][self.parent.grid][1]
                        #copy = self._Buffer
                        pdc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
                        dc = wx.GCDC(pdc)
                        odc = wx.DCOverlay(self.overlay, pdc)
                        odc.Clear()
                        pos = event.GetPosition()
                        found, e, grid, file = self.parent.msdb.HitTest(pos)
                        if file == self.parent.file and e[1]==self.parent.e[1]: #XIC vs RIC; match i's.  SPECs same match P's.
                            if self.parent.e=="SPEC":
                                #If on the same axis, draw the horizontal line across
                                if grid == self.parent.grid:
                                    dc.DrawLine(self.parent.postup[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                                    dc.SetPen(wx.Pen(wx.BLUE,2))
                                    #This is the first position marking the OnLeftDown
                                    dc.DrawLine(self.parent.postup[0], self.parent.yaxco[1], self.parent.postup[0], self.parent.yaxco[3])
                                    #Draw vertical line marking the current position.
                                    dc.DrawLine(pos[0], self.parent.yaxco[1], pos[0], self.parent.yaxco[3])
                                    brushclr = wx.Colour(0,0,255,8)
                                    dc.SetBrush(wx.Brush(brushclr))
                                    if self.parent.postup[0] < pos[0]:
                                        dc.DrawRectangle(self.parent.postup[0], self.parent.yaxco[1], pos[0] - self.parent.postup[0], self.parent.yaxco[3]- self.parent.yaxco[1])
                                    else:
                                        dc.DrawRectangle(pos[0], self.parent.yaxco[1], self.parent.postup[0] - pos[0], self.parent.yaxco[3]- self.parent.yaxco[1])
                                else:
                                    current = self.parent.msdb.files[self.parent.msdb.Display_ID[file]]["axco"][grid][1]
                                    dc.SetPen(wx.Pen(wx.BLUE,2))
                                    #This is the first position marking the OnLeftDown
                                    dc.DrawLine(self.parent.postup[0], self.parent.yaxco[1], self.parent.postup[0], self.parent.yaxco[3])
                                    #Draw vertical line marking the current position.
                                    dc.DrawLine(pos[0], current[1], pos[0], current[3])                            
                            if self.parent.e[1]=="I":
                                if grid == self.parent.grid:
                                    dc.DrawLine(self.parent.postup[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                                    dc.SetPen(wx.Pen(wx.BLUE,2))
                                    dc.DrawLine(self.parent.postup[0], self.parent.yaxco[1], self.parent.postup[0], self.parent.yaxco[3])
                                    dc.DrawLine(pos[0], self.parent.yaxco[1], pos[0], self.parent.yaxco[3])  
                                    brushclr = wx.Colour(255,0,0,8)
                                    dc.SetBrush(wx.Brush(brushclr))
                                    if self.parent.postup[0] < pos[0]:
                                        dc.DrawRectangle(self.parent.postup[0], self.parent.yaxco[1], pos[0] - self.parent.postup[0], self.parent.yaxco[3]- self.parent.yaxco[1])
                                    else:
                                        dc.DrawRectangle(pos[0], self.parent.yaxco[1], self.parent.postup[0] - pos[0], self.parent.yaxco[3]- self.parent.yaxco[1])                                
                                else:
                                    dc.DrawLine(self.parent.postup[0], self.parent.postup[1], pos[0], pos[1])
                                    dc.DrawRectangle(pos[0],pos[1], 100, 50)
                                    dc.DrawText("XIC",pos[0]+50, pos[1]+25)
                                    #currentFile = self.msdb.files[self.msdb.Display_ID[rawID]]
                                    #GET SUB BIT MAP    
                                    #active_xic = currentFile['active_xic'][grid]
                                    #xaxis = currentFile['xic_axco'][grid][0]
                                    #yaxis = currentFile['xic_axco'][grid][1]                                 
                                    #sb = self._Buffer.GetSubBitmap(50, 50, 500, 500)
                                    #dc.DrawBitmapPoint(sb, (xaxis[0], yaxis[0]))
                                    #dc.DrawBitmap(sb, pos[0]+50, pos[1]+25)
                                    #del sb
                        #dc.DrawRectangle(self.parent.postup[0], self.parent.yaxco[1], pos[0] - self.parent.postup[0], self.parent.yaxco[3]- self.parent.yaxco[1])
                        del odc
                        self.Refresh()
                        self.Update()
                    elif self.parent.e == 'Thr':
                        print "Doing it"
                        pdc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
                        dc = wx.GCDC(pdc)
                        odc = wx.DCOverlay(self.overlay, pdc)
                        odc.Clear()
                        pos = event.GetPosition()  
                        #--------------Use y value of pos to drawline from axco-7, y to axco, y 
                        currentFile = self.parent.msdb.files[self.parent.msdb.Display_ID[self.parent.file]]
                        xaxis = currentFile['axco'][0][0]
                        yaxis = currentFile['axco'][0][1]
                        dc.DrawLine(yaxis[0]-7, pos[1], xaxis[2], pos[1])
                        del odc
                        self.Refresh()
                        self.Update()                        
            except:
                event.Skip()
        if event.Dragging() and event.RightIsDown(): #XIC event on SPEC window
            if self.parent.found:
                dc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
                odc = wx.DCOverlay(self.overlay, dc)
                odc.Clear()
                pos = event.GetPosition()
                found, e, grid, file = self.parent.msdb.HitTest(pos)
                if not found:
                    event.Skip()
                    return
                if file == self.parent.file and e==self.parent.e and self.parent.right_down_pos: #XIC vs RIC; match i's.  SPECs same match P's.
                    if self.parent.e=="SPEC":
                        #If on the same axis, draw the horizontal line across
                        if grid == self.parent.grid:
                            dc.DrawLine(self.parent.right_down_pos[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                            dc.SetPen(wx.Pen(wx.BLUE,2))
                            #This is the first position marking the OnLeftDown
                            dc.DrawLine(self.parent.right_down_pos[0], self.parent.yaxco[1], self.parent.right_down_pos[0], self.parent.yaxco[3])
                            #Draw vertical line marking the current position.
                            dc.DrawLine(pos[0], self.parent.yaxco[1], pos[0], self.parent.yaxco[3])
                    if self.parent.e[1]=="I":
                        if grid == self.parent.grid:
                            dc.DrawLine(self.parent.right_down_pos[0], pos[1], pos[0], pos[1])#self.parent.postup[1]
                            dc.SetPen(wx.Pen(wx.BLUE,2))
                            dc.DrawLine(self.parent.right_down_pos[0], self.parent.yaxco[1], self.parent.right_down_pos[0], self.parent.yaxco[3])
                            dc.DrawLine(pos[0], self.parent.yaxco[1], pos[0], self.parent.yaxco[3])  
                            #brushclr = wx.Colour(255,0,0,8)
                            #dc.SetBrush(wx.Brush(brushclr))
                            #if self.parent.postup[0] < pos[0]:
                            #    dc.DrawRectangle(self.parent.postup[0], self.parent.yaxco[1], pos[0] - self.parent.postup[0], self.parent.yaxco[3]- self.parent.yaxco[1])
                            #else:
                            #    dc.DrawRectangle(pos[0], self.parent.yaxco[1], self.parent.postup[0] - pos[0], self.parent.yaxco[3]- self.parent.yaxco[1])                         
        event.Skip()    

    def OnSize(self,event):
        # The Buffer init is done here, to make sure the buffer is always
        # the same size as the Window
        #Size  = self.GetClientSizeTuple()
        Size  = self.ClientSize

        # Make new offscreen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self._Buffer = wx.EmptyBitmap(*Size)
        self.UpdateDrawing()
        if event:
            event.Skip()

    def SaveToFile(self, FileName, FileType=wx.BITMAP_TYPE_PNG):
        ## This will save the contents of the buffer
        ## to the specified file. See the wxWindows docs for 
        ## wx.Bitmap::SaveFile for the details
        self._Buffer.SaveFile(FileName, FileType)

    def UpdateDrawing(self):
        """
        This would get called if the drawing needed to change, for whatever reason.

        The idea here is that the drawing is based on some data generated
        elsewhere in the system. If that data changes, the drawing needs to
        be updated.

        This code re-draws the buffer, then calls Update, which forces a paint event.
        """
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        self.Draw(dc)
        del dc # need to get rid of the MemoryDC before Update() is called.
        #self.Refresh()
        #self.Update()

class DrawWindow(BufferedWindow):
    def __init__(self, parent, size):#*args, **kwargs
        ## Any data the Draw() function needs must be initialized before
        ## calling BufferedWindow.__init__, as it will call the Draw
        ## function.
        self.parent = parent
        self.DrawData = {}
        #self.Bind(wx.EVT_LEFT_DOWN, self.parent.OnLeftDown)
        #self.Bind(wx.EVT_LEFT_UP, self.parent.OnLeftUp)
        #self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        #self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        #self.Bind(wx.EVT_KEY_DOWN, self.parent.OnKeyDown)        
        BufferedWindow.__init__(self, parent, parent)
        #self.Bind(wx.EVT_LEFT_DOWN, self.parent.OnLeftDown)
        #self.Bind(wx.EVT_LEFT_UP, self.parent.OnLeftUp)  
        #self.dragController = DragController(self, None, pos=(0, 0))
              
    def Draw(self, dc):
        self.parent.OnDraw(dc)

#class ParentFrame(aui.AuiNotebook):
class ParentFrame(object):
    def __init__(self, parent): 
        #-----------------------PARENT IS THE TopLevelFrame
        #-----------------------"ParentFrame" manages the aui notebook.
        #-----------------------Tool bar and menu come from the parent (top level frame)
        #-----------------------
        #-----------------------OnNewChild adds a page to the aui notebook (page is a drawpanel)
        #-----------------------DrawPanel has a DrawWindow
        #-----------------------DrawWindow is a BufferedWindow
        #-----------------------DrawPanel has msdb
        #-----------------------
        #-----------------------
        #-----------------------
        #-----------------------
        #-----------------------Page is added from OnNewChild in TopLevelFrame
        #---------------------------child = DrawPanel(self.parentFrame, rawfile, 1)        
        #---------------------------self.ctrl.AddPage(child, os.path.basename(rawfile), False)      
        #---------------------------       
        self.parent = parent
        sz = self.parent.GetClientSize()
        
        #aui.AuiNotebook.__init__(self,parent,id=-1, name='Browse', size =(1800,1400), pos = (50,50))  
        #self.notebook = aui.AuiNotebook(parent,id=-1, name='Browse', size =(1800,1400), pos = (50,50))
        self.notebook = aui.AuiNotebook(parent,id=-1, size =(1800,1400), pos = (50,50))
        
        #aui.AuiNotebook.__init__(self.notebook,id=-1, size =(1800,1400), pos = (50,50))  
        #self.notebook.Bind(wx.lib.agw.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnClose, self.notebook)
        #self.notebook.SetMinSize((900,700))
        #self.notebook.SetMinClientSize((900,700))
        
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.winClose)
        #self.notebook.SetMinSize((400,400))
        self.count = 0
        #mb = self.MakeMenuBar()
        #self.SetMenuBar(mb)
        #self.SetIcon(wx.Icon(installdir + r'\image\multiplierz.ico'))
        #self.notebook.Bind(wx.EVT_CLOSE, self.OnDoClose)
        
        #self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.notebook.Bind(wx.EVT_TIMER, self.TimerHandler)
        self.timer = wx.Timer(self.notebook) 
        self.ObjectOrganizer = ObjectOrganizer.ObjectOrganizer()

    def winClose(self, event):
        print "EVENT"
        
        activepanel = self.notebook.GetPage(self.notebook.GetSelection())
        try:
            dbf = self.ObjectOrganizer.getObjectOfType(dbFrame.dbFrame)
            if dbf.currentPage == activepanel:
                dbf_frame = self.parent._mgr.GetPane(dbf)
                self.parent._mgr.ClosePane(dbf_frame)
                self.parent._mgr.Update()
                self.ObjectOrganizer.removeObject(dbf)
        except KeyError: # No dbf.
            pass
        
        event.Skip()

    def OnClose(self, event):
        print "CLOSE"
        event.Skip()

    def SetupAdjustableGauge(self, text ="Processing...", color=wx.GREEN):
        self.adj_gauge = AdjProg.PyGaugeDemoW(self.parent.tb, size=(155, 15), pos=(500,5), color=color, parent=self)
        self.adjtxt1 = wx.StaticText(self.parent.tb, -1, text, size=(100, 25), pos=(700,5))
        self.adjtxt1.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.NORMAL, wx.BOLD, face="Franklin Gothic Book"))
        
    def HideAdjGauge(self):
        self.adj_gauge.gauge1.Destroy()
        self.adj_gauge.Destroy()
        self.adjtxt1.Destroy()      

    def StartGauge(self, text="Processing...", color=wx.GREEN):
        self.busy_gauge = pg.ProgressGauge(self.parent.tb, size=(155, 15), pos=(500,5), color=color)
        self.timer.Start(100)
        self.txt1 = wx.StaticText(self.parent.tb, -1, text, size=(180, 25), pos=(700,5)) 
            
    def StopGauge(self):
        self.timer.Stop()
        self.busy_gauge.Destroy()
        self.txt1.Destroy()    
        
    def StartThrobber(self):
        self.throbber = throb.Throbber(self.tb, -1, images, size=(50, 50),frameDelay = 0.05, pos=(750,5))
        self.throbber.Start()
        self.txt1 = wx.StaticText(self.tb, -1, "Processing...", size=(100, 25), pos=(800,5))        
        
    def TimerHandler(self, event):
        try:
            self.busy_gauge.Pulse()
        except wx.PyDeadObjectError:
            self.timer.Stop()
        event.Skip()
        
    def OnKeyDown(self, event):
        print "OnKeyDown"
        self.notebook.GetActiveChild().OnKeyDown(event)
        event.Skip()
        
    def OnDoClose(self, evt):
        # Close all ChildFrames first else Python crashes
        for m in self.notebook.GetChildren():
            if isinstance(m, aui.AuiMDIClientWindow):
                for k in m.GetChildren():
                    if isinstance(k, DrawPanel):
                        k.Close()  
        evt.Skip()

class DrawPanel(wx.Panel): 
    def __init__(self, parent, MSfilename, startScan):
        #self.dragController = None
        self.parent = parent
        self.msdb = MS_Data_Manager(self)
        if MSfilename:
            self.msdb.addFile(MSfilename)
            self.msdb.active_file = 0
        else:
            self.msdb.active_file = None
        print self.msdb.active_file
        wx.Panel.__init__(self, parent.notebook, size=(1690, 1050))
        self.SetBackgroundColour("White")
        self.e = None
        self.right_shift = False
        size = self.ClientSize
        self._buffer = wx.EmptyBitmap(*size)
        self.f = lambda a, l:min(l,key=lambda x:abs(x-a)) #function used later
        self.mb = parent.parent.MakeMenuBar()
        self.AddToParentMenuBar()
        self.parent.parent.SetMenuBar(self.mb)        

        active_image_file = os.path.join(installdir, r'image\pp3.jpg')
        xls_image_file = os.path.join(installdir, r'image\microsoft-office-excel-2007-logo.png')
        inactive_image_file = os.path.join(installdir, r'image\pp1.jpg')
        lock_image_file = os.path.join(installdir, r'image\lock.jpg')
        mascot_image_file = os.path.join(installdir, r'image\mascot.png')
        start_image = wx.Image(active_image_file)
        start_image.Rescale(30, 30)
        self.active_image = wx.BitmapFromImage(start_image)
        start_image = wx.Image(inactive_image_file)
        start_image.Rescale(30, 30)
        self.inactive_image = wx.BitmapFromImage(start_image)
        start_image = wx.Image(xls_image_file)
        start_image.Rescale(30, 30)
        self.xls_image = wx.BitmapFromImage(start_image)
        start_image = wx.Image(lock_image_file)
        start_image.Rescale(30, 30)
        self.lock_image = wx.BitmapFromImage(start_image)
        start_image = wx.Image(mascot_image_file)
        start_image.Rescale(30, 30)
        self.mascot_image = wx.BitmapFromImage(start_image)
        
        size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(size.width, size.height)
        
        #self.SetIcon(wx.Icon(installdir + r'\image\multiplierz.ico'))
        self.Window = DrawWindow(self, size=(2690, 1850))   #(1690, 850)
        self.Window.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Window.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Window.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Window.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Window.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        
        #self.Window.Bind(wx.EVT_SIZE, self.OnSize, self.Window)
        
        #self.Bind(wx.EVT_MOTION, self.OnMotion)        
        #BufferedWindow.__init__(self)   
        self.area_tb = None
        self.right_down_pos = None
        self.average_start = None
        self.area_time = None
        #----------------THIS WORKED
        ##self.dragController = DragController(self, None, pos=self.drag_coords)
    
        self.alt_drag_start = None
        self.postup = None
        self.found = None
    
    #def OnSize(self, event):
        #print 'SIZING.'
        #event.Skip()
    
    def OnClose(self, event):
        # It doesn't seem to be necessary to explicitly delete data on 
        # file close, but in case it is.
        #for filedata in self.msdb.files.values():
            #for datathing in filedata.values():
                #del datathing
            
        #print "FOOBAR %s" % self
        
        
        event.Skip()
        
    def AddToParentMenuBar(self):
        mb = self.parent.parent.MakeMenuBar(full=True)
        self.parent.parent.SetMenuBar(mb)    

    def OnXICAddTraceStyle(self, event):
        tsize = (24,24)
        active = self.msdb.active_file
        currentFile = self.msdb.files[self.msdb.Display_ID[active]]        
        if currentFile['xic_style'] == 'NEWTRACE':
            currentFile['xic_style'] = 'OVERLAY'
            self.parent.parent.tb.SetToolNormalBitmap(150, wx.BitmapFromImage(wx.Image(installdir + r'\image\Overlay.png').Rescale(*tsize)))  
            help_string = "XIC overlays on last trace"
            self.parent.parent.tb.SetToolLongHelp(150, help_string)
            self.parent.parent.tb.SetToolShortHelp(150, help_string)
        elif currentFile['xic_style'] == 'OVERLAY':
            currentFile['xic_style'] = 'NEWTRACE'        
            self.parent.parent.tb.SetToolNormalBitmap(150, wx.BitmapFromImage(wx.Image(installdir + r'\image\Add new trace.png').Rescale(*tsize)))
            help_string = "XIC adds to new window"
            self.parent.parent.tb.SetToolLongHelp(150, help_string)
            self.parent.parent.tb.SetToolShortHelp(150, help_string)            

    def AddRawFile(self, file):
        self.files.append(file)

    def get_single_file(self, caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
        dlg = wx.FileDialog(None, caption, pos = (2,2), wildcard = wx_wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath()
            dir = dlg.GetDirectory()
            #print filename
            #print dir
        else:
            return None, None
        dlg.Destroy()
        return filename, dir

    def OnChangeSettings(self, event):
        active = self.msdb.active_file
        currentFile = self.msdb.files[self.msdb.Display_ID[active]]
        settings_frame = Settings.SettingsFrame(self, currentFile["settings"])
        settings_frame.Show()
    
    def OnOpen(self, event):
        if self.msdb.getDisplayWindows() < 2:
            rawfile = mzGUI.file_chooser('Choose RAW File(s)', wildcard='MS files (*.raw,*.wiff, *.t2d, *.mgf)|*.raw;*.wiff;*.t2d;*.mgf')
            if not rawfile:
                return
            
            dir = os.path.dirname(rawfile)
            #rawfile, dir = self.get_single_file("Select raw file...", 'MS files (*.raw,*.wiff, *.t2d)|*.raw;*.wiff;*.t2d')
            self.Window.Refresh()
            self.msdb.addFile(rawfile)
            print "A2"
            print self.msdb.active_file
            if self.msdb.active_file == None:
                self.msdb.active_file = 0
                self.SetTitle(os.path.basename(self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["FileAbs"]))
            else:
                active = self.msdb.active_file
                self.parent.SetPageText(self.parent.GetSelection(), "Active File: " + os.path.basename(self.msdb.files[self.msdb.Display_ID[active]]["FileAbs"]))
            print self.msdb.active_file
            self.Window.UpdateDrawing()
            self.Refresh()        
        else:
            dlg = wx.MessageDialog(self, 'Max Display Files = 2!', 'Alert', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()            

    def OnClose_not_used(self, event):
        '''
        Need to:
        (1) Close data File
        (2) delete entry from Display_ID
        (3) delete file from files
        (4) re-order Display_ID queue
        '''
        print "CLOSING"
        active = self.msdb.active_file
        self.msdb.files[self.msdb.Display_ID[active]]["m"].close()
        del self.msdb.files[self.msdb.Display_ID[active]]
        print "B4"
        print self.msdb.Display_ID.keys()
        del self.msdb.Display_ID[active]
        print self.msdb.Display_ID.keys()
                
        if self.msdb.Display_ID.keys():
            shift_set = filter(lambda x: x>active, self.msdb.Display_ID.keys())
            if shift_set:
                shift_set.sort()
                for key in shift_set:
                    self.msdb.Display_ID[key-1] = self.msdb.Display_ID[key]
                    del self.msdb.Display_ID[key]
            if self.msdb.active_file: #If active file was > 0, make active file previous one
                self.msdb.active_file -= 1
            print self.msdb.Display_ID.keys()
        else:
            self.msdb.active_file=None
            self.SetTitle("Blank Window")
        if len(self.msdb.Display_ID.keys()) == 1:
            self.SetTitle(os.path.basename(self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["FileAbs"]))
        if self.msdb.active_file != None:
            self.msdb.set_axes()
        self.Window.UpdateDrawing()
        self.Refresh()

    def OnOpenSpecBase(self, event):
        print self
        if SpecBase_aui3.SpecFrame not in self.parent.ObjectOrganizer.ActiveObjects:
            self.sb = SpecBase_aui3.SpecFrame(self.parent.parent, -1, self.parent.ObjectOrganizer)
            self.parent.parent._mgr.AddPane(self.sb, aui.AuiPaneInfo().Name("SpecBase").MaximizeButton(True).MinimizeButton(True).
                                            Caption("SpecStylus").Right().
                                            MinSize(wx.Size(50, 210)))
            self.sb.aui_pane_obj = self.parent.parent._mgr.GetPane(self.sb)
                                
            self.parent.parent._mgr.Update() 
            self.parent.parent._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.sb.OnClose)
        else:
            self.sb = self.parent.ObjectOrganizer.ActiveObjects[SpecBase_aui3.SpecFrame]
    
    def OnSendXICToSpecBase(self,event):
        if SpecBase_aui3.SpecFrame not in self.parent.ObjectOrganizer.ActiveObjects:
            messdog = wx.MessageDialog(self, 'SpecBase is not currently active', 
                                       'Could not send to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()            
            return        
        
        elif not self.parent.ObjectOrganizer.ActiveObjects[SpecBase_aui3.SpecFrame].tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'No SpecStylus database has been opened', 
                                       'Could not send to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return                
        
        xic = self.make_xic_object(None)
        
        SpecStylus = self.parent.ObjectOrganizer.getObjectOfType(SpecBase_aui3.SpecFrame)
                        
        node = SpecStylus.tc.tree.GetSelection()
                        
        title = 'XIC'
        item = SpecStylus.tc.tree.AppendItem(node, title)         
                            
        mxe = SpecBase_aui3.multiRICentry(None, rawfile=xic.rawfile, data=xic.data, sequence='', title='XIC', xr=xic.xr, time_range=xic.time_range, 
                            xic_mass_ranges=xic.xic_mass_ranges, xic_filters=xic.xic_filters, notes='', xic_scale=xic.xic_scale, 
                            xic_max=xic.xic_max, active_xic=xic.active_xic, xic_view=xic.xic_view)
        
        SpecStylus.tc.tree.SetPyData(item, {"type":"XIC", "flag":"experiment", "exp":'Title', "xic_data": mxe, "raw_xic": xic})
        #Do we need a base entry?  Why not just pass the spec object?
        SpecStylus.TreeRefresh()                           
    
    def On_Set_Ion_Label_Tolerance(self, event):
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]] 
        
        dlg = wx.TextEntryDialog(self, 'Enter label threshold (Da) \n(0 to go by instrument default)', 'Set fragment ion label threshold', str(currentFile['settings']['ionLabelThresh']))
        if dlg.ShowModal() == wx.ID_OK:
            try:
                currentFile['settings']['ionLabelThresh'] = float(dlg.GetValue())
            except:
                wx.MessageBox("Enter a floating point value")      
            self.msdb.set_axes()
            self.Window.UpdateDrawing()
            self.Window.Refresh()
        
    def PropagateXICsInWindow(self, event):
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        self.copyfrom = xicFrame(self, self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]], self.msdb.active_file)
        entries = self.copyfrom.GetXICEntries()
        for k, file_member in enumerate(self.msdb.files.keys()):          
            if k != self.msdb.active_file:
                #print "Building XICs..."
                busy = PBI.PyBusyInfo("Propagating XICs...", parent=None, title="Processing...")
                proc = ProcFrame(None)
                proc.Show()
                proc.Update()
                proc.Refresh()                    
                wx.Yield()                    
                self.frm = xicFrame(self, self.msdb.files[self.msdb.Display_ID[k]], k)
                for i in range(0, entries):
                    self.frm.grid.SetCellValue(i, 0, self.copyfrom.grid.GetCellValue(i,0))
                    self.frm.grid.SetCellValue(i, 1, self.copyfrom.grid.GetCellValue(i,1))
                    self.frm.grid.SetCellValue(i, 2, self.copyfrom.grid.GetCellValue(i,2))
                    self.frm.grid.SetCellValue(i, 3, self.copyfrom.grid.GetCellValue(i,3))
                    self.frm.grid.SetCellValue(i, 5, self.copyfrom.grid.GetCellValue(i,5))
                    self.frm.grid.SetCellValue(i, 6, self.copyfrom.grid.GetCellValue(i,6))
                    self.frm.grid.SetCellValue(i, 7, self.copyfrom.grid.GetCellValue(i,7))
                    self.frm.grid.SetCellValue(i, 8, self.copyfrom.grid.GetCellValue(i,8))
                    self.frm.mark_base.append({})

                self.frm.OnClick(None)
                self.frm.Destroy()
                del busy
                proc.Destroy()
    
    def XICReport(self, event):
        text = ''
        pages = self.parent.GetPageCount()
        #current_page = self.parent.GetSelection()
        print self.max_tables
        for i in range(0, pages):        #-----------Go through each page
            pg = self.parent.GetPage(i)  
            for k, file_member in enumerate(pg.msdb.files.keys()): #------Go through each file in each page
                currentFile = pg.msdb.files[pg.msdb.Display_ID[k]]
                #----- FILE, FILTER, MZ RANGE, TITLE,  PEAK HEIGHT
                filters = currentFile['filters']
                ranges = currentFile['xic_mass_ranges']
                titles = currentFile['xic_title']
                intens = pg.max_tables
                for j in range(0, len(intens)):
                    for t in range(0, len(intens[j])):
                        text += currentFile['Filename'] + '\t' + filters[j][t] + '\t' + str(ranges[j][t]) + '\t' + titles[j][t] + '\t' + str(intens[j][t]) + '\n'
                        print text
        data = wx.TextDataObject()
        data.SetText(str(text))
        #if wx.Clipboard.Open():
        if wx.TheClipboard.Open():
            yo = wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()        
        #wx.Clipboard.SetData(data)
                
    def PropagateXICsAllWindows(self, event):
        #-------------self.parent is the AUI notebook
        #-------------GetPage returns Drawpanel, which has msbd
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        self.copyfrom = xicFrame(self, self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]], self.msdb.active_file) 
        entries = self.copyfrom.GetXICEntries()
        
        pages = self.parent.notebook.GetPageCount()
        current_page = self.parent.notebook.GetSelection()
        for i in range(0, pages):
            if i != current_page:
                pg = self.parent.notebook.GetPage(i)
                print pg.msdb
                #print "NOT THIS PAGE"
                for k, file_member in enumerate(pg.msdb.files.keys()):          
                    busy = PBI.PyBusyInfo("Propagating XICs...", parent=None, title="Processing...")
                    #proc = ProcFrame(None)
                    #proc.Show()
                    #proc.Update()
                    #proc.Refresh()                    
                    wx.Yield()                    
                    self.frm = xicFrame(self, pg.msdb.files[pg.msdb.Display_ID[k]], k)
                    for i in range(0, entries):
                        self.frm.grid.SetCellValue(i, 0, self.copyfrom.grid.GetCellValue(i,0))
                        self.frm.grid.SetCellValue(i, 1, self.copyfrom.grid.GetCellValue(i,1))
                        self.frm.grid.SetCellValue(i, 2, self.copyfrom.grid.GetCellValue(i,2))
                        self.frm.grid.SetCellValue(i, 3, self.copyfrom.grid.GetCellValue(i,3))
                        self.frm.grid.SetCellValue(i, 5, self.copyfrom.grid.GetCellValue(i,5))
                        self.frm.grid.SetCellValue(i, 6, self.copyfrom.grid.GetCellValue(i,6))
                        self.frm.grid.SetCellValue(i, 7, self.copyfrom.grid.GetCellValue(i,7))
                        self.frm.grid.SetCellValue(i, 8, self.copyfrom.grid.GetCellValue(i,8))

                        self.frm.grid.SetCellValue(i, 13, self.copyfrom.grid.GetCellValue(i,13))
                        
                        self.frm.mark_base.append({})
                        
                                
                    self.frm.OnClick(None)
                    self.frm.Destroy()
                    del busy
                    #proc.Destroy() 
                pg.msdb.set_axes() 
                pg.Window.UpdateDrawing()
                pg.Window.Refresh()
                
            else:
                #print "THIS PAGE"
                self.PropagateXICsInWindow(None)
                
    

    def make_xic_object(self, event):
        '''
                
        Code for drag and drop xic
    
        
        '''                
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        #if currentFile['Filename'].lower().endswith('mgf'):
        #    wx.MessageBox('XIC operations are not supported on MGF files.')
        #    print "Not making XIC object for MGF file."
        #    return
        
        data = currentFile["xic"]
        xr = currentFile["xr"]
        xic_filters = currentFile["filters"]
        xic_mass_ranges = currentFile["xic_mass_ranges"]
        tr = currentFile["time_ranges"][0]
        xic_view = currentFile['xic_view']
        active_xic = currentFile['active_xic']
        xic_max = currentFile['xic_max']
        xic_scale = currentFile['xic_scale']
        rawfile = currentFile["FileAbs"]
    
        xic = XICObject.XICObject(rawfile, data, xr, tr, xic_mass_ranges, xic_filters, xic_scale, xic_max, active_xic, xic_view)
                
        return xic        

    def make_spectrum_object(self, event):
        '''
        
        Code for drag and drop spectrum
        
        
        '''
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        if currentFile['vendor'] in ['Thermo', 'mgf']:
            filt = currentFile["filter_dict"][currentFile["scanNum"]]
        #elif currentFile['vendor'] == 'ABI':
        #    filt = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])
        else:
            filt = ''
        vendor = currentFile['vendor']
        
        profile = False
        if filt.find("+ p")>-1: profile = True
        
        detector = None
        if filt.find("FTMS")>-1:
            detector = "FT"
        elif filt.find("ITMS")>-1:
            detector = "IT"
        elif filt.find("TOF")>-1:
            detector = "TOF"
        elif filt.find("MGF")>-1:
            detector = 'MGF'
            
        scan_type = None
        if filt.find("ms2")>-1:
            scan_type = "MS2"
        elif filt.find("Full ms ")>-1:
            scan_type = "MS1"
        if filt.find("etd")>-1:
            scan_type = 'etd'
        if vendor == 'ABI-MALDI':
            if filt.find("_MSMS_") > -1:
                scan_type = "MS2"
            else:
                scan_type = "MS1"
        
        scanNum = currentFile["scanNum"]
               
        # GETS SCAN DATA HERE
        
        if vendor == "Thermo":
            if profile:
                if filt.find('FTMS')>-1:
                    scan_data = currentFile["m"].scan(scanNum)
                    cent_data = currentFile['m'].rscan(scanNum)
                elif any([filt.find(x) for x in ['TOF', 'Q1', 'Q3']]):
                    scan_data= currentFile["m"].scan(scanNum)
                    cent_data = currentFile['m'].scan(scanNum, centroid=True)
            else:
                scan_data = currentFile["m"].scan(scanNum)
                cent_data = None
        elif vendor == 'mgf':
            scan_data = currentFile["m"].scan(scanNum)
            cent_data = currentFile["m"].scan(scanNum)
        elif vendor == 'ABI':
            scan_data = currentFile["m"].scan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'])
            cent_data = currentFile["m"].cscan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'], algorithm=currentFile['settings']['abi_centroid'], eliminate_noise = currentFile['settings']['eliminate_noise'], step_length = currentFile['settings']['step_length'], peak_min = currentFile['settings']['peak_min'], cent_thresh = current['settings']['threshold_cent_abi'])
        elif vendor == "ABI-MALDI":
            scan_data = currentFile["scan"]
            cent_data = None
        else:
            scan_data = None
            cent_data = None
        
        processed_scan_data = currentFile["processed_data"] 
        charge = None
        varmod = ''
        fixedmod = ''
        if scan_type in ['MS2', 'etd']:
            seqkey = 'Peptide Sequence'
            varmodkey = 'Variable Modifications'
            if currentFile['SearchType'] not in ['Mascot', 'X!Tandem', 'COMET']:
                seqkey = 'Annotated Sequence'
                varmodkey = 'Modifications'
            try:
                if vendor in ['Thermo', 'mgf']:
                    seq = currentFile["ID_Dict"][currentFile["scanNum"]][seqkey]
                    varmod = currentFile["ID_Dict"][currentFile["scanNum"]][varmodkey]
                    fixedmod = currentFile["fixedmod"]
                elif vendor == 'ABI':
                    seq = currentFile["ID_Dict"][(currentFile["scanNum"], currentFile["experiment"])][seqkey]
                    varmod = currentFile["ID_Dict"][(currentFile["scanNum"], currentFile["experiment"])][varmodkey]
                    fixedmod = currentFile["fixedmod"]                    
            except:
                try:
                    seq = currentFile['overlay_sequence']
                    varmod = ''
                    fixedmod = ''
                except:
                    seq = ''
                    varmod = ''
                    fixedmod = ''       
                    
            peptide_container = mz_core.create_peptide_container(seq, varmod, fixedmod)
            sequence = ''
            for member in peptide_container:
                sequence += member
            try:
                charge = currentFile["ID_Dict"][currentFile["scanNum"]]["Charge"]
            except:
                charge = 2
            if vendor == "ABI-MALDI":
                charge = 1
        elif scan_type == "MS1":
            sequence = 'MS1, scan: ' + str(currentFile["scanNum"])
            varmod = ''
        if not sequence:
            sequence = 'MS2, scan: ' + str(currentFile["scanNum"])
        
        display_range = (currentFile['scan low mass'],currentFile['scan high mass'])
        mass_ranges = currentFile["mass_ranges"]
        score = None
        try:
            score = currentFile['score']
        except:
            score = 0
        
        scan = currentFile["scanNum"]
        
        if currentFile['vendor'] in ['Thermo', 'mgf']:
            filt = currentFile["filter_dict"][currentFile["scanNum"]]
        elif currentFile['vendor'] == 'ABI':
            filt = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]       
        
        rawfile = currentFile["FileAbs"]
        
        spec = SpecObject.SpecObject(vendor, profile, detector, scan_type, scan_data, cent_data, processed_scan_data, filt, display_range, mass_ranges, score,
                 sequence, varmod, fixedmod, scan, charge, rawfile)
        
        return spec

    def OnSendToSpecBase(self, event):
        '''
        
        Code to send spectrum to spec stylus.
        
        
        '''
        
        if (SpecBase_aui3.SpecFrame not in self.parent.ObjectOrganizer.ActiveObjects):
            messdog = wx.MessageDialog(self, 'SpecStylusis not currently active', 
                                       'Could not send to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return
        elif not self.parent.ObjectOrganizer.ActiveObjects[SpecBase_aui3.SpecFrame].tc.tree.GetRootItem().IsOk():
            messdog = wx.MessageDialog(self, 'No SpecStylus database has been opened', 
                                       'Could not send to SpecBase', style = wx.OK)
            messdog.ShowModal()
            messdog.Destroy()
            return            
        
        spec = self.make_spectrum_object(None)
        #print "Spectrum object created."        
        
        SpecStylus = self.parent.ObjectOrganizer.getObjectOfType(SpecBase_aui3.SpecFrame)
        
        node = SpecStylus.tc.tree.GetSelection()
                        
       
            
        title = spec.sequence 
        item = SpecStylus.tc.tree.AppendItem(node, title) 
    
        be = SpecBase_aui3.BaseEntry(None, sequence=spec.sequence, filter=spec.filter, title="Mass Spectrum", charge=spec.charge, 
                   full_range=spec.display_range, mass_ranges=spec.mass_ranges, scan=spec.scan, 
                   scan_data=spec.scan_data, cent_data=spec.cent_data, vendor=spec.vendor, detector=spec.detector, profile=spec.profile, 
                   scan_type=spec.scan_type, varmod=spec.varmod, fixedmod=spec.fixedmod, mascot_score=spec.score, 
                   processed_scan_data=spec.processed_scan_data)
    
        SpecStylus.tc.tree.SetPyData(item, {"type":"specfile", "flag":"experiment", "exp": 'Title', "spectrum_data": be, "raw_spec": spec})  #self.window.tc.tree.GetItemText(node)
        #Do we need a base entry?  Why not just pass the spec object?
        SpecStylus.TreeRefresh()

    def OnSaveImage(self, event):
        pngfile, dir = self.get_single_file("Select image file...", "PNG files (*.png)|*.png")
        if pngfile:
            self.img.SaveFile(pngfile,wx.BITMAP_TYPE_PNG)

    def OnSaveSVG(self, event):
        svgfile, dir = self.get_single_file("Select image file...", "SVG files (*.svg)|*.svg")
        if not svgfile:
            return
        
        busy = PBI.PyBusyInfo("Saving SVG, please wait...", parent=None, title="Processing...")
        wx.Yield()
        buffersize = self.Window._Buffer.GetSize()
        self.svgDC = wx.SVGFileDC(svgfile, width = buffersize.width/2.0, height = buffersize.height/2.0, dpi = 72)
        #currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        #print "SAVING...(lines)"
        for line in self.msdb.svg["lines"]:
            if len(line)==4:
                self.svgDC.DrawLine(*line)
            else:
                self.svgDC.SetPen(line[4])
                self.svgDC.DrawLine(line[0], line[1], line[2], line[3])
        #print "SAVING...(text)"
        for text in self.msdb.svg["text"]:
            if len(text)==4:
                self.svgDC.DrawRotatedText(*text)
            else:
                self.svgDC.SetTextForeground(text[4])
                self.svgDC.SetFont(text[5])
                self.svgDC.DrawRotatedText(text[0],text[1],text[2],text[3])
        #print "Saving drawlines..."
        for pointList in self.msdb.svg["pointLists"]:
            self.svgDC.DrawLines(pointList)  #.DrawLine(*line)
        #print "DONE."
        self.svgDC.Destroy()
        del busy

    def OnSavePDF(self, event):
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF
        except ImportError:
            wx.MessageBox("PDF creation requires ReportLab and svglib to be installed.")
            return
            
        pdffile, dir = self.get_single_file("Select image file...", "PDF files (*.pdf)|*.pdf")
        if not pdffile:
            return
        
        tempsvg = pdffile + 'TEMP.svg'
        
        busy = PBI.PyBusyInfo("Saving PDF, please wait...", parent=None, title="Processing...")
        wx.Yield()
        buffersize = self.Window._Buffer.GetSize()
        self.svgDC = wx.SVGFileDC(tempsvg, width = buffersize.width/2.0, height = buffersize.height/2.0, dpi=72)
        for line in self.msdb.svg["lines"]:
            if len(line)==4:
                self.svgDC.DrawLine(*line)
            else:
                self.svgDC.SetPen(line[4])
                self.svgDC.DrawLine(line[0], line[1], line[2], line[3])
        #print "SAVING...(text)"
        for text in self.msdb.svg["text"]:
            if len(text)==4:
                self.svgDC.DrawRotatedText(*text)
            else:
                self.svgDC.SetTextForeground(text[4])
                self.svgDC.SetFont(text[5])
                self.svgDC.DrawRotatedText(text[0],text[1],text[2],text[3])
        #print "Saving drawlines..."
        for pointList in self.msdb.svg["pointLists"]:
            self.svgDC.DrawLines(pointList)  #.DrawLine(*line)
        #print "DONE."
        self.svgDC.Destroy()
        
        svgdata = svg2rlg(tempsvg)
        renderPDF.drawToFile(svgdata, pdffile)
        os.remove(tempsvg)
        
        del busy        

    def LoadDb(self,event,xlsfile,searchType):
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        currentFile["SearchType"]=searchType
        currentFile["xlsSource"]=xlsfile
        if not os.path.exists(xlsfile[:-4] + '.db'):
            busy = PBI.PyBusyInfo("Making database, please wait...", parent=None, title="Processing...")
            wx.Yield()
            dbase = self.MakeDatabase(xlsfile, currentFile["SearchType"])
            del busy
        else:
            dbase = xlsfile[:-4] + '.db'
        currentFile["database"] = dbase
        busy = PBI.PyBusyInfo("Reading database, please wait...", parent=None, title="Processing...")
        wx.Yield()
        currentFile["mzSheetcols"] = db.get_columns(dbase, table = 'peptides' if currentFile["SearchType"] == "Mascot" else 'fdr')
        if currentFile["SearchType"] == "Mascot":
            currentFile["rows"] = db.pull_data_dict(dbase, 'select * from "peptides"')
        
        for row in currentFile['rows']:
            if currentFile['vendor']=='Thermo':
                if currentFile["SearchType"] == "Mascot":
                    row['scan']=int(row['Spectrum Description'].split(".")[1])
                if currentFile["SearchType"] == "Pilot":
                    row['scan']=int(row['Spectrum'].split(".")[3])
            elif currentFile['vendor']=='ABI':
                row['scan']=int(row['Spectrum Description'].split(".")[3])-1
                try:
                    row['experiment']=int(row['Spectrum Description'].split(".")[4])-1
                except:
                    #print row['Spectrum Description']
                    asds
        del busy
        busy = PBI.PyBusyInfo("Reading Header & creating ID List, please wait...", parent=None, title="Processing...")
        wx.Yield()
        if currentFile["SearchType"] == "Mascot":
            #print "PULLING FIXED MODS..."
            self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"] = mz_core.pull_mods_from_mascot_header(xlsfile)
            if "Quantitation method" in self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"].keys():
                print "Quant method detected!"
                currentFile["SILAC"]["mode"]=True
                currentFile["SILAC"]["method"]=currentFile["header"]["Quantitation method"]
                print currentFile["SILAC"]["method"]
            self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["fixedmod"] = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"]["Fixed modifications"]
        #print "Building ID list..."
        currentFile["ID_Dict"]= self.build_ID_dict(currentFile["rows"], currentFile["mzSheetcols"], currentFile["Filename"],currentFile["vendor"])
        del busy
        self.Refresh()
        self.dbFrame = dbFrame.dbFrame(self)
        self.dbFrame.Show(True)             

    def read_ID_base(self, dir):
        file = dir + '\\mascot_ID_base.txt'
        file_r = open(file, 'r')
        lines = file_r.readlines()
        self.datDict = {}
        for line in lines:
            temp = line.split("\t")
            self.datDict[str(dir + '\\' + temp[1].strip() + '.mgf.xls').lower()] = dir + '\\' + 'F%s.dat' % (temp[0].zfill(6))
        #print self.datDict

    def OnJump(self, event):
        dlg = wx.TextEntryDialog(self, 'Scan Number', 'Jump To Scan')

        if dlg.ShowModal() == wx.ID_OK:
            activeFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
            if activeFile['vendor'] == 'Thermo':
                activeFile["scanNum"]=int(dlg.GetValue())
                self.msdb.set_scan(activeFile["scanNum"], self.msdb.active_file)
                self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"])
            elif activeFile['vendor'] == 'ABI':
                scan, experiment = dlg.GetValue().split(",")
                activeFile["scanNum"]=int(scan.strip())
                activeFile["experiment"]=experiment.strip()
                self.msdb.set_scan(activeFile["scanNum"], self.msdb.active_file)
                self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"], vendor = 'ABI')
            self.Window.UpdateDrawing()
            self.Refresh()

        dlg.Destroy()

    def On_XIC_range(self, event):
        dlg = wx.TextEntryDialog(self, 'Start time, Stop time', 'Set time range')
        if dlg.ShowModal() == wx.ID_OK:
            activeFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
            if ',' in dlg.GetValue():
                entry = dlg.GetValue().split(",")
            elif '-' in dlg.GetValue():
                entry = dlg.GetValue().split("-")   
            else:
                wx.MessageBox("Range must be in the form '10-20' or '10,20'.")
                return
            start = float(entry[0].strip())
            stop = float(entry[1].strip())
            activeFile["time_ranges"]=[(start, stop)]
            self.Window.UpdateDrawing()
            self.Refresh()
        dlg.Destroy()

    def On_mz_range(self, event):
        dlg = wx.TextEntryDialog(self, 'Start mz-Stop mz or Center, Width', 'Set mz range')
        if dlg.ShowModal() == wx.ID_OK:
            activeFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
            if dlg.GetValue().find("-") > -1:
                entry = dlg.GetValue().split("-")
                low_mass = float(entry[0].strip())
                hi_mass = float(entry[1].strip())
            elif dlg.GetValue().find(",") > -1:
                entry = dlg.GetValue().split(",")
                center = float(entry[0].strip())
                width = float(entry[1].strip())
                hi_mass = center + width
                low_mass = center - width
            activeFile["newl"]=hi_mass #LAST MASS
            activeFile['newf']=low_mass #FIRST MASS
            activeFile["mass_ranges"]=[]
            current_mz = low_mass
            step = float(activeFile["newl"]-activeFile["newf"])/float(activeFile["axes"])
            for i in range(0, activeFile["axes"]):
                activeFile["mass_ranges"].append((current_mz, current_mz + step))
                current_mz += step
            self.Window.UpdateDrawing()
            self.Refresh()

        dlg.Destroy()

    def On_inten_range(self, event):
        '''
        
        Sets intensity scaling for mass spectrum.  Typing '*' turns off scaling.
        
        '''
        dlg = wx.TextEntryDialog(self, '', 'Set Max Intensity')
        if dlg.ShowModal() == wx.ID_OK:
            
            if dlg.GetValue() == '*':
                activeFile["intensity_scaling"]=0
            else:
                activeFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
                intensity = float(dlg.GetValue())
                activeFile["intensity_scaling"]=intensity
            
            self.Window.UpdateDrawing()
            self.Refresh()

        dlg.Destroy()    
                    
    def build_ID_dict(self, rows, cols, filename, vendor = 'Thermo'):
        '''
        
        Makes a dictionary of scans to ID (i.e. search result info).
        
        '''
        try:
            currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
            spec_lookup = "Spectrum Description" if currentFile['SearchType']=='Mascot' else "Spectrum"
            spec_index = 0 if currentFile['SearchType']=='Mascot' else 3
            ID_Dict = {}
            counter = 0
            for row in rows:
                if counter % 1000 == 0:
                    print counter
                counter += 1
                scan = row["scan"]
                if vendor == 'ABI':
                    exp = str(row['experiment'])
                if vendor == 'mgf':
                    ID_Dict[currentFile['scan_dict'][scan]]={}
                    for col in cols:
                        ID_Dict[currentFile['scan_dict'][scan]][col]=row[col]
                if vendor == 'Thermo':
                    if "File" not in cols or ("File" in cols and filename.lower()==row[spec_lookup].split(".")[spec_index].lower().replace('_RECAL','')+'.raw'):
                        ID_Dict[scan]={}
                        if "Scan Type" not in cols: #Logic implemented to label CAD/HCD pair with same ID.
                            for col in cols:
                                ID_Dict[scan][col]=row[col]
                        else:
                            for col in cols:
                                ID_Dict[scan][col]=row[col]                        
                            if row['Scan Type'] == "HCD":
                                ID_Dict[scan-1]={}
                                for col in cols:
                                    ID_Dict[scan-1][col]=row[col] 
                            else:
                                ID_Dict[scan+1]={}
                                for col in cols:
                                    ID_Dict[scan+1][col]=row[col]                            
                if vendor == 'ABI':
                    if "File" not in cols or ("File" in cols and filename.lower()==row[spec_lookup].split(".")[spec_index].lower().replace('_RECAL','')+'.raw'):
                        ##print "Found!"
                        ID_Dict[(scan, exp)]={}
                        for col in cols:
                            ID_Dict[(scan, exp)][col]=row[col]
            return ID_Dict
        except:
            wx.MessageBox("Error building ID dictionary!\nAre you sure the report matches your file?")
            return {}

    def dump_ID_Dict(self, dict):
        IDList = dict.keys()
        IDList.sort()
        for member in IDList:
            print str(member) + ' ' + dict[member]["Peptide Sequence"]
    
    def build_ID_list(self, currentFile):
        currentFile["ID_Dict"] = {}
        counter = 0
        for row in currentFile["rows"]:
            if counter % 100 == 0:
                print counter
            counter += 1
            if "File" not in currentFile["mzSheetcols"] or ("File" in currentFile["mzSheetcols"] and currentFile["Filename"].lower()==row["Spectrum Description"].split(".")[0].lower()+'.raw'):
                currentFile["ID_Dict"][scan]={}
                for col in currentFile["mzSheetcols"]:
                    scan = row["scan"]
                    currentFile["ID_Dict"][scan][col]=row[col]

    def MakeDatabase(self, xlsfile, searchtype="Mascot", mgf_dict={}):
        #self.parent.StartGauge(text="Building Database...", color=wx.RED)
        dbase = db.make_database(xlsfile, parent=self, searchtype=searchtype, mgf_dict=mgf_dict)
        #self.parent.StopGauge()
        #self.parent.HideAdjGauge()
        return dbase

    def ReadSheet(self, xlsfile):
        #print "READING SHEET..."
        busy = PBI.PyBusyInfo("Opening xls, please wait...", parent=None, title="Processing...")
        wx.Yield()
        g = PyGaugeDemo(None)
        g.Show()
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        rdr = mzReport.reader(xlsfile, sheet_name = "Data")
        del busy
        g.gauge1.SetRange(len(rdr._data))
        g.Update()
        currentFile["mzSheetcols"] = rdr.columns
        counter = 0
        busy = PBI.PyBusyInfo("Processing xls, please wait...", parent=None, title="Processing...")
        wx.Yield()
        vendor = currentFile["vendor"]
        for row in rdr:
            if vendor == 'Thermo':
                scan = int(row["Spectrum Description"].split(".")[1])
            if vendor == 'ABI':
                scan = int(row["Spectrum Description"].split(".")[3])-1
                exp = int(row["Spectrum Description"].split(".")[4])
                row['experiment']= exp-1
            row["scan"] = scan
            currentFile["rows"].append(row)
            if counter % 50 == 0:
                #print counter
                g.gauge1.SetValue(counter)
                g.Update()
                g.Refresh()
            counter += 1
        rdr.close()
        del busy
        #self.build_ID_list()
        busy = PBI.PyBusyInfo("Reading Header & creating ID List, please wait...", parent=None, title="Processing...")
        wx.Yield()
        #print "PULLING FIXED MODS..."
        self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"] = mz_core.pull_mods_from_mascot_header(xlsfile)
        if "Quantitation method" in self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"].keys():
            print "Quant method detected!"
            currentFile["SILAC"]["mode"]=True
            currentFile["SILAC"]["method"]=currentFile["header"]["Quantitation method"]
            print currentFile["SILAC"]["method"]        
        self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["fixedmod"] = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["header"]["Fixed modifications"]
        #print "Building ID list..."
        currentFile["ID_Dict"]= self.build_ID_dict(currentFile["rows"], currentFile["mzSheetcols"], currentFile["Filename"], vendor)
        g.Destroy()
        del busy
        ##print self.ID_Dict.keys()
        self.Refresh()
        ##print self.rows

    def OnXIC(self, event):
        self.frm = xicFrame(self, self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]], self.msdb.active_file)
        self.frm.Show(True)

    def ions_search(self):
        y_labels = []
        for i, member in enumerate(self.y_ions):
            found, found_mz, found_int = self.search_for_mass(member, self.scan)
            if found:
                y_labels.append(['y'+str(i+1), found_mz, found_int])
        return y_labels

    def CheckLabels(self, loc, labels):
        found = False
        for member in labels:
            if loc > member[0] and loc < member[1]:
                found = True
        return found

    def ConvertPixelToIntensity(self, pixel, axis, file_number):
        currentFile = self.msdb.files[self.msdb.Display_ID[file_number]]
        lastMass = currentFile["mass_ranges"][axis][1]
        firstMass = currentFile["mass_ranges"][axis][0]        
        #yaxis = self.spectrum.axco[axis][1]
        yaxis = currentFile["axco"][axis][1]
        max_int = currentFile["max_int"][axis]
        inten = (float(yaxis[3]-pixel)/float((yaxis[3]-yaxis[1])))*float(max_int)
        return inten    

    def ConvertPixelToTime(self, pixel, file_number):
        currentFile = self.msdb.files[self.msdb.Display_ID[file_number]]
        stop_time = currentFile["time_ranges"][0][1]
        start_time = currentFile["time_ranges"][0][0]
        time = (((pixel - currentFile["xic_axco"][0][0][0])/float(currentFile["xic_axco"][0][0][2]-currentFile["xic_axco"][0][0][0])) * float(stop_time-start_time)) + start_time
        return time

    def ConvertPixelToMass(self, pixel, axis, file_number):
        currentFile = self.msdb.files[self.msdb.Display_ID[file_number]]
        lm = currentFile["mass_ranges"][axis][1]
        fm = currentFile["mass_ranges"][axis][0]
        mr = lm - fm
        pr = currentFile["axco"][0][0][2] - currentFile["axco"][0][0][0]
        mpp = float(mr)/float(pr)
        #mass = (((pixel - currentFile["axco"][0][0][0])/float(currentFile["axco"][0][0][2])) * float(lm-fm)) + fm
        mass = ((pixel - currentFile["axco"][0][0][0]) * mpp)+ fm
        return mass

    def GetAxis(self, ypos):
        axis = 0
        for k in range(0, self.axes):
            if ypos > self.axco[k][1][1] and ypos < self.axco[k][1][3]:
                axis = k
                break
        return axis

    def get_coord(self, pos):
        xic_event = False
        spec_event = False
        if self.mode != "SPEC":
            for member in self.xic_axco:
                #[((50, 550, 450, 550),(50,50,50,550))]
                if pos[0] > member[0][0] and pos[0] < member[0][2] and pos[1] > member[1][1] and pos[1] < member[1][3]:
                    xic_event = True
                    #print "XIC!"
        for member in self.axco:
            if pos[0] > member[0][0] and pos[0] < member[0][2] and pos[1] > member[1][1] and pos[1] < member[1][3]:
                spec_event = True
                #print "SPEC!"
        return xic_event, spec_event

    def OnLeftDown(self, event):
        '''
        
        Manages left button down event.
        
        pos = position
        
        Calls HitTest.  Returns:
            file = Relevant Data File
            e = "XIC" or "SPEC"
            grid = which trace or spectrum axis
            Found = True or False
        
        '''
        #if wx.GetKeyState(wx.WXK_ALT):
            #print "MARK AVERAGE START"
            #self.alt_drag_start = event.GetPositionTuple()
            #return
        
        pos = event.GetPosition()
        self.postup = pos
        found, e, grid, file = self.msdb.HitTest(pos)
        self.found = found
        self.grid=grid
        self.file=file
        self.e = e        
        
        if wx.GetKeyState(wx.WXK_CONTROL):
            print "DRAG MAKE DATA OBJECT"
            currentPage = self.parent.parent.ctrl.GetPage(self.parent.parent.ctrl.GetSelection())
            self.currentPage = currentPage
            self.currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]            
            if e == "SPEC":
                spec = self.make_spectrum_object(None)
                print "Spectrum."
                data_object = wx.CustomDataObject("scan_data")
                data = cPickle.dumps(spec)
                data_object.SetData(data)
                dropSource = wx.DropSource(self)
                dropSource.SetData(data_object)
                result = dropSource.DoDragDrop(wx.Drag_AllowMove)
                if result == wx.DragMove:
                    print "1"      
            if e == "RIC":
                xic = self.make_xic_object(None)
                print "XIC"
                data_object = wx.CustomDataObject("scan_data")
                data = cPickle.dumps(xic)
                data_object.SetData(data)
                dropSource = wx.DropSource(self)
                dropSource.SetData(data_object)
                result = dropSource.DoDragDrop(wx.Drag_AllowMove)
                if result == wx.DragMove:
                    print "1"                      
                
        if found:
            self.found = found
            self.grid=grid
            self.file=file
            self.e = e            
            if e == "RIC":
                self.msdb.files[self.msdb.Display_ID[file]]['currently_selected_filter']=self.msdb.files[self.msdb.Display_ID[file]]['filters'][grid]
                self.msdb.files[self.msdb.Display_ID[file]]['XICinfo']=[self.msdb.files[self.msdb.Display_ID[file]]['filters'][grid], e, grid, file]
                #print "FILTER:"
                #print self.msdb.files[self.msdb.Display_ID[file]]['currently_selected_filter']
                time = self.ConvertPixelToTime(pos[0], file)
                self.new_startTime = time
                #print time
                self.yaxco = self.msdb.files[self.msdb.Display_ID[file]]['xic_axco'][grid][1]
                self.e = "XIC"
            if e == "SPEC":
                #print grid
                mz = self.ConvertPixelToMass(pos[0], grid, file)
                #print "mz " + str(mz)
                self.msdb.files[self.msdb.Display_ID[file]]["newf"] = mz
                self.yaxco = self.msdb.files[self.msdb.Display_ID[file]]['axco'][grid][1]
                self.e = "SPEC"
        else:
            found, e, file = self.msdb.HitTestThr(pos)
            if found:
                self.e = 'Thr'
                self.file = file
                self.found = found
        event.Skip()        
                
    def set_scan(self, currentFile, file, grid, trace):
        scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
        prev_scan = mz_core.find_MS1(currentFile['scan_dict'], scanNum, "Reverse")
        self.msdb.set_scan(prev_scan, file)
        self.msdb.build_current_ID(self.msdb.Display_ID[file], prev_scan)
        currentFile['newf'] = currentFile['xr'][grid][trace][2]-5
        currentFile['newl'] = currentFile['xr'][grid][trace][3]+8
        step = float(currentFile["newl"]-currentFile["newf"])/float(currentFile["axes"])
        current_mz = currentFile["newf"]
        currentFile["mass_ranges"]=[]
        for i in range(0, currentFile["axes"]):
            currentFile["mass_ranges"].append((current_mz, current_mz + step))
            current_mz += step        

    def OnLeftUp(self, event):
        pos = event.GetPosition()
        
        
        #if wx.GetKeyState(wx.WXK_ALT):
            #print "MARK AVERAGE START"
            #self.alt_drag_start = event.GetPositionTuple()
            #return        
        
        #--------------Was threshold box hit?
        if self.e == 'Thr':
            print "Reset thresh"
            currentFile = self.msdb.files[self.msdb.Display_ID[self.file]] 
            xaxis = currentFile['axco'][0][0]
            yaxis = currentFile['axco'][0][1]   
            max_int = currentFile["max_int"][0]
            #_thr_y1 = xaxis[1] - ((float(thresh)/float(max_int)) * (yaxis[3]-yaxis[1]))
            thresh = (xaxis[1] - pos[1])/(yaxis[3]-yaxis[1]) * float(max_int)
            currentFile["settings"]["label_threshold"][currentFile['vendor']] = thresh
            print "Set"
            print thresh
            self.Window.ClearOverlay()
            self.Window.UpdateDrawing()
            self.Refresh()        
            
        #-------------------------------------CHECK TO SEE IF FEATURE BOXES HIT
        #if currentFile["Features"]:
        if pos: tfound, index, feature = self.msdb.HitTestFeatures(pos)
        if tfound:
            print "HIT!"
            print feature 
            currentFile = self.msdb.files[self.msdb.Display_ID[self.file]] 
            featureData = currentFile['featureByIndex'][feature]
            featurePSMs = currentFile['featureToPSMs'].get(feature, [])
            #To get mass for XIC: currentFile['scanFToPeaks'][(scannum, featurenum)]
            peaks = currentFile['scanFToPeaks'][(currentFile['scanNum'], feature)]
            #a = FeaturePopUp.FeaturePopUp(self, -1, feature, currentFile['featureToPSMs'][feature], pos=(pos[0],pos[1]-50), peaks=peaks)
            a = FeaturePopUp_new.FeaturePopUp(self.parent.parent, -1, feature, featureData, self, featurePSMs)
            self.parent.parent._mgr.AddPane(a, aui.AuiPaneInfo().Right().Caption('Feature # %s' % feature))
            self.parent.parent._mgr.Update()
            #a.Show()
            
        #-------------------------------------CHECK TO SEE IF DELETE XIC HIT
        tfound, tgrid, tfile = self.msdb.HitTestRemoveXIC(pos, 10, 10)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]  
            print "HIT!"
            self.frm = xicFrame(self, currentFile, self.msdb.active_file)
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0) == str(tgrid):
                    self.frm.grid.SetCellValue(k, 4, '1')
                    self.frm.OnClick(None)
                    self.frm.Destroy()
        #-------------------------------------CHECK TO SEE IF EXTRACT XIC BUTTON HIT
        tfound, ttrace, tgrid, tfile = self.msdb.HitTestXICBox(pos, 40)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]
            #JUST HIT EXTRACT A TRACE.
            #WHICH WINDOW?  WHICH TRACE?  NOT ACTIVE.
            #MAKE XIC GRID.  CHANGE WINDOW/TRACE TO MAX WINDOW + 1
            #---------------This code finds the next available window
            self.frm = xicFrame(self, currentFile, self.msdb.active_file)
            winmax = 0
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0):
                    curWin = int(self.frm.grid.GetCellValue(k, 0))
                    if curWin > winmax:
                        winmax = curWin
            winmax += 1
            print winmax
            #--------------This code finds the activated window, goes to the correct trace, and changes the window value of the trace
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0) == str(tgrid):
                    self.frm.grid.SetCellValue(k + ttrace, 0, str(winmax))
                    self.frm.OnClick(None)
                    self.frm.Destroy()
                    break
            print "XTRACT GRID HIT!"
            
            self.Window.UpdateDrawing()
            self.Refresh()          
            
        #-------------------------------------CHECK TO SEE IF ACTIVE TRACE BUTTON HIT
        #tfound, ttrace, tgrid, tfile = self.msdb.HitTestActiveTrace(pos)
        tfound, ttrace, tgrid, tfile = self.msdb.HitTestXICBox(pos, 10)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]
            currentFile['active_xic'][tgrid] = ttrace
            print "TRACE GRID HIT!"
            if not currentFile['xic_view'][tgrid][ttrace]:
                currentFile['xic_view'][tgrid][ttrace] = True
            self.Window.UpdateDrawing()
            self.Refresh()            
            
        #-------------------------------------CHECK TO SEE IF TRACE ON_OFF HIT
        #tfound, ttrace, tgrid, tfile = self.msdb.HitTestTraceOnOff(pos)
        tfound, ttrace, tgrid, tfile = self.msdb.HitTestXICBox(pos, 25)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]
            if currentFile['active_xic'][tgrid] != ttrace:
                currentFile['xic_view'][tgrid][ttrace] = not currentFile['xic_view'][tgrid][ttrace]
            print "CONTROL GRID HIT!"
            self.Window.UpdateDrawing()
            self.Refresh()         
            
        #-------------------------------------CHECK TO SEE IF SPECTRUM/XIC HIT
        found, e, grid, file = self.msdb.HitTest(pos)
        if found:
            self.msdb.active_file = file
            #print file
            currentFile = self.msdb.files[self.msdb.Display_ID[file]]
            #print e
            if self.e == "SPEC":
                if pos != self.postup:
                    currentFile['is_zooming'] = True
                    mz = self.ConvertPixelToMass(pos[0], grid, file)
                    #print "UP:" + str(mz)
                    currentFile["newl"] = mz
                    if currentFile["newl"] < currentFile["newf"]:
                        temp = 0
                        temp = currentFile["newl"]
                        currentFile["newl"] = currentFile["newf"]
                        currentFile["newf"] = temp
                    step = float(currentFile["newl"]-currentFile["newf"])/float(currentFile["axes"])
                    current_mz = currentFile["newf"]
                    currentFile["mass_ranges"]=[]
                    for i in range(0, currentFile["axes"]):
                        currentFile["mass_ranges"].append((current_mz, current_mz + step))
                        current_mz += step
                        
            if self.e == "XIC":
                time = self.ConvertPixelToTime(pos[0], file)
                #print time
                #----------------------------LEFT DOWN AND LEFT UP ON SAME XIC GRID
                if self.grid == grid:
                    if self.postup[0]==pos[0]:
                        #-----------------LEFT DOWN AND UP SAME POSITION IN XIC; GO TO SCAN
                        currentFile["spectrum_style"] = "single scan"
                        currentFile["Processing"] = False
                        #CHECK IF THERE IS A PEPTIGRAM IN WINDOW
                        if 'p' not in currentFile["xic_type"][grid]: # [['x'], ['x', 'x', 'x'], ['p']]
                            if currentFile['vendor']=='Thermo':
                                scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                                self.msdb.set_scan(scanNum, file)
                                self.msdb.build_current_ID(self.msdb.Display_ID[file], scanNum)
                            elif currentFile['vendor']=='mgf':
                                scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                                self.msdb.set_scan(str(scanNum), file)
                                self.msdb.build_current_ID(self.msdb.Display_ID[file], scanNum)                            
                            elif currentFile['vendor']=='ABI':
                                #scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                                #lambda a, l:min(l,key=lambda x:abs(x-a))
                                RTs = [x[0] for x in currentFile["rt2scan"].keys()]
                                rt = self.f(self.new_startTime, RTs)
                                scanNum = currentFile["rt2scan"][(rt, currentFile['rt2exp'][rt])]
                                self.msdb.set_scan(scanNum[0], file) #***NOTE: scanNum here has (Scan, "Exp")
                                self.msdb.build_current_ID(self.msdb.Display_ID[file], (scanNum,currentFile['experiment']), 'ABI')
                        else: #THERE IS A PEPTIGRAM
                            #CHECK TO SEE if time in middle of peptigram
                            print "CHECKING..."
                            trace_types = currentFile["xic_type"][grid]
                            peptidegrams = []
                            for i, member in enumerate(trace_types):
                                if member == 'p':
                                    #print "Found one!"
                                    peptidegrams.append(i)
                            trace_dict = {} #This maps trace # to tuple of (start, stop)
                            for member in peptidegrams:
                                print currentFile['xic'][grid][member]
                                trace_dict[member] = (min(currentFile['xic'][grid][member], key = lambda t:t[0])[0], max(currentFile['xic'][grid][member], key = lambda t:t[0])[0])
                            print trace_dict
                            match = []
                            for key in trace_dict.keys():
                                p_start = trace_dict[key][0]
                                p_stop = trace_dict[key][1]
                                if self.new_startTime > p_start and self.new_startTime < p_stop:
                                    match.append(key)
                            if match and len(match) == 1:
                                #scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                                #prev_scan = mz_core.find_MS1(currentFile['scan_dict'], scanNum, "Reverse")
                                #self.msdb.set_scan(prev_scan, file)
                                #self.msdb.build_current_ID(self.msdb.Display_ID[file], prev_scan)
                                #a = currentFile['xr']
                                #currentFile['newf'] = currentFile['xr'][grid][match[0]][2]-5
                                #currentFile['newl'] = currentFile['xr'][grid][match[0]][3]+8
                                #step = float(currentFile["newl"]-currentFile["newf"])/float(currentFile["axes"])
                                #current_mz = currentFile["newf"]
                                #currentFile["mass_ranges"]=[]
                                #for i in range(0, currentFile["axes"]):
                                    #currentFile["mass_ranges"].append((current_mz, current_mz + step))
                                    #current_mz += step
                                self.set_scan(currentFile, file, grid, match[0])
                            elif match and len(match) > 1 and currentFile['active_xic'][grid] in match:
                                #match = traces that match left click hit
                                #currentFile['active_xic'][grid] = # of the active trace in the grid 
                                index = match.index(currentFile['active_xic'][grid])
                                self.set_scan(currentFile, file, grid, match[index])
                            else:
                                scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                                if currentFile['vendor']=='Thermo':
                                    self.msdb.set_scan(scanNum, file)
                                    self.msdb.build_current_ID(self.msdb.Display_ID[file], scanNum)
                                elif currentFile['vendor']=='ABI':
                                    self.msdb.set_scan(scanNum[0], file) #***NOTE: scanNum here has (Scan, "Exp")
                                    self.msdb.build_current_ID(self.msdb.Display_ID[file], (scanNum,currentFile['experiment']), 'ABI')                                
                    #----------------LEFT DOWN AND UP IN SAME XIC GRID BUT MOVED; SET NEW TIME RANGE
                    else:
                        #print "XIC!"
                        #print "Time: " + str(time)
                        self.new_stopTime = time
                        if wx.GetKeyState(wx.WXK_ALT):
                            # Average scan show.
                            currentFile["spectrum_style"] = "average scan"
                            #averaging_range = self.new_startTime, self.new_stopTime
                            relevant_filter = self.msdb.files[self.msdb.Display_ID[file]]['filters'][grid][currentFile["active_xic"][grid]]

                            worked = self.msdb.set_average_scan(self.new_startTime,self.new_stopTime, 
                                                                relevant_filter, 
                                                                file)
                            #if worked:
                                #self.msdb.set_scan('Averagescan', file)
                            
                            
                            #scanNum = currentFile["rt2scan"][self.f(self.new_startTime, currentFile["rt2scan"].keys())]
                            #self.msdb.set_scan(str(scanNum), file)
                            #self.msdb.build_current_ID(self.msdb.Display_ID[file], scanNum)                             
                        else:
                            # Set XIC time range.
                            if self.new_stopTime < self.new_startTime:
                                temp = self.new_stopTime
                                self.new_stopTime = self.new_startTime
                                self.new_startTime = temp
                            if currentFile['vendor']=='Thermo':
                                currentFile["time_ranges"]=[(self.f(self.new_startTime, currentFile["rt2scan"].keys()), self.f(self.new_stopTime, currentFile["rt2scan"].keys()))]
                            elif currentFile['vendor']=='mgf':
                                currentFile["time_ranges"]=[(self.f(self.new_startTime, currentFile["rt2scan"].keys()), self.f(self.new_stopTime, currentFile["rt2scan"].keys()))]                        
                            elif currentFile['vendor']=='ABI':
                                RTs = [x[0] for x in currentFile["rt2scan"].keys()]
                                #rt = self.f(self.new_startTime, RTs)
                                #scanNum = currentFile["rt2scan"][(rt, currentFile['rt2exp'][rt])]                            
                                currentFile["time_ranges"]=[(self.f(self.new_startTime, RTs), self.f(self.new_stopTime,RTs))]
                else:
                    print "DRAG N DROP XIC TO DIFFERENT LOCATION"
                    self.frm = xicFrame(self, currentFile, self.msdb.active_file)
                    #self.grid = dragged from
                    #grid = dropped on; change self.grid to grid
                    for k in range(0,10):
                        if self.frm.grid.GetCellValue(k, 0) == str(self.grid):
                            self.frm.grid.SetCellValue(k, 0, str(grid))
                            self.frm.OnClick(None)
                            self.frm.Destroy()                    
        self.Window.ClearOverlay()
        self.Window.UpdateDrawing()
        
        try:
            currentFile['is_zooming'] = False
        except:
            pass
        
        self.Refresh()

    def OnRightDown(self, event):
        
        self.right_shift = False
        pos = event.GetPosition()
        found, e, grid, file = self.msdb.HitTest(pos)
        if not found:
            event.Skip()
            return
        self.found = found
        self.e = e
        self.grid = grid
        self.file=file
        if file > -1:
            currentFile = self.msdb.files[self.msdb.Display_ID[file]]
        if e == "SPEC":
            #self.msdb.set_mass_ranges(currentFile["FileAbs"])
            self.right_down_pos = pos
            self.yaxco = self.msdb.files[self.msdb.Display_ID[file]]['axco'][grid][1]
        if e == "RIC":
            if event.ShiftDown():
                print "SHIFT DOWN"
                self.right_shift = True
                self.right_down_pos = pos
                time = self.ConvertPixelToTime(pos[0], file)
                self.average_start = time
                self.yaxco = self.msdb.files[self.msdb.Display_ID[file]]['xic_axco'][grid][1]
                
            else:
                self.right_down_pos = pos
                #currentFile["time_ranges"] = [(currentFile["unzStartTime"], currentFile["unzStopTime"])]
                time = self.ConvertPixelToTime(pos[0], file)
                self.areaTime = time
                print time
                self.yaxco = self.msdb.files[self.msdb.Display_ID[file]]['xic_axco'][grid][1]
                #self.e = "XIC"            
        self.Refresh()

    def OnRightUp(self, event):
        
        
        '''
                
        Handles right mouse button up events.  For example, right click on spectrum zooms out.
        Right click/drag on XIC performs integration.
        Right click/drag on spectrum performs XIC.
        Right click on XIC tab deletes xic.
        
        
        '''        
        
        refresh = True
        #--------------------------------CHECK TO SEE IF DELETE XIC HIT
        pos = event.GetPosition()
        tfound, tgrid, tfile = self.msdb.HitTestRemoveXIC(pos, 10, 10)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]
            if len(currentFile["xic_params"][tgrid]) > 3:
                palette = XICPalette.XICPalette(self, currentFile, tgrid)
                palette.Show()
        tfound, ttrace, tgrid, tfile = self.msdb.HitTestXICBox(pos, 25)
        if tfound:
            currentFile = self.msdb.files[self.msdb.Display_ID[tfile]]
            self.frm = xicFrame(self, currentFile, self.msdb.active_file)
            for k in range(0,10):
                if self.frm.grid.GetCellValue(k, 0) == str(tgrid):
                    self.frm.grid.SetCellValue(k + ttrace, 4, '1')
                    self.frm.OnClick(None)
                    self.frm.Destroy()
                    break
            
            
            self.Window.UpdateDrawing()
            self.Refresh()                 

        found, e, grid, file = self.msdb.HitTest(pos)
        if not found:
            event.Skip
            return
        if file != -1:
            currentFile = self.msdb.files[self.msdb.Display_ID[file]]
        if e == "RIC":
            if not self.right_shift and self.right_down_pos:
                if pos[0] == self.right_down_pos[0]:
                    currentFile["time_ranges"] = [(currentFile["unzStartTime"], currentFile["unzStopTime"])]
                else:
                    #-------------------------------EXECUTING AREA
                    #--NEED ACTIVE
                    if self.areaTime:
                        time = self.ConvertPixelToTime(pos[0], file)
                        startTime = min([time, self.areaTime])
                        stopTime = max([time, self.areaTime])
                        
                        xic = []
                        for member in currentFile['xic'][grid][currentFile['active_xic'][grid]]:
                            if member[0]>startTime and member[0]<stopTime:
                                xic.append(member)
                        aw = AreaWindow.AreaWindow(None, -1, xic)
                        if aw.valid:
                            aw.Show()
                        if self.parent.parent.area_tb:  #self.parent.parent.area_tb
                            current = self.parent.parent.area_tb.areaBox.GetValue()
                            if current:
                                current += '\t'
                            self.parent.parent.area_tb.areaBox.SetValue(current + str(aw.area))
                    
                        
            else:
                if self.average_start:
                    print "Capture average"
                    self.right_shift = False
                    self.average_stop = self.ConvertPixelToTime(pos[0], file)
                    self.average_start_scan = currentFile['rt2scan'][self.f(self.average_start, currentFile["rt2scan"].keys())]
                    self.average_stop_scan = currentFile['rt2scan'][self.f(self.average_stop, currentFile["rt2scan"].keys())]
                    self.average_filter = currentFile["xic_params"][grid][currentFile['active_xic'][grid]][2]
                    #activeFile['scan'] = activeFile['m'].average_scan(activeFile['average_range'][0],activeFile['average_range'][1],activeFile['currently_selected_filter'])
                    print "AVERAGE"
                    currentFile['scan'] = currentFile['m'].average_scan(self.average_start_scan, self.average_stop_scan, self.average_filter)
                    print "DONE"
                    currentFile["spectrum_style"]='average'
                
        if e == "SPEC":
            # Right down and up in same position zooms out.
            if pos == self.right_down_pos:
                self.msdb.set_mass_ranges(currentFile["FileAbs"])
                self.msdb.set_axes()
                self.Window.ClearOverlay()
                if refresh:
                    self.Window.UpdateDrawing()  
                    self.Refresh()    
                return
            
            # otherwise make XIC    
            if not currentFile['vendor'] in ['mgf', 'ABI-MALDI']:
                #self.Window.ClearOverlay()
                dc = wx.BufferedDC(wx.ClientDC(self.Window), self.Window._Buffer)
                dc.DrawText("Building XIC...", pos[0], self.yaxco[1])
                self.Window.Refresh()
                #busy = PBI.PyBusyInfo("Building XIC...", parent=None, title="Processing...")   
                #proc = ProcFrame(None)
                #proc.Show()
                #proc.Update()
                #proc.Refresh()
                #wx.Yield()
                mz1 = self.ConvertPixelToMass(self.right_down_pos[0], grid, file)
                mz2 = self.ConvertPixelToMass(pos[0], grid, file)
                if abs(mz1-mz2)>0.01:
                    currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
                    self.frm = xicFrame(self, currentFile, self.msdb.active_file)
                    #xics = len(currentFile["xic_mass_ranges"])
                    traces = 0
                    wins = len(currentFile["xic_mass_ranges"])
                    for win in range(0, wins):
                        for trace in range(0, len(currentFile["xic_mass_ranges"][win])):
                            traces += 1
                    add_window = wins
                    if currentFile['xic_style'] == 'OVERLAY':
                        add_window = wins - 1
                    if traces < 10:
                        self.frm.grid.SetCellValue(traces, 0, str(add_window))  #WIN
                        self.frm.grid.SetCellValue(traces, 1, str(round(mz1,3))) #START
                        self.frm.grid.SetCellValue(traces, 2, str(round(mz2,3))) #STOP
                        self.frm.grid.SetCellValue(traces, 3, str("Full ms ")) # FILTER
                        self.frm.grid.SetCellValue(traces, 5, str("Auto")) #SCALE
                        self.frm.grid.SetCellValue(traces, 6, str("1")) #VIEW
                        self.frm.grid.SetCellValue(traces, 7, str("1")) #ACTIVE
                        self.frm.grid.SetCellValue(traces, 8, str("x"))
                        self.frm.mark_base.append({})
                        self.frm.OnClick(None)
                        self.frm.Destroy()
                        refresh = False
                #del busy
                #proc.Destroy()
            else:
                wx.MessageBox("XIC not supported for %s" % currentFile['vendor'], "mzStudio")
                
        self.Window.ClearOverlay()
        if refresh:
            self.Window.UpdateDrawing()  
            self.Refresh()
        

    def OnKeyDown(self, event):
        '''
        
        
        Main code for handling mzStudio Key Press events.
        
        
        '''
        key = event.GetKeyCode()
        activeFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        print "KEY: " + str(key)
        
        #if key == 90: # "Z"
            #hi = self.GetHiMass()
            #lo = self.GetLoMass()
            #step = float(hi-lo)/float(self.axes)
            #current_mz = lo
            #self.mass_ranges=[]
            #for i in range(0,3):
                #self.mass_ranges.append((current_mz, current_mz + step))
                #current_mz += step
                
        if key == 65: #"A"
            #print "Activate"
            for i in range (0, self.msdb.getFileNum()):
                if i == self.msdb.active_file:
                    self.msdb.files[self.msdb.Display_ID[i]]["Display"]=True
                else:
                    self.msdb.files[self.msdb.Display_ID[i]]["Display"]=False
            self.msdb.set_axes()
            
        #if key == 72: #"B" RECALIBRATE
        #    print "RECAL"
        #    self.RecalFrame = RecalFrame(self)
        #    self.RecalFrame.Show()        
            
        #if key == 67: #"C"
            ##print "Mark average start"
            #activeFile['average_range']=[activeFile['scanNum']]
            ##print activeFile['average_range']
            
        #if key == 68: #"D"
            ##print "Mark average end"
            #activeFile['average_range'].append(activeFile['scanNum'])
            ##print activeFile['average_range']
            #activeFile['scan'] = activeFile['m'].average_scan(activeFile['average_range'][0],activeFile['average_range'][1],activeFile['currently_selected_filter'])
        
        if key == 87: #"W"  LOCKS FILTER
            if activeFile['filterLock']==None:
                #print "LOCK check"
                if not activeFile['targ_check']:
                    targ_filt = set()
                    for member in activeFile['filter_dict'].values():
                        id = self.msdb.targ.match(member)
                        if id:
                            targ_filt.add(member)
                        id = self.msdb.targ_ms3.match(member)
                        if id:
                            targ_filt.add(member)
                    activeFile["targ_filt"] = list(targ_filt)
                    activeFile['targ_check']=True
                if activeFile["filter_dict"][activeFile['scanNum']] in activeFile["targ_filt"]:
                    #print "locked on filter"
                    activeFile['filterLock']=activeFile["filter_dict"][activeFile['scanNum']]
                else:
                    print activeFile['filter']
                    print activeFile['targ_filt']
                print activeFile['filterLock']
            else:
                #print "UNLOCK"
                activeFile['filterLock']=None
                
        elif key == 86: #"V"
            #print "View All"
            for i in range(0, self.msdb.getFileNum()):
                self.msdb.files[self.msdb.Display_ID[i]]["Display"]=True
            self.msdb.set_axes()
            
        #if key == 69: #"E" HCD error toggle
            ##Toggle viewing errors
            #activeFile["errorFlag"] = not activeFile["errorFlag"]
            
        #if key == 89: #"Y"
            #self.mass_ranges = [(self.mass_ranges[0][0], self.mass_ranges[self.axes-1][1])]
            #self.axes = 1
            #self.axco = [((550, 550, 1050, 550),(550, 50, 550, 550))]
            
        #if key == 88: #"X"
            #if self.axes == 1:
                #mrange = float(self.mass_ranges[self.axes-1][1]-self.mass_ranges[0][0])/float(2)
                #self.mass_ranges = [(self.mass_ranges[0][0], self.mass_ranges[0][0] + mrange), (self.mass_ranges[0][0] + mrange, self.mass_ranges[self.axes-1][1])]
            #self.axes = 2
            #self.axco = [((550, 250, 1050, 250),(550, 50, 550, 250)), ((550, 550, 1050, 550),(550, 350, 550, 550))]
            
        #+----------------------NOTE, ADDITIONAL CODE RUNS FOR +/- scan see logic block below
        #-----------------------Runs set_scan and build_current_ID
        elif key == 61: #"+"
            if activeFile['vendor']=='Thermo':
                activeFile["scanNum"] += 1
                while (activeFile["scanNum"] not in activeFile['filter_dict']
                       and activeFile['scanNum'] <= activeFile['scan_range'][1]):
                    activeFile['scanNum'] += 1
            if activeFile['vendor']=='mgf':
                try:
                    activeFile["scanNum"] = min(x for x in activeFile['scan_dict']
                                                if x > activeFile['scanNum'])
                except ValueError:
                    activeFile["scanNum"] = max(activeFile['scan_dict'])          
            if activeFile['vendor']=='ABI':
                if activeFile["scanNum"] in activeFile["m"].associated_MS2.keys():
                    currentExp = int(activeFile["experiment"])
                    maxExp = activeFile["m"].associated_MS2[activeFile["scanNum"]]
                    if currentExp == maxExp:
                        activeFile['scanNum']=activeFile["scanNum"]+1
                        activeFile['experiment'] = "0"
                    else:
                        keep_looking = True
                        look_for_exp = currentExp
                        while keep_looking:
                            look_for_exp += 1
                            look_for = (activeFile['scanNum'], str(look_for_exp))
                            if look_for in activeFile['filter_dict']:
                                activeFile['experiment']=str(look_for_exp)
                                break
                            if currentExp == maxExp:
                                activeFile['scanNum']=activeFile["scanNum"]+1
                                activeFile['experiment'] = "0"
                                break
                            
                else:
                    activeFile['scanNum']=activeFile["scanNum"]+1
                    activeFile['experiment'] = "0"

        elif key == 45: #"-"
            '''
            NEEDS PATCH TO CHECK FOR VALID SCAN
            
            '''            
            if activeFile['vendor']=='Thermo':
                activeFile["scanNum"] -= 1 if activeFile["scanNum"] else 0
                while (activeFile["scanNum"] not in activeFile['filter_dict']
                       and activeFile['scanNum'] >= activeFile['scan_range'][0]):
                    activeFile['scanNum'] -= 1                
            elif activeFile['vendor']=='mgf':
                try:
                    activeFile["scanNum"] = max(x for x in activeFile['scan_dict']
                                                if x < activeFile['scanNum'])
                except ValueError:
                    activeFile["scanNum"] = 0
            
            
            elif activeFile['vendor']=='ABI':
                if activeFile['experiment']=="0":
                    if activeFile["scanNum"]-1 in activeFile["m"].associated_MS2.keys():
                        activeFile['experiment'] = str(activeFile["m"].associated_MS2[activeFile["scanNum"]-1])
                        activeFile['scanNum']-=1
                    else:
                        activeFile['scanNum']-=1
                else:
                    activeFile['experiment'] = str(int(activeFile['experiment'])-1)
                    
        elif key == 44: # Originally 314 = "Left arrow"; AUI notebook uses this to move through windows; change to <
            if activeFile['master_scan'] != 'ms2':
                if activeFile['filterLock']:
                    msfilter = activeFile['filterLock']
                    activeFile["scanNum"]=mz_core.find_filter(activeFile["filter_dict"], activeFile["scanNum"], "Reverse", msfilter)   
                else:
                    if activeFile['vendor']=='Thermo':
                        activeFile["scanNum"] = mz_core.find_MS1(activeFile["scan_dict"], activeFile["scanNum"], "Reverse")
                    if activeFile['vendor']=='ABI':
                        activeFile["scanNum"] = activeFile["scanNum"] - 1
                        activeFile['experiment'] = "0"
            else:
                dlg = wx.MessageDialog(self, 'This is an MS2 file! Use +/- to navigate.', 'Alert', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                
                    
        elif key == 46: # Originally 316 = "Right arrow"; AUI notebook uses this to move through windows; change to >
            if activeFile['master_scan'] != 'ms2':
                if activeFile['filterLock']:
                    msfilter = activeFile['filterLock']
                    activeFile["scanNum"]=mz_core.find_filter(activeFile["filter_dict"], activeFile["scanNum"], "Forward", msfilter)
                else:
                    if activeFile['vendor']=='Thermo':
                        activeFile["scanNum"] = mz_core.find_MS1(activeFile["scan_dict"], activeFile["scanNum"], "Forward")
                    if activeFile['vendor']=='ABI':
                        activeFile["scanNum"] = activeFile["scanNum"] + 1
                        activeFile['experiment'] = "0"
            else:
                dlg = wx.MessageDialog(self, 'This is an MS2 file! Use +/- to navigate.', 'Alert', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
        
        elif key == 83: #"S"  VIEW SPECTRUM ONLY
            activeFile["mode"] = "SPEC"
            self.msdb.set_axes()
        
        elif key == 82: #"R" VIEW CHROMATOGRAM AND SPECTRUM
            activeFile["mode"] = "RIC-SPEC"
            self.msdb.set_axes()
            
        elif key == 81: # "Q"
            print "Q"
            if not activeFile["Processing"]:
                activeFile["Processing"] = True # Was 'RRC'.
    
                #activeFile['viewCentroid']=True              
                #activeFile["scan"] = activeFile["m"].rscan(activeFile["scanNum"])
                #activeFile['scan'] = activeFile['m'].scan(activeFile['scanNum'], centroid = True)
                #self.msdb.set_scan(activeFile["scanNum"], self.msdb.active_file)
                
                #self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"]) 
            else:
                activeFile["Processing"] = False
                activeFile['processed_data'] = activeFile['unprocessed_data']
            
                self.msdb.set_scan(activeFile["scanNum"], self.msdb.active_file)
                
                #self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"])                 
                
        elif key == 80: #"P" PROPAGATE XICS
            #print "Propagating XICs..."
            for j, member in enumerate(self.msdb.files.keys()):
                #print j
                #print member
                if j != self.msdb.active_file:
                    #print "Building XICs..."
                    busy = PBI.PyBusyInfo("Propagating XICs...", parent=None, title="Processing...")
                    proc = ProcFrame(None)
                    proc.Show()
                    proc.Update()
                    proc.Refresh()                    
                    wx.Yield()                    
                    self.frm = xicFrame(self, self.msdb.files[self.msdb.Display_ID[j]], j)
                    for m in [0,1,2,3]:
                        for n in [0,1,2]:
                            self.frm.grid.SetCellValue(m, n, "")
                    for i, member in enumerate(activeFile["xic_mass_ranges"]):
                        #print i
                        #print activeFile["filters"][i]
                        self.frm.grid.SetCellValue(i, 0, str(activeFile["xic_mass_ranges"][i][0]))
                        self.frm.grid.SetCellValue(i, 1, str(activeFile["xic_mass_ranges"][i][1]))
                        self.frm.grid.SetCellValue(i, 2, str(activeFile["filters"][i]))
                    self.frm.OnClick(None)
                    self.frm.Destroy()
                    del busy
                    proc.Destroy()
                    
        elif key == 71:# "g"  Get isotope list
            #label_file = os.path.dirname(activeFile["xlsSource"]) + '\\IsotopeLabels.csv'
            label_file = mzGUI.file_chooser('Select isotope label csv file', wildcard='csv files (*.csv)|*.csv')
            if label_file:
                rdr = csv.reader(open(label_file), delimiter=',', quotechar='|')
                self.msdb.isotope_labels=[]
                for i, row in enumerate(rdr):
                    self.msdb.isotope_labels.append([float(row[0]), row[1]])
                    self.msdb.isotope_dict[float(row[0])]= row[1]  
                
        #elif key == 70:# "f"
        #    self.findFrame = findFrame(self.parent.parent)
        #    self.findFrame.Show()
            
        elif key == 85:# "U"
            activeFile["label_non_id"] = not activeFile["label_non_id"]
            
        elif key == 49: #"1"
            activeFile["axes"] = 1
            self.msdb.set_axes()
            
        elif key == 50: #"2"
            activeFile["axes"] = 2
            self.msdb.set_axes()
            
        elif key == 51: #"3"
            activeFile["axes"] = 3
            self.msdb.set_axes()
            
        elif key == 52: #"4" LOAD REPORTER ION CORRECTION FILE.
            label_file = mzGUI.file_chooser('Select correction factor csv file', wildcard='csv files (*.csv)|*.csv')
            if label_file:
                rdr = csv.reader(open(label_file), delimiter=',', quotechar='|')
                self.msdb.cf=[]
                for i, row in enumerate(rdr):
                    self.msdb.cf.append([float(row[0]), float(row[1])])
                    self.msdb.cf_dict[float(row[0])]=float(row[1])
            
        #elif key == 53: #5
            #print "5"
            #IDd_Ions = LabelCoverage.derive_IDd_Ions(activeFile)
            #print IDd_Ions
            #key = None
            #if activeFile['vendor']=='Thermo':
                #key = activeFile["scanNum"]
            #elif activeFile['vendor']=='ABI':
                #key = (activeFile['scanNum'], activeFile['experiment'])
            #if activeFile["SearchType"]=="Mascot":
                #seq = activeFile["ID_Dict"][key]["Peptide Sequence"]
                #fixedmod = activeFile["fixedmod"]
                #varmod = activeFile["ID_Dict"][key]["Variable Modifications"]            
            #lf = LabelCoverage.CoveragePanel(self, seq, fixedmod, varmod, IDd_Ions, True, True)
            #lf.Show()
            
        elif key == 73: #"i"
            if self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["axes"] == 1:
                self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["mass_ranges"]=[(110,120)]
                
        elif key == 56: #"8"
            if self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["axes"] == 1:
                self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["mass_ranges"]=[(109,125)]   
                
        #elif key == 77: #"M"
            #self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["viewMascot"] = not self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["viewMascot"]
            #self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"])
            #print "TOGGLE"
            #self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["viewMascot"] 
            
        elif key == 76: #"L"
            self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["locked"] = not self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["locked"]
        
        elif key == 84:
            if self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["axes"] == 1:
                self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["mass_ranges"]=[(121,136)]
        
        #elif key == 315: # "UP"
            #if self.msdb.getDisplayWindows() > 1:
                #if self.msdb.active_file > self.msdb.getNextActiveWindow(-1, "forward"):
                    #self.msdb.active_file = self.msdb.getNextActiveWindow(self.msdb.active_file, "reverse")
                    #self.SetTitle("Active File: " + os.path.basename(self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["FileAbs"]))
        
        #elif key == 317: # "DOWN"
            #if self.msdb.getDisplayWindows() > 1:
                #if self.msdb.active_file < self.msdb.getNextActiveWindow(self.msdb.getFileNum(), "reverse"):
                    #self.msdb.active_file = self.msdb.getNextActiveWindow(self.msdb.active_file, "forward")
                    #self.SetTitle("Active File: " + os.path.basename(self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["FileAbs"]))
        
        else:
            # Wasn't a key mapped to anything, don't bother updating.
            event.Skip()
            return
            
        if key in [61, 45, 44, 46]:
            activeFile["spectrum_style"] = "single scan"
            activeFile["Processing"] = False
            try:
                self.msdb.set_scan(activeFile["scanNum"], self.msdb.active_file)
            except KeyError:
                print "Scan %s not present in file.  (Return from OnKeyDown.)" % activeFile["scanNum"]
                return
            if activeFile['vendor']=='Thermo':
                self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], activeFile["scanNum"])
            if activeFile['vendor']=='ABI':
                self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], (activeFile["scanNum"], activeFile['experiment']), 'ABI')
                
        self.Window.UpdateDrawing()
        self.Refresh()
        event.Skip()
        # Note floating return on line 3574.
        
    def read_colors(self):
        colorfile = os.path.join(installdir, 'settings', 'colors.txt')
        file_r = open(colorfile, 'r')
        colors = file_r.readlines()
        color_list = [x.strip() for x in colors]
        print color_list        
        return color_list

    def get_xic_color(self, xic, dc):
        if xic == 0:
            dc.SetPen(wx.Pen(wx.BLACK,1))
            col = wx.BLACK
        elif xic == 1:
            dc.SetPen(wx.Pen(wx.RED,1))
            col = wx.RED
        elif xic == 2:
            dc.SetPen(wx.Pen(wx.BLUE,1)) 
            col = wx.BLUE
        elif xic == 3:
            dc.SetPen(wx.Pen(wx.GREEN,1)) 
            col = wx.GREEN    
        elif xic == 4:
            dc.SetPen(wx.Pen(wx.YELLOW,1)) 
            col = wx.YELLOW    
        elif xic == 5:
            dc.SetPen(wx.Pen(wx.CYAN,1)) 
            col = wx.CYAN
        elif xic ==6:
            dc.SetPen(wx.Pen(wx.Colour(255, 128, 128,255)))
            col = wx.Colour(255, 128, 128,255)
        elif xic ==7:
            dc.SetPen(wx.Pen(wx.Colour(128, 64, 64,255)))
            col = wx.Colour(128, 64, 64,255)    
        elif xic ==8:
            dc.SetPen(wx.Pen(wx.Colour(128, 0, 0,255)))
            col = wx.Colour(128, 0, 0,255) 
        elif xic ==9:
            dc.SetPen(wx.Pen(wx.Colour(64, 0, 0,255)))
            col = wx.Colour(64, 0, 0,255)   
        elif xic ==10:
            dc.SetPen(wx.Pen(wx.Colour(255, 128, 64,255)))
            col = wx.Colour(255, 128, 64, 255)   
        elif xic ==11:
            dc.SetPen(wx.Pen(wx.Colour(0, 128, 128,255)))
            col = wx.Colour(0, 128, 128, 255) 
        elif xic ==12:
            dc.SetPen(wx.Pen(wx.Colour(0, 64, 128,255)))
            col = wx.Colour(0, 64, 128, 255)  
        elif xic ==13:
            dc.SetPen(wx.Pen(wx.Colour(0, 64, 128,255)))
            col = wx.Colour(0, 64, 128, 255) 
        elif xic ==14:
            dc.SetPen(wx.Pen(wx.Colour(128, 0, 64,255)))
            col = wx.Colour(128, 0, 64, 255)            
        #(255, 128, 128), (128, 64, 64), (128, 0, 0), (64, 0, 0), (255, 128, 64), 
        else:
            if xic > 14 and xic <25:
                dc.SetPen(wx.Pen(wx.Colour(xic*10,255-(xic*10),255,0)))
                col = wx.Colour(xic*5,255,255,0)
            elif xic >24 and xic <100:
                dc.SetPen(wx.Pen(wx.Colour(255-(xic-25)*5,(xic-25)*5,255-(xic-25)*5,0)))
                col = wx.Colour(255,xic*5,255,0)                    
        return col

    def get_xic_color_old(self, xic, dc):
        if xic < 50:
            color = self.colors[xic]
            col = eval("wx."+color)
            res = eval("dc.SetPen(wx.Pen(wx."+color+',1))')
        else:
            col = eval("wx.BLACK")
            dc.SetPen(wx.Pen(wx.BLACK,1))
        return col    

    def DrawXic(self, dc, key, rawID, global_max, max_tables):
        '''
        
        Main code for drawing extracted ion chromatograms.
        
        
        '''
        num_xics = len(max_tables)
        font_size = 10
        if num_xics > 5:
            font_size = 8
        scaling = False
        currentFile = self.msdb.files[self.msdb.Display_ID[rawID]]
        startTime = currentFile["time_ranges"][0][0]
        stopTime = currentFile["time_ranges"][0][1]
        active_xic = currentFile['active_xic'][key]
        window_marks = None
        #if key in currentFile['xic_marks'].keys():
        window_marks = currentFile['xic_marks'][key]
        maxTable = max_tables[key]
        #maxTable = []
        #for xic in range(0, len(currentFile["xic_params"][key])):
        #    maxTable.append(self.msdb.GetMaxSignal(startTime, stopTime, key, self.msdb.Display_ID[rawID], xic))
        max_trace = maxTable.index(max(maxTable))
        xics = len(currentFile["xic_params"][key])
        xaxis = currentFile['xic_axco'][key][0]
        yaxis = currentFile['xic_axco'][key][1]        
        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
        #dc.DrawRectangle(xaxis[0]-10, (yaxis[1]+10)+(30*len(currentFile["xic_params"][key])),10,10)
        dc.DrawRectangle(xaxis[0]-10, (yaxis[1]+10),10,10)
        for xic in range(0, len(currentFile["xic_params"][key])):
            trace_marks = None
            #if window_marks:
            #if xic in currentFile['xic_marks'][key].keys():
            trace_marks = currentFile['xic_marks'][key][xic]            
            col = self.get_xic_color(xic, dc)
            #dc.SetBrush(wx.Brush(col, wx.SOLID))        
            if xics > 1 and xics <4:
                dc.SetTextForeground(col)
                dc.SetFont(wx.Font(6, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                ex = dc.GetTextExtent(str(currentFile['xic_mass_ranges'][key][xic][0]))
                dc.DrawText(str(currentFile['xic_mass_ranges'][key][xic][0])+'-', xaxis[0]-1-ex[0], (yaxis[1]+48)+ (30*xic))
                ex = dc.GetTextExtent(str(currentFile['xic_mass_ranges'][key][xic][1]))
                dc.DrawText(str(currentFile['xic_mass_ranges'][key][xic][1]), xaxis[0]-1-ex[0], (yaxis[1]+58)+ (30*xic))
                dc.SetTextForeground("BLACK")
                dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                #dc.DrawRectangle(xaxis[0]+250 + (20*xic), yaxis[1]-20,10,10)
                dc.SetBrush(wx.Brush(col, wx.TRANSPARENT))
                dc.DrawRectangle(xaxis[0]-25, (yaxis[1]+40)+ (30*xic),10,10) 
                dc.DrawRectangle(xaxis[0]-40, (yaxis[1]+40)+ (30*xic),10,10)
                dc.DrawText('>', xaxis[0]-40+2, (yaxis[1]+40)+ (30*xic)-3)
                #dc.DrawLine(xaxis[0]-35, (yaxis[1]+10) + (20*xic),xaxis[0]-35, yaxis[1]+20 + (20*xic))
                #dc.DrawLine(xaxis[0]-35, (yaxis[1]+19) + (20*xic),xaxis[0]-32, yaxis[1]+15 + (20*xic))
                #dc.DrawLine(xaxis[0]-35, (yaxis[1]+19) + (20*xic),xaxis[0]-38, yaxis[1]+15 + (20*xic))
                dc.DrawText('+' if currentFile['xic_view'][key][xic] else '-', xaxis[0]-25+2, (yaxis[1]+40)+ (30*xic)-3)
                dc.SetBrush(wx.Brush(col, wx.SOLID))
                dc.DrawRectangle(xaxis[0]-10, (yaxis[1]+40)+ (30*xic),10,10) 
            if currentFile['xic_view'][key][xic]:
                currentActive=False
                if active_xic == xic:
                    currentActive = True
                # if xic == 0, only one trace to draw.
                #a = currentFile['xic_scale'][key]
                scale = currentFile['xic_scale'][key][xic]
                #xaxis[0]-10, (yaxis[1]+10)+ (20*xic),10,10
                #xaxis = currentFile['xic_axco'][key][0]
                #yaxis = currentFile['xic_axco'][key][1]
                dc.SetPen(wx.Pen(wx.BLACK,1))
                dc.DrawLine(*xaxis)
                self.msdb.svg["lines"].append(xaxis)
                dc.DrawLine(*yaxis)
                self.msdb.svg["lines"].append(yaxis)
                dc.DrawLine(xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1])
                self.msdb.svg["lines"].append((xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1]))
                height = yaxis[3]-yaxis[1]
                width = xaxis[2]-xaxis[0]
                max_signal = maxTable[xic]
                #max_signal = self.msdb.GetMaxSignal(startTime, stopTime, key, self.msdb.Display_ID[rawID], xic)
                if scale == -1:
                    #max_signal = self.msdb.GetMaxSignal(startTime, stopTime, key, self.msdb.Display_ID[rawID], xic)
                    max_signal = maxTable[xic]
                elif str(scale)=='tmax':
                    max_signal = maxTable[max_trace]
                    scaling = True
                elif str(scale)=='wmax':
                    print max_tables
                    print global_max
                    max_signal = max_tables[global_max[0]][global_max[1]]
                    scaling = True                
                elif str(scale).lower().startswith("s"):
                    #Scale to a trace
                    max_signal = max_tables[int(str(scale)[1:])][currentFile['active_xic'][int(str(scale)[1:])]]      # #should make to active trace
                    scaling = True
                else:
                    print "SCALING"
                    max_signal = scale
                    scaling = True           
                #tr = int(currentFile["time_ranges"][0][1])-int(currentFile["time_ranges"][0][0])
                tr = (currentFile["time_ranges"][0][1])-(currentFile["time_ranges"][0][0])
                #print "tr:" + str(tr)
                try:
                    px = float(width)/float(tr)
                except:
                    px = 1
                try:
                    py = float(height)/float(max_signal)
                except:
                    py = 0
                self.xic_width = width
                x1 = yaxis[0]
                y1 = yaxis[3]
                dc.SetTextForeground("BLACK")
                dc.SetFont(wx.Font(font_size, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                if currentActive:
                    dc.DrawText("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7)
                    self.msdb.svg["text"].append(("%.1e"%max_signal, xaxis[0]-50, yaxis[1]-7,0.00001))
                points = []
                #print "building"
                if trace_marks:
                    font = dc.GetFont()
                    dc.SetFont(wx.Font(30, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                    dc.SetTextForeground("RED")
                    for mark in trace_marks.keys():
                        mark_time = trace_marks[mark].time
                        if mark_time > startTime and mark_time < stopTime:
                            x2 = yaxis[0] + px*(mark_time-startTime)
                            if not scaling:
                                y2 = yaxis[1] + (height - trace_marks[mark].intensity * py)
                            else:
                                c_inten = trace_marks[mark].intensity
                                y2 = (yaxis[1] + (height - c_inten*py)) if c_inten < max_signal else (yaxis[1] + (height - max_signal*py))  
                            #--------------XIC Lookup is used by OnMotion for coordinates and information
                            currentFile['xic_lookup'].append([x2,y2,currentFile['xic_marks'][key][xic][mark]])
                            dc.DrawText("*", x2-10, y2-20)
                    dc.SetFont(wx.Font(font_size, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
                    dc.SetTextForeground("BLACK")
                #t4 = time.time()
                #--------------------------------------------------------------------
                #This code builds the XIC - loop through all data points and make a list of points to draw
                for member in currentFile['xic'][key][xic]:
                    if member[0]>startTime and member[0]<stopTime:
                        x2 = yaxis[0] + px*(member[0]-startTime)
                        if not scaling:
                            y2 = yaxis[1] + (height - member[1]*py)
                        else:
                            y2 = (yaxis[1] + (height - member[1]*py)) if member[1] < max_signal else (yaxis[1] + (height - max_signal*py))  
                            #if member[1] > max_signal:
                        points.append((x2, y2))
                col = self.get_xic_color(xic, dc)
        
                #t1 = time.time()
                dc.DrawLines(points)
                #t2 = time.time()
                self.msdb.svg["pointLists"].append(points)
                #t3 = time.time()
                
                #print "XIC"
                #print "Draw"
                #print t2-t1
                #print t3-t2
                #print "XIC CALCS"
                #print t1-t4
                
                dc.SetTextForeground("BLACK")
                dc.SetPen(wx.Pen(wx.BLACK,1))
                xticks = []
                startTime = float(startTime)
                stopTime = float(stopTime) # Not doing these casts can have hilarious effects.
                if tr >= 0.5:
                    if tr > 10:
                        scale = int(round(round(tr, -1 * int(math.floor(math.log10(tr)))) / 10))
                        assert scale
                    else:
                        scale = tr/10
                    
                    if self.GetClientSize()[0] < 600:
                        scale = scale * 3
                    elif self.GetClientSize()[0] < 800:
                        scale = scale * 2                    
                    if scale >= 1:
                        firstlabel = self.myRound(startTime, scale)
                        lastlabel = self.myRound(stopTime, scale)
                    if scale >= 0.1:
                        firstlabel = float(self.myRound(startTime*10, scale*10))/float(10)
                        lastlabel = float(self.myRound(stopTime*10, scale*10))/float(10)
                    else:
                        return # Has MS technology reached the sub-second-sampling level yet?
                    if firstlabel < startTime:
                        firstlabel += scale
                    if lastlabel > stopTime:
                        lastlabel -= scale
                    if scale >= 1:
                        # Looking for why your ticks are wonky?  Its probably this!
                        # Replace with float-compatible range equivalent?
                        #for i in range (int(firstlabel), int(lastlabel + scale), int(scale)):
                        for i in floatrange(firstlabel, lastlabel + scale, scale):
                            if i%1 == 0:
                                i = int(i)
                            xticks.append(i)
                    if scale >= .1 and scale < 1:
                        #for i in range (int(firstlabel)*10, int(lastlabel)*10 + int(scale)*10, int(scale)*10):
                        for i in floatrange(firstlabel*10, lastlabel*10 + scale*10, scale*10):
                            xticks.append(float(i)/float(10))
                else:
                    xticks.append(round(startTime, 1))
                    xticks.append(round(stopTime, 1))
                for member in xticks:
                    memberstr = "%.2f" % member if isinstance(member, float) else str(member)
                    x1 = currentFile['xic_axco'][key][0][0] + px*((member-startTime))
                    if x1 > (xaxis[0]-1) and x1 < (xaxis[2] +1):
                        dc.DrawText(memberstr, x1-8,yaxis[3]+5)
                        self.msdb.svg["text"].append((memberstr, x1-8,yaxis[3]+5,0.00001))
                        dc.DrawLine(x1, yaxis[3], x1, yaxis[3]+2)
                        self.msdb.svg["lines"].append((x1, yaxis[3], x1, yaxis[3]+2))
                #This draws the text for the mz range
                if currentActive:
                    col = self.get_xic_color(xic, dc)
                    dc.SetTextForeground(col)
                    dc.DrawText("mz " + str(currentFile['xic_mass_ranges'][key][xic][0]) + '-'+ str(currentFile['xic_mass_ranges'][key][xic][1]) + ' (' + currentFile['filters'][key][xic].strip() + ')', currentFile['xic_axco'][key][1][0], currentFile['xic_axco'][key][1][1] - 20)
                    dc.DrawText(currentFile['xic_title'][key][xic], xaxis[2] - dc.GetTextExtent(currentFile['xic_title'][key][xic])[0], currentFile['xic_axco'][key][1][1] - 15)
                    #currentFile['xic_title'][key][xic]
                    self.msdb.svg["text"].append(("mz " + str(currentFile['xic_mass_ranges'][key][xic][0]) + '-'+ str(currentFile['xic_mass_ranges'][key][xic][1]), currentFile['xic_axco'][key][1][0], currentFile['xic_axco'][key][1][1] - 20,0.00001))
                if currentFile['spectrum_style']=='single scan':
                    if currentFile['vendor']=='Thermo':
                    
                        rt = currentFile['rt_dict'][currentFile['scanNum']]
                    
                    elif currentFile['vendor']=='mgf':
                        #rt = currentFile['rt_dict'][currentFile['scanNum']]                
                        rt = currentFile['scanNum']
                    elif currentFile['vendor']=='ABI':
                        rt = currentFile['rt_dict'][(currentFile['scanNum'], currentFile['experiment'])][0]
                    current_x = currentFile['xic_axco'][key][0][0] + ((float(rt)-startTime)*px)
                    #------------------This draws the red line on the XIC
                    dc.SetPen(wx.Pen(wx.RED,2))
                    bar_min = xaxis[0]
                    bar_max = xaxis[2]
                    if current_x > bar_min and current_x < bar_max:
                        dc.DrawLine(current_x, yaxis[1], current_x, yaxis[3])
                        self.msdb.svg["lines"].append((current_x, yaxis[1], current_x, yaxis[3]))
                    #-----------------------------------------------------
                    dc.SetPen(wx.Pen(wx.BLACK,1))
                    dc.SetTextForeground("BLACK")

    def DrawFeatures(self, dc, key, rawID):
        '''
        
        This code will highlight features that are detected.
        
        '''
        #pdc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
        currentFile = self.msdb.files[self.msdb.Display_ID[rawID]]
        
        if "scansWithFeatures" in currentFile and currentFile["scanNum"] in currentFile["scansWithFeatures"]:
            gdc = wx.GCDC(dc)
            currentFile['FeatureBoxes'] = []
            print "FOUND FEATURES"
            thresh = currentFile["settings"]["label_threshold"][currentFile['vendor']]
                    
            firstMass = currentFile["mass_ranges"][key][0]
            lastMass = currentFile["mass_ranges"][key][1]
            
            xaxis = currentFile['axco'][key][0]
            yaxis = currentFile['axco'][key][1]
            height = yaxis[1]-yaxis[3]
            width = xaxis[2]-xaxis[0]
            px = width
            self.width = width
            self.indent = yaxis[0]
           
            if not currentFile['intensity_scaling']:
                max_int = self.msdb.GetMaxInt(firstMass, lastMass, self.msdb.Display_ID[rawID])
            else:
                max_int = currentFile['intensity_scaling']
                
            currentFile["max_int"][key]=max_int
            
            features = currentFile["scanToF"][currentFile["scanNum"]] 
            mr = currentFile["mass_ranges"][key][1]-currentFile["mass_ranges"][key][0]
            for feature in features:
                
                scan_data = currentFile["scanFToPeaks"][currentFile["scanNum"], feature]
                max_mz = scan_data[len(scan_data)-1][0] + 0.1
                
                # scan_data[0][0] is the first mass of the feature
                
                if scan_data[0][0] > firstMass and max_mz < lastMass: #Only draw features within mass range
                    
                    x2 = yaxis[0] + px*((max_mz-firstMass)/float(mr))
                    x1 = yaxis[0] + px*((scan_data[0][0]-firstMass)/float(mr))
                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(scan_data[0][1]/float(max_int))
                    
                    
                    #x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                    #x2 = x1                
                    
                    if currentFile['intensity_scaling']:
                        if scan_data[0][1] > float(max_int):
                            y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])                
                    y_frac = (float(yaxis[3])-float(y1))/(float(yaxis[3])-float(yaxis[1]))
                    if y_frac > 0.2: #x1>firstMass and x1<lastMass and
                        #-------------------------------------DRAW BOX AROUND FEATURE
                        brushclr = wx.Colour(0,255,255,18)
                        gdc.SetBrush(wx.Brush(brushclr))                    
                        gdc.DrawRectangle(x1, y1,x2-x1,yaxis[3]-y1)
                        try:
                            #seq = currentFile["featureToPSMs"][feature][0]['Peptide Sequence']
                            psms = currentFile["featureToPSMs"][feature]
                            psms.sort(key=lambda t: t["Peptide Score"], reverse=True) 
                            seq = psms[0]['Peptide Sequence']
                        except:
                            seq = 'No ID'
                        #dc.SetTextForeground(wx.Colour(255,0,255,128))
                        dc.DrawText(seq, x1, y1)
                        #------------------------------------DRAW FEATURE BOX
                        #------------------------------------HIGHEST INTENSITY, HIGHEST MZ
                        brushclr = wx.Colour(0,0,0,0)
                        dc.SetBrush(wx.Brush(brushclr))
                        dc.SetPen(wx.Pen(wx.BLACK,3))
                        pen = wx.Pen(wx.BLACK,1)                         
                        dc.DrawRectangle(x2,y1+20,10,10)
                        currentFile['FeatureBoxes'].append((x2, y1+20, x2+10, y1+30, feature))
                    #---------------- DRAWS THE FEATURE PEAKS
                    for member in scan_data:
                        if member[0]>firstMass and member[0]<lastMass:
                            x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                            x2 = x1
                            y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])*(member[1]/float(max_int))
                            if currentFile['intensity_scaling']:
                                if member[1] > float(max_int):
                                    y1 = yaxis[1] + yaxis[3]-yaxis[1] - (yaxis[3]-yaxis[1])
                                
                            y2 = yaxis[3]    
                            dc.SetPen(wx.Pen(wx.RED,3))
                            pen = wx.Pen(wx.RED,3)                            
                            dc.DrawLine(x1, y1, x2, y2)
        
    def DrawTextLabels(self, scan_data, dc, thresh, cutoff, currentFile, key, scan_type, rd, rawID, filter):
        xaxis = currentFile['axco'][key][0]
        yaxis = currentFile['axco'][key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        firstMass = currentFile["mass_ranges"][key][0]
        lastMass = currentFile["mass_ranges"][key][1]    
        
        #if profile: # and scan_type == 'MS1'
        #    if currentFile['vendor']=='Thermo':
        #        if filter.find("ITMS + p") == -1:
        #            scan_data = currentFile["m"].rscan(currentFile["scanNum"])
        #        else:
        #            scan_data = currentFile["m"].scan(currentFile["scanNum"], True)
        
        #if currentFile['vendor']=='ABI':
        #        scan_data = currentFile["m"].cscan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'], algorithm=currentFile['settings']['abi_centroid'], eliminate_noise = currentFile['settings']['eliminate_noise'], step_length = currentFile['settings']['step_length'], peak_min = currentFile['settings']['peak_min'], cent_thresh = currentFile['settings']['threshold_cent_abi'])
        #    if currentFile['vendor']=='ABI-MALDI':
        #        # The multiplierz centroid function should be used here instead.
        #        scan_data = t2dv2.centroid(currentFile['m'].scan())
        #else:
        #    scan_data = currentFile["scan"]          
        
        if currentFile['Processing']==True and self.parent.parent.custom_spectrum_process:
            # scan_data is already coming from being processed in DrawSpectrum!  This is redundant!
            #scan_data = self.parent.parent.custom_spectrum_process(scan_data)
            #currentFile["processed_data"] = scan_data
            
            #currentFile["scan"] = scan_data
            #----------FOR PROCESSED SPECTRUM, MUST OVERRIDE RAW DATA
            #Redefine first and last mass - this is for viewing the entire spectrum
            minMass = min([x[0] for x in scan_data])
            maxMass = max([x[0] for x in scan_data])
            currentFile['processed_first']=minMass
            currentFile['processed_last']=maxMass
        #else:
            #currentFile["processed_data"] = scan_data
        assert currentFile['processed_data'] == scan_data
        #if scan_data:
        #    max_int = max(x[1] for x in scan_data)        
        #else:
        #    max_int = 1        
        if not currentFile['Processing']:
            mr = currentFile["mass_ranges"][key][1]-currentFile["mass_ranges"][key][0] #MASS RANGE
        else:
            mr = lastMass - firstMass   
            
        max_int = self.msdb.GetMaxIntScanData(firstMass, lastMass, self.msdb.Display_ID[rawID], scan_data)
        
        px = width
        self.width = width
        self.indent = yaxis[0]        
        scan_data.sort(key=lambda x: x[1], reverse=True)
        #scan_data = filter(function_or_None, sequence)
        sub_scan = scan_data[:200]
        yvar1 = yaxis[1] + yaxis[3]-yaxis[1]
        yvar2 = (yaxis[3]-yaxis[1]) 
        labels = []
        for member in sub_scan:
            if member[0]>firstMass and member[0]<lastMass:
                x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                y1 = yvar1 - yvar2*(member[1]/float(max_int))
                if currentFile['intensity_scaling']:
                    if member[1] > float(max_int):
                        y1 = yvar1 - yvar2 #IF INTENSITY SCALING, and would go off-scale, scale to max display.
                y2 = yaxis[3]            
                if member[1] > thresh: #or member[0] in currentFile["label_dict"].keys():  #ONLY LABEL IF OVER THRESHOLD
                    angle = 90
                    pt = 10
                    right_margin = 9
                    if member[1] > cutoff:
                        angle = 15
                        pt = 9
                        right_margin = 50
                    #------------Smaller size if more than 1 axis or file
                    if currentFile["axes"] > 1 and self.msdb.getFileNum() > 1:
                        pt = 7
                    dc.SetFont(currentFile["settings"]['font1'])
                    font = wx.Font(pt, wx.ROMAN, wx.NORMAL, wx.BOLD, False)
                    #----------------------------------------------------------------------------
                    #-------------------labels have label locations so labels don't crowd together
                    #-------------------Was a peak near this m/z already labeled?
                    found = self.CheckLabels(x1, labels)
                    if not found:
                        if member[0] not in currentFile["label_dict"].keys():
                            if currentFile["label_non_id"]:
                                dc.SetTextForeground(currentFile['settings']["mainfont"]["color"])
                                #MS1 peak labeling
                                if scan_type == "MS1":
                                    if len(member) > 2:
                                        if member[3] >= currentFile["settings"]['min_cg'] and member[3] <= currentFile["settings"]['max_cg']:
                                            if not currentFile["label_res"]:  #-------LABEL RESOLUTION?
                                            #if member[3] > 0:
                                                dc.DrawRotatedText(str(round(member[0],rd)) + ' +' + str(int(member[3])),x1-7,y1-5,angle)
                                                self.msdb.svg["text"].append((str(round(member[0],rd)) + ' +' + str(int(member[3])),x1-7,y1-5,angle, "BLACK", font))
                                            else:
                                            #if member[3] >= currentFile["settings"]['min_cg'] and member[3] <= currentFile["settings"]['max_cg']:
                                                dc.DrawRotatedText(str(round(member[0],rd)) + ' +' + str(int(member[3])) + " %.2e"%member[4],x1-7,y1-5,angle)
                                                self.msdb.svg["text"].append((str(round(member[0],rd)) + ' +' + str(int(member[3])) + " %.2e"%member[4],x1-7,y1-5,angle, "BLACK", font))                                                
                                    else:
                                        dc.DrawRotatedText(str(round(member[0],rd)),x1-7,y1-5,angle)
                                        self.msdb.svg["text"].append((str(round(member[0],rd)),x1-7,y1-5,angle, "BLACK", font))
                                #-----------------END MS1 PEAK LABELING
                                #LABEL NON MS1
                                else:
                                    dc.DrawRotatedText(str(round(member[0],rd)),x1-7,y1-5,angle)
                                    self.msdb.svg["text"].append((str(round(member[0],rd)),x1-7,y1-5,angle, "BLACK", font))
                                    
                                labels.append([x1-9,x1+9]) #--------CO-ORDINATES OF LABEL TO BLOCK OFF (SO DO NOT OVERCROWD)
                                
                        
                        else:
                            #Peak is labeled
                            error = ''
                            if filter.find("FTMS")>-1:
                                th = currentFile["found2theor"][member[0]]
                                exp = member[0]
                                if currentFile['errorFlag']:
                                    try:
                                        error = ' ' + str(round((float(abs(exp-th)/float(th)))*1000000,1)) + ' ppm'
                                    except:
                                        error = '0 ppm'
                            if currentFile["label_dict"][member[0]].startswith("y") or currentFile["label_dict"][member[0]].startswith("z"):
                                dc.SetTextForeground("RED")
                                color = "RED"
                            elif currentFile["label_dict"][member[0]].startswith("b") or currentFile["label_dict"][member[0]].startswith("c"):
                                dc.SetTextForeground("BLUE")
                                color = "BLUE"
                            else:
                                color = "BLACK"
                            if currentFile["viewMascot"]:
                                dc.DrawRotatedText(str(round(member[0],rd)) + ' ' + currentFile["label_dict"][member[0]] + error,x1-7,y1-5,angle)
                                self.msdb.svg["text"].append((str(round(member[0],rd)) + ' ' + currentFile["label_dict"][member[0]],x1-7,y1-5,angle, color, font))
                            else:
                                dc.DrawRotatedText(str(round(member[0],rd)) + '  (' + currentFile["label_dict"][member[0]] + ')' + error,x1-7,y1-5,angle)
                                self.msdb.svg["text"].append((str(round(member[0],rd)) + '  (' + currentFile["label_dict"][member[0]] + ')'+ error,x1-7,y1-5,angle, color, font))
                            labels.append([x1-9,x1+right_margin])

    def DrawSpectrum(self, dc, key, rawID, profile=False, drawLines = True):
        '''
        
        MAIN FUNCTION FOR SPECTRUM RENDERING (Centroided spectrum).  This is used to draw text labels also.
        
        '''
        
        currentFile = self.msdb.files[self.msdb.Display_ID[rawID]]
        
        #-------------------------------
        #  Get spectral filter - helps decide whether high or low res/ prof/cent data
        #-------------------------------
        
        if currentFile['vendor'] in ['Thermo', 'ABI-MALDI', 'mgf'] and currentFile['spectrum_style']=='single scan':
            filter = currentFile["filter_dict"][currentFile["scanNum"]]
        else:
            filter = currentFile["filter_dict"][int(currentFile["scanNum"].split('-')[0])]
        #elif currentFile['vendor']=='ABI':
            #filter = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]        
        
        #-------------------------------
        #     FIRST GET SCAN DATA
        #--------------------------------------------
        
        prof_data = None
        if currentFile['spectrum_style']=='single scan':
            if profile: # and scan_type == 'MS1'
                if currentFile['vendor']=='Thermo':
                    #if filter.find("ITMS + p") == -1:
                    if "FTMS" in filter:
                        scan_data = currentFile["m"].rscan(currentFile["scanNum"]) # Used to be rscan.
                    else:
                        try:
                            scan_data = currentFile["m"].scan(currentFile["scanNum"], True)
                        except TypeError:
                            prof_data = currentFile["m"].scan(currentFile["scanNum"])
                            scan_data = mz_centroid(prof_data)
                        #max_int = self.msdb.GetMaxIntScanData(firstMass, lastMass, self.msdb.Display_ID[rawID], scan_data)
                if currentFile['vendor']=='ABI':
                    scan_data = currentFile["m"].cscan(currentFile['m'].scan_time_from_scan_name(currentFile["scanNum"]), currentFile['experiment'], algorithm=currentFile['settings']['abi_centroid'], eliminate_noise = currentFile['settings']['eliminate_noise'], step_length = currentFile['settings']['step_length'], peak_min = currentFile['settings']['peak_min'], cent_thresh = currentFile['settings']['threshold_cent_abi'])
                if currentFile['vendor']=='ABI-MALDI':
                    try:
                        scan_data = mz_centroid(currentFile['m'].scan(), threshold_scale = 2)
                    except:
                        scan_data = mz_centroid(currentFile['m'].scan())
            else:
                scan_data = currentFile["scan"]  
        else:
            scan_data = currentFile["scan"]
            
        currentFile['unprocessed_data'] = scan_data
            
        ## Correct ER filters.  (Hacky!)
        #if 'ER' in filter and (prof_data or scan_data):
            #peaks = zip(*(prof_data if prof_data else scan_data))[0]
            #rangestr = '[%.2f-%.2f]' % (min(peaks), max(peaks))
            #filter = filter.split('[')[0]
            #filter += rangestr
            #currentFile["filter_dict"][currentFile["scanNum"]] = filter
            #print "Corrected- " + filter
            
        #CUST_PROC
        
        if currentFile['Processing']==True and self.parent.parent.custom_spectrum_process:
            #No lscan silliness!  We tell people its a list of pairs.
            scan_data = [x[:2] for x in scan_data]
            
            try:
                scan_data = self.parent.parent.custom_spectrum_process(scan_data)
                #if scan_data:
                    #mzs = zip(*scan_data)[0]
                    #currentFile['mass_ranges'][0] = min(mzs)-1, max(mzs)+1
            except:
                wx.MessageBox("Error in spectrum processing script!", "mzStudio")
                scan_data = [(0, 0)]
            
            #currentFile["scan"] = scan_data
            if scan_data == []:
                print "No scan data."
                scan_data = [(0, 0)]
            #----------FOR PROCESSED SPECTRUM, MUST OVERRIDE RAW DATA
            #Redefine first and last mass - this is for viewing the entire spectrum
            minMass = min([x[0] for x in scan_data])
            maxMass = max([x[0] for x in scan_data])
            currentFile['processed_first']=minMass
            currentFile['processed_last']=maxMass
        
        currentFile["processed_data"] = scan_data

        if scan_data:
            max_int = max(x[1] for x in scan_data)        
        else:
            max_int = 1
        
        
        #------FOR DRAGGING SPECTRUM
        self.drag_coords=(currentFile['axco'][key][0][2]+35, currentFile['axco'][key][1][1])
        
        #THRESHOLD FOR LABELING
        thresh = currentFile["settings"]["label_threshold"][currentFile['vendor']]
        
        #GET FIRST AND LAST MASS
        
        if (not currentFile['is_zooming']) and (currentFile['Processing'] or 'ER' in filter) and (prof_data or scan_data):
            peaks = zip(*(prof_data if prof_data else scan_data))[0]
            firstMass = min(peaks) - 1
            lastMass = max(peaks) + 1
            currentFile["mass_ranges"][key] = firstMass, lastMass
        else:
            firstMass = currentFile["mass_ranges"][key][0]
            lastMass = currentFile["mass_ranges"][key][1]
        
        #DRAW AXES
        xaxis = currentFile['axco'][key][0]
        yaxis = currentFile['axco'][key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        px = width
        self.width = width
        self.indent = yaxis[0]
        dc.DrawLine(*xaxis)
        self.msdb.svg["lines"].append(xaxis)
        dc.DrawLine(*yaxis)
        self.msdb.svg["lines"].append(yaxis)
        dc.DrawLine(xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1])
        self.msdb.svg["lines"].append((xaxis[0]-5, yaxis[1], xaxis[0], yaxis[1]))
        
        #IF SCALING, GET ABSOLUTE VALUE.  IF NOT, SCALE TO MAXIMUM INTENSITY
        if not currentFile['intensity_scaling']:
            max_int = self.msdb.GetMaxInt(firstMass, lastMass, self.msdb.Display_ID[rawID])
        else:
            max_int = currentFile['intensity_scaling']
            
        currentFile["max_int"][key]=max_int
        
        #--------------WANT TO DRAW TRIANGLE SHOWING LABEL THRESHOLD
        #--------------IF THRESH = 200, MAX_INT = 400, then it will be 50% of yax3-yax1
        if max_int > 0:
            _thr_y1 = xaxis[1] - ((float(thresh)/float(max_int)) * (yaxis[3]-yaxis[1]))
            _thr_x1 = xaxis[0]-3
            _thr_y2 = _thr_y1 - 3
            _thr_x2 = _thr_x1 - 3
            dc.DrawLine(_thr_x1, _thr_y1, _thr_x2, _thr_y2)
            dc.DrawLine(_thr_x1, _thr_y1, _thr_x2, _thr_y2+6)
            dc.DrawLine(_thr_x2, _thr_y2, _thr_x2, _thr_y2+6)
            #dc.DrawRectangle(xaxis[0], (yaxis[1]+10),10,10)
            self.thresh_box = (_thr_x1 - 7, _thr_y2, _thr_x1, _thr_y2+14 )
        else:
            self.thresh_box = (0 , 0, 0, 0)
        #---------------------------------------------------------------------------
        
        if not currentFile['Processing']:
            mr = currentFile["mass_ranges"][key][1]-currentFile["mass_ranges"][key][0] #MASS RANGE
        else:
            mr = lastMass - firstMass
        
        #ONLY DRAW IF THERE IS A PEAK WITH ABOVE ZERO INTENSITY
        if max_int > 0:
            cutoff = 0.75 * float(max_int) #CUTOFF FOR LABEL TILT
            
            #DRAW NORMALIZED INTENSITY VALUE
            dc.SetTextForeground("BLACK")
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
            dc.DrawText("%.1e"%max_int, xaxis[0]-50, yaxis[1]-7)
            self.msdb.svg["text"].append(("%.1e"%max_int, xaxis[0]-50, yaxis[1]-7,0.00001))
            
            labels = []
            
            
            
            #-------------LOGIC TO DETERMINE SCAN TYPE FROM FILTER
            scan_type = 'MS2' # ASSUME MS2
            rd = 1 #RD = DECIMAL PLACES TO ROUND TO
            if filter.find("Precursor") > -1:
                scan_type = 'Precursor'
            if filter.find("EPI") > -1 or filter.find("TOF PI") > -1 or filter.find("MGF ms2"):
                scan_type = 'MS2'
            if filter.find("FTMS")>-1 or filter.find("TOF")>-1:
                rd = 4 #HIGH MASS ACCURACY SHOW MORE DECIMAL PLACES
            if filter.find("FTMS") > -1 and filter.find("Full ms ") > -1:
                scan_type = 'MS1'
            if filter.find("TOF MS") > -1 and filter.find("Full ms ") > -1:
                scan_type = 'MS1'
            if filter.find("ITMS + p ESI Full ms ") > -1:
                scan_type = 'MS1'
            if filter.find("MS3") > -1:
                scan_type = 'MS3'                    
            #------------------------------------------------------------
            #print scan_type
            ### this would add lots of redundancy if split on 3-axes - pulls centroid or scan multiple times!!!
            
                    
                    
            #--------------FINISHED GETTING SCAN DATA AND PROCESSING
            
            #-------------------------------------------------------
            #--------------Correction factors entered into label list (label_mz)
            apply_CF = False
            highest_label = 0
            label_mz = [] #label list
            if self.msdb.cf and scan_type=="MS2" and filter.lower().find("hcd") > -1:
                #print "--*"
                apply_CF = True
                highest_label = max(entry[0] for entry in self.msdb.cf)
                label_mz = [entry[0] for entry in self.msdb.cf]
                #print highest_label
                #print label_mz
                
                
            
            #START DRAWING
            #----------------------------------------------------------------------------
            # Main drawing of peaks
            #----------------------------------------------------------------------------
            scan_data.sort(key = lambda t:t[1], reverse = True)
            lines = []
            yvar1 = yaxis[1] + yaxis[3]-yaxis[1]
            yvar2 = (yaxis[3]-yaxis[1])
            print "Main Draw"
            t1=time.time()
            for member in scan_data:
                if member[0]>firstMass and member[0]<lastMass: #ONLY PEAKS IN DISPLAYED MASS RANGE
                    x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                    #x2 = x1
                    y1 = yvar1 - yvar2*(member[1]/float(max_int))
                    if currentFile['intensity_scaling']:
                        if member[1] > float(max_int):
                            y1 = yvar1 - yvar2 #IF INTENSITY SCALING, and would go off-scale, scale to max display.
                        
                    y2 = yaxis[3]
                    #-------------- This code block overlays iTRAQ correction factors
                    if apply_CF:
                        if member[0] < (highest_label+1):
                            found = False
                            found_mz = 0
                            found_int = 0
                            found_label = None
                        
                            #LOOK FOR PEAKS
                            for entry in label_mz:
                                if member[0] - 0.01 < entry and member[0] + 0.01 > entry:
                                    found = True
                                    found_mz = member[0]
                                    found_int = member[1]
                                    found_label = entry
                                    break
                            #IF FOUND, DRAW
                            if found:
                                corrected_int = found_int * self.msdb.cf_dict[found_label]
                                correct_mz = found_mz - 0.1
                                dc.SetPen(wx.Pen(wx.RED,3))
                                pen = wx.Pen(wx.RED,3)
                                a1 = yaxis[0] + px*((correct_mz-firstMass)/float(mr))
                                a2 = a1
                                b1 = yvar1 - yvar2*(corrected_int/float(max_int))
                                b2 = yaxis[3]                            
                                dc.DrawLine(a1, b1, a2, b2)   
                                self.msdb.svg["lines"].append((a1, b1, a2, b2 , pen))
                                if self.msdb.isotope_dict:
                                    dc.DrawRotatedText(self.msdb.isotope_dict[entry],a1-7,b1-5,0.0001)
                                    self.msdb.svg["text"].append((self.msdb.isotope_dict[entry],a1-7,b1-5,0.0001, "BLACK", wx.Font(12, wx.ROMAN, wx.NORMAL, wx.BOLD, False)))
                    
                    #---------------------SILAC LABELING ANNOTATION        
                    if currentFile['SILAC']['mode']: 
                        if scan_type=='MS1':
                            for peak in currentFile['SILAC']['peaks']:
                                if abs(member[0] - peak) < 0.05:
                                    dc.SetPen(wx.Pen(wx.RED,3))
                                    pen = wx.Pen(wx.RED,3)                                
                                    dc.DrawLine(x1, y1, x1, y2)
                    
                    #--------------------------------------------
                    #-----------MAIN DRAWING OF UNLABELED PEAKS
                    #-----------LABELED ONES ARE DONE SEPARATELY, IN COLOR
                    
                    if member[0] not in currentFile["label_dict"].keys():
                        #Unlabeled peaks done in normal
                        dc.SetPen(wx.Pen(wx.Colour(*currentFile['settings']['line color']),currentFile['settings']['line width']))
                        pen = wx.Pen(wx.Colour(*currentFile['settings']['line color']),currentFile['settings']['line width'])
                        if currentFile['Processing'] or currentFile["viewCentroid"] or (profile and currentFile['settings']['drawCentroid']) or not profile:
                            '''
                            If PROFILE, AND VIEW CENTROID False skip this line
                            
                            '''                            
                            dc.DrawLine(x1, y1, x1, y2) #------------Skip this line to not draw centroid
                            self.msdb.svg["lines"].append((x1, y1, x1, y2 , pen))
                    else:
                        #LABELED PEAKS ARE DRAWN IN COLOR
                        if currentFile["label_dict"][member[0]].find("y") > -1 or currentFile["label_dict"][member[0]].find("z") >-1:
                            dc.SetPen(wx.Pen(wx.RED,2))
                            pen = wx.Pen(wx.RED,2)
                        elif currentFile["label_dict"][member[0]].find("b") > -1 or currentFile["label_dict"][member[0]].find("c")>-1:
                            dc.SetPen(wx.Pen(wx.BLUE,2))
                            pen = wx.Pen(wx.BLUE,2)
                        else:
                            pen = wx.Pen(wx.BLACK,2)
                        dc.DrawLine(x1, y1, x1, y2)
                        self.msdb.svg["lines"].append((x1, y1, x1, y2, pen))
                        dc.SetPen(wx.Pen(wx.BLACK,1))
                    
                    #------------FOR DRAWING TEXT LABELS
                    #if False:
            if currentFile['settings']['labelPeaks']:        
                self.DrawTextLabels(scan_data, dc, thresh, cutoff, currentFile, key, scan_type, rd, rawID, filter)
                    
            t2 = time.time()
            print t2-t1
        dc.SetTextForeground("BLACK")
        dc.SetPen(wx.Pen(wx.BLACK,1))                
        xticks = []
        if mr >= 5:
            if mr >= 10000:
                scale = 5000
            if mr >= 5000 and mr < 10000:
                scale = 1000
            if mr >= 2000 and mr < 5000:
                scale = 500
            if mr >= 1000 and mr < 2000:
                scale = 200
            if mr >= 500 and mr < 1000:
                scale = 100
            if mr >= 200 and mr < 500:
                scale = 50
            if mr >= 80 and mr < 200:
                scale = 20
            if mr >= 20 and mr < 80:
                scale = 5
            if mr >= 5 and mr < 20:
                scale = 1
            if self.GetClientSize()[0] < 600:
                scale = scale * 3
            elif self.GetClientSize()[0] < 800:
                scale = scale * 2
            #if self.GetClientSize()[0] < 600:
                #scale = scale * 3
            firstlabel = self.myRound(firstMass, scale)
            #if firstlabel < currentFile["fm"]:
            if firstlabel < firstMass:
                firstlabel += scale
            lastlabel = self.myRound(lastMass, scale)
            #if lastlabel > currentFile["lm"]:
            if lastlabel > lastMass:
                lastlabel -= scale
            for i in range (firstlabel, lastlabel + scale, scale):
                xticks.append(i)
        else:
            xticks.append(round(firstMass, 1))
            xticks.append(round(lastMass, 1))
        for member in xticks:
            x1 = currentFile["axco"][key][0][0] + px*((member-firstMass)/float(mr))
            dc.DrawRotatedText(str(member), x1-8,yaxis[3]+5,0.00001)
            self.msdb.svg["text"].append((str(member), x1-8,yaxis[3]+5,0.00001))
            dc.DrawLine(x1, yaxis[3], x1, yaxis[3]+2)
            self.msdb.svg["lines"].append((x1, yaxis[3], x1, yaxis[3]+2))
        if key == 0:
            x = currentFile["axco"][0][0][2]
            subxx = currentFile["axco"][0][0][0]
            y = currentFile["axco"][0][1][1]
            #This displays filter lock
            if currentFile['filterLock']:
                dc.DrawText("Filter Locked: " + currentFile['filterLock'], subxx, y - 45)
            #This displays filename on trace
            dc.DrawText(currentFile["Filename"].split('.')[0], subxx, y - 30)
            self.msdb.svg["text"].append((currentFile["Filename"][:-4], subxx, y - 30,0.00001))
            if currentFile['vendor']=='Thermo':
                if currentFile["spectrum_style"] == "single scan":
                    dc.DrawText("Scan: " + str(currentFile["scanNum"]), x+5, y + 110)
                    self.msdb.svg["text"].append(("Scan: " + str(currentFile["scanNum"]), x+5, y + 110,0.00001))
                else:
                    print "SOME SORT OF AVERAGE SCAN DESCRIPTION BIT HERE."
                    #dc.DrawText("AV: " + str(self.average_start_scan) + '-' + str(self.average_stop_scan), x+5, y + 110)
                    rtstart = currentFile['m'].timeForScan(int(currentFile['scanNum'].split('-')[0]))
                    rtstop = currentFile['m'].timeForScan(int(currentFile['scanNum'].split('-')[1].split(' ')[0]))
                    dc.DrawText("Average Scan\n" + currentFile['scanNum'] + '\n' + str(round(rtstart,2)) + '-' + str(round(rtstart,2)), x+5, y +110)
            if currentFile['vendor']=='mgf':
                dc.DrawText("Query: " + str(currentFile["scanNum"]), x+5, y + 110)
                self.msdb.svg["text"].append(("Query: " + str(currentFile["scanNum"]), x+5, y + 110,0.00001))            
            if currentFile['vendor']=='ABI':
                dc.DrawText("Scan: (" + str(currentFile["scanNum"]) + ', ' + currentFile['experiment'] + ')', x+5, y + 110)
                self.msdb.svg["text"].append(("Scan: (" + str(currentFile["scanNum"]) + ', ' + currentFile['experiment'] + ')', x+5, y + 110,0.00001))
            self.msdb.svg["text"].append(("Scan: " + str(currentFile["scanNum"]), x+5, y + 110,0.00001))
            if currentFile['vendor']=='Thermo':
                if currentFile['spectrum_style']=='single scan':
                    rt = currentFile["rt_dict"][currentFile["scanNum"]]
                else:
                    rt = 'AV'
            elif currentFile['vendor']=='ABI':
                rt = currentFile["rt_dict"][(currentFile["scanNum"], currentFile['experiment'])]
            elif currentFile['vendor']=='ABI-MALDI':
                rt = 0
            if currentFile['spectrum_style']=='single scan':
                if currentFile['vendor']=='Thermo':
                    dc.DrawText("RT: " + str(round(rt,2)), x+5, y + 130)
                if currentFile['vendor']=='ABI':
                    dc.DrawText("RT: " + str(round(rt[0],2)), x+5, y + 130)
            else:
                print "SOME SORT OF AVERAGE SCAN DESCRIPTION BIT HERE."
                #dc.DrawText("RT: " + str(round(self.average_start,2))+'-'+str(round(self.average_stop,2)), x+5, y + 130)
            if currentFile['vendor']=='Thermo' and currentFile['spectrum_style']=='single scan':
                self.msdb.svg["text"].append(("RT: " + str(round(rt,2)), x+5, y + 130,0.00001))
            if currentFile['vendor']=='ABI':
                self.msdb.svg["text"].append(("RT: " + str(round(rt[0],2)), x+5, y + 130,0.00001))
            if currentFile['vendor']=='Thermo':
                if currentFile['spectrum_style']=='single scan':
                    fd=self.msdb.Create_Filter_Info(currentFile["filter_dict"][currentFile["scanNum"]], 'Thermo')
                else:
                    if "ms1" in filter:
                        currentFile['fd'] = {'mode':"ms1", 'analyzer':'average', 'data':'average' , 'mr':'[t1-t2]'}
                    elif "ms2" in filter:
                        currentFile['fd'] = {'mode':"ms1", 'analyzer':'average', 'precursor':'average', 'data':'average', 'reaction':'average', 'mr':'[t1-t2]', 'energy':'average'}
            if currentFile['vendor']=='mgf':
                fd=self.msdb.Create_Filter_Info(currentFile["filter_dict"][currentFile["scanNum"]], 'mgf') 
                dc.DrawText("Scan: " + str(fd['file scan']), x+5, y + 90)
            if currentFile['vendor']=='ABI':
                fd=self.msdb.Create_Filter_Info(currentFile["filter_dict"][(currentFile["scanNum"],currentFile['experiment'])], 'ABI')
            if currentFile['vendor']=='ABI-MALDI':
                #fd={"mode":"ms1", "analyzer":"tof", "data":"centroid", "mr":str(currentFile['m'].scan_range())}
                fd = self.msdb.Create_Filter_Info(currentFile["filter_dict"][currentFile["scanNum"]], 'ABI-MALDI')
            ystart = y + 150
            if self.msdb.getFileNum() > 1:
                dc.SetFont(wx.Font(7, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
            if currentFile["spectrum_style"] == "single scan":
                if fd["mode"].lower() in ["ms1", "sim (ms1)", "precursor", 'ms']:
                    keys = ["mode", "analyzer", "data", "mr"]
                    for key in keys:
                        dc.DrawText(fd[key], x+5, ystart)
                        self.msdb.svg["text"].append((fd[key], x+5, ystart,0.00001))
                        ystart+=15
                elif fd["mode"].lower()=="ms2":
                    keys = ["mode", "analyzer", "data", "precursor", "reaction", "energy", "mr"]
                    for key in keys:
                        dc.DrawText(fd[key], x+5, ystart)
                        self.msdb.svg["text"].append((fd[key], x+5, ystart,0.00001))
                        ystart+=15
                elif fd["mode"]=="ms3":
                    keys = ["mode", "analyzer", "data", "precursor", "reaction", "energy", "mr", "precursor ms3", "reaction ms3", "energy ms3"]
                    for key in keys:
                        dc.DrawText(fd[key], x+5, ystart)
                        self.msdb.svg["text"].append((fd[key], x+5, ystart,0.00001))
                        ystart+=15
            if currentFile['vendor']=='Thermo' and currentFile['spectrum_style']=='single scan':
                try:
                    inj_time = currentFile['m'].scanInjectionTime(currentFile["scanNum"])
                    dc.DrawText("Inj: " + str(inj_time), x+5, ystart)
                    self.msdb.svg["text"].append(("Inj: " + str(inj_time), x+5, ystart,0.00001))
                except AttributeError: # Actually a WIFF file in disguise.
                    pass
                
                
            dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
        #self.parent.Window.dragController.SetPosition()
        #page=self.ctrl.GetPage(self.ctrl.GetSelection())
        
        if currentFile["ID"]: # Handles drawing the sequence
            #print "ID!!"
            key = None
            if currentFile['vendor']=='Thermo':
                key = currentFile["scanNum"]
            elif currentFile['vendor']=='ABI':
                key = (currentFile['scanNum'], currentFile['experiment'])
            elif currentFile['vendor']=='mgf':
                key = currentFile["scanNum"]          
            
            if currentFile["SearchType"] in ["Mascot", "X!Tandem"]:
                seq = currentFile["ID_Dict"][key]["Peptide Sequence"]
                fixedmod = currentFile["fixedmod"]
                varmod = currentFile["ID_Dict"][key]["Variable Modifications"]
            if currentFile["SearchType"] in ['Proteome Discoverer']:
                seq = currentFile["ID_Dict"][key]["Annotated Sequence"].upper()
                fixedmod = ''
                varmod = currentFile["ID_Dict"][key]["Modifications"]            
            else:
                seq = currentFile["ID_Dict"][key]["Peptide Sequence"]
                fixedmod = currentFile["fixedmod"]
                varmod = currentFile["ID_Dict"][key]["Variable Modifications"]                
            
            if currentFile["SearchType"] in ["Mascot", "X!Tandem"]:
                score = currentFile["ID_Dict"][key]["Peptide Score"]
            elif currentFile["SearchType"]=="COMET" :
                score = currentFile["ID_Dict"][key]["Cross-Correlation"]
            elif currentFile["SearchType"]=="Proteome Discoverer" :
                score = currentFile["ID_Dict"][key]["XCorr"]            
                 
            peptide_container = mz_core.create_peptide_container(seq, varmod, fixedmod)
            sequence = ''
            for member in peptide_container:
                sequence += member            
            dc.DrawText(sequence + ' (' + str(score) + ')', currentFile['axco'][currentFile['axes']-1][0][0]+100, currentFile['axco'][currentFile['axes']-1][0][1] + 25)
            self.msdb.svg["text"].append((seq, currentFile['axco'][currentFile['axes']-1][0][0]+100, currentFile['axco'][currentFile['axes']-1][0][1] + 25,0.00001))

    def DrawProfileSpectrum(self, dc, key, rawID):
        '''
        
        Main function for drawing profile data.
        
        
        '''
        currentFile = self.msdb.files[self.msdb.Display_ID[rawID]]
        firstMass = currentFile["mass_ranges"][key][0]
        lastMass = currentFile["mass_ranges"][key][1]
        
        xaxis = currentFile['axco'][key][0]
        yaxis = currentFile['axco'][key][1]
        height = yaxis[1]-yaxis[3]
        width = xaxis[2]-xaxis[0]
        self.indent = yaxis[0]
        
        if not currentFile['intensity_scaling']:
            max_int = self.msdb.GetMaxInt(firstMass, lastMass, self.msdb.Display_ID[rawID])
        else:
            max_int = currentFile['intensity_scaling']
            
        cutoff = 0.75 * float(max_int)
        dc.SetTextForeground("BLACK")
        dc.SetFont(wx.Font(10, wx.ROMAN, wx.NORMAL, wx.BOLD, False))
        
        mr = currentFile["mass_ranges"][key][1]-currentFile["mass_ranges"][key][0]
        #print mr
        px = width
        self.width = width
        labels = []
        scan_type = 'MS2'
        if currentFile['vendor'] == 'Thermo':
            if currentFile['spectrum_style']=='single scan':
                filter = currentFile["filter_dict"][currentFile["scanNum"]]
            else:
                filter = currentFile["filter_dict"][int(currentFile["scanNum"].split('-')[0])]              
                          
        elif currentFile['vendor'] == 'ABI-MALDI':
            filter = currentFile['filter_dict'][None]
        elif currentFile['vendor'] == 'ABI':
            try:
                filter = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]
            except:
                filter = currentFile["filter_dict"][(currentFile["scanNum"])]
        #print filter
        if filter.find("FTMS") > -1 and filter.find("Full ms ") > -1:
            scan_type = 'MS1'
        if filter.find("TOF MS") > -1 and filter.find("Full ms ") > -1:
            scan_type = 'MS1'
        #print scan_type
        scan_data = currentFile["scan"]
        scan_data.sort(key = lambda t:t[0])

        if len(scan_data) > 1 and max_int > 0:
            points = []
            dc.SetPen(wx.Pen(wx.Colour(*currentFile['settings']['line color']),currentFile['settings']['line width']))
            
            y_var = yaxis[1] + yaxis[3]-yaxis[1] # == yaxis[3]?
            y_var2 = (yaxis[3]-yaxis[1])
            
            for member in scan_data:
                if member[0]>firstMass and member[0]<lastMass:
                    x1 = yaxis[0] + px*((member[0]-firstMass)/float(mr))
                    if currentFile['intensity_scaling'] and member[1] > float(max_int):
                        y1 = y_var - (yaxis[3]-yaxis[1]) 
                    else:
                        y1 = y_var - y_var2*(member[1]/float(max_int))
                    
                    points.append((x1, y1))
            
            dc.DrawLines(points)
            self.msdb.svg["pointLists"].append(points)

    def myRound(self, x, base=5):
        return int(base*round(float(x)/base))

    def locateMS2(self, mz, tolerance):
        '''
        
        Searches file for precursors within a certain mass range.
        
        '''
        currentFile = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        counter = 0
        found = []        
        
        if currentFile['vendor'] == 'Thermo':
            inst=["FTMS", "ITMS", "TOF PI"]
            mode=["c","p"]
            act=["hcd", "cid", "etd"]
            regex = None
            
            #------------------------------Which regex to use?
            if currentFile['FileAbs'].endswith('.raw'):
                regex = [self.msdb.pa, self.msdb.lockms2]
            elif currentFile['FileAbs'].endswith('.wiff'):
                regex = self.msdb.tofms2            
            elif currentFile['FileAbs'].endswith('.d'):
                regex = self.msdb.Dms     
            
            
            #-------------------------------Loop through all scans    
            start, stop = currentFile["scan_range"]
            for i in range(start, stop):
                if counter % 500 == 0:
                    print str(i)
                    print currentFile["filter_dict"][i]
                counter += 1
                #------------------------------------------FIND MS2 scans, then match to regex.
                if currentFile["scan_dict"][i]=="MS2":
                    filt = currentFile["filter_dict"][i]
                    if not isinstance(regex, list):
                        id = regex.match(filt)
                    else:
                        for reg in regex:
                            id = reg.match(filt)
                            if id:
                                break
                    #--------------------------------------------------------Right now, thermo and wiff are the same logic; should adjust Agilent so the same.
                    #--------------------------------------------------------This would remove the extra if/else.
                    if currentFile['FileAbs'].endswith('.d') == False:
                        # IF NOT AGILENT, WILL BE THERMO, ABI.
                        if currentFile['vendor']=='Thermo':
                            # THERMO OR WIFF
                            if id:
                                if id.groups()[0] in inst and id.groups()[1] in mode and id.groups()[3] in act:
                                    prec = float(id.groups()[2])
                                    if mz > prec - tolerance and mz < prec + tolerance:
                                        found.append([i, id.groups()[2], id.groups()[3], filt])
                            else:
                                id = self.msdb.etd.match(filt)
                                if id:
                                    #'.*?([FI]TMS) [+] ([cp]) NSI (t E d sa|d sa) Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]'
                                    if id.groups()[0] in inst and id.groups()[1] in mode and id.groups()[4] in act:
                                        prec = float(id.groups()[3])
                                        if mz > prec - tolerance and mz < prec + tolerance:
                                            found.append([i, id.groups()[3], id.groups()[4], filt])
                        
                    #AGILENT   
                    else:
                        prec = float(id.groups()[3])
                        if mz > prec - tolerance and mz < prec + tolerance:
                            found.append([i, id.groups()[3], "CAD", filt])
                            
        elif currentFile['vendor'] == 'mgf':
            regex = self.msdb.mgf            
            for key in currentFile['filter_dict'].keys():
                current_filter = currentFile['filter_dict'][key]
                if current_filter.lower().find("ms2") > -1:
                    id = regex.match(current_filter)
                    if id:
                        prec = float(id.groups()[0])
                        if mz > prec - tolerance and mz < prec + tolerance:
                            found.append([key, prec, 'MGF MS2', current_filter])            
                            
                             
                                    

        found.sort()
       
        return found

    def storeImage(self, dc):
        #size = dc.Size
        size = self.GetClientSize()
        bmp = wx.EmptyBitmap(size.width, size.height)
        #bmp = wx.EmptyBitmap(1690, 1050)
        memDC = wx.MemoryDC()
        memDC.SelectObject(bmp)
        memDC.Blit(0,0,size.width,size.height,dc,0,0)
        #memDC.Blit(0,0,1690,1050,dc,0,0)
        memDC.SelectObject(wx.NullBitmap)
        img = bmp.ConvertToImage()
        self.img = img

    def OnDraw(self, dc):
        '''
        
        Main loop for redrawing mzStudio datafile window, for example XIC and spectra.
        
        '''
        
        sz = self.parent.notebook.GetClientSize()
        if sz[0] > 400 and sz[1] > 250:
        
            t1 = time.time()
            dc.SetBackground( wx.Brush("White") )
            dc.Clear() # make sure you clear the bitmap!        
            try:
                del self.msdb.svg
            except:
                pass
            self.msdb.svg = defaultdict(list)
            
            dc.SetPen(wx.Pen(wx.BLACK,2))
            for i in range(0, self.msdb.getFileNum()):
                if self.msdb.files[self.msdb.Display_ID[i]]["Display"]:
                    currentFile = self.msdb.files[self.msdb.Display_ID[i]]
                    for k in range(0, self.msdb.files[self.msdb.Display_ID[i]]["axes"]):
                        #print "DRAWING... spec axis " + str(k) + " on file " + str(i)
                        profFlag = False
                        if currentFile["vendor"] in ["Thermo", "ABI-MALDI", 'mgf']:
                            try:
                                filt = currentFile["filter_dict"][currentFile["scanNum"]]
                            except KeyError:
                                filt = currentFile["filter_dict"].values()[0]
                        elif currentFile["vendor"]=="ABI":
                            try:
                                filt = currentFile["filter_dict"][(currentFile["scanNum"], currentFile['experiment'])]
                            except:
                                filt = currentFile["filter_dict"][(currentFile["scanNum"])]
                        #if filt.find("+ p")>-1:
                        if '+ p' in filt:
                            profFlag = True # Indicates *file* scan is in profile data.
                               
                        t2=time.time()
                        #if currentFile["vendor"] != "ABI-MALDI": #Need to have option to centroid
                        self.DrawSpectrum(dc, k, i, profFlag) #draws the centroid
                        t3=time.time()
                        #is this a profile spectrum?
                        if profFlag and not (currentFile["viewCentroid"] or currentFile['Processing']):
                            self.DrawProfileSpectrum(dc, k, i)
                        t4=time.time()
                        if currentFile['features']:
                            self.DrawFeatures(dc, k, i)
                        
                
                    if self.msdb.files[self.msdb.Display_ID[i]]["mode"] != "SPEC":
                        currentFile['xic_lookup']=[]
                        #---------------------------------FIND MAXIMA
                        maxTables = []
                        startTime = currentFile["time_ranges"][0][0]
                        stopTime = currentFile["time_ranges"][0][1]
                        global_grid = 0
                        global_trace = 0
                        global_inten = 0
                        for k in range(0, len(self.msdb.files[self.msdb.Display_ID[i]]["xic_axco"])):
                            maxTable = []
                            for xic in range(0, len(currentFile["xic_params"][k])):
                                if currentFile['xic_view'][k][xic]: #DECISION POINT COULD BE ADDED WHETHER TO SCALE IF VISIBLE OR NOT
                                    maxTable.append(self.msdb.GetMaxSignal(startTime, stopTime, k, self.msdb.Display_ID[i], xic))
                                else:
                                    maxTable.append(0)
                            maxTables.append(maxTable)
                        for ti, table in enumerate(maxTables):
                            for tj, entry in enumerate(table):
                                if maxTables[ti][tj] > global_inten:
                                    global_inten = maxTables[ti][tj]
                                    global_grid = ti
                                    global_trace= tj
                        global_max = (global_grid, global_trace)
                        self.max_tables = maxTables
                        t5 = time.time()
                        #---------------------------------DRAW XICs one by one
                        for k in range(0, len(self.msdb.files[self.msdb.Display_ID[i]]["xic_axco"])):
                            #print "DRAWING... ric axis " + str(k) + " on file " + str(i)
                            self.DrawXic(dc, k, i, global_max, maxTables)
            t6 = time.time()
                  
            self.storeImage(dc)
            
            for i in range(0, len(self.msdb.files.keys())):
                if self.msdb.files[self.msdb.Display_ID[i]]["locked"]:
                    x = self.msdb.files[self.msdb.Display_ID[i]]["axco"][0][0][2]
                    y = self.msdb.files[self.msdb.Display_ID[i]]["axco"][0][1][1]
                    dc.DrawBitmap(self.lock_image, x, y+60, True)
                if self.msdb.files[self.msdb.Display_ID[i]]["Display"]:
                    x = self.msdb.files[self.msdb.Display_ID[i]]["axco"][0][0][2]
                    y = self.msdb.files[self.msdb.Display_ID[i]]["axco"][0][1][1]
                    if i == self.msdb.active_file:
                        dc.DrawBitmap(self.active_image, x, y, True)
                    else:
                        dc.DrawBitmap(self.inactive_image, x, y, True)
                    if self.msdb.files[self.msdb.Display_ID[i]]["rows"]:
                        dc.DrawBitmap(self.xls_image, x, y+30, True)
                    if self.msdb.files[self.msdb.Display_ID[i]]["datLink"]:
                        dc.DrawBitmap(self.mascot_image, x, y+90, True)
            
            #print "Drawing"        
            #t7 = time.time()
            #print "Setup:" + str(t2-t1)
            #print "Draw Spectrum: " + str(t3-t2)
            #print "Draw Profile: " + str(t4-t3)
            #print "Get Max Int Table: " + str(t5-t4)
            #print "Draw XIC: " + str(t6-t5)
            #print "Draw Bitmaps: " + str(t7-t6)
            #print "Total: " + str(t7-t1)
        else:
            dc.SetBackground( wx.Brush("White") )
            dc.Clear() # make sure you clear the bitmap!              
            dc.DrawText("Can't Display! Resize!", 10, 10)
                    
            

    def On_Text_Spectrum(self):
        infodict = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        scan = infodict['processed_data']
        filt = infodict['filter_dict'][infodict['scanNum']]
        scan.sort()
        textdog = TextSpectrumDialog(self, scan, filt)
        textdog.ShowModal()
        textdog.Destroy()
    
    def On_Search_Spectrum(self):
        
        #---------------------------------------------
        # CODE FOR SEARCH OF ACTIVE SPECTRUM WITH MASCOT, COMET, or X!Tandem
        # ALGORITHM SELECTED IN SETTINGS PAGE
        # MASCOT SERVER SETTINGS CAN BE DEFINED IN MZ DESKTOP GUI (PREFERENCES)
        #---------------------------------------------
        
        infodict = self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]
        searchMode = infodict['settings']['searchAlgorithm']
            
        scan = [x[:2] for x in infodict['processed_data']]
        filt = infodict['filter_dict'][infodict['scanNum']]
        scan.sort() # Just in case it isn't already, if not it could cause problems.
        
        
        if '@' not in filt and 'ms2' not in filt.lower():
            wx.MessageBox(("Invalid filter string for search: %s"
                           "\n(Is this not an MS2 spectrum?)")
                          % filt)
            return
        
        
        if '@' in filt:
            mz = filt.split('@')[0].split()[-1]        
        else:
            words = filt.lower().split()
            try:
                mz = float(words[words.index('ms2') + 1])
            except ValueError:
                wx.MessageBox("Invalid filter string for search: %s" % filt)
                return        
            
        if searchMode == 'Mascot':
            from MascotSearch import runMascotSearch
            
            results = runMascotSearch((scan, filt, mz))
            if results:
                psms, header = results
            else: # Login cancellation or something.
                return
            if psms == None:
                return
            if not psms:
                messdog = wx.MessageDialog(self, 'No peptide match found.',
                                           style = wx.OK)
                messdog.ShowModal()
                return
            else:
                psm = max(psms, key = lambda x: x['Peptide Score'])
                # Temporary PSM output.
                print psm
                print 'SCORE: %s' % psm['Peptide Score']
                infodict['SearchType']="Mascot"
                         
        elif searchMode == 'Comet':
            from Comet_GUI import run_GUI_from_app
            psms, header = run_GUI_from_app(self, scan, mz)
            if psms == None:
                return
            if not psms:
                messdog = wx.MessageDialog(self, 'No peptide match found.',
                                           style = wx.OK)
                messdog.ShowModal()
                return
            else:
                rank_one = filter(lambda x: x['Peptide Rank']==1, psms)
                psm = max(rank_one, key = lambda x: x['Cross-Correlation'])
                print psm
                print 'SCORE: %s' % psm['Cross-Correlation']
                infodict['SearchType']="COMET"
                
            
        elif searchMode == 'X!Tandem':
            from Tandem_GUI import run_GUI_from_app
            psms, header = run_GUI_from_app(self, scan, mz)
            if psms == None:
                return
            if not psms:
                messdog = wx.MessageDialog(self, 'No peptide match found.',
                                           style = wx.OK)
                messdog.ShowModal()
                return
            else:
                psm = max(psms, key = lambda x: x['Peptide Score'])
        else:
            raise Exception, "Invalid search mode string: %s" % searchMode
        
        # Note that the psms will have different keys based on where they
        # come from; I've tried to standardize the reports but that only
        # goes so far.
        
        #---------------------------------------------------
        # Transfer the most significant hit to the ID_Dictionary, build the ID, and refresh the display.
        infodict["ID_Dict"][infodict['scanNum']] = psm 
        self.msdb.build_current_ID(self.msdb.Display_ID[self.msdb.active_file], self.msdb.files[self.msdb.Display_ID[self.msdb.active_file]]["scanNum"])
        self.Window.UpdateDrawing()
        self.Refresh()
        
class MyGrid(grid.Grid, glr.GridWithLabelRenderersMixin):
    def __init__(self, *args, **kw):
        grid.Grid.__init__(self, *args, **kw)
        glr.GridWithLabelRenderersMixin.__init__(self)

class MyColLabelRenderer(glr.GridLabelRenderer):
    def __init__(self):
        self._bmp = wx.ArtProvider.GetBitmap(wx.ART_CLOSE)

    def Draw(self, grid, dc, rect, col):
        x = rect.left + (rect.width - self._bmp.GetWidth()) / 2
        y = rect.top + (rect.height - self._bmp.GetHeight()) / 2
        dc.DrawBitmap(self._bmp, x, y, True)

class MyRowLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor

    def Draw(self, grid, dc, rect, row):
        dc.SetBrush(wx.Brush(self._bgcolor))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)

class findGrid(wx.grid.Grid):
    '''
    
    Grid for the Find output function.
    
    '''
    def __init__(self, parent, rows):
        wx.grid.Grid.__init__(self, parent, -1, pos=(0,0), size =(450,200))
        self.CreateGrid(rows,4)
        self.SetColLabelValue(0, "Scan")
        self.SetColLabelValue(1, "mz")
        self.SetColLabelValue(2, "Scan type")
        self.SetColLabelValue(3, "Filter")
        self.SetColSize(0,5)

class findOutput(wx.Panel):
    '''
    
    This makes the panel after a precursor search, allowing user to go to MS2 scans.
    
    '''
    def __init__(self,parent,output):
        self.output = output
        self.parent = parent
        wx.Panel.__init__(self, parent, size=(475,275))
        self.grid = findGrid(self, len(output))
        self.grid.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelClick)
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        for i, member in enumerate(output):
            self.grid.SetCellValue(i, 0, str(member[0]))
            self.grid.SetCellValue(i, 1, str(member[1]))
            self.grid.SetCellValue(i, 2, str(member[2]))
            self.grid.SetCellValue(i, 3, str(member[3]))

    def OnLabelClick(self,event):
        row = event.GetRow()
        if row < 0:
            event.Skip()
        
        #print scan
        currentPage = self.parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
        self.currentPage = currentPage
        self.currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]        
        
        if self.currentFile['vendor'] in ['Thermo', 'mgf'] and row != -1:
            scan = int(self.grid.GetCellValue(row, 0))        
            self.currentPage.msdb.files[self.currentPage.msdb.Display_ID[self.currentPage.msdb.active_file]]["scanNum"]=scan
       
        self.currentPage.msdb.set_scan(scan, self.currentPage.msdb.active_file)
        
        if self.currentFile['vendor']=='Thermo' and row != -1:
            self.currentPage.msdb.build_current_ID(self.currentPage.msdb.files[self.currentPage.msdb.Display_ID[self.currentPage.msdb.active_file]]["FileAbs"], scan)
        if self.currentFile['vendor']=='ABI':
            exp = self.currentFile['experiment']
            self.currentPage.msdb.build_current_ID(self.currentPage.msdb.files[self.currentPage.msdb.Display_ID[self.currentPage.msdb.active_file]]["FileAbs"], (scan, exp), 'ABI')
        self.currentPage.Window.UpdateDrawing()
        self.currentPage.Refresh()

class RecalFrame(wx.Frame):
    '''
    
    Recalibreate current scan.
    
    '''
    def __init__(self, parent):
        self.parent = parent
        self.currentFile = parent.msdb.files[parent.msdb.Display_ID[parent.msdb.active_file]]
        wx.Frame.__init__(self, parent, -1, "Recalibrate Scan", size=(225, 150))
        panel = wx.Panel(self, -1)
        
        self.label1 = wx.StaticText(panel, -1, label="Slope", size=(200, 20), pos=(75, 10))
        self.label2 = wx.StaticText(panel, -1, label="Intercept", size=(200,20), pos=(75,30))
        self.slope = wx.TextCtrl(panel, -1, '1', size = (50,20), pos=(10, 10))
        self.intercept = wx.TextCtrl(panel, -1, "0", size = (50,20), pos=(10, 30))
        self.btn = wx.Button(panel, -1, "Recalibrate", pos = (10, 50), size=(50,20))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.ToggleWindowStyle(wx.STAY_ON_TOP)

    def OnClick(self,event):
        slope = float(self.slope.GetValue().strip())
        intercept = float(self.intercept.GetValue().strip())
        
        for member in self.currentFile["scan"]:
            member[0] = member[0] + member[0] * slope + intercept
        self.parent.Window.UpdateDrawing()
        self.parent.Refresh()
        self.Hide()


class findFrame(wx.Panel):
    def __init__(self, parent):
        '''
        
        This code screens MS2 scans for m/z +/- specified tolerance and displays in a grid for selection.
        PARENT = AUI Frame; self.parent._mgr = AUI Manager
        
        '''
        assert 'TopLevelFrame' in str(type(parent)) # Is called from multiple places, not correctly in each case.
        # TopLevelFrame is when called from the toolbar; where else?
        
        self.parent = parent
        currentPage = parent.ctrl.GetPage(self.parent.ctrl.GetSelection())
        self.currentPage = currentPage
        self.currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]

        wx.Panel.__init__(self, parent, size=(225, 150))
        
        mass_entry = ''
        
        if self.currentFile["vendor"] in ['Thermo', 'mgf']:
            filt = self.currentFile["filter_dict"][self.currentFile["scanNum"]]
        #elif self.currentFile["vendor"]=='ABI':
        #    filt = self.currentFile["filter_dict"][(self.currentFile["scanNum"],self.currentFile["experiment"])]
        
        #2017-03-26 adding code for lock mass scans.
        if filt.find("ms2") > -1:
            ms2_filters = [(currentPage.msdb.pa,2), (currentPage.msdb.etd,3), (currentPage.msdb.lockms2, 2), (currentPage.msdb.mgf, 0)]
            for ms2_filter, mass_group in ms2_filters:
                match = ms2_filter.match(filt)
                if match:
                    mass_entry = match.groups()[mass_group]
                
        self.label1 = wx.StaticText(self, -1, label="mz", size=(200, 20), pos=(75, 10))
        self.label2 = wx.StaticText(self, -1, label="Tolerance", size=(200,20), pos=(75,30))
        self.prec = wx.TextCtrl(self, -1, mass_entry, size = (50,20), pos=(10, 10))
        self.tol = wx.TextCtrl(self, -1, "3", size = (50,20), pos=(10, 30))
        self.btn = wx.Button(self, -1, "Locate", pos = (10, 50), size=(50,20))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.ToggleWindowStyle(wx.STAY_ON_TOP)

    def OnClick(self,event):
        prec = float(self.prec.GetValue().strip())
        tol = float(self.tol.GetValue().strip())
        
        #-----------------------------------------------------
        #--  THIS SEARCHES PRECURSOR MASSES FOR MATCHES
        foundList = self.currentPage.locateMS2(prec, tol)
        
        # outputFrame used to be made a member of TopLevelFrame, but this
        # remote attribute-assignment was unwise and, also, it didn't seem
        # to be accessed outside this function.
        outputFrame = findOutput(self.parent, foundList)
        
        self.parent._mgr.DetachPane(self)
        self.parent._mgr.AddPane(outputFrame, aui.AuiPaneInfo().Left().Caption("MS2: " + str(prec) + ' +/- ' + str(tol) + ' Da'))
        self.parent._mgr.Update()
        self.Destroy()

class XICgrid(grid.Grid, glr.GridWithLabelRenderersMixin):
    def __init__(self, parent, *args, **kw):
        grid.Grid.__init__(self, parent.panel, id=-1, size=(950,200), pos=(0,0))
        glr.GridWithLabelRenderersMixin.__init__(self)
        self.CreateGrid(150,15)  #ROWS, COLUMNS
        for i, setting in enumerate([("Window", 50), ("Start", 50), ("Stop", 50), ("Filter", 185), ("Remove", 20), ("Scale", 50), ("Active", 50), ("View", 50), ("Type",50), ("Sequence",152), ("mz",50), ("Cg",20),("Scan", 50), ("Marks",50), ("Title", 100)]):
            self.SetColLabelValue(i, setting[0])
            self.SetColSize(i, setting[1])
        #self.SetRowLabelRenderer(0, MyRowLabelRenderer('#ffe0e0'))
        self.SetColLabelRenderer(4, MyColLabelRenderer())
        #self.SetColLabelRenderer(6, MyColLabelRenderer())
        self.parent = parent
        try:
            all_modes = self.parent.currentFile['m'].scan_modes()
            filter_list = ['Full ms ']
            for mode in all_modes:
                if mode not in filter_list:
                    filter_list.append(mode)
        except AttributeError:
            filter_list = ['Full ms ','Full ms2 ']
        if self.parent.currentFile['m'].file_type == 'mgf':
            filter_list = ['MGF ms2']
        filter_list += self.parent.currentFile["targ_filt"]
        for k in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            self.SetCellEditor(k,3,wx.grid.GridCellChoiceEditor(choices=filter_list, allowOthers=True))
            self.SetCellEditor(k,4,wx.grid.GridCellBoolEditor())
            self.SetCellRenderer(k, 4, wx.grid.GridCellBoolRenderer())
            self.SetCellValue(k, 5, "Auto")
            self.SetCellEditor(k, 6, wx.grid.GridCellBoolEditor())
            self.SetCellRenderer(k, 6, wx.grid.GridCellBoolRenderer())
            self.SetCellEditor(k, 7, wx.grid.GridCellBoolEditor())
            self.SetCellRenderer(k, 7, wx.grid.GridCellBoolRenderer())
            self.SetCellEditor(k,8,wx.grid.GridCellChoiceEditor(choices=['x', 'p'], allowOthers=False))
            
        #---------------------------------Peptigram functionality not yet ready for release.
        #---------------------------------Hide these columns for now.
        for k in [8, 9, 10, 11, 12]:
            self.HideCol(k)

class xicFrame(wx.Frame):
    '''
    
    Interface for performing extracted ion chromatograms.
    
    '''
    def __init__(self, parent, currentFile, fileID):
        self.currentFile = currentFile
        self.fileID = fileID
        self.xic_mass_ranges = currentFile["xic_mass_ranges"]
        self.filters = currentFile["filters"]
        self.xic_scale = currentFile['xic_scale']
        self.xic_type = currentFile['xic_type']
        self.xic_mz = currentFile['xic_mass']
        self.xic_cg = currentFile['xic_charge']
        self.xic_sequence = currentFile['xic_sequence']
        self.xic_scan = currentFile['xic_scan']
        self.xic_marks = currentFile['xic_marks']
        self.xic_dict = currentFile["xic_dict"]
        self.x = currentFile["xic"]
        self.titles = currentFile['xic_title']
        self.parent = parent
        #original: size=(600,175)
        wx.Frame.__init__(self, parent, -1, "XIC", size=(750,300))
        self.panel = wx.Panel(self, -1)
        if not self.currentFile['targ_check']:
            targ_filt = set()
            for member in currentFile['filter_dict'].values():
                id = self.parent.msdb.targ.match(member)
                if id:
                    targ_filt.add(member)
                id = self.parent.msdb.targ_ms3.match(member)
                if id:
                    targ_filt.add(member)                
            self.currentFile["targ_filt"] = list(targ_filt)
            self.currentFile['targ_check']=True
        self.grid = XICgrid(self)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        #print self.currentFile['targ_check']
        #print self.currentFile["targ_filt"]
        self.btn = wx.Button(self.panel, -1, "OK", size=(25,25), pos = (0, 210))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.saveButton = wx.Button(self.panel, -1, "Save", size=(40,25), pos = (35, 210))
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.saveButton)
        self.loadButton = wx.Button(self.panel, -1, "Load", size=(40,25), pos = (85, 210))
        self.Bind(wx.EVT_BUTTON, self.OnLoad, self.loadButton)
        #self.defaultButton = wx.Button(self.panel, -1, "Delete", size=(40,25), pos = (130, 210))
        #self.Bind(wx.EVT_BUTTON, self.OnDefault, self.defaultButton)        
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        self.scanButton = wx.Button(self.panel, -1, "Scan Filters", size=(150,25), pos = (355, 210))
        self.Bind(wx.EVT_BUTTON, self.OnScan, self.scanButton)             
        
        
        self.mark_base = []
        self.xbase = []
        self.InitialGridPopulate()
        #for j in range(counter, 150):
        #    self.mark_base.append({})
        self.radiobox = wx.RadioBox(self.panel, -1, label='Parameters', pos=(150, 210), size=wx.DefaultSize, choices=['Start\Stop', 'Center\Width'], majorDimension=2, style=wx.RA_SPECIFY_COLS | wx.NO_BORDER) #
        self.radiobox.Hide()
        self.Bind(wx.EVT_RADIOBOX, self.OnRadio, self.radiobox)
        self.type = "SS"
    
    def InitialGridPopulate(self):
        active_xic = self.currentFile['active_xic'] # [0,1,0]
        xic_view = self.currentFile['xic_view']        
        counter = 0
        for i, member in enumerate(self.xic_mass_ranges): # 0, [(300,2000)]
            for j, trace in enumerate(member): # 0, (300,2000)
                self.grid.SetCellValue(counter, 0, str(i))
                self.grid.SetCellValue(counter, 1, str(trace[0]))
                self.grid.SetCellValue(counter, 2, str(trace[1]))
                self.grid.SetCellValue(counter, 3, str(self.filters[i][j]))
                self.grid.SetCellValue(counter, 14, self.titles[i][j])
                self.grid.SetCellValue(counter, 5, str(self.xic_scale[i][j] if self.xic_scale[i][j] > -1 else "Auto"))
                self.grid.SetCellValue(counter, 6, '1' if j == active_xic[i] else '')
                self.grid.SetCellValue(counter, 7, '1' if xic_view[i][j] else '')
                self.grid.SetCellValue(counter, 8, str(self.xic_type[i][j]))
                self.grid.SetCellValue(counter, 13, str('(...)'))
                self.mark_base.append(self.xic_marks[i][j])
                self.xbase.append(self.x[i][j])
                if self.xic_type[i][j] == 'p': #SEQ MZ CG SCAN
                    self.grid.SetCellValue(counter, 9, str(self.xic_sequence[i][j]))
                    self.grid.SetCellValue(counter, 10, str(self.xic_mz[i][j]))
                    self.grid.SetCellValue(counter, 11, str(self.xic_cg[i][j]))
                    self.grid.SetCellValue(counter, 12, str(self.xic_scan[i][j]))
                counter += 1        
        
    
    def OnScan(self, evt):
        '''
        
        2015-11-09 version 0.1
        
        If running targ MS2 from inclusion list, the filter has a 'd' so that the targ check does not pick it up.
        To add inclusion list MS2 to the filter combo box, this function was added.
        
        '''
        
        print "Scanning"
        targ_filt = set()
        for member in self.currentFile['filter_dict'].values(): 
            targ_filt.add(member)
        print len(targ_filt)
        self.currentFile["targ_filt"] = list(targ_filt)
        self.currentFile['targ_check']=True
        self.grid.Destroy()
        self.grid = XICgrid(self)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellLeftDClick)
        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)        
        self.InitialGridPopulate()
    
    def get_next_available_window(self):
        winmax = 0
        for k in range(0,150):
            if self.grid.GetCellValue(k, 0):
                curWin = int(self.grid.GetCellValue(k, 0))
                if curWin > winmax:
                    winmax = curWin
            else:
                break
        winmax += 1
        return winmax
    
    def OnSelectCell(self, evt):  
        if evt.GetRow() == self.GetXICEntries():
            self.grid.SetCellValue(self.GetXICEntries(), 13, str('(...)'))
            self.grid.SetCellValue(self.GetXICEntries()-1, 6, '1')
            self.grid.SetCellValue(self.GetXICEntries()-1, 7, '1')
            self.grid.SetCellValue(self.GetXICEntries()-1, 8, 'x')
            if self.GetXICEntries()-1 != 0:
                if self.currentFile['xic_style'] != 'OVERLAY':
                    prev = self.GetXICEntries() - 2
                    value = int(self.grid.GetCellValue(int(prev), 0))
                    value += 1
                    self.grid.SetCellValue(self.GetXICEntries()-1, 0, str(value))
                else:
                    prev = self.GetXICEntries() - 2
                    value = int(self.grid.GetCellValue(int(prev), 0))
                    self.grid.SetCellValue(self.GetXICEntries()-1, 0, str(value))                    
            self.mark_base.append({})
    
    def GetXICEntries(self):
        '''
        
        Counts the number of entries in the XIC grid.
        
        '''
        for i in range(0, 150):
            if self.grid.GetCellValue(i, 13) == '':
                break
        return i
          
    def OnCellLeftDClick(self, evt):
        print "Got it!"
        #If valid mark cell, open window and edit
        #evt.GetRow(), evt.GetCol(), evt.GetPosition()
        if evt.GetCol() == 13:
            if evt.GetRow() < self.GetXICEntries():
                index = evt.GetRow()
                current_mark = self.mark_base[index]
                current_xic = self.xbase[index]
                self.Hide()
                m = MGrid.MFrame(parent=self, currentMarks=current_mark, currentXIC=current_xic, index=index, dataFile=self.currentFile['m'])
                m.Show()
        evt.Skip()
        
    def OnDefault(self, event):
        pass

    def OnRadio(self, event):
        print "radio"
        print self.radiobox.GetSelection()
        if self.radiobox.GetSelection() == 0:
            self.type = "SS"
            self.grid.SetColLabelValue(0, "Start")
            self.grid.SetColLabelValue(1, "Stop")
            for i in range(0,4):
                current = self.grid.GetCellValue(i,0)
                if current != '':
                    if not self.grid.GetCellValue(i,3):
                        center = float(self.grid.GetCellValue(i, 0))
                        width = float(self.grid.GetCellValue(i, 1))
                        start = center - width
                        stop = center + width
                        self.grid.SetCellValue(i,0,str(start))
                        self.grid.SetCellValue(i,1,str(stop))            
        else:
            self.type = "CW"
            self.grid.SetColLabelValue(0, "Center")
            self.grid.SetColLabelValue(1, "Width")
            for i in range(0,4):
                current = self.grid.GetCellValue(i,0)
                if current != '':
                    if not self.grid.GetCellValue(i,3):
                        start = float(self.grid.GetCellValue(i, 0))
                        stop = float(self.grid.GetCellValue(i, 1))
                        xr = float(stop-start)/float(2)
                        center = start + xr
                        self.grid.SetCellValue(i,0,str(center))
                        self.grid.SetCellValue(i,1,str(xr))
                                

    def CountMarks(self):
        marks = 0
        for i, window in enumerate(self.mark_base):
            for j, xic in enumerate(window):
                mark_dict = self.mark_base[i][j]
                marks += len(mark_dict.keys())
        return marks
                
    def OnSave(self, event):
        '''
        
        Save grid settings to file.
        
        
        '''
        dlg = wx.FileDialog(None, "Save as..", pos = (2,2), style = wx.SAVE, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.savedir = dir
        self.savefilename = filename
        #print dir
        #print filename
        if filename.find(".txt") == -1:
            filename += ".txt"
            self.savefilename = filename
        file_w = open(dir + '\\' + filename, 'w')

        lines = []
        for member in range(0,150):
            line = [str(self.grid.GetCellValue(member,col)) for col in [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]]
            lines.append(line)
        outlist = []
        for line in lines:
            print line
            print line[0]
            if line[0] != '':
                for i, member in enumerate(line):
                    if not member:
                        line[i] = '0'
                outlist.append(line)
        num_lines = len(outlist) - 1
        for i, line in enumerate(outlist):
            file_w.write('\t'.join(x for x in line))
            if i < num_lines:
                file_w.write('\n')
            #file_w.write(line[0] + '\t' + line[1] + '\t' + line[2] + '\t' + line[3] + '\t' + line[4] + '\t' + line[5] if line[5] else '0' + '\t' + line[6] if line[6] else '0' + '\t\n')
        file_w.close()

    def OnLoad(self, event):
        '''
        
        Load contents of text file into grid.
        
        '''
        dlg = wx.FileDialog(None, "Load...", pos = (2,2), style = wx.OPEN, wildcard = "text files (*.txt)|")
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dir = dlg.GetDirectory()
            os.chdir(dir)
        dlg.Destroy()
        self.loaddir = dir
        self.loadfilename = filename
        #print dir
        #print filename
        self.grid.ClearGrid()
        file_r = open(dir + '\\' + filename, 'r')
        lines = file_r.readlines()
        self.mark_base = []
        for i, line in enumerate(lines):
            data = lines[i].split('\t')
            for col in [0,1,2,3,7,8,9,10,11]:
                self.grid.SetCellValue(i, col, str(data[col]))
            self.grid.SetCellValue(i, 5, str(data[4]))
            self.grid.SetCellValue(i, 6, '1' if str(data[5]) == '1' else '')
            self.grid.SetCellValue(i, 7, '1' if str(data[6]).strip() == '1' else '')
            self.grid.SetCellValue(i, 8, data[7].strip() )
            self.grid.SetCellValue(i, 9, str(data[8]).strip() if str(data[8]).strip() != '0' else '')
            self.grid.SetCellValue(i, 10, str(data[9]).strip() if str(data[9]).strip() != '0' else '')
            self.grid.SetCellValue(i, 11, str(data[10]).strip() if str(data[10]).strip() != '0' else '')
            self.grid.SetCellValue(i, 12, str(data[11]).strip() if str(data[11]).strip() != '0' else '')
            self.grid.SetCellValue(i, 13, str('(...)'))
            self.mark_base.append({})
            
        file_r.close()
        

    #SET_XIC
    def OnClick(self, event): #WINDOW, START, STOP, FILTER, REMOVE, SCALE, ACTIVE, VIEW
        '''
        
        Apply grid entries to make XICs.
        
        '''
        # SHOULD ADD CODE TO VALIDATE SCALES i.e. MAKE SURE they reference existing traces
        self.Hide()
        #--------------------THIS SECTION READS THE GRID AND PLACES IN RESULT
        #--------------------[  [WINDOW, START, STOP, FILTER, SCALE, ACTIVE, VIEW], [...
        #--------------------ACTIVE AND VIEW CONVERTED TO INT
        result = []
        for i in range(0,150):
            window = self.grid.GetCellValue(i,0)
            if window != '':
                if not self.grid.GetCellValue(i,4): # IF REMOVE CHECKED, SKIP
                    if self.type == "SS": # IS IT START STOP?
                        result.append([self.grid.GetCellValue(i,col) for col in [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]] + [self.mark_base[i]] + [self.grid.GetCellValue(i,14)])
                    else: # IS IT CENTER WIDTH?
                        window = int(self.grid.GetCellValue(i, 0))
                        center = float(self.grid.GetCellValue(i, 1))
                        hwidth = float(self.grid.GetCellValue(i, 2))/float(2)
                        filter = self.grid.GetCellValue(i, 3)
                        scale = self.grid.GetCellValue(i, 5)
                        active = self.grid.GetCellValue(i, 6)
                        view = self.grid.GetCellValue(i, 7)
                        xtype = self.grid.GetCellValue(i, 8)
                        seq = self.grid.GetCellValue(i, 9)
                        mz = self.grid.GetCellValue(i, 10)
                        cg = self.grid.GetCellValue(i, 11)
                        scan = self.grid.GetCellValue(i, 12)
                        title = self.grid.GetCellValue(i, 14)
                        if active == '1':
                            active = 1
                        else:
                            active = 0
                        if view == '1':
                            view = 1
                        else:
                            view = 0                        
                        result.append([window, center - hwidth, center + hwidth, filter, scale, active, view, xtype, seq, mz, cg, scan, self.xic_marks[i], title])
        self.result = result
        #NEED TO RECONSTRUCT XICS
        #current["filters"] =[["Full ms "],["Full ms ","Full ms ", "Full ms "]]
        #current["xic_params"] = [[(fm, lm, u'Full ms ')], [(571.3, 572.3, u'Full ms '), (495.3, 496.3, u'Full ms '), (644, 646, u'Full ms ')]]
        
        #--------------------------THIS SECTION MAKES A DICTIONARY OF XIC PARAMS TO XIC AND XIC MAXES
        #--------------------------SO IF RETAINED, THEY ARE NOT RECALCULATED
        
        xic_storage = {}
        xic_maxes = {}
        dict_storage = {}
        xr_storage = {}
        for i, window in enumerate(self.currentFile["xic_params"]):
            for j, trace in enumerate(window):
                xic_storage[trace] = self.currentFile["xic"][i][j]
                xic_maxes[trace] = self.currentFile["xic_max"][i][j]
                dict_storage[trace] = self.currentFile["xic_dict"][i][j]
                xr_storage[trace] = self.currentFile["xr"][i][j]
        print xic_maxes
        #current["xic_mass_ranges"] = [[(fm, lm)], [(571.3, 572.3),(495.3, 496.3), (644, 646)]]
        #current["xic_scale"] = [[-1],[-1,'s0', 's0']]
        #current["active_xic"] = [0,1]        
        #current["xr"] = [[current["m"].time_range() + (fm, lm, "Full ms ")], [current["m"].time_range() + (571.3, 572.3, "Full ms "), current["m"].time_range() + (495.3, 496.3, "Full ms "), current["m"].time_range() + (644, 646, "Full ms ")]]
        #current["xic"] = [[self.GetAnXIC(self, current["m"], current["xr"][0][0])], [self.GetAnXIC(self, current["m"], current["xr"][1][0]), self.GetAnXIC(self, current["m"], current["xr"][1][1]), self.GetAnXIC(self, current["m"], current["xr"][1][2])]]
        #current["xic_max"] = [[max([x[1] for x in current["xic"][0][0]])], [max([x[1] for x in current["xic"][1][0]]), max([x[1] for x in current["xic"][1][1]]), max([x[1] for x in current["xic"][1][2]])]]
        
        #------------------------------THIS SECTION READS THROUGH ALL "TRACES" i.e. entries in grid
        #------------------------------AND GROUPS BY "WINDOW"
        #------------------------------"Windows" {0:{0:[W, Start, Stop, Filter, Scale, Active, View], 1:[etc]}}
        #------------------------------Means the first window has two "traces"
        #------------------------------NEED TO MAP TO LOWEST INTEGERS i.e. lets say 2,1,4 are entered
        #------------------------------Windows should be renumbered to 0,1,2
        #------------------------------a = windows.keys().sort() = 1,2,4
        #------------------------------range(0, a) = [0,1,2]
        
        windows = defaultdict(dict) 
        
        for member in self.result: #WINDOW START, STOP, FILTER, SCALE, ACTIVE, VIEW, XTYPE, SEQ, MZ, CG, SCAN
            window = int(member[0])
            trace = None
            if window in windows.keys():
                trace = len(windows[window].keys())
            else:
                trace = 0
                windows[window] = {}
            windows[window][trace] = member
        #----------------------------REMAPPING
        winList = windows.keys()
        winList.sort()
        #ordered_windows = range(0, winList)
        
        #----------------------------MAP OF "WINDOW" # SPECIFIED IN GRID TO REMAPPED WINDOW ASSINGMENT
        #NOT NECESSARY
        #window_map = dict(zip(winList, ordered_windows)) #{1: 0, 2: 1, 4: 2}
        
        
        #----------------------------THIS SECTION NOW BUILDS ALL XIC PARAMETERS FROM THE ASSEMBLED WINDOWS AND TRACES
        #----------------------------THEY ARE ASSIGNED TO SELF FIRST BEFORE ASSIGNING TO CURRENTFILE
        #self.xic = [None for x in self.result]
        self.xic = []
        self.xic_mass_ranges = []
        self.filters = []
        self.titles = []
        self.xic_params = []
        self.xic_axco = []
        self.xic_scale = []
        self.active_xic = [0 for x in range(0, len(windows.keys()))]
        self.xic_max = []
        self.xic_view = []
        self.xic_type = []
        self.xic_seq = []
        self.xic_mz = []
        self.xic_cg = []
        self.xic_scan = []
        self.marks = []
        self.xic_dicts = []
        self.xr = []
        #1,2,4 -- to get parameters from dictionary
        #try:
        for win_num, win in enumerate(winList):  #{0:{0:params, 1:params}}  WINDOWS
            traces = windows[win].keys()
            traces.sort()
            self.filters.append([windows[win][trace][3] for trace in traces])
            self.titles.append([windows[win][trace][13] for trace in traces])
            self.xic_mass_ranges.append([(float(windows[win][trace][1]),float(windows[win][trace][2])) for trace in traces])
            self.xic_params.append([(float(windows[win][trace][1]),float(windows[win][trace][2]), windows[win][trace][3]) for trace in traces])
            self.xic_view.append([windows[win][trace][6] for trace in traces])
            self.xic_type.append([windows[win][trace][7] for trace in traces])
            self.marks.append([windows[win][trace][12] for trace in traces])
            scales = []
            views = []
            seqs = []
            mzs = []
            cgs = []
            scans = []
            for trace in traces:
                #if windows[win][trace][6]:
                #    views.append=trace      
                if windows[win][trace][7]=='p':
                    seqs.append(windows[win][trace][8])
                    mzs.append(windows[win][trace][9])
                    cgs.append(windows[win][trace][10])
                    scans.append(windows[win][trace][11])
                else:
                    seqs.append(None)
                    mzs.append(None)
                    cgs.append(None)
                    scans.append(None)
                if windows[win][trace][5]:
                    #self.active_xic[win]=trace
                    self.active_xic[win_num]=trace #Go by enumerated win number
                cval = None
                float_it = True
                if windows[win][trace][4] == 'Auto' or str(windows[win][trace][4]).startswith("s"):
                    float_it = False
                elif windows[win][trace][4] == 'wmax' or windows[win][trace][4] == 'tmax':
                    float_it = False
                if float_it:
                    cval = int(float(windows[win][trace][4]))
                else:
                    cval = str(windows[win][trace][4])
                    if cval == 'Auto':
                        cval = -1
                scales.append(cval)
        
            self.xic_scale.append(scales)
            self.xic_seq.append(seqs)
            self.xic_mz.append(mzs)
            self.xic_cg.append(cgs)
            self.xic_scan.append(scans)
            xics = []
            maxs = []            
            xdicts = []
            xr_list = []
            for trace in traces:
                currentXIC = None
                current_params = (float(windows[win][trace][1]),float(windows[win][trace][2]), windows[win][trace][3])
                if current_params in xic_storage.keys():
                    xics.append(xic_storage[current_params])
                    maxs.append(xic_maxes[current_params])
                    xdicts.append(dict_storage[current_params])
                    xr_list.append(xr_storage[current_params])
                else:
                    if self.currentFile['vendor'] in ['Thermo', 'mgf']:
                        xr = self.currentFile["m"].time_range() + current_params
                        if windows[win][trace][7]=='x':
                            cx = self.parent.msdb.GetAnXIC(self, self.currentFile["m"], xr, self.currentFile["filter_dict"], self.currentFile['rt2scan'])
                            xr_list.append(xr)
                        else:
                            #cx = self.parent.msdb.GetAnXIC(self, self.currentFile["m"], xr)
                            cx = Peptigram.GetAPeptigram(self.currentFile, int(windows[win][trace][11]), float(windows[win][trace][9]), int(windows[win][trace][10]), tolerance=0.02)
                            xr_list.append((min(cx, key = lambda t:t[0])[0], max(cx, key = lambda t:t[0])[0]) + current_params)
                        xics.append(cx)
                        xdicts.append(self.parent.msdb.make_xic_dict(cx))
                        maxs.append(max([x[1] for x in cx]))
                    elif self.currentFile['vendor']=='ABI':
                        self.currentFile["m"].set_sample(0)
                        self.currentFile["m"].set_experiment("0")                                          
                        xr = self.currentFile["m"].time_range() + current_params
                        if windows[win][trace][7]=='x':
                            cx = self.parent.msdb.GetAnXIC(self, self.currentFile["m"], xr, self.currentFile["filter_dict"], self.currentFile['rt2scan'])
                            xr_list.append(xr)
                        else:
                            #cx = self.parent.msdb.GetAnXIC(self, self.currentFile["m"], xr)
                            cx = Peptigram.GetAPeptigram(self.currentFile, int(windows[win][trace][11]), float(windows[win][trace][9]), int(windows[win][trace][10]), tolerance=0.02)
                            xr_list.append((min(cx, key = lambda t:t[0])[0], max(cx, key = lambda t:t[0])[0]) + current_params)
                        xics.append(cx)    
                        xdicts.append(self.parent.msdb.make_xic_dict(cx))
                        maxs.append(max([x[1] for x in cx]))   
                print maxs
            self.xic.append(xics)
            self.xic_max.append(maxs)
            self.xic_dicts.append(xdicts)
            self.xr.append(xr_list)
        #except Exception as err:
            #wx.MessageBox("Error parsing parameters!\nCheck for missing\\incorrect values, \nor invalid filters.")
            #return
            try:
                self.parent.parent.StopGauge()
            except:
                pass
        
        self.currentFile['xr'] = self.xr
        self.currentFile["xic"] = self.xic
        self.currentFile["xic_params"] = self.xic_params
        self.currentFile["filters"] = self.filters
        self.currentFile["xic_mass_ranges"] = self.xic_mass_ranges
        self.currentFile["xic_scale"] = self.xic_scale
        self.currentFile['xic_max'] = self.xic_max
        self.currentFile['active_xic'] = self.active_xic
        self.currentFile['xic_view'] = self.xic_view
        self.currentFile['xic_type'] = self.xic_type
        self.currentFile['xic_sequence'] = self.xic_seq
        self.currentFile['xic_mass'] = self.xic_mz
        self.currentFile['xic_charge'] = self.xic_cg
        self.currentFile['xic_scan'] = self.xic_scan
        self.currentFile['xic_marks'] = self.marks
        self.currentFile['xic_title'] = self.titles
        #print self.xic_dicts
        self.currentFile['xic_dict'] = self.xic_dicts
        self.parent.msdb.set_axes()
        
        for i, win in enumerate(self.currentFile['xic_marks']):
            for j, trace in enumerate(win):
                for key in trace.keys():
                    if trace[key].xic==None:
                        #currentFile['xic_marks'][i][j][key].xic=self.currentFile['xic'][i][j]
                        trace[key].xic=self.currentFile['xic'][i][j]
                        trace[key].intensity=trace[key].get_nearest_intensity(trace[key].xic, trace[key].time)        
        
        #self.parent.Window.UpdateDrawing()
        self.parent.Window.UpdateDrawing()
        self.parent.Refresh()

class PyGaugeDemo(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent , -1, "Progress...", size=(150,110))
        self.mainPanel = wx.Panel(self, -1)
        self.mainPanel.SetBackgroundColour(wx.WHITE)
        self.gauge1 = PG.PyGauge(self.mainPanel, -1, size=(100,25),style=wx.GA_HORIZONTAL)
        self.gauge1.SetValue(0)
        self.gauge1.SetBackgroundColour(wx.WHITE)
        self.gauge1.SetBarColor(wx.RED)
        self.gauge1.SetBorderColor(wx.BLACK)
        self.DoLayout()

    def DoLayout(self):
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.gauge1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 20)
        self.mainPanel.SetSizer(mainSizer)
        mainSizer.Layout()
        frameSizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(frameSizer)
        frameSizer.Layout()


    def OnStartProgress(self, elapsedchoice=True, cancelchoice=True, proportion=20, steps=50):
        style = wx.PD_APP_MODAL
        if elapsedchoice:
            style |= wx.PD_ELAPSED_TIME
        if cancelchoice:
            style |= wx.PD_CAN_ABORT

        dlg = PP.PyProgress(None, -1, "PyProgress Example",
                            "An Informative Message",
                            agwStyle=style)

        backcol = wx.WHITE
        firstcol = wx.WHITE
        secondcol = wx.BLUE

        dlg.SetGaugeProportion(proportion/100.0)
        dlg.SetGaugeSteps(steps)
        dlg.SetGaugeBackground(backcol)
        dlg.SetFirstGradientColour(firstcol)
        dlg.SetSecondGradientColour(secondcol)
        max = 400
        keepGoing = True
        count = 0
        while keepGoing and count < max:
            count += 1
            wx.MilliSleep(30)
            if count >= max / 2:
                keepGoing = dlg.UpdatePulse("Half-time!")
            else:
                keepGoing = dlg.UpdatePulse()
        dlg.Destroy()
        wx.SafeYield()
        wx.GetApp().GetTopWindow().Raise()
        
class TestPopup(wx.PopupWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""
    def __init__(self, parent, style, text, pos):
        wx.PopupWindow.__init__(self, parent, style)
        pnl = self.pnl = wx.Panel(self)
        pnl.SetBackgroundColour("AQUAMARINE")
        self.parent = parent
        self.pos = pos
        st = wx.StaticText(pnl, -1,text, pos=(10,10))

        sz = st.GetBestSize()
        self.SetSize( (sz.width+10, sz.height+10) )
        pnl.SetSize( (sz.width+10, sz.height+10) )

        pnl.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        pnl.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        pnl.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        pnl.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        st.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        st.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        st.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        st.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        wx.CallAfter(self.Refresh)
        

    def OnMouseLeftDown(self, evt):
        self.Refresh()
        self.ldPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.wPos = self.ClientToScreen((0,0))
        self.pnl.CaptureMouse()
        evt.Skip()

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            dPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            nPos = (self.wPos.x + (dPos.x - self.ldPos.x),
                   self.wPos.y + (dPos.y - self.ldPos.y))
            self.Move(nPos)
        #pos = evt.GetPositionTuple()
        #member = self.pos
        #x1 = member[0]-10
        #x2 = member[0]
        #y1 = member[1] - 10
        #y2 = member[1]
        #if pos[0] > x1 and pos[0] <x2 and pos[1] > y1 and pos[1] < y2:   
        #    pass
        #else:
        #    self.Show(False)
        #    self.Destroy()            

    def OnMouseLeftUp(self, evt):
        if self.pnl.HasCapture():
            self.pnl.ReleaseMouse()

    def OnRightUp(self, evt):
        #Go to scan with MS2
        currentFile = self.parent.parent.msdb.files[self.parent.parent.msdb.Display_ID[self.parent.parent.msdb.active_file]]
        scan = int(self.pos[2].scan) 
        currentFile['scanNum']=scan
        self.parent.parent.msdb.set_scan(currentFile["scanNum"], self.parent.parent.msdb.active_file)
        if currentFile['vendor']=='Thermo':
            self.parent.parent.msdb.build_current_ID(self.parent.parent.msdb.Display_ID[self.parent.parent.msdb.active_file], currentFile["scanNum"])        
        #self.Show(False)
        #self.Destroy()
        self.parent.parent.Window.UpdateDrawing() 
        self.parent.parent.Refresh()        
        
class TopLevelFrame(wx.Frame):

    def __init__(self, parent, id=-1, title="mzStudio (version 0.9.9, 2017-07-06, build 1)", pos=wx.DefaultPosition,
                 size=(1200, 600), style=wx.DEFAULT_FRAME_STYLE):

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self.parent = parent

        self._mgr = aui.AuiManager()
        self.SetMinSize((1200,600))
        self.knownSize = None

        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)
        client_size = self.GetClientSize()
        self.parentFrame = ParentFrame(self)
        self.ctrl = self.parentFrame.notebook

        self.page_bmp = wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, wx.Size(16, 16))

        # add the panes to the manager
        self._mgr.AddPane(self.ctrl, aui.AuiPaneInfo().CenterPane().Caption("BlaisBrowser"))
        #self._mgr.Bind(wx.lib.agw.aui.EVT_AUI_PANE_CLOSE, self.OnPageClose)
        #self._mgr.Bind(wx.lib.agw.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnPageClose)
        #self._mgr.Bind(wx.lib.agw.aui.EVT_AUI, self.OnPageClose)
        #self.ctrl.Bind(wx.lib.agw.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.OnClose)
        #---------------CREATE MAIN FRAME TOOLBAR, STATUS BAR
        self.tb = self.CreateToolBar( TBFLAGS )
        #self.tb = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_FLAT | wx.TB_NODIVIDER)
        self.SetToolBar(self.tb)
        self.statusbar = self.CreateStatusBar()
        #self._mgr.AddPane(self.tb, aui.AuiPaneInfo().Name("tb1").Caption("Sample Bookmark Toolbar").ToolbarPane().Top().Row(1).LeftDockable(False).RightDockable(False))  
        
        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        #---------------BIND EVENTS
        #self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.Bind(aui.EVT_AUI_PANE_DOCKED, self.OnSash)
        self.Bind(aui.EVT_AUI_PERSPECTIVE_CHANGED, self.OnPersp)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChange)

        
        
        self.timer = wx.Timer(self)
        
        mb = self.MakeMenuBar(full=False)
        self.SetMenuBar(mb)     
        self.area_tb = None
        
        self.custom_spectrum_process = None
        self.custom_spectrum_process_file = ''
        
    def OnPageClose(self, event):
        print "close page"
        event.Skip()

    def MakeMenuBar(self, full=True):
        if not full:
            mb = wx.MenuBar()
            menu = wx.Menu()
            item = menu.Append(-1, "Open MS Data File (New Tab)\tCtrl-N")
            self.Bind(wx.EVT_MENU, self.OnNewChild, item)
            item = menu.Append(-1, "Open D Data File (New Tab)")
            self.Bind(wx.EVT_MENU, self.onDFileBrowse, item)            
            #item = menu.Append(-1, "Close All Windows")
            #self.Bind(wx.EVT_MENU, self.OnDoClose, item)
            item = menu.Append(-1, "Quit")
            self.Bind(wx.EVT_MENU, self.OnClose_smaller, item)
            _Test = False # This bit could be taken out altogether, aside from development stuff.
            if _Test:
                item = menu.Append(-1, "....Test")
                self.Bind(wx.EVT_MENU, self.OnTest, item)
            mb.Append(menu, "&File")
            return mb    
        else:
            mb = wx.MenuBar()
            menu = wx.Menu()
            item = menu.Append(-1, "Open MS Data File (New Tab)\tCtrl-N")
            self.Bind(wx.EVT_MENU, self.OnNewChild, item)
            item = menu.Append(-1, "Open D Data File (New Tab)")
            self.Bind(wx.EVT_MENU, self.onDFileBrowse, item)
            #item = menu.Append(-1, "Close All Windows")
            #self.Bind(wx.EVT_MENU, self.OnDoClose, item)
            item = menu.Append(-1, "Quit")         
            self.Bind(wx.EVT_MENU, self.OnClose_smaller, item)
            mb.Append(menu, "&File")            
            for eachMenuData in self.menuData():
                menuLabel = eachMenuData[0]
                menuItems = eachMenuData[1]
                mb.Append(self.createMenu(menuItems), menuLabel)
            return mb
    
    def OnTest(self, evt):
        
        sb = SpecBase_aui3.SpecFrame(self, id=-1)
        self._mgr.AddPane(sb, aui.AuiPaneInfo().Name("SpecNote").MaximizeButton(True).MinimizeButton(True).
                                      Caption("SpecStylus").Right().
                                      MinSize(wx.Size(50, 210)))
                    
        self._mgr.Update()
        #self.ObjectOrganizer.addObject(sb, "SpecBase") 
        
    #def CreateMinibar(self, parent):
        ## create mini toolbar
        #self._mtb = FM.FlatMenuBar(parent, wx.ID_ANY, 16, 6, options = FM_OPT_SHOW_TOOLBAR|FM_OPT_MINIBAR)

        #checkCancelBmp = wx.Bitmap(os.path.join(bitmapDir, "ok-16.png"), wx.BITMAP_TYPE_PNG)
        #viewMagBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-16.png"), wx.BITMAP_TYPE_PNG)
        #viewMagFitBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmagfit-16.png"), wx.BITMAP_TYPE_PNG)
        #viewMagZoomBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-p-16.png"), wx.BITMAP_TYPE_PNG)
        #viewMagZoomOutBmp = wx.Bitmap(os.path.join(bitmapDir, "viewmag-m-16.png"), wx.BITMAP_TYPE_PNG)

        #self._mtb.AddCheckTool(wx.ID_ANY, "Check Settings Item", checkCancelBmp)
        #self._mtb.AddCheckTool(wx.ID_ANY, "Check Info Item", checkCancelBmp)
        #self._mtb.AddSeparator()
        #self._mtb.AddRadioTool(wx.ID_ANY, "Magnifier", viewMagBmp)
        #self._mtb.AddRadioTool(wx.ID_ANY, "Fit", viewMagFitBmp)
        #self._mtb.AddRadioTool(wx.ID_ANY, "Zoom In", viewMagZoomBmp)
        #self._mtb.AddRadioTool(wx.ID_ANY, "Zoom Out", viewMagZoomOutBmp)    
    
    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachItem in menuData:
            if len(eachItem) == 2:
                label = eachItem[0]
                subMenu = self.createMenu(eachItem[1])
                menu.AppendMenu(wx.NewId(), label, subMenu)
            else:
                self.createMenuItem(menu, *eachItem)
        return menu        

    def createMenuItem(self, menu, label, status, handler, kind = wx.ITEM_NORMAL):
        if not label:
            menu.AppendSeparator()
            return
        menuItem = menu.Append(-1, label, status, kind)
        self.Bind(wx.EVT_MENU, handler, menuItem)

    def OnClose(self, evt):
        evt.Skip()
    
    def OnSaveImage(self, evt): 
        curpage = self.ctrl.GetSelection()
        if curpage != -1:
            self.ctrl.GetPage(curpage).OnSaveImage(evt)
        
    def OnSaveSVG(self, evt):
        curpage = self.ctrl.GetSelection()
        if curpage != -1:        
            self.ctrl.GetPage(curpage).OnSaveSVG(evt)
        
    def OnSavePDF(self, evt):
        curpage = self.ctrl.GetSelection()
        if curpage != -1:        
            self.ctrl.GetPage(curpage).OnSavePDF(evt)
        
    def OnView(self, evt): pass    
    def OnSaveAnalysis(self, evt): pass
    def OnLoadAnalysis(self, evt): pass
    
    def OnOpenSpecBase(self, evt):
        curpage = self.ctrl.GetSelection()
        if curpage != -1:   
            self.ctrl.GetPage(curpage).OnOpenSpecBase(None)
    def OnSendToSpecBase(self, evt): self.ctrl.GetPage(self.ctrl.GetSelection()).OnSendToSpecBase(None)
    def OnSendXICToSpecBase(self, evt): self.ctrl.GetPage(self.ctrl.GetSelection()).OnSendXICToSpecBase(None)
    
    def PropagateXICsInWindow(self, event): self.ctrl.GetPage(self.ctrl.GetSelection()).PropagateXICsInWindow(None)
    def PropagateXICsAllWindows(self, event): self.ctrl.GetPage(self.ctrl.GetSelection()).PropagateXICsAllWindows(None)
    def XICReport(self, event): self.ctrl.GetPage(self.ctrl.GetSelection()).XICReport(None)
    def OnBuildMALDIBase(self, event): pass    
    
    def OnSendAnalysisToSpecBase(self, evt): pass
    def OnChangeSettings(self, evt): self.ctrl.GetPage(self.ctrl.GetSelection()).OnChangeSettings(None) 
    def OnSeqTest(self, evt): pass

    def OnSetProcessor(self, event):
        prodog = ProcessorDialog(self, self.custom_spectrum_process_file)
        if prodog.ShowModal() == wx.ID_OK and prodog.success:
            self.custom_spectrum_process = prodog.function
            self.custom_spectrum_process_file = prodog.filename
        prodog.Destroy()
        
    def shortMenuData(self):
        return [
            ("SpecStylus", (
                        ("&Open SpecStylus", "Open SpecStylus", self.OnOpenSpecBase),
                        ("&Send to SpecStylus", "Send to SpecStylus", self.OnSendToSpecBase),
                        #("&Build MALDI Base", "Build MALDI-base", self.OnBuildMALDIBase), # Function is "pass".
                        ("&Send XIC to SpecStylus", "Send XIC to SpecStylus", self.OnSendXICToSpecBase),
                        #("&Send Analysis to SpecBase", "Send analysis to SpecBase", self.OnSendAnalysisToSpecBase), # Function is "pass".
                             ))        
        
        ]

    def menuData(self):
        return [
            #("&Current Window", (
            #("&Open MS Data File (New Tab)\tCtrl-N", "Open MS Data File (New Tab)", self.OnOpen),
            #("&Close All Windows", "Close All Windows", self.OnDoClose),
            #("&Quit", "Quit", self.OnClose))),
                 ("Image", (
            ("Save &PNG", "Save PNG", self.OnSaveImage),
            ("Save &SVG", "Save SVG", self.OnSaveSVG),
            ("Save &PDF", "Save PDF", self.OnSavePDF))),
                #("Link", (
            #("&Link to mz sheet", "Link to mz sheet", self.OnLink),
            #("&Link to dat file", "Link to dat file", self.OnDat),
            #("&View mz sheet", "View mz sheet", self.OnView))),
                ("XIC", (
            ("&XIC", "XIC", self.OnXIC),
            #("Generate XIC Report", "Generate XIC Report", self.XICReport),
            #("&Propagate XICs within Window", "Propagate in Window", self.PropagateXICsInWindow),
            ("Propagate XICs", "Propagate XICs all Windows", self.PropagateXICsAllWindows))),
                #("Analysis", (
            #("&Save Analysis", "Save Analysis", self.OnSaveAnalysis),
            #("&Load Analysis", "Save Analysis", self.OnLoadAnalysis))),
                ("SpecStylus", (
            ("&Open SpecStylus", "Open SpecStylus", self.OnOpenSpecBase),
            ("&Send to SpecStylus", "Send to SpecStylus", self.OnSendToSpecBase),
            #("&Build MALDI Base", "Build MALDI-base", self.OnBuildMALDIBase), # Function is "pass".
            ("&Send XIC to SpecStylus", "Send XIC to SpecStylus", self.OnSendXICToSpecBase),
            #("&Send Analysis to SpecBase", "Send analysis to SpecBase", self.OnSendAnalysisToSpecBase), # Function is "pass".
                 )),
                ("Settings", (
            ("&Change Settings", 'Change Settings', self.OnChangeSettings),
            ("&Set Spectral Processor", 'Set Spectral Processor', self.OnSetProcessor))),
                #("Development", (
            #("&Label Test", 'Label Test', self.OnSeqTest),)) ,
                ("Tools", (
            ("&miniCHNOPS", 'miniCHOPS', self.OnMiniCHNOPS),
            ("&areaBank", 'areaBank', self.OnAreaBox),
            ("&Mass Accuracy Calculator", 'Mass Accuracy Calculator', self.OnMassAcc),)),
                ("Features", (
            ("Make Feature File", 'Derives Features from Rawfiles', self.OnMakeFeatureFile),
            ("Toggle Feature Detection", 'Toggle Feature Detection', self.OnToggleFeatureDetection),
            ("Import Feature File", 'Import Feature File', self.OnImportFeatureFile),))            
        ]    

    def OnImportFeatureFile(self, event):
        currentPage = self.ctrl.GetPage(self.ctrl.GetSelection())
        current = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]           

        if 'xlsSource' in current:
            psmfile = current['xlsSource']
        else:
            psmfile = mzGUI.file_chooser("Select feature-annotated multiplierz report...", wildcard="XLSX|*.xlsx|XLS|*.xls|Other|*")
            if not psmfile:
                return
            current['xlsSource'] = psmfile
            
        featureFile = mzGUI.file_chooser("Import Feature File...", wildcard="Feature files (*.features)|*.features|Other|*.*")   #wildcard="featurePickle files (*.featurePickle)|*.featurePickle"
        if not featureFile:
            print "No feature file, returning."
            return
        
        print "LOADING FEATURES."

        datafile = current['FileAbs']
        data = mzAPI.mzFile(datafile, compatible_mode = True)
        
        #current["scanToF"], current["scanFToPeaks"], current["featureToPSMs"] = FeatureImport.import_features(featureFile)
        featureDB = featureUtilities.FeatureInterface(featureFile)
        featureData = featureDB.mz_range(1, 9999999)
        try:
            (scanToF, scanFToPeaks,
             featureToMS1s) = featureUtilities.getScanFeatureDicts(data,
                                                                   featureData,
                                                                   absScanFeatures = True)
            
            featureToPSMs = featureUtilities.featureToPSM(current['xlsSource'], featureData)
        except IOError as err:
            wx.MessageBox('Error loading file: %s' % err)
            return

        
        current["scanToF"] = scanToF
        current["scanFToPeaks"] = scanFToPeaks
        current["featureToPSMs"] = featureToPSMs
        current["featureByIndex"] = dict(featureData)
        
        current["scansWithFeatures"]=current["scanToF"].keys()
        current["scansWithFeatures"].sort()
        
        current['features'] = True
        print "IMPORTED!"        
    
    def OnMakeFeatureFile(self, event):
        rawFile = mzGUI.file_chooser("Make Feature File (select rawfile)...", wildcard="raw files|*.raw|Other|*")
        if rawFile:
            xlsFile = mzGUI.file_chooser("Make Feature File (select multiplierz report)...", wildcard="XLSX|*.xlsx|XLS|*.xls|Other|*")
        else:
            xlsFile = None
        if not (rawFile and xlsFile):
            return
        #featureFile = mzGUI.file_chooser("Make Feature File (select feature file)...", wildcard="featurePickle files (*.featurePickle)|*.featurePickle")
        featureFile = rawFile + '.features'
        featureDetector.feature_analysis(rawFile, [xlsFile])
        
        print "Done."
        
    def OnToggleFeatureDetection(self, event):
        currentPage = self.ctrl.GetPage(self.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]
        currentFile["features"] = not currentFile["features"]      
        

    def OnMassAcc(self, event):
        self.tb5 = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        self.tb5.measured = wx.TextCtrl(self.tb5, -1, 'Measured') #,size = (150,20)
        self.tb5.AddControl(self.tb5.measured)
        self.tb5.calculated = wx.TextCtrl(self.tb5, -1, 'Calc')#,, size = (150,20)
        self.tb5.AddControl(self.tb5.calculated)
        self.tb5.calcButton = wx.Button(self.tb5, -1, "Calc")#,, size=(50,20)
        self.tb5.Bind(wx.EVT_BUTTON, self.OnMassAccCalc, self.tb5.calcButton)  
        self.tb5.AddControl(self.tb5.calcButton)
        self.tb5.result = wx.TextCtrl(self.tb5, -1, '0.0')#,, size = (150,20)
        self.tb5.AddControl(self.tb5.result)        
        self.tb5.Realize()  
               
        self._mgr.AddPane(self.tb5, aui.AuiPaneInfo().Name("tb5").Caption("Mass Accuracy Calculator").ToolbarPane().Top().Row(2).LeftDockable(False).RightDockable(False))  
        self._mgr.Update()        

    def OnMassAccCalc(self, event):
        self.tb5.result.SetValue(str((abs(float(self.tb5.measured.GetValue())-float(self.tb5.calculated.GetValue()))/float(self.tb5.calculated.GetValue()))*10**6))
    
    
    def OnClickCalc(self, event):
        chnopsvalues = self.tb4.pa.findall(self.tb4.chnopsData.GetValue())
        chnopsvalues = [(el, int(c) if c else 1) for el, c in chnopsvalues]
        masstype = 'mi' if self.tb4.choice.GetStringSelection() == "Monoisotopic" else 'av'
        mass = mz_masses.calc_mass(dict([(x, int(y)) for (x, y) in chnopsvalues]),
                                   masstype)
        self.tb4.result.SetValue(str(mass))
           
    def OnClickClear(self, event):
        self.area_tb.areaBox.SetValue('')
    
    def OnClickCopy(self, event):
        data = wx.TextDataObject()
        data.SetText(self.area_tb.areaBox.GetValue())
        if wx.TheClipboard.Open():
            yo = wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()             
        
    def OnMiniCHNOPS(self, evt):
        #c = miniCHNOPS.miniCHNOPS(self.tb, -1) #THIS CODE ADDS TO MAIN TOOLBAR
        #self.tb4 = wx.ToolBar(self, -1, wx.DefaultPosition, (300,50), wx.TB_FLAT | wx.TB_NODIVIDER | wx.TB_HORZ_TEXT)
        self.tb4 = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        self.tb4.chnopsData = wx.TextCtrl(self.tb4, -1, '') #,size = (150,20)
        self.tb4.AddControl(self.tb4.chnopsData)
        self.tb4.result = wx.TextCtrl(self.tb4, -1, '')#,, size = (150,20)
        self.tb4.AddControl(self.tb4.result)
        self.tb4.calcButton = wx.Button(self.tb4, -1, "Calc")#,, size=(50,20)
        self.tb4.Bind(wx.EVT_BUTTON, self.OnClickCalc, self.tb4.calcButton)  
        self.tb4.AddControl(self.tb4.calcButton)
        #self.tb4.pa = re.compile('([A-Z]+[a-z+]*)[ ]*\(*([0-9]+)\)*')
        self.tb4.pa = re.compile('([A-Z][a-z]*)([0-9]*)(?=$|[A-Za-z])*')
        self.tb4.choice = wx.Choice(self.tb4, -1, choices=["Monoisotopic", "Average"])
        self.tb4.choice.SetStringSelection("Monoisotopic")
        self.tb4.AddControl(self.tb4.choice)        
            
        self.tb4.Realize()  
        self._mgr.AddPane(self.tb4, aui.AuiPaneInfo().Name("tb4").Caption("MiniCHNOPS").ToolbarPane().Top().Row(2).LeftDockable(False).RightDockable(False))  
        self._mgr.Update()

    def OnAreaBox(self, evt):
        self.area_tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        self.area_tb.areaBox = wx.TextCtrl(self.area_tb, -1, '') #,size = (150,20)
        self.area_tb.AddControl(self.area_tb.areaBox)
        
        self.area_tb.copyButton = wx.Button(self.area_tb, -1, "Copy")#,, size=(50,20)
        self.area_tb.Bind(wx.EVT_BUTTON, self.OnClickCopy, self.area_tb.copyButton)  
        self.area_tb.AddControl(self.area_tb.copyButton)
        
        self.area_tb.clearButton = wx.Button(self.area_tb, -1, "Clear")
        self.area_tb.Bind(wx.EVT_BUTTON, self.OnClickClear, self.area_tb.clearButton)  
        self.area_tb.AddControl(self.area_tb.clearButton)        
        
        self.area_tb.Realize()  
        self._mgr.AddPane(self.area_tb, aui.AuiPaneInfo().Name("area_tb").Caption("AreaBank").ToolbarPane().Top().Row(2).LeftDockable(False).RightDockable(False))  
        self._mgr.Update()
        
     

    def OnDoClose(self, evt):
        # NEED TO UPDATE FOR AUI
        # Close all ChildFrames first else Python crashes
        #for m in self.GetChildren():
            #if isinstance(m, wx.lib.agw.aui.AuiMDIClientWindow):
                #for k in m.GetChildren():
                    #if isinstance(k, DrawPanel):
                        #k.Close()  
        for window in self.ctrl.GetChildren():
            if isinstance(window, DrawPanel):
                paneinfo = self._mgr.GetPaneByWidget(window)
                self._mgr.ClosePane(paneinfo)
                window.OnClose(evt)
                #window.Destroy()
        evt.Skip()
    

    def OnPageChange(self, evt):
        self.ctrl.GetPage(self.ctrl.GetSelection()).msdb.set_axes()
        self.ctrl.GetPage(self.ctrl.GetSelection()).Window.UpdateDrawing()
        self.ctrl.GetPage(self.ctrl.GetSelection()).Window.Refresh()
        evt.Skip()

    def OnPersp(self, evt):
        if self.ctrl.GetPageCount() > 0:
            sel = self.ctrl.GetSelection()
            if sel >= self.ctrl.GetPageCount():
                sel = self.ctrl.GetPageCount()-1
            
            self.ctrl.GetPage(sel).msdb.set_axes()
            self.ctrl.GetPage(sel).Window.UpdateDrawing()
            self.ctrl.GetPage(sel).Window.Refresh()
        evt.Skip()

    def OnSash(self, evt):
        if self.ctrl.GetPageCount() > 0:
            self.ctrl.GetPage(self.ctrl.GetSelection()).msdb.set_axes()
            self.ctrl.GetPage(self.ctrl.GetSelection()).Window.UpdateDrawing()
            self.ctrl.GetPage(self.ctrl.GetSelection()).Window.Refresh()
        evt.Skip()

    def OnSize(self, evt):
        print self.GetClientSize(), evt.Size, self.knownSize
        newsize = evt.Size
        if self.knownSize and (abs(self.knownSize[0] - newsize[0]) < 3 and
                               abs(self.knownSize[1] - newsize[1]) < 3):
            print "SKIPPING RESIZE."
            evt.Skip()
            return
        else:
            self.knownSize = newsize
            print "RESIZING!"
            print self.GetClientSize(), evt.Size
            if self.ctrl.GetPageCount() > 0:
                self.ctrl.GetPage(self.ctrl.GetSelection()).msdb.set_axes()
                self.ctrl.GetPage(self.ctrl.GetSelection()).Window.UpdateDrawing()
            #self.ctrl.GetPage(self.ctrl.GetSelection()).Window.Refresh()
            self.Refresh()
            evt.Skip()

    def SetupAdjustableGauge(self, text ="Processing...", color=wx.GREEN):
        self.adj_gauge = AdjProg.PyGaugeDemoW(self.tb, size=(155, 15), pos=(500,5), color=color, parent=self)
        self.adjtxt1 = wx.StaticText(self.tb, -1, text, size=(100, 25), pos=(700,5))         
        self.adjtxt1.SetFont(wx.Font(14, wx.ROMAN, wx.NORMAL, wx.BOLD))
    
    def HideAdjGauge(self):
        self.adj_gauge.Destroy()
        self.adjtxt1.Destroy()    

    def StartGauge(self, text ="Processing...", color=wx.GREEN):
        self.busy_gauge = pg.ProgressGauge(self.tb, size=(155, 15), pos=(500,5), color=color)
        self.timer.Start(100)
        self.txt1 = wx.StaticText(self.tb, -1, text, size=(100, 25), pos=(700,5)) 
        
    def StopGauge(self):
        self.timer.Stop()
        self.busy_gauge.Destroy()
        self.txt1.Destroy()

    def OnToolRClick(self, event):
        pass

    def OnToolClick(self, event):
        '''
        
        
        Handle events for clicking main toolbar.
        
        
        '''
        if event.GetId() == 10:
            self.OnNewChild(None)
            return
        if event.GetId() == 20:
            self.OnClose(event)
            return
        if event.GetId() == 40:
            self.OnLoadAnalysis(None)
            return
        if event.GetId() == 50:
            self.OnDat(None)
            return
        if event.GetId() == 70:
            fr = findFrame(self)
            self._mgr.AddPane(fr, aui.AuiPaneInfo().Left().Caption("Locate MS2"))
            self._mgr.Update()            
            return
        if event.GetId() == 80:
            self.OnXIC(None)
            return
        if event.GetId() == 90:
            #currentpanes = self._mgr.GetAllPanes()
            #if not any(['BlaisPepCalc' in x.name for x in currentpanes]):
                #b = BlaisPepCalc2.MainBPC(self, id=-1)
            if not self.parentFrame.ObjectOrganizer.containsType(BlaisPepCalcSlim_aui2.MainBPC):
                #b = BlaisPepCalcSlim_aui2.BlaisPepCalc(self, -1, self.ctrl.ObjectOrganizer)
                #MainBPC
                b = BlaisPepCalcSlim_aui2.MainBPC(self, -1, self.parentFrame.ObjectOrganizer)
                self._mgr.AddPane(b, aui.AuiPaneInfo().Left().Caption("PepCalc"))
                self._mgr.Update()
                b.aui_pane = self._mgr.GetPaneByWidget(b)
                
                # THIS is how to properly catch the pane close event.
                # _mgr can't be the third argument in a Bind call, but it can
                # do the binding for some reason, which has the same effect.
                self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, b.OnClose)
            
            return
        
        selection = self.ctrl.GetSelection()
        if selection == -1:
            wx.MessageBox("Open an MS data file first.", "An error occurred.")
            return
        
        if event.GetId() == 100:
            #self.OnJump(None)
            self.ctrl.GetPage(selection).OnJump(None)
        if event.GetId() == 110:
            self.OnMakeDb(None)
        if event.GetId() == 120:
            self.ctrl.GetPage(selection).On_XIC_range(None)
            #self.On_XIC_range(None)
        if event.GetId() == 130:
            self.ctrl.GetPage(selection).On_mz_range(None)
            #self.On_mz_range(None)
        if event.GetId() == 140:
            self.ctrl.GetPage(selection).On_inten_range(None)
            #self.On_inten_range(None)   
        if event.GetId() == 150:
            self.ctrl.GetPage(selection).OnXICAddTraceStyle(None)
            #self.OnXICAddTraceStyle(event)     
        if event.GetId() == 160:
            self.ctrl.GetPage(selection).On_Text_Spectrum()
        if event.GetId() == 170:
            self.ctrl.GetPage(selection).On_Search_Spectrum()
        if event.GetId() == 180:
            self.ctrl.GetPage(selection).On_Set_Ion_Label_Tolerance(None)        
            
    def OnMakeDb(self, event):
        #-----------------------------------
        # Reads database search result file
        #-----------------------------------
        
        if self.parentFrame.ObjectOrganizer.containsType(dbFrame.dbFrame):
            wx.MessageBox('A search result file is already open.')
            return
        
        import check_search_type
        mgf_dict = {}
        
        currentPage = self.ctrl.GetPage(self.ctrl.GetSelection())
        currentFile = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]        
        
        xlsfile = mzGUI.file_chooser('Select search result file...', wildcard='xls files (*.xls,*.xlsx;*.txt)|*.xls;*.xlsx;*.txt')
        if not xlsfile:
            print "No file specified; returning."
            return
        if xlsfile.find(".xls") == -1: # Load proteome discoverer
            if currentFile['FileAbs'].endswith('.wiff'):
                mgfFile = mzGUI.file_chooser('Select corresponding mgf file...', wildcard='mgf files (*.mgf)|*.mgf')
                from multiplierz.mgf import parse_to_generator
                mgf_dict = dict([(i, x['title']) for i, x in enumerate(parse_to_generator(mgfFile))])
        
        dir = os.path.dirname(xlsfile)
        
        currentFile["xlsSource"]=xlsfile
        
        currentFile['SearchType'] = check_search_type.perform_check(xlsfile)        
        
        #------------------------------------
        # Look for database file.  If present, load it.  If not, make it.
        #------------------------------------
        if not os.path.exists(xlsfile[:-4] + '.db'):         
            dbase = self.ctrl.GetPage(self.ctrl.GetSelection()).MakeDatabase(xlsfile, currentFile['SearchType'], mgf_dict=mgf_dict)
        else:
            dbase = xlsfile[:-4] + '.db'
        
        #-------------------------------------
        
        
        
        import sqlite3    
        con = sqlite3.connect(dbase)
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")      
        tables = [x[0] for x in cursor.fetchall()]
            
        currentFile["database"] = dbase
        
        #if currentFile["SearchType"] == "Mascot":
        currentFile["rows"], currentFile["mzSheetcols"] = db.pull_data_dict(dbase, 'select * from "peptides"')
                
        for row in currentFile['rows']:
            if currentFile["SearchType"] in ['Mascot', 'X!Tandem', 'COMET']:
                if currentFile['vendor']=='Thermo':
                    #if currentFile["SearchType"] == "Mascot":
                    if 'MultiplierzMGF' in row['Spectrum Description']:
                        row['scan'] = int(standard_title_parse(row['Spectrum Description'])['scan'])
                        #else:
                        #    row['scan']=int(row['Spectrum Description'].split(".")[1])
                    
                elif currentFile['vendor']=='ABI':
                    row['scan']=int(row['Spectrum Description'].split(".")[3])-1
                    try:
                        row['experiment']=int(row['Spectrum Description'].split(".")[4])-1 #Locus:1.1.1.1903.2 File:"20061229_EGFR_iTRAQ_IP.wiff"
                    except:
                        #print row['Spectrum Description']
                        row['experiment']=int(row['Spectrum Description'].split(".")[4].split(" ")[0])-1
            else:
                if currentFile['FileAbs'].endswith(".wiff"):
                    query=int(row['First Scan'])
                    row['Spectrum Description']=mgf_dict[int(query)]
                    row['scan']=int(standard_title_parse(mgf_dict[int(query)])['scan'])
                if currentFile['FileAbs'].endswith(".raw"):
                    row['scan'] = int(row['First Scan'])
                    row['Spectrum Description']='NA'
                
                #Proteome discoverer - get spectrum description and scan from MGF
                
        #try:            
        if currentFile["SearchType"] == "Mascot":
            currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["header"] = mz_core.pull_mods_from_mascot_header(xlsfile)
            if "Quantitation method" in currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["header"].keys():
                print "Quant method detected!"
                currentFile["SILAC"]["mode"]=True
                currentFile["SILAC"]["method"]=currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["header"]["Quantitation method"]
                print currentFile["SILAC"]["method"]            
            currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["fixedmod"] = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["header"]["Fixed modifications"]
        if currentFile["SearchType"] == "COMET":
            # -------------------------------------------- PARSE FIXED MODS FROM COMET HEADER
            h = currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["header"] = mz_core.pull_mods_from_comet_header(xlsfile)        
            aamods = ['add_A_alanine','add_C_cysteine','add_D_aspartic_acid','add_E_glutamic_acid','add_F_phenylalanine','add_G_glycine','add_H_histidine','add_I_isoleucine','add_K_lysine','add_L_leucine','add_M_methionine','add_N_asparagine','add_P_proline','add_Q_glutamine','add_R_arginine','add_S_serine','add_T_threonine','add_V_valine','add_W_tryptophan','add_Y_tyrosine'] #'add_Cterm_peptide','add_Cterm_protein', 'add_Nterm_peptide','add_Nterm_protein'
            currentPage.msdb.files[currentPage.msdb.Display_ID[currentPage.msdb.active_file]]["fixedmod"] =  dict((x, '[' + str(y) + ']') for x, y in [(x[4], y) for x, y in zip(h.keys(), h.values()) if x in aamods and y > 0])
           
            #[u'add_C_cysteine:57.022']

        #-------------------------------The ID dict is a dictionary of scan number to the associated ID.
        currentFile["ID_Dict"]= currentPage.build_ID_dict(currentFile["rows"], currentFile["mzSheetcols"], currentFile["Filename"], currentFile["vendor"])
        self.Refresh()
        #b = BlaisPepCalc2.MainBPC(self, wx.NewId())
        addTheFrame = True
        if not self.parentFrame.ObjectOrganizer.containsType(BlaisPepCalcSlim_aui2.MainBPC):
            b = BlaisPepCalcSlim_aui2.MainBPC(self, -1, self.parentFrame.ObjectOrganizer)
        else:
            b = self.parentFrame.ObjectOrganizer.getObjectOfType(BlaisPepCalcSlim_aui2.MainBPC)
            addTheFrame=False

            
            
        dbf = dbFrame.dbFrame(self, wx.NewId(), b)

        self.parentFrame.ObjectOrganizer.addObject(dbf)
            
        self._mgr.AddPane(dbf, aui.AuiPaneInfo().Bottom().MaximizeButton(True).MinimizeButton(True).Caption("mzResult: " + xlsfile))
        #self._mgr.Update()         
        
        if addTheFrame: self._mgr.AddPane(b, aui.AuiPaneInfo().Left().MaximizeButton(True).MinimizeButton(True).Caption("mzPepCalc"))
        self._mgr.Update()
        
        dbf.aui_pane = self._mgr.GetPane(dbf)
        
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, dbf.OnClose)
            
        #except:
            #del busy
            #dlg = wx.MessageDialog(self, 'Error!  Does xls have header?', 'Alert', wx.OK | wx.ICON_INFORMATION)
            #dlg.ShowModal()
            #dlg.Destroy()
            
    def OnJump(self, event):
        try:
            self.ctrl.GetPage(self.ctrl.GetSelection()).OnJump(None)
        except ValueError:
            print "No open page."    
            
    def OnXIC(self,event):
        try:
            self.ctrl.GetPage(self.ctrl.GetSelection()).OnXIC(None)
        except ValueError:
            print "No open page."
    
    def OnClose_smaller(self, event):
        # deinitialize the frame manager
        self._mgr.UnInit()

        self.Destroy()
        event.Skip()

    def OnOpen(self, event):
        self.ctrl.GetPage(self.ctrl.GetSelection()).OnOpen(None)

    def OnNewChild(self, evt, file_given = None):
        if file_given:
            rawfile = file_given
        else:
            rawfile = mzGUI.file_chooser('Choose Data File(s)',
                                         wildcard='MS files (*.raw,*.wiff, *.t2d, *.mgf, *.D)|*.raw;*.wiff;*.t2d;*.mgf|Any|*')
        if not rawfile:
            return
        
        dir = os.path.dirname(rawfile)
        
        #-------------CREATE A NEW DRAWPANEL, ADD THE NEW PANEL TO A NEW AUINOTEBOOK PAGE
        child = DrawPanel(self.parentFrame, rawfile, 1)        
        self.ctrl.AddPage(child, os.path.basename(rawfile), False)#, self.page_bmp)
        self.ctrl.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, child.OnClose, self.ctrl)
        

    def onDFileBrowse(self, evt):
        dfile = mzGUI.directory_chooser(self, 'Select D File Directory')
        if not dfile:
            return
        if not dfile.split('.')[-1].lower() == 'd':
            messdog = wx.MessageDialog(self, '%s does not appear to be an Agilent .D file directory' % dfile, 
                                       'Could not open file', style = wx.OK)            
            messdog.ShowModal()
            messdog.Destroy()
            return
    
        #child = DrawPanel(self.ctrl, dfile, 1)
        child = DrawPanel(self.parentFrame, dfile, 1)
        self.ctrl.AddPage(child, os.path.basename(dfile), False) #, self.page_bmp
        self.ctrl.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, child.OnClose, self.ctrl)

    def ToolBarData(self):
        return ((10, "Open", wx.ART_FILE_OPEN, "Open", "Open a New MS File", 10),
            #(20, "Close", wx.ART_CLOSE, "Close", "Long help for 'Close'", 20),
            #("sep", 0, 0, 0, 0, 0),
            #(30, "Save Analysis", wx.ART_FILE_SAVE, "Save", "Long help for 'Save'", 30),
            #(40, "Load Analysis", wx.ART_FOLDER_OPEN, "Load Analysis", "Long help for 'Load Analysis'", 40),
            #("sep", 0, 0, 0, 0, 0),
            #(50, "Link to Mascot", wx.Image(os.path.join(installdir,  r'\image\mascot.png'), "Link to Dat File", "Long help for 'Load Analysis'", 50),
            #(60, "Link to mzSheet", wx.Image(os.path.join(installdir,  r'\image\mz_results.ico'), "Link to Multiplierz Report", "Long help for 'Load Analysis'", 60),
            ("sep", 0, 0, 0, 0, 0),
            (70, "Find MS2", wx.ART_FIND, "Find MS2", "Find MS2 scans of a given M/Z", 70),
            (80, "XIC", wx.Image(os.path.join(installdir,  r'image/XIC.png')), "XIC", "Open XIC Configuration Menu", 80),
            (90, "Pepcalc", wx.Image(os.path.join(installdir,  r'image/Pepcalc.png')), "Pepcalc", "Open the Peptide Calculator", 90),
            (100, "Jump to Scan", wx.Image(os.path.join(installdir,  r'image/Jump.png')), "Jump to Scan", "Jump to Scan By Scan Number", 100),
            (110, "Make Database", wx.Image(os.path.join(installdir,  r'image/SQLiteIcon.png')), "Open PSM File", "Open a Search Result Linked to the Current Data File", 110),
            ("sep", 0, 0, 0, 0, 0),
            (180, "Ion Label Tolerance", wx.Image(os.path.join(installdir,  r'image/dialIcon.bmp')), "Ion label tolerance", "Select Ion Label Tolerance", 180),
            (120, "XIC Range", wx.Image(os.path.join(installdir,  r'image/XICRangeGraphic.png')), "Specify RIC time range", "Specify Plot Time Range", 120),
            (130, "Spectrum Range", wx.Image(os.path.join(installdir,  r'image/MZRangeGraphic.png')), "Specify mass range", "Specify Plot Mass Range", 130),
            (140, "Intensity Scale", wx.Image(os.path.join(installdir,  r'image/IntensityGraphic.png')), "Specify Intensity Scale", "Specify Intensity Scale'", 140),
            (150, "XIC", wx.Image(os.path.join(installdir,  r'image/Add new trace.png')), "XIC adds to new window", "XIC adds to new window'", 150),
            ("sep", 0, 0, 0, 0, 0),
            (160, "Spectrum Readout", wx.ART_NORMAL_FILE, "Spectrum Text", "Show Selected Spectrum in Text Format", 160),
            ("sep", 0, 0, 0, 0, 0),
            (170, "Search Spectrum", wx.ART_EXECUTABLE_FILE, "Search Spectrum", "Submit Spectrum To Database Search", 170))
    
    
    def AddToolBarItems(self, tb):
        tsize = (24,24)
        for pos, label, art, short_help, long_help, evt_id  in self.ToolBarData():
            if pos != "sep":
                if not isinstance(art, basestring):
                    art.Rescale(*tsize)
                    new_bmp = wx.BitmapFromImage(art)
                else: # wx.ART_* and etc.
                    new_bmp = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, tsize)
                tb.AddLabelTool(pos, label, new_bmp, shortHelp=short_help, longHelp=long_help)
                self.Bind(wx.EVT_TOOL, self.OnToolClick, id=evt_id)
            else:
                tb.AddSeparator()

    def SetToolBar(self, tb):
        tsize = (24,24)
        self.AddToolBarItems(tb)
        tb.SetToolBitmapSize(tsize)
        tb.Realize() 

images = [wx.Image(os.path.join(os.path.dirname(__file__), 'image', '%s.PNG' % x)) for x in range(1,10)]
    
if __name__ == '__main__':
    try:
        frame = TopLevelFrame(None)        
        frame.Show()
    except wx._core.PyNoAppError:
        app = wx.App(False)
        frame = TopLevelFrame(None)        
        frame.Show()
        
    import platform
    if 'Windows' in platform.platform():
        import multiplierz.mzAPI.management as api_management
        guids_that_work = api_management.testInterfaces()
        if any(guids_that_work) and not all(guids_that_work):
            print "\n\n\n\n\n"
            print "NOTE- One or more vendor file interfaces are not currently installed."
            print "Access to some files may fail."
            print "To fix, run multiplierz.mzAPI.management.registerInterfaces() from a Python console."
            print '\n\n'
        elif not any(guids_that_work):
            ask_about_mzAPI = """
The multiplierz mzAPI vendor file interface modules
have not been enabled on this machine; these are required
in order to access .RAW, .WIFF and .D files.  Enable now?
            """
        
            askdialog = wx.MessageDialog(None, ask_about_mzAPI, 'mzAPI Setup', wx.YES_NO | wx.ICON_QUESTION)
            if askdialog.ShowModal() == wx.ID_YES:
                #api_management.registerInterfaces()
                from subprocess import call
                call([sys.executable, '-m', 'multiplierz.mzAPI.management'])           
        
    app.MainLoop()

    
