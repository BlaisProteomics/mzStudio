
import time

def test1():
    a = [(400, 10000) for i in xrange(0, 21000)]
    
    print len(a)
    
    points = []
    
    t1 = time.time()
    
    for member in a:
        x1 = 5 + 5*((member[0]-100)/1000)
        y1 = 10 + 15 - 3 - (5-2)*(member[1]/20000)
        if 0:
            print "A"
        points.append((x1,y1))
        
    t2 = time.time()
    
    print t2-t1

def test2():
    
    a = [(400, 10000) for i in xrange(0, 21000)]
        
    print len(a)
    
    points = []
    
    t1 = time.time()
    
    for member in a:
        x1 = 2
        y1 = 2
        #if 0:
        #    print "A"
        points.append((x1,y1))
        
    t2 = time.time()
    
    print t2-t1

def test3():
    
    a = [(400, 10000) for i in xrange(0, 21000)]
        
    print len(a)
    
    points = set()
    
    t1 = time.time()
    
    for member in a:
        x1 = 2
        y1 = 2
        #if 0:
        #    print "A"
        points.add((x1, y1))
        
    t2 = time.time()
    
    print t2-t1    

test1()
test2()
test3()
