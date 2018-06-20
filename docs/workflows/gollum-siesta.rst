Gollum Siesta workflow
++++++++++++++++++++++

Description
-----------

The **GollumSiestaWorkchain** workflow produces files with the
transmission and the number of open channels from the electronic
structure calculated with Siesta.

.. important:: In order for this workflow to work it is also necessary to install the aiida_siesta plugin (http://aiida-siesta-plugin.readthedocs.io/en/latest/)

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
Siesta calculation for the extended molecule and finally a Gollum
simulation to calculate the transport properties.

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

- fast::
    
             {
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

* **kpoints_le**, class :py:class:`KpointsData
  <aiida.orm.data.array.kpoints.StructureData>`

An array with the number of k-points along each direction in the leads

* **kpoints_em**, class :py:class:`KpointsData
  <aiida.orm.data.array.kpoints.StructureData>`

An array with the number of k-points along each direction in the
extended molecule

* **parameters**, class :py:class:`ParameterData
  <aiida.orm.data.parameter.ParameterData>`

Some parameters for the Gollum simulation (typically the *leadp* and
*atom* blocks).

Outputs
-------

* **open_channels** :py:class:`ArrayData <aiida.orm.data.array.ArrayData>` 

The number of open channels of the first electrode (we assume at the
moment that both electrodes are equal). In case of a spin-polarized
calculation the output distinguishes between spin-up and down channels.

* **transmission** :py:class:`ArrayData <aiida.orm.data.array.ArrayData>` 

The transmission between electrodes. In case of a spin-polarized
calculation the output distinguishes between spin-up and down transmissions.

