from multiplierz.internalAlgorithms import peak_pick

def processor_function(scan):
    envelopes, scan = peak_pick(scan, min_peaks = 2, tolerance = 0.01,
                                enforce_isotopic_ratios = False)
    for chg, chgEnvelopes in envelopes.items():
        for envelope in chgEnvelopes:
            scan.append(envelope[0])
    return scan