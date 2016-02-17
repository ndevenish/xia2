from __future__ import division
import json
import optparse
import sys

def parse_compound(compound):
  import string
  result = { }
  element = ''
  number = ''
  compound += 'X'
  for c in compound:
    if c in string.uppercase:
      if not element:
        element += c
        continue
      if number == '':
        count = 1
      else:
        count = int(number)
      if not element in result:
        result[element] = 0
      result[element] += count
      element = '' + c
      number = ''
      if c == 'X':
        break
    elif c in string.lowercase:
      element += c
    elif c in string.digits:
      number += c
  return result

def mtz_to_hklf4(hklin, out):
  from iotbx import mtz
  mtz_obj = mtz.object(hklin)
  miller_indices = mtz_obj.extract_original_index_miller_indices()
  i = mtz_obj.get_column('I').extract_values()
  sigi = mtz_obj.get_column('SIGI').extract_values()
  f = open(out, 'wb')
  for j, mi in enumerate(miller_indices):
    f.write('%4d%4d%4d' % mi)
    f.write('%8.2f%8.2f\n' % (i[j], sigi[j]))
  f.close()
  return

def to_shelx(hklin, prefix, compound='', options={}):
  '''Read hklin (unmerged reflection file) and generate SHELXT input file
  and HKL file'''

  from iotbx.reflection_file_reader import any_reflection_file
  from iotbx.shelx import writer
  from cctbx.xray.structure import structure
  from cctbx.xray import scatterer

  reader = any_reflection_file(hklin)
  intensities = [ma for ma in reader.as_miller_arrays(merge_equivalents=False)
                 if ma.info().labels == ['I', 'SIGI']][0]

  # FIXME do I need to reindex to a conventional setting here

  mtz_to_hklf4(hklin, '%s.hkl' % prefix)

  crystal_symm = intensities.crystal_symmetry()

  wavelength = options.wavelength
  if wavelength is None:
    mtz_object = reader.file_content()
    mtz_crystals = mtz_object.crystals()
    wavelength = mtz_crystals[1].datasets()[0].wavelength()
  print 'Experimental wavelength: %.3f Angstroms' % wavelength

  unit_cell_dims = None
  unit_cell_esds = None
  if options.cell:
    with open(options.cell, 'r') as fh:
      cell_data = json.load(fh)
      cell_data = cell_data.get('solution_constrained', cell_data['solution_unconstrained'])
      unit_cell_dims = tuple([
          cell_data[dim]['mean'] for dim in ['a', 'b', 'c', 'alpha', 'beta', 'gamma']
        ])
      unit_cell_esds = tuple([
          cell_data[dim]['population_standard_deviation'] for dim in ['a', 'b', 'c', 'alpha', 'beta', 'gamma']
        ])

  cb_op = crystal_symm.change_of_basis_op_to_reference_setting()

  if cb_op.c().r().as_hkl() == 'h,k,l':
    print 'Change of basis to reference setting: %s' % cb_op
    crystal_symm = crystal_symm.change_basis(cb_op)
    if str(cb_op) != "a,b,c":
      unit_cell_dims = None
      unit_cell_esds = None
      # Would need to apply operation to cell errors, too. Need a test case for this

  # crystal_symm.show_summary()
  xray_structure = structure(crystal_symmetry=crystal_symm)
  if compound:
    result = parse_compound(compound)
    for element in result:
      xray_structure.add_scatterer(scatterer(label=element,
                                             occupancy=result[element]))
  open('%s.ins' % prefix, 'w').write(''.join(
    writer.generator(xray_structure,
                     wavelength=wavelength,
                     full_matrix_least_squares_cycles=0,
                     title=prefix,
                     unit_cell_esds=unit_cell_esds)))

if __name__ == '__main__':
  parser = optparse.OptionParser("usage: %prog .mtz-file output-file [atoms]")
  parser.add_option("-?", action="help", help=optparse.SUPPRESS_HELP)
  parser.add_option("-w", "--wavelength", dest="wavelength", help="Override experimental wavelength (Angstrom)", default=None, type="float")
  parser.add_option("-c", "--cell", dest="cell", metavar="FILE", help="Read unit cell information from a .json file", default=None, type="string")
  options, args = parser.parse_args()
  if len(args) > 2:
    atoms = ''.join(args[2:])
    print 'Atoms: %s' % atoms
    to_shelx(args[0], args[1], atoms, options)
  elif len(args) == 2:
    print options
    to_shelx(args[0], args[1], options=options)
  else:
    parser.print_help()
