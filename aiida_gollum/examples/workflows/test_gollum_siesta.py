#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

#
# An example of Workchain to perform a transport simulation from
# the electronic structure (leads and extende molecule) calculated
# with Siesta
#
import argparse
from aiida.common.exceptions import NotExistent
from aiida.orm.data.base import Int, Str, Float
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.array.kpoints import KpointsData
from aiida_siesta.data.psf import PsfData
from aiida.work.run import run

from aiida_gollum.workflows.gollumsiesta import GollumSiestaWorkChain

import os

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.12.0"
__contributors__ = "Victor M. Garcia-Suarez"

def parser_setup():
    """
    Setup the parser of command line arguments and return it. This is separated from the main
    execution body to allow tests to effectively mock the setup of the parser and the command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Run the GollumSiestaWorkChain for given input structures',
    )
    parser.add_argument(
        '-c', type=str, required=True, dest='siesta_codename',
        help='the AiiDA code that references siesta.siesta plugin'
    )
    parser.add_argument(
        '-g', type=str, required=True, dest='gollum_codename', 
        help='the AiiDA code that references siesta.gollum plugin'
    )
    parser.add_argument(
        '-p', type=str, required=False, dest='protocol', default='standard',
        help='the protocol (default: %(default)s)'
    )
    parser.add_argument(
        '-l', type=int, required=False, dest='structure_le', default=0,
        help='the node id of the structure of the leads'
    )
    parser.add_argument(
        '-e', type=int, required=False, dest='structure_em', default=0,
        help='the node id of the structure of the extended molecule'
    )

    return parser


def execute(args):
    """
    The main execution of the script, which will run some preliminary checks on the command
    line arguments before passing them to the workchain and running it
    """
    try:
        siesta_code = Code.get_from_string(args.siesta_codename)
    except NotExistent as exception:
        print "Execution failed: could not retrieve the code '{}'".format(args.siesta_codename)
        print "Exception report: {}".format(exception)
        return

    try:
        gollum_code = Code.get_from_string(args.gollum_codename)
    except NotExistent as exception:
        print "Execution failed: could not retrieve the code '{}'".format(args.gollum_codename)
        print "Exception report: {}".format(exception)
        return

    protocol = Str(args.protocol)
    
    ###### Siesta structures ##############################
    alat = 1.00 # Angstrom. Not passed to the fdf file

    # Leads
    cellle = [[20.,  0.,  0.,],
              [ 0., 20.,  0.,],
              [ 0.,  0.,  5.,]]
    sle = StructureData(cell=cellle)
    for i in range(0,2):
        sle.append_atom(position=(0.,0.,i*2.5),symbols=['Au'])

    if args.structure_em > 0:
        structure_le = load_node(args.structure_le)
    else:
        structure_le = sle

    # Extended molecule
    cellem = [[20.,  0.,  0.,],
              [ 0., 20.,  0.,],
              [ 0.,  0., 45.,]]
    sem = StructureData(cell=cellem)
    for i in range(0,18):
        sem.append_atom(position=(0.,0.,i*2.5),symbols=['Au'])

    if args.structure_em > 0:
        structure_em = load_node(args.structure_em)
    else:
        structure_em = sem

    ###### Siesta k-ppoints ###############################
    kpoints_le = KpointsData()
    kpoints_le.set_kpoints_mesh([1,1,90])

    kpoints_em = KpointsData()
    kpoints_em.set_kpoints_mesh([1,1,10])

    ###### Gollum parameters ##############################
    # The "atom" block is definied independently
    pms = {
        'NBlock leadp': """
        2 2 -1
        2 2 1 """,
        'atom': """
        1 2  2
        0 0 10
        2 2  2 """
    }
    parameters = ParameterData(dict=pms)

    ######

    run(GollumSiestaWorkChain,
        siesta_code=siesta_code,
        gollum_code=gollum_code,
        structure_le=structure_le,
        structure_em=structure_em,
        protocol=protocol,
        kpoints_le=kpoints_le,
        kpoints_em=kpoints_em,
        parameters=parameters
    )


def main():
    """
    Setup the parser to retrieve the command line arguments and pass them to the main execution function.
    """
    parser = parser_setup()
    args   = parser.parse_args()
    result = execute(args)


if __name__ == "__main__":
    main()
