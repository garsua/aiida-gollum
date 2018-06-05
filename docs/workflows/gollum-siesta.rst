Gollum Siesta workflow
++++++++++++++++++++++

Description
-----------

The **GollumSiestaWorkchain** workflow produces files with the
transmission through the system and the number of open channels
of each electrode from the electronic structure obtained from
Siesta calculations.

The inputs to the Gollum workchain include the Siesta code, the Gollum
code, the structures of the leads and the extended molecule, the
protocol, the number of kpoints in the leads and the extended molecule
and some parameters.

The Gollum package can calculate transport properties such as the
transmission and the number of open channels either from tight-binding
or ab-initio simulations. In the latter case, it can use the Siesta
or QuantumEspresso-Wannier90 codes. This workflow presents an
example of transport calculation with the Siesta code. First, it
launches a Siesta calculation to simulate the leads, then another
Siesta calculation for the extended molecule and finally it launches
a Gollum simulation to calculate the transport properties.

Supported Gollum versions
-------------------------

At least 2.0.0 version of the code, which can be downloaded from the Golum
webpage (http://www.physics.lancs.ac.uk/gollum/index.php/downloads).

Inputs
------

* **siesta_code**
  
A code associated to the Siesta plugin

* **gollum_code**

A code associated to the Gollum plugin

* **structure_le**, class :py:class:`StructureData
  <aiida.orm.data.structure.StructureData>`

A Siesta structure for the leads.

* **structure_em**, class :py:class:`StructureData
  <aiida.orm.data.structure.StructureData>`

A Siesta structure for the extended molecule.

* **protocol**, class :py:class:`Str <aiida.orm.data.base.Str>`

Either "standard" or "fast". Each has its own set of associated
parameters.

- standard::

             {
                'kpoints_mesh_offset': [0., 0., 0.],
                'kpoints_mesh_density': 0.2,
                'dm_convergence_threshold': 1.0e-4,
                'forces_convergence_threshold': "0.02 eV/Ang",
                'min_meshcutoff': 100, # In Rydberg (!)
                'electronic_temperature': "25.0 meV",
                'md-type-of-run': "cg",
                'md-num-cg-steps': 10,
                'pseudo_familyname': 'lda-ag',
                'atomic_heuristics': {
                    'H': { 'cutoff': 100 },
                    'Si': { 'cutoff': 100 }
                },
                'basis': {
                    'pao-energy-shift': '100 meV',
                    'pao-basis-size': 'DZP'
                }
	      }

- fast::
    
             {
                'kpoints_mesh_offset': [0., 0., 0.],
                'kpoints_mesh_density': 0.25,
                'dm_convergence_threshold': 1.0e-3,
                'forces_convergence_threshold': "0.2 eV/Ang",
                'min_meshcutoff': 80, # In Rydberg (!)
                'electronic_temperature': "25.0 meV",
                'md-type-of-run': "cg",
                'md-num-cg-steps': 8,
                'pseudo_familyname': 'lda-ag',
                'atomic_heuristics': {
                    'H': { 'cutoff': 50 },
                    'Si': { 'cutoff': 50 }
                },
                'basis': {
                    'pao-energy-shift': '100 meV',
                    'pao-basis-size': 'SZP'
                }
	      }

* **kpoints_le**, class :py:class:`KpointsData
  <aiida.orm.data.array.kpoints.StructureData>`

An array with the number of k-points along each direction in the leads

* **kpoints_em**, class :py:class:`KpointsData
  <aiida.orm.data.array.kpoints.StructureData>`

An array with the number of k-points along each direction in the
extended molecule

* **parameters**, class :py:class:`ParameterData
  <aiida.orm.data.parameter.ParameterData>`

Some parameters for the Gollum simulation (tipically the *leadp* and
*atom* blocks).

Outputs
-------

* **transmission** :py:class:`ArrayData <aiida.orm.data.array.ArrayData>` 

The transission between electrodes.

* **open_channels** :py:class:`ArrayData <aiida.orm.data.array.ArrayData>` 

The number of open channels of each electrode.

