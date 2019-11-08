# Settings page

import wx
import mzAtomicYardstick

'''

Make sure the new setting is added to dictionary in OnUpdate() funciton.
Make sure you add your settings to mzStudio.py in SaveSettings() function.


'''



class Page(wx.Panel):
    def __init__(self, parent):
        panel = wx.Panel.__init__(self, parent)



class YardstickSettings(Page):
    def __init__(self, parent, settings):
        Page.__init__(self, parent)
        
        topLabel = wx.StaticText(self, -1, "Calculate Mass Types:")
        self.aminoCheck = wx.CheckBox(self, -1, "Oligopeptides")
        self.chnopsCheck = wx.CheckBox(self, -1, "CHNOPS Formulae")
        chargeLabel = wx.StaticText(self, -1, "Charge States:")
        modLabel = wx.StaticText(self, -1, "Peptide PTMs")
        self.chargeStates = wx.CheckListBox(self, -1, choices = ["+1", "+2", "+3"])
        self.modStates = wx.CheckListBox(self, -1,
                                         choices = [x for x in 
                                                    mzAtomicYardstick.mod_mass_lookup.keys()
                                                    if x])
        
        gbs = wx.GridBagSizer(10, 10)
        gbs.Add(topLabel, (0, 1))
        gbs.Add(self.aminoCheck, (1, 1))
        gbs.Add(self.chnopsCheck, (1, 2))
        gbs.Add(wx.StaticLine(self, -1, style = wx.LI_HORIZONTAL), (2, 1), span = (1, 2), flag = wx.EXPAND)
        gbs.Add(chargeLabel, (3, 1), flag = wx.ALIGN_LEFT)
        gbs.Add(modLabel, (3, 2), flag = wx.ALIGN_RIGHT)
        gbs.Add(self.chargeStates, (4, 1))
        gbs.Add(self.modStates, (4, 2), flag = wx.ALIGN_RIGHT)
        
        gbs.AddGrowableCol(0)
        gbs.AddGrowableCol(1)
        
        overbox = wx.BoxSizer()
        overbox.Add(gbs, 0, flag = wx.ALL, border = 30)
        
        self.SetSizerAndFit(overbox)
        
        get_AAs, get_CHNOPS, get_charges, get_mods = settings
        self.aminoCheck.SetValue(get_AAs)
        self.chnopsCheck.SetValue(get_CHNOPS)
        self.chargeStates.SetCheckedStrings(get_charges)
        self.modStates.SetCheckedStrings(get_mods)
        

    def GetValues(self):
        get_AAs = self.aminoCheck.GetValue()
        get_CHNOPS = self.chnopsCheck.GetValue()
        get_charges = self.chargeStates.GetCheckedStrings()
        get_mods = self.modStates.GetCheckedStrings()
        return get_AAs, get_CHNOPS, get_charges, get_mods


class SettingsFrame(wx.Frame):
    def __init__(self,parent,settings):
        self.settings = settings
        self.parent = parent
        wx.Frame.__init__(self, parent, -1, "Settings", size=(475,675))
        self.panel = wx.Panel(self, -1)
        nb = wx.Notebook(self.panel, size=(450,585), pos= (10,10))
        self.page_general = Page(nb)
        nb.AddPage(self.page_general, "General")   
        self.page_thermo = Page(nb)
        nb.AddPage(self.page_thermo, "Thresholds") 
        self.page_yardstick = YardstickSettings(nb, settings['yardstick_settings'])
        nb.AddPage(self.page_yardstick, "Yardstick")
        #self.page_abi = Page(nb)
        #nb.AddPage(self.page_abi, "ABI")   
        #self.page_display = Page(nb)
        #nb.AddPage(self.page_display, "Display")
    
        self.ToggleWindowStyle(wx.STAY_ON_TOP)
        try:
            self.createLabels()
            self.createTextBoxes()
            self.createComboBoxes()
            self.createButtons()
        except:
            pass
        #self.page_abi.Hide()
        #self.page_display.Hide()
        
        
    def LabelData(self):
        return (("Centroid Profile Data", (10, 10), (100,30),self.page_general), ("Multifile Report", (230, 10), (60,30),self.page_general),
                ("Label Threshold", (10, 10), (100,20),self.page_thermo), ("Ion label tolerance", (230, 10), (60,30),self.page_thermo),
                ("Min Charge to Label", (10, 50), (100,30),self.page_general), ("Label Peaks", (230, 50), (60,30),self.page_general),
                ("Max Charge to Label", (10, 90), (100,30),self.page_general), ("Area Algorithm", (230, 90), (60,30),self.page_general),
                ("Show resolution", (10, 130), (100,20),self.page_general), #("Max # Peaks to label", (10, 10), (100,20),self.page_thermo),
                ("Main Font Size", (10, 170), (100,20),self.page_general),
                ("Main Font", (10, 210), (100,20),self.page_general),
                ("Main Font Style", (10, 250), (100,20),self.page_general),
                ("Main Font Weight", (10, 290), (100,20),self.page_general),
                ("Main Font Face", (10, 330), (100,20),self.page_general),
                ("Main Font Color", (10, 370), (100,20),self.page_general),
                ("Line Color", (10, 410), (100,20),self.page_general),
                ("Line Width", (10, 450), (100,20),self.page_general),
                ("Draw Centroid", (10, 490), (100,20),self.page_general),
                ("Search Algorithm", (10, 530), (100,20),self.page_general),
                
                #("Centroiding Algorithm", (10, 10), (100,45),self.page_abi),
                #("Eliminate Noise", (10, 50), (100,20),self.page_abi),
                #("Step Length", (10, 90), (100,20),self.page_abi),
                #("Peak Min", (10, 130), (100,20),self.page_abi),
                #("Threshold", (10, 170), (100,20),self.page_abi),
                                
                #("Space", (10, 10), (100,20),self.page_display),
                #("Inter-raw space", (10, 50), (100,20),self.page_display),
                #("y margin", (10, 90), (100,20),self.page_display),
                #("Total xic height", (10, 130), (100,20),self.page_display),
                #("Total spec height", (10, 170), (100,20),self.page_display),
                #("Inter-axis factor", (10, 210), (100,20),self.page_display),
                #("Inter-xic space", (10, 250), (100,20),self.page_display),
                #("Spec Indent", (10, 290), (100,20),self.page_display),
                #("Spec Width", (10, 330), (100,20),self.page_display),
                #("RIC Spec Indent", (10, 370), (100,20),self.page_display),
                #("RIC Spec Width", (10, 410), (100,20),self.page_display),
                                
                )       
        
    def createLabels(self):
        for eachLabel, labelPos, labelSize, eachPanel in self.LabelData():
            label = self.MakeOneLabel(eachLabel, labelPos, labelSize, eachPanel)    
            
    def MakeOneLabel(self, label, labelPos, labelSize, eachPanel):        
        label = wx.StaticText(eachPanel, -1, label, pos=labelPos, size=labelSize, name =label)
        return label    
    
    def TextBoxData(self):
        return ((str(self.settings['min_cg']), (110,50), (50,20), "min_cg",self.page_general),
                (str(self.settings['max_cg']), (110,90), (50,20), "max_cg",self.page_general),
                (str(self.settings["label_threshold"]['Thermo']), (140,10), (50,20), "Thermo_label_threshold",self.page_thermo), (str(self.settings["ionLabelThresh"]), (320,10), (50,20), "ionLabelThresh",self.page_thermo),
                (str(self.settings['line color']), (110,410), (50,20), "line color",self.page_general),
                (str(self.settings['line width']), (110,450), (50,20), "line width",self.page_general),
                
                #(str(self.settings['step_length']), (110,90), (50,20), "step_length",self.page_abi),
                #(str(self.settings['peak_min']), (110,130), (50,20), "peak_min",self.page_abi),
                #(str(self.settings['threshold_cent_abi']), (110,170), (50,20), "threshold_cent_abi",self.page_abi),
                
                #(str(self.settings['space']), (110,10), (50,20), "space",self.page_display),
                #(str(self.settings['inter_raw_space']), (110,50), (50,20), "inter_raw_space",self.page_display),
                #(str(self.settings['y_marg']), (110,90), (50,20), "y_marg",self.page_display),
                #(str(self.settings['total_xic_height']), (110,130), (50,20), "total_height",self.page_display), 
                #(str(self.settings['total_spec_height']), (110,170), (50,20), "total_height",self.page_display), 
                #(str(self.settings['inter_axis_factor']), (110,210), (50,20), "inter_axis_factor",self.page_display),
                #(str(self.settings['inter_xic_space']), (110,250), (50,20), "inter_xic_space",self.page_display),
                #(str(self.settings['spec_indent']), (110,290), (50,20), "spec_indent",self.page_display),
                #(str(self.settings['spec_width']), (110,330), (50,20), "spec_width",self.page_display), 
                #(str(self.settings['ric_spec_indent']), (110,370), (50,20), "ric_spec_indent",self.page_display),
                #(str(self.settings['ric_spec_width']), (110,410), (50,20), "ric_spec_width",self.page_display),
                               
                )          
    
    def createTextBoxes(self):
        for eachLabel, boxPos, boxSize, eachName, eachPanel in self.TextBoxData():
            TextBox = self.MakeOneTextBox(eachLabel, boxSize, boxPos, eachName, eachPanel)    
    
    def MakeOneTextBox(self, eachLabel, boxSize, boxPos, eachName, eachPanel):
        textBox = wx.TextCtrl(eachPanel, -1, eachLabel, pos = boxPos, size=boxSize, name = eachName)
        return textBox    

    def ComboBoxData(self):
        return (('viewCentroid', (110, 10), (100,20), ["True","False"], ["True","False"].index(str(self.settings['viewCentroid'])), self.page_general),
                ('multiFileOption', (320, 10), (100,20), ["LOAD ALL","SEQUENTIAL"], ["LOAD ALL","SEQUENTIAL"].index(str(self.settings['multiFileOption'])), self.page_general),
                ('labelPeaks', (320, 50), (100,20), ["True","False"], ["True","False"].index(str(self.settings['labelPeaks'])), self.page_general),
                ('areaCalcOption', (320, 90), (100,20), ["SUM","GUASSIAN"], ["SUM","GUASSIAN"].index(str(self.settings['areaCalcOption'])), self.page_general),
                ('label_res', (110, 130), (100,20), ["True","False"], ["True","False"].index(str(self.settings['label_res'])), self.page_general),
               ('main_font_size', (110, 170), (100,20), ["8", "9", "10", "12"], ["8", "9", "10", "12"].index(str(self.settings['mainfont']['size'])), self.page_general),
               ('main_font_font', (110, 210), (100,20), ["ROMAN", "SWISS"], ["ROMAN", "SWISS"].index(str(self.settings['mainfont']['font'])), self.page_general),
               ('main_font_style', (110, 250), (100,20), ["NORMAL"], ["NORMAL"].index(str(self.settings['mainfont']['style'])), self.page_general),
               ('main_font_weight', (110, 290), (100,20), ["BOLD"], ["BOLD"].index(str(self.settings['mainfont']['weight'])), self.page_general),               
               ('main_font_face', (110, 330), (100,20), ["Times New Roman", "Arial", "Bodoni MT Black"], ["Times New Roman", "Arial", "Bodoni MT Black"].index(str(self.settings['mainfont']['face'])), self.page_general),
               ('main_font_color', (110, 370), (100,20), ["BLACK", "RED"], ["BLACK", "RED"].index(str(self.settings['mainfont']['color'])), self.page_general),               
               ('drawCentroid', (110, 490), (100,20), ["True","False"], ["True","False"].index(str(self.settings['drawCentroid'])), self.page_general),
               #('line color', (110, 410), (100,20), ["BLACK", "RED", "BLUE","YELLOW","MAGENTA"], ["BLACK", "RED", "BLUE","YELLOW","MAGENTA"].index(self.settings['line color']).GetAsString(wx.C2S_NAME), self.page_general),               
               #('line width', (110, 370), (100,20), ["1", "2", "3"], ["1", "2", "3"].index(str(self.settings['line width'])), self.page_general),               
               
               #('abi_centroid', (110, 10), (100,20), ["old","new"], ["old","new"].index(str(self.settings['abi_centroid'])), self.page_abi),
               #('eliminate_noise', (110, 50), (100,20), ["True","False"], ["True","False"].index(str(self.settings['eliminate_noise'])), self.page_abi), 
               ('searchAlgorithm', (110, 530), (100,20), ["Mascot","Comet","X!Tandem"], ["Mascot", "Comet","X!Tandem"].index(str(self.settings['searchAlgorithm'])), self.page_general),
                )    
    
    def createComboBoxes(self):
        for eachName, eachPos, eachSize, eachList, eachInit, eachPanel in self.ComboBoxData():
            ComboBox = self.BuildOneComboBox(eachName, eachPos, eachSize, eachList, eachInit, eachPanel)

    def BuildOneComboBox(self, eachName, eachPos, eachSize, eachList, eachInit, eachPanel):
        ComboBox = wx.ComboBox(eachPanel, -1, size=eachSize, pos=eachPos, name=eachName, value=eachList[eachInit], choices=eachList)
        return ComboBox    
    
    def ButtonData(self):
        return (("OK", self.OnUpdate, (10, 600), (120,25), self.panel),
                #("Make mgf", self.OnCmd1, (1140, 30), (120,25), self.page_general)
                )   
    
    def createButtons(self):
        for eachLabel, eachHandler, pos, size, eachPanel in self.ButtonData():
            button = self.BuildOneButton(eachLabel, eachHandler, pos, size, eachPanel)    
            
    def BuildOneButton(self, label, handler, pos, size, eachPanel):
        button = wx.Button(eachPanel, -1, label, pos, size)
        self.Bind(wx.EVT_BUTTON, handler, button)
        return button    
    
    def OnUpdate(self, event):
        active = self.parent.msdb.active_file
        currentFile = self.parent.msdb.files[self.parent.msdb.Display_ID[active]]        
        currentFile.viewCentroid = True if self.FindWindowByName("viewCentroid").GetValue() == 'True' else False
        currentFile.settings['labelPeaks'] = True if self.FindWindowByName("labelPeaks").GetValue() == 'True' else False
        currentFile.settings['multiFileOption'] = self.FindWindowByName("multiFileOption").GetValue()
        currentFile.settings['areaCalcOption'] = self.FindWindowByName("areaCalcOption").GetValue()
        currentFile.settings['ionLabelThresh'] = float(self.FindWindowByName("ionLabelThresh").GetValue())
                                                                          
        currentFile.drawCentroid = True if self.FindWindowByName("drawCentroid").GetValue() == 'True' else False
        currentFile.settings['searchAlgorithm'] = self.FindWindowByName("searchAlgorithm").GetValue()
        currentFile.settings['viewCentroid']=currentFile.viewCentroid
        currentFile.settings['drawCentroid']=currentFile.drawCentroid
        currentFile.label_res = True if self.FindWindowByName("label_res").GetValue() == 'True' else False
        currentFile.settings['label_res']=currentFile.label_res        
        self.parent.msdb.set_scan(currentFile.scanNum, self.parent.msdb.active_file)
        currentFile.settings['min_cg'] = int(self.FindWindowByName("min_cg").GetValue())
        currentFile.settings['max_cg'] = int(self.FindWindowByName("max_cg").GetValue())
        
        currentFile.settings["label_threshold"]['Thermo'] = float(self.FindWindowByName("Thermo_label_threshold").GetValue())
        
        #currentFile.settings['space'] = int(self.FindWindowByName("space").GetValue())
        #currentFile.settings['inter_raw_space'] = int(self.FindWindowByName("inter_raw_space").GetValue())        
        #currentFile.settings['y_marg'] = int(self.FindWindowByName("y_marg").GetValue())
        #currentFile.settings['total_height'] = int(self.FindWindowByName("total_height").GetValue())   
        #currentFile.settings['inter_axis_factor'] = int(self.FindWindowByName("inter_axis_factor").GetValue())
        #currentFile.settings['inter_xic_space'] = int(self.FindWindowByName("inter_xic_space").GetValue())        
        #currentFile.settings['spec_indent'] = int(self.FindWindowByName("spec_indent").GetValue())
        #currentFile.settings['spec_width'] = int(self.FindWindowByName("spec_width").GetValue()) 
        #currentFile.settings['ric_spec_indent'] = int(self.FindWindowByName("ric_spec_indent").GetValue())
        #currentFile.settings['ric_spec_width'] = int(self.FindWindowByName("ric_spec_width").GetValue())                     
        
        #currentFile.settings['abi_centroid'] = self.FindWindowByName("abi_centroid").GetValue()
        #currentFile.settings['eliminate_noise'] = bool(self.FindWindowByName("eliminate_noise").GetValue())
        #currentFile.settings['step_length'] = float(self.FindWindowByName("step_length").GetValue())
        #currentFile.settings['peak_min'] = int(self.FindWindowByName("peak_min").GetValue())
        #currentFile.settings['threshold_cent_abi'] = int(self.FindWindowByName("threshold_cent_abi").GetValue())
        
        currentFile.settings['mainfont']['size'] = int(self.FindWindowByName("main_font_size").GetValue())
        currentFile.settings['mainfont']['font'] = self.FindWindowByName("main_font_font").GetValue()
        currentFile.settings['mainfont']['face'] = self.FindWindowByName("main_font_face").GetValue()
        currentFile.settings['mainfont']['style'] = self.FindWindowByName("main_font_style").GetValue()
        currentFile.settings['mainfont']['weight'] = self.FindWindowByName("main_font_weight").GetValue()
        currentFile.settings['mainfont']['color'] = self.FindWindowByName("main_font_color").GetValue()
        colortxt = self.FindWindowByName("line color").GetValue().replace('[','').replace(']','').split(',')
        color = [int(x.strip()) for x in colortxt]
        currentFile.settings['line color'] = color
        currentFile.settings['line width'] = float(self.FindWindowByName("line width").GetValue())
        sz = str(currentFile.settings['mainfont']['size'])
        font = currentFile.settings['mainfont']['font']
        style = currentFile.settings['mainfont']['style']
        wt = currentFile.settings['mainfont']['weight']
        face = currentFile.settings['mainfont']['face']
        selfont = 'wx.Font('+ sz + ', wx.' + font + ', wx.' + style +', wx.' + wt + ', False, "' + face + '")'
        #print selfont
        currentFile.settings['font1'] = eval(selfont)        
        if currentFile.vendor=='Thermo':
            self.parent.msdb.build_current_ID(self.parent.msdb.Display_ID[self.parent.msdb.active_file], currentFile.scanNum)
        #if currentFile.vendor=='ABI':
        #    self.parent.msdb.build_current_ID(self.parent.msdb.Display_ID[self.parent.msdb.active_file], (currentFile.scanNum, currentFile.experiment), 'ABI')        
        
        yardstick_values = self.page_yardstick.GetValues()
        if currentFile.settings['yardstick_settings'] != yardstick_values:
            mzAtomicYardstick.initialize_masses(*yardstick_values)
            currentFile.settings['yardstick_settings'] = yardstick_values
        
        
        
        self.parent.Window.UpdateDrawing()
        self.parent.Refresh()        
        
        self.parent.msdb.SaveSettings(currentFile)
        self.Destroy()
    
    
if __name__ == '__main__':
    class FakeNews(str):
        def __init__(self):
            pass
        def __getitem__(self, key):
            return FakeNews()
        
    app = wx.App(0)
    foo = SettingsFrame(None, FakeNews())
    foo.Show()
    app.MainLoop()
    