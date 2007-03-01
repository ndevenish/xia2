#!/usr/bin/env python
# NullScalerImplementation.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 30/OCT/06
#
# An empty scaler - this presents the Scaler interface but does 
# nothing, making it ideal for when you have the reduced data already -
# this will simply return that reduced data...
#
# FIXME 04/DEC/06 this will need to be able to transmogrify data from one
#                 format to another (e.g. to scalepack from mtz, for instance)
#                 and also be able to get reflection file information from
#                 "trusted" formats (that is, from mtz format - cell, symmetry
#                 information will not be trusted in scalepack files.)

import os
import sys

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])

from Wrappers.CCP4.Mtzdump import Mtzdump
from Schema.Interfaces.Scaler import Scaler

# file conversion (and merging) jiffies

from Modules.Scalepack2Mtz import Scalepack2Mtz
from Modules.Mtz2Scalepack import Mtz2Scalepack

class NullScalerImplementation(Scaler):
    '''A null scaler implementation which looks like a real scaler
    but actually does nothing but wrap a couple of reflection files.
    This will also transmogrify reflection files if appropriate.'''

    def __init__(self):
        '''Set myself up - making room for reflection file handles if
        appropriate. Note that this should also have room to hold the
        correct spacegroup (or a list of likely candidates) and also
        the unit cell parameters. Setters will be needed for this,
        so that that information may come from some modification of
        a .xinfo file.'''

        Scaler.__init__(self)

        # the following need to be configured:
        # self._scalr_scaled_reflection_files - dictionary containing file
        #                                       links - this will want to
        #                                       have a structure like:
        #
        # ['sca'][WAVELENGTH] = filename - for merged scalepack
        # ['sca_unmerged'][WAVELENGTH] = filename - for unmerged
        # ['mtz_merged_free'] = filename - merged cadded + free mtz
        #
        # so these are the only formats which there is any value in
        # transforming to/from.
        # 
        # self._scalr_statistics - dictionary containing statistics from
        #                          scaling
        # self._scalr_cell - canonical unit cell from data reduction
        # self._scalr_likely_spacegroups - a list of likely spacegroups
        # self._scalr_highest_resolution - a float of the highest resolution
        #                                  achieved from this crystal
        # 
        # The following tokens will be defined (optionally) for the
        # whole resolution range of the data set in the .xinfo file
        # for this stage:
        # 
        # BEGIN WAVELENGTH_STATISTICS
        # ANOMALOUS_COMPLETENESS
        # ANOMALOUS_MULTIPLICITY
        # COMPLETENESS
        # MULTIPLICITY
        # HIGH_RESOLUTION_LIMIT
        # LOW_RESOLUTION_LIMIT
        # I_SIGMA
        # R_MERGE
        # N_REF
        # N_REF_UNIQUE
        # END WAVELENGTH_STATISTICS
        #
        # These need to be mapped to the following dictionary entries
        # (which should be defined in the Scaler interface...):
        #
        # 'High resolution limit'
        # 'Low resolution limit'
        # 'Completeness'
        # 'Multiplicity'
        # 'I/sigma'
        # 'Rmerge'
        # 'Anomalous completeness'
        # 'Anomalous multiplicity'
        # 'Total observations'
        # 'Total unique'
        #
        # There are other tokens defined but they are not very interesting
        # at the moment...

        return

    def add_scaled_reflection_file(self, type, wavelength = None, filename):
        '''Add a reflection file keyed by type and optionally wavelength
        (for e.g. scalepack files).'''

        if not wavelength:
            self._scalr_scaled_reflection_files[type] = filename
        else:
            self._scalr_scaled_reflection_files[type][wavelength] = filename

        return

    def set_scaler_statistics(self, statistics_dictionary):
        '''Set the scaling statistics for later return.'''

        # transform from .xinfo format to scaler dictionary

        xinfo_to_internal = {
            'I_SIGMA':'I/Sigma',
            'R_MERGE':'Rmerge',
            'N_REF':'Total observations',
            'N_REF_UNIQUE':'Total unique'
            }

        # store statistics
        
        self._scalr_statistics = { }

        for token in statistics_dictionary.keys():
            if token in xinfo_to_internal.keys:
                self._scalr_statistics[xinfo_to_internal[
                    token]] = statistics_dictionary[token]
            else:
                self._scalr_statistics[token.replace(' ', '_').upper(
                    )] = statistics_dictionary[token]

        return
            

