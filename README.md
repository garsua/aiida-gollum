# AiiDA-Gollum plugins and workflows

A plugin with the [Gollum](http://www.physics.lancs.ac.uk/gollum/) transport
code interface to the [AiiDA](http://www.aiida.net/) system.

The Gollum input plugin, parser, workflow and examples were developed
by Víctor Manuel García-Suárez.

This version of the plugin only works with the aiida-0.12.0 version.

![Aiida](docs/images/aiida-gollum.png)

## Documentation

Basic documentation can be found in:

https://github.com/garsua/aiida-gollum/tree/master/docs

## Installation

Install the plugin by executing, from the top level of the plugin directory:

```
pip install -e .
```
As a pre-requisite, this will install an appropriate version of the aiida_core python framework.

Next, do not forget to run the following command:

```
reentry scan -r aiida
```
This is to make sure all other plugins are discovered and registered.

# License  

The terms of the AiiDA-Gollum license can be found in the LICENSE.txt file.

# Acknowledgements

We acknowledge support from the Spanish MINECO (project FIS2015-63918-R),
the Spanish Ministerio de Ciencia, Innovación y Universidades
(project PGC2018-094783-B-I00) and the EU Centre of Excellence
"MaX - Materials Design at the Exascale" (http://www.max-centre.eu,
Horizon 2020 EINFRA-5, grant No. 676598). We also thank the AiiDA team for
their help.

<p align="center">
<img src="docs/images/funding.png" width="500">
</p>

