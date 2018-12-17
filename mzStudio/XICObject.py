class XICObject():
    
    def __init__(self, rawfile, data, xr, time_range, xic_mass_ranges, xic_filters, xic_scale, xic_max, active_xic, xic_view):
        
        self.type = 'XIC'
        self.rawfile = rawfile
        self.data = data
        self.xr = xr
        self.time_range = time_range
        self.full_time_range = time_range
        self.xic_mass_ranges = xic_mass_ranges
        self.xic_filters = xic_filters
        self.xic_scale= xic_scale
        self.xic_max = xic_max
        self.active_xic = active_xic
        self.xic_view = xic_view     
        
        self.notes = ''