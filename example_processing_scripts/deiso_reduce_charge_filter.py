from multiplierz.spectral_process import peak_pick
from multiplierz.mass_biochem import protonMass

def processor_function(scan):
    envelopes, scan = peak_pick(scan, min_peaks = 2, tolerance = 0.01,
                                enforce_isotopic_ratios = False)
    for chg, chgEnvelopes in envelopes.items():
        for envelope in chgEnvelopes:
            mz, ints = envelope[0]
            red_mz = ((mz * chg) - ((chg-1) * protonMass))
            scan.append((red_mz, ints))
    return scan    