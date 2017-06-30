def floatrange(fromnum, tonum, step = 1):
    assert step
    assert step * (tonum - fromnum) >= 0 # To prevent infinite loops.
    
    i = fromnum
    while i < tonum:
        yield i
        i += step