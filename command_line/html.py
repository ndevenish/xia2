# -*- coding: utf-8 -*-
# LIBTBX_SET_DISPATCHER_NAME dev.xia2.html

import sys
import os
import math
import time
import exceptions
import traceback

# Needed to make xia2 imports work correctly
import libtbx.load_env
xia2_root_dir = libtbx.env.find_in_repositories("xia2")
sys.path.insert(0, xia2_root_dir)
os.environ['XIA2_ROOT'] = xia2_root_dir
os.environ['XIA2CORE_ROOT'] = os.path.join(xia2_root_dir, "core")

from Handlers.Streams import Chatter, Debug

from Handlers.Files import cleanup
from Handlers.Citations import Citations
from Handlers.Environment import Environment, df

from Applications.xia2 import get_command_line, write_citations, help

from XIA2Version import Version

from lib.tabulate import tabulate

# XML Marked up output for e-HTPX
if not os.path.join(os.environ['XIA2_ROOT'], 'Interfaces') in sys.path:
  sys.path.append(os.path.join(os.environ['XIA2_ROOT'], 'Interfaces'))

def run():
  assert os.path.exists('xia2.json')
  from Schema.XProject import XProject
  xinfo = XProject.from_json(filename='xia2.json')

  rst = get_xproject_rst(xinfo)

  with open('xia2.new.html', 'wb') as f:
    print >> f, rst2html(rst)

  #with open('xia2.tex', 'wb') as f:
    #print >> f, rst2latex(rst)

  #with open('xia2.odt', 'wb') as f:
    #print >> f, rst2odt(rst)

def make_logfile_html(logfile):
    tables = extract_loggraph_tables(logfile)
    rst = []

    for table in tables:
      #for graph_name, html in table_to_google_charts(table).iteritems():
      for graph_name, html in table_to_c3js_charts(table).iteritems():
        #rst.append('.. __%s:\n' %graph_name)
        rst.append('.. raw:: html')
        rst.append('\n    '.join(html.split('\n')))

    rst = '\n'.join(rst)

    html_file = '%s.html' %(
      os.path.splitext(os.path.basename(logfile))[0])
    with open(html_file, 'wb') as f:
      print >> f, rst2html(rst)
    return html_file


def rst2html(rst):
  from docutils.core import publish_string
  from docutils.writers.html4css1 import Writer,HTMLTranslator

  class xia2HTMLTranslator(HTMLTranslator):
    def __init__(self, document):
      HTMLTranslator.__init__(self, document)

    def visit_table(self, node):
      self.context.append(self.compact_p)
      self.compact_p = True
      classes = ' '.join(['docutils', self.settings.table_style]).strip()
      self.body.append(
        self.starttag(node, 'table', CLASS=classes, border="0"))

    def write_colspecs(self):
      self.colspecs = []


  args = {
    'stylesheet_path': os.path.join(xia2_root_dir, 'css', 'voidspace.css')
  }

  w = Writer()
  w.translator_class = xia2HTMLTranslator

  return publish_string(rst, writer=w, settings=None, settings_overrides=args)

def rst2latex(rst):
  from docutils.core import publish_string
  from docutils.writers.latex2e import Writer

  w = Writer()

  return publish_string(rst, writer=w)

def rst2odt(rst):
  from docutils.core import publish_string
  from docutils.writers.odf_odt import Writer

  w = Writer()

  return publish_string(rst, writer=w)

def get_xproject_rst(xproject):

  lines = []

  lines.extend(overview_section(xproject))
  lines.extend(crystallographic_parameters_section(xproject))
  lines.extend(output_files_section(xproject))
  lines.extend(integration_status_section(xproject))
  lines.extend(detailed_statistics_section(xproject))

  return '\n'.join(lines)

def overview_section(xproject):
  lines = []
  lines.append('xia2 Processing Report: %s' %xproject.get_name())
  lines.append('#' * len(lines[-1]))

  lines.append('\n')
  xia2_status = 'normal termination' # XXX FIXME
  lines.append("xia2 version %s completed with status '%s'\n" %(
    Version.split()[-1], xia2_status))

  lines.append('Read output from `<%s/>`_\n' %os.path.abspath(os.path.curdir))

  columns = []
  columns.append([
    '',
    u'Wavelength (Å)',
    'High resolution limit',
    'Low resolution limit',
    'Completeness',
    'Multiplicity',
    'CC-half',
    'I/sigma',
    'Rmerge',
    'Anomalous completeness',
    'Anomalous multiplicity',
    #'See all statistics',
  ])

  for cname, xcryst in xproject.get_crystals().iteritems():
    statistics_all = xcryst.get_statistics()
    for wname in xcryst.get_wavelength_names():
      statistics = statistics_all[(xproject.get_name(), cname, wname)]
      xwav = xcryst.get_xwavelength(wname)
      high_res = statistics['High resolution limit']
      low_res = statistics['Low resolution limit']
      column = [
        wname, xwav.get_wavelength(),
        '%s (%s - %s)' %(high_res[0], low_res[2], high_res[2]),
        '%s (%s - %s)' %(low_res[0], high_res[2], low_res[2]),
        '%s' %statistics['Completeness'][0],
        '%s' %statistics['Multiplicity'][0],
        '%s' %statistics['CC half'][0],
        '%s' %statistics['I/sigma'][0],
        '%s' %statistics['Rmerge'][0],
        '%s' %statistics['Anomalous completeness'][0],
        '%s' %statistics['Anomalous multiplicity'][0],
      ]
      columns.append(column)

  table = [[c[i] for c in columns] for i in range(len(columns[0]))]

  cell = xcryst.get_cell()
  table.append(['','',''])
  table.append([u'Unit cell dimensions: a (Å)', '%.3f' %cell[0], ''])
  table.append([u'b (Å)', '%.3f' %cell[1], ''])
  table.append([u'c (Å)', '%.3f' %cell[2], ''])
  table.append([u'α (°)', '%.3f' %cell[3], ''])
  table.append([u'β (°)', '%.3f' %cell[4], ''])
  table.append([u'γ (°)', '%.3f' %cell[5], ''])

  from cctbx import sgtbx
  spacegroups = xcryst.get_likely_spacegroups()
  spacegroup = spacegroups[0]
  sg = sgtbx.space_group_type(str(spacegroup))
  spacegroup = sg.lookup_symbol()
  table.append(['','',''])
  table.append(['Space group', spacegroup, ''])

  twinning_score = ''
  table.append(['','',''])
  table.append(['Sfcheck twinning score', twinning_score, ''])

  headers = table.pop(0)

  lines.append('\n')
  lines.append('.. class:: table-one')
  lines.append('\n')
  lines.append(tabulate(table, headers, tablefmt='grid'))
  lines.append('\n')

    #Spacegroup P 41 2 2

    #Sfcheck twinning score     2.99
    #Your data do not appear to be twinned
    #All crystallographic parameters..

  lines.append('Contents of the rest of this document:')
  lines.append('\n')
  lines.append(
    '* `Reflection files output from xia2`_')
  lines.append(
    '* `Full statistics for each wavelength`_')
  lines.append(
    '* `Log files from individual stages`_')
  lines.append(
    '* `Integration status for images by wavelength and sweep`_')
  #lines.append(
    #'* `Lists of programs and citations`_')

  #lines.append('Inter-wavelength B and R-factor analysis')
  #lines.append('-' * len(lines[-1]))
  #lines.append('\n')

  return lines

def crystallographic_parameters_section(xproject):
  lines = []

  for cname, xcryst in xproject.get_crystals().iteritems():

    lines.append('\n')
    lines.append('Crystallographic parameters')
    lines.append('=' * len(lines[-1]))
    lines.append('\n')

    lines.append('Unit cell')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')

    cell = xcryst.get_cell()
    headers = [u'a (Å)', u'b (Å)', u'c (Å)', u'α (°)', u'β (°)', u'γ (°)']
    table = [['%.3f' %c for c in cell]]
    lines.append('\n')
    lines.append(tabulate(table, headers, tablefmt='grid'))
    lines.append('\n')

    lines.append('.. note:: The unit cell parameters are the average for all measurements.')
    lines.append('\n')

    from cctbx import sgtbx
    spacegroups = xcryst.get_likely_spacegroups()
    spacegroup = spacegroups[0]
    sg = sgtbx.space_group_type(str(spacegroup))
    spacegroup = sg.lookup_symbol()
    table.append(['Space group', spacegroup, ''])

    lines.append('Space group')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')
    lines.append('Space group: %s' %spacegroup)
    lines.append('\n')
    lines.append('Other possibilities could be:')
    lines.append('\n')
    if len(spacegroups) > 1:
      for sg in spacegroups[1:]:
        sg = sgtbx.space_group_type(str(sg))
        lines.append('* %s\n' %sg.lookup_symbol())
    lines.append('\n')
    lines.append('.. note:: The spacegroup was determined using pointless (see log file)')
    lines.append('\n')

    twinning_score = ''
    lines.append('Twinning analysis')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')
    lines.append('Overall twinning score: %s' %twinning_score)
    lines.append('Your data do not appear to be twinned')
    lines.append('\n')
    lines.append(
      '.. note:: The twinning score is the value of <E4>/<I2> reported by')
    lines.append(
      '      sfcheck (see `documentation <http://www.ccp4.ac.uk/html/sfcheck.html#Twinning%20test>`_)')
    lines.append('\n')

    lines.append('Asymmetric unit contents')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')
    lines.append('\n')
    lines.append('.. note:: No information on ASU contents (because no sequence information was supplied?)')
    lines.append('\n')

  return lines


def output_files_section(xproject):
  lines = []

  for cname, xcryst in xproject.get_crystals().iteritems():
    lines.append('Output files')
    lines.append('=' * len(lines[-1]))
    lines.append('\n')

    lines.append('.. _Reflection files output from xia2:\n')
    lines.append('Reflection data files')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')

    lines.append(
      'xia2 produced the following reflection data files - to download,'
      'right-click on the link and select "Save Link As..."')
    lines.append('\n')

    reflection_files = xcryst.get_scaled_merged_reflections()
    lines.append('MTZ files (useful for CCP4 and Phenix)')
    lines.append('_' * len(lines[-1]))
    lines.append('\n')

    headers = ['Dataset', 'File name']
    merged_mtz = reflection_files['mtz']
    table = [['All datasets', '`%s <%s>`_' %(os.path.basename(merged_mtz), merged_mtz)]]
    #['All datasets (unmerged)', '`%s <%s>`_' %(os.path.basename(merged_mtz), merged_mtz],

    for wname, unmerged_mtz in reflection_files['mtz_unmerged'].iteritems():
      table.append(
        [wname, '`%s <%s>`_' %(os.path.basename(unmerged_mtz), unmerged_mtz)])

    lines.append('\n')
    lines.append(tabulate(table, headers, tablefmt='rst'))
    lines.append('\n')


    lines.append('SCA files (useful for AutoSHARP, etc.)')
    lines.append('_' * len(lines[-1]))
    lines.append('\n')

    table = []
    for wname, merged_sca in reflection_files['sca'].iteritems():
      table.append(
        [wname, '`%s <%s>`_' %(os.path.basename(merged_sca), merged_sca)])

    lines.append('\n')
    lines.append(tabulate(table, headers, tablefmt='rst'))
    lines.append('\n')

    lines.append('SCA_UNMERGED files (useful for XPREP and Shelx C/D/E)')
    lines.append('_' * len(lines[-1]))
    lines.append('\n')

    table = []
    for wname, unmerged_sca in reflection_files['sca_unmerged'].iteritems():
      table.append(
        [wname, '`%s <%s>`_' %(os.path.basename(unmerged_sca), unmerged_sca)])

    lines.append('\n')
    lines.append(tabulate(table, headers, tablefmt='rst'))
    lines.append('\n')

    lines.append('.. _Log files from individual stages:\n')
    lines.append('Log files')
    lines.append('-' * len(lines[-1]))
    lines.append('\n')

    lines.append(
      'The log files are located in `<%s/LogFiles>`_ and are grouped by '
      'processing stage:' %os.path.abspath(os.path.curdir))

    table = []
    log_dir = os.path.join(os.path.abspath(os.path.curdir), 'LogFiles')
    import glob
    g = glob.glob(os.path.join(log_dir, '*.log'))
    for logfile in g:
      html_file = make_logfile_html(logfile)
      table.append(
        [os.path.basename(logfile),
         '`original <%s>`__' %logfile,
         '`html <%s>`__' %html_file
         ])
    lines.append('\n')
    lines.append(tabulate(table, headers, tablefmt='rst'))
    print tabulate(table, headers, tablefmt='rst')
    lines.append('\n')

  return lines


def integration_status_section(xproject):
  lines = []
  status_lines = []

  lines.append('\n')
  lines.append('.. _Integration status for images by wavelength and sweep:\n')
  lines.append('Integration status per image')
  lines.append('=' * len(lines[-1]))
  lines.append(
    'The following sections show the status of each image from the final '
    'integration run performed on each sweep within each dataset. The table '
    'below summarises the image status for each dataset and sweep.')

  overall_table = []
  headers = ['Dataset', 'Sweep', 'Good', 'Ok', 'Bad rmsd', 'Overloaded',
             'Many bad', 'Weak', 'Abandoned', 'Total']

  good = 'o'
  ok = '%'
  bad_rmsd = '!'
  overloaded = 'O'
  many_bad = '#'
  weak = '.'
  abandoned = '@'

  for cname, xcryst in xproject.get_crystals().iteritems():
    for wname in xcryst.get_wavelength_names():
      xwav = xcryst.get_xwavelength(wname)
      for xsweep in xwav.get_sweeps():
        intgr = xsweep._get_integrater()
        stats = intgr.show_per_image_statistics()
        status = stats.split(
          'Integration status per image')[1].split(':')[1].split(
            '"o" => good')[0].strip()
        status = ''.join(status.split())

        overall_table.append([
          wname, xsweep.get_name(),
          status.count(good), status.count(ok), status.count(bad_rmsd),
          status.count(overloaded), status.count(many_bad), status.count(weak),
          status.count(abandoned), len(status)])


        import textwrap
        status = '\n'.join('| %s' %s for s in textwrap.wrap(status, width=60))

        status_lines.append('\n')
        status_lines.append('Dataset %s' %wname)
        status_lines.append('-' * len(status_lines[-1]))
        status_lines.append('\n')
        batches = xsweep.get_image_range()
        status_lines.append(
          '%s: batches %d to %d' %(xsweep.get_name(), batches[0], batches[1]))
        status_lines.append('\n%s\n' %status)

        #if '(60/record)' in stats:
          #status_lines.append('\n')
          #status_lines.append('.. note:: (60 images/record)')
          #status_lines.append('\n')

  lines.append('\n')
  lines.append(tabulate(overall_table, headers, tablefmt='rst'))
  lines.append('\n')

  lines.extend(status_lines)
  return lines


def detailed_statistics_section(xproject):
  lines = []
  lines.append('\n')
  lines.append('.. _Full statistics for each wavelength:\n')
  lines.append('\n')
  lines.append('Detailed statistics for each dataset')
  lines.append('=' * len(lines[-1]))
  lines.append('\n')

  for cname, xcryst in xproject.get_crystals().iteritems():
    statistics_all = xcryst.get_statistics()

    from collections import OrderedDict

    for key, statistics in statistics_all.iteritems():

      pname, xname, dname = key

      lines.append('Dataset %s' %dname)
      lines.append('-' * len(lines[-1]))

      table = []

      headers = [' ', 'Overall', 'Low', 'High']

      available = statistics.keys()

      formats = OrderedDict([
        ('High resolution limit', '%6.2f'),
        ('Low resolution limit', '%6.2f'),
        ('Completeness', '%5.1f'),
        ('Multiplicity', '%5.1f'),
        ('I/sigma', '%5.1f'),
        ('Rmerge', '%5.3f'),
        ('Rmeas(I)', '%5.3f'),
        ('Rmeas(I+/-)', '%5.3f'),
        ('Rpim(I)', '%5.3f'),
        ('Rpim(I+/-)', '%5.3f'),
        ('CC half', '%5.3f'),
        ('Wilson B factor', '%.3f'),
        ('Partial bias', '%5.3f'),
        ('Anomalous completeness', '%5.1f'),
        ('Anomalous multiplicity', '%5.1f'),
        ('Anomalous correlation', '%6.3f'),
        ('Anomalous slope', '%5.3f'),
        ('dF/F', '%.3f'),
        ('dI/s(dI)', '%.3f'),
        ('Total observations', '%d'),
        ('Total unique', '%d')
      ])

      for k in formats.keys():
        if k in available:
          values = [formats[k] % v for v in statistics[k]]
          if len(values) == 1:
            values = [values[0], '', '']
          assert len(values) == 3
          table.append([k] + values)


      lines.append('\n')
      lines.append(tabulate(table, headers, tablefmt='grid'))
      lines.append('\n')

  return lines


def extract_loggraph_tables(logfile):
  from iotbx import data_plots
  return data_plots.import_ccp4i_logfile(file_name=logfile)


def table_to_google_charts(table, ):
  html_graphs = {}
  draw_chart_template = """

  function drawChart_%(name)s() {

    var data_%(name)s = new google.visualization.DataTable();
    %(columns)s

    %(rows)s

    var options = {
      width: 500,
      height: 250,
      hAxis: {
        title: '%(xtitle)s'
      },
      vAxis: {
        title: '%(ytitle)s'
      },
      title: '%(title)s'
    };

    var chart_%(name)s = new google.visualization.LineChart(
      document.getElementById('%(id)s'));

    chart_%(name)s.draw(data_%(name)s, options);

  }

"""

  import re
  #title = re.sub("[^a-zA-Z]","", table.title)

  divs = []

  for i_graph, graph_name in enumerate(table.graph_names):

    script = [
      "<!--Load the AJAX API-->",
      '<script type="text/javascript" src="https://www.google.com/jsapi"></script>',
      '<script type="text/javascript">',
      "google.load('visualization', '1', {packages: ['corechart']});",
    ]

    name = re.sub("[^a-zA-Z]","", graph_name)

    script.append("google.setOnLoadCallback(drawChart_%s);" %name)

    graph_columns = table.graph_columns[i_graph]

    columns = []
    for i_col in graph_columns:
      columns.append(
        "data_%s.addColumn('number', '%s');" %(name, table.column_labels[i_col]))

    add_rows = []
    add_rows.append('data_%s.addRows([' %name)
    data = [table.data[i_col] for i_col in graph_columns]
    n_rows = len(data[0])
    for j in xrange(n_rows) :
      row = [ col[j] for col in data ]
      add_rows.append('%s,' %row)
    add_rows.append(']);')

    script.append(draw_chart_template %({
      'name': name,
      'id': name,
      'columns': '\n    '.join(columns),
      'rows': '\n    '.join(add_rows),
      'xtitle': table.column_labels[graph_columns[0]],
      'ytitle': '',
      'title': graph_name,
     }))

    divs.append('<div class="graph" id="%s"></div>' %name)

    script.append('</script>')

    html_graphs[graph_name] = """
%(script)s

<!--Div that will hold the chart-->
%(div)s

  """ %({'script': '\n'.join(script),
         'div': '\n'.join(divs)})

  return html_graphs


def table_to_c3js_charts(table, ):
  html_graphs = {}
  draw_chart_template = """
var chart_%(name)s = c3.generate({
    bindto: '#chart_%(name)s',
    data: %(data)s,
    axis: %(axis)s,
    legend: {
      position: 'right'
    },
});
"""

  import re

  divs = []

  ## local files in xia2 distro
  #c3css = os.path.join(xia2_root_dir, 'c3', 'c3.css')
  #c3js = os.path.join(xia2_root_dir, 'c3', 'c3.min.js')
  #d3js = os.path.join(xia2_root_dir, 'd3', 'd3.min.js')

  # webhosted files
  c3css = 'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.10/c3.css'
  c3js = 'https://cdnjs.cloudflare.com/ajax/libs/c3/0.4.10/c3.min.js'
  d3js = 'https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js'

  for i_graph, graph_name in enumerate(table.graph_names):
    print graph_name

    script = [
      '<!-- Load c3.css -->',
      '<link href="%s" rel="stylesheet" type="text/css">' %c3css,
      '<!-- Load d3.js and c3.js -->',
      '<script src="%s" charset="utf-8"></script>' %d3js,
      '<script src="%s"></script>' %c3js,
      '<script type="text/javascript">',
    ]

    name = re.sub("[^a-zA-Z]","", graph_name)

    row_dicts = []
    graph_columns = table.graph_columns[i_graph]
    for row in zip(*[table.data[i_col] for i_col in graph_columns]):
      row_dict = {'name': ''}
      for i_col, c in enumerate(row):
        row_dict[table.column_labels[graph_columns[i_col]]] = c
      row_dicts.append(row_dict)

    data_dict = {'json': row_dicts,
                 'keys': {
                   'x': table.column_labels[graph_columns[0]],
                   'value': [table.column_labels[i_col]
                             for i_col in graph_columns[1:]]}
                 }

    import json

    xlabel = table.column_labels[graph_columns[0]]
    if xlabel in ('1/d^2', '1/resol^2'):
      xlabel = u'Resolution (Å)'
      tick = """\
tick: {
          format: function (x) { return (1/Math.sqrt(x)).toFixed(2); }
        }
"""
    else:
      tick = ''

    axis = """
    {
      x: {
        label: {
          text: '%(text)s',
          position: 'outer-center'
        },
        %(tick)s
      }
    }
""" %{'text': xlabel,
      'tick': tick}

    script.append(draw_chart_template %({
      'name': name,
      'id': name,
      'data': json.dumps(data_dict, indent=2),
      'axis': axis,
     }))

    divs = []
    divs.append('''\
<div>
  <p>%s</p>
  <div class="graph" id="chart_%s"></div
</div>''' %(graph_name, name))

    script.append('</script>')

    html_graphs[graph_name] = """
<!--Div that will hold the chart-->
%(div)s

%(script)s

  """ %({'script': '\n'.join(script),
         'div': '\n'.join(divs)})

  return html_graphs


if __name__ == '__main__':
  run()