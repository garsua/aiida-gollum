# -*- coding: utf-8 -*-
import numpy as np
from aiida.orm.data.parameter import ParameterData
from aiida.parsers.parser import Parser
from aiida.parsers.exceptions import OutputParsingError
from aiida_gollum.calculations.gollum import GollumCalculation

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.12.0"
__contributors__ = "Victor M. Garcia-Suarez"
# Based on the 0.9.0 version of the STM workflow developed by Alberto
# Garcia for the aiida_siesta plugin

standard_output_list = [ 'siesta:FreeE', 'siesta:E_KS',
                         'siesta:Ebs', 'siesta:E_Fermi',
                         'siesta:stot']  ## leave svec for later

class GollumOutputParsingError(OutputParsingError):
     pass

class GollumParser(Parser):
    """
    Parser for the output of a Gollum calculation.
    """
    def __init__(self,calc):
        """
        Initialize the instance of GollumParser
        """
        # check for valid input
        self._check_calc_compatibility(calc)
        super(GollumParser, self).__init__(calc)

    def _check_calc_compatibility(self,calc):
        if not isinstance(calc,GollumCalculation):
            raise GollumOutputParsingError("Input calc must be a GollumCalculation")

    def _get_output_nodes(self, output_path, messages_path):
        """
        Extracts output nodes from the standard output and standard error
        files. (And XML and JSON files)
        """
        from aiida.orm.data.array.trajectory import TrajectoryData
        import re

        result_list = []

        # Add errors
        successful = True
        if messages_path is None:
             errors_list = ['WARNING: No aiida.out file...']
        else:
             successful, errors_list = self.get_errors_from_file(messages_path)

        result_dict = {}
        result_dict["errors"] = errors_list

        # Add warnings
        warnings_list = self.get_warnings_from_file(messages_path)
        result_dict["warnings"] = warnings_list

        # Add outuput data
        output_dict = self.get_output_from_file(output_path)
        result_dict.update(output_dict)
        
        # Add parser info dictionary
        parser_info = {}
        parser_version = 'aiida-0.1.0--gollum-2.0.0'
        parser_info['parser_info'] =\
            'AiiDA Siesta Parser V. {}'.format(parser_version)
        parser_info['parser_warnings'] = []
        parsed_dict = dict(result_dict.items() + parser_info.items())

        output_data = ParameterData(dict=parsed_dict)
        
        link_name = self.get_linkname_outparams()
        result_list.append((link_name,output_data))

        return successful, result_list

    def parse_with_retrieved(self,retrieved):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        
        from aiida.common.exceptions import InvalidOperation
        import os

        output_path = None
        messages_path  = None
        try:
            output_path, messages_path = self._fetch_output_files(retrieved)
        except InvalidOperation:
            raise
        except IOError as e:
            self.logger.error(e.message)
            return False, ()

        if output_path is None and messages_path is None:
            self.logger.error("No output files found")
            return False, ()

        successful, out_nodes = self._get_output_nodes(output_path, messages_path)
        
        return successful, out_nodes

    def _fetch_output_files(self, retrieved):
        """
        Checks the output folder for standard output and standard error
        files, returns their absolute paths on success.

        :param retrieved: A dictionary of retrieved nodes, as obtained from the
          parser.
        """
        from aiida.common.datastructures import calc_states
        from aiida.common.exceptions import InvalidOperation
        import os

        # Check that the retrieved folder is there
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
        except KeyError:
            raise IOError("No retrieved folder found")

        list_of_files = out_folder.get_folder_list()

        output_path = None
        messages_path  = None

        if self._calc._DEFAULT_OUTPUT_FILE in list_of_files:
            output_path = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_OUTPUT_FILE )
        if self._calc._DEFAULT_MESSAGES_FILE in list_of_files:
            messages_path  = os.path.join( out_folder.get_abs_path('.'),
                                        self._calc._DEFAULT_MESSAGES_FILE )

        print output_path, messages_path
        return output_path, messages_path

    def get_output_from_file(self,output_path):
     """
     Generates a list of variables from the 'aiida.out' file.

     :param output_path: 

     Returns a list of strings.
     """
     f=open(output_path)
     lines=f.read().split('\n')   # There will be a final '' element

     import re

     # Find data
     output_dict = {}
     for line in lines:
          if re.match('^.*Version.*$',line):
               output_dict['gollum:version'] = line.strip()
          if re.match('^.*LIBRARY.*$',line):
               output_dict['ld_library_path'] = line.strip()
          if re.match('^.*Start of run.*$',line):
               output_dict['start_of_run'] = ' '.join(line.split()[-2:])
          if re.match('^.*Elapsed time.*$',line):
               output_dict['total_time'] = line.split()[-2]
     
     return output_dict

    def get_errors_from_file(self,messages_path):
     """
     Generates a list of errors from the 'aiida.out' file.

     :param messages_path: 

     Returns a boolean indicating success (True) or failure (False)
     and a list of strings.
     """
     f=open(messages_path)
     lines=f.read().split('\n')   # There will be a final '' element

     import re
     
     # Search for 'Error' messages, log them, and return immediately
     lineerror = []
     there_are_fatals = False 
     for line in lines:
         if re.match('^.*Error.*$',line):
             self.logger.error(line)
             lineerror.append(line)
             there_are_fatals = True
               
     if there_are_fatals:
         lineeror.append(lines[-1])
         return False, lineerror

     # Make sure that the job did finish (and was not interrupted
     # externally)

     normal_end = False
     for line in lines:
          if re.match('^.*THE END.*$',line):
               normal_end = True
               
     if normal_end == False:
          lines[-1] = 'FATAL: ABNORMAL_EXTERNAL_TERMINATION'
          self.logger.error("Calculation interrupted externally")
          return False, lines[-2:] # Return also last line of the file

     return True, lineerror

    def get_warnings_from_file(self,messages_path):
     """
     Generates a list of errors from the 'aiida.out' file.

     :param messages_path: 

     Returns a boolean indicating success (True) or failure (False)
     and a list of strings.
     """
     f=open(messages_path)
     lines=f.read().split('\n')   # There will be a final '' element

     import re

     # Find warnings
     linewarning = []
     for line in lines:
          if re.match('^.*in =/.*$',line):
               linewarning.append(line)
     
     return linewarning

    def get_linkname_outstructure(self):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'

    def get_linkname_outarray(self):
        """                                                                     
        Returns the name of the link to the output_array                        
        In Siesta, Node exists to hold the final forces and stress,
        pending the implementation of trajectory data.
        """
        return 'output_array'

    def get_linkname_bandsarray(self):
        """                                                                     
        Returns the name of the link to the bands_array                        
        In Siesta, Node exists to hold the bands,
        pending the implementation of trajectory data.
        """
        return 'bands_array'

    def get_linkname_bandsparameters(self):
        """
        Returns the name of the link to the bands_path.
        X-axis data for bands. Maybe should use ArrayData (db-integrity?).
        """
        return 'bands_parameters'
