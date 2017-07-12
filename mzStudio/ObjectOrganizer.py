
import wx


# Maintains a list of *types*, where only one
# instance of each type is going to be active at once.

class ObjectOrganizer(object):
    
    def __init__(self):
        self.ActiveObjects={}
    
    def addObject(self, obj):
        objType = type(obj)
        assert objType not in self.ActiveObjects
        self.ActiveObjects[objType] = obj
        
    def containsType(self, objtype):
        return objtype in self.ActiveObjects
        
    def getObjectOfType(self, objtype):
        return self.ActiveObjects[objtype]
    
    def removeObject(self, obj):
        del self.ActiveObjects[type(obj)]
    
    
        
        
        
        