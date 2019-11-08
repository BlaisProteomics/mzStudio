__author__ = 'Scott Ficarro'
__version__ = '1.0'


import multiplierz.mzReport as mzReport
from multiplierz.mgf import standard_title_parse
import sqlite3 as sql
import os
import wx

try:
    from agw import pygauge as PG
except ImportError: # if it's not there locally, try the wxPython lib.
    try:
        import wx.lib.agw.pygauge as PG
    except:
        raise Exception("Requires wxPython version greater than 2.9.0.0")

def check_entry(entry):
    type = "None"
    try:
        float(entry)
        type = "real"
    except:
        type = "text"
    return type

'''
Useful routines for working with sqlite files.


'''


def make_database(file, overwrite=True, vendor='Thermo', parent=None, 
                  searchtype="Mascot", scan_convert = None, mgf_dict={}):
    '''
    
    Takes an xls or txt file and makes an mzResults file (sqlite database) for easy access and parsing of data.
    
    '''
    parent.parent.SetupAdjustableGauge()
    hh = parent.parent.adj_gauge.gauge1
    wx.Yield()
    
    db = file[:-4] + '.db'
    if os.path.exists(db):
        if overwrite:
            os.remove(db)
    conn = sql.connect(db)
    c = conn.cursor()
    
    try:
        rdr = mzReport.reader(file, sheet_name="Data")
    except (IOError, TypeError) as err:
        if file.lower().endswith('.txt') or file.lower().endswith('.csv'):
            from multiplierz.mzReport.mzCSV import CSVReportReader
            rdr = CSVReportReader(file)
        else:
            raise err
    
    rdrdata = list(rdr)
    hh.SetRange(len(rdrdata))
    parent.parent.adj_gauge.Update()
    parent.Update() # This may want to trigger parent.parent.notebook.Update instead,
    # but I think this should trigger that in turn.
    
    line = 'create table if not exists peptides (id integer primary key, '
    
    
    for i, col in enumerate(rdr.columns):
        typ = check_entry(rdrdata[0][col])
        if col.lower() == 'id':
            col = 'id_'
        elif col.lower() == 'scan':
            col = 'scan_'
        line += '"' + col + '"' + typ + ' , '  #' text, '
    
    if vendor == 'Thermo' and searchtype in ['Mascot', 'COMET', 'X!Tandem']:
        line += '"scan" integer);'
    else: #Proteome Discoverer
        line += '"scan" integer, "spectrum description" text);'
    #else:
        #line = line[:-2] + ');' # To remove trailing , .
    
    #if vendor == 'ABI':
    #    line += '"scan" integer, "experiment" string);'
        
    print line
    c.execute(line)
    conn.commit()
    counter = 0
    for i, row in enumerate(rdrdata):
        if counter % 50 == 0:
            print counter
            
            hh.SetValue(counter)
            parent.parent.adj_gauge.Update()
            parent.Update() # Or parent.parent.notebook.Update, see above.
            hh.Refresh()
           
        counter += 1
        wx.Yield()
        
        parent.parent.adj_gauge.Update()
        parent.Update()
        hh.Refresh()
        
        line = 'insert into peptides values (' + str(i) + ', "'
        
        
        for col in rdr.columns:
            current = row[col]
            if not current:
                current = ''
            try:
                current=current.replace('"','')
            except:
                pass
            line += str(current) + '", "'
            
        line = line[:-1]
        if searchtype in ['Mascot', 'X!Tandem', "COMET"]:
            scan = scan_convert(row['Spectrum Description'])
            line += scan
            #if 'MultiplierzMGF' in row['Spectrum Description']:
                #scandata = standard_title_parse(row['Spectrum Description'])
                #scan = scandata['scan']
                #line += str(scan)
            #elif vendor == 'Thermo':
                #scan = row["Spectrum Description"].split(".")[1]
                #line += scan
            #elif vendor == 'ABI':
                #scan = row["Spectrum Description"].split(".")[4]
                #experiment = row["Spectrum Description"].split(".")[5]
                #line += scan + ", " + experiment
            line += ');'
        elif searchtype == 'PEAKS':
            if 'Precursor Id' in row:
                line += str(row['Precursor Id']) + ', "NA");'
            else:
                line += row['Scan'].split(':')[1] + ', "NA");'
        else:
            #Proteome Discoverer or MGF
            if mgf_dict:
                query=int(row['First Scan'])
                desc=mgf_dict[int(query)]
                scan=int(standard_title_parse(mgf_dict[int(query)])['scan'])            
                line += str(scan) + ', "' + desc+ '");'
            else:
                line += row['First Scan'] + ', "NA");'
        
        c.execute(line)
        
        if i % 1000 == 0:
            conn.commit()
        
    conn.commit()

    c.close()
    conn.close()
    
    parent.parent.HideAdjGauge()
    return db

def get_columns(database, table='peptides'):
    '''
    
    Get columns gets all columns from the table.  Uses PRAGMA table_info command
    
    Now deprecated.  Get columns directory from query with c.description.
    
    '''
    raise ValueError("Deprecated.")
    conn = sql.connect(database)
    c = conn.cursor()
    c.execute('PRAGMA table_info('+ table + ');')
    cols = []
    for row in c:
        cols.append(row[1])
    c.close()
    conn.close()
    return cols

def pull_data(database, query):
    conn = sql.connect(database)
    c = conn.cursor()
    #c.execute(".headers on") #THIS ONLY WORKS IN COMMAND LINE TOOL
    c.execute(query)
    data = []
    for row in c:
        data.append(row)
    c.close()
    conn.close()
    return data

def construct_data_dict(database, query):
    '''

    EXECUTES QUERY ON DATABASE.  RETURNS RESULTS AND COLUMNS.
    
    '''
    #----------EXECUTE THE QUERY
    conn = sql.connect(database)
    c = conn.cursor()
    c.execute(query)
    datalist = []
    for row in c:
        datalist.append(row)
    print "On the DL"
    print datalist
    #----------RETRIEVE THE COLUMNS FROM THE QUERY; THIS IS STORED IN C.DESCRIPTION    
    cols = [y[0] for y in c.description]    
    print cols
    #----------CONSTRUCT A "LIST OF DICTIONARIES"
    #----------EACH ENTRY WILL NOW BE A DICT i.e. {"Peptide Sequence":"AYTSSSLK", "Peptide Score":55,...}
    data = []
    for member in datalist:
        entry = {}
        for i, col in enumerate(cols):
            entry[col]=row[i]
        data.append(entry)
    c.close()
    conn.close()
    return data, cols    

def pull_data_dict(database, query, table='peptides'):
    '''
    
    Performs query on sql database, returns columns and rows.
    
    '''
    
    if query.split()[0].lower() != 'select':
        wx.MessageBox('Query must select entries.')
        raise NotImplementedError
    
    
    #cols = get_columns(database, table)
    conn = sql.connect(database)
    c = conn.cursor()
    #c.execute("headers on;") #ONLY WORKS IN COMMAND LINE MODE
    c.execute(query)

    col_list = c.description
    cols = []
    for x in col_list:
        cols.append(x[0])
    
    data = []
    for row in c:
        entry = {}
        for i, col in enumerate(cols):
            entry[col]=row[i]
        data.append(entry)
    c.close()
    conn.close()
    return data, cols


#-----------------------------------------------------------------------------------CODE FOR GAUGES AND PROGRESS

class TestPanel(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent , -1, "Progress...", size=(300,110), pos=(100,200))
        self.mainPanel = wx.Panel(self, -1)
        self.mainPanel.SetBackgroundColour(wx.WHITE)
        self.count = 0

        self.g2 = wx.Gauge(self, -1, 50, (250, 95), (250, 25))

        self.Bind(wx.EVT_TIMER, self.TimerHandler)
        self.timer = wx.Timer(self)
        self.timer.Start(2000)
        self.DoLayout()

    def __del__(self):
        self.timer.Stop()

    def TimerHandler(self, event):
        #self.count += 1
        #if self.count == 100:
        #    self.count = 0

        self.g2.Pulse()

    def DoLayout(self):
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.g2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 20)
        self.mainPanel.SetSizer(mainSizer)
        mainSizer.Layout()
        frameSizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(frameSizer)
        frameSizer.Layout()

class PyGaugeDemo(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent , -1, "Progress...", size=(150,110))
        self.mainPanel = wx.Panel(self, -1)
        self.mainPanel.SetBackgroundColour(wx.WHITE)
        self.gauge1 = PG.PyGauge(self.mainPanel, -1, size=(100,25),style=wx.GA_HORIZONTAL)
        self.gauge1.SetValue(0)
        self.gauge1.SetBackgroundColour(wx.WHITE)
        self.gauge1.SetBarColor(wx.RED)
        self.gauge1.SetBorderColor(wx.BLACK)
        self.DoLayout()

    def DoLayout(self):
        frameSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.gauge1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 20)
        self.mainPanel.SetSizer(mainSizer)
        mainSizer.Layout()
        frameSizer.Add(self.mainPanel, 1, wx.EXPAND)
        self.SetSizer(frameSizer)
        frameSizer.Layout()


    def OnStartProgress(self, elapsedchoice=True, cancelchoice=True, proportion=20, steps=50):
        style = wx.PD_APP_MODAL
        if elapsedchoice:
            style |= wx.PD_ELAPSED_TIME
        if cancelchoice:
            style |= wx.PD_CAN_ABORT

        dlg = PP.PyProgress(None, -1, "PyProgress Example",
                            "An Informative Message",
                            agwStyle=style)

        backcol = wx.WHITE
        firstcol = wx.WHITE
        secondcol = wx.BLUE

        dlg.SetGaugeProportion(proportion/100.0)
        dlg.SetGaugeSteps(steps)
        dlg.SetGaugeBackground(backcol)
        dlg.SetFirstGradientColour(firstcol)
        dlg.SetSecondGradientColour(secondcol)
        max = 400
        keepGoing = True
        count = 0
        while keepGoing and count < max:
            count += 1
            wx.MilliSleep(30)
            if count >= max / 2:
                keepGoing = dlg.UpdatePulse("Half-time!")
            else:
                keepGoing = dlg.UpdatePulse()
        dlg.Destroy()
        wx.SafeYield()
        wx.GetApp().GetTopWindow().Raise()
        
