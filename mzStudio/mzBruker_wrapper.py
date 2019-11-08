from multiplierz.mzAPI.bruker import mzBruker
from collections import defaultdict
import os
from time import clock

RT_CAT_W = 5
MZ_CAT_W = 1
K0_CAT_W = 0.1

def collect_dict(sequence):
    collection = defaultdict(list)
    for things in sequence:
        foo = things[0]
        bar = things[1:] if len(things) > 2 else things[1]
        collection[foo].append(bar)
    return collection

def aggregate_axis(seq, axis1, axis2):
    dat = defaultdict(float)
    for thing in seq:
        dat[thing[axis1]] += thing[axis2]
    return sorted(dat.items())


def parse_mob_filter(filt):
    # E.g. 'MOB: [RT 1.0-2.0] [MZ 1.0-2.0] [k0 0.0-3.0]'
    filt = filt.lower().split(':')[1]
    assert 'rt' in filt
    assert 'mz' in filt
    assert 'k0' in filt
    rts = map(float, filt.split('rt')[1].split(']')[0].split('-'))
    mzs = map(float, filt.split('mz')[1].split(']')[0].split('-'))
    k0s = map(float, filt.split('k0')[1].split(']')[0].split('-'))
    
    return rts[0], rts[1], mzs[0], mzs[1], k0s[0], k0s[1]

def _overlap(a, b, x, y):
    if a <= x and b >= y:
        return 'T'
    else:
        return (a <= x <= b or
                a <= y <= b or
                x <= a <= y)


class mzBrukerWrapped(object):
    """
    mzBruker object wrapped up to imitate a Thermo mzFile object.
    
    Scan numbers are meaningless outside the wrapper!
    """
    
    def __init__(self, filename):
        self.file_type = "Bruker"
        self.source = mzBruker(filename)
        precursorsFromMS = collect_dict(self.source.dbquery("SELECT Parent, AverageMz, Id FROM Precursors"))
        
        precursorFrames = collect_dict(self.source.dbquery("SELECT Precursor, Frame FROM PasefFrameMsMsInfo"))
        
        used_rts = set() # Total hack.
        pasef_rts = dict(self.source.pasef_frames)
        self.scan_list = []
        self.prec_num_lookup = {}
        self.ms1_num_lookup = {}
        self.precursor_scans = {} # For indexing from PEAKS report.
        for f_id, rt in self.source.ms1_frames:
            self.ms1_num_lookup[len(self.scan_list)+1] = f_id
            self.scan_list.append((rt, 0.0, len(self.scan_list)+1, 'MS1', []))
            for mz, prec_num in precursorsFromMS.get(f_id, []):
                frames = precursorFrames[prec_num]
                rts = [pasef_rts[f] for f in frames]
                
                nominal_rt = min(rts)
                while nominal_rt in used_rts:
                    nominal_rt += 0.0000001
                used_rts.add(nominal_rt)
                
                nominal_scannum = len(self.scan_list)+1
                self.prec_num_lookup[nominal_scannum] = prec_num
                self.scan_list.append((nominal_rt, mz, nominal_scannum, 'MS2', frames))
                
                self.precursor_scans[prec_num] = nominal_scannum
        
        self._xic_cache = {}    
        self._filters = None
        
        self.scantimes = {sn:rt for rt, _, sn, _, _ in self.scan_list}

    def scan(self, scanname, k0_start = None, k0_stop = None):
        if k0_start is None:
            k0_start = 0.0
        if k0_stop is None:
            k0_stop = 10.0
        
        rt, mz, sn, level, frames = self.scan_list[scanname-1]
        if level == 'MS1':
            id_num = self.ms1_num_lookup[sn]
            full_frame = self.source.frame(id_num)
            min_int = 0 if len(full_frame) < 1000 else min(set(zip(*full_frame)[-1]))
            full_frame = [x for x in full_frame if k0_start <= x[1] <= k0_stop]
            scan = [x for x in aggregate_axis(full_frame, 0, 2)]
        elif level == 'MS2':
            prec_num = self.prec_num_lookup[sn]
            scan = []
            for frame in frames:
                scan += self.source.pasef_scans(frame, prec_num = prec_num,
                                                include_k0 = True)
            scan = [(x[0], x[2]) for x in scan]# if k0_start <= x[1] <= k0_stop]
            # Decided to not filter on K0 for MS2s, because the PASEF system means
            # that that will simply blank out certain scans (precursors are TIMS'd, 
            # not fragmentation products.)  But that's easy to change.
            scan.sort()
        
        return scan
    
    def xic(self, start_time, stop_time, start_mz, stop_mz, filter = None, 
            force = False, **etcetc):
        window = (start_time, stop_time, start_mz, stop_mz, 0, 10)
        if (window, filter) in self._xic_cache:
            return self._xic_cache[window, filter]          
        elif filter and filter.split(':')[0] in {'RT', 'MZ', 'K0', 'KO', 'MOB'}:
            axis = {'RT' : 0, 'MZ' : 1, 'K0' : 2, 'KO' : 2, 'MOB' : 2}[filter.split(':')[0]]
            (start_time, stop_time, start_mz, 
             stop_mz, start_k0, stop_k0) = parse_mob_filter(filter)
            xic = self.generalized_xgram(axis,
                                         start_time, stop_time,
                                         start_mz, stop_mz,
                                         start_k0, stop_k0)
        elif not force and stop_mz - start_mz > 500:
            print "Assuming full-MZ-range XIC!"
            # Does not add to the in-code cache, since it's fast regardless.
            return [x for x in self.tic() if
                    start_time <= x[0] <= stop_time]  
        else:
            xic = self.source.xic_batch([window])[0][1]
                
        self._xic_cache[window, filter] = xic    
        return xic
    
    def tic(self):
        tic = self.source.dbquery("SELECT Time, SummedIntensities FROM Frames WHERE MsMsType = 0")
        tic.sort()
        return tic
    
    def scan_info(self, *etc, **etcetc):
        return [(rt, mz, sn, lvl, 'p') for rt, mz, sn, lvl, _ in self.scan_list]
    
    def filters(self, *etc, **etcetc):
        if self._filters is not None:
            return self._filters
        else:
            self._filters = []
            ms1_filt = "FTMS + p NSI Full ms [100.0-2000.0]"
            for rt, mz, sn, lvl, frames in self.scan_list:
                if lvl == "MS1":
                    self._filters.append((rt, ms1_filt))
                elif lvl == 'MS2':
                    # "ITMS" doesn't get centroided.
                    filt = "ITMS + p NSI Full ms2 %.2f@hcd1.0 [100.0-2000.0]" % mz
                    self._filters.append((rt, filt))
            
            return self._filters
    
    def scan_range(self):
        return 1, len(self.scan_list)
    
    def time_range(self):
        return self.scan_list[0][0], self.scan_list[-1][0]
    
    def headers(self):
        return self.scan_info()    
    
    def timeForScan(self, sn):
        return self.scantimes[sn]
    
    def scan_for_precursor(self, precursor):
        return self.precursor_scans[int(float(precursor))]
    
    def generalized_xgram(axis, start_time, stop_time,
                          start_mz, stop_mz, start_k0, stop_k0):
        volume = self.source.extract_MS1_volumes([start_time, stop_time, start_mz,
                                                  stop_mz, start_k0, stop_k0])
        
        pts = defaultdict(float)
        for pt in volume:
            pts[pt[axis]] += pt[-1]
        return sorted(pts.items())
            
        
if __name__ == '__main__':
    from time import clock
    foo = mzBrukerWrapped(r'C:\Users\Max\Desktop\Projects\2019-05-25-CSF-10min-trap_Slot2-39_1_397.d')
    start = clock()
    bar = foo.xic(0, 10000, 500, 501)
    print clock() - start
    start = clock()
    bar = foo.xic(5000, 6000, 500, 501)
    print clock() - start
    print "FOO"
