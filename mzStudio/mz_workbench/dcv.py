

def extract_peak(mz, cg, MS2time, rawfile):
    pass

def find_index(mass_list, current_entry):
    return_index = -1
    for i, entry in enumerate(mass_list):
        if entry == current_entry:
            return_index = i
    return return_index

def find_mi(mass_list, current_entry, toler = 0.02, cg_column=3):
    charge = current_entry[cg_column]
    mass = current_entry[0]
    current_step = 1/float(charge)
    current_mass = mass - current_step
    result = True
    return_mz = mass
    return_int = current_entry[1]
    return_index = find_index(mass_list, current_entry)
    while result == True:
        result, found_mz, found_int, found_index = look_for_mass(mass_list, current_mass, toler)
        if result == True and found_int >= (0.4 * return_int):
            return_mz = found_mz
            return_int = found_int
            return_index = found_index
            current_mass -= current_step
        if result == True and found_int < (0.4 * return_int):
            result = False
    return return_mz, return_int, return_index

def limit_range(mass_list, start, stop):
    range = []
    for mass in mass_list:
        if mass[0] > start and mass[0] < stop:
            range.append(mass)
    return range

def dump_mass(mass_list):
    mass_list.sort(key=lambda t:t[0])
    for mass in mass_list:
        print mass[0]

def remove_isotopes(mass_list, mz, charge, toler = 0.02):
    current_step = 1/float(charge)
    current_mass = mz + current_step
    search_result = True
    while search_result:
        search_result, mass, intensity, index = look_for_mass(mass_list, current_mass)
        if search_result:
            del mass_list[index]
            current_mass += current_step
    return mass_list

def get_charge(mass, inten, mList, toler=0.005, cg_min=2, cg_max=7):
    #GET LIST OF EVERYTHING WITHIN 1 Da of peak in consideration
    candidates = []
    for member in mList:
        if member[0] > (mass + 0.09) and member[0] < (mass + 0.51):
            candidates.append(member[0])
        if member[0] > (mass + 0.51):
            break
    poss_cg = []
    for i in range(cg_min, cg_max+1):
        look_for = mass + (float(1)/float(cg_min))
        for member in candidates:
            if look_for < (member + toler) and look_for > (member - toler):
                poss_cg.append(i)

def deistope_reduce_charge(mass_list, cg_min=2, cg_max=7, min_int=0, toler=0.005):
    output = []
    if mass_list:
        mass_list_i.sort(key=lambda t: t[1], reverse=True)
        mass_list_m.sort(key=lambda t: t[0])
        Keep_going = True
        while Keep_going:
            current_entry = mass_list[0]
            current_inten = mass_list[1]
            get_charge(current_entry, current_inten, mass_list_m, toler, cg_min=1, cg_max=7)

def deisotope(mass_list, cg_min =0, cg_max = 100, min_int = 0, cg_column=3, toler=0.02):
    #sort list from most intense to least
    #0- mz, 1-intensity, 2-?, 3-charge
    mi_list = []
    if mass_list:
        mass_list.sort(key=lambda t: t[1], reverse=True)
        go = True #len(mass_list > 0)
        mi_list = []
        while go:
            current_entry = mass_list[0]
            current_cg = mass_list[0][cg_column]
            c_mi, c_int, c_ind = find_mi(mass_list, current_entry, cg_column=cg_column, toler=toler)
            v1, v2, v3, v4 = look_for_mass(mass_list, c_mi + (1/float(current_cg)), toler=toler)
            if v1 == True and current_cg > cg_min and current_cg < cg_max and c_int > min_int:
                if cg_column==3:
                    mi_list.append((mass_list[c_ind][0],mass_list[c_ind][1],mass_list[c_ind][2],mass_list[c_ind][3]))
                elif cg_column==2:
                    mi_list.append((mass_list[c_ind][0],mass_list[c_ind][1],0,mass_list[c_ind][2]))
            del mass_list[c_ind]
            mass_list = remove_isotopes(mass_list, c_mi, current_cg, toler=toler)
            if len(mass_list) == 0:
                go = False
    return mi_list
                
def look_for_mass(mass_list, mz, toler = 0.02):
    #mass_list should be in the form of a list of tuples [(17.387898333333332, 0.0, 2958, 'MS2', 'p')]
    hi = mz + toler
    lo = mz - toler
    result = False
    found_mz = 0
    found_int = 0
    found_index = 0
    found_list = []
    for i, entry in enumerate(mass_list):
        mass = entry[0]
        if mass > lo and mass < hi:
            found_mz = mass
            found_index = i
            found_int = entry[1]
            found_list.append([found_mz, found_index, found_int])
        
    if found_list:
        result = True
        found_list.sort(key=lambda t:t[2],reverse=True)
        found_mz = found_list[0][0]
        found_index = found_list[0][1]
        found_int = found_list[0][2]
    return result, found_mz, found_int, found_index

            
def check_mz_cg(mass_list, mz, cg, toler = 0.02):
    hi = mz + toler
    lo = mz - toler
    result = False
    index = 0
    for i, entry in enumerate(mass_list):
        mass = entry[0]
        charge = entry[3]
        if mass > lo and mass < hi and cg == charge:
            #print entry
            result = True
            index = i
    return result, index
    