from subprocess import check_output

x = check_output([r"\\rc-data1.dfci.harvard.edu\blaise\ms_data_share\mzBrowserProject\mzBrowser\mzStudio\C#\ConsoleApp1.exe", "-p"])

#out = check_output([r"C:\Users\Scott\Desktop\ConsoleApp1.exe", "-p"])
print 'From Python'
import xml.etree.ElementTree as ET

root = ET.fromstring(x)

print root.attrib['name']
print
print root[4].attrib['objectID']
objectID = root[4].attrib['objectID']
print
print root.attrib['ID']
pageID = root.attrib['ID']

z = check_output([r"\\rc-data1.dfci.harvard.edu\blaise\ms_data_share\mzBrowserProject\mzBrowser\mzStudio\C#\ConsoleApp2.exe", pageID, objectID])
print 
print z
