__author__ = 'Scott Ficarro'
__version__ = '1.0'


# Check sheet type

import multiplierz.mzReport as mzReport


def perform_check(filename):
    
    search_type = 'Unknown'
    try:
        rdr = mzReport.reader(filename, sheet_name="Data")
    except (IOError, TypeError) as err:
        if filename.split('.')[-1] in {'csv', 'txt'}:
            from multiplierz.mzReport.mzCSV import CSVReportReader
            rdr = CSVReportReader(filename)
            if 'DeltaCn' in rdr.columns:
                return 'Proteome Discoverer'
            elif 'AScore' in rdr.columns:
                return 'PEAKS'
        else:
            raise IOError, 'Report type not recognized. (Not PD file.)'
    sheets = rdr.sheet_names()
    rdr.close()
    if "Mascot_Header" in sheets or 'Mascot Header' in sheets:
        search_type = 'Mascot'
    elif "XTandem_Header" in sheets:
        search_type = 'X!Tandem'
    elif "Comet_Header" in sheets:
        search_type = 'COMET'
    #elif 'PSMs' in sheets:
        #search_type = "Proteome Discoverer"
    else:
        if 'Data' in sheets:
            print "WARNING- Assuming Multiplerz-style Mascot PSM file."
            search_type = 'Mascot'
        else:
            raise IOError, 'Report type not recognized. (No *_Header sheet, and not PD file.)'
    return search_type
    
def test():
    filename = r'D:\SBF\COMETvsMASCOT\2014-03-12-K562-1_HCD_RECAL.mgf.xls'
    filename = r'D:\SBF\mzStudio\RESULT4.xlsx'
    #filename = r'D:\SBF\mzStudio\mascot.xlsx'
    #filename = r'D:\SBF\mzStudio\comet.xlsx'
    #filename = r'D:\SBF\mzStudio\tandem.xlsx'
    
    rdr = mzReport.reader(filename)
    
    print "A"
    
    search_type = perform_check(filename)
    print search_type
    
#test()

def test2():
    
    from multiplierz.mass_biochem import fragment
    
    seq = 'DMRVYISHPFHL'
    
    a = fragment(seq, mods=['S6: Phospho', 'M2: 16.0', 'Nterm: 42'], charges=[2], ions=['b', 'y'], 
            neutralPhosLoss=False, neutralLossDynamics={}, 
            enumerateFragments=False, waterLoss=False)
    
    
    print "A"
    
    
#test2()
    
def test3():
    
    filename = r'D:\SBF\mzStudio\RESULT_PSMs.txt'
    
    rdr = mzReport.reader(filename)
    
    print
    
#test3()