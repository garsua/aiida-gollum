Installation
++++++++++++

It could be useful first to create and switch to a new python
virtual environment before the installation to avoid conflicts with
third-party packages.

Install the plugin by executing, from the top level of the plugin
directory:

::

    pip install -e .

As a pre-requisite, this will install an appropriate version of the
aiida_core python framework.

.. important:: Next, do not forget to run the following command to make sure all other plugins are discovered and registered

::

   reentry scan -r aiida

