#!/usr/bin/env python
# CommandLine.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 12th June 2006
# 
# A handler for all of the information which may be passed in on the command
# line. This singleton object should be able to handle the input, structure
# it and make it available in a useful fashion.
# 
# This is a hook into a global data repository.
# 
# Modification log:
# 
# 21/JUN/06 - Added in parsing of image (passed in on -image token, or
#             last token) to template & directory to work with. Note 
#             well - I need to think more carefully about this in the
#             future, though this solution may scale...
# 
# 16/AUG/06 - FIXED - need to be able to handle a resolution limit in here 
#             as well as any other information our user may wish to pass
#             in on the comand line, for example a lattice or a spacegroup.
#             See 04/SEP/06 below.
# 
# 23/AUG/06 - FIXED - need to add handling of the lattice input in particular,
#             since this is directly supported by Mosflm.py...
#
# 04/SEP/06 - FIXED - need to be able to pass in a resolution limit to
#             work to, for development purposes (this should become
#             automatic in the future.)
#
# 07/FEB/07 - FIXED need flags to control "experimental" functionality
#             e.g. the phasing pipeline - for instance this could
#             be -phase to perform phasing on the scaled data.
# 
#             At the moment the amount of feedback between the phasing
#             and the rest of the data reduction is non existent.
# 
# 15/MAY/07 - FIXED need to add flag -ehtpx_xml_out which will enable 
#             writing of e-HTPX xml for the data reduction portal. This
#             should be provided the path on which to write the file.

import sys
import os
import exceptions
import copy
import traceback

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'
if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.path.join(os.environ['XIA2_ROOT']))

from Schema.Object import Object
from Experts.FindImages import image2template_directory
from Schema.XProject import XProject
from Handlers.Flags import Flags
from Handlers.Streams import Chatter, Debug
from Handlers.PipelineSelection import add_preference

class _CommandLine(Object):
    '''A class to represent the command line input.'''

    def __init__(self):
        '''Initialise all of the information from the command line.'''

        Object.__init__(self)

        self._argv = []

        return

    def print_command_line(self):
        cl = '%s' % self._argv[0]
        for arg in self._argv[1:]:
            cl += ' %s' % arg
        Chatter.write('Command line: %s' % cl)
        return

    def setup(self):
        '''Set everything up...'''

        # things which are single token flags...

        self._argv = copy.deepcopy(sys.argv)

        self._read_debug()
        self._read_trust_timestamps()
        self._read_batch_scale()
        self._read_old_mosflm()
        self._read_small_molecule()
        self._read_quick()
        self._read_smart_scaling()
        self._read_chef()
        self._read_reversephi()
        self._read_no_lattice_test()
        self._read_fiddle_sd()
        self._read_no_relax()
        self._read_norefine()
        self._read_noremove()        
        self._read_2d()
        self._read_3d()
        self._read_3dii()
        self._read_migrate_data()
        self._read_zero_dose()
        self._read_no_correct()
        self._read_free_fraction()
        self._read_free_total()

        # flags relating to unfixed bugs...
        self._read_fixed_628()

        try:
            self._read_beam()
        except:
            raise RuntimeError, self._help_beam()

        try:
            self._read_cell()
        except:
            raise RuntimeError, self._help_cell()

        try:
            self._read_first_last()
        except:
            raise RuntimeError, self._help_first_last()

        try:
            self._read_image()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_image(), str(e))

        try:
            self._read_project_name()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_project_name(), str(e))

        try:
            self._read_atom_name()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_atom_name(), str(e))

        try:
            self._read_crystal_name()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_crystal_name(), str(e))
        
        # FIXME why is this commented out??! - uncomment this though may
        # want to explain exactly what is wrong...

        try:
            self._read_xinfo()
        except exceptions.Exception, e:
            traceback.print_exc(file = open('xia2-xinfo.error', 'w'))
            raise RuntimeError, '%s (%s)' % \
                  (self._help_xinfo(), str(e))

        try:
            self._read_ehtpx_xml_out()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_ehtpx_xml_out(), str(e))

        try:
            self._read_parallel()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_parallel(), str(e))

        try:
            self._read_spacegroup()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_spacegroup(), str(e))

        try:
            self._read_resolution()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_resolution(), str(e))

        try:
            self._read_z_min()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_z_min(), str(e))

        try:
            self._read_freer_file()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_freer_file(), str(e))

        try:
            self._read_reference_reflection_file()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_reference_reflection_file(), str(e))

        try:
            self._read_rejection_threshold()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_rejection_threshold(), str(e))

        try:
            self._read_i_over_sigma_limit()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_i_over_sigma_limit(), str(e))

        try:
            self._read_cellref_mode()
        except exceptions.Exception, e:
            raise RuntimeError, '%s (%s)' % \
                  (self._help_cellref_mode(), str(e))

        # FIXME add some consistency checks in here e.g. that there are
        # images assigned, there is a lattice assigned if cell constants
        # are given and so on

        return

    # command line parsers, getters and help functions.

    def _read_beam(self):
        '''Read the beam centre from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-beam')
        except ValueError, e:
            # the token is not on the command line
            self.write('No beam passed in on the command line')
            self._beam = (0.0, 0.0)
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        try:
            beam = sys.argv[index + 1].split(',')
        except IndexError, e:
            raise RuntimeError, '-beam correct use "-beam x,y"'

        if len(beam) != 2:
            raise RuntimeError, '-beam correct use "-beam x,y"'

        self.write('Beam passed on the command line: %7.2f %7.2f' % \
                   (float(beam[0]), float(beam[1])))

        self._beam = (float(beam[0]), float(beam[1]))

        Debug.write('Beam read from command line as %f %f' % \
                    self._beam)

        return

    def _help_beam(self):
        '''Return a help string for the read beam method.'''
        return '-beam x,y'

    def get_beam(self):
        return self._beam

    def _read_first_last(self):
        '''Read first, last images from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-first_last')
        except ValueError, e:
            self.write('No first_last passed in on command line')
            self._first_last = (-1, -1)
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        try:
            first, last = tuple(map(int, sys.argv[index + 1].split(',')))
        except IndexError, e:
            raise RuntimeError, '-first_last first,last'

        self._first_last = first, last

        self.write('first_last passed in on command line as %d, %d' % \
                   self._first_last)

        Debug.write('First & last image: %d %d' % self._first_last)

        return

    def _help_first_last(self):
        return '-first_last first,last'

    def get_first_last(self):
        return self._first_last

    def _help_image(self):
        '''Return a string for explaining the -image method.'''
        return '-image /path/to/an/image_001.img'

    def _read_image(self):
        '''Read image information from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-image')
        except ValueError, e:
            # the token is not on the command line
            self._default_template = None
            self._default_directory = None
            self._default_image = None
            self.write('No image passed in on the command line')
            return

        image = sys.argv[index + 1]

        # check if there is a space in the image name - this happens and it
        # looks like the python input parser will split it even if the
        # space is escaped or it is quoted

        if image[-1] == '\\':
            try:
                image = '%s %s' % (sys.argv[index + 1][:-1],
                                   sys.argv[index + 2])
            except:
                raise RuntimeError, 'image name ends in \\'

        template, directory = image2template_directory(image)
        self._default_template = template
        self._default_directory = directory
        self._default_image = image

        Debug.write('Interpreted from image %s:' % image)
        Debug.write('Template %s' % template)
        Debug.write('Directory %s' % directory)
        
        return

    def _read_atom_name(self):
        try:
            index = sys.argv.index('-atom')

        except ValueError, e:
            self._default_atom_name = None
            return

        self._default_atom_name = sys.argv[index + 1]

        Debug.write('Heavy atom: %s' % \
                    self._default_atom_name)
        
        return

    def _help_atom_name(self):
        return '-atom se'

    def get_atom_name(self):
        return self._default_atom_name

    def _read_project_name(self):
        try:
            index = sys.argv.index('-project')

        except ValueError, e:
            self._default_project_name = None
            return

        self._default_project_name = sys.argv[index + 1]

        Debug.write('Project: %s' % self._default_project_name)
        
        return

    def _help_project_name(self):
        return '-project foo'

    def get_project_name(self):
        return self._default_project_name

    def _read_crystal_name(self):
        try:
            index = sys.argv.index('-crystal')

        except ValueError, e:
            self._default_crystal_name = None
            return

        self._default_crystal_name = sys.argv[index + 1]
        Debug.write('Crystal: %s' % self._default_crystal_name)
        
        return

    def _help_crystal_name(self):
        return '-crystal foo'

    def get_crystal_name(self):
        return self._default_crystal_name

    def _read_xinfo(self):
        try:
            index = sys.argv.index('-xinfo')
        except ValueError, e:
            self.write('No .xinfo passed in on command line')
            self._xinfo = None
            return

        if index < 0:
            raise RuntimeError, 'negative index (no xinfo file name given)'

        self._xinfo = XProject(sys.argv[index + 1])

        Debug.write(60 * '-')
        Debug.write('XINFO file: %s' % sys.argv[index + 1])
        for record in open(sys.argv[index + 1], 'r').readlines():
            # don't want \n on the end...
            Debug.write(record[:-1])
        Debug.write(60 * '-')

        return

    def _help_xinfo(self):
        return '-xinfo example.xinfo'

    def set_xinfo(self, xinfo):
        self._xinfo = XProject(xinfo)

    def get_xinfo(self):
        '''Return the XProject.'''
        return self._xinfo

    def _read_parallel(self):
        try:
            index = sys.argv.index('-parallel')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_parallel(int(sys.argv[index + 1]))
        Debug.write('Parallel set to %d' % Flags.get_parallel())
            
        return

    def _help_parallel(self):
        return '-parallel N'

    def _read_spacegroup(self):
        try:
            index = sys.argv.index('-spacegroup')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_spacegroup(sys.argv[index + 1])
        Debug.write('Spacegroup set to %s' % sys.argv[index + 1])
            
        return

    def _help_spacegroup(self):
        return '-spacegroup P43212'

    def _read_resolution(self):
        try:
            index = sys.argv.index('-resolution')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        resolution = sys.argv[index + 1]
        if ',' in resolution:
            a, b = map(float, resolution.split(','))
            dmin = min(a, b)
            dmax = max(a, b)
        else:
            dmin = float(resolution)
            dmax = None

        Flags.set_resolution_high(dmin)
        Flags.set_resolution_low(dmax)

        if dmax:
            Debug.write('Resolution set to %.3f %.3f' % (dmin, dmax))
        else:
            Debug.write('Resolution set to %.3f' % dmin)
            
        return

    def _help_resolution(self):
        return '-resolution high[,low]'

    def _read_z_min(self):
        try:
            index = sys.argv.index('-z_min')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_z_min(float(sys.argv[index + 1]))
        Debug.write('Z min set to %f' % Flags.get_z_min())
            
        return

    def _help_z_min(self):
        return '-z_min N'

    def _read_freer_file(self):
        try:
            index = sys.argv.index('-freer_file')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_freer_file(sys.argv[index + 1])
        Debug.write('FreeR_flag column taken from %s' %
                    Flags.get_freer_file())

        # this should also be used as an indexing reference to make
        # sense...

        Flags.set_reference_reflection_file(sys.argv[index + 1])
        Debug.write('Reference reflection file: %s' %
                    Flags.get_reference_reflection_file())

        # and also the spacegroup copied out?! ok - this is done
        # "by magic" in the scaler.
            
        return

    def _help_freer_file(self):
        return '-freer_file my_freer_file.mtz'

    def _read_reference_reflection_file(self):
        try:
            index = sys.argv.index('-reference_reflection_file')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_reference_reflection_file(sys.argv[index + 1])
        Debug.write('Reference reflection file: %s' %
                    Flags.get_reference_reflection_file())
            
        return

    def _help_reference_reflection_file(self):
        return '-reference_reflection_file my_reference_reflection_file.mtz'

    def _read_rejection_threshold(self):
        try:
            index = sys.argv.index('-rejection_threshold')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_rejection_threshold(float(sys.argv[index + 1]))
        Debug.write('Rejection threshold set to %f' % \
                    Flags.get_rejection_threshold())
            
        return

    def _help_rejection_threshold(self):
        return '-rejection_threshold N'

    def _read_i_over_sigma_limit(self):
        try:
            index = sys.argv.index('-i_over_sigma_limit')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_i_over_sigma_limit(float(sys.argv[index + 1]))
        Debug.write('I/sigma limit set to %f' % \
                    Flags.get_i_over_sigma_limit())
            
        return

    def _help_i_over_sigma_limit(self):
        return '-i_over_sigma_limit N'

    def _read_ehtpx_xml_out(self):
        try:
            index = sys.argv.index('-ehtpx_xml_out')
        except ValueError, e:
            self._ehtpx_xml_out = None
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        self._ehtpx_xml_out = sys.argv[index + 1]
        Debug.write('e-HTPX XML output set to %s' % sys.argv[index + 1])
            
        return

    def _help_ehtpx_xml_out(self):
        return '-ehtpx_xml_out project.xml'

    def get_ehtpx_xml_out(self):
        '''Return the ehtpx xml out file.'''
        return self._ehtpx_xml_out
    
    def get_template(self):
        return self._default_template

    def get_directory(self):
        return self._default_directory

    def get_image(self):
        return self._default_image

    def _read_trust_timestamps(self):

        if '-trust_timestamps' in sys.argv:
            Flags.set_trust_timestamps(True)
            Debug.write('Trust timestamps on')
        return

    def _read_batch_scale(self):

        if '-batch_scale' in sys.argv:
            Flags.set_batch_scale(True)
            Debug.write('Batch scaling mode on')
        return

    def _read_old_mosflm(self):

        if '-old_mosflm' in sys.argv:
            Flags.set_old_mosflm(True)
            Debug.write('Old Mosflm selected')
        return

    def _read_small_molecule(self):

        if '-small_molecule' in sys.argv:
            Flags.set_small_molecule(True)
            Debug.write('Small molecule selected')
        return

    def _read_cellref_mode(self):
        try:
            index = sys.argv.index('-cellref_mode')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_cellref_mode(sys.argv[index + 1])
        Debug.write('Cell refinement mode (2D) set to %s' % \
                    Flags.get_cellref_mode())

        return

    def _help_cellref_mode(self):
        return '-cellref_mode (default|parallel|orthogonal|both)'

    def _read_quick(self):

        if '-quick' in sys.argv:
            Flags.set_quick(True)
            Debug.write('Quick mode selected')
        return

    def _read_smart_scaling(self):

        if '-smart_scaling' in sys.argv:
            Flags.set_smart_scaling(True)
            Debug.write('Smart scaling mode selected')
        return

    def _read_chef(self):

        if '-chef' in sys.argv:
            Flags.set_chef(True)
            Debug.write('Chef mode selected')
        return

    def _read_reversephi(self):

        if '-reversephi' in sys.argv:
            Flags.set_reversephi(True)
            Debug.write('Reversephi mode selected')
        return

    def _read_no_lattice_test(self):

        if '-no_lattice_test' in sys.argv:
            Flags.set_no_lattice_test(True)
            Debug.write('No lattice test mode selected')
        return

    def _read_fiddle_sd(self):

        if '-fiddle_sd' in sys.argv:
            Flags.set_fiddle_sd(True)
            Debug.write('[deprecated] Fiddle SD (3D) mode selected')
        return

    def _read_no_relax(self):

        if '-no_relax' in sys.argv:
            Flags.set_relax(False)
            Debug.write('XDS relax about indexing selected')
        return

    def _read_zero_dose(self):

        if '-zero_dose' in sys.argv:
            Flags.set_zero_dose(True)
            Debug.write('Zero-dose mode (XDS/XSCALE) selected')
        return

    def _read_no_correct(self):

        if '-no_correct' in sys.argv:
            Flags.set_no_correct(True)
            Debug.write('No-correct mode (XDS/XSCALE) selected')
        elif '-yes_correct' in sys.argv:
            Flags.set_no_correct(False)
            Debug.write('Yes-correct mode (XDS/XSCALE) selected')
        return

    def _read_norefine(self):

        if '-norefine' in sys.argv:
            Flags.set_refine(False)
            # FIXME what does this do??? - switch off orientation refinement
            # in integration
        return

    def _read_noremove(self):

        if '-noremove' in sys.argv:
            Flags.set_remove(False)
        return

    def _read_2d(self):

        if '-2d' in sys.argv:
            add_preference('integrater', 'mosflm')
            add_preference('scaler', 'ccp4')
            Debug.write('2D pipeline selected')
        return

    def _read_3d(self):

        if '-3d' in sys.argv:
            add_preference('integrater', 'xds')
            add_preference('scaler', 'xds')
            Debug.write('3D pipeline selected')
        return

    def _read_3dii(self):

        if '-3dii' in sys.argv:
            add_preference('indexer', 'xdsii')
            add_preference('integrater', 'xds')
            add_preference('scaler', 'xds')
            Debug.write('3D II pipeline (XDS IDXREF all images) selected')
        return

    def _read_debug(self):

        if '-debug' in sys.argv:
            # join the debug stream to the main output
            Debug.join(Chatter)
            Debug.write('Debugging output switched on')
        return

    def _read_migrate_data(self):

        if '-migrate_data' in sys.argv:
            Flags.set_migrate_data(True)
            Debug.write('Data migration switched on')
        return

    def _read_cell(self):
        '''Read the cell constants from the command line.'''

        index = -1

        try:
            index = sys.argv.index('-cell')
        except ValueError, e:
            # the token is not on the command line
            self.write('No cell passed in on the command line')
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        try:
            cell = sys.argv[index + 1].split(',')
        except IndexError, e:
            raise RuntimeError, \
                  '-cell correct use "-cell a,b,c,alpha,beta,gamma"'

        if len(cell) != 6:
            raise RuntimeError, \
                  '-cell correct use "-cell a,b,c,alpha,beta,gamma"'

        _cell = tuple(map(float, cell))

        Flags.set_cell(_cell)

        format = 6 * ' %7.2f'
        
        self.write('Cell passed on the command line: ' + \
                   format % _cell)

        Debug.write('Cell read from command line:' + \
                    format % _cell)

        return

    def _help_cell(self):
        '''Return a help string for the read cell method.'''
        return '-cell a,b,c,alpha,beta,gamma'

    def _read_free_fraction(self):
        try:
            index = sys.argv.index('-free_fraction')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_free_fraction(float(sys.argv[index + 1]))
        Debug.write('Free fraction set to %f' % Flags.get_free_fraction())
            
        return

    def _help_free_fraction(self):
        return '-free_fraction N'

    def _read_free_total(self):
        try:
            index = sys.argv.index('-free_total')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_free_total(int(sys.argv[index + 1]))
        Debug.write('Free total set to %f' % Flags.get_free_total())
            
        return

    def _help_free_total(self):
        return '-free_total N'

    def _read_fixed_628(self):
        try:
            index = sys.argv.index('-fixed_628')
        except ValueError, e:
            return

        if index < 0:
            raise RuntimeError, 'negative index'

        Flags.set_fixed_628()
            
        return

    def _help_fixed_628(self):
        return '-fixed_628'

CommandLine = _CommandLine()
CommandLine.setup()

if __name__ == '__main__':
    print CommandLine.get_beam()
    print CommandLine.get_xinfo()
