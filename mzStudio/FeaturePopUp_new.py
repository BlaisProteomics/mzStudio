import wx
import wx.grid
#import wx.ScrolledWindow as scrollpanel

from multiplierz.mgf import standard_title_parse
from multiplierz.internalAlgorithms import collectByCriterion

ms1_grid_cols = ['MS1 Scan', 'Intensity']
ms2_grid_cols = ['MS2 Scan', 'Peptide Score']


def getScanFromPsm(psm):
    desc = psm['Spectrum Description']
    if 'MultiplierzMGF' in desc:
        return standard_title_parse(desc)['scan']
    else:
        return desc.split('.')[1]

class FeaturePopUp(wx.Panel):
    def __init__(self, parent, idn, featureIndex, feature, drawPanel, psms = []):      
        wx.Panel.__init__(self, parent, idn, size = (300, -1)) #name = 'Feature %s' % featureIndex,
                                   #style = wx.VSCROLL)
        self.parent = parent
        self.feature = feature
        self.featureIndex = featureIndex
        self.psms = psms
        self.drawPanel = drawPanel # For calling jump to scan functions.
        
        if psms:
            psm = psms[0]        
            peptideDescription = '%s\n%s\nCharge %s\n' % (psm['Peptide Sequence'],
                                                 psm['Variable Modifications'],
                                                 psm['Charge'])
            if any([x in psm for x in ['GeneName', 'gene_symbols']]):
                geneDescription = [psm[x] for x in ['GeneName', 'gene_symbols'] if x in psm][0]
            else:
                geneDescription = 'No Gene Data'
        else:
            peptideDescription = 'No ID'
            geneDescription = ''
        
        ms1_data = sorted([(s, x[0][1]) for s, x in feature.regions])
        ms2_data = sorted([(k, v[0]['Peptide Score']) for k, v in
                           collectByCriterion(psms, getScanFromPsm).items()])
        #ms2_data = [(getScanFromPsm(x), x['Peptide Score']) for x in psms]
        
        panel = wx.Panel(self, -1)
        #panel = self
        peptideText = wx.StaticText(panel, -1, peptideDescription, style = wx.EXPAND)
        geneText = wx.StaticText(panel, -1, geneDescription, style = wx.EXPAND)
        
        self.ms1Grid = wx.grid.Grid(panel, -1, style = wx.EXPAND)
        self.ms1Grid.CreateGrid(len(ms1_data),len(ms1_grid_cols))     
        for i, colname in enumerate(ms1_grid_cols):
            self.ms1Grid.SetColLabelValue(i, colname)
        for i, (scan, intensity) in enumerate(ms1_data):
            self.ms1Grid.SetCellValue(i, 0, str(scan))
            self.ms1Grid.SetCellValue(i, 1, str(intensity))
            
        self.ms2Grid = wx.grid.Grid(panel, -1, style = wx.EXPAND)
        self.ms2Grid.CreateGrid(len(ms2_data), len(ms2_grid_cols))
 
        for i, colname in enumerate(ms2_grid_cols):
            self.ms2Grid.SetColLabelValue(i, colname)
        for i, (scan, score) in enumerate(ms2_data):
            self.ms2Grid.SetCellValue(i, 0, str(scan))
            self.ms2Grid.SetCellValue(i, 1, str(score))
        
        pw, ph = self.parent.GetSize()
        self.ms1Grid.SetMaxSize(wx.Size(-1, ph / 3))
        self.ms2Grid.SetMaxSize(wx.Size(-1, ph / 3))
        
        self.xicButton = wx.Button(self, -1, 'XIC')        
        self.bpcButton = wx.Button(self, -1, 'PepCalc')
        self.closeButton = wx.Button(self, -1, "Close", style = wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.triggerXIC, self.xicButton)
        self.Bind(wx.EVT_BUTTON, self.triggerBPC, self.bpcButton)
        self.Bind(wx.EVT_BUTTON, self.onClose, self.closeButton)
        
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.goToScan, self.ms1Grid)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.goToScan, self.ms2Grid)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.goToScan, self.ms1Grid)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.goToScan, self.ms2Grid)
        if not self.psms:
            self.bpcButton.Enable(False)
        
        gbs = wx.GridBagSizer()
        gbs.Add(peptideText, (0, 0), flag = wx.ALIGN_LEFT)
        gbs.Add(geneText, (1, 0), flag = wx.ALIGN_LEFT)
        gbs.Add(self.ms1Grid, (3, 0), span = (3, 3))#, flag = wx.EXPAND | wx.ALL)
        gbs.Add(self.ms2Grid, (7, 0), span = (3, 3))#, flag = wx.EXPAND | wx.ALL)
        gbs.Add(self.xicButton, (11, 0))
        gbs.Add(self.bpcButton, (11, 2))
        gbs.Add(self.closeButton, (13, 0), span = (1, 2))
        
        overbox = wx.BoxSizer()
        overbox.Add(gbs, 1, wx.ALL, 20)
        
        panel.SetSizerAndFit(overbox)
        
        self.ms1Grid.SetRowLabelSize(20)
        colsize = (self.ms1Grid.GetSize()[0] - 20) / 2           
        for i, colname in enumerate(ms1_grid_cols):
            self.ms1Grid.SetColSize(i, colsize)        
        self.ms2Grid.SetRowLabelSize(20)
        colsize = (self.ms2Grid.GetSize()[0] - 20) / 2        
        for i, colname in enumerate(ms2_grid_cols):
            self.ms2Grid.SetColSize(i, colsize)    
        
        self.Bind(wx.EVT_SIZE, self.onSize)
        
    def onSize(self, event):
        pw, ph = self.parent.GetSize()
        self.ms1Grid.SetMaxSize(wx.Size(-1, ph / 3))
        self.ms2Grid.SetMaxSize(wx.Size(-1, ph / 3))
        # This is still not ideal!
        
    def triggerXIC(self, event):
        pass
    def triggerBPC(self, event):
        pass
    
    def goToScan(self, event):
        row = event.GetRow()
        grid = event.GetEventObject()
        scanNum = int(grid.GetCellValue(row, 0))
        
        active_file = self.drawPanel.msdb.active_file
        self.drawPanel.msdb.set_scan(scanNum, active_file)
        self.drawPanel.msdb.build_current_ID(self.drawPanel.msdb.Display_ID[active_file],
                                             scanNum)
        self.drawPanel.Window.UpdateDrawing()
        self.drawPanel.Refresh()
        
        event.Skip()
    
    def onClose(self, event):
        self.Close(True)
        
        


#if __name__ == '__main__':
    #app = wx.App()
    #foo = FeaturePopUp(None, -1, 1000, )