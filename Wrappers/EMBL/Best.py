import os
import sys

from xia2.Driver.DriverFactory import DriverFactory

def BestStrategy(DriverType=None):

  DriverInstance = DriverFactory.Driver(DriverType)

  class BestStrategyWrapper(DriverInstance.__class__):

    def __init__(self):
      DriverInstance.__class__.__init__(self)

      self.set_executable('best')

      # Input parameters - lower case per frame
      # upper case whole scan

      self._detector = None
      self._t_ref = None
      self._trans_ref = 100.0
      self._t_min = None
      self._T_max = None
      self._S_max = None
      self._w_min = None
      self._M_min = None
      self._C_min = None
      self._i2s = None
      self._sensitivity = None
      self._shape = None
      self._mos_dat = None
      self._mos_par = None
      self._mos_hkl = []
      self._anomalous = False
      self._xmlout = None

      # output parameters
      self._phi_start = None
      self._phi_end = None
      self._phi_width = None
      self._completeness = None
      self._multiplicity = None
      self._exposure_time = None
      self._transmission = None
      self._resolution = None

      return

    def set_detector(self, detector):
      self._detector = detector

    def set_t_ref(self, t_ref):
      self._t_ref = t_ref

    def set_trans_ref(self, trans_ref):
      self._trans_ref = trans_ref

    def set_T_max(self, T_max):
      self._T_max = T_max

    def set_t_min(self, t_min):
      self._t_min = t_min

    def set_S_max(self, S_max):
      self._S_max = S_max

    def set_w_min(self, w_min):
      self._w_min = w_min

    def set_M_min(self, M_min):
      self._M_min = M_min

    def set_C_min(self, C_min):
      self._C_min = C_min

    def set_i2s(self, i2s):
      self._i2s = i2s

    def set_sensitivity(self, sensitivity):
      self._sensitivity = sensitivity

    def set_shape(self, shape):
      self._shape = shape

    def set_mos_dat(self, mos_dat):
      self._mos_dat = mos_dat

    def set_mos_par(self, mos_par):
      self._mos_par = mos_par

    def add_mos_hkl(self, mos_hkl):
      self._mos_hkl.append(mos_hkl)

    def set_anomalous(self, anomalous = True):
      self._anomalous = anomalous

    def set_xmlout(self, xmlout):
      self._xmlout = xmlout

    def get_phi_start(self):
      return self._phi_start

    def get_phi_end(self):
      return self._phi_end

    def get_phi_width(self):
      return self._phi_width

    def get_completeness(self):
      return self._completeness

    def get_multiplicity(self):
      return self._multiplicity

    def strategy(self):

      assert self._detector is not None
      assert self._t_ref is not None

      command_line = []

      command_line.extend(('-f', '%s' %self._detector))
      command_line.extend(('-t', '%.3f' %self._t_ref))
      if self._t_min is not None:
        command_line.extend(('-M', '%.3f' %self._t_min))
      if self._T_max is not None:
        command_line.extend(('-T', '%.3f' %self._T_max))
      if self._S_max is not None:
       command_line.extend(('-S', '%.3f' %self._S_max))
      if self._w_min is not None:
       command_line.extend(('-w', '%.3f' %self._w_min))
      if self._M_min is not None:
        command_line.extend(('-R', '%.3f' %self._M_min))
      if self._C_min is not None:
        command_line.extend(('-C', '%.3f' %self._C_min))
      if self._i2s is not None:
       command_line.extend(('-i2s', '%.3f' %self._i2s))
      if self._sensitivity is not None:
        command_line.extend(('-su', '%.3f' %self._sensitivity))
      if self._shape is not None:
       command_line.extend(('-sh', '%.3f' %self._shape))

      if self._anomalous:
        command_line.append('-a')
      if self._xmlout is not None:
        command_line.extend(('-dna', self._xmlout))

      command_line.append('-mos')
      command_line.append(self._mos_dat)
      command_line.append(self._mos_par)
      for mos_hkl in self._mos_hkl:
        command_line.append(mos_hkl)

      self.set_command_line(command_line)
      self.start()
      self.close_wait()

      # FIXME really I should check for bugs or errors
      output = self.get_all_output()

      for record in output:
        if 'ERROR' in record:
          raise RuntimeError, record.strip()

      # BEWARE this is dependent on order of output
      for j, record in enumerate(output):
        tokens = record.split()
        if 'Phi_start - Phi_finish' in record:
          self._phi_start = float(tokens[-3])
          self._phi_end = float(tokens[-1])
        if 'Overall Completeness' in record:
          self._completeness = float(tokens[-1].replace('%', ''))
        if 'Redundancy' in record:
          m = tokens[-1]
          if m != 'automatic':
            m = float(m)
          self._multiplicity = m
        if 'WEDGE PARAMETERS' in record:
          data_items = output[j + 6].replace('|', ' ').split()
          self._phi_width = float(data_items[2])
          self._exposure_time = float(data_items[3])
        if 'Resolution limit =' in record and 'Transmission =' in record:
          self._transmission = float(tokens[6].replace('%', ''))
          self._resolution = float(tokens[2].replace('=', ''))

      return

    def get_completeness(self):
      return self._completeness

    def get_multiplicity(self):
      return self._multiplicity

    def get_exposure_time(self):
      return self._exposure_time

    def get_transmission(self):
      return self._transmission

    def get_resolution(self):
      return self._resolution

  return BestStrategyWrapper()

if __name__ == '__main__':

  best = BestStrategy()
  best.set_detector('pilatus6m')
  best.set_t_ref(0.5)
  best.set_T_max(807)
  best.set_t_min(0.067)
  best.set_trans_ref(25.0)
  best.set_S_max(10.0)
  best.set_w_min(0.1)
  best.set_M_min(3.0)
  best.set_C_min(99.0)
  best.set_i2s(2.0)
  best.set_mos_dat('bestfile.dat')
  best.set_mos_par('bestfile.par')
  best.add_mos_hkl('bestfile.hkl')
  best.set_anomalous(False)
  best.strategy()

  print 'Native'
  print 'Start / end / width: %.2f/%.2f/%.2f' % (best.get_phi_start(), best.get_phi_end(), best.get_phi_width())
  print 'Completeness / multiplicity / resolution: %.2f/%.2f/%.2f' % (best.get_completeness(), best.get_multiplicity(), best.get_resolution())
  print 'Transmission / exposure %.3f/%.3f' % (best.get_transmission(), best.get_exposure_time())

  best.set_anomalous(True)
  best.strategy()

  print 'Anomalous'
  print 'Start / end / width: %.2f/%.2f/%.2f' % (best.get_phi_start(), best.get_phi_end(), best.get_phi_width())
  print 'Completeness / multiplicity / resolution: %.2f/%.2f/%.2f' % (best.get_completeness(), best.get_multiplicity(), best.get_resolution())
  print 'Transmission / exposure %.3f/%.3f' % (best.get_transmission(), best.get_exposure_time())