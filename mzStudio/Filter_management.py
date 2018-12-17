__author__ = 'Scott Ficarro, William Max Alexander'
__version__ = '1.0'


#Filter management
import re

def Onms1(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def OnQuantivaQMS(filter_dict, id):
    #('.*?[+] ([pc]) [NE]SI sid=(\d+?.\d+?) Q([13])MS \[(\d+?.\d+?)-(\d+?.\d+?)\]')
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]='Q' + id.groups()[2] + 'MS'
    filter_dict["data"]= "+cent" if id.groups()[0]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[3]+'-'+id.groups()[4]+']'
    filter_dict['sid']=id.groups()[1]
    return filter_dict

def OnQuantivaMS2(filter_dict, id):
    #('.*?[+] ([pc]) [NE]SI sid=(\d+?.\d+?) (Full ms2)|(pr) (\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
    #           0                      1             2           3             4           5
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[2]
    filter_dict["data"]= "+cent" if id.groups()[0]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[4]+'-'+id.groups()[5]+']'
    filter_dict['sid']=id.groups()[1]
    filter_dict["precursor"]=id.groups()[3]
    filter_dict["reaction"]='CAD'
    filter_dict["energy"]=''    
    return filter_dict

def OnQuantivaSRM(filter_dict, id):
    #
    #           0                      1             2           3             4           5
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]='SRM'
    filter_dict["data"]= "+cent" if id.groups()[0]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[3]+'-'+id.groups()[6]+']'
    filter_dict['sid']=id.groups()[1]
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]='CAD'
    filter_dict["energy"]=''    
    return filter_dict

def Onlockms2(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[5]+'-'+id.groups()[6]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]=id.groups()[3]
    filter_dict["energy"]=id.groups()[4] + '% NCE'
    return filter_dict

def Onlockms1(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def Onsim_ms1(filter_dict, id):
    filter_dict["mode"]="sim (ms1)"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def Onpa(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[5]+'-'+id.groups()[6]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]=id.groups()[3]
    filter_dict["energy"]=id.groups()[4] + '% NCE'
    return filter_dict

def OnSRM(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[5]+'-'+id.groups()[8]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]=id.groups()[3]
    filter_dict["energy"]=id.groups()[4] + '% NCE'
    return filter_dict

def Ontarg(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[6]+'-'+id.groups()[7]+']'
    filter_dict["precursor"]=id.groups()[3]
    filter_dict["reaction"]=id.groups()[4]
    filter_dict["energy"]=id.groups()[5] + '% NCE'
    return filter_dict

def Onetd(filter_dict, id):
    #('.*?([FI]TMS) [+] ([cp]) NSI (t E )*d sa Full ms2 (\d+?.\d+?)@(hcd|cid|etd)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[6]+'-'+id.groups()[7]+']'
    filter_dict["precursor"]=id.groups()[3]
    filter_dict["reaction"]=id.groups()[4]
    filter_dict["energy"]=id.groups()[5] + '% NCE'
    return filter_dict
    
def Ontarg_ms3(filter_dict, id):
    #([FI]TMS) [+] ([cp]) [NE]SI Full ms3 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
    #0           1                      2           3         4              5        6          7             8           9
    filter_dict["mode"]="ms3"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[8]+'-'+id.groups()[9]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]=id.groups()[3]
    filter_dict["energy"]=id.groups()[4] + '% NCE'
    filter_dict["precursor ms3"]=id.groups()[5]
    filter_dict["reaction ms3"]=id.groups()[6]
    filter_dict["energy ms3"]=id.groups()[7] + '% NCE'
    return filter_dict

def Ondd_ms3(filter_dict, id):
    #([FI]TMS) [+] ([cp]) sps d [NE]SI Full ms3 (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) (\d+?.\d+?)@(hcd|cid)(\d+?.\d+?) \[(\d+?.\d+?)-(\d+?.\d+?)\]')
    #0           1                      2           3         4              5        6          7             8           9
    filter_dict["mode"]="ms3"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[8]+'-'+id.groups()[9]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]=id.groups()[3]
    filter_dict["energy"]=id.groups()[4] + '% NCE'
    filter_dict["precursor ms3"]=id.groups()[5]
    filter_dict["reaction ms3"]=id.groups()[6]
    filter_dict["energy ms3"]=id.groups()[7] + '% NCE'
    return filter_dict

def OnDms(filter_dict, id):
    ##(GC|TOF) MS \+ NSI Full ms(2?) \[(\d+)-(\d+)\]
    #'TOF MS + NSI Full ms 191.1781@00.00[58-3000]'
    #r'(GC|TOF) MS \+ NSI Full (ms[2]?) ((\d+.\d+)@\d+.\d+)?\[(\d+)-(\d+)\]'
    filter_dict['mode'] = id.groups()[1].upper()
    filter_dict['analyzer'] = id.groups()[0] # That's what that is, right?
    filter_dict['data'] = 'cent'
    filter_dict['mr'] = '[%s-%s]' % id.groups()[-2:]
    filter_dict["precursor"]= id.groups()[3]
    filter_dict["reaction"]='CAD'
    filter_dict["energy"]=''
    return filter_dict

def OnSRM(filter_dict, id):
    filt = id.groups()[0]
    words = filt.split()
    filter_dict['mode'] = words[0]
    filter_dict['analyzer'] = words[2]
    filter_dict['data'] = words[1]
    filter_dict['precursor'] = words[6]
    filter_dict['reaction'] = 'SRM'
    filter_dict['energy'] = words[3].replace('sid=', '')
    
    ranges = [x.strip('[], ').split('-') for x in words[7:]]
    filter_dict['mr'] = '[%s-%s]' % (ranges[0][0], ranges[-1][1])
    
    return filter_dict
    

#def OnTOFms2(filter_dict, id):
    #filter_dict['mode'] = 'ms2'
    #filter_dict['analyzer'] = 'TOF'
    #filter_dict['data'] = 'cent'
    #filter_dict['mr'] = '[%s-%s]' % id.groups()
    #return filter_dict


def Onprecursor(filter_dict, id):
    #self.precursor = re.compile('.*?(Precursor) [+] ([cp]) [NE]SI Full ms2 (\d+?.\d+?)@(\d+?.\d+?) \[(\d+?.*\d*?)-(\d+?.*\d*?)\]')
    #                                    0             1                        2            3             4              5
    filter_dict["mode"]="Precursor"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[4]+'-'+id.groups()[5]+']'
    filter_dict["precursor"]= id.groups()[2]
    filter_dict["reaction"]='CAD'
    filter_dict["energy"]=''    
    return filter_dict    

def Onqms1(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def Onqms2(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[-2]+'-'+id.groups()[-1]+']'
    
    
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]='NA'
    filter_dict["energy"]='NA'    
    
    return filter_dict    

def Onpi(filter_dict, id):
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    
    
    filter_dict["precursor"]='NA'
    filter_dict["reaction"]='CID'
    filter_dict["energy"]='NA'    
    
    return filter_dict

def Onerms(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def Onq3ms(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def Onems(filter_dict, id):
    filter_dict["mode"]="ms1"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    return filter_dict

def onmrmms(filter_dict, id):
    filter_dict["mode"]="mrm"
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    #filter_dict["mr"]='[' + id.groups()[2]+'-'+id.groups()[3]+']'
    #filter_dict["precursor"]='MRM'
    filter_dict["reaction"]='CAD'
    return filter_dict
    #raise NotImplementedError

def Onmgf(filter_dict, id):
    #MGF ms2 542.4232 [100:2000]
    filter_dict['mode']='ms2'
    filter_dict['analyzer']=''
    filter_dict['data']='mgf'
    filter_dict["mr"]='[' + id.groups()[1]+'-'+id.groups()[2]+']'
    filter_dict["precursor"]=id.groups()[0]
    filter_dict["reaction"]="MS2"
    if id.groups()[4]:
        filter_dict["reaction"]=id.groups()[4]
    filter_dict["energy"]=''   
    filter_dict['file scan'] = id.groups()[3]
    return filter_dict
    

def Ontofms2(filter_dict, id):
    #TOF MS p NSI Full ms2 540.032306122@0[100-1400][1375:4]
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[4]+'-'+id.groups()[5]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]="TOF MS2"
    filter_dict["energy"]='Rolling CE'
    return filter_dict

def Onepi(filter_dict, id):
    #EPI p NSI Full ms2 540.032306122@0[100-1400][1375:4]
    filter_dict["mode"]="ms2"
    filter_dict["analyzer"]=id.groups()[0]
    filter_dict["data"]= "+cent" if id.groups()[1]== "c" else "+prof"
    filter_dict["mr"]='[' + id.groups()[4]+'-'+id.groups()[5]+']'
    filter_dict["precursor"]=id.groups()[2]
    filter_dict["reaction"]="CAD"
    filter_dict["energy"]='Rolling CE'
    return filter_dict