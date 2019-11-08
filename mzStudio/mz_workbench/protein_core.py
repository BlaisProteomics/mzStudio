

__author__ = 'Scott'

__version__ = "0.2.3"

__lastRevision__ = "2017-01-3"

'''
extract_gi(filename, sheetname, outfile, gi_sheet_name = 'gi')
    Creates a separate sheet of gi's for pathway pallete input

create_gene_dicts(organism)
    organism = "HUMAN" or "MOUSE"
    returns gi2geneID, gi2geneName, geneID2geneName
    note geneIDs are integers, not strings

match_gene_names(filename, sheet, genelist, output)
    Matches 'GeneName' column to a list (csv format, or list - checks type) and outputs a text file of matches

match_gene_names2xls(filename, sheet, genelist, out_sheet)
    Matches 'GeneName' column to a csv formatted list, outputs list to same xls in sheet out_sheet

match_gene_namesInXLS(filename, sheet, genelist, title)
    Keep everything in one sheet

label_multiplierz_sheet(filename, organism = "HUMAN", sheetname = "Data")
    Adds gene names to a multiplierz sheet

def extract_regulated(filename, uratio, column_header, sheet_name = "Data", trim=True, extreme=False, ext_thresh=0.05, stringent=False)
    Makes separate sheets in a multiplierz file with "regulated" up or down entries
    Mode 1: extreme=False;
        Uses uratio (ratio i.e. 1.5 fold or 2 fold).
        column header should be 'condition X\ condition Y'
        trim should be a very low number i.e. 0.0000000000001 to exclude bogus values
    Mode 2: extreme=True
        Extracts extreme values at threshold (ext_thres)
    If stringent = True, only use protein unique entries

def create_report(filename, peptide_stringency, organism = "HUMAN")
    Makes a protein report

grab_gi (gi, organism)
    Looks up gi from database.  Takes a bit of time as parsing large text file.
    Right now only does human.
    Returns sequence

'''

print "Powered by protein core! Version " + __version__ + ' Last revised: ' + __lastRevision__

#2011-04-10
#Takes list of peptides and proteins and makes new sheets, stringent and inclusive, with gene names and geneIDs

#2011-04-13
#added stringency as argument

#gi to gene
import sqlite3 as sql
import os
import wx
import multiplierz.mzReport as mzReport
from collections import defaultdict
#import multiplierz.genbank as genbank
import re
import csv
import multiplierz.mass_biochem as mzF
import multiplierz.mass_biochem as mzFunctions
#import win32com
import pylab
#import multiplierz.mzTools.mz_image as Image
import collections
import sys
#import protein_base
import Kinase_Matcher
import cPickle
import glob
import multiplierz.mzAPI as mzAPI
import csv
import time

FILES_DIR = os.path.dirname(__file__)

def get_single_file(caption='Select File...', wx_wildcard = "XLS files (*.xls)|*.xls"):
    app = wx.PySimpleApp()
    dlg = wx.FileDialog(None, caption, defaultDir = default_dir, pos = (2,2), wildcard = wx_wildcard)
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetPath()
        dir = dlg.GetDirectory()
    dlg.Destroy()
    return filename, dir

def reduce_mods(remove, varmod):
    '''
    
    remove = any mod containing this text will be removed
    
    varmod = list of variable modifications (MASCOT format)
    
    varmod is split on ";"
    
    '''
    mods = varmod.split(';')
    reduced = ''
    for mod in mods:
        if mod.find(remove) == -1:
            reduced += mod + "; "
    return reduced[:-2].strip()

def create_gene_dicts(organism):
    print "*"
    print "Creating gene dictionaries..."
    gi2geneID = {}
    gi2geneName = {}
    geneID2geneName = {}
    organism = organism.upper()
    if organism in ["HUMAN", "H"]:
        organism = "HUMAN"
    elif organism in ["MOUSE", "M"]:
        organism = "MOUSE"
    if organism == "HUMAN":
        gene_file = os.path.join(FILES_DIR, r'gi2geneid_human.txt')
        file_r = open(gene_file, 'r')
        genes=file_r.readlines()
        for gene in genes:
            line = gene.strip().split('\t')
            gi2geneID["gi|" + line[0]] = int(line[1])
            gi2geneName["gi|" + line[0]] = line[2]
            geneID2geneName[int(line[1])] = line[2]
    elif organism == "MOUSE":
        gene_file = os.path.join(FILES_DIR, r'gi2geneid_mouse.txt')
        file_r = open(gene_file, 'r')
        genes=file_r.readlines()
        for gene in genes:
            line = gene.strip().split('\t')
            gi2geneID[line[0]] = int(line[1])
            gi2geneName[line[0]] = line[2]
    return gi2geneID, gi2geneName, geneID2geneName

def read_gene_list(filename):
    '''
    
    Reads a set of genes (text file) and returns a set
    
    '''
    geneSet = set()
    file_r = open(filename, 'r')
    file_reader = file_r.readlines()
    for line in file_reader:
        geneSet.add(line.strip())  
    return geneSet

def match_gene_namesInXLS(filename, sheet, genelist, title, loosen = [], alt_gene_column = '', drop = []):
    '''
    Filename = Filename in which to match genes
    sheet = Sheet to examine
    genelist = text file with gene names to match; each line is gene name\n
    title = New Column header
    loosen = any name in this list is matched by FIND, not EQUAL
    alt_gene_column = if Gene Names not in GeneName, what column is it in?
    drop = any name in this list is not matched
    '''
    geneSet = set()
    file_r = open(genelist, 'r')
    file = file_r.readlines()
    for line in file:
        geneSet.add(line.strip())

    print geneSet
    print "opening sheet..."
    rdr = mzReport.reader(filename, sheet_name = sheet)
    wtr = mzReport.writer(filename, rdr.columns + [title], sheet_name = sheet)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print str(counter)
        counter += 1
        rowGenes = set()
        if not alt_gene_column:
            genes = row["GeneName"]
        else:
            genes = row[alt_gene_column]
        if not genes:
            genes = "UNR"
        try:
            genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
        except:
            genes = "UNR"
        for gene in genes:
            gene = gene.strip()
            rowGenes.add(gene)
        check = False
        for gene in rowGenes:
            if gene in geneSet:
                check = True
            for member in loosen:
                if gene.startswith(member) > -1:
                    check = True
                    for member in drop:
                        if gene == drop:
                            check = False
        row[title] = check
        wtr.write(row)
    rdr.close()
    wtr.close()

def get_key1_phosphopeptides(filename, sheet, verbose=False):
    '''
    
    Version 0.1 2014-07-09
    Get unique combinations of sequence + phos state (i.e. single phos with same sequence but phosphorylated at different residue are counted only once)
    returns a set
    
    '''
    phosphopeps = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            if verbose:
                print counter
        counter += 1
        desc = row["Protein Description"]
        acc = row["Accession Number"]        
        varmod = row['Variable Modifications']
        if not varmod:
            varmod = ''
        if acc.find("rev_gi") == -1 and desc.find("Marto") == -1 and varmod:
            #print phos
            seq = row['Peptide Sequence']
            phos_sites = CountPhos(varmod)
            key = seq + '|' + str(phos_sites)
            phosphopeps.add(key)
            
    return phosphopeps  

def quick_phosphorylation_site_count(filename, sheet, instrument="Orbi(CID-HCD)"):
    '''
    Uses 1% FLR Threshold (tolerance={"CID":11, "HCD":10})
    '''
    pa = re.compile('.*?[Y](\d+): Phospho')
    MDsites = set()
    UGsites= set()
    sites = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    tolerance={"CID":11, "HCD":10}
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print counter
        counter += 1
        desc = row["Protein Description"]
        acc = row["Accession Number"]
        varmod = row['Variable Modifications']
        if not varmod:
            varmod = ''
        if acc.find("rev_gi") == -1 and desc.find("Marto") == -1 and varmod:
            phos = row["Protein Relative Modifications"]
            #print phos
            phos_sites = pa.findall(phos)
            genes = row["GeneName"]
            genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
            geneSet = set()
            for gene in genes:
                gene = gene.strip()
                geneSet.add(gene)
                for site in phos_sites:
                    sites.add(gene + '|' + site)
            if len(geneSet)==1:
                for site in phos_sites:
                    UGsites.add(gene + '|' + site)
                if instrument=="Orbi(CID-HCD)":
                    MD_threshold = tolerance[row["Scan Type"]]
                try:
                    if float(row["MD Score"].split("-")[len(row["MD Score"].split("-"))-1].strip()) > MD_threshold:
                        for site in phos_sites:
                            MDsites.add(gene + '|' + site)
                except:
                    try:
                        if float(row["MD Score"]) > MD_threshold:
                            for site in phos_sites:
                                MDsites.add(gene + '|' + site)
                    except:
                        pass
    print "---"
    print len(sites)
    print len(UGsites)
    print len(MDsites)



def quick_gene_summary(filename, sheet, unique=False, threshold=0):
    '''
    Version 0.21 2014-08-08
    Use to count genes in a multiplierz sheet.  Expects data manager style gene annotations (column=geneName).
    
    ['PFN1'] or ['HIST1H2BG', 'HIST1H2BD', 'HIST1H2BB', 'HIST1H2BO', 'HIST1H2BK', 'HIST1H2BJ']

    If unique=True, only counts unique genes (i.e. single entry)
    
    If threshold specified, returns only genes mapped by more than (or equal to) threshold peptides.
    '''
    geneSet = set()
    genePeps = defaultdict(set)
    if filename.find('.xls')>-1:
        rdr = mzReport.reader(filename, sheet_name = sheet)
    else:
        rdr = mzReport.reader(filename)
    if not unique:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                genes = row["GeneName"]
                genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
                for gene in genes:
                    gene = gene.strip()
                    geneSet.add(gene)
                    genePeps[gene].add(row['Peptide Sequence'])
    else:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                genes = row["GeneName"]
                if not genes.find(',') > -1:
                    gene = genes.replace('[', '').replace(']','').replace("'","").strip()
                    geneSet.add(gene)
                    genePeps[gene].add(row['Peptide Sequence'])
    rdr.close()
    genes = list(geneSet)
    genes.sort()
    if threshold:
        genes = [x for x in genes if len(genePeps[x])>=threshold]
    return genes

def quick_phospho_to_gene_summary(filename, sheet, unique=False):
    '''
    
    Use to count genes in a multiplierz sheet.  Expects data manager style gene annotations (column=geneName).
    
    ['PFN1'] or ['HIST1H2BG', 'HIST1H2BD', 'HIST1H2BB', 'HIST1H2BO', 'HIST1H2BK', 'HIST1H2BJ']

    If unique=True, only counts unique genes (i.e. single entry)
    
    '''
    geneSet = set()
    if filename.find('.xls')>-1:
        rdr = mzReport.reader(filename, sheet_name = sheet)
    else:
        rdr = mzReport.reader(filename)
    if not unique:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            varmod = row['Variable Modifications']
            if not varmod:
                varmod = ''
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1 and varmod.find("Phospho") > -1:
                genes = row["GeneName"]
                genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
                for gene in genes:
                    gene = gene.strip()
                    geneSet.add(gene)
    else:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            varmod = row['Variable Modifications']
            if not varmod:
                varmod = ''            
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1 and varmod.find("Phospho") > -1:
                genes = row["GeneName"]
                if not genes.find(',') > -1:
                    gene = genes.replace('[', '').replace(']','').replace("'","").strip()
                    geneSet.add(gene)
    rdr.close()
    genes = list(geneSet)
    genes.sort()
    return genes

def quick_protein_summary(filename, sheet, unique=False):
    protSet = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    if not unique:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                prots = acc.split(";")
                for prot in prots:
                    prot = prot.strip()
                    protSet.add(prot)
    else:
        for row in rdr:
            desc = row["Protein Description"]
            acc = row["Accession Number"]
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                prots = acc.split(";")
                if len(prots) == 1:
                    for prot in prots:
                        prot = prot.strip()
                        protSet.add(prot)
    rdr.close()
    prots = list(protSet)
    prots.sort()
    return prots

def quick_kinase_summary(filename, sheet, unique=False):
    kinases = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    if not unique:
        for row in rdr:
            kinase = row["Kinase?"]
            if kinase == True:
                genes = row["GeneName"]
                genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
                for kin in genes:
                    kin = kin.strip()
                    kinases.add(kin)
    else:
        for row in rdr:
            kinase = row["Kinase?"]
            unique = row["Unique"]
            if unique == True and kinase == True:
                gene = row["GeneName"]
                gene = gene.replace('[', '').replace(']','').replace("'","")
                kinases.add(gene)
    rdr.close()
    kinase_list = list(kinases)
    kinase_list.sort()
    return kinase_list

def match_gene_names2xls(filename, sheet, genelist, out_sheet):
    if sheet == out_sheet:
        raise ValueError("Input and output files are the same!  Do not overwrite!")
    geneSet = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    for row in rdr:
        genes = row["GeneName"]
        genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
        for gene in genes:
            gene = gene.strip()
            geneSet.add(gene)
    #print geneSet
    rdr.close()

    csvReader = csv.reader(open(genelist), delimiter=',', quotechar='|')
    SearchSet = set()
    FoundSet = set()
    for i, row in enumerate(csvReader):
        SearchSet.add(row[0])
    wtr = mzReport.writer(filename, ['GeneName'], sheet_name = out_sheet)
    row = {}
    for gene in SearchSet:
        if gene in geneSet:
            print gene
            FoundSet.add(gene)
            row['GeneName'] = gene
            wtr.write(row)
    if not FoundSet:
        print "NONE DETECTED!"
    wtr.close()

def match_gene_names(filename, sheet, genelist, output):
    geneSet = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    for row in rdr:
        genes = row["GeneName"]
        genes = genes.replace('[', '').replace(']','').replace("'","").split(',')
        for gene in genes:
            gene = gene.strip()
            geneSet.add(gene)
    #print geneSet
    rdr.close()
    if isinstance(genelist, list):
        file_w = open(output, 'w')
        for gene in genelist:
            if gene in geneSet:
                print gene
                file_w.write(gene + '\n')
        file_w.close()
    else:
        csvReader = csv.reader(open(genelist), delimiter=',', quotechar='|')
        SearchSet = set()
        FoundSet = set()
        for i, row in enumerate(csvReader):
            SearchSet.add(row[0])
        file_w = open(output, 'w')
        for gene in SearchSet:
            if gene in geneSet:
                print gene
                FoundSet.add(gene)
                file_w.write(gene + '\n')
        if not FoundSet:
            print "NONE DETECTED!"
        file_w.close()

def add_gene_IDs(filename, organism = "HUMAN", sheetname = "Data"):
    desc_bank = {}
    gi2geneID, gi2geneName, geneID2genename = create_gene_dicts(organism)
    inclusive_gi2desc = {}
    inclusive_gi2pep = defaultdict(set)
    stringent_gi2desc = {}
    stringent_gi2pep = defaultdict(set)
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    try:
        wtr = mzReport.writer(filename, rdr.columns + ['GeneID'], sheet_name = sheetname)
    except:
        wtr = mzReport.writer(filename, rdr.columns, sheet_name = sheetname)
    pa = re.compile('(gi\|[0-9]+?)\|')
    pa2 = re.compile('(gi\|[0-9]+)')
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print str(counter)
        counter += 1
        try:
            gi_row = row["Accession Number"]
        except:
            gi_row = row["Accession"]
        gis = gi_row.split(";")
        row_names = []
        genelist = []
        for gi in gis:
            gi = gi.strip()
            id = pa.match(gi)
            if not id:
                print gi
                id = pa2.match(gi)
                if id:
                    print "FOUND!"
            if id:
                try:
                    geneID = gi2geneID[id.groups()[0]]
                except:
                    geneID = 'unresolved: ' + gi
            else:
                geneID = 'NA'
            if geneID not in genelist:
                genelist.append(geneID)
        row['GeneID'] = str(genelist).replace(']','').replace('[','')
        wtr.write(row)
    wtr.close()
    rdr.close()
        
def label_multiplierz_sheet(filename, organism = "HUMAN", sheetname = "Data"):
    desc_bank = {}
    gi2geneID, gi2geneName, geneID2genename = create_gene_dicts(organism)
    inclusive_gi2desc = {}
    inclusive_gi2pep = defaultdict(set)
    stringent_gi2desc = {}
    stringent_gi2pep = defaultdict(set)
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    try:
        wtr = mzReport.writer(filename, rdr.columns + ['GeneName'], sheet_name = sheetname)
    except:
        wtr = mzReport.writer(filename, rdr.columns, sheet_name = sheetname)
    pa = re.compile('(gi\|[0-9]+?)\|')
    pa2 = re.compile('(gi\|[0-9]+)')
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print str(counter)
        counter += 1
        try:
            gi_row = row["Accession Number"]
        except:
            gi_row = row["Accession"]
        gis = gi_row.split(";")
        row_names = []
        genelist = []
        for gi in gis:
            gi = gi.strip()
            id = pa.match(gi)
            if not id:
                print gi
                id = pa2.match(gi)
                if id:
                    print "FOUND!"
            if id:
                try:
                    geneName = gi2geneName[id.groups()[0]]
                except:
                    geneName = 'unresolved: ' + gi
            else:
                geneName = 'NA'
            if geneName not in genelist:
                genelist.append(geneName)
        row['GeneName'] = str(genelist)
        wtr.write(row)
    wtr.close()
    rdr.close()


def annotate_extreme_vals(filename, column_header, trim_val=0, ext_thresh=0.05, output_name = ''):
    '''
    
    This function will read a multiplierz sheet and determine extreme value ratios (ext_thresh/2 on each side).
    column_header should contain untransformed ratios
    Ratios greater than trim value will be accepted (0 means 0 ratios are not considered)
    
    
    '''


    ratio_list = []
    print "Determining boundary values..."
    #------------------------------------------------------------------------------
    # READING RATIOS
    #------------------------------------------------------------------------------
    rdr = mzReport.reader(filename, sheet_name="Data")
    for row in rdr:
        current_ratio = float(row[column_header])
        if current_ratio > trim_val:
            ratio_list.append(current_ratio)

    num_r = len(ratio_list) # number of ratios
    print "RATIOS"
    print num_r
    target = int(float(round(float(ext_thresh) * float(num_r)) - 1)/float(2.0)) #This many values each side meet the extreme value threshold and should pass
    print "BOUNDARIES TARGET"
    print target
    ratio_list.sort()
    lo = ratio_list[int(target)]
    hi = ratio_list[int(num_r-target)]
    print "Ratios..."
    print str(num_r)
    print lo
    print hi
    print target
    print str(num_r-target)
    

def extract_regulated(filename, uratio, column_header, sheetname = "Data", trim=True, extreme=False, ext_thresh=0.05, stringent=False):
    trim_val = 0.00000000001
    if not extreme:
        uratio = float(uratio)
        dratio = float(1)/float(uratio)
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    names = column_header.split('\\')
    if not extreme:
        prefix = ''
        if stringent:
            prefix = 'Stringent '
        upreg_name = prefix + names[0].strip()
        downr_name = prefix + names[1].strip()
        upr = mzReport.writer(filename, columns=rdr.columns, sheet_name = upreg_name)
        dwn = mzReport.writer(filename, columns=rdr.columns, sheet_name = downr_name)
        counter = 0
        for row in rdr:
            try:
                redundancy = row["Accession Number"].count(';')+1
            except:
                redundancy = row["Accession"].count(';')+1
            if counter % 500 == 0:
                print str(counter)
                #print str(float(row[column_header]))
            counter += 1
            if stringent and redundancy == 1 or not stringent:
                try:
                    current_ratio = float(row[column_header])
                    if current_ratio > uratio:
                        upr.write(row)
                    if current_ratio < dratio and current_ratio > trim_val:
                        dwn.write(row)
                except:
                    continue
        upr.close()
        dwn.close()
    else:
        #Determine ratios
        ratio_list = []
        print "Determining boundary values..."
        #------------------------------------------------------------------------------
        # READING RATIOS
        #--------------------------------
        for row in rdr:
            try:
                current_ratio = float(row[column_header])
                if current_ratio > trim_val:
                    ratio_list.append(current_ratio)
            except:
                continue
        num_r = len(ratio_list)
        print "RATIOS"
        print num_r
        target = round(float(ext_thresh) * float(num_r)) - 1
        print "BOUNDARIES TARGET"
        print target
        ratio_list.sort()
        lo = ratio_list[int(target)]
        hi = ratio_list[int(num_r-target)]
        print "Ratios..."
        print str(num_r)
        print lo
        print hi
        print target
        print str(num_r-target)
        prefix = ''
        if stringent:
            prefix = 'Stringent '
        upreg_name = prefix + 'e' + names[0].strip()
        downr_name = prefix + 'e' + names[1].strip()
        upr = mzReport.writer(filename, columns=rdr.columns, sheet_name = upreg_name)
        dwn = mzReport.writer(filename, columns=rdr.columns, sheet_name = downr_name)
        counter = 0
        for row in rdr:
            try:
                redundancy = row["Accession Number"].count(';')+1
            except:
                redundancy = row["Accession"].count(';')+1
            if counter % 500 == 0:
                print str(counter)
                #print str(float(row[column_header]))
            counter += 1
            if stringent and redundancy == 1 or not stringent:
                try:
                    current_ratio = float(row[column_header])
                    if current_ratio >= hi:
                        upr.write(row)
                    if current_ratio <= lo and current_ratio > trim_val:
                        dwn.write(row)
                except:
                    continue
        upr.close()
        dwn.close()


def create_report(filename, peptide_stringency, organism = "HUMAN"):
    desc_bank = {}
    gi2geneID, gi2geneName, geneID2genename = create_gene_dicts(organism)
    inclusive_gi2desc = {}
    inclusive_gi2pep = defaultdict(set)
    stringent_gi2desc = {}
    stringent_gi2pep = defaultdict(set)
    rdr = mzReport.reader(filename, sheet_name = "Data")

    for row in rdr:
        gi_row = row["Accession Number"]
        seq = row["Peptide Sequence"]
        desc_row = row["Protein Description"]
        red = int(row["Protein Redundancy"])
        gis = gi_row.split(";")
        descs = desc_row.split(";")
        if desc_row.find("Marto_Lab") == -1:
            for gi, desc in zip(gis, descs):
                gi = 'gi|' + gi.split("|")[1]
                inclusive_gi2desc[gi] = desc
                inclusive_gi2pep[gi].add(seq)
                desc_bank[gi] = desc
            if red == 1:
                gi = 'gi|' + gis[0].split("|")[1]
                stringent_gi2desc[gi] = descs[0]
                stringent_gi2pep[gi].add(seq)
    rdr.close()
    wtr = mzReport.writer(filename, columns =['accession', 'geneID', 'geneName', 'Description', 'Peptides', 'Number of Peptides'], sheet_name = "Protein Report-Inclusive")
    row = {}

    for gi in inclusive_gi2pep.keys():
        if len(inclusive_gi2pep[gi]) >= peptide_stringency: #At least 2 peptides
            row['accession'] = gi
            row['Description'] = desc_bank[gi]
            row['Number of Peptides'] = len(inclusive_gi2pep[gi])
            try:
                row['geneID'] = gi2geneID[gi]
                row['geneName'] = gi2geneName[gi].strip()
            except:
                #gb = genbank.download_genbank(gi)
                #row["geneName"] = gb.gene
                #line = 'select * from "gene info" where "Gene Symbol" = "' + str(gb.gene) + '";'
                #c.execute(line)
                #name = c.fetchone()[2]
                #print name
                #row['geneID'] = name
                row["geneName"] = 'Not converted!'
                row["geneID"] = 'Not converted!'
            row['Peptides'] = str(inclusive_gi2pep[gi])
            wtr.write(row)
    wtr.close()
    wtr = mzReport.writer(filename, columns =['accession', 'geneID', 'geneName', 'Description', 'Peptides', 'Number of Peptides'], sheet_name = "Protein Report-Stringent")
    row = {}

    for gi in stringent_gi2pep.keys():
        if len(stringent_gi2pep[gi]) >= peptide_stringency: #At least 2 peptides
            row['accession'] = gi
            row['Description'] = desc_bank[gi]
            row['Number of Peptides'] = len(stringent_gi2pep[gi])
            try:
                row['geneID'] = gi2geneID[gi]
                row['geneName'] = gi2geneName[gi].strip()
            except:
                #gb = genbank.download_genbank(gi)
                #row["geneName"] = gb.gene
                #line = 'select * from "gene info" where "Gene Symbol" = "' + str(gb.gene) + '";'
                #c.execute(line)
                #name = c.fetchone()[2]
                #print name
                #row['geneID'] = name
                row["geneName"] = 'Not converted!'
                row["geneID"] = 'Not converted!'
            row['Peptides'] = str(stringent_gi2pep[gi])
            wtr.write(row)
    wtr.close()
    #c.close()

def extract_gi(filename, sheetname, outfile, gi_sheet_name = 'gi'):
    gi_set = set()
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    counter = 0
    pa = re.compile('(gi\|[0-9]+?)\|')
    for row in rdr:
        if counter % 100 == 0:
            print str(counter)
        counter += 1
        try:
            gi_row = row["Accession Number"]
        except:
            gi_row = row["Accession"]
        gis = gi_row.split(";")
        for gi in gis:
            gi = gi.strip()
            id = pa.match(gi)
            if id:
                current_gi = id.groups()[0]
                gi_set.add(current_gi)
    rdr.close()
    wtr = mzReport.writer(outfile, sheet_name = gi_sheet_name, columns=["Accession Number"])
    row = {}
    for member in gi_set:
        row["Accession Number"] = member
        wtr.write(row)
    wtr.close()

class protein():
    def __init__(self, sequence):
        self.sequence = sequence
        self.peptides = set()
        self._metadata=[]
        self.pepDict = defaultdict(dict) # {'SEQUENCE|VARMOD|CG' (KEY) : 'seq', 'varmod', 'cg', 'psm_list':[(scan, score)]}
        self.seqDict = defaultdict(set)  # {'SEQUENCE':set(keys)}
        for member in sequence:
            self._metadata.append({"Bold":False, "Color":"Black", "Underline":False, "Size":10, "Score":0, "Mods":set()})
            #self._metadata.append({"Background":wx.NullColour, "FontArgs":(12, wx.ROMAN, wx.NORMAL, wx.BOLD, False), "Color":"Black", "Score":0, "Mods":set()})
    def __str__(self):
        return self.sequence
    def calcTotalCoverage(self, start=0, end=None):
        '''Start and end are 0 to n-1'''
        if not end:
            end = len(self.sequence)-1
        res = len(self.sequence)
        coverage = 0
        if res > 0:
            scanned = 0
            cov = 0
            for i, member in enumerate(self._metadata):
                if i >= start and i <= end:
                    scanned += 1
                if member["Score"] > 0 and i >= start and i <= end:
                    cov += 1
            coverage = float(cov)/float(scanned)
        return coverage, cov, scanned, res
    def calcResidueCoverage(self, residue, start=0, end=None):
        if not end:
            end = len(self.sequence)-1
        res = self.sequence.count(residue, start, end+1)
        coverage = 0
        if res > 0:
            cov = 0
            scanned = 0
            for i, member in enumerate(self._metadata):
                if i >= start and i <= end:
                    scanned += 1
                if member["Score"] > 0 and self.sequence[i]==residue and i >= start and i <= end:
                    cov += 1
            coverage = float(cov)/float(res)
        return coverage, cov, scanned, res
    def save(self):
        filename, dir = get_single_file('Enter Filename...', "*.prt")
        pickle_file = open(filename, "w")
        cPickle.dump(self, pickle_file)
        pickle_file.close()
    def saveFile(self, filename):
        pickle_file = open(filename, "w")
        cPickle.dump(self, pickle_file)
        pickle_file.close()
    def load(self):
        filename, dir = get_single_file('Select File...', "*.prt")
        pickle_file = open(filename, "r")
        self = cPickle.load(pickle_file)
        pickle_file.close()
        return self
    def loadFile(self, filename):
        pickle_file = open(filename, "r")
        self = cPickle.load(pickle_file)
        pickle_file.close()
        return self
    def dump_peptides(self):
        pep_list=list(self.peptides)
        pep_list.sort()
        for member in pep_list:
            print member
    def map(self, filename, sheetname, score_threshold=0):
        print "AMMPING"
        phos = re.compile('.*?([STY])(\d+?)[:] Phospho')
        acet = re.compile('([KC])(\d+?)[:] Acetyl')
        inhib = re.compile('([K])(\d+?)[:] UL44i')
        print "Reading sheet..."
        rdr = mzReport.reader(filename, sheet_name = sheetname)
        counter = 0
        for row in rdr:
            if counter % 100 == 0:
                print counter
            counter += 1
            seq = row["Peptide Sequence"]
            mods = row["Variable Modifications"]
            if not mods:
                mods = 'None'
            score = row["Peptide Score"]
            cg = row['Charge']
            scan = int(row['Spectrum Description'].split('.')[1])
            if float(score) > score_threshold:
                #self.pepDict = defaultdict(dict) # {'SEQUENCE|VARMOD|CG' (KEY) : 'seq', 'varmod', 'cg', 'psm_list':[(scan, score)]}
                #self.seqDict = defaultdict(set)  # {'SEQUENCE':set(keys)}  
                key = seq + '|' + mods + '|' + str(cg)
                psm_entry = (scan, score)
                if key not in self.pepDict.keys():
                    self.pepDict[key]={'seq':seq, 'varmod':mods, 'cg':cg, 'psm_list':[psm_entry]}
                    self.seqDict[seq].add(key)
                else:
                    self.pepDict[key]['psm_list'].append(psm_entry)
                self.peptides.add(seq)
                hits = self.sequence.count(seq)
                current = 0
                for i in range(0, hits):
                    pos = self.sequence.find(seq, current)
                    #self.peptides.add(seq) Redundant
                    current = pos + 1
                    for k in range(0, len(seq)):
                        self._metadata[pos + k]["Bold"] = True
                        self._metadata[pos + k]["Underline"] = True
                        self._metadata[pos + k]["Color"]="Red"
                        current_score = self._metadata[pos + k]["Score"]
                        if score > current_score:
                            self._metadata[pos + k]["Score"] = score
                    if mods:
                        mod_list = mods.split(";")
                        for mod in mod_list:
                            id = phos.match(mod)
                            if id:
                                mod_pos = int(id.groups()[1])
                                self._metadata[pos + mod_pos - 1]["Mods"].add("Phosphorylation")
                                self._metadata[pos + mod_pos - 1]["Color"]="Red"
                            id = acet.match(mod)
                            if id:
                                mod_pos = int(id.groups()[1])
                                self._metadata[pos + mod_pos - 1]["Mods"].add("Acetyl")
                                self._metadata[pos + mod_pos - 1]["Color"]="Red"
                            id = inhib.match(mod)
                            if id:
                                mod_pos = int(id.groups()[1])
                                self._metadata[pos + mod_pos - 1]["Mods"].add("UL44i")
                                self._metadata[pos + mod_pos - 1]["Color"]="Blue"
        rdr.close()

class TestPopup(wx.PopupWindow):
    """Adds a bit of text and mouse movement to the wx.PopupWindow"""
    def __init__(self, parent, style, text, pos):
        wx.PopupWindow.__init__(self, parent, style)
        pnl = self.pnl = wx.Panel(self)
        pnl.SetBackgroundColour("WHITE")
        self.parent = parent
        self.pos = pos
        st = wx.StaticText(pnl, -1,text, pos=(10,10))
        self.st = st
        sz = st.GetBestSize()
        self.SetSize( (sz.width+10, sz.height+10) )
        pnl.SetSize( (sz.width+10, sz.height+10) )
        #self.SetSize( (sz.width+0, sz.height+0) )
        #pnl.SetSize( (sz.width+0, sz.height+0) )        

        pnl.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        pnl.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        pnl.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        pnl.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        st.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        st.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        st.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        st.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        wx.CallAfter(self.Refresh)
        

    def OnMouseLeftDown(self, evt):
        self.Refresh()
        mousePos = evt.GetPosition()
        
        self.ldPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.wPos = self.ClientToScreen((0,0))
        self.pnl.CaptureMouse()
        
        

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            dPos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            nPos = (self.wPos.x + (dPos.x - self.ldPos.x),
                   self.wPos.y + (dPos.y - self.ldPos.y))
            self.Move(nPos)
        #pos = evt.GetPositionTuple()
        #member = self.pos
        #x1 = member[0]-10
        #x2 = member[0]
        #y1 = member[1] - 10
        #y2 = member[1]
        #if pos[0] > x1 and pos[0] <x2 and pos[1] > y1 and pos[1] < y2:   
        #    pass
        #else:
        #    self.Show(False)
        #    self.Destroy()            

    def OnMouseLeftUp(self, evt):
        if self.pnl.HasCapture():
            self.pnl.ReleaseMouse()

    def OnRightUp(self, evt):
        #Go to scan with MS2
        currentFile = self.parent.parent.msdb.files[self.parent.parent.msdb.Display_ID[self.parent.parent.msdb.active_file]]
        scan = int(self.pos[2].scan) 
        currentFile['scanNum']=scan
        self.parent.parent.msdb.set_scan(currentFile["scanNum"], self.parent.parent.msdb.active_file)
        if currentFile['vendor']=='Thermo':
            self.parent.parent.msdb.build_current_ID(self.parent.parent.msdb.Display_ID[self.parent.parent.msdb.active_file], currentFile["scanNum"])        
        #self.Show(False)
        #self.Destroy()
        self.parent.parent.Window.UpdateDrawing()
        self.parent.parent.Refresh() 

class TextFrame(wx.Frame):
    def __init__(self, protein):
        self.frame = wx.Frame.__init__(self,None,-1, "Protein Coverage", size=(1100,500))
        self.panel = wx.Panel(self, -1)
        self.richText = wx.TextCtrl(self.panel, -1, protein.sequence, size=(1000, 400), style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.richText.Bind(wx.EVT_LEFT_UP, self.OnLeftDown)
        self.richText.Bind(wx.EVT_MOTION, self.OnMotion)
        self.label = wx.StaticText(self.panel, -1, "            ")
        self.saveButton = wx.Button(self.panel, -1, label="S", size=(25,25))
        self.saveButton.Bind(wx.EVT_BUTTON, self.OnListSave)
        self.highLiteResButton = wx.Button(self.panel, -1, label="H", size=(25,25))
        self.highLiteResButton.Bind(wx.EVT_BUTTON, self.OnHiLite)        
        #self.loadButton = wx.Button(self.panel, -1, label="L", size=(25,25))
        #self.loadButton.Bind(wx.EVT_BUTTON, self.OnListLoad)
        self.richText.SetInsertionPoint(0)
        self.fp = wx.Font(12, wx.ROMAN, wx.NORMAL, wx.BOLD, False)
        self.sizer = wx.FlexGridSizer(cols = 2, hgap=6, vgap = 6)
        self.sizer.AddMany([self.richText, self.saveButton, self.label, self.highLiteResButton]) #, self.loadButton
        self.panel.SetSizer(self.sizer)
        self.curentPopUp = None
        self.popPos = 0
        self.popText = None
        self.protein = protein
        for i, member in enumerate(self.protein._metadata):
            #self.richText.SetStyle(i, i+1, wx.TextAttr(member["Color"], member["Background"], wx.Font(i for i in member["Font"])))
            if member["Bold"]:
                self.richText.SetStyle(i, i+1, wx.TextAttr(member["Color"], wx.NullColour, self.fp))
#            if "Acetyl" in member["Mods"]:
#                self.richText.SetStyle(i, i+1, wx.TextAttr("red", wx.NullColour, self.fp)) 

    def getChargesFromKeys(self,keyset):
        cg_txt = ''
        cg_set = set()
        for key in keyset:
            cg_set.add(key.split('|')[2].strip())
        cg_list = list(cg_set)
        cg_list.sort()
        for cg in cg_list:
            cg_txt += '+' + cg + ', '
        return cg_txt[:-2]

    def OnHiLite(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter residues to highlight:', 'Set mz range')
        if dlg.ShowModal() == wx.ID_OK:
            for res in dlg.GetValue():
                for i, member in enumerate(self.richText.GetValue()):
                    if res==member:
                        self.richText.SetStyle(i, i+1, wx.TextAttr(wx.BLUE, wx.NullColour, self.fp))
        #            if "Acetyl" in member["Mods"]:
        #                self.richText.SetStyle(i, i+1, wx.TextAttr("red", wx.NullColour, self.fp))                 

        dlg.Destroy()           

    def OnMotion(self, event):
        print "EVT"
        mousePos = event.GetPosition()
        location = self.richText.HitTestPos(mousePos)
        
        if location[1] < len(self.protein.sequence):
            cur = []
            for member in self.protein.peptides:
                pepstart = self.protein.sequence.find(member)
                peppos = [pepstart, pepstart + len(member) - 1]
                if location[1] >= peppos[0] and location[1] <= peppos[1]:
                    cur.append(peppos)
            line = ''
            for member in cur:
                line += self.protein.sequence[member[0]:member[1]+1] + '  '
            line2 = ''
            for member in cur:
                cur_seq = self.protein.sequence[member[0]:member[1]+1]
                pd = self.protein.pepDict[cur_seq]
                sd = self.protein.seqDict[cur_seq]
                cg_txt = self.getChargesFromKeys(sd)
                #self.pepDict = defaultdict(dict) # {'SEQUENCE|VARMOD|CG' (KEY) : 'seq', 'varmod', 'cg', 'psm_list':[(scan, score)]}
                #self.seqDict = defaultdict(set)  # {'SEQUENCE':set(keys)}                 
                line2 += cur_seq + ' ' + cg_txt + '\n'
                
            self.label.SetLabel(self.protein.sequence[location[1]] + ": " + str(location[1]) + " " + line)
            if line2 != self.popText:
                if self.curentPopUp:
                    self.curentPopUp.Destroy()
                    #del self.curentPopUp
                    self.curentPopUp = None
            #if not self.curentPopUp:
                win = TestPopup(self, wx.SIMPLE_BORDER, line2, (100,100))
                win.Position((mousePos[0]+20,mousePos[1]-20), (0, 100))
                win.Show(True) 
                self.popPos = location[1]
                self.popText = line2
                self.curentPopUp = win
        #pos4 = event.GetPosition()
        #print pos4
        #pos5 = self.richText.HitTestPos(pos4)
        #print pos5
        #print self.protein.sequence[pos5[1]:pos5[1]+1]        
        
        event.Skip()
    
    
    def OnLeftDown(self, event):
        print "Pressed!"
        point = wx.GetMousePosition()
        point2 = self.richText.GetPosition()
        print point2
        print point
        pos = self.richText.HitTest(point)
        pos2 = self.richText.HitTestPos(point)
        #pos3 = self.HitTestXY
        print pos
        print pos2
        pos3 = self.richText.GetSelection()
        cur = []
        for member in self.protein.peptides:
            pepstart = self.protein.sequence.find(member)
            peppos = [pepstart, pepstart + len(member) - 1]
            if pos3[0] >= peppos[0] and pos3[0] <= peppos[1]:
                cur.append(peppos)
        line = ''
        for member in cur:
            line += self.protein.sequence[member[0]:member[1]+1] + '  '
        self.label.SetLabel(self.protein.sequence[pos3[0]] + ": " + str(pos3[1]) + " " + line)
        pos4 = event.GetPosition()
        print pos4
        pos5 = self.richText.HitTestPos(pos4)
        print pos5
        print self.protein.sequence[pos5[1]:pos5[1]+1]
        #print self.richText.ClientToScreenXY()
        #a = wxPoint(self.richText.GetPosition())
        #print a

    def OnListSave(self, event):
        self.protein.save()
    def OnListLoad(self, event):
        self.protein = self.protein.load()
        self.refresh()
    def refresh(self):
        self.richText.SetValue(self.protein.sequence)
        self.richText.SetInsertionPoint(0)
        for i, member in enumerate(self.protein._metadata):
            if member["Bold"]:
                self.richText.SetStyle(i, i+1, wx.TextAttr(member["Color"], wx.NullColour, self.fp))
            if "Acetyl" in member["Mods"]:
                self.richText.SetStyle(i, i+1, wx.TextAttr("red", wx.NullColour, self.fp))

def coverage(sequence, filename, sheetname='Data', score_threshold=0):
    if type(filename) == str:
        prot = protein(sequence)
        prot.map(filename, sheetname, score_threshold)
        prot.dump_peptides()
        print "calc"
        coverage, cov, scanned, res = prot.calcTotalCoverage()
        print coverage
        print cov
        print scanned
        print res
    elif type(filename) == list:
        prot = protein(sequence)
        for member in filename:
            prot.map(member, sheetname, score_threshold)
        print "calc"
        coverage, cov, scanned, res = prot.calcTotalCoverage()
        print coverage
        print cov
        print scanned
        print res
    app = wx.PySimpleApp()
    frame = TextFrame(prot)                
    frame.Show()
    app.MainLoop()

def load_protein():
    filename, dir = get_single_file("Select .prt file...", "*.prt")
    pickle_file = open(filename, "r")
    prot = cPickle.load(pickle_file)
    pickle_file.close()
    return prot

def load_coverage():
    filename, dir = get_single_file("Select .prt file...", "*.prt")
    pickle_file = open(filename, "r")
    prot = cPickle.load(pickle_file)
    pickle_file.close()
    app = wx.PySimpleApp()
    frame = TextFrame(prot)
    frame.Show()
    app.MainLoop()

def display_coverage(filename):
    pickle_file = open(filename, "r")
    prot = cPickle.load(pickle_file)
    pickle_file.close()
    app = wx.PySimpleApp()
    frame = TextFrame(prot)
    frame.Show()
    app.MainLoop()

#if __name__ == '__main__':
    #app = wx.PySimpleApp()

    #dlg = wx.FileDialog(None, "Choose Multiplierz File:", defaultFile=os.getcwd(), pos = (2,2))
    #if dlg.ShowModal() == wx.ID_OK:
        #filename=dlg.GetPath()
        #dir = dlg.GetDirectory()
        #print filename
        #print dir
    #dlg.Destroy()

def MHC_motif_analysis(filename, sheet):
    min_res = 9
    max_res = 12
    Cterm = ["L", "I", "V", "F", "Y", "W", "A", "M"]
    rdr = mzReport.reader(filename, sheet_name = sheet)
    wtr = mzReport.writer(filename, rdr.columns + ["Motif Match"], sheet_name = sheet)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print str(counter)
        counter += 1
        seq = row["Peptide Sequence"]
        acc = row["Accession Number"]
        row["Motif Match"]=False
        match = False
        if len(seq) >= min_res and len(seq) <= max_res:
            if seq[len(seq)-1] in Cterm:
                if acc.find("rev_gi") == -1:
                    match = True
        if match:
            row["Motif Match"]=True
        wtr.write(row)
    rdr.close()
    wtr.close()

def PKC_motif_analysis(filename, sheet):
    pa1 = re.compile('.*?[ST][FLV].?[RK]')
    pa2 = re.compile('.*?[RK]\w[S][FLVYIAMWG][RK]')
    rdr = mzReport.reader(filename, sheet_name = sheet)
    try:
        wtr = mzReport.writer(filename, rdr.columns + ["Motif Match 1", "Motif Match 2"], sheet_name = sheet)
    except:
        wtr = mzReport.writer(filename, rdr.columns, sheet_name = sheet)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        seq = row["Peptide Sequence"]
        row["Motif Match 1"]= True if pa1.match(seq) else False
        row["Motif Match 2"]= True if pa2.match(seq) else False
        wtr.write(row)
    rdr.close()
    wtr.close()

def make_phospho_sheet(filename, sheetname = "Data"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = "Phospho")
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        varmod = row["Variable Modifications"]
        acc = row["Accession Number"]
        if not varmod:
            varmod = ''
        if varmod.find("Phospho") > -1 and acc.find("rev_gi") == -1:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()

def make_gene_sheet(filename, sheetname = "Data", gene="", newSheetName=''):
    '''
    
    Makes sub worksheet in xls for any entry with specified gene name.
    If new sheet name not given, uses gene name.
    Related function make_genes_sheet matches a list of genes, rather than a single gene
    
    '''
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    if not newSheetName:
        newSheetName = gene
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = newSheetName)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        geneName = row["GeneName"]
        acc = row["Accession Number"]
        if geneName.find(gene) > -1 and acc.find("rev_gi") == -1:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()
    
def make_genes_sheet(filename, sheetname = "Data", targetGenes=[""], newSheetName='Targets'):
    '''
    2014-05-11
    Makes sub worksheet in xls for any entry with a gene in the specified list.
    If new sheet name not given, uses gene name.
    make_genes_sheet takes a list
    
    '''    
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = newSheetName)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        geneNames = delist_text(row["GeneName"])
        acc = row["Accession Number"]
        if acc.find("rev_gi") == -1:
            found = False
            for gn in geneNames:
                if gn in targetGenes:
                    found = True
                    break
            if found:
                wtr.write(row)
        counter += 1
    print "Read"
    rdr.close()
    print "Close1"
    wtr.close()
    print "Close2"

def make_pY_sheet(filename, sheetname = "Data"):
    pa = re.compile(".*?Y(\d+): Phospho")
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = "pY")
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        varmod = row["Variable Modifications"]
        acc = row["Accession Number"]
        if not varmod:
            varmod = ''
        id = pa.match(varmod)
        if not varmod:
            varmod = ''
        if id and acc.find("rev_gi") == -1:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()

def make_sub_sheet(filename, sheetname="Data", test_col="Targets", pos=True, new_sheet="Targets"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = new_sheet)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        current = row[test_col]
        if current == pos:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()

def make_kinase_sheet(filename, sheetname = "Data"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    print sheetname
    print "OPENED"
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = "Kinases")
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        kinase = row['Kinase?']
        if kinase == True:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()

def make_protein_sheet(filename, sheetname = "Data", gi = 'None', name="None"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns, sheet_name = name)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        acc = row["Accession Number"]
        if acc.find(gi) > -1 and acc.find("rev_gi") == -1:
            wtr.write(row)
        counter += 1
    rdr.close()
    wtr.close()

def protein_relative_modifications(filename, sheet, _mod="Phosphorylation"):
    if _mod == "Phosphorylation":
        pa = re.compile('([STY])(\d+?)[:] Phospho')
        __mod = ": Phospho"
    elif _mod == "Acetylation":
        __mod = ": Acetyl"
        pa = re.compile('([KC])(\d+?)[:] Acetyl')
    elif _mod == "Fucosylation":
        __mod = ": Fucosylation"
        pa = re.compile('([ST])(\d+?)[:] Fucosylation')
    rdr = mzReport.reader(filename, sheet_name = sheet)
    try:
        wtr = mzReport.writer(filename, rdr.columns + ["Protein Relative Modifications"], sheet_name = sheet)
    except:
        wtr = mzReport.writer(filename, rdr.columns, sheet_name = sheet)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        varmod = row["Variable Modifications"]
        start = int(row["Start Position"])
        if varmod:
            mods = varmod.split(';')
        else:
            mods = ''
        prm = ''
        for mod in mods:
            mod = mod.strip()
            id = pa.match(mod)
            if id:
                if prm:
                    prm += '; '
                new_prm = id.groups()[0] + str(int(id.groups()[1]) + start - 1) + __mod
                prm += new_prm
        row['Protein Relative Modifications'] = prm
        wtr.write(row)
    rdr.close()
    wtr.close()
    
def quick_summary(filename, sheetname='Data', score_threshold=0, reverse_text='rev_gi', gene_threshold=0):
    '''
    Version 0.21 2014-08-08
    Quick analysis of multiplierz report: PSMs, unique peptides, Genes mapped uniquely by peptides.
    Gene Threshold = number of unique peptides that must map to gene to be counted
    
    '''
    print "PSMs"
    print str(count_PSMs(filename, sheetname, score_threshold=score_threshold, reverse_text=reverse_text))
    peptides = count_unique_peptides(filename, sheetname, score_cutoff=score_threshold)
    print "UNIQUE PEPTIDE SEQUENCES"
    print len(peptides)
    print "GENES MAPPED UNIQUELY BY PEPTIDES"
    ugenes = quick_gene_summary(filename, sheetname, True, gene_threshold)
    print len(ugenes)
    print "ALL GENES MAPPED BY PEPTIDES"
    igenes = quick_gene_summary(filename, sheetname, False, gene_threshold)
    print len(igenes)    
    
    return peptides, ugenes, igenes
    

def count_PSMs(filename, sheetname = 'Data', score_threshold=15, reverse_text='rev_gi'):
    '''
    
    Version 0.2 2014-07-18
    Does not count reverse hits matching text
    
    '''
    if filename.find('.xls')>-1:
        rdr = mzReport.reader(filename, sheet_name = sheetname)
    else:
        rdr = mzReport.reader(filename)
    counter = 0
    for row in rdr:
        count=True
        if reverse_text:
            acc = row['Accession Number']
            if acc.find(reverse_text)>-1:
                count=False
        score = row['Peptide Score']
        if score < score_threshold:
            count = False
        if count:
            counter += 1
    return counter

def count_peptides_and_genes(filename, sheetname = "Data"):
    peptides = count_unique_peptides(filename, sheetname)
    print "UNIQUE PEPTIDE SEQUENCES"
    print len(peptides)
    print "GENES MAPPED UNIQUELY BY PEPTIDES"
    genes = quick_gene_summary(filename, sheetname, True)
    print len(genes)
    print "ALL GENES MAPPED BY PEPTIDES"
    genes = quick_gene_summary(filename, sheetname, False)
    print len(genes)

def count_unique_peptides(filename, sheet, score_cutoff=10):
    peptides = set()
    if filename.find('.xls')>-1:
        rdr = mzReport.reader(filename, sheet_name = sheet)
    else:
        rdr = mzReport.reader(filename)
    counter = 0
    for row in rdr:
        if counter % 500 == 0:
            print str(counter)
        counter += 1
        seq = row["Peptide Sequence"]
        acc = row["Accession Number"]
        desc = row["Protein Description"]
        if not score_cutoff:
            if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                peptides.add(seq)
        else:
            score = row['Peptide Score']
            if score >= score_cutoff:
                if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
                    peptides.add(seq)                 
    print '----'
    print len(peptides)
    print "Unique peptides"
    rdr.close()
    return peptides

def retrieve_database(organism):
    '''

    Matches each peptide to UNIPROT subdatabase of kinases.
    This version calls retrieve_database (organism) to make a dictionary of header:sequence for HUMAN or MOUSE.
    The databases reside in SouthStation and correspond to EC2.7.10.-, 2.7.11.-, 2.7.12.- (protein kinases).
    Creates new columns: Kinase? (True/False), Matches (UNIPROT header), Unique (Is it a unique kinase match?)

    '''
    organism = organism.upper()
    kinobase = {}
    print "Loading kinobase in RAM..."
    if organism in ['H', "HUMAN"]:
        for header, sequence in mzF.parse_fasta(os.path.join(FILES_DIR, 'files', "protein kinases human.fasta")):
            kinobase[header] = sequence
    if organism in ['M', "MOUSE"]:
        for header, sequence in mzF.parse_fasta(os.path.join(FILES_DIR, 'files', "protein kinases mouse.fasta")):
            kinobase[header] = sequence
    print "Loaded!"
    return kinobase

def label_kinases(filename, sheetname="Data", organism="HUMAN"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns + ['Kinase?', 'Matches', 'Unique'], sheet_name = sheetname)
    counter = 0
    kinobase = retrieve_database(organism)
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        found = False
        unique = 'NA'
        kin_list = []
        acc = row["Accession Number"]
        peptide = row["Peptide Sequence"]
        if acc.find("rev_gi") == -1:
            for header, sequence in kinobase.iteritems():
                if sequence.find(peptide.strip()) > -1:
                    found = True
                    kin_list.append(header)
            if len(kin_list) == 1:
                unique = True
            else:
                unique = False
        row['Unique'] = unique
        row['Kinase?'] = found
        if not kin_list:
            kin_list = ['NA']
        row['Matches'] = str(kin_list)
        wtr.write(row)
    rdr.close()
    wtr.close()


def extract_genes(entry):
    entry = entry.replace('[','').replace(']','').replace("'","")
    genes = entry.split(',')
    gene_list = []
    for member in genes:
        gene = member.strip()
        if gene.find("unresolved") == -1:
            gene_list.append(gene)
    return gene_list


def kinase_match(filename, sheetname="Data", flag="Stringent", phoscheck = False, peptide_stringency = 1, organism = "human"):
    kinobase = retrieve_database(organism)
    sequences = set()
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    print "Reading sequences..."
    for row in rdr:
        varmod = row["Variable Modifications"]
        if not varmod:
            varmod = ''
        desc = row["Protein Description"]
        proceed = True
        if phoscheck:
            if varmod.find("Phospho") == -1:
                proceed = False
        if desc.find("Marto") > -1:
            proceed = False
        if proceed == True:
            sequences.add(row["Peptide Sequence"])
    print sequences
    rdr.close()
    main_list = []
    unique = set()
    all = set()
    kin_dict_un = collections.defaultdict(set)
    kin_dict_all = collections.defaultdict(set)
    for peptide in sequences:
        print peptide
        kin_list = []
        kin_dict = collections.defaultdict(set)
        for header, sequence in kinobase.iteritems():
            if sequence.find(peptide.strip()) > -1:
                kin_list.append(header)
                kin_dict[header].add(peptide)
        if len(kin_list) == 1:
            unique.add(kin_list[0])
            print kin_dict[kin_list[0]]
            print kin_list[0]
            kin_dict_un[kin_list[0]].update(kin_dict[kin_list[0]]) #kinases for which unique peptide evidence exists
            all.add(kin_list[0])
            kin_dict_all[kin_list[0]].update(kin_dict[kin_list[0]])
        else:
            for kin in kin_list:
                all.add(kin)
                kin_dict_all[kin].update(kin_dict[kin])
    ac_un = []
    ac_un_set = set()
    for member in unique:
        found = False
        subtext = member.split(" ")
        for sub in subtext:
            if sub.find('GN=')>-1:
                ac_un.append(sub[3:])
                ac_un_set.add(sub[3:])
                found = True
    ac_all_un = []
    ac_all_un_set = set()
    for member in all:
        subtext = member.split(" ")
        for sub in subtext:
            if sub.find('GN=')>-1:
                ac_all_un.append(sub[3:])
                ac_all_un_set.add(sub[3:])
    res_text = "Kinases with unique matches: " + str(len(ac_un_set)) + " " + "All matches: " + str(len(ac_all_un_set)) + "  "
    st_pass = set()
    output_text=[]
    if flag == 'Stringent':
        output_text.append("Kinase Analysis Results")
        output_text.append("STRIGENT COUNTING (KINASES) SELECTED")
        if phoscheck:
            output_text.append("PHOSPHORYLATION REQUIRED")
        else:
            output_text.append("PHOSPHORYLATION -NOT- REQUIRED")
        output_text.append("COUNTING ALL KINASES WITH AT LEAST " + str(peptide_stringency) + " Peptide(s)")
        output_text.append("Adventitious proteins removed")
        un_an = 0
        for member in kin_dict_un.keys():
            if len(kin_dict_un[member]) >= peptide_stringency:
                add_mem = None
                subtext = member.split(" ")
                found = False
                for sub in subtext:
                    if sub.find('GN=')>-1:
                        add_mem=(sub[3:])
                        found = True
                if found == False:
                    un_an += 1
                if add_mem != None and add_mem not in st_pass:
                    output_text.append(add_mem + '|||' + member + " " + str(kin_dict_un[member]) + '|||' + str(len(kin_dict_un[member])))
                st_pass.add(add_mem)
        temp = ''
        for member in st_pass:
            temp += member + ', '
        output_text.append(temp[:-1])
        output_text.append(str(len(st_pass)))
        res_text += "Unique Meeting stringency: " + str(len(st_pass)) + " Un An: " + str(un_an)
        Write_Output(filename, "Kinase Report-Stringent",output_text)
    else:
        output_text.append("Protein Manager Results")
        output_text.append("INCLUSIVE COUNTING (KINASES) SELECTED")
        if phoscheck:
            output_text.append("PHOSPHORYLATION REQUIRED")
        else:
            output_text.append("PHOSPHORYLATION -NOT- REQUIRED")
        output_text.append("COUNTING ALL KINASES WITH AT LEAST " + str(peptide_stringency) + " Peptide(s)")
        output_text.append("Adventitious proteins removed")

        un_an = 0
        for member in kin_dict_all.keys():
            if len(kin_dict_all[member]) >= peptide_stringency:
                add_mem = None
                subtext = member.split(" ")
                found = False
                for sub in subtext:
                    if sub.find('GN=')>-1:
                        add_mem=(sub[3:])
                        found = True
                if found == False:
                    un_an += 1
                if add_mem != None and add_mem not in st_pass:
                    output_text.append(add_mem + '|||' + member + " " + str(kin_dict_all[member]) + '|||' + str(len(kin_dict_all[member])))
                if add_mem != None:
                    st_pass.add(add_mem)
        temp = ''
        for member in st_pass:
            temp += member + ', '
        output_text.append(temp[:-1])
        output_text.append(str(len(st_pass)))
        res_text += "Inclusive Meeting stringency: " + str(len(st_pass)) + " Un An: " + str(un_an)
        Write_Output(filename, "Kinase Report-Inclusive",output_text)

def Write_Output(filename, sheetname, out_list):
    wtr = mzReport.writer(filename, columns =['Output'], sheet_name = sheetname)
    row = {}
    for line in out_list:
        row['Output'] = line
        wtr.WriteRow(row)
    wtr.close()

def replace_char(string_object, replace_chars):
    '''
    
    string_object should be a string
    
    replace_chars = list of chars to replace
    
    '''
    for ch in replace_chars:
        if ch in string_object:
            string_object = string_object.replace(ch, '')
            
    return string_object

def delist_text(list_as_text):
    members = list_as_text.replace('[', '').replace(']','').replace("'","").split(',')
    return_list = []
    for member in members:
        return_list.append(member.strip())
    return return_list

def deset_text(set_as_text):
    '''
    
    Desets text.  Returns a list
    
    '''
    members = set_as_text.replace('set([', '').replace('])','').replace("'","").split(',')
    return_set = []
    for member in members:
        return_set.append(member.strip())
    return return_set

def clean_text(text):
    '''
    Version 0.1 2014-07-18
    Input=text version of a set of list.
    Output=clean version of text (no [, ], ', or set())
    
    '''
    if text.find('set') > -1:
        text=text.replace('set([', '').replace('])','').replace("'","")
    elif text.startswith('['):
        text=text.replace('[', '').replace(']','').replace("'","")
    return text

def deset(seq_list):
    '''
  
    seq_list argument should be a list
    
    '''
    set_list = []
    for member in seq_list:
        temp = member.replace("set([", '').replace("u'", '').replace("'", "").replace(']','').replace(")", "").replace("|None", "").strip()
        set_list.append(temp)
    return set_list

def deset_sheet(filename, sheetname, column_title):
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    wtr = mzReport.writer(filename, columns = rdr.columns, sheet_name=sheetname)
    for row in rdr:
        seq_list = row[column_title]
        print row[column_title]
        set_list = deset([seq_list])
        print set_list
        line = ''
        for member in set_list:
            member = member.replace('[','').replace('u', '').replace("]", "").replace("'", "").strip()
            line = line + member + ', '
        line = line[:-2]
        row[column_title]=line
        wtr.write(row)
    rdr.close()
    wtr.close()

def cys_cap_evaluation(filename, sheetname="Data", label=False):
    '''
        
    Reads multiplierz sheet.  
    
    If label true:
    Adds column "Cys?".  If sequence contains "C", "Yes" is added to the corresponding row, otherwise "No".
    
    To calculate % cysteine peptides, seq + '|' + varmod is added to a Python set.
    % cys peptides = % of Cys containing peptides in the set / total number of peptides.
    (Using a set counts only unique seq/varmod combinations).
        
    '''    
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    if label:
        wtr = mzReport.writer(filename, columns = rdr.columns + ["Cys?"], sheet_name=sheetname)
    peplist=set()
    counter = 0
    for row in rdr:
        if counter%100==0:
            print counter
        counter += 1
        pep = row["Peptide Sequence"]
        varmod = row["Variable Modifications"]
        if not varmod:
            varmod = ''
        peplist.add(pep + '|' + varmod)
        if label:
            cys = "No"
            if pep.find("C")>-1:
                cys="Yes"
            row["Cys?"] = cys
            wtr.write(row)
    rdr.close()
    if label:
        wtr.close()
    else:
        tot = len(peplist)
        cys_count = 0
        for member in peplist:
            if member.find("C")>-1:
                cys_count+=1
        print cys_count
        print tot
        print str(float(cys_count)/float(tot))
        
def cys_alkylation_evaluation(filename, sheetname="Data"):
    '''
        
    Reads multiplierz sheet.  
    
    
        
    '''    
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    peplist=set()
    counter = 0
    for row in rdr:
        if counter%100==0:
            print counter
        counter += 1
        pep = row["Peptide Sequence"]
        varmod = row["Variable Modifications"]
        if not varmod:
            varmod = ''
        peplist.add(pep + '|' + varmod)
    rdr.close()
    
    tot = len(peplist)
    cys_count = 0
    carbam = 0
    mmts = 0
    fully_labeled = 0
    for member in peplist:
        if member.find("C")>-1:
            cys_count+=1
            cys_res = member.count("C")
            mmts_groups = member.count("Methylthio")
            carbam_groups = member.count("Carbamido")
            if cys_res == mmts_groups or cys_res == carbam_groups:
                fully_labeled += 1
                if carbam_groups:
                    carbam += 1
                if mmts_groups:
                    mmts += 1
            
            
    print cys_count
    print tot
    print str(float(cys_count)/float(tot))
    print str(float(carbam)/float(tot))
    print str(float(mmts)/float(tot))

def copy_header_sheet(copyFrom, copyTo):
    rdr = mzReport.reader(copyFrom, sheet_name = "Mascot_Header")
    wtr = mzReport.writer(copyTo, columns = rdr.columns, sheet_name = "Mascot_Header")
    for row in rdr:
        wtr.write(row)
    rdr.close()
    wtr.close()

def missed_cleavage_analysis(file, sheetname):
    rdr = mzReport.reader(file, sheet_name = sheetname)
    mc = 0
    total = 0
    for row in rdr:
        total += 1
        current = int (row['Missed Cleavages'])
        if current:
            mc += 1
    print "MC"
    print str(mc)
    pct = float(mc)/float(total)
    print str(pct) + ' %'
    return mc, total
    rdr.close()

def CountPhos(varmod):
    phos = 0
    for mod in varmod.split(';'):
        if mod.find("Phospho") > -1:
            phos += 1
    return phos

def FLR_analysis(file, sheetname):
    rdr = mzReport.reader(file, sheet_name = sheetname)
    flr = 0
    total = 0
    pepset = set()
    for row in rdr:
        total += 1
        if total % 100 == 0:
            print total
        MD = row['MD Score']
        if not MD:
            MD = 0
        current = int(MD)
        if current >= 11:
            seq = row["Peptide Sequence"]
            varmod = row["Variable Modifications"]
            if not varmod:
                varmod = ''
            phos = CountPhos(varmod)
            if phos > 0:
                key = seq + '|' + varmod
                pepset.add(key)
    print "TOT"
    print total
    print len(pepset)

    print pepset
    rdr.close()
    
def residue_counter(filename, sheetname="Data", residue="K"):
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    wtr = mzReport.writer(filename, columns = rdr.columns + [residue + " Count"], sheet_name=sheetname)
    counter = 0
    for row in rdr:
        if counter%100==0:
            print counter
        counter += 1
        pep = row["Peptide Sequence"]
        row[residue + " Count"] = str(pep.count(residue))
        wtr.write(row)
    rdr.close()
    wtr.close()

def make_gene_list(genes):
    genes = genes.replace("'", "").replace("[","").replace("]","")
    genes = genes.split(",")
    gene_list = []
    for gene in genes:
        gene = gene.strip()
        if gene != "NA":
            gene_list.append(gene)
    return gene_list

def make_site_set(filename, sheetname):
    counter = 0
    print "Opening sheet..."
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    print "Processing..."
    splitter = int(float(len(rdr._data)/float(10.0)))
    phos_set = set()
    for row in rdr:
        if counter % splitter == 0:
            print counter
        counter += 1
        seq = row["Peptide Sequence"]
        prm = row["Protein Relative Modifications"]
        geneList = make_gene_list(row["GeneName"])
        if not prm:
            prm = ''
        mods = prm.split(";")
        for mod in mods:
            if mod.find("Phospho")>-1:
                for gene in geneList:
                    key = gene + "|" + mod.split(":")[0].strip()
                    phos_set.add(key)
    rdr.close()
    return phos_set

#class mzd_writer():
#    def __init__(self, filename, table):
#help["db2xls":''' db2xls: function to convert sqlite files to xls sheets.\n
#db2xls(filename, table)\n
#mzd files, main table=PeptideData
#''']
def db2xls(filename, table):
    print "Reading db..."
    fields = get_table_fields(filename, table)
    headers = [x[1].strip() for x in fields]
    conn = sql.connect(filename)
    c = conn.cursor()
    line = 'select * from "' + table +'";'
    data = []
    c.execute(line)
    a = c.fetchall()
    for member in a:
        data.append(member)
    print "Writing xls..."
    xls_name = filename[:-3]+'.xls'
    wtr = mzReport.writer(xls_name, columns=headers, sheet_name=table)
    for row in data:
        wtr.write(row)
    wtr.close()
    c.close()
    conn.close()



##---------------------------------MODULES FOR PROTEIN PILOT DATA

def get_table_fields(filename, tablename):
    # Returns list of tuples: (0, u'id', u'integer', 0, None, 1)
    print filename
    conn = sql.connect(filename)
    c = conn.cursor()

    line = 'pragma table_info(' + tablename + ');'
    fields = []
    c.execute(line)
    a = c.fetchall()
    for member in a:
        fields.append(member)
    c.close()
    conn.close()
    return fields

def create_new_table_append_columns(filename, base_table, new_table, columns):
    fields = get_table_fields(filename, base_table)
    print fields
    counter = len(fields)
    for member in columns.keys():
        new_field = [(counter, member, columns[member], 0, None, 0)]
        print new_field
        fields += new_field
        counter += 1
    print fields
    conn = sql.connect(filename)
    c = conn.cursor()
    line = 'create table if not exists ' + new_table + ' ('
    for member in fields:
        print member
        name = member[1].strip()
        type = member[2].strip()
        line += '"'+name+'" ' + type + ', '
    line = line[:-2]
    line += ');'
    print line
    c.execute(line)
    conn.commit()

def build_field_list(fields):
    field_list = '("'
    for member in fields:
        field_list += member[1] + '", "'
    field_list = field_list[:-3] + ')'
    return field_list

def assign_fdr(filename):
    print "FDR..."
    conn = sql.connect(filename)
    c = conn.cursor()
    line = 'select id, db from fdr order by "Conf" desc;'
    f_count = 0.0
    r_count = 0.0
    counter = 0
    c.execute(line)
    a = c.fetchall()
    filtered = []
    passed = True
    passed_count = 0
    counter = 0
    for member in a:
        if counter % 1000 == 0:
            print counter
        counter += 1
        if member[1]=="FWD":
            f_count += 1.0
        if member[1]=="REV":
            r_count += 1.0
        if r_count > 0:
            fdr = float(r_count) / float(f_count)
        else:
            fdr = 0.0
        line = 'update fdr set fdr=' + str(fdr)+' where id='+str(member[0])+';'
        c.execute(line)
        if passed:
            if fdr >= 0.01:
                passed = False
        line = 'update fdr set passed="' + str(passed)+'" where id='+str(member[0])+';'
        c.execute(line)
        counter += 1
    conn.commit()
    c.close()
    conn.close()


def assign_database(filename, PepGroup):
    fwd_peps = parse_fwd_peptides(PepGroup)
    print filename
    create_new_table_append_columns(filename, "unique_query", "fdr", {"db":'text', "fdr":'real', "passed":'text'})
    fields = get_table_fields(filename, "unique_query")
    print fields
    field_list = build_field_list(fields)
    print field_list
    line = 'insert into fdr ' + field_list + ' select * from unique_query;'
    conn = sql.connect(filename)
    c = conn.cursor()
    c.execute(line)
    print "Building index..."
    line = 'create index fdr_id on fdr(id);'
    c.execute(line)
    conn.commit()
    print "Done"
    counter = 0
    line = 'select id, Accessions, Sequence from fdr;'
    c.execute(line)
    a = c.fetchall()
    for member in a:
        if counter % 1000 == 0:
            print counter
        counter += 1
        current_acc = member[1]
        #print member[1]
        fra = "?"
        prots = member[1].split(";")
        for prot in prots:
            if prot.find("REV_") == -1 and prot != " " and prot != None:
                fra = "FWD"
                break
            elif prot.find("REV_")>-1:
                seq = member[2].strip()
                if seq in fwd_peps:
                    fra = "FWD"
                    break
                else:
                    fra = "REV"
            elif prot == " " or prot == None:
                seq = member[2].strip()
                if seq in fwd_peps:
                    fra = "FWD"
                    break
                else:
                    fra = "REV"
        #print fra
        line = 'update fdr set db="' + fra +'" where id=' +str(member[0])+';'
        #print line
        c.execute(line)
        #fdfd

    conn.commit()
    c.close()
    conn.close()

def parse_fwd_peptides(filename):
    #PepGroup is a master list of  all peptide sequences that match the forward database
    #Returns fwd_peps, a set of all peptides parsed from this file
    #Uses PeptideSearch.py
    fwd_peps = set()
    file_r = open(filename, 'r')
    data = file_r.readlines()
    for member in data:
        fwd_peps.add(member.split('\t')[1].strip())
    return fwd_peps

def check_entry(entry):
    #Auxiliary module for txt2_sql_convert
    type = "None"
    try:
        float(entry)
        type = "real"
    except:
        type = "text"
    return type

def read_pilot_file_map(filename):
    file_r = open(filename, 'r')
    data = file_r.readlines()
    file_r.close()
    file_map = {}
    pa = re.compile('(\d+?)[)] ([0-9A-Za-z_.\\\:]+)')
    for line in data:
        fid = pa.match(line)
        if fid:
            file_map[int(fid.groups()[0])]=fid.groups()[1]
    file_r.close()
    return file_map
    

def convert_csv2sql(filename):
    #Input: SpectrumSummary_filtered.csv i.e. coverted to .csv
    #Protein Pilot exported data that has been filtered using "Filter_protein_pilot.mz"
    #Creates sql database representing this file and creates unique_queries table
    #file_r = open(file, 'r')
    #data = file_r.readlines()
    #file_r.close()
    data = []
    print "Reading..."
    rdr = csv.reader(open(filename, "rU"), delimiter = ",", dialect=csv.excel_tab)    
    counter = 0
    for row in rdr:
        if counter % 10000 == 0:
            print counter
        counter += 1
        data.append(row)
        
    db = filename[:-4] + '.db'
    conn = sql.connect(db)
    c = conn.cursor()
    cols = data[0]
    bcount = 0
    for i, member in enumerate(cols):
        if not member:
            cols[i]="BLANK"+str(bcount)
            bcount+=1
    print cols
    print data[1]
    fl = data[1]
    line = 'create table if not exists peptides (id integer primary key, '
    for i, col in enumerate(cols):
        print col
        line += '"' + col + '" ' + check_entry(fl[i]) + ', '  #' text, '
    line = line[:-2]
    line += ');'
    print line
    c.execute(line)
    conn.commit()
    line = 'create table if not exists unique_query (id integer primary key, '
    for i, col in enumerate(cols):
        line += '"' + col + '" ' + check_entry(fl[i]) + ', '  #' text, '
    line = line[:-2]
    line += ');'
    print line
    c.execute(line)
    conn.commit()

    data = data[1:]
    counter = 0
    for i, row in enumerate(data):
        if counter % 50 == 0:
            print counter
        counter += 1
        line = 'insert into peptides values (' + str(i) + ', "'
        for col in row:
            current = col
            if not current:
                current = ''
            try:
                current=current.replace('"','').replace("'",'')
            except:
                pass
            line += str(current) + '", "'
        line = line[:-3]
        line += ');'
        try:
            c.execute(line)
        except:
            print line
            sdfdsf
    conn.commit()
    print "Building index..."
    line = 'create index ind1 on peptides(Spectrum);'
    c.execute(line)
    print "Done"
    print "Building index..."
    line = 'create index ind2 on peptides(Sequence);'
    c.execute(line)
    print "Done"    
    conn.commit()
    c.close()
    conn.close()
    return db

def convert_txt2sql(file):
    #Input: SpectrumSummary_filtered.txt
    #Protein Pilot exported data that has been filtered using "Filter_protein_pilot.mz"
    #Creates sql database representing this file and creates unique_queries table
    file_r = open(file, 'r')
    data = file_r.readlines()
    file_r.close()
    db = file[:-4] + '.db'
    conn = sql.connect(db)
    c = conn.cursor()
    cols = [x.strip() for x in data[0].split("\t")]
    bcount = 0
    for i, member in enumerate(cols):
        if not member:
            cols[i]="BLANK"+str(bcount)
            bcount+=1
    fl = [x.strip() for x in data[1].split("\t")]
    line = 'create table if not exists peptides (id integer primary key, '
    for i, col in enumerate(cols):
        line += '"' + col + '" ' + check_entry(fl[i]) + ', '  #' text, '
    line = line[:-2]
    line += ');'
    print line
    c.execute(line)
    conn.commit()
    line = 'create table if not exists unique_query (id integer primary key, '
    for i, col in enumerate(cols):
        line += '"' + col + '" ' + check_entry(fl[i]) + ', '  #' text, '
    line = line[:-2]
    line += ');'
    print line
    c.execute(line)
    conn.commit()

    data = data[1:]
    counter = 0
    for i, row in enumerate(data):
        if counter % 50 == 0:
            print counter
        counter += 1
        line = 'insert into peptides values (' + str(i) + ', "'
        for col in [x.strip() for x in row.split("\t")]:
            current = col
            if not current:
                current = ''
            try:
                current=current.replace('"','').replace("'",'')
            except:
                pass
            line += str(current) + '", "'
        line = line[:-3]
        line += ');'
        try:
            c.execute(line)
        except:
            print line
            sdfdsf
    conn.commit()
    print "Building index..."
    line = 'create index ind1 on peptides(Spectrum);'
    print "Done"
    c.execute(line)
    conn.commit()
    c.close()
    conn.close()
    return db

def get_unique_id(file):
    conn = sql.connect(file)

    c = conn.cursor()

    line = 'select distinct "Spectrum" from peptides;'
    spec = set()
    c.execute(line)
    a = c.fetchall()
    for member in a:
        spec.add(member[0])

    counter = 0
    for query in spec:
        counter += 1
        if counter % 100 == 0:
            print counter
        # take 1st id
        #line = 'select * from peptides where "Spectrum" = "' + query + '" and "Conf" = (select MAX("Conf") from peptides where "Spectrum" = "' + query + '");'
        line = 'select * from peptides where "Spectrum" = "' + query + '" and "id" = (select MIN("id") from peptides where "Spectrum" = "' + query + '");'
        c.execute(line)
        a = c.fetchone()
        #print a

        line = 'insert into unique_query values ' + str(a).replace("u''", '" "').replace("u'", '"').replace("'", '"').replace('""', '"') + ';'
        #print line
        try:
            c.execute(line)
        except:
            print line
            raise ValueError("SQL error")
    conn.commit()
    c.close()
    conn.close()

def make_pep_list(database, output_name):
    seqs = set()
    conn = sql.connect(database)
    c = conn.cursor()

    line = 'select distinct "Sequence" from "unique_query";'
    c.execute(line)
    a = c.fetchall()
    for member in a:
        seqs.add(member[0])
    c.close()
    conn.close()

    file_w = open(output_name, 'w')

    #for member in seqs:
    file_w.writelines([x + '\n' for x in seqs])

    file_w.close()

def concat(db_list):
    line = 'insert into peptides values('
    for entry in db_list:
        line += '"' + str(entry) + '", '
    line = line[:-2] + ');'
    return line

#help["make_sequence_database":'''
#[void] make_sequence_database(seqfile, dbFile)
#\n
#SEQFILE\n
#Reads protein sequence list\n
#A2AKK5-2	Acnat1 AAAAAHLITTTTTSSSSAAA...........\n
#and makes database of tryptic peptides indexed by sequence\n
#(id integer primary key, sequence text, gene text, accession text, start integer, end integer, mc integer);\n
#\n
#dfFile is the name of the database that is created.
#''']

def rev_check(seqFile,dbFile, out, notfind):
    outw = open(out,'w')
    notfindf =open(notfind, 'w')
    file_r = open(seqFile, 'r')
    data = file_r.readlines()
    file_r.close()
    conn = sql.connect(dbFile)
    c = conn.cursor()
    counter = 0
    for seq in data:
        if counter % 100 == 0:
            print counter
        counter += 1
        if seq:
            seq = seq.strip()
            #print seq
            line = 'select * from peptides where sequence="' + seq + '";'
            #print line
            c.execute(line)
            a = c.fetchall()
            #print a
            if a:
                #for member in a:
                    #(0-id, 1-sequence text, 2-gene text, 3-accession text, 4-start integer, 5-end integer, 6-mc integer, info text)
                print >>outw, seq
            else:
                print >>notfindf, seq

def make_fwd_db_from_fasta(fastafile, dbFile, enzyme="Trypsin", missed_cleavages = 2):
    '''
    Deprecated: use make_sequence_database
    '''
    print "Deprecated: use make_sequence_database"
    conn = sql.connect(dbFile)
    c = conn.cursor()
    line = 'create table if not exists peptides (id integer primary key, sequence text);'
    c.execute(line)
    conn.commit()
    counter = 0
    ind = 0
    print enzyme
    for header, sequence in mzFunctions.parse_fasta(fastafile):
        if counter % 5000 == 0:
            print counter
        counter += 1
        if header.find('REV_') == -1:
            digest = mzFunctions.digest(sequence, enzyme=enzyme, missed_cleavages = missed_cleavages)
            for entry in digest:
                seq = entry[0]
                line2 = 'insert into peptides values ("' + str(ind) + '", "' + seq + '");'
                try:
                    c.execute(line2)
                except:
                    print line2
                    dsd
                ind += 1
    conn.commit()
    print "indexing..."
    line = 'create index ind1 on peptides(sequence);'
    c.execute(line)
    conn.commit()
    print "Done"
    c.close()
    conn.close()

def make_revdb_from_fasta(fastafile, dbFile, enzyme="Trypsin", missed_cleavages = 2):
    conn = sql.connect(dbFile)
    c = conn.cursor()
    line = 'create table if not exists peptides (id integer primary key, sequence text);'
    c.execute(line)
    conn.commit()
    counter = 0
    ind = 0
    for header, sequence in mzFunctions.parse_fasta(fastafile):
        if counter % 5000 == 0:
            print counter
        counter += 1
        if header.find('REV_') > -1:
            digest = mzFunctions.digest(sequence, enzyme=enzyme, missed_cleavages = missed_cleavages)
            for entry in digest:
                seq = entry[0]
                line2 = 'insert into peptides values ("' + str(ind) + '", "' + seq + '");'
                try:
                    c.execute(line2)
                except:
                    print line2
                    dsd
                ind += 1
    conn.commit()
    print "indexing..."
    line = 'create index ind1 on peptides(sequence);'
    c.execute(line)
    conn.commit()
    print "Done"
    c.close()
    conn.close()

def make_sequence_database(seqfile, dbFile, enzyme="Trypsin", missed_cleavages = 6):
    '''
    
    Use to make forward sequence databases
    seqFile should be seq_mu0611_g
    dbFile is name of database
    
    '''
    conn = sql.connect(dbFile)
    c = conn.cursor()
    line = 'create table if not exists peptides (id integer primary key, sequence text, gene text, accession text, start integer, end integer, mc integer, info text);'
    c.execute(line)
    conn.commit()
    pro2en = {} # This is accession to gene dictionary
    pro2seq = {} #This is accession to sequence dictionary
    print "Parsing seqfile..."
    counter = 0
    for en in open(seqfile).xreadlines():
        if counter % 5000 == 0:
            print counter
        counter += 1
        en = en.strip().split("\t")
        pro2en[en[0]] = en[1]
        pro2seq[en[0]] = str(en[2])

    print "Making db..."
    ind = 0
    counter = 0
    for (k, v) in pro2seq.items():
        last_res = len(v)-1
        digest = mzFunctions.digest(v, enzyme=enzyme, missed_cleavages = missed_cleavages)
        for member in digest:
            if len(member[0]) < 100:
                if member[1][0]==0:
                    line = concat([ind, member[0], pro2en[k], k, member[1][0], member[1][1], member[2], "Head"])
                    c.execute(line)
                    if member[0][0]=='M': #If this is N-term Met, add the truncated to database!
                        ind += 1
                        line = concat([ind, member[0][1:], pro2en[k], k, member[1][0], member[1][1], member[2], "MHead"])
                        c.execute(line)
                elif member[1][1]==last_res:
                    line = concat([ind, member[0], pro2en[k], k, member[1][0], member[1][1], member[2], "End"])
                    c.execute(line)
                else:
                    line = concat([ind, member[0], pro2en[k], k, member[1][0], member[1][1], member[2], "Reguler"]) #Misspelled intentionally to match Shoajuan's code!!
                    c.execute(line)
                ind += 1
        if counter % 1000 == 0:
            print counter
        counter += 1

    print "indexing..."
    line = 'create index ind1 on peptides(sequence);'
    c.execute(line)
    conn.commit()
    print "Done"
    c.close()
    conn.close()

#help["peptide_search":'''
#[void] peptide_search(dbFile, peptides, seqfile, notfindf, outw)
#\n
#peptides\n
#text file list of unique peptide sequences for example one made by make_peptide_list\n
#
#Each one is opened and then a result file is created\n
#AIANVFQNR	Fryl	F8VQ05	MSSITID.............. START(1 indexed) END(1 indexed) INFO(Head, MHead, Reguler, End)\n
#dfFile is the name of the database of tryptic peptides.
#''']

def fast_peptide_search(dbFile, peptides, seqfile, notfind, out):
    outw = open(out,'w')
    notfindf =open(notfind, 'w')
    pro2en = {} # This is accession to gene dictionary
    pro2seq = {} #This is accession to sequence dictionary
    print "Parsing seqfile..."
    counter = 0
    for en in open(seqfile).xreadlines():
        if counter % 5000 == 0:
            print counter
        counter += 1
        en = en.strip().split("\t")
        pro2en[en[0]] = en[1]
        pro2seq[en[0]] = str(en[2])
    print "Connecting to database..."
    conn = sql.connect(dbFile)
    c = conn.cursor()
    print "Connected!"
    counter = 0
    for p in open(peptides).xreadlines(): # Loop through peptide sequences
        if counter % 1000 == 0:
            print counter
        counter += 1
        p = p.strip()
        if p:
            line = 'select * from peptides where sequence="' + p + '";'
            c.execute(line)
            a = c.fetchall()
            if a:
                for member in a:
                    #(0-id, 1-sequence text, 2-gene text, 3-accession text, 4-start integer, 5-end integer, 6-mc integer, info text)
                    print >>outw, p+"\t"+member[2]+"\t"+member[3]+"\t"+pro2seq[member[3]]+"\t"+str(member[4]+1)+"\t"+str(member[5]+1)+"\t" + member[7]
            else:
                print >>notfindf, p

#This module was written by Shaojuan
def three_classes(file, col1, col2, firstGroup, secondGroup):
    peptide = {}
    protein = {}

    for line in open(file).xreadlines():
        line = line.strip().split()
        if peptide.has_key(line[col1]):
            if not line[col2] in peptide[line[col1]]:
                peptide[line[col1]].append(line[col2])
        else:
            peptide[line[col1]] = [line[col2]]

        if protein.has_key(line[col2]):
            if not line[col1] in protein[line[col2]]:
                protein[line[col2]].append(line[col1])
        else:
            protein[line[col2]] = [line[col1]]

    peptide_class = {}
    protein_class = {}

    for k in peptide.keys():
        if len(peptide[k]) == 1:
            peptide_class[k] = 1
            protein_class[peptide[k][0]] = 1

    for k in protein_class.keys():
        if protein_class[k] == 1 and len(protein[k]) > 1:
            for m in protein[k]:
                if not peptide_class.has_key(m):
                    peptide_class[m] = 2

    for k in peptide.keys():
        if not peptide_class.has_key(k):
            peptide_class[k] = 3

    for k in peptide_class.keys():
        if peptide_class[k] == 3:
            for m in peptide[k]:
                if not protein_class.has_key(m):
                    protein_class[m] = 3

    for k in protein.keys():
        if not protein_class.has_key(k):
            protein_class[k] = 2

    firstout = open(firstGroup, 'w')
    secondout = open(secondGroup, 'w')

    for i in range(1, 4):
        for k in peptide_class.keys():
            if peptide_class[k] == i:
                fp = []
                sp = []
                tp = []
                for p in list(set(peptide[k])):
                    if protein_class[p] == 1:
                        fp.append(p)
                    if protein_class[p] == 2:
                        sp.append(p)
                    if protein_class[p] == 3:
                        tp.append(p)
                print >>firstout, str(i)+ '\t' + k + '\t' + ';'.join(list(set(peptide[k]))) + '\t'+ str(len(list(set(peptide[k])))) \
                + '\t' + ';'.join(list(set(fp)))+ '|' + ';'.join(list(set(sp))) + '|' + ';'.join(list(set(tp))) + '\t' + str(len(list(set(fp))))+ '|' + str(len(list(set(sp)))) + '|' + str(len(list(set(tp)))) \
                + '\t' + ';'.join(list(set(fp)))+ '\t' + ';'.join(list(set(sp))) + '\t' + ';'.join(list(set(tp))) + '\t' + str(len(list(set(fp))))+ '\t' + str(len(list(set(sp)))) + '\t' + str(len(list(set(tp))))

    for i in range(1, 4):
        for k in protein_class.keys():
            if protein_class[k] == i:
                fp = []
                sp = []
                tp = []
                for p in list(set(protein[k])):
                    if peptide_class[p] == 1:
                        fp.append(p)
                    if peptide_class[p] == 2:
                        sp.append(p)
                    if peptide_class[p] == 3:
                        tp.append(p)
                print >>secondout, str(i)+ '\t' + k + '\t' + ';'.join(list(set(protein[k]))) + '\t'+ str(len(list(set(protein[k])))) \
                + '\t' + ';'.join(list(set(fp)))+ '|' + ';'.join(list(set(sp))) + '|' + ';'.join(list(set(tp))) + '\t' + str(len(list(set(fp))))+ '|' + str(len(list(set(sp)))) + '|' + str(len(list(set(tp)))) \
                + '\t' + ';'.join(list(set(fp)))+ '\t' + ';'.join(list(set(sp))) + '\t' + ';'.join(list(set(tp))) + '\t' + str(len(list(set(fp))))+ '\t' + str(len(list(set(sp)))) + '\t' + str(len(list(set(tp))))

def filter_protein_pilot(pep_sum, CUTOFF):
    '''
    Written by James Webber.  Input = text file of protein pilot data.  Removes entries with Conf below cutoff value.
    Renames extending _filtered.txt
    '''
    rdr = csv.reader(open(pep_sum, 'rb'), delimiter='\t')
    wtr = csv.writer(open(pep_sum[:-4] + '_filtered.txt', 'wb'), delimiter='\t')
    cols = rdr.next()
    conf_index = cols.index('Conf')
    wtr.writerow(cols)
    wtr.writerows(row for row in rdr if float(row[conf_index]) >= CUTOFF)
    print 'Done'

def annotate_pilot_xls_with_file(filename, sheetname, mapfilename='File Map.txt'):
    '''
    Filename is xls of pilot results.  Expects map file in same directory (get this from Protein Pilot).  
    Creates a dictionary of file number (from locus in Spectrum) to file name.
    Filename should not be full path, dirname of filename added
    '''
    pa = re.compile('(\d+?)[\)] ([0-9a-zA-Z:.\\\\_\-]+)')
    file_r = open(os.path.dirname(filename)+'\\' + mapfilename)
    file_dict = {}
    data = file_r.readlines()
    for member in data:
        id = pa.match(member)
        if id:
            file_dict[int(id.groups()[0])]=os.path.basename(id.groups()[1])
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    wtr = mzReport.writer(filename, columns=rdr.columns+['File'],sheet_name=sheetname)
    counter = 0
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        spec = row["Spectrum"]
        row["File"]=file_dict[int(spec.split(".")[0])]
        wtr.write(row)
    rdr.close()
    wtr.close()

def LysCpeptideSearch(peptides, seqfile, out, notfind ):
    outw = open(out,'w')
    notfindf =open(notfind, 'w')
    pro2en = {} # This is accession to gene dictionary
    pro2seq = {} #This is accession  to sequence dictionary
    for en in open(seqfile).xreadlines():
        en = en.strip().split("\t")
        pro2en[en[0]] = en[1]
        pro2seq[en[0]] = str(en[2])
    counter = 0
    st = time.clock()
    file_r = open(peptides, 'r')
    data = file_r.readlines()
    num = len(data)-1
    file_r.close()
    for p in open(peptides).xreadlines(): # Loop through peptide sequences
        if counter % 10 == 0:
            print str(counter) +' of ' + str(num)
            now = time.clock()
            total = now-st
            av = float(total)/float(counter + 1)
            remaining = num - counter
            print "Estimated " + str(float(remaining * av)/float(60.0)) + ' minutes remaining'
        counter+=1
        p = p.strip()
        if p:
            reg1 = p+'[^P]' # P is peptide sequence
            reg2 = '[K]'+p
            reg3 = '[K]'+p+'[^P]'
            ex1 = re.compile(reg1)
            ex2 = re.compile(reg2)
            ex3 = re.compile(reg3)
            ii = 0
            for (k,v) in pro2seq.items():
                i = 0
                iterator1 = ex1.finditer(v)
                for match1 in iterator1:
                    if match1.start() == 0 and p[-1] == "K":
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match1.start()+1)+"\t"+str(match1.start()+ len(p))+"\tHead"
                        i = 1
                        ii = 1
                        break
                    if match1.start() == 1 and p[-1] == "K":
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match1.start()+1)+"\t"+str(match1.start()+ len(p))+"\tMHead"
                        i = 1
                        ii = 1
                        break
                if i == 0:
                    iterator2 = ex2.finditer(v)
                    for match2 in iterator2:
                        if match2.end() == len(v):
                            print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match2.start()+2)+"\t"+str(match2.start()+ len(p)+1)+"\tEnd"
                            i = 1
                            ii = 1
                            break
                if i == 0 and p[-1] == "K":
                    iterator3 = ex3.finditer(v)
                    for match3 in iterator3:
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match3.start()+2)+"\t"+str(match3.start()+ len(p)+1)+"\tReguler"
                        i = 1
                        ii = 1
                        break
            if ii ==0:
                print >>notfindf, p

def peptideSearch_pilot_data(xlsfile, sheetname="Data", dbFile=''):
    rdr = mzReport.reader(xlsfile, sheet_name=sheetname)
    wtr = mzReport.writer(xlsfile, sheet_name=sheetname, columns = rdr.columns + ["Combined Accessions", "Combined Genes"])
    conn = sql.connect(dbFile)
    c = conn.cursor()
    print dbFile
    print "Connected!" 
    counter = 0
    for row in rdr:
        #print "LOOPING"
        try:
            seq = row["Sequence"]
        except:
            seq = row["Peptide Sequence"]
        #print seq
        if counter % 1000 == 0:
            print counter
        counter += 1
        line = 'select * from peptides where sequence="' + seq + '";'
        c.execute(line)
        a = c.fetchall()
        accs = []
        genes = set()
        for member in a:
            accs.append(member[3])
            genes.add(member[2])
        row["Combined Accessions"] = str(accs).replace("u'", '').replace("'", '').replace("[",'').replace("]",'')
        row["Combined Genes"] = str(list(genes)).replace("u'", '').replace("'", '').replace("[",'').replace("]",'')
        wtr.write(row)
    rdr.close()
    wtr.close()
    c.close()
    conn.close()
    print dbFile
    print "Detached!"
    
def peptideSearch(peptides, seqfile, out, notfind ):
    outw = open(out,'w')
    notfindf =open(notfind, 'w')
    pro2en = {} # This is accession to gene dictionary
    pro2seq = {} #This is accession  to sequence dictionary
    for en in open(seqfile).xreadlines():
        en = en.strip().split("\t")
        pro2en[en[0]] = en[1]
        pro2seq[en[0]] = str(en[2])
    counter = 0
    st = time.clock()
    file_r = open(peptides, 'r')
    data = file_r.readlines()
    num = len(data)-1
    file_r.close()
    for p in open(peptides).xreadlines(): # Loop through peptide sequences
        if counter % 10 == 0:
            print str(counter) +' of ' + str(num)
            now = time.clock()
            total = now-st
            av = float(total)/float(counter + 1)
            remaining = num - counter
            print "Estimated " + str(float(remaining * av)/float(60.0)) + ' minutes remaining'
        counter+=1
        p = p.strip()
        if p:
            reg1 = p+'[^P]' # P is peptide sequence
            reg2 = '[KR]'+p
            reg3 = '[KR]'+p+'[^P]'
            ex1 = re.compile(reg1)
            ex2 = re.compile(reg2)
            ex3 = re.compile(reg3)
            ii = 0
            for (k,v) in pro2seq.items():
                i = 0
                iterator1 = ex1.finditer(v)
                for match1 in iterator1:
                    if match1.start() == 0 and ( p[-1] == "K" or p[-1] == "R" ):
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match1.start()+1)+"\t"+str(match1.start()+ len(p))+"\tHead"
                        i = 1
                        ii = 1
                        break
                    if match1.start() == 1 and ( p[-1] == "K" or p[-1] == "R" ):
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match1.start()+1)+"\t"+str(match1.start()+ len(p))+"\tMHead"
                        i = 1
                        ii = 1
                        break
                if i == 0:
                    iterator2 = ex2.finditer(v)
                    for match2 in iterator2:
                        if match2.end() == len(v):
                            print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match2.start()+2)+"\t"+str(match2.start()+ len(p)+1)+"\tEnd"
                            i = 1
                            ii = 1
                            break
                if i == 0 and ( p[-1] == "K" or p[-1] == "R" ):
                    iterator3 = ex3.finditer(v)
                    for match3 in iterator3:
                        print >>outw, p+"\t"+pro2en[k]+"\t"+k+"\t"+v+"\t"+str(match3.start()+2)+"\t"+str(match3.start()+ len(p)+1)+"\tReguler"
                        i = 1
                        ii = 1
                        break
            if ii ==0:
                print >>notfindf, p

def combine_out(file1, file2):
    file1_r = open(file1, 'r')
    data1 = file1_r.readlines()
    file1_r.close()
    file2_r = open(file2, 'r')
    data2 = file2_r.readlines()
    file2_r.close()
    dir = os.path.dirname(file1)
    out_w = open(dir + '\\Combined_out.txt', 'w')
    out_w.writelines(data1+data2)

def protein_pilot_phos_analysis(filename, sheetname):
    '''
    Reads pilot formatted sheet, counting seq | number of phos (other mods like MetOx not included)
    Returns length of sets for all peps and phos peps, as well as the actual set of phosphopeps.
    Last modified 2012-11-02
    '''      
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    counter = 0
    allpeps=set()
    phosphopeps = set()
    for row in rdr:
        if counter % 1000 ==0:
            print counter
        counter += 1
        seq = row["Sequence"]
        mod = row["Modifications"]
        if not mod:
            mod = ""
        phos = mod.count("Phospho")
        key = seq + "|" + str(phos)
        allpeps.add(key)
        if phos > 0:
            phosphopeps.add(key)
    rdr.close()
    return len(allpeps), len(phosphopeps), phosphopeps
        
def mascot_phos_analysis(filename, sheetname):
    '''
    Reads mascot formatted sheet, counting seq | number of phos (other mods like MetOx not included)
    Returns length of sets for all peps and phos peps, as well as the actual set of phosphopeps.
    Last modified 2012-11-02
    '''    
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    counter = 0
    allpeps=set()
    phosphopeps = set()
    for row in rdr:
        if counter % 1000 ==0:
            print counter
        counter += 1
        seq = row["Peptide Sequence"]
        mod = row["Variable Modifications"]
        if not mod:
            mod = ""
        phos = mod.count("Phospho")
        key = seq + "|" + str(phos)
        allpeps.add(key)
        if phos > 0:
            phosphopeps.add(key)
    rdr.close()
    return len(allpeps), len(phosphopeps), phosphopeps

def create_filtered_phos_sheet_for_pilot(filename, sheet_name='fdr'):
    '''
    Expects _filtered.xls file
    Outputs _filtered2.xls file.
    Does not write to new sheet if (1) not phosphorylated, (2) does not pass FDR, (3) is from the reverse database, (4) is not iTRAQ labeled, (5) is not fully labeled
    '''
    print "PROC:" + filename
    rdr = mzReport.reader(filename, sheet_name=sheet_name)
    if "Scan" in rdr.columns:
        cols = rdr.columns
    else:
        cols = rdr.columns + ["Scan"]    
    wtr = mzReport.writer(filename[:-4]+'2.xls', columns=cols, sheet_name='fdr')
    counter = 0
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        mods = row["Modifications"]
        passed = row["passed"]
        dbase = row['db']
        spec = row["Spectrum"]
        scan = int(spec.split(".")[3])
        row["Scan"]=scan        
        if mods.find("Phospho") > -1 and passed == True and dbase == 'FWD' and mods.find("iTRAQ") > -1 and mods.find("No iTRAQ")==-1:
            wtr.write(row)
    rdr.close()
    wtr.close()       

def pilot_combine_reporters(filename, sheetname, type='iTRAQ(8-plex)'):
    if type == "iTRAQ":
        rep_cols = (114, 115, 116, 117)
    if type == "TMT":
        rep_cols = (126, 127, 128, 129, 130, 131)
    if type == "iTRAQ(8-plex)":
        rep_cols = (113, 114, 115, 116, 117, 118, 119, 121)
    rep_names = ['i%d'%i for i in rep_cols]    
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    
    cols = rdr.columns[:]
    cols.extend(['Peptide Count', 'Top Peptide Score'])
    cols.extend('Summed %d' % c for c in rep_cols)
    cols.extend('Max %d' % c for c in rep_cols)

    wtr = mzReport.writer(filename[:-4] + '_summed_rep.xls',
                          columns=cols, sheet_name = sheetname)
    
    peptides = defaultdict(list)
    
    for row in rdr:
        peptides[(row['Sequence'], row['Modifications'])].append(row)

    rdr.Close()

    for k in sorted(peptides.keys()):
        pep_list = peptides[k]

        max_score = max(row['Conf'] for row in pep_list)

        rep_vals = [(row, tuple(float(c) for c in [row[i] for i in rep_names])) for row in pep_list]

        summed_rep = [sum(v[i] for r,v in rep_vals) for i in range(len(rep_cols))]

        max_row,max_rep = max(rep_vals, key=lambda (r,v): sum(v))

        max_row['Peptide Count'] = len(pep_list)
        max_row['Top Peptide Score'] = max_score

        max_row.update(('Summed %d' % c, summed_rep[i]) for i,c in enumerate(rep_cols))
        max_row.update(('Max %d' % c, max_rep[i]) for i,c in enumerate(rep_cols))

        wtr.write(max_row)

    wtr.close()    

def make_quant_dict_from_directory(dirname, outputfile):
    '''
    Makes a master quant dict from a directory containing mgfs.
    Key is filename + "|" + str(scan) = quant (list)
    outputfile should be the whole path, including the directory
    CAD or HCD doesn't matter - correct quant already embedded in mgf
    '''
    mgfs = glob.glob(dirname + '\\*.mgf')
    master_dict = {}
    counter = 0
    for mgf in mgfs:
        print counter
        counter+= 1
        mgf_dict = make_quant_dict_from_mgf(mgf)
        master_dict.update(mgf_dict)
    pickle_file = open(outputfile, "w")
    cPickle.dump(master_dict, pickle_file)
    pickle_file.close()    

def make_quant_dict_from_mgf(filename):
    file_r = open(filename, 'r')
    data = file_r.readlines()
    file_r.close()
    #TITLE=2012-09-05-Luckey-CD44-iTRAQ-pST-0-0.631.631.3.dta - 381.96480|0|0|0|0|0|0|0|0|INTERNAL
    pa = re.compile('TITLE=([-\dA-Za-z_]+?)\.(\d+?)\.')
    mgf_dict = {}
    for line in data:
        if line.find("TITLE=") > -1:
            id = pa.match(line)
            (filename, scan) = id.groups()
            quant = [int(x) for x in line.split(" - ")[1].split("|")[1:-1]]
            mgf_dict[filename + "|" + str(scan)] = quant
    return mgf_dict

motif_dict = {'AKT':'.+?[R][A-Z][A-Z][ST]',
              'PKA':'.+?[RK][RK][A-Z][ST]'}
        
def motif_analysis(filename, sheetname="Data", motif = "AKT"):
    '''
    General script for analyzing peptides for motifs.  Motif regexes are derived from motif_dict.
    Right now, supports AKT and PKA motifs.
    '''
    site_pa = re.compile('.?[STY]([0-9]+): Phospho')
    pa = re.compile(motif_dict[motif])
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    try:
        wtr = mzReport.writer(dir+"\\"+file, columns=rdr.columns+['Pattern Match', 'Site Match', 'Exp Site', 'Match Site', 'Site Lib'], sheet_name="Data")
    except:
        wtr = mzReport.writer(dir+"\\"+file, columns=rdr.columns, sheet_name="Data")

    print "WORKING ON... " + file
        
    for i, row in enumerate(rdr):
        if i % 50 == 0:
            print "working on row... " + str(i)
        seq = row["Peptide Sequence"]
        varmod = row["Variable Modifications"]
        if not varmod:
            varmod = ''
        pm = False
        sm = False
        exp_site = None
        match_site = None
        site_library = None
        if varmod.find("Phospho") > -1:
            id = pa.match(seq)
            if id:
                match_site = len(id.group())
                pm = True
                site_library = []
                for mod in varmod.split(";"):
                    site_id = site_pa.match(mod)
                    if site_id:
                        site = int(site_id.groups()[0])
                        site_library.append(site)
                if match_site in site_library:
                    sm = True
                    exp_site = match_site
        row["Pattern Match"] = pm
        row['Site Match'] = sm
        row['Exp Site'] = exp_site
        row['Match Site'] = match_site
        row['Site Lib'] = str(site_library)
        wtr.write(row)
    
    rdr.close()
    wtr.close()    
    

key_translate = {"File":"File", "Accessions":"Accession Number", "Names":"Protein Description", "Sequence":"Peptide Sequence", "Modifications":"Variable Modifications", 'Protein Relative Mods':'Protein-Relative Modifications',
                 "Conf":"Conf", "Cleavages":"Missed Cleavages", "dMass":"Delta", "Prec m/z":"Experimental mz", "Theor MW":"Predicted mr", "Theor z":"Charge", "fdr":"FDR", "Scan Type":"Scan Type", "Spectrum":"Spectrum Description"}

parse_mod = re.compile(r'(?P<type>[A-Z0-9]+)(?:\()?(?P<aa>[A-Z])?(?:\)?)?(?:@)(?P<position>[A-Z0-9-]+)', re.IGNORECASE)
   
def read_sheet(filename, sheetname, keys, pilot=False):
    '''
    Reads an xls file.  Makes a dictionary called sub_sheet where keys are SEQUENCE|VAR MOD and values are dictionaries of column header to value.
    Note: iTRAQ and carbamidomethylation from pilot mod styles are ignored to align with Mascot results.
    For pilot sheets, keys are adjusted to match Mascot naming conventions.
    Columns deemed unimportant i.e. not in list "keys" are ignored and are NOT written to the final file.
    For Mascot sheets, Conf is added with "NA" value, and Peptide Score is added to Pilot rows also with "NA"
    '''
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    counter = 0
    sub_sheet = defaultdict(dict)
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        new_row = {}
        for key in keys:
            if pilot:
                if key != "Modifications":
                    if key.find("Summed") > -1 or key.startswith("c") or key.find("Max") > -1:
                        new_row[key] = row[key]
                    else:
                        new_row[key_translate[key]] = row[key]
                else:
                    translate = ''
                    for member in parse_mod.findall(row["Modifications"]):
                        if member[0].find("iTRAQ") == -1 and member[0].find("Carbamido") == -1:
                            if member[2] != 'N-term':
                                translate += member[1] + member[2] + ': ' + member[0] + '; '  # S311: Phospho; N-term: Acetyl
                            else:
                                translate += 'N-term: ' + member[0] + '; '
                    new_row[key_translate[key]] = translate[:-2]
                    new_row["Peptide Score"] = 'NA'
            else:
                new_row[key] = row[key]
                new_row["Conf"] = 'NA'
        dict_key = new_row["Peptide Sequence"] + '|' + new_row["Variable Modifications"]
        sub_sheet[dict_key] = new_row
    rdr.close()    
    return sub_sheet
    
def pilot_mascot_combine(pilot_filename, pilot_sheetname, mascot_filename, mascot_sheetname, output_filename, quant='i8'):
    '''
    Right now, quant only supports iTRAQ-8plex.
    Reads Pilot Sheet and Mascot Sheet, making a new set of rows according to specified keys.
    Pilot names are converted to Mascot names, when applicable.
    
    Give all full path names.
    '''
    if quant == 'i8':
        reps = [str(113 + i) for i in range(0,7)]+["121"]
        quant_cols = []
        for member in ["Summed ", "Max ", "c"]:
            quant_cols += [member + i for i in reps]
    pilot_keys = ["File", "Accessions", "Names", "Sequence", "Modifications", 'Protein Relative Mods', "Conf", "Cleavages", "dMass", "Prec m/z", "Theor MW", "Theor z", "fdr", "Scan Type", "Spectrum"] + quant_cols
    print "Parsing Pilot"
    pilot_data = read_sheet(pilot_filename, pilot_sheetname, pilot_keys, True)
    mascot_keys = ["File", "Accession Number", "Protein Description", "Peptide Sequence", "Variable Modifications", 'Protein-Relative Modifications', "Peptide Score", "Missed Cleavages", "Delta", "Experimental mz", "Predicted mr", "Charge",  "FDR", "Scan Type", "Spectrum Description"] + quant_cols
    print "Parsing Mascot"
    mascot_data = read_sheet(mascot_filename, mascot_sheetname, mascot_keys, False)
    all_keys = set(pilot_data.keys() + mascot_data.keys())
    mascot_keys.insert(mascot_keys.index('Peptide Score')+1, 'Conf')
    mascot_keys += ['Search Type']
    wtr = mzReport.writer(output_filename, sheet_name="Data", columns=mascot_keys)
    print 'writing...'
    counter = 0
    for key in all_keys:
        if counter % 1000 == 0:
            print counter
        counter += 1
        if key in pilot_data.keys() and key in mascot_data.keys():
            current_row = mascot_data[key]
            current_row["Conf"] = pilot_data[key]["Conf"] # Mascot data has a blank entry for Conf, must update
            for entry in ["Delta", "Experimental mz", "Predicted mr" , "FDR", "Scan Type", "Spectrum Description"]:
                current_row[entry] = 'M: ' + str(mascot_data[key][entry]) + '|P: ' + str(pilot_data[key][entry]) #Merges Mascot and Pilot entries to retain both sets
            current_row["Search Type"] = 'Both'
            current_row["File"] = os.path.basename(current_row["File"]).split("_")[0]
            wtr.write(current_row)
        elif key in pilot_data.keys() and key not in mascot_data.keys():
            current_row = pilot_data[key]
            current_row["Search Type"] = 'Pilot'
            current_row["File"] = current_row["File"].split("_")[0]
            wtr.write(current_row)
        elif key in mascot_data.keys() and key not in pilot_data.keys():
            current_row = mascot_data[key]
            current_row["Search Type"] = 'Mascot'
            current_row["File"] = os.path.basename(current_row["File"]).split("_")[0]
            wtr.write(current_row)        
    wtr.close()


def pilot_combine_CID_HCD_Lo_HCD_Hi(cid_sheet, hcd_ltq_sheet, hcd_ft_sheet):
    '''
    Input is 'filtered2.xls' files.
    Filenames should be formatted like 2012-11-16-Luckey-CD44-iTRAQ-pST-15-110 i.e. no _ characters
    '''
    print "READ CID"
    print cid_sheet
    cid_rdr = mzReport.reader(cid_sheet, sheet_name = 'fdr')
    print "READ HCD-FT"
    print hcd_ft_sheet
    hcd_ft_rdr = mzReport.reader(hcd_ft_sheet, sheet_name = 'fdr')
    print "READ HCD-LTQ"
    print hcd_ltq_sheet
    hcd_ltq_rdr = mzReport.reader(hcd_ltq_sheet, sheet_name = 'fdr')
    cols = cid_rdr.columns[:]
    new_cols = ['Scan Type', 'Found in Other File?']
    rows = defaultdict(list)
    #29.1.1.2549.4
    print "CID"
    for row in cid_rdr:
        scan_num = row["Spectrum"].split(".")[3]
        file_split = row["File"].split("_")
        if row["File"].find("2012-12-07") > -1:
            file_name = file_split[0] + "_" + file_split[1]
        else:
            file_name = file_split[0]
    
        row['Scan Type'] = 'CID'
    
        rows[(file_name, int(scan_num))].append(row)
    
    cid_rdr.close()
    
    print "HCD-FT"
    for row in hcd_ft_rdr:
        scan_num = row["Spectrum"].split(".")[3]
        file_split = row["File"].split("_")
        if row["File"].find("2012-12-07") > -1:
            file_name = file_split[0] + "_" + file_split[1]
        else:
            file_name = file_split[0]
    
        row['Scan Type'] = 'HCD-FT'
    
        rows[(file_name, int(scan_num))].append(row)
    
    hcd_ft_rdr.close()
    
    print "HCD-LTQ"
    for row in hcd_ltq_rdr:
        scan_num = row["Spectrum"].split(".")[3]
        file_split = row["File"].split("_")
        if row["File"].find("2012-12-07") > -1:
            file_name = file_split[0] + "_" + file_split[1]
        else:
            file_name = file_split[0]
    
        row['Scan Type'] = 'HCD-LTQ'
    
        rows[(file_name, int(scan_num))].append(row)
    
    hcd_ltq_rdr.close()
    
    wtr = mzReport.writer(os.path.join(os.path.dirname(cid_sheet),
                                       'Combined_CID-HCD.xls'),
                          columns = cols + new_cols)
    
    
    counter = 0
    for k in rows:
        if counter % 1000 == 0:
            print counter
        counter += 1
        if len(rows[k]) == 1:
            row = rows[k][0]
            row['Found in Other File?'] = 'No'
            #row.update(na_row)
            wtr.WriteRow(row)
        elif len(rows[k]) == 2:
            #print str(rows[k])
            #print str(sorted(rows[k], key=lambda r: r['Peptide Score']))
            lo_row, hi_row = sorted(rows[k], key=lambda r: r['Conf'])
    
            hi_row['Found in Other File?'] = 'Yes'
    
            wtr.write(hi_row)
        else:
            #print len(sorted(rows[k], key=lambda r: r['Conf']))
            lo_row, medium_row, hi_row = sorted(rows[k], key=lambda r: r['Conf'])
    
            hi_row['Found in Other File?'] = 'Yes'
    
            wtr.write(hi_row)    
    
    wtr.close()    
    
def pilot_populate_quant_in_xls_from_dicts(CAD_Dict, HCD_Dict, filename, label_type='iTRAQ(8-plex)'):
    '''
    CAD_Dict and HCD_Dict should be pkl files created using make_quant_dict_from_mgf (or directory).
    Filename is the name of the file to add quant from
    Full paths should be given
    
    Right now only iTRAQ(8-plex) supported.
    
    Adds columns i114, i115, etc. depending on label type.
    
    Filename should not have any _ characters.
    '''
    supported_labels=['iTRAQ(8-plex)']
    if label_type not in supported_labels:
        raise ValueError('Label type not supported!')
    if label_type == 'iTRAQ(8-plex)':
        cols = ['i'+str(113 + x) for x in range(0,7)]+['i121']
        
    print "Loading CAD"
    pickle_file = open(CAD_Dict, "r")
    CAD = cPickle.load(pickle_file)
    pickle_file.close()
    
    print "Loading HCD"
    pickle_file = open(HCD_Dict, "r")
    HCD = cPickle.load(pickle_file)
    pickle_file.close()
    
    #print HCD['2012-09-05-Luckey-CD44-iTRAQ-pST-0-0|3926']
    
    rdr = mzReport.reader(filename, sheet_name = "Data")
    
    try:
        wtr = mzReport.writer(filename, columns = rdr.columns + cols, sheet_name = "Data")
    except:
        wtr = mzReport.writer(filename, columns = rdr.columns, sheet_name = "Data")
    counter = 0
    scans = {}
    scans.update(CAD)
    scans.update(HCD)
    for row in rdr:
        if counter % 1000 == 0:
            print counter
        counter += 1
        if row['File'].find('2012-12-07') == -1:
            filename = row["File"].split("_")[0]
        else:
            filename = row["File"].split("_")[0] + '_' + row["File"].split("_")[1]
        scan = int(row["Scan"])
        key = filename+"|"+str(scan)
        quant = scans[key]
        for i, col in enumerate(cols):
            row[col]=quant[i]
        wtr.write(row)
    rdr.close()
    wtr.close()    
    
def pilot_make_db_of_protein_mappings(filename):
    pass

def evaluate_cys_freq(filename, sheet='Data'):
    
    seqs = set()
    rdr = mzReport.reader(filename, sheet_name = sheet)
    
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print counter
        counter += 1
        desc = row["Protein Description"]
        acc = row["Accession Number"]        
        
        if acc.find("rev_gi") == -1 and desc.find("Marto") == -1:
            seq = row["Peptide Sequence"]
            varmod = row["Variable Modifications"]   
            if not varmod:
                varmod = "None"            
            seqs.add(seq + "|" + varmod)
    total=len(seqs)
    cys = 0
    for member in seqs:
        seq = member.split("|")[0]
        if seq.find("C") > -1:
            cys += 1
    result = {"Total":total, "Cys":cys}
    return result

def apply_mass_accuracy_filter_to_multiplierz_report(filename, sheetname="Data", ppm=25):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename[:-4]+'_'+str(ppm)+'ppmFiltered.xls', columns=rdr.columns + ['ppm'], sheet_name = sheetname)
    
    counter = 0
    for row in rdr:
        if counter % 100 == 0:
            print counter
        counter += 1
        theor = row["Predicted mr"]
        delta = row["Delta"]
        row['ppm'] = (abs(float(delta))/float(theor))*1000000
        if row['ppm'] < ppm:
            wtr.write(row)
    rdr.close()
    wtr.close()


def phospho_site_report(filename, sheetname="Data", sequence_tag= None, score_cutoff=15, MD_score_cutoff=11):
    '''
    
    Reads a multiplierz search result with MD Score column.
    If entry:
    1) is a phosphopeptide
    2) has MD score above threshold
    3) (if specified) has a sequence listed in sequence tag (matched by find, not starts with)
    4) has mascot score > score cutoff
    Will be written to output file.
    
    '''
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    counter = 0
    result = []
    for row in rdr:
        if counter % 100 == 0:
            print counter
        counter += 1
        MDscore = row["MD Score"]
        if not MDscore:
            MDscore = -10000        
        score = row["Peptide Score"]
        seq = row["Peptide Sequence"]
        varmod = row["Protein Relative Modifications"]
        proceed = True
        if float(score) < score_cutoff:
            proceed = False
        if not varmod:
            varmod = ''
        if varmod.find("Phospho") == -1:
            proceed = False
        if sequence_tag:
            if seq.find(sequence_tag) == -1:
                proceed = False
        if float(MDscore) < MD_score_cutoff:
            proceed = False
        if proceed:
            result.append([seq, varmod, str(score), str(MDscore)])
    out_w = open(os.path.dirname(filename) + '\\output.txt', 'w')
    for member in result:
        out_w.write(", ".join(member) + '\n')
    out_w.close()
    rdr.close()    
        
def compare_quants(filenames, sheetname, use_cg=False, outputfilename='Quant_Compare.csv'):
    '''
    
    filenmames should be a list of files
    
    '''
    c_dir = os.path.dirname(filenames[0])
    def get_pep_dict(filename, use_cg=False):
        rdr = mzReport.reader(filename, sheet_name = sheetname)
        counter = 0
        peps = {}
        for row in rdr:
            if counter % 100 == 0:
                print counter
            counter += 1
            seq = row['Peptide Sequence']
            varmod = row['Variable Modifications']
            q = row['Peak Intensity']
            if use_cg:
                cg = row['Charge']
            if not varmod:
                varmod = "None"
            if not use_cg:
                key = seq + '|' + varmod
            else:
                key = seq + '|' + varmod + '|' + str(cg)
            if key not in peps:
                peps[key]=q
            else:
                current_q = peps[key]
                if q > current_q:
                    peps[key] = q
        rdr.close()
        return peps
    master_dict = {}
    masterkeys = set()
    for filename in filenames:
        print "Reading... " + filename
        master_dict[filename] = get_pep_dict(filename, use_cg)
        masterkeys.update(master_dict[filename].keys())
    wtr = csv.writer(open(cdir + '\\' + outputfilename, 'wb'), delimiter=',', quotechar='|')
    wtr.writerow(['Key'] + [key for key in master_dict.keys()])
    for pepkey in masterkeys:
        output = [pepkey]
        for filename in master_dict.keys():
            if pepkey in master_dict[filename]:
                output += [master_dict[filename][pepkey]]
            else:
                output += [0]
        wtr.writerow(output)


def extract_gene_name_from_uniprot_entry(filename, sheetname='Data'):
    '''
    
    Version 0.1 2014-07-18
    From: Uncharacterized protein OS=Oryctolagus cuniculus GN=CRKL PE=4 SV=1
    Updates 'GeneName' column with CRKL
    
    '''
    pa = re.compile('.*?GN=([A-Za-z0-9]+?) ')
    rdr = mzReport.reader(filename, sheet_name=sheetname)
    wtr = mzReport.writer(filename, columns=rdr.columns, sheet_name=sheetname)
    for row in rdr:
        geneSet = set()
        descs = row['Protein Description'].split(';')
        for desc in descs:
            id=pa.match(desc)
            if id:
                geneSet.add(id.groups()[0])
            else:
                geneSet.add(desc[:desc.find(' OS=')])
        if geneSet:
            row['GeneName']=clean_text(str(geneSet))
        else:
            row['GeneName']='NA'
        wtr.write(row)
    rdr.close()
    wtr.close()
        
def convert_mzd_to_xls(filename):
    rdr = mzReport.reader(filename)
    wtr = mzReport.writer(filename[:-4] + '.xlsx', columns=rdr.columns, sheet_name="Data")
    for row in rdr:
        wtr.write(row)
    rdr.close()
    wtr.close()
