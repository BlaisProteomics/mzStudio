import wx
import imp
from multiplierz.mzGUI_standalone import file_chooser


intro_text = """
You may use Python functions to filter or enhance spectra in the viewer;
select a Python module containing a function process_spectrum() that takes
a list of (mz, intensity) tuples representing spectrum data and returns
a new list of tuples representing the processed spectrum.
"""


class ProcessorDialog(wx.Dialog):
    def __init__(self, parent = None, selectedFile = ''):
        super(ProcessorDialog, self).__init__(parent, title = 'Spectrum Processor',
                                              size = (600, 300))
        
        panel = wx.Panel(self, -1, style = wx.EXPAND)
        
        introText = wx.StaticText(panel, -1, intro_text)

        self.selectorLabel = wx.StaticText(panel, -1, "Select File")
        self.selectorBox = wx.TextCtrl(panel, -1, selectedFile)
        self.selectorButton = wx.Button(panel, -1, "Browse")
        self.loadButton = wx.Button(panel, -1, "Load")
        self.Bind(wx.EVT_BUTTON, self.browseForFile, self.selectorButton)
        self.Bind(wx.EVT_BUTTON, self.load, self.loadButton)
        
        #windowSplit = wx.StaticLine(panel, -1, style = wx.LI_HORIZONTAL)

        self.okButton = wx.Button(panel, -1, "OK")
        self.cancelButton = wx.Button(panel, -1, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.onOK, self.okButton)
        self.Bind(wx.EVT_BUTTON, self.close, self.cancelButton)
        
        gbs = wx.GridBagSizer()
        
        gbs.Add(introText, (0, 0), span = (2, 4))
        
        gbs.Add(self.selectorLabel, (2, 0), flag = wx.ALIGN_LEFT)
        gbs.Add(self.selectorBox, (3, 0), span = (1, 3), flag = wx.ALIGN_LEFT | wx.EXPAND)
        gbs.Add(self.selectorButton, (3, 3), flag = wx.ALIGN_LEFT)
        gbs.Add(self.loadButton, (4, 3), flag = wx.ALIGN_LEFT)
        
        #gbs.Add(windowSplit, (5, 0), span = (1, 4), flag = wx.EXPAND)
        
        gbs.Add(self.okButton, (7, 2), flag = wx.ALIGN_RIGHT)
        gbs.Add(self.cancelButton, (7, 3), flag = wx.ALIGN_LEFT)
    
        gbs.AddGrowableRow(1)
        gbs.AddGrowableRow(5)
        gbs.AddGrowableCol(2)
    
        overbox = wx.BoxSizer()
        overbox.Add(gbs, 1, wx.ALL | wx.EXPAND, 20)
        panel.SetSizerAndFit(overbox)
        
        self.filename = ''
        self.function = None
        self.mod = None
        
        self.success = None
    
    def browseForFile(self, event):
        filename = file_chooser(title = 'Select Python module:', mode = 'r',
                                wildcard = '*.py')
        
        if not filename:
            return
        self.selectorBox.SetValue(filename)
        
        self.loadAndCheckFunction(filename)        
        self.filename = filename
        
    def load(self, event):
        if self.selectorBox.GetValue():
            self.filename = self.selectorBox.GetValue()
            self.loadAndCheckFunction(self.filename)
        
    def loadAndCheckFunction(self, filename):
        try:
            mod = imp.load_source('custom_module', filename)
        except Exception as err:
            wx.MessageBox("Could not load script: %s" % err)
            return
        
        self.mod = mod
            
        try:
            assert 'processor_function' in self.mod.__dict__, "processor_function() not defined in chosen file."
            
            testspectrum = [(100.0, 300.0), (500.0, 1000.0), (700.0, 200.0)]
            print "Checking custom processor_function..."
            try:
                returnval = self.mod.processor_function(testspectrum)
            except Exception as err:
                raise AssertionError, "Custom function failed on test spectrum:\n%s" % str(err)
            assert hasattr(returnval, '__iter__'), "proessor_function() return value is not iterable!"
            assert returnval != None, "processor_function() returned None.  (Did you forget a return statement?)"
            assert all([hasattr(x, '__iter__') and len(x) == 2
                        for x in returnval]), 'processor_function() return value is not a list of length-2 iterables!'
            
            print "Custom processor function check successful."
            self.mod = mod
            self.function = mod.processor_function
            self.filename = filename
            
        except AssertionError as err:
            messdog = wx.MessageDialog(self,
                                       'Custom function check failed:\n\n' + repr(err),
                                       'Could not load custom processor function.',
                                       style = wx.OK)
            self.success = False
            messdog.ShowModal()
            messdog.Destroy()
            return      
        
        messdog = wx.MessageDialog(self, 'Custom function loaded and checked successfully.',
                                   'Function loaded.', style = wx.OK)
        self.success = True
        messdog.ShowModal()
        messdog.Destroy()        
        
    #def reloadFunction(self, evt):
        #reload(self.mod)
        #self.function = self.mod.processor_function
    
    
    def onOK(self, event):
        self.isOK = True
        self.EndModal(wx.ID_OK)
        
    def close(self, event):
        self.isOK = False
        self.EndModal(wx.ID_CANCEL)
    
    
    
    
    
    
    
    
if __name__ == '__main__':
    app = wx.App(0)
    foo = ProcessorDialog(None, '', '')
    foo.ShowModal()
    
    app.MainLoop()