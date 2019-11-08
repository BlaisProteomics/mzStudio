# import comtypes
# from comtypes.client import CreateObject
# from ctypes import *
import re
from collections import defaultdict

import multiplierz.mgf as mgf

# print "wiff.py: 0.2.0"

debug = True

def _to_float(x):
    try :
        out = float(x)
    except ValueError :
        out = str(x)
    return out

from multiplierz.mzAPI import mzScan, mzFile as mzAPImzFile

class mzScan(list):
    """Subclass of list object for custom scan methods

    The mode can be 'p' or 'c' for profile or centroid respectively

    """

    def __init__(self, s, time, mode='p', mz=0.0, z=0):
        list.__init__(self, s)
        self.time = time
        self.mode = mode
        self.mz = mz
        self.z = z
        
    def peak(self, mz, tolerance):
        return max([i for m,i in self if abs(m-mz) <= tolerance] or [0])

class mzFile(mzAPImzFile):
    """wiffreader-based implementation of mzAPI's mzFile class"""

    def GetMassListFromScanNum(self, nScanNumber):
        #This is a function test, not implemented in original raw function
        #MassList = self.source.GetMassListFromScanNum(nScanNumber, 1)
        rt = self.source.getRTfromScan(nScanNumber)
        #print rt
        MassList = self.source.Get_Spectrum(rt, self.experiment)
        return MassList

    def filters(self):
        #GENERIC MGF FILTER
        #MGF ms2 542.5423 [first_mass:last_mass] Scan
        filters = []
        #for i in range(1, self.scan_number+1):
        for i in sorted(self.mgf_data.keys(), key = lambda x: int(x)):
            cur_scan = self.scan(i)                
            addTitle = ''
            # addRxn removed because what extractor produces this?
            #addRxn = ''
            #if 'REACTION' in self.mgf_data[i].keys():
                #addRxn =' ' + self.mgf_data[i]['REACTION']
            if 'title' in self.mgf_data[i].keys():
                if self.mgf_data[i]['title'].find(".dta"):
                    if 'MultiplierzMGF' in self.mgf_data[i]['title']:
                        addTitle = mgf.standard_title_parse(self.mgf_data[i]['title'])['scan']
                    else:
                        try:
                            addTitle = self.mgf_data[i]['title'].split(".")[1]
                        except:
                            addTitle = self.mgf_data[i]['title'].split(":")[1].split(" ")[0]
            #current_filter = (i, "MGF ms2 " + str(self.mgf_data[i]['pepmass']) + ' [' + str(int(min([x[0] for x in cur_scan]))-10) + ':' + str(int(max([x[0] for x in cur_scan]))+10) + ']' + addTitle + addRxn) 
            if cur_scan:
                startmass = str(int(min([x[0] for x in cur_scan]))-10)
                stopmass = str(int(max([x[0] for x in cur_scan]))+10)
            else:
                startmass = "0.0"
                stopmass = "0.0"
            current_filter = "MGF ms2 %s [%s:%s] %s" % (str(self.mgf_data[i]['pepmass']),
                                                          startmass, stopmass,
                                                          addTitle)
            filters.append((i, current_filter))
        return filters
            
    def headers(self):
        '''Doesn't actually store the full headers. Generates the full scan_info
        list by looking at filter and header values. The results are cached.
        '''
        self._headers = None
        return self._headers

    def __init__(self, data_file, **kwargs):
        """Initializes mzAPI and opens a new file

        >>> dataFile = 'C:\\Documents and Settings\\User\\Desktop\\rawFile.RAW'
        >>> myPeakFile = mzAPI.mzFile(dataFile)

        """
        
        self.file_type = 'mgf'
        self.data_file = data_file
        self.source = None
        
        
        print "Parsing mgf (may take a long time for large file!) ..."
        def parseToScan(desc):
            if 'MultiplierzMGF' in desc:
                return int(mgf.standard_title_parse(desc)['scan'])
            elif r'1/K0' in desc:
                return int(desc.split('#')[1].split('-')[0])
            else:
                return int(desc.split('.')[1])
        mgf_data = mgf.parse_mgf(data_file, labelType = parseToScan)
        print "Finished parsing MGF"
        
        
        self.mgf_data = mgf_data
    
        self._filters = None
        self._headers = None
        self.scan_number = max(map(int, self.mgf_data.keys()))
        
        
        
    def close(self):
        #modified
        """Closes the open MS data file

        Example:
        >>> myPeakFile.close()

        """
        self.source.Close()

    def scan_list(self, start_time=None, stop_time=None, start_mz=0, stop_mz=99999):
        """Gets a list of [(time,mz)] in the time and mz range provided

        All full MS scans that fall within the time range are included.
        Only MS/MS scans that fall within the mz range (optional) are included

        Example:
        >>> scan_list = my_peakfile.scan_list(30.0, 35.0, 435.82, 436.00)

        """
        
        return None
        #return [(t, mz) for t, mz in scanList if start_time <= t <= stop_time and (mz == 0.0 or start_mz <= mz <= stop_mz)]

    def scan_info(self, start_time, stop_time=0, start_mz=0, stop_mz=99999):
        """Gets a list of [(time, mz, scan_name, scan_type, scan_mode)] in the time and mz range provided

        scan_name = number for RAW files, (cycle, experiment) for WIFF files.

        All full MS scans that fall within the time range are included.
        Only MS/MS scans that fall within the mz range (optional) are included

        Example:
        >>> scan_info = my_peakfile.scan_info(30.0, 35.0, 435.82, 436.00)
        """
        #if not self._headers:
        #    self.headers()

        if stop_time == 0:
            stop_time = start_time

        return [(t,mz,sn,st,sm) for t,mz,sn,st,sm in self.headers()
                if start_time <= t <= stop_time and (st == 'MS1' or st == 'Precursor' or start_mz <= mz <= stop_mz)]

    def scan_time_from_scan_name(self, scan_name):
        """Essentially, gets the time for a raw scan number

        Example:
        >>> #raw
        >>> scan_time = myPeakFile.scan_time_from_scan_name(2165)

        """
        #modified for C# COM Object
        scantime = self.source.getRTfromScan(scan_name)
        return scantime

    def scan(self, scan_number):
        """Gets scan based on the specified scan number

        The scan is a list of (mz, intensity) pairs.

        Example:
        >>> scan = myPeakFile.scan(1)

        """
        return self.mgf_data[scan_number]['spectrum']
        #query = self.mgf_data[str(scan_number)]
        #ions_string = query['IONSTRING']
        #if ions_string:
            #try:
                #cur_scan = [(float(mz), float(intensity)) for mz, intensity in [peak.split(":") for peak in ions_string.split(",")]]
            #except:
                #cur_scan = [(float(mz), float(intensity), float(cg)) for mz, intensity, cg in [peak.split(":") for peak in ions_string.split(",")]]
        #else:
            #cur_scan = []

        #return cur_scan

    def xic(self, start_scan, stop_scan, start_mz, stop_mz, filter=None):
        #modified
        """Generates eXtracted Ion Chromatogram (XIC) for given scan and mz range

        The function integrates the precursor intensities for given time and mz range.
        The xic is a list of (scan,intensity) pairs.

        Example:
        >>> xic = myPeakFile.xic(31.4, 32.4, 435.82, 436.00)

        For wiff files, Filter is not used!

        """
        xic = []
        for i in sorted(self.mgf_data.keys(), key = lambda x: int(x)):
            cur_scan = self.mgf_data[i]['spectrum']
            
            total = 0
            for member in cur_scan:
                if member[0] > start_mz and member[0] < stop_mz:
                    total += member [1]
            xic.append((float(i), total))
        
        return xic

    def time_range(self):
        #start = 1
        #stop = len(self.mgf_data)
        start = min(self.mgf_data.keys(), key = int)
        stop = max(self.mgf_data.keys(), key = int)        
        return (int(start), int(stop))

    def scanForTime(self,the_time):
        raise NotImplementedError('Not implemented for mgf')

    def timeForScan(self,the_scan):
        raise NotImplementedError('Not implemented for mgf')
    
    def scan_range(self):
        start = min(self.mgf_data.keys(), key = int)
        stop = max(self.mgf_data.keys(), key = int)
        return (start, stop)

    
