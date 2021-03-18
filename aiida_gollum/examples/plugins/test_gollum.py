#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.12.0"
__contributors__ = "Victor M. Garcia-Suarez"

import sys
import os

from aiida.common.example_helpers import test_and_get_code

################################################################

ParameterData = DataFactory('parameter')
#SinglefileData = DataFactory('singlefile')

#####- Execution arguments -------------------------------------

try:
    dontsend = sys.argv[1]
    if dontsend == "--dont-send":
        submit_test = True
    elif dontsend == "--send":
        submit_test = False
    else:
        raise IndexError
except IndexError:
    print >> sys.stderr, ("The first parameter can only be either "
                          "--send or --dont-send")
    sys.exit(1)

#####- Code ----------------------------------------------------

try:
    codename = sys.argv[2]
except IndexError:
    codename = 'go-2.0.0@cm135'

code = test_and_get_code(codename, expected_code_type='gollum.gollum')

#####- Set up calculation object -------------------------------

calc = code.new_calc()
calc.label = "Test Gollum. Spin-polarized chain"
calc.description = "Test calculation with the Gollum code. Spin-pol chain"

#####- Settings ------------------------------------------------

emname = os.path.realpath(os.path.join(os.path.dirname(__file__),
    "../data"))+'/Extended_Molecule'
l1name = os.path.realpath(os.path.join(os.path.dirname(__file__),
    "../data"))+'/Lead_1'
l2name = os.path.realpath(os.path.join(os.path.dirname(__file__),
    "../data"))+'/Lead_2'
settings_dict={'additional_local_copy_list': [emname, l1name, l2name],
               'cmdline': '/share/apps/MATLAB/MCR/MCR_R2017b/v92/'}
settings = ParameterData(dict=settings_dict)
calc.use_settings(settings)

#####- Parameters ----------------------------------------------

# SBlock is for string blocks and NBlock for numerical blocks
# The "atom" block is definied independently
params_dict= {
    'Mode': 1,
    'Verbose': 0,
    'HamiltonianProvider': 'tbm',
    'SBlock Path_Leads': """
    1 ./Lead_1
    2 ./Lead_2""",
    'Path_EM': './Extended_Molecule',
    'NBlock ERange': """
     -8.0 8.0 1000 """,
    'NBlock leadp': """
     2 2 -1
     2 2  1 """,
    'atom': """
     1 2 1
     0 0 1
     2 2 1 """
}
parameters = ParameterData(dict=params_dict)
calc.use_parameters(parameters)

#####- Singe file (if necessary) -------------------------------

#fileg = SinglefileData()
#absname = os.path.realpath(os.path.join(os.path.dirname(__file__),"data"))+'/Extended_Molecule'
#fileg.add_path(absname)
#calc.use_singlefile(fileg)

#####- Remote calculation settings -----------------------------

calc.set_max_wallclock_seconds(30*60) # 30 min
#calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 2})
calc.set_resources({"parallel_env": 'mpi', "tot_num_mpiprocs": 1})
code_mpi_enabled =  False
try:
    code_mpi_enabled =  code.get_extra("mpi")
except AttributeError:
    pass
calc.set_withmpi(code_mpi_enabled)
queue = None
# calc.set_queue_name(queue)

#####- Submmit test locally or remotely ------------------------

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test_submit for calculation (uuid='{}')".format(
        calc.uuid)
    print "Submit file in {}".format(os.path.join(
        os.path.relpath(subfolder.abspath),
        script_filename
        ))
else:
    calc.store_all()
    print "Created calc=Calculation(uuid='{}') #ID={}".format(
        calc.uuid,calc.dbnode.pk)
    calc.submit()
    print "Submitted calc=Calculation(uuid='{}') #ID={}".format(
        calc.uuid,calc.dbnode.pk)

