import wx



class TextSpectrumDialog(wx.Dialog):
    def __init__(self, parent = None, data = None, scan_title = None):
        assert data, "No scan data!"
        super(TextSpectrumDialog, self).__init__(parent, title = scan_title,
                                                 size = (300, 600))
        
        scanlines = []
        for pt in data:
            scanlines.append("%.6f\t%.6f" % pt[:2])
        scantext = '\n'.join(scanlines)
        
        panel = wx.Panel(self, -1, style = wx.EXPAND)
        box = wx.BoxSizer()
        self.display = wx.TextCtrl(panel, -1, scantext,
                                   style = wx.TE_MULTILINE | wx.TE_READONLY)
        box.Add(self.display, 1, wx.ALL | wx.EXPAND, 2)
        panel.SetSizerAndFit(box)
        
        self.Show()
        
        




if __name__ == '__main__':
    testdata = [(1,2),(3,4),(5,6)]
    app = wx.App(0)
    foo = TextSpectrumDialog(None, testdata, 'Foobar')
    foo.ShowModal()
    app.MainLoop()