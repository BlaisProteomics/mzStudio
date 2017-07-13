# NOTE: Requires numpy for standard deviation calculation!
from numpy import average, std


signal_to_noise_threshold = 1.5


def processor_function(scan):
    if not scan:
        return scan
    
    scan.sort(key = lambda x: x[1])
    for i in range(0, len(scan)):
        ints = [int for mz, int in scan[i:]]
        SN = average(ints) / std(ints)
        if SN > signal_to_noise_threshold:
            return scan[i:]
        
    return scan