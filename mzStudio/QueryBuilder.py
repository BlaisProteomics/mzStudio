__author__ = 'Scott Ficarro'
__version__ = '1.0'


import multiplierz.mzAPI
import multiplierz.mzReport as mzReport
import wx
import subprocess
import multiplierz.mzReport.mzSpreadsheet as mzSpreadsheet
import collections
import os
import sys
import re
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('.') + '\\Extraction')
import shutil
import multiplierz.mzTools as mzTools

from collections import defaultdict

import mz_workbench.mz_core as mz_core
from multiplierz.mzAPI.raw import mzFile

#print sys.path
#print os.path.abspath(os.getcwd())
sys.path.append(".")

import glob
import sqlite3 as sql
import csv
import pylab
#import win32com.client
import mz_workbench.protein_core as protein_core
import cPickle

class QueryBuilder(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self,parent,id, 'BlaisPepCalc', size =(800,100), pos = (50,50))
        self.panel = wx.Panel(self)
        self.query = wx.TextCtrl(self.panel, -1, "", size = (600,20), pos=(0,0))
        self.btn = wx.Button(self.panel, -1, "->", pos=(620,0), size=(20,20))
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.btn)
        self.canned = wx.ComboBox(self.panel, -1, "", size = (600,20), pos=(0,25), choices=['select * from peptides;'])
        self.builder = wx.ComboBox(self.panel, -1, "", size=(600, 20),pos=(0, 50), choices=[
            'select * from peptides where',
            'select * from peptides where "Protein Description" like "%oligo%" order by "Peptide Score" desc;',
            'select * from peptides where "Protein Description" like "%oligo%" and "Variable Modifications" like "%Phospho%" order by "Peptide Score" desc;'
            'like "%Phospho%"',
            'order by',
            '"Variable Modifications"',
            '"Peptide Score"',
            '"FDR"',
            '"Gene Name"'
        ])
        self.Bind(wx.EVT_COMBOBOX, self.Build, self.builder)
        self.Bind(wx.EVT_COMBOBOX, self.SendCanned, self.canned)

    def OnClick(self, event):
        self.parent.query.SetValue(self.query.GetValue())

    def Build(self, event):
        self.query.SetValue(self.query.GetValue()+self.builder.GetValue())

    def SendCanned(self, event):
        self.parent.query.SetValue(self.canned.GetValue())

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = QueryBuilder(parent=None, id=-1)
    frame.Show()
    app.MainLoop()
