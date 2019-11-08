

filename = r'D:\SBF\mzStudio\wiff\2012-03-29-Ascites-MRM-1.wiff'

import multiplierz.mzAPI as mzAPI

m = mzAPI.mzFile(filename)
start, stop = m.scan_range()
import mz_workbench.mz_core as mz_core

scan_dict, rt_dict, filter_dict, rt2scan = mz_core.create_dicts(m, start, stop)