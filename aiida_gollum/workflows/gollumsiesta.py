# -*- coding: utf-8 -*-
from aiida.orm import Code
from aiida.orm.data.base import Bool, Int, Str, Float
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.remote import RemoteData

from aiida.work.run import submit
from aiida.work.workchain import WorkChain, ToContext
from aiida.work.workfunction import workfunction
from aiida.common.links import LinkType

from aiida_siesta.data.psf import get_pseudos_from_structure
from aiida_siesta.calculations.siesta import SiestaCalculation
from aiida_siesta.workflows.base import SiestaBaseWorkChain

from aiida_gollum.calculations.gollum import GollumCalculation

import os

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.12.0"
__contributors__ = "Victor M. Garcia-Suarez"
                        
class GollumSiestaWorkChain(WorkChain):
    """
    Gollum Workchain. An example of workflow composition for transport
    """

    def __init__(self, *args, **kwargs):
        super(GollumSiestaWorkChain, self).__init__(*args, **kwargs)

    @classmethod
    def define(cls, spec):
        super(GollumSiestaWorkChain, cls).define(spec)
        spec.input('siesta_code', valid_type=Code)
        spec.input('gollum_code', valid_type=Code)
        spec.input('structure_le', valid_type=StructureData)
        spec.input('structure_em', valid_type=StructureData)
        spec.input('protocol', valid_type=Str, default=Str('standard'))
        spec.input('kpoints_le', valid_type=KpointsData)
        spec.input('kpoints_em', valid_type=KpointsData)
        spec.input('parameters', valid_type=ParameterData)
        spec.outline(
            cls.setup_siesta_inputs,
            cls.setup_protocol,
            cls.setup_structures,
            cls.setup_pseudo_potentials,
            cls.setup_siesta_parameters,
            cls.setup_basis,
            cls.setup_kpoints,
            cls.run_leads,
            cls.run_extmol,
            cls.setup_gollum_inputs,
            cls.setup_gollum_settings,
            cls.setup_gollum_parameters,
            cls.run_gollum,
            cls.run_results,
        )
        spec.dynamic_output()
                                         
    def setup_siesta_inputs(self):
        """
        Setup of context variables and inputs for the SiestaBaseWorkChain.
        Based on the specified protocol, we define values for variables that
        affect the execution of the calculations
        """
        self.ctx.siesta_inputs = {
            'siesta_code': self.inputs.siesta_code,
            'parameters': {},
            'settings': {},
            'options': ParameterData(dict={
                'resources': {
                    'parallel_env': 'mpi',
                    'tot_num_mpiprocs':1
                },
                'max_wallclock_seconds': 1800,
            }),
        }

    def setup_protocol(self):
        if self.inputs.protocol == 'standard':

            self.report('running the workchain in the "{}" protocol'.format(self.inputs.protocol.value))

            self.ctx.protocol = {
                'dm_convergence_threshold': 1.0e-4,
                'min_meshcutoff': 150, # In Rydberg (!)
                'electronic_temperature': "25.0 meV",
                'pseudo_familyname': 'si_ldapsf',
                'atomic_heuristics': {
                    'Au': { 'cutoff': 100 }
                },
                'basis': {
                    'pao-energy-shift': '100 meV',
                    'pao-basis-size': 'DZP'
                }
                          
            }
        elif self.inputs.protocol == 'fast':

            self.report('running the workchain in the "{}" protocol'.format(self.inputs.protocol.value))

            self.ctx.protocol = {
                'dm_convergence_threshold': 1.0e-3,
                'min_meshcutoff': 80, # In Rydberg (!)
                'electronic_temperature': "25.0 meV",
                'pseudo_familyname': 'si_ldapsf',
                'atomic_heuristics': {
                    'Au': { 'cutoff': 50 }
                },
                'basis': {
                    'pao-energy-shift': '100 meV',
                    'pao-basis-size': 'SZ'
                }
                          
            }
        else:
            self.abort_nowait('Protocol {} not known'.format(self.ctx.protocol.value))

    def setup_structures(self):
        """
        Very simple. Avoid seekpath for now
        """

        self.report('Running setup_structures')
        
        self.ctx.structure_le = self.inputs.structure_le
        self.ctx.structure_em = self.inputs.structure_em

    def setup_pseudo_potentials(self):
        """
        Based on the given input structure, get the 
        pseudo potentials for the different elements in the structure
        """

        self.report('Running setup_pseudo_potentials')

        structure = self.ctx.structure_em
        pseudo_familyname = self.ctx.protocol['pseudo_familyname']
        self.ctx.siesta_inputs['pseudos'] = get_pseudos_from_structure(structure, pseudo_familyname)

    def setup_siesta_parameters(self):
        """
        Setup the default input parameters required for a
        SiestaCalculation and the SiestaBaseWorkChain
        """

        self.report('Running setup_siesta_parameters')

        structure = self.ctx.structure_em
        meshcutoff = 0.0

        for kind in structure.get_kind_names():
            try:
                cutoff = self.ctx.protocol['atom_heuristics'][kind]['cutoff']
                meshcutoff = max(meshcutoff,cutoff)
            except:
                pass    # No problem. No heuristics, no info

        # In case nothing was gotten, set a minimum value
        meshcutoff = max(self.ctx.protocol['min_meshcutoff'], meshcutoff)    
                
        self.ctx.siesta_inputs['parameters'] = {
            'dm-tolerance': self.ctx.protocol['dm_convergence_threshold'],
            'mesh-cutoff': "{} Ry".format(meshcutoff),
            'electronic-temperature':
                self.ctx.protocol['electronic_temperature'],
            'maxscfiterations': 1000,
            'dm-mixingweight': 0.05,
            'dm-numberpulay': 5,
            'dm-numberkick': 5,
            'dm-kickmixingweight': 0.1,
            'writeeigenvalues': True,
            'savehs': True,
            '#SystemLabel': 'aiida',
            '#LatticeConstant': '1.000 Ang',
        }

    def setup_basis(self):
        """
        Setup the basis dictionary.
        """

        self.report('Running setup_basis')

        self.ctx.siesta_inputs['basis'] = self.ctx.protocol['basis']
        
    def setup_kpoints(self):
        """
        Define the k-point mesh for the Siesta calculations
        """

        self.report('Running setup_kpoints')

        self.ctx.kpoints_le = self.inputs.kpoints_le
        self.ctx.kpoints_em = self.inputs.kpoints_em

    def run_leads(self):
        """
        Run the SiestaBaseWorkChain to calculate the extended molecule
        structure
        """

        self.report('Running run_leads')

        siesta_inputs = dict(self.ctx.siesta_inputs)

        rle_inputs = {}
        rle_inputs['code'] = siesta_inputs['siesta_code']
        rle_inputs['kpoints'] = self.ctx.kpoints_le
        rle_inputs['basis'] = ParameterData(dict=siesta_inputs['basis'])
        rle_inputs['structure'] = self.ctx.structure_le
        rle_inputs['pseudos'] = siesta_inputs['pseudos']
        rle_inputs['parameters'] = ParameterData(dict=siesta_inputs['parameters'])
        rle_inputs['settings'] = ParameterData(dict=siesta_inputs['settings'])
        rle_inputs['clean_workdir'] = Bool(False)
        rle_inputs['max_iterations'] = Int(20)
        rle_inputs['options'] = siesta_inputs['options']
        
        running = submit(SiestaBaseWorkChain, **rle_inputs)

        self.report('launched SiestaBaseWorkChain<{}> in run-Siesta mode'.format(running.pid))
        
        return ToContext(workchain_leads=running)

    def run_extmol(self):
        """
        Run the SiestaBaseWorkChain to calculate the extended molecule
        structure
        """

        self.report('Running run_extmol')

        siesta_inputs = dict(self.ctx.siesta_inputs)

        rem_inputs = {}
        rem_inputs['code'] = siesta_inputs['siesta_code']
        rem_inputs['kpoints'] = self.ctx.kpoints_em
        rem_inputs['basis'] = ParameterData(dict=siesta_inputs['basis'])
        rem_inputs['structure'] = self.ctx.structure_em
        rem_inputs['pseudos'] = siesta_inputs['pseudos']
        rem_inputs['parameters'] = ParameterData(dict=siesta_inputs['parameters'])
        rem_inputs['settings'] = ParameterData(dict=siesta_inputs['settings'])
        rem_inputs['clean_workdir'] = Bool(False)
        rem_inputs['max_iterations'] = Int(20)
        rem_inputs['options'] = siesta_inputs['options']
        
        running = submit(SiestaBaseWorkChain, **rem_inputs)

        self.report('launched SiestaBaseWorkChain<{}> in run-Siesta mode'.format(running.pid))
        
        return ToContext(workchain_extmol=running)

    def setup_gollum_inputs(self):
        """
        Setup of context variables and inputs for the GollumSiestaWorkChain.
        Define values for variables that affect the execution of the
        calculations
        """
        self.ctx.gollum_inputs = {
            'gollum_code': self.inputs.gollum_code,
            'settings': {},
            'parameters': {},
            'options' : {
                'resources': {
                    'parallel_env': 'mpi',
                    'tot_num_mpiprocs': 1
                },
                'max_wallclock_seconds': 600
            }
        }

    def setup_gollum_settings(self):
        """
        Setup the default input settings required for a
        GollumSiestaCalculation
        """
        self.ctx.gollum_inputs['settings']={
                'cmdline': '/share/apps/MATLAB/MCR/MCR_R2017b/v92/'}

    def setup_gollum_parameters(self):
        """
        Setup the default input parameters required for a
        GollumSiestaCalculation
        """
        atm = self.inputs.parameters.get_dict()
        self.ctx.gollum_inputs['parameters'] = {
            'Mode': 1,
            'Verbose': 0,
            'HamiltonianProvider': 'dft',
            'NBlock ERange': """
            -8.0 8.0 1000 """,
            'NBlock leadp': atm['NBlock leadp'],
            'atom': atm['atom']
        }

    def run_gollum(self):
        """
        Run a GollumCalculation with the calculation parent folder
        """

        self.report('Running Gollum calculation')

        ginputs = dict(self.ctx.gollum_inputs)

        # Get the remote folders of previous calculations
        remote_folder_le = self.ctx.workchain_leads.get_outputs_dict()['remote_folder']
        lepath = remote_folder_le.get_remote_path()
        lep = "\n 1 " + lepath + "/aiida.out" + "\n 2 " + lepath + "/aiida.out"

        remote_folder_em = self.ctx.workchain_extmol.get_outputs_dict()['remote_folder']
        empath = remote_folder_em.get_remote_path()
        emp = empath + "/aiida.out"

        ginputs['parameters'].update({
            'SBlock Path_Leads': lep,
            'Path_EM': emp,
            })

        gollum_inputs = {}
        gollum_inputs['code'] = ginputs['gollum_code']
        #gollum_inputs['parent_folder'] = remote_folder
        gollum_inputs['settings'] = ParameterData(dict=ginputs['settings'])
        gollum_inputs['parameters'] = ParameterData(dict=ginputs['parameters'])
        gollum_inputs['_options'] = ginputs['options']

        process = GollumCalculation.process()
        running = submit(process, **gollum_inputs)
        
        self.report('launching GollumCalculation<{}>'.format(running.pid))
        
        return ToContext(gollum_calc=running)

    def run_results(self):
        """
        Attach the relevant output nodes from the gollum calculation to the workchain outputs
        for convenience
        """
        calculation_gollum = self.ctx.gollum_calc

        self.report('workchain succesfully completed'.format())
