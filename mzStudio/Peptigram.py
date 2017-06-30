__author__ = 'Scott Ficarro'
__version__ = '1.0'


#Create Peptigram

import mz_workbench.mz_core as mz_core

def look_for_mz_return_intensity(current_MS1, mz, tolerance = 0.02, inten=0):
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

def derive_elution_range_by_C12_C13(m, scan_dict, scan, mz, cg, tolerance, threshold, rtdict):
    start = scan
    stop = scan
    last_scan = scan
    found_mz, found, intensity = look_for_mz_return_intensity(m.cscan(scan), mz, tolerance)
    scan_array = [[rtdict[scan], intensity]]
    isotope_step = float(mz_core.mass_dict['mi']["H+"])/float(cg)
    #find = [mz, mz + isotope_step, mz + (2*isotope_step)]
    find = [mz + isotope_step, mz + (2*isotope_step), mz]
    print "Scanning elution range for ... " + str(mz) + " around scan " + str(scan) + '\n'
    task = ["Forward", "Reverse"]
    for subtask in task:
        current_scan = scan
        go = True
        while go:
            fa = [False, False, False]
            all_found = False
            next_scan = mz_core.find_MS1(scan_dict, current_scan, subtask)
            scan_data = m.cscan(next_scan)
            for i, member in enumerate(find):
                found_mz, found, intensity = look_for_mz_return_intensity(scan_data, member, tolerance)
                fa[i] = found
            all_found = reduce(lambda x, y: x & y, fa)
            if not all_found:
                stop = current_scan
                go = False
            else:
                scan_array.append([rtdict[next_scan], intensity])
                current_scan = next_scan
    scan_array.sort()
    print scan_array
    return start, stop, scan_array

def GetAPeptigram(currentFile, scan, mz, cg, tolerance=0.02, threshold = 200):
    start, stop, scan_array = derive_elution_range_by_C12_C13(currentFile["m"], currentFile["scan_dict"], scan, mz, cg, tolerance, threshold, currentFile["rt_dict"])
    return scan_array