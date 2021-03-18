# -*- coding: utf-8 -*-
import os

from aiida.common.constants import elements
from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.singlefile import SinglefileData

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.12.0"
__contributors__ = "Victor M. Garcia-Suarez"

class GollumCalculation(JobCalculation):
    """
    Plugin for the Gollum program which computes the electronic transport
    properties from a DFT or tight-binding calculation.
    """
    _gollum_plugin_version = 'aiida-0.12.0--gollum-2.1.0'

    def _init_internal_params(self):
        super(GollumCalculation, self)._init_internal_params()

        # Default Gollum output parser provided by AiiDA
        self._default_parser = "gollum.parser"

        # Default input and output files
        self._DEFAULT_INPUT_FILE = 'input'
        self._DEFAULT_OUTPUT_FILE = 'aiida.out'
        self._DEFAULT_MESSAGES_FILE = 'aiida.out'
        self._DEFAULT_OC_FILE = 'Open_channels_per_spin1.gdat'
        self._DEFAULT_OU_FILE = 'Open_channels_up1.gdat'
        self._DEFAULT_OD_FILE = 'Open_channels_down1.gdat'
        self._DEFAULT_TT_FILE = 'T_per_spin2.gdat'
        self._DEFAULT_TU_FILE = 'T_up2.gdat'
        self._DEFAULT_TD_FILE = 'T_down2.gdat'

        self._GFILES_SUBFOLDER = './'
        self._OUTPUT_SUBFOLDER = './'
        self._PREFIX = 'aiida'
        self._INPUT_FILE_NAME = 'input'
        self._OUTPUT_FILE_NAME = 'aiida.out'
        self._MESSAGES_FILE_NAME = 'aiida.out'
        self._OC_FILE_NAME = 'Open_channels_per_spin1.gdat'
        self._OU_FILE_NAME = 'Open_channels_up1.gdat'
        self._OD_FILE_NAME = 'Open_channels_down1.gdat'
        self._TT_FILE_NAME = 'T_per_spin2.gdat'
        self._TU_FILE_NAME = 'T_up2.gdat'
        self._TD_FILE_NAME = 'T_down2.gdat'

        # in restarts, it will copy from the parent the following
        self._restart_copy_from = os.path.join(self._OUTPUT_SUBFOLDER, 'partial.mat')

        # in restarts, it will copy the previous folder in the following one
        self._restart_copy_to = self._OUTPUT_SUBFOLDER

    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        retdict = JobCalculation._use_methods

        retdict["settings"] = {
            'valid_types': ParameterData,
            'additional_parameter': None,
            'linkname': 'settings',
            'docstring': "Use an additional node for special settings",
        }
        retdict["parameters"] = {
            'valid_types': ParameterData,
            'additional_parameter': None,
            'linkname': 'parameters',
            'docstring': ("Use a node that specifies the input parameters "
                          "for the namelists"),
        }
        retdict["parent_folder"] = {
            'valid_types': RemoteData,
            'additional_parameter': None,
            'linkname': 'parent_calc_folder',
            'docstring': ("Use a remote folder as parent folder (for "
                          "restarts and similar"),
        }
        retdict['singlefile'] = {
            'valid_types': SinglefileData,
            'additional_parameter': None,
            'linkname': 'singlefile',
            'docstring': ("Some file that is needed to run the calculation"),
        }
        return retdict

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param tempfolder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        :param inputdict: a dictionary with the input nodes, as they would
                be returned by get_inputdata_dict (without the Code!)
        """

        local_copy_list = []
        remote_copy_list = []

        # Process the settings dictionary first
        # Settings can be undefined, and defaults to an empty dictionary
        settings = inputdict.pop(self.get_linkname('settings'), None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings, ParameterData):
                raise InputValidationError(
                    "settings, if specified, must be of "
                    "type ParameterData")

            # Settings converted to UPPERCASE to standardize the usage and
            # avoid ambiguities
            settings_dict = _uppercase_dict(
                settings.get_dict(), dict_name='settings')

        # Parameters
        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this "
                                       "calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type "
                                       "ParameterData")

        # Singlefile
        singlefile = inputdict.pop(self.get_linkname('singlefile'), None)
        if singlefile is not None:
            if not isinstance(singlefile, SinglefileData):
                raise InputValidationError("singlefile, if specified,"
                                           "must be of type SinglefileData")

        # Parent calculation folder
        parent_calc_folder = inputdict.pop(
            self.get_linkname('parent_folder'), None)
        if parent_calc_folder is not None:
            if not isinstance(parent_calc_folder, RemoteData):
                raise InputValidationError("parent_calc_folder, if specified,"
                                           "must be of type RemoteData")

        # Code
        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError(
                "No code specified for this calculation")

        # Here, there should be no more input data
        if inputdict:
            raise InputValidationError(
                "The following input data nodes are "
                "unrecognized: {}".format(inputdict.keys()))

        ##############################
        # END OF INITIAL INPUT CHECK #
        ##############################

        input_params = parameters.get_dict()

        # = Preparation of input data ============================

        input_filename = tempfolder.get_abs_path(self._INPUT_FILE_NAME)

        with open(input_filename, 'w') as infile:
            # Here print keys and values to file

            for k, v in sorted(input_params.iteritems()):
                infile.write(get_input_data_text(k, v))

        # = Additional files =====================================

        # Create the subfolder that will contain Gollum files
        tempfolder.get_subfolder(self._GFILES_SUBFOLDER, create=True)
        # Create the subfolder with the output data
        tempfolder.get_subfolder(self._OUTPUT_SUBFOLDER, create=True)

        if singlefile is not None:
            lfile=singlefile.get_file_abs_path().split("path/",1)[1]
            local_copy_list.append((singlefile.get_file_abs_path(),
                os.path.join(self._GFILES_SUBFOLDER, lfile)))
            
        settings_local_copy_list = settings_dict.pop(
                'ADDITIONAL_LOCAL_COPY_LIST', [])
        if settings_local_copy_list is not None:
            for k in settings_local_copy_list:
                lfile=k.split("/")
                lf='./'+lfile[len(lfile)-1]
                local_copy_list.append((unicode(k),unicode(lf)))

        # = Parent calculation folder ============================

        # The presence of a 'parent_calc_folder' input node signals
        # that we want to get something from there, as indicated in the
        # self._restart_copy_from attribute. In Gollum, partial.mat
        #
        # It will be copied to the current calculation's working folder

        if parent_calc_folder is not None:
            remote_copy_list.append(
                (parent_calc_folder.get_computer().uuid, os.path.join(
                    parent_calc_folder.get_remote_path(),
                    self._restart_copy_from), self._restart_copy_to))

        # = Calculation information and parameters ===============

        calcinfo = CalcInfo()

        calcinfo.uuid = self.uuid

        cmdline_params = settings_dict.pop('CMDLINE', [])

        if cmdline_params:
            calcinfo.cmdline_params = list(cmdline_params)
        calcinfo.local_copy_list = local_copy_list
        calcinfo.remote_copy_list = remote_copy_list

        calcinfo.stdin_name = self._INPUT_FILE_NAME
        calcinfo.stdout_name = self._OUTPUT_FILE_NAME
        calcinfo.messages_name = self._MESSAGES_FILE_NAME
        calcinfo.oc_name = self._OC_FILE_NAME
        calcinfo.ou_name = self._OU_FILE_NAME
        calcinfo.od_name = self._OD_FILE_NAME
        calcinfo.tt_name = self._TT_FILE_NAME
        calcinfo.tu_name = self._TU_FILE_NAME
        calcinfo.td_name = self._TD_FILE_NAME

        # = Code information object ==============================

        codeinfo = CodeInfo()
        #codeinfo.cmdline_params = list(cmdline_params)
        codeinfo.cmdline_params = [cmdline_params]
        #codeinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.messages_name = self._MESSAGES_FILE_NAME
        codeinfo.oc_name = self._OC_FILE_NAME
        codeinfo.ou_name = self._OU_FILE_NAME
        codeinfo.od_name = self._OD_FILE_NAME
        codeinfo.tt_name = self._TT_FILE_NAME
        codeinfo.tu_name = self._TU_FILE_NAME
        codeinfo.td_name = self._TD_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]

        # = Retrieve files =======================================

        # Retrieve by default: the output file
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append(self._MESSAGES_FILE_NAME)
        calcinfo.retrieve_list.append(self._OC_FILE_NAME)
        calcinfo.retrieve_list.append(self._OU_FILE_NAME)
        calcinfo.retrieve_list.append(self._OD_FILE_NAME)
        calcinfo.retrieve_list.append(self._TT_FILE_NAME)
        calcinfo.retrieve_list.append(self._TU_FILE_NAME)
        calcinfo.retrieve_list.append(self._TD_FILE_NAME)

        # Any other files specified in the settings dictionary
        settings_retrieve_list = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST',
                                                   [])
        calcinfo.retrieve_list += settings_retrieve_list

        # = Copy additional remote files =========================

        # Additional remote copy list for files like the EM or leads 
        settings_remote_copy_list = settings_dict.pop(
                'ADDITIONAL_REMOTE_COPY_LIST', [])
        calcinfo.remote_copy_list += settings_remote_copy_list

        if settings_remote_copy_list and parent_calc_folder is None:
            raise ValueError("The definition of a parent calculation folder "
                             "is also needed when there is a remote copy list")
        for src_relative, dest_relative in settings_remote_copy_list:
            calcinfo.remote_copy_list.append(
                [parent_calc_folder.get_computer().uuid,
                src_relative,dest_relative])

        return calcinfo

    def _set_parent_remotedata(self, remotedata):
        """
        Used to set a parent remotefolder in the restart of ph.
        """
        from aiida.common.exceptions import ValidationError

        if not isinstance(remotedata, RemoteData):
            raise ValueError('remotedata must be a RemoteData')

        # Complain if another remotedata is already found
        input_remote = self.get_inputs(node_type=RemoteData)
        if input_remote:
            raise ValidationError(
                "Cannot set several parent calculation to a "
                "{} calculation".format(self.__class__.__name__))

        self.use_parent_folder(remotedata)


def get_input_data_text(key, val, mapping=None):
    """
    Given a key and a value, return a string (possibly multiline for arrays)
    with the text to be added to the input file.

    :param key: the flag name
    :param val: the flag value. If it is an array, a line for each element
            is produced, with variable indexing starting from 1.
    :param mapping: Optional parameter, must be provided if val is a dictionary.
            It maps each key of the 'val' dictionary to the corresponding
            list index. For instance, if ``key='magn'``,
            ``val = {'Fe': 0.1, 'O': 0.2}`` and ``mapping = {'Fe': 2, 'O': 1}``,
            this function will return the two lines ``magn(1) = 0.2`` and
            ``magn(2) = 0.1``. This parameter is ignored if 'val'
            is not a dictionary.
    """
    # Check first the dictionary, because it would also match
    # hasattr(__iter__)
    if isinstance(val, dict):
        if mapping is None:
            raise ValueError("If 'val' is a dictionary, you must provide also "
                             "the 'mapping' parameter")

        list_of_strings = []
        for elemk, itemval in val.iteritems():
            try:
                idx = mapping[elemk]
            except KeyError:
                raise ValueError("Unable to find the key '{}' in the mapping "
                                 "dictionary".format(elemk))

            list_of_strings.append((idx, "  {0}({2}) = {1}\n".format(
                key, itemval, idx)))

        # Resort to remove the index from the first column, finally to
        # join the strings
        list_of_strings = zip(*sorted(list_of_strings))[1]
        return "".join(list_of_strings)
    elif hasattr(val, '__iter__'):
        # A list/array/tuple of values
        list_of_strings = [
            "{0}({2})  {1}\n".format(key, itemval, idx + 1)
            for idx, itemval in enumerate(val)
        ]
        return "".join(list_of_strings)
    else:
        # Numerical block
        if key[:6] == 'NBlock':
            nrows = val.count("\n")
            line1 = val.splitlines()[1]
            ncolumns = len(line1.split())
            bname = key.split()[1]
            b1 = "# name: {0}\n# type: matrix\n# rows: {1}\n# columns: "\
                "{2}".format(bname,nrows,ncolumns)
            for i in range(nrows):
                b1 += "\n {0}".format(val.splitlines()[i+1].lstrip())
            return b1 + "\n"
        # String block
        elif key[:6] == 'SBlock':
            nrows = val.count("\n")
            bname = key.split()[1]
            b1 = "# name: {0}\n# type: string\n# rows: {1}"\
                .format(bname,nrows)
            for i in range(nrows):
                b1 += "\n {0}".format(val.splitlines()[i+1].lstrip())
            return b1 + "\n"
        # Atomic block
        elif key == "atom":
            nrows = val.count("\n")
            b1='';l=0
            for i in range(nrows):
                line = val.splitlines()[i+1]
                a0 = line.split()[0]
                a1 = line.split()[1]
                a2 = line.split()[2]
                if int(a0) == 1:
                    i1=int(a1);i2=0;i3=-1
                elif int(a0) == 0:
                    i1=0;i2=1;i3=1
                else:
                    i1=1;i2=int(a1)+1;i3=1
                for k in range(i1,i2,i3):
                    for j in range(1,int(a2)+1):
                        l+=1
                        b1 += " {0} {1} {2} {3} 0.00 0.00\n"\
                            .format(l,a0,k,a0)
            return "# name: {0}\n# type: matrix\n# rows: {1}\n# columns: 6\n"\
                .format(key,l) + b1
        # Scalars and strings
        else:
            try:
                int(val)
                typd = 'scalar'
                b1 = "# name: {0}\n# type: {1}\n {2}"\
                    .format(key,typd,val)
            except:
                typd = 'string'
                b1 = "# name: {0}\n# type: {1}\n# rows: 1\n {2}"\
                    .format(key,typd,val)
            return b1 + "\n"


def _uppercase_dict(d, dict_name):
    from collections import Counter

    if isinstance(d, dict):
        new_dict = dict((str(k).upper(), v) for k, v in d.iteritems())
        if len(new_dict) != len(d):

            num_items = Counter(str(k).upper() for k in d.keys())
            double_keys = ",".join([k for k, v in num_items if v > 1])
            raise InputValidationError(
                "Inside the dictionary '{}' there are the following keys that "
                "are repeated more than once when compared case-insensitively: "
                "{}."
                "This is not allowed.".format(dict_name, double_keys))
        return new_dict
    else:
        raise TypeError(
            "_lowercase_dict accepts only dictionaries as argument")
