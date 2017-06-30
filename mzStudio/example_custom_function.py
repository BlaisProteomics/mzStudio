

# Example function, removes low-intensity datapoints.
def processor_function(mz_int_points):
    output = []
    avgInt = sum(zip(*mz_int_points)[1]) / len(mz_int_points)
    for mz, intensity in mz_int_points:
        if intensity > avgInt:
            output.append((mz, intensity))
        
    return output