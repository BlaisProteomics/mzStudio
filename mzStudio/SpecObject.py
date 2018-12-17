
class SpecObject():
    
    def __init__(self, vendor, profile, detector, scan_type, scan_data, cent_data, processed_scan_data, filt, display_range, mass_ranges, score,
                 sequence, varmod, fixedmod, scan, charge, rawfile, viewProcData, viewCent, axes = 1):
        
        self.type = "Spectrum"
        self.vendor = vendor
        self.profile = profile
        self.detector = detector
        self.scan_type = scan_type
        self.scan_data = scan_data
        self.cent_data = cent_data
        self.processed_scan_data = processed_scan_data
        
        self.filter = filt
        self.display_range = display_range
        self.mass_ranges = mass_ranges
        self.score = score
        self.sequence = sequence
        
        self.varmod = varmod
        self.scan = scan
        self.charge = charge
        self.fixedmod = fixedmod
        self.rawfile = rawfile
        self.viewProcData = viewProcData
        self.viewCent = viewCent
        self.notes = ''
        self.axes = axes
        
        
        