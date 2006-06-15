#!/usr/bin/env python
# Sweep.py
# Maintained by G.Winter
# 15th June 2006
# 
# A class to represent a sweep of frames collected under the same conditions.
# This pertains to the dataset object in the early phases of processing.
# 

import os
import sys
import copy
import time

if not os.environ.has_key('DPA_ROOT'):
    raise RuntimeError, 'DPA_ROOT not defined'
if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ['DPA_ROOT'] in sys.path: 
    sys.path.append(os.path.join(os.environ['DPA_ROOT']))

from Experts.FindImages import image2template, find_matching_images, \
     template_directory_number2image, image2template_directory, \
     headers2sweeps, headers2sweep_ids

from Schema.Object import Object

# image header reading functionality
from Wrappers.XIA.Printheader import Printheader

def SweepFactory(template, directory, beam = None):
    '''A factory which will return a list of sweep objects which match
    the input template and directory.'''

    sweeps = []

    images = find_matching_images(template, directory)

    headers = { }

    for i in images:
        image = template_directory_number2image(template,
                                                directory,
                                                i)
        ph = Printheader()
        ph.setImage(image)
        headers[i] = ph.readheader()

    sweep_ids = headers2sweep_ids(headers)

    for s in sweep_ids:
        sweeps.append(Sweep(template, directory,
                            id_image = s, beam = beam))

    return sweeps

class Sweep(Object):
    '''A class to represent a single sweep of frames.'''

    def __init__(self,
                 template,
                 directory,
                 id_image = None,
                 beam = None):

        '''Initialise the sweep by inspecting the images. id_image
        defines the first image in this sweep, and hence the identity of
        the sweep of more than one are found which match.'''

        Object.__init__(self)

        self._identity_attributes = ['_collect_start', '_collect_end',
                                     '_template', '_id_image']

        if not id_image is None:
            self._id_image = id_image
        else:
            self._id_image = -1

        # populate the attributes of this object

        self._template = template
        self._directory = directory

        # populate the rest of the structure
        self._images = []
        self.update()

        # if the beam has been specified, then use this
        if beam:
            self._beam = beam()

        return

    def getTemplate(self):
        return self._template

    def getDirectory(self):
        return self._directory

    def getImages(self):
        # check if any more images have appeared
        self.update()
        return self._images

    def getCollect(self):
        return self._collect_start, self._collect_end

    def getPhi(self):
        return self._phi

    def getExposure_time(self):
        return self._exposure_time

    def getDistance(self):
        return self._distance

    def getWavelength(self):
        return self._wavelength

    def getBeam(self):
        return self._beam

    def _read_headers(self):
        '''Get the image headers for all of the images - this is not designed
        to be called exernally.'''

        self._headers = { }
        
        t = time.time()

        for i in self._images:
            ph = Printheader()            
            image = template_directory_number2image(self._template,
                                                    self._directory,
                                                    i)
            ph.setImage(image)
            header = ph.readheader()
            self._headers[i] = header

        self.write('reading %d headers took %s s' % (len(self._images),
                                                     int(time.time() - t)))

        return

    def update(self):
        '''Check to see if any more frames have appeared - if they
        have update myself and reset.'''

        images = find_matching_images(self._template,
                                      self._directory)

        if len(images) > len(self._images):
            # more images have appeared - reset myself

            self._images = images
            
            self._read_headers()

            sweeps = headers2sweeps(self._headers)

            # select the correct "sweep" - at the moment
            # define this to be the one with the most frames
            # in, though some way of manually defining this
            # will be useful FIXME.

            sweep = None

            # select which sweep to represent - default to the largest
            # earliest one

            if self._id_image == -1:

                max_images = 0
                
                for s in sweeps:
                    if len(s['images']) > max_images:
                        sweep = s
                        max_images = len(s['images'])

            else:
                for s in sweeps:
                    if self._id_image in s['images']:
                        sweep = s

                if sweep is None:
                    raise RuntimeError, 'no matching sweep found'
                
            self._images = sweep['images']
            self._collect_start = sweep['collect_start']
            self._collect_end = sweep['collect_end']

            self._phi = (sweep['phi_start'], sweep['phi_end'],
                         sweep['phi_width'])
            self._exposure_time = sweep['exposure_time']
            self._distance = sweep['distance']
            self._wavelength = sweep['wavelength']
            self._beam = sweep['beam']

            self.reset()

        return

if __name__ == '__main__':

    if len(sys.argv) < 2:
        image = os.path.join(os.environ['DPA_ROOT'],
                             'Data', 'Test', 'Images', '12287_1_E1_001.img')
    else:
        image = sys.argv[1]
        
    template, directory = image2template_directory(image)
    
    sl = SweepFactory(template, directory)

    for s in sl:

        t = s.getCollect()
        print 'Data collection took %s seconds' % (t[1] - t[0])
        print 'For a total of %s seconds of exposure' % \
              (s.getExposure_time() * \
               len(s.getImages()))
    
                                                     
