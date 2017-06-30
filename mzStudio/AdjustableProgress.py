import wx

try:
    from agw import pygauge as PG
except ImportError: # if it's not there locally, try the wxPython lib.
    try:
        import wx.lib.agw.pygauge as PG
    except:
        raise Exception("This demo requires wxPython version greater than 2.9.0.0")

class PyGaugeDemoW(wx.PyWindow):  #(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1,30), color=wx.GREEN)

    def __init__(self, panel, id=wx.ID_ANY, pos=(550, 5), size=(-1,30), color=wx.GREEN, parent=None):  #(self, parent, id, pos, size, style=wx.BORDER_NONE)
        self.parent=parent
        wx.PyWindow.__init__(self, panel , id, pos, size, style=wx.BORDER_NONE)
        #self.mainPanel = wx.Panel(self, -1)
        #self.mainPanel.SetBackgroundColour(wx.WHITE)
        self.gauge1 = PG.PyGauge(panel, -1, pos=pos, size=(150,15),style=wx.GA_HORIZONTAL)
        self.gauge1.SetValue(0)
        self.gauge1.SetBackgroundColour(wx.WHITE)
        self.gauge1.SetBarColor(wx.RED)
        self.gauge1.SetBorderColor(wx.BLACK)
        #self.DoLayout()

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
