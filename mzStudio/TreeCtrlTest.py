
import cPickle

def scan_for_folders(member, folder_names):
    if member['data']['type']=='container':
        folder_names.append(member['label']) 
    if 'children' in member.keys():
        if member['children']:
            for child in member['children']:
                scan_for_folders(child, folder_names)

def test():
    pickle_file = open(r'D:\SBF\mzStudio\SpecBaseTest1.sbr', "r")
    data = cPickle.load(pickle_file)
    pickle_file.close()    
    print data
    
    folder_names = []
    
    for member in data:
        scan_for_folders(member, folder_names)
    
    print folder_names
    
test()