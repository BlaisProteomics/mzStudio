# Copyright 2008 Dana-Farber Cancer Institute
# multiplierz is distributed under the terms of the GNU Lesser General Public License
#
# This file is part of multiplierz.
#
# multiplierz is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# multiplierz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with multiplierz.  If not, see <http://www.gnu.org/licenses/>.

from scipy import arange, array, mean, median, e, log, sqrt, pi
from scipy.optimize import leastsq
#import scipy.io.array_import

##pNames = {'Gaussian': (['Amp','x0','sigma','y0']),
##          'Extreme Value': (['Amp','x0','beta','y0']),
##          'Log Normal': (['Amp','x0','sigma','y0','mu'])
##    }

##pInitials = {'Gauss1': array([mean(y),median(x),0.3,0]),
##             'Gaussian': array([mean(y),median(x),0.3,0]),
##             'Extreme Value': array([mean(y),median(x),0.3,0]),
##             'Log Normal': array([mean(y),x[0],0.3,0,2])
##             }


def residuals(p, y, x, function):
    err = y - function(p, x)
    return err


def gauss(p, x):
    '''Takes a set of parameters and a numpy.ndarray of x values, and
    returns the y-coordinates of a gaussian at those values.
    '''

    a = p[0] # peak height
    b = p[1] # peak center
    c = p[2] # curve-width parameter

    f = a * e**(-1 * (x - b)**2 / (2 * (c**2)))

    return f


def evd(p, x):
    '''Computes a Gumbel distribution for the provided array of x values.
    '''

    a = p[0] # overall scaling factor
    b = p[1] # location parameter ('alpha')
    c = p[2] # scale parameter ('beta')
    d = p[3] # overall y-shift

    f = a * ((1 / c) * (e**((x - b) / c)) * (e**(-1 * (e**((x - b) / c))))) + d

    return f


def lognormal(p, x):
    '''Computes a log-normal distribution for the provided array of x values.
    '''

    a = p[0] # overall scaling factor--if a < 0, the result is an array of zeroes
    c = p[2] # standard deviation of log(x)
    if c <= 0.0:
        raise ValueError('p[2] (sigma) must be positive')

    s = p[4] # mean of log(x)

    # store some values
    csq2 = 2 * (c**2)
    c_sqrt2pi = c * sqrt(2*pi)

    f = scipy.zeros_like(x)
    if a <= 0.0:
        return f

    # the old version of this function ignored the x values and just used the length...?
    #x = arange(0,3,3.0/len(x))

    i = x > 0.0
    f[i] = a * ((e**(-1 * (((log(x[i]) - s)**2) / csq2))) / (x[i] * c_sqrt2pi))

    return f


def fit_data(data, parameters=None, function=gauss):
    """Fits a function to the data provided using least sqaures.

    function must take parameters and an x list, and return y list
    ex: 2.71828
    parameters = [1.5, 2.3]
    def my_function(parameters, x):
        a = parameters[0]
        b = parameters[1]
        returns f = a*x**2 + b
    get_fit(data, parameters, my_function)

    You can also use lambda functions
    Ex: lambda p, x: p[0]*2.7183**(-1*(x-p[1])**2/p[2]**2)

    """
    x = array([x1 for x1, y1 in data])
    y = array([y1 for x1, y1 in data])

    if not parameters:
        parameters = [mean(y), median(x), 0.3, 0]

    p0 = array(parameters)

    try:
        plsq = leastsq(residuals, p0, args=(y, x, function), maxfev=2000)
    except:
        pass

    final_p = plsq[0]

    f = function(final_p, x)

    #force 0
    f[f < 0.0] = 0.0

    R2 = coeff_det(y, f)

    return (f, final_p, R2)


def coeff_det(yExp, yTheo):
    '''Calculates the coefficient of determination given vectors of expected
    and theoretical y values. Both should be numpy arrays of the same length.

    R^2 = 1 - Sum(yExpi - yTheoi)^2 / Sum(yExpi - yExpAvg)^2
    '''

    yExpAvg = mean(yExp)

    sum1 = ((yExp - yTheo)**2).sum()
    sum2 = ((yExp - yExpAvg)**2).sum()

    R2 = 1 - (sum1 / sum2)

    return R2


def FWHM(p, xmin, xmax, function=gauss):
    '''Full width at half maximum. Given a range for x, calculates the function
    at 10000 points along the interval and returns the subset of x for which f(x)
    is close to half the maximum value. Rounds x to two decimal places.
    '''
    x = arange(xmin, xmax, float(xmax-xmin)/10000)

    f = function(p, x)
    halfHeight = (f.max() / 2.0)

    # where does this interval come from?
    interval = abs(f[int(float(len(x))/3)] - f[int(float(len(x))/3) + 1])

    halfX = x[abs(f - halfHeight) <= interval].round(2)

    return halfX
