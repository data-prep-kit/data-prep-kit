# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import argparse
import ast
from typing import Union
import importlib
import copy

from data_processing.data_access import (
    DataAccess,
    DataAccessFactoryBase
)
from data_processing.utils import ParamsUtils, str2bool


class DataAccessFactory(DataAccessFactoryBase):
    """
    This class is accepting Data Access parameters, validates them and instantiates an appropriate
    Data Access class based on these parameters.
    This class has to be serializable, so that we can pass it to the actors
    """
    default_class = 'DataAccessLocal'
    default_package = 'data_processing.data_access'

    s3_class = 'DataAccessS3'

    def __init__(self, cli_arg_prefix: str = "data_", enable_data_navigation: bool = True):
        """
        Create the factory to parse a set of args that will then define the type of DataAccess object
        to be created by the create_data_access() method.
        :param cli_arg_prefix:  if provided, this will be prepended to all the CLI arguments names.
               Make sure it ends with _
        :param enable_data_navigation: if true enables CLI args and configuration for input/output paths,
            data sets, checkpointing, files to use, sampling and max files.
        This allows the creation of transform-specific (or other) DataAccess instances based on the
        transform-specific prefix (e.g. bl_ for blocklist transform).  The resulting keys returned
        in get_input_params() will include the prefix.  The underlying AST or other values of those
        keys is not effected by the prefix.
        """
        super().__init__(cli_arg_prefix=cli_arg_prefix)
        self.config= None
        self.enable_data_navigation = enable_data_navigation
        self.data_access=None
        self.data_access_class=self.default_class
        self.data_access_package=self.default_package
        

    def add_input_params(self, parser: argparse.ArgumentParser) -> None:
        """
        Define data access specific parameters
        The set of parameters here is a superset of parameters required for all
        supported data access. The user only needs to specify the ones that he needs
        the rest will have the default values
        This might need to be extended if new data access implementation is added
        :param parser: parser
        :return: None
        """

        self.logger.debug(f"{__name__} - add_input_param: self.cli_arg_prefix={self.cli_arg_prefix} self.enable_data_navigation={self.enable_data_navigation}")

        if self.enable_data_navigation:
            self.__add_data_navigation_params(parser)
            

    def __add_data_navigation_params(self, parser):

        help_example_dict = {
            "input_folder": [
                "s3-path/your-input-bucket",
                "Path to input folder of files to be processed",
            ],
            "output_folder": [
                "s3-path/your-output-bucket",
                "Path to output folder of processed files",
            ],
            "da_class": [
                "package[.module].classname",
                "Class name that implements the desired data access",
            ],
            "kwargs": [
                "class-defined-attributes",
                "Attributes that are required by the data access class referenced in da_class",
            ],
        }
        parser.add_argument(
            f"--{self.cli_arg_prefix}s3_config",
            type=ast.literal_eval,
            default=None,
            help="AST string containing input/output paths.\n" + ParamsUtils.get_ast_help_text(help_example_dict),
        )

        parser.add_argument(
            f"--{self.cli_arg_prefix}lh_config",
            type=ast.literal_eval,
            default=None,
            help="AST string containing input/output using lakehouse.\n" + ParamsUtils.get_ast_help_text(help_example_dict),
        )

        parser.add_argument(
            f"--{self.cli_arg_prefix}data_config",
            type=ast.literal_eval,
            default=None,
            help="AST string containing input/output for custom defined data access class.\n" + ParamsUtils.get_ast_help_text(help_example_dict),
        )

        help_example_dict = {
            "input_folder": ["./input", "Path to input folder of files to be processed"],
            "output_folder": ["/tmp/output", "Path to output folder of processed files"],
        }
        parser.add_argument(
            f"--{self.cli_arg_prefix}local_config",
            type=ast.literal_eval,
            default=None,
            help="ast string containing input/output folders using local fs.\n"
            + ParamsUtils.get_ast_help_text(help_example_dict),
        )
        parser.add_argument(
            f"--{self.cli_arg_prefix}max_files", type=int, default=-1, help="Max amount of files to process"
        )
        parser.add_argument(
            f"--{self.cli_arg_prefix}checkpointing",
            type=lambda x: bool(str2bool(x)),
            default=False,
            help="checkpointing flag",
        )
        # In the case of binary files, the resulting extension can be different from the source extension
        # The checkpointing extension is defined here. If multiple files (extensions) are produced from the
        # source files, only the leading one is required here
        parser.add_argument(
            f"--{self.cli_arg_prefix}files_to_checkpoint",
            type=ast.literal_eval,
            default=ast.literal_eval("['.parquet']"),
            help="list of file extensions to choose for checkpointing.",
        )
        parser.add_argument(
            f"--{self.cli_arg_prefix}data_sets",
            type=ast.literal_eval,
            default=None,
            help="List of sub-directories of input directory to use for input. For example, ['dir1', 'dir2']",
        )
        parser.add_argument(
            f"--{self.cli_arg_prefix}files_to_use",
            type=ast.literal_eval,
            default=ast.literal_eval("['.parquet']"),
            help="list of file extensions to choose for input.",
        )
        parser.add_argument(
            f"--{self.cli_arg_prefix}num_samples", type=int, default=-1, help="number of random input files to process"
        )

    def apply_input_params(self, args: Union[dict, argparse.Namespace]) -> bool:
        """
        Validate data access specific parameters
        This might need to be extended if new data access implementation is added
        :param args: user defined arguments
        :return: None
        """
        import os
        self.logger.debug(f"list of Env. Variables for this prefix {self.cli_arg_prefix}")
        list= [x for x,_ in os.environ.items() if x.startswith(self.cli_arg_prefix)]
        self.logger.debug(f"{list}")
        if isinstance(args, argparse.Namespace):
            arg_dict = vars(args)
        elif isinstance(args, dict):
            arg_dict = args
        else:
            raise ValueError("args must be Namespace or dictionary")

        checkpointing = arg_dict.get(f"{self.cli_arg_prefix}checkpointing", False)
        max_files = arg_dict.get(f"{self.cli_arg_prefix}max_files", -1)
        data_sets = arg_dict.get(f"{self.cli_arg_prefix}data_sets", None)
        n_samples = arg_dict.get(f"{self.cli_arg_prefix}num_samples", -1)
        files_to_use = arg_dict.get(f"{self.cli_arg_prefix}files_to_use", [".parquet"])
        files_to_checkpoint = arg_dict.get(f"{self.cli_arg_prefix}files_to_checkpoint", [".parquet"])

        #########################################################################
        # Set Data Access Class defaults to used based on provided cli parameters
        ## The use of s3_config and local_config will be depricated over time
        ## For now, allow backward compatibility until we adapt all the tansforms
        ## to use the new logic and specify their prefix configuration as needed
        if (arg_dict.get(f"{self.cli_arg_prefix}s3_config")):
            self.data_access_class='DataAccessS3'
        elif (arg_dict.get(f"{self.cli_arg_prefix}local_config")):
            self.data_access_class='DataAccessLocal'
        elif (arg_dict.get(f"data_s3_config")):
            self.data_access_class='DataAccessS3'
        else:
            self.data_access_class=self.default_class
        self.data_access_package=self.default_package


        ################################################################
        # check which configuration (S3 or Local) is specified
        # For backward compatibility, we are allowing s3_config, local_config, lh_config, 
        # In the next release, only data_config will be allowed
        defined_args=[x for x in arg_dict.keys() if arg_dict.get(x, None) is not None]
        config_args=[f"{self.cli_arg_prefix}s3_config", f"{self.cli_arg_prefix}local_config",
                        f"{self.cli_arg_prefix}lh_config",f"{self.cli_arg_prefix}config"]
        provided_configs=[x for x in defined_args if x in config_args]

        
        #####################################################################
        ## For now, cannot have more than one configuration
        ## Configuration can also specify a class name to use for data access
        if len(provided_configs) > 1:
            self.logger.error(
                f"data factory {self.cli_arg_prefix} cannnot specify more than one data configuration"
                f"{provided_configs} configurations specified, but only one configuration expected"
            )
            return False
        elif len(provided_configs) == 0:
            self.logger.info(
                f"data factory {self.cli_arg_prefix} " f"Missing local configuration"
            )
        else:
            self.config = arg_dict.get(provided_configs[0])
            if 'prefix' not in self.config:
                self.config['prefix']=self.cli_arg_prefix
            logging_config = copy.deepcopy(self.config)
            logging_config.pop('access_key', None)
            logging_config.pop('secret_key', None)
            self.logger.debug(
            f"data factory {self.cli_arg_prefix} "
            f"data configuration used: {logging_config}"
            )
            del logging_config
            ##########################################################################
            ## Data Access Class can be specified as par of the data configuration dictionary
            # expect da_class string to be in the form: package[.submodule].classname
            da_class=self.config.get('da_class')
            if da_class:
                dotNdx=da_class.rfind(".")
                if dotNdx <= 0:
                    self.logger.error(
                        f"data factory {self.cli_arg_prefix} configuration must specify the data access class and its package name"
                        f"{self.config['da']} must have the following format: packagename.classname"
                    )
                    self.data_access_package=None
                    self.data_access_class=da_class
                else:
                    self.data_access_class=da_class[dotNdx+1:]
                    self.data_access_package=da_class[:dotNdx]
                self.logger.info(f"Using Package: {self.data_access_package} and class: {self.data_access_class}")

        # Check whether both max_files and number samples are defined
        self.logger.info(f"data factory {self.cli_arg_prefix} max_files {max_files}, n_sample {n_samples}")
        if max_files > 0 and n_samples > 0:
            self.logger.error(
                f"data factory {self.cli_arg_prefix} "
                f"Both max files {max_files} and random samples {n_samples} are defined. Only one allowed at a time"
            )
            return False
        self.checkpointing = checkpointing
        self.max_files = max_files
        self.n_samples = n_samples
        self.files_to_use = files_to_use
        self.files_to_checkpoint = files_to_checkpoint
        self.dsets = data_sets
        if data_sets is None or len(data_sets) < 1:
            self.logger.info(
                f"data factory {self.cli_arg_prefix} "
                f"Not using data sets, checkpointing {checkpointing}, max files {max_files}, "
                f"random samples {n_samples}, files to use {files_to_use}, files to checkpoint {files_to_checkpoint}"
            )
        else:
            self.logger.info(
                f"data factory {self.cli_arg_prefix} "
                f"Using data sets {self.dsets}, checkpointing {checkpointing}, max files {max_files}, "
                f"random samples {n_samples}, files to use {files_to_use}, files to checkpoint {files_to_checkpoint}"
            )

        try:
            if self.data_access_package and self.data_access_package != '':
                ## For now, this is always the case where we set a default
                self.data_access=getattr(importlib.import_module(self.data_access_package), self.data_access_class)
            else:
                ## In the future, we may want to allow global scope packages
                self.data_access=globals().get(self.data_access_class)
        except ImportError:
            self.logger.error(f"Failed to import package {self.data_access_package}")
            return False
        except AttributeError:
            self.logger.error(f"Class {self.data_access_class} {self.data_access_package}  Not found")
            return False
            # At this point, we could call the class validation method if we want to retain the same logic as before
        if not self.data_access:
            self.logger.error(f"Failed to import package {self.data_access_package}.{self.data_access_class}")
            return False
        self.logger.info(
                f"data factory {self.cli_arg_prefix} "
                f"Data Access:  {self.data_access_class}"
            )
        if self.enable_data_navigation:
            if not self.data_access.validate_config(self.config, self.cli_arg_prefix):
                return False
        return True

    def create_data_access(self) -> DataAccess:
        """
        Create data access based on the parameters
        :return: corresponding data access class
        """
        try:
            if self.data_access is None:
                ##### MT
                ## A number of transform assumes they can call this method directly without
                ## any pre-configration to get a local data access class without any validation
                self.data_access=getattr(importlib.import_module(self.data_access_package), self.data_access_class)
            return self.data_access(
                config=self.config,
                d_sets=self.dsets,
                checkpoint=self.checkpointing,
                m_files=self.max_files,
                n_samples=self.n_samples,
                files_to_use=self.files_to_use,
                files_to_checkpoint=self.files_to_checkpoint
            )
        except ImportError:
            self.logger.error(f"Failed to import package {self.data_access_package}")
            raise
        except AttributeError:
            self.logger.error(f"Class {self.data_access_class}  Not found")
            raise
        except Exception:
            self.logger.error(f"Failed to create data access instance {self.data_access_package}.{self.data_access_class}")
            raise
   
