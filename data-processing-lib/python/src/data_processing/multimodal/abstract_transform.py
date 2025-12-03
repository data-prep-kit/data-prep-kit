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

import time


from argparse import ArgumentParser, Namespace
from typing import Any

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration


from data_processing.multimodal.util import Schema, JsonUtils
from data_processing.utils import CLIArgumentProvider, TransformUtils

batch_size_key = "batch_size"
batch_size_default = 32

class AbstractMultimodalTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]):
        """
        """
        super().__init__(config)
        from data_processing.utils import get_dpk_logger
        self.batch_size = config.get(batch_size_key,batch_size_default)
        self.logger = get_dpk_logger()

    def transform_binary(self, file_name: str, byte_array: bytes) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        '''
        Override to enable polars to parse the byte_array into a Table.
        '''
        table = JsonUtils.get_table_from_bytes(byte_array)
        del byte_array
        tables, metadata = self.transform(table,file_name)
        return self._check_and_convert_tables(tables, metadata)


    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        """
        self.logger.info(f"Begin transforming table with {table.num_rows} from file {file_name}")
        # columns = table.select(["image_bins", "orig_image_fpaths"])
        # images = columns[0]
        # paths = columns[1]
        # for i in range(len(images)):
        #     print(f"{len(images[i])=}, {len(paths[i])}, {paths[i]}")

        # table = table.take([796,797,798]) ## debugging selected rows

        # A list of list of images, each list of images from a single row.
        # One list for each row in the table.
        list_of_image_lists, list_of_paths_lists = JsonUtils.get_image_lists(table)
        assert len(list_of_image_lists) == len(list_of_paths_lists)
        assert len(list_of_image_lists) == table.num_rows

        self.logger.info(f"Begin transforming {len(list_of_image_lists)} rows from file {file_name}")

        # Get the annotations for each row of images.
        list_of_image_annotations, row_indexes_with_errors = self.__annotate_nested_images(list_of_image_lists, list_of_paths_lists)
        assert len(list_of_image_annotations) == len(list_of_image_lists)

        # Accumulate the batched annotations as lists, which will be added later as new columns in the table.
        annotations = {}    # A dictionary of column names mapped to list/rows of values.
        self.logger.info(f"Begin annotating file {file_name}")
        for ia in list_of_image_annotations:
            self.__append_annotations(annotations, ia)
        self.logger.info(f"Done annotating file {file_name}")
        # Done with all batches

        # Append the dictionary of columns
        for key, value in annotations.items():
            table = TransformUtils.add_column(table,key, value)

        # Remove the rows with any images that failed to generated annotations.
        table = self.__remove_rows_with_errors(table, row_indexes_with_errors)

        self.logger.info(f"Done transforming {len(list_of_image_lists)} rows from file {file_name}")
        return [table], {"removed-row-count": len(row_indexes_with_errors)}

    def __remove_rows_with_errors(self, table:pa.Table, row_indexes_with_errors:list[int]) -> pa.Table:
        if len(row_indexes_with_errors) == 0:
            return table

        to_take = []
        for index in range(table.num_rows):
            if index not in row_indexes_with_errors:
                to_take.append(index)
        table = table.take(to_take)
        return table

    def __apply_dummy_annotations(self, image_annotation_list:list[dict[str,Any]], dummy_indexes:list[int],
                                  dummy_annotation:dict):
        """
        Replace all annotations at the given dummy_indexes with the dummy_annotation.
        Yes, there is probably a more pythonic way to do this :).
        """
        for index in dummy_indexes:
            image_annotation_list[index] = dummy_annotation
        return image_annotation_list

    def __annotate_nested_images(self, images:list[list[bytes]], paths:list[list[str]]) -> tuple[dict[str,Any],list[int]]:
        """
        Annotate the list of list of images, merging annotations when a list element contains multiple images.
        Return:
            1) the list of dictionaries of annotations, 1:1 with input list
            2) indexes of elements of the input list on which a failure to create annotations was encountered
                for any i of images[i][j]
        """
        # Flatten the images into a list[bytes], keeping track of the original sizes of the nested lists.
        denested_image_list, list_sizes = self.__de_nest_list(images)
        denested_path_list, path_list_sizes = self.__de_nest_list(paths)
        assert path_list_sizes == list_sizes

        # Let the sub-class annotation these in bulk.
        list_of_image_annotations = self._annotate_images(denested_image_list, denested_path_list)
        assert len(denested_image_list) == len(list_of_image_annotations)

        # Merge annotations as necessary across 1 or more images to produce a list of annotations
        # the same length as the input images list.
        annotations, row_indexes_with_errors = self.__align_de_nested_annotations(list_of_image_annotations,
                                                                                  list_sizes)
        assert len(annotations) == len(images)

        return annotations, row_indexes_with_errors

    def __align_de_nested_annotations(self, annotation_list:list[dict], nested_sizes:list[int]) -> list[dict]:
        """
        Takes a list of annotations for the list of images and sizes produced from __de_nest_list(images).
        This then merges and inserts annotations (from across 0 or more images within a list[bytes]), to produce
        a list of annotations that is the same length as the original list[list[bytes]].  To do that it needs
        to merge annotations when the length list[bytes] is greater than 1 (i.e. the row contained more than
        1 image). And insert dummy annotations when the list of images was of 0 length. It uses the input
        nested_sizes, containing the sizes of the original list[bytes], to merge/insert/align
        the list of annotations that is then in 1:1 correspondence with each list[bytes] in
        the list[list[bytes]].  Done in the sub-class
            1 - Merging annotation dictionaries across multiple images
            2 - defining annotations for 0-length lists of images
        Return:
            1) list: a list of length equal to the list of nested_sizes.  Each element contains a dictionary
            of annotations, merged as necessary, for each list[bytes] in a given row.
            2) list of integer indices of the ROWs that had 1 or more errors generating the annotations for
                any of the images in a row.
        """
        annotation_index = 0
        merged_annotations = []
        row_indexes_with_errors = []
        dummy_annotations = self._get_dummy_annotations()
        assert dummy_annotations is not None, "Dummy annotations is None"
        annotation_key_count = len(dummy_annotations)
        assert annotation_key_count != 0, "Dummy annotations has no keys"

        row_index = 0
        for num_images_in_row in nested_sizes:  # len(nested_sizes) == table.num_rows
            if num_images_in_row == 0:
                # For rows with 0 images, insert dummy annotations.
                merged = dummy_annotations
            else:
                past_merge_count = 0
                row_error = False
                merged = None
                for image_index in range(num_images_in_row):
                    annotations = annotation_list[annotation_index]
                    if annotations is None: # Error generating annotations for this image.
                        if row_index not in row_indexes_with_errors:
                            row_indexes_with_errors.append(row_index)
                        annotations = dummy_annotations
                        row_error = True
                    if merged is None:
                        merged = annotations
                    elif not row_error:
                        #self.logger.info(f"{row_index=}, {num_images_in_row=}, {image_index=}, {annotation_index=}, {merged=}, {annotations=}")
                        merged = self._merge_annotations(merged, annotations, past_merge_count)
                        assert merged is not None, "Annotation merging resulted in unexpected None value"
                        assert len(merged) == annotation_key_count, f"Merge {merged=} did not produce the same number of keys as dummy annotations {dummy_annotations=}"
                annotation_index += 1
                past_merge_count += 1
            merged_annotations.append(merged)
            row_index += 1

        return merged_annotations, row_indexes_with_errors


    def __de_nest_list(self, items:list[list[Any]]) -> tuple[list[Any], list[int]]:
        """
        Extract all items in the lists contained in the given list into a single list and
        capture the sizes of each of the lists.
        Return: a tuple containing
            list : of all items contained in the lists contained in the given items list
            list : a list of length equal to that of the input list containing the sizes of
                ech of the lists contained in the items list.
        """
        flattened_items = []
        sizes = []
        for item in items:
            for element in item:
                flattened_items.append(element)
            sizes.append(len(item))
        return flattened_items, sizes

    def _annotate_images(self, images:list[bytes], image_paths:list[str]) -> list[dict[str,Any]]:
        """
        Determine a set of annotations for each image.
        Parameters:
            images: a list of bytes as would be read from an image file (e.g., gif, jpg, png, etc).
                As such the bytes may need to be decoded before examination, depending on the implementation.
            image_paths: list of paths/image names in 1:1 correspondence from which each image was read.
        Return: a list of the same length as the input.  Each element of the list is either
            1) a dictionary of key/values that will be appended to the Table as new columns, or
            2) None if there was an error in creating annotations for the image.  In this case the row
                from which the image originated will be dropped from the output table.
            Implementations must always return the same set of keys in the dictionary so that
            the same set of columns are always added to a row.
            Also see _get_dummy_annotations() and _merge_annotations() which must also use/generate
            the same set of keys.
        """
        raise RuntimeError("Sub-class must implement")

    def _merge_annotations(self, merged:dict, addend:dict, past_merge_count:int) -> dict:
        """
        This combines the annotations from multiple images (usually within the same row).
        Either one of merged or addend annotations may be a value returned by _get_dummy_annotations() if
        either
            1) the row did not contain any image or
            2) any 1 of the images in a row encountered an error during annotation and provide None as the
            annotation dictionary for a given image in the list returned by _annotation_images().
        Parameters:
            merged: the running accumulation of merges.  Will never be None.
            addend: the dictionary to merge into the first.  This is expected to have the same keys as
            the first.
            past_merge_count: the number of merges done on the given merged dictionary.  This may be useful
            for merging statistics in the annotations (for example "average HAP score" annotation).

        Return:
            a new dictionary that is a merge of the two dictionaries. Never None.
        """
        raise RuntimeError("Sub-class must implement")

    def _get_dummy_annotations(self):
        """
        Gets the set of annotations that should be applied to a row w/o any images.

        This expects a dummy image to be treated as not containing any relevant content, for example, faces,
        people, HAP, etc.  For example, if a sub-class is providing annotations of the form
            { "face-count" : <int>, "face-confidence" : <float> },
        this method should probably return
            { "face-count" : 0, "face-confidence" : 1 },

        Return: dict, always with the same set of keys as generated by _annatote_images(), never None.
        """
        raise RuntimeError("Sub-class must implement")

    def __append_annotations(self, accumulation:dict, to_append:dict):
        """
        Accumulate the keys from the to_append dictionary into the accumulation dictionary whose
        values are a list accumulated values from past to_append values.
        Keys in the accumulation dictionary are the same as those in the to_append dict.
        Values under the keys of the accumulation dictionary are lists.

        Return: dict, with the same set of keys as in the input and as returned by _annotate_images(), never None.
        """
        # Make sure the keys match
        if len(accumulation) == 0:
            for key, value in to_append.items():
                accumulation[key] = [value]
        elif accumulation.keys() != to_append.keys():
            raise RuntimeError("Set of annotations keys is not consistent")
        else:
            for key, value in to_append.items():
                accumulation[key].append(value)


class AbstractMultimodalTransformConfiguration(TransformConfiguration):

    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self, name:str, transform_class:AbstractMultimodalTransform,remove_from_metadata=[]):
        super().__init__(
            name=name,
            transform_class=transform_class,
            remove_from_metadata=remove_from_metadata
        )
        from data_processing.utils import get_dpk_logger
        self.cli_prefix = name + "_"
        self.logger = get_dpk_logger()

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        """

#        name = self.get_name()
        parser.add_argument(
            f"--{self.cli_prefix}{batch_size_key}",
            type=int,
            default=batch_size_default,
            help="The number of rows in a batch to provided to the annotator"
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, self.cli_prefix, False)
        self.params = self.params | captured
        self.logger.info(f"mm parameters are : {self.params}")
        return True
