from multiplierz.mass_biochem import AminoAcidMasses, mod_masses, AW, formulaForMass, peptideForMass, protonMass
from multiplierz.internalAlgorithms import ProximityIndexedSequence, PPM_bounds
import time # Testing only.

mass_of_molecules = []
masslist = []

calculate_tolerance = 0.1
lookup_tolerance = 1

def formula_string(formula):
    parts = []
    for atom, elements in sorted(formula.items()):
        if not elements: continue
        if len(atom) > 1:
            parts.append('(%s)%s' % (atom, elements if elements > 1 else ''))
        else:
            parts.append('%s%s' % (atom, elements if elements > 1 else ''))
    return ''.join(parts)

def generate_formula_masses():
    from multiplierz.mass_biochem import chemicalDataMass
    chnopscounts = {'C':5,
                    'H':10,
                    'O':5,
                    'P':3,
                    'S':1}
    formulae = []
    for cs in range(1, chnopscounts['C']+1):
        for hs in range(0, chnopscounts['H']+1):
            for os in range(0, chnopscounts['O']+1):
                for ps in range(0, chnopscounts['P']+1):
                    for ss in range(0, chnopscounts['S']+1):
                        if any([cs*2 < x for x in [os, ps, ss]]) or any([hs < x for x in [cs, ps, ss, os]]):
                            continue # Basic plausibility requirements.
                        formula = {'C':cs,'H':hs, 'O':os, 'P':ps, 'S':ss}
                        formulae.append((chemicalDataMass(formula), formula_string(formula)))
    
    return formulae

mod_mass_lookup = {'':0.0,
                   'Deamidated': 0.984016,
                   'Methyl': 14.01565,
                   'Oxidation': 15.994915,
                   'Phospho': 79.966331,
                   'TMT6': 229.162932}
def generate_oligo_masses(mod_list):
    from multiplierz.mass_biochem import peptide_mass, AminoAcidMasses
    from itertools import combinations_with_replacement
    
    aaList = sorted(AminoAcidMasses.keys())
    
    def oligomass(oligo):
        return sum(AminoAcidMasses[x][0] for x in oligo)
    
    oligae = []
    for oligolen in range(0, 5):
        for oligo in combinations_with_replacement(aaList, oligolen):
            for mod in [''] + list(mod_list):
                modmass = mod_mass_lookup[mod]
                if mod:
                    mod = '+' + mod
                # Base fragment:
                oligae.append((oligomass(oligo) + modmass, '+'.join(oligo) + mod))
                # Also b-ion (+ proton):
                oligae.append((oligomass(oligo) + modmass + protonMass, '+'.join(oligo) + mod + '+H'))
                # Also y-ion (+H2O):
                oligae.append((oligomass(oligo) + modmass + protonMass + 18.010565, '+'.join(oligo) + mod + '+H2O'))
            
    return oligae


def initialize_masses(calculate_AAs, calculate_CNHOPS, charge_list, mod_list):
    starttime = time.clock()
    
    global mass_of_molecules
    global masslist
    mass_of_molecules = []
    masslist = []

    base_molecules = ((generate_formula_masses() if calculate_CNHOPS else [])
                         + 
                         (generate_oligo_masses(mod_list) if calculate_AAs else []))
    charged_molecules = []
    for mass, molec in base_molecules:
        if '+2' in charge_list:
            charged_molecules.append(((mass + protonMass)/2, molec + '(++)'))
        if '+3' in charge_list:
            charged_molecules.append(((mass + (protonMass*2))/2, molec + '(+++)'))
    if '+1' in charge_list:
        charged_molecules += base_molecules
        
    mass_of_molecules = charged_molecules
    mass_of_molecules.sort()
    masslist = zip(*mass_of_molecules)[0]
    
    stoptime = time.clock()
    print "Yardstick preprocessing time: %s" % (stoptime - starttime)



from bisect import bisect_left, bisect_right
def analyze_delta(mz_delta, tolerance):
    starttime = time.clock()
    # Outputs printable, potentially multi_line string of what the delta matches.  And quickly!
    #strings = ['MZ: %.3f\n' % mz_delta]
    strings = []
    botmz, topmz = mz_delta - tolerance, mz_delta + tolerance
    inrange = mass_of_molecules[bisect_left(masslist, botmz) : bisect_right(masslist, topmz)]
    for mass, molecule in inrange:
        strings.append('%s (err. %.3f)' % (molecule, mz_delta - mass))    
    strings.append('MZ: %.3f\n' % mz_delta)
    print "%f yardstick time: %s" % (mz_delta, time.clock() - starttime)
    return '\n'.join(strings)

def match_to_mass(mz, ppm_tol): 
    # Same except only gets best match, designed for much tighter tolerance.
    #botmz, topmz = mz - tolerance, mz + tolerance
    botmz, topmz = PPM_bounds(ppm_tol, mz)
    inrange = mass_of_molecules[bisect_left(masslist, botmz) : bisect_right(masslist, topmz)]
    if inrange:
        match = min(inrange, key = lambda x: abs(mz - x[0]))
        return '%s (err. %.2E)' % (match[1], (mz - match[0]))
    else:
        return ''







if __name__ == '__main__':
    match_to_mass(1085.6133, 10)
    #masses = []
    #masses += generate_formula_masses()
    #masses += generate_oligo_masses()
    #import bisect as b
    #masses.sort()
    #print "FOO"