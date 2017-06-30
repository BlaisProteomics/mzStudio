#2011-04-10-Kinase-Matcher-v1
#Uses uniprot kinases
#Matches peptides from sheet to Uniprot database
import mz_workbench.protein_core
import multiplierz.mzReport.mzSpreadsheet as mzSpreadsheet
import collections
import multiplierz.mass_biochem as mzFunctions
import multiplierz.mzReport as mzReport

import wx
import os

def get_sheet(filename, sheetname):
    xl_app = mzSpreadsheet._start_excel()

    data_list = []

    workbook = xl_app.Workbooks.Open(filename)
    sheet_list = [str(workbook.Worksheets(i).Name) for i in range(1,workbook.Worksheets.Count + 1)]
    if sheetname in sheet_list: 
        #GETTING COLUMN NUMBERS
        data = workbook.Worksheets(sheetname).Range("A1").CurrentRegion.Value
        data_list = [list(row) for row in list(data)]
        columns = len(data_list[0])
        rows = len(data_list)
        print columns
        print rows

    workbook.Close(SaveChanges=0)
    return rows, columns, data_list

def get_headers(data_list):
    headers = {}
    columns = len(data_list[0])
    for i in range(0, columns):
        headers[data_list[0][i]] = i
    return headers

def Write_Output(filename, sheetname, out_list):
    wtr = mzReport.writer(filename, columns =['Output'], sheet_name = sheetname)
    row = {}
    for line in out_list:
        row['Output'] = line
        wtr.write(row)
    wtr.close()

def deset(seq_list):
    set_list = []
    for member in seq_list:
        temp = member.replace("set([", '').replace("u'", '').replace("'", "").replace(']','').replace(")", "").strip()
        set_list.append(temp)
    return set_list

def Write_Output2(filename, sheetname, out_list, vmd, rmd):
    hit_list = []
    info_list = ['', '']
    for member in out_list:
        if member.find('|||') > -1:
            hit_list.append(member)
        else:
            info_list.append(member)
    hit_list.sort()
    wtr = mzReport.writer(filename, columns =['GeneName', 'Uniprot entry', 'Unique Peptides', 'Unique Peptide Sequences', 'Unique Peptide Sequences, Relative Mods'], sheet_name = sheetname)
    row = {}
    for entry in hit_list:
        temp = entry.split('|||')
        geneName = temp[0].strip()
        uniprotEntry = temp[1].strip()
        uniquePeptides = temp[3].strip()
        uniqueSeq = temp[2].replace("set([", '').replace("u'", '').replace("'", "").replace(']','').replace(")", "").strip()
        seqline = ''
        rseqline = ''
        seqs = uniqueSeq.split(",")
        for member in seqs:
            seq = member.strip()
            set_list = deset(vmd[seq])
            rset_list = deset(rmd[seq])
            seqline = seqline + seq + "(" + str(set_list) + "), "
            rseqline = rseqline + seq + "(" + str(rset_list) + "), "
        seqline = seqline[:-2]
        rseqline = rseqline[:-2]
        row["GeneName"]=geneName
        row["Uniprot entry"]=uniprotEntry
        row["Unique Peptides"]=uniquePeptides
        row['Unique Peptide Sequences']=seqline
        row['Unique Peptide Sequences, Relative Mods']=rseqline
        wtr.write(row)
    for line in info_list:
        row["GeneName"]=line
        row["Uniprot entry"]=''
        row["Unique Peptides"]=''
        row['Unique Peptide Sequences']=''
        row['Unique Peptide Sequences, Relative Mods']=''
        wtr.write(row)
    wtr.close()

def flag_xls(filename, flag="Stringent", phoscheck = False, peptide_stringency = 1, sheetname="Data"):
    rdr = mzReport.reader(filename, sheet_name = sheetname)
    wtr = mzReport.writer(filename, rdr.columns + ['Kinase?', 'Matches'], sheet_name = name)
    counter = 0
    for row in rdr:
        if counter % 50 == 0:
            print str(counter)
        counter += 1
        found = False
        kin_list = []
        acc = row["Accession Number"]
        peptide = row["Peptide Sequence"]
        if acc.find("rev_gi") == -1:
            for header, sequence in mzFunctions.parse_fasta("H:\\Desktop\\Kinobase_tag.fasta"):
                if sequence.find(peptide.strip()) > -1:
                    found = True
                    kin_list.append(header)
        row['Kinase?'] = found
        if not kin_list:
            kin_list = ['NA']
        row['Matches'] = str(kin_list)
        wtr.write(row)
    rdr.close()
    wtr.close()

def kinase_match(filename, flag="Stringent", phoscheck = False, peptide_stringency = 1, organism="human", sheetname="Data", modcheck=''):
    sequences = set()
    vmd = collections.defaultdict(set)
    rmd = collections.defaultdict(set)
    kinobase = mz_workbench.protein_core.retrieve_database(organism)
    rows, columns, data_list = get_sheet(filename, sheetname)
    headers = get_headers(data_list)

    for i in range(1, rows):
        varmod = str(data_list[i][headers["Variable Modifications"]])
        rmod = str(data_list[i][headers["Protein Relative Modifications"]])
        if not varmod:
            varmod = ''
            rmod = ''
        desc = str(data_list[i][headers["Protein Description"]])
        proceed = True
        if phoscheck:
            if varmod.find("Phospho") == -1:
                proceed = False
        if modcheck:
            if varmod.find(modcheck) == -1:
                proceed = False        
        if desc.find("Marto") > -1:
            proceed = False
        if proceed == True:
            sequences.add(data_list[i][headers["Peptide Sequence"]])
            vmd[data_list[i][headers["Peptide Sequence"]]].add(varmod)
            rmd[data_list[i][headers["Peptide Sequence"]]].add(rmod)
    #print sequences

    main_list = []

    unique = set()
    all = set()
    kin_dict_un = collections.defaultdict(set)
    kin_dict_all = collections.defaultdict(set)
    for peptide in sequences:
        #print peptide
        kin_list = []
        kin_dict = collections.defaultdict(set)
        for header, sequence in kinobase.iteritems():
            if sequence.find(peptide.strip()) > -1:
                kin_list.append(header)
                kin_dict[header].add(peptide)
                #print "match"
        if len(kin_list) == 1:
            unique.add(kin_list[0])
            #print kin_dict[kin_list[0]]
            #print kin_list[0]
            kin_dict_un[kin_list[0]].update(kin_dict[kin_list[0]]) #kinases for which unique peptide evidence exists
            all.add(kin_list[0])
            kin_dict_all[kin_list[0]].update(kin_dict[kin_list[0]]) 
        else:
            for kin in kin_list:
                all.add(kin)
                kin_dict_all[kin].update(kin_dict[kin])
        
    print "UN"
    print len(unique)
    #print unique

    print "ALL"
    print len(all)
    #print all
    
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
###-----------------------------------
    #filename = self.FindWindowByName("outputName").GetValue()
    st_pass = set()
    output_text=[]
    if flag == 'Stringent':
        output_text.append("Kinase Analysis Results")
        output_text.append("STRIGENT COUNTING (KINASES) SELECTED")
        if phoscheck:
            output_text.append("PHOSPHORYLATION REQUIRED")
        else:
            output_text.append("PHOSPHORYLATION -NOT- REQUIRED")
        if modcheck:
            output_text.append("MODCHECK REQUIRED: " + modcheck)
        else:
            output_text.append("ADDITIONAL MODCHECK -NOT- REQUIRED")        
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
                    output_text.append(add_mem + '|||' + member + "|||" + str(kin_dict_un[member]) + '|||' + str(len(kin_dict_un[member])))
                st_pass.add(add_mem)
        temp = ''
        for member in st_pass:
            temp += member + ', '
        output_text.append(temp[:-1])
        output_text.append(str(len(st_pass)))
        res_text += "Unique Meeting stringency: " + str(len(st_pass)) + " Un An: " + str(un_an)
        Write_Output2(filename, "Kinase Report-Stringent",output_text, vmd, rmd)
    else:
        output_text.append("Protein Manager Results")
        output_text.append("INCLUSIVE COUNTING (KINASES) SELECTED")
        if phoscheck:
            output_text.append("PHOSPHORYLATION REQUIRED")
        else:
            output_text.append("PHOSPHORYLATION -NOT- REQUIRED")
        if modcheck:
            output_text.append("MODCHECK REQUIRED: " + modcheck)
        else:
            output_text.append("ADDITIONAL MODCHECK -NOT- REQUIRED")
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
                    output_text.append(add_mem + '|||' + member + "|||" + str(kin_dict_all[member]) + '|||' + str(len(kin_dict_all[member])))
                if add_mem != None:
                    st_pass.add(add_mem)
        temp = ''
        for member in st_pass:
            temp += member + ', '
        output_text.append(temp[:-1])
        output_text.append(str(len(st_pass)))
        res_text += "Inclusive Meeting stringency: " + str(len(st_pass)) + " Un An: " + str(un_an)
        Write_Output2(filename, "Kinase Report-Inclusive",output_text, vmd, rmd)
if __name__ == "__main__":
    app = wx.PySimpleApp()

    dlg = wx.FileDialog(None, "Choose Multiplierz File:", defaultFile=os.getcwd(), pos = (2,2))
    if dlg.ShowModal() == wx.ID_OK:
        filename=dlg.GetPath()
        dir = dlg.GetDirectory()
        print filename
        print dir
    dlg.Destroy()

    kinase_match(filename, "Stringent", phoscheck = True, peptide_stringency = 1)
    kinase_match(filename, "Inclusive", phoscheck = True, peptide_stringency = 1)