Installation
++++++++++++

It could be useful to create and switch to a new python virtual
environment before the installation to avoid conflicts with
third-party packages.

Install the plugin by executing, from the top level of the plugin
directory:

::

    pip install -e .

As a pre-requisite, this will install an appropriate version of the
aiida_core python framework.

.. important:: Next, do not forget to run the following command

::

   reentry scan -r aiida

