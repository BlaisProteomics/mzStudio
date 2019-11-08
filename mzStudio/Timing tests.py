
import multiplierz.mzAPI as mzAPI

import time
import glob

def process():
    filename = r'd:\sbf\mzstudio\multifile\2017-03-02-csf-biofind-set1-proteome-tmt-3d-15-230.raw'
    filename = r'd:\sbf\mzstudio\multifile\2017-03-02-CSF-BIOFIND-SET1-PROTEOME-TMT-3D-39-200.raw'
    filename = r'd:\sbf\mzstudio\multifile\2017-03-02-CSF-BIOFIND-SET1-PROTEOME-TMT-3D-33-200.raw'
    t1 = time.time()
    m = mzAPI.mzFile(filename)
    
    #x = m.xic(0, 999999, 300, 2000, 'Full ms ')
    print "File open time"
    t2 = time.time()
    
    print str(t2-t1)
    #ms1_count = len([x for x in m.scan_info() if x[3] == 'MS1'])
    #ms2_count = len([x for x in m.scan_info() if x[3] == 'MS2'])
    #print ms1_count
    #print ms2_count
    print "TIC time"
    x = m.xic(0, 999999, 0, 2000, '')

    t5 = time.time()
    print str(t5-t2)
    print len(x)
    
    print "XIC time"
    x = m.xic(0, 999999, 644, 645, " ms ")
    
    t6 = time.time()
    print str(t6-t5)
    
    m.close()
    
    #scant = m.scan_time_from_scan_name(4000)
    #print scant
    #t3 = time.time()
    #scan = m.scan(scant)
    #t4 = time.time()
    #print len(scan)
    #print "Time"
    #print str(t4-t3)
    
    #scant = m.scan_time_from_scan_name(5000)
    #print scant
    #t3 = time.time()
    #scan = m.scan(scant)
    #t4 = time.time()
    #print len(scan)
    #print "Time"
    #print str(t4-t3)    
    
process()

def get_MS2():
    files = glob.glob(r'D:\SBF\mzStudio\timingTests\2011-08-08-enolase-100fmol-1.wiff')
    files = [r'D:\SBF\mzStudio\20fmolBSA-profile.d']
    for file_name in files:
        m = mzAPI.mzFile(file_name)
        ms1_count = len([x for x in m.scan_info() if x[3] == 'MS1'])
        ms2_count = len([x for x in m.scan_info() if x[3] == 'MS2'])        
        print file_name
        print ms1_count
        print ms2_count
        m.close()
    
#get_MS2()