# 2012-12-25
# Redesigned to overcome a limitation in the interface to the Data Explorer
# Operations like get_spectral_data and close occur on the active file object only.
# I could not find a way to guarantee that the active file is the desired file object when multiple files are opened
# Therefore, the Data Explorer is used to open a file, get all the necessary data, store it in the object instance, and then close the Data Explorer File.
# The only calls to vb_MALDI.dll occur during open_file, where all the data is extracted.

try:
    import comtypes.client
except ImportError:
    pass

def old_centroid(spectrum, eliminate_noise = True, step_length = 0.025, peak_min = 3, cent_thresh=0):
    if spectrum:
        cent = []
        if eliminate_noise:
            masses, intens = zip(*spectrum)
            if cent_thresh:
                noise = cent_thresh
            else:
                noise = min(intens)
            new_spec = []
            for member in spectrum:
                if member[1] > noise:
                    new_spec.append(member)
            spectrum = new_spec
        if len(spectrum) > 2:
            groups = []
            current = 0
            group = []
            delta = 0
            go = True
            while go == True:
                while delta <= step_length:
                    group.append(spectrum[current])
                    current += 1
                    try:
                        delta = spectrum[current][0] - spectrum[current-1][0]
                    except:
                        delta = step_length + 1
                        go = False
                groups.append(group)
                if current == len(spectrum) - 1:
                    go = False
                group = []
                delta = 0
            for member in groups:
                if len(member) >= peak_min:
                    member.sort(key=lambda t:t[1], reverse = True)
                    cent.append([member[0][0], member[0][1]])
        del spectrum
        return cent
    else:
        return [(0,0)]

def centroid(spectrum, eliminate_noise = True, step_length = 0.025, peak_min = 2, cent_thresh=0):
    spectrum = [x for x in spectrum if x[1] > 8]
    if spectrum:
        cent = []
        if eliminate_noise:
            masses, intens = zip(*spectrum)
            noise = min(intens)
            new_spec = []
            for member in spectrum:
                if member[1] > noise:
                    new_spec.append(member)
            spectrum = new_spec
        if len(spectrum) > 2:
            groups = []
            current = 0
            group = []
            delta = 0
            go = True
            while go == True:
                while delta <= step_length:
                    group.append(spectrum[current])
                    current += 1
                    try:
                        delta = spectrum[current][0] - spectrum[current-1][0]
                    except:
                        delta = step_length + 1
                        go = False
                groups.append(group)
                if current == len(spectrum) - 1:
                    go = False
                group = []
                delta = 0
            for member in groups:
                if len(member) >= peak_min:
                    member.sort(key=lambda t:t[1], reverse = True)
                    half_max_int = float(member[0][1])/float(2.0)
                    tops = filter(lambda x: x[1] > half_max_int, member)
                    #tops.sort(key=lambda t:t[0])
                    tops.sort(key=lambda t:t[1], reverse = True)
                    #result = old_centroid(tops, eliminate_noise = False, step_length = 0.005, peak_min = 3)
                    #for member in result:
                    cent.append([tops[0][0], tops[0][1]])
                    
        del spectrum
        return cent
    else:
        return [(0,0)]

class t2dFile():

    def __init__(self):
        try:
            self.source = comtypes.client.CreateObject("{AAF19623-2381-4D5B-8155-B44D7F73AD91}")
        except:
            print "COM Object not registered!"
            raise ValueError("Register COM Object!")
            
    def open_file(self, filename):
        self.source.OpenFile(filename)
        self.first_mass = self.source.GetFirstSpectrumNumber()
        self.last_mass = self.source.GetLastSpectrumNumber()
        self.spectral_data = self.source.GetSpectralData()
        self.source.Close()

    def close(self):
        del self.spectral_data
        del self.first_mass
        del self.last_mass

    def get_first_mass(self):
        return self.first_mass

    def get_last_mass(self):
        return self.last_mass

    def get_headers(self):
        return self.spectral_data.split('\n')[0].split('\t')

    def scan_range(self):
        return (self.get_first_mass(), self.get_last_mass())

    def get_scan(self):
        scan = []
        for member in self.get_spectral_data():
            #print member
            scan.append([member[1], member[5]])
        return scan

    def get_spectral_data(self):
        spectral_data = self.spectral_data.split('\n')
        data = []
        for i in range(1, len(spectral_data)):
            entry = []
            current = spectral_data[i].split('\t')
            for member in current:
                if member:
                    entry.append(float(member))
                #else:
                    #ent
            if entry:
                data.append(entry)
        return data

