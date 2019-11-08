from multiplierz.mass_biochem import AminoAcidMasses, mod_masses, AW, formulaForMass, peptideForMass, protonMass
from multiplierz.internalAlgorithms import ProximityIndexedSequence, PPM_bounds
import time # Testing only.


#starttime = time.clock()
##interesting_elements = [(x, AW[x]) for x in 
                        ##['C', 'H', 'N', 'O', 'P', 'S', '13C', '15N']]
#aaMasses = [(x, y[0]) for x, y in AminoAcidMasses.items()]
#singly_charged_stuff = aaMasses + mod_masses.items()
#doubly_charged_stuff = [(x + '++', y/2) for x, y in singly_charged_stuff]


#mass_lookup = ProximityIndexedSequence(singly_charged_stuff + doubly_charged_stuff,
                                       #indexer = lambda x: x[1],
                                       #dynamic = False)
#stoptime = time.clock()
#print "Yardstick preprocessing time: %s" % (stoptime - starttime)

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
                        if any([cs*2 < x for x in [hs, os, ps, ss]]):
                            continue # Basic plausibility requirement.
                        formula = {'C':cs,'H':hs, 'O':os, 'P':ps, 'S':ss}
                        formulae.append((chemicalDataMass(formula), formula_string(formula)))
    
    return formulae

def generate_oligo_masses():
    from multiplierz.mass_biochem import peptide_mass, AminoAcidMasses
    from itertools import combinations_with_replacement
    
    aaList = sorted(AminoAcidMasses.keys())
    
    def oligomass(oligo):
        return sum([AminoAcidMasses[x][0] for x in oligo])
    
    oligae = []
    for oligolen in range(0, 6):
        for oligo in combinations_with_replacement(aaList, oligolen):
            for mod, modmass in [('', 0), ('+Phospho', 79.966331),
                                 ('+Oxidation', 15.994915), ('+Deamidated', 0.984016),
                                 ('+Methyl', 14.01565), ('+H20', 18.010565)]:
                oligae.append((oligomass(oligo) + modmass + protonMass, '+'.join(oligo) + mod))
            
    return oligae




mass_of_molecules = sorted(generate_formula_masses() + generate_oligo_masses())
masslist = zip(*mass_of_molecules)[0]


#def analyze_delta(mz_delta):
    #starttime = time.clock()
    ## Outputs printable, potentially multi_line string of what the delta matches.  Quickly!
    #strings = ['MZ: %.3f\n' % mz_delta]
    #if mz_delta < 71.0788:
        #formulae = formulaForMass(mz_delta, calculate_tolerance, 
                                  #components = ('C', 'H', 'N', 'O', 'P', 'S', 
                                                #'13C', '15N', '2H'))
        #strings += map(formula_string, formulae)
    #else:    
        #things = mass_lookup.returnRange(mz_delta - lookup_tolerance, mz_delta + lookup_tolerance)
        #if mz_delta > 71.0788*2:
            #things += peptideForMass(mz_delta, 2, calculate_tolerance,
                                      #unique_sets = True)        
            #if mz_delta > 71.0788*3:
                #things += peptideForMass(mz_delta, 3, calculate_tolerance,
                                                      #unique_sets = True)                  
        #for name, mz in things:
            #diff = mz_delta - mz
            #substring = '%s (err. %.3f)' % (name, diff)
            #strings.append(substring)
            

            
    
    #print "%f yardstick time: %s" % (mz_delta, time.clock() - starttime)
    #return '\n'.join(strings)

from bisect import bisect_left, bisect_right
def analyze_delta(mz_delta, tolerance):
    starttime = time.clock()
    # Outputs printable, potentially multi_line string of what the delta matches.  And quickly!
    strings = ['MZ: %.3f\n' % mz_delta]
    botmz, topmz = mz_delta - tolerance, mz_delta + tolerance
    inrange = mass_of_molecules[bisect_left(masslist, botmz) : bisect_right(masslist, topmz)]
    for mass, molecule in inrange:
        strings.append('%s (err. %.3f)' % (molecule, mz_delta - mass))    
    
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
    masses = []
    masses += generate_formula_masses()
    masses += generate_oligo_masses()
    import bisect as b
    masses.sort()
    print "FOO"