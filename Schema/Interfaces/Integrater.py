#!/usr/bin/env python
# Integrater.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the terms and conditions of the
#   CCP4 Program Suite Licence Agreement as a CCP4 Library.
#   A copy of the CCP4 licence can be obtained by writing to the
#   CCP4 Secretary, Daresbury Laboratory, Warrington WA4 4AD, UK.
# 
# An interface for programs which do integration - this will handle
# all of the input and output, delegating the actual processing to an
# implementation of this interfacing.
# 
# The following are considered critical:
# 
# Input:
# An implementation of the indexer class.
# 
# Output:
# [processed reflections?]
#
# This is a complex problem to solve...
# 
# Assumptions & Assertions:
# 
# (1) Integration includes any cell and orientation refinement.
# (2) If there is no indexer implementation provided as input,
#     it's ok to go make one, or raise an exception (maybe.)
# 
# This means...
# 
# (1) That this needs to have the posibility of specifying images for
#     use in both cell refinement (as a list of wedges, similar to 
#     the indexer interface) and as a SINGLE WEDGE for use in integration.
# (2) This may default to a local implementation using the same program,
#     e.g. XDS or Mosflm - will not necessarily select the best one.
#     This is left to the implementation to sort out.
#
# Useful standard options:
# 
# Resolution limits (low, high)
# ?Gain? - can this be determined automatically
# ?Areas to exclude? - this may be a local problem e.g. for mosflm just exclude
#                      appropriate areas by detector class
#
# Error Conditions:
# 
# FIXED 25/AUG/06 need a way to get the output reflection file from this
#                 interface, so that it can be passed in to a scaler
#                 implementation for ... scaling.
# 
# FIXED 05/SEP/06 also need to make this more like the indexer interface,
#                 providing access to everything only through getters and
#                 setters - no action methods. the tracking & calculations
#                 must be performed explicitly... FIXED - access through
#                 integrate_get_reflections, though tracking is not yet
#                 implemented FIXED - it is now..
# 
# FIXED 06/SEP/06 need to replace integrate_set with set_integrater as per
#                 the indexer interface, likewise getters. Done.
# 
# FIXED 08/SEP/06 need to record the number of batches in each run, so that
#                 rebatch may be used to reassign batch numbers in multi-
#                 sweep scaling.
# 
#                 Also - need to be able to assign the range of images
#                 to integrate, in particular single images if I intend to
#                 bolt this into DNA. Also for people who record three
#                 wavelengths with the same image prefix, for instance.
#                 Done done done....
#
# FIXED 27/SEP/06 need to be able to pass integration parameters, e.g. GAIN,
#                 from one instance of Integrater to another - e.g. via some
#                 kind of export parameters/import parameters framework.
#                 Note well that this will be complicated by the need to
#                 make sure that those parameters are relevent.
# 
#                 This is complicated - I need to figure out how to get the 
#                 exported parameters to all of the other integrater instances
#                 which will make life rather complicated. Aha - need to key it
#                 in some global dictionary someplace by the current crystal
#                 identity, and switch it off if this is not available.
# 
# FIXME 20/OCT/06 need to be able to rerun integration as much as we like
#                 until everyone is happy with the results (e.g. a good
#                 resolution limit, sensible GAIN, etc. has been set.)
#                 This will mean that the cell refinement implementation
#                 for some programs may need to be separated off, so perhaps
#                 there should be a prepare_to_integrate method, which needs
#                 to be run once, followed by a "proper" integrate method,
#                 which will be run repeatedly...
#
#                 Implement this change - call prepare_to_integrate followed
#                 by integrate...

import os
import sys
import exceptions

if not os.environ.has_key('DPA_ROOT'):
    raise RuntimeError, 'DPA_ROOT not defined'

if not os.environ['DPA_ROOT'] in sys.path:
    sys.path.append(os.path.join(os.environ['DPA_ROOT']))

from lib.Guff import inherits_from
from Handlers.Streams import Chatter
from Handlers.Exception import DPAException

# image header reading functionality
from Wrappers.XIA.Printheader import Printheader

class Integrater:
    '''An interface to present integration functionality in a similar
    way to the indexer interface.'''

    def __init__(self):

        # a pointer to an implementation of the indexer class from which
        # to get orientation (maybe) and unit cell, lattice (definately)
        self._intgr_indexer = None

        # optional parameters
        self._intgr_reso_high = 0.0
        self._intgr_reso_low = 0.0

        # required parameters 
        self._intgr_wedge = None

        # implementation dependent parameters - these should be keyed by
        # say 'mosflm':{'yscale':0.9999} etc.
        self._intgr_program_parameters = { }

        # the same, but for export to other instances of this interface
        self._intgr_export_program_parameters = { }

        # batches to integrate, batches which were integrated - this is
        # to allow programs like rebatch to work c/f self._intgr_wedge
        # note well that this may have to be implemented via mtzdump?
        # or just record the images which were integrated...
        self._intgr_batches_out = [0, 0]

        self._intgr_done = False
        self._intgr_prepare_done = False
        self._intgr_hklout = None

        # a place to store the project, crystal, wavelength, sweep information
        # to interface with the scaling...
        self._intgr_pname = None
        self._intgr_xname = None
        self._intgr_dname = None
        self._intgr_epoch = 0
        
        return

    def set_integrater_project_information(self,
                                           project_name,
                                           crystal_name,
                                           dataset_name):
        '''Set the metadata information, to allow passing on of information
        both into the reflection files (if possible) or to the scaling stages
        for dataset administration.'''

        # for mosflm, pname & dname can be used as part of the harvesting
        # interface, and should therefore end up in the mtz file?
        # add this as harvest pname [pname] dname [dname] and three separate
        # keywords...
        
        self._intgr_pname = project_name
        self._intgr_xname = crystal_name
        self._intgr_dname = dataset_name
        
        return

    def get_integrater_project_information(self):
        return self._intgr_pname, self._intgr_xname, self._intgr_dname

    def get_integrater_epoch(self):
        return self._intgr_epoch

    def set_integrater_epoch(self, epoch):
        self._intgr_epoch = epoch
        return

    def set_integrater_wedge(self, start, end):
        '''Set the wedge of images to process.'''
        
        self._intgr_wedge = (start, end)

        # FIXME update the epoch of the start of data collection
        # in here...
        # this will involve - get full file name from start, get header
        # from full file name, parse & pull out start date. this may be
        # NULL, in which case too bad!

        first_image_in_wedge = self.get_image_name(start)
        ph = Printheader()
        ph.set_image(first_image_in_wedge)
        header = ph.readheader()

        # only update the epoch if we (1) have a new value
        # and (2) do not have a user supplied value...
        if header['epoch'] > 0 and self._intgr_epoch == 0:
            self._intgr_epoch = int(header['epoch'])

        Chatter.write('Sweep epoch: %d' % self._intgr_epoch)
        
        self._intgr_done = False
        
        return

    def set_integrater_resolution(self, dmin, dmax):
        '''Set both resolution limits.'''

        self._intgr_reso_high = min(dmin, dmax)
        self._intgr_reso_low = max(dmin, dmax)
        self._intgr_done = False

        return

    def set_integrater_high_resolution(self, dmin):
        '''Set high resolution limit.'''

        self._intgr_reso_high = dmin

        # Chatter.write('Setting high resolution limit')
        
        self._intgr_done = False
        return

    def set_integrater_parameter(self, program, parameter, value):
        '''Set an arbitrary parameter for the program specified to
        use in integration, e.g. the YSCALE or GAIN values in Mosflm.'''

        if not self._intgr_program_parameters.has_key(program):
            self._intgr_program_parameters[program] = { }

        self._intgr_program_parameters[program][parameter] = value
        return

    def get_integrater_parameter(self, program, parameter):
        '''Get a parameter value.'''

        try:
            return self._intgr_program_parameters[program][parameter]
        except:
            return None
        
    def get_integrater_parameters(self, program):
        '''Get all parameters and values.'''

        try:
            return self._intgr_program_parameters[program]
        except:
            return { }

    def set_integrater_parameters(self, parameters):
        '''Set all parameters and values.'''

        self._intgr_program_parameters = parameters

        # Chatter.write('Setting integration parameters: %s' % str(parameters))
        
        self._intgr_done = False

        return

    def set_integrater_export_parameter(self, program, parameter, value):
        '''Set an arbitrary parameter for the program specified to
        use in integration, e.g. the YSCALE or GAIN values in Mosflm.'''

        if not self._intgr_export_program_parameters.has_key(program):
            self._intgr_export_program_parameters[program] = { }

        self._intgr_export_program_parameters[program][parameter] = value
        return

    def get_integrater_export_parameter(self, program, parameter):
        '''Get a parameter value.'''

        try:
            return self._intgr_export_program_parameters[program][parameter]
        except:
            return None
        
    def get_integrater_export_parameters(self):
        '''Get all parameters and values.'''

        try:
            return self._intgr_export_program_parameters
        except:
            return { }

    def set_integrater_indexer(self, indexer):
        '''Set the indexer implementation to use for this integration.'''

        # check that this indexer implements the Indexer interface
        if not inherits_from(indexer.__class__, 'Indexer'):
            raise RuntimeError, 'input %s is not an Indexer implementation' % \
                  indexer.__name__

        self._intgr_indexer = indexer

        # Chatter.write('Resetting integration flags')
        self._intgr_done = False
        self._intgr_prepare_done = False
        return

    def integrate(self):
        '''Actually perform integration until we think we are done...'''

        # FIXME 20/OCT/06 need to be sure that this will work correctly...
        # FIXME could the repeated integration needed in Mosflm be entirely
        # handled from here??? Apparently yes!

        while not self._intgr_prepare_done:
            Chatter.write('Preparing to do some integration...')
            self._intgr_prepare_done = True

            # if this raises an exception, then perhaps the autoindexing
            # solution has too high symmetry. if this the case, then
            # perform a self._intgr_indexer.eliminate() - this should
            # reset the indexing system

            try:
                self._integrate_prepare()
            except DPAException, e:
                # fixme I should trap the correct exception here
                Chatter.write('Uh oh! %s' % str(e))
                self._intgr_indexer.eliminate()
                self._intgr_prepare_done = False                

        while not self._intgr_done:
            Chatter.write('Doing some integration...')
            
            # assert that it is indeed done
            self._intgr_done = True
            
            # but it may not be - if the integrate itself decides something
            # needs redoing
            self._intgr_hklout = self._integrate()

        # ok, we are indeed "done"...
        
        return self._intgr_hklout

    def get_integrater_indexer(self):
        return self._intgr_indexer

    def get_integrater_reflections(self):
        # in here check if integration has already been performed, if
        # it has and everything is happy, just return the reflections,
        # else repeat the calculations.

        if not self._intgr_done:
            self.integrate()
        return self._intgr_hklout
            
    def get_integrater_batches(self):
        if not self._intgr_done:
            self.integrate()
        return self._intgr_batches_out
