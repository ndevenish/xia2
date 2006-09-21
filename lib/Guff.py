#!/usr/bin/env python
# Guff.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the terms and conditions of the
#   CCP4 Program Suite Licence Agreement as a CCP4 Library.
#   A copy of the CCP4 licence can be obtained by writing to the
#   CCP4 Secretary, Daresbury Laboratory, Warrington WA4 4AD, UK.
#
# 21/SEP/06
# 
# Python routines which don't really belong anywhere else.
# 

def inherits_from(this_class,
                  base_class_name):
    '''Return True if base_class_name contributes to the this_class class.'''

    if this_class.__bases__:
        for b in this_class.__bases__:
            if inherits_from(b, base_class_name):
                return True

    if this_class.__name__ == base_class_name:
        return True

    return False

def is_mtz_file(filename):
    '''Check if a file is MTZ format - at least according to the
    magic number.'''

    magic = open(filename, 'r').read(4)

    if magic == 'MTZ ':
        return True

    return False

def nifty_power_of_ten(num):
    '''Return 10^n: 10^n > num; 10^(n-1) <= num.'''

    result = 10

    while result <= num:
        result *= 10

    return result
    
if __name__ == '__main__':
    # run a test

    class A:
        pass

    class B(A):
        pass

    class C:
        pass

    if inherits_from(B, 'A'):
        print 'ok'
    else:
        print 'failed'

    if not inherits_from(C, 'A'):
        print 'ok'
    else:
        print 'failed'
