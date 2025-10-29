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

import sys
from collections import defaultdict
import pyarrow as pa
import json

from PIL import Image

# See https://stackoverflow.com/questions/51152059/pillow-in-python-wont-let-me-open-image-exceeds-limit
Image.MAX_IMAGE_PIXELS = None

import io
import os
import pyarrow as pa

from data_processing.data_access.data_access import DataAccess
from data_processing.utils import TransformUtils


class Schema:
    ID_COLUMN_NAME = "id"
    CONVERSATION_COLUMN_NAME = "conversations"
    IMAGES_COLUMN_NAME = "image_bins"
    IMAGE_PATHS_COLUMN_NAME = "image_paths"

    LLAVA_PARQUET_SCHEMA = pa.schema(
        [
            ("id", pa.utf8()),  # From source JSON
            ("contents", pa.utf8()),  # Created from j2p
            ("source", pa.utf8()),  # From j2p if not in source JSON
            (
                "orig_image_fpaths",
                pa.list_(pa.utf8()),
            ),  # From j2p - contents of "image" key in JSON
            (
                "conversations",  # From source JSON
                pa.list_(pa.struct([("from", pa.utf8()), ("value", pa.utf8())])),
            ),
            ("orig_json_path", pa.utf8()),  # From j2j
            (
                "image_bins",
                pa.list_(pa.binary()),
            ),  # J2P generates this by reading image off of COS
            ("index", pa.int64()),  # From J2J
            (
                "fixed_image_fpaths",
                pa.list_(pa.utf8()),
            ),  # J2P generated - relative paths to image
            (
                "absolute_image_paths",
                pa.list_(pa.utf8()),
            ),  # J2P generated - full path to image
        ]
    )
    LLAVA_JSONL_REQUIRED_KEYS = {
        "id",  # Source JSON
        "conversations",  # Source JSON
        "index",  # Added from j2j
        "orig_json_path",  # Added from j2j
    }


from data_processing.utils import get_dpk_logger

logger = get_dpk_logger()


class JsonUtils:

    @staticmethod
    def resize_table(table: pa.Table, parquet_size_limit: int) -> list[pa.Table]:
        """
        Split pa.Table into list of smaller pa.Table objects less than parquet_size_limit.

        :param table: pa.Table to be resized
        :param parquet_size_limit: int - Max size in bytes for each smaller table
        :return: - list of pa.Table objects after resize - can return empty list if table is empty
        """
        parquet_size_limit = (
            0.95 * parquet_size_limit
        )  # 95% of full size for some breathing room
        tables, curr_table = [], []
        for row in table.to_batches(max_chunksize=1):
            curr_table.append(row)
            if (  # If size of table is above threshold, create it
                sys.getsizeof(t := pa.Table.from_batches(batches=curr_table))
                >= parquet_size_limit
            ):
                tables.append(t)
                curr_table = []
        if len(curr_table) > 0:
            tables.append(pa.Table.from_batches(batches=curr_table))
        tables = [t for t in tables if t]
        return tables

    @staticmethod
    def jsonl_to_list_of_dicts(jsonl_bytes: bytes) -> list[dict]:
        """Convert bytes of jsonl file to list of dictionaries.

        Args:
            jsonl_bytes (bytes): Jsonl file as bytes

        Returns:
            list[dict]: List of dictionaries, each from a line of the jsonl file
        """
        lines = jsonl_bytes.splitlines()
        return [json.loads(line) for line in lines]

    @staticmethod
    def batch(
        datapoints: list[object], len_per_batch: int = None
    ) -> list[list[object]]:
        """Group list of items to list of list of items, where each of the
        sub-lists are of the size len_per_batch.

        Args:
            datapoints (list[object]): List of object to split into smaller lists
            len_per_batch (int, optional): Max length of the smaller lists. Defaults to None. <= 0 or None returns a single batch.

        Returns:
            list[list[object]]: list of object sublists.
        """
        if not len_per_batch or len_per_batch <= 0:
            return [datapoints]
        total, batched_datapoints = len(datapoints), []
        for start_index in range(0, total, len_per_batch):
            batched_datapoints.append(
                datapoints[start_index : min(start_index + len_per_batch, total)]
            )
        return batched_datapoints

    @staticmethod
    def map_absolute_paths_to_cos_paths(
        orig_paths: list[str], prefix_to_replace: str, prefix_to_replace_to: str
    ) -> list[str]:
        """
        Replace prefix_to_replace with prefix_to_replace_to in all strings in list.
        Returns the same list of strings if either prefix_to_replace or prefix_to_replace_to
        are None.

        :param orig_paths: list of strings to replace in
        :param prefix_to_replace: string prefix to replace
        :param prefix_to_replace_to: string to replace prefix to
        :return: list of strings with their prefixes replaced
        """
        if prefix_to_replace and prefix_to_replace_to:
            return [
                p.replace(prefix_to_replace, prefix_to_replace_to, 1)
                for p in orig_paths
            ]
        else:
            return orig_paths

    @staticmethod
    def read_images(image_paths: list[str], data_access: DataAccess) -> list[bytes]:
        """
        Read list of image paths into list of image bytes.
        Throws exception if image cannot be read or cannot be parsed by cv2.

        :param image_paths: list of absolute path strings for image files
        :param data_access: DataAccess object used to get the images
        :return: list of bytes of images.
        """
        img_bins = [data_access.get_file(img_path)[0] for img_path in image_paths]
        cv2_imgs = [JsonUtils.convert_bytes_to_image(img) for img in img_bins]
        if None in img_bins or None in cv2_imgs:
            raise Exception("Image not read correctly.")
        return img_bins

    @staticmethod
    def read_llava(
        datapoint: dict,
        data_access: DataAccess,
        orig_image_parent_dir: str,
        actual_image_parent_dir: str,
    ) -> dict:
        """
        Re-formats the datapoint dictionary of the LLAVA format into dictionary conforming
        to Schema.LLAVA_PARQUET_SCHEMA.
        Throws exception if image could not be read or if datapoint not in LLAVA format.

        :param datapoint: dictionary with LLAVA keys
        :param data_access: DataAccess object used to read images from
        :param orig_image_parent_dir: path substring in image's absolute path that should be replaced with the correct one
        :param actual_image_parent_dir: path substring in image's path to replace orig_image_parent_dir to
        :return: dictionary with standardized key-values pairs for parquet generation.
        """
        if len(Schema.LLAVA_JSONL_REQUIRED_KEYS.difference(set(datapoint.keys()))) != 0:
            raise Exception(
                f"Missing keys from json file: "
                f"{Schema.LLAVA_JSONL_REQUIRED_KEYS.difference(set(datapoint.keys()))}"
            )

        # Create "contents" and add "source"=None if not available for consistency
        if "contents" not in datapoint:
            datapoint["contents"] = "\n".join(
                [conv["value"].strip() for conv in datapoint["conversations"]]
            )
        if datapoint["id"] is not None:
            datapoint["id"] = str(datapoint["id"])
        if "source" not in datapoint:
            datapoint["source"] = None

        # LLAVA format allows images to be None, i.e. conversations without a
        # reference image. In that case fill with empty arrays-
        if "image" not in datapoint:
            datapoint["image"] = None
        if datapoint["image"] is None:
            datapoint["image_bins"] = []
            datapoint["fixed_image_fpaths"] = []
            datapoint["absolute_image_paths"] = []
            datapoint["orig_image_fpaths"] = []
            return datapoint

        # Standardize to list of images
        if type(datapoint["image"]) != list:
            datapoint["image"] = [datapoint["image"]]
        datapoint["orig_image_fpaths"] = datapoint["image"]
        datapoint["absolute_image_paths"] = JsonUtils.map_absolute_paths_to_cos_paths(
            orig_paths=datapoint["image"],
            prefix_to_replace=orig_image_parent_dir,
            prefix_to_replace_to=actual_image_parent_dir,
        )
        datapoint["fixed_image_fpaths"] = [
            f.replace(orig_image_parent_dir, "") for f in datapoint["orig_image_fpaths"]
        ]

        # Read images as bytes
        datapoint["image_bins"] = JsonUtils.read_images(
            image_paths=datapoint["absolute_image_paths"], data_access=data_access
        )
        return datapoint

    @staticmethod
    def list_of_dicts_to_dict_of_lists(datapoints: list[dict]) -> dict[str, list]:
        """Converts list of dictionaries to dictionary of lists.

        E.g. given [{"key1" : 1, "key2" : "2"}, ....] returns {"key1" : [1], "key2": ["2"]}.
        If the same keys do not exist for all items in list, then will be set to None in output
        dict.

        Does not perform type checks.

        Args:
            datapoints (list[dict]): List of dictionary objects to convert.

        Returns:
            dict[list]: Dictionary of lists.
        """
        # Getting all possible dictionary keys
        all_keys = set()
        for d in datapoints:
            all_keys.update(d.keys())

        # Converting here.
        dict_of_lists = defaultdict(list)
        for d in datapoints:
            for k in all_keys:
                dict_of_lists[k].append(d[k])
        return dict_of_lists

    @staticmethod
    def table2json(
        self, table: pa.Table, as_jsonl: bool = True, data_access: DataAccess = None
    ) -> str:
        """
        Takes a table created from JSON using json2table() and regenerates the json, maintaining
        only the original format as expected by json2table().   Any additional columns are ignored.
        data_access is used to write the json file and images embedded in the table to the relative locations
        specified in the table for each image.
        """
        # Convert to Pandas DataFrame (optional, for easier handling)
        df = table.to_pandas()
        if "orig_image_fpaths" in df.columns:
            if "image" not in df.columns:
                df = df.rename(columns={"orig_image_fpaths": "image"})

        if "image" not in df.columns:
            raise RuntimeError("No path provided for output images")

        df_columns = list(df.columns)

        if data_access is not None:

            output_folder = data_access.get_output_folder()
            image_output_folder = os.path.join(output_folder, self.write_image_path)
            image_columns = [
                "image_bins",
                "blurred_images",
            ]  # Columns that store binary images
            image_export_required_columns = ["image_bins", "image"]

            image_columns_export = list(set(image_columns) & set(self.export_columns))
            if len(image_columns_export) > 1:  # If
                raise RuntimeError("More than 1 image columns need to be exported!")
            if len(image_columns_export) == 0:
                raise RuntimeError(
                    "Please specify the image column need to be exported!"
                )

            if "image_bins" in image_columns_export:
                json_columns_export = list(set(df_columns) - set(image_columns_export))
            else:
                image_columns_export.append("image_bins")
                json_columns_export = list(set(df_columns) - set(image_columns_export))

            image_columns_export = list(
                set(image_export_required_columns + image_columns_export)
            )  # add column path for output structure
            # separate columns that needed for generating json from those needed for image writing
            for item in image_columns_export:
                if item not in df_columns:
                    raise RuntimeError(item + " not in parquet table!")

            img_df = df[image_columns_export]
            df = df[json_columns_export]

        # Convert to JSON
        if as_jsonl:
            json_str = ""
            separator = "\n"
        else:
            json_str = "[\n"
            separator = ",\n"
        first = True
        for i, row in df.iterrows():
            if data_access is not None:
                # write out the image(s)
                if "image_bins" in self.export_columns:
                    for img_idx in range(len(img_df["image"][i])):
                        try:
                            # temparaty path fix, should use image path directly
                            if img_df["image"][i][img_idx].startswith("/"):
                                img_relative_path = img_df["image"][i][img_idx][1:]
                            else:
                                img_relative_path = img_df["image"][i][img_idx]
                            single_image_path = os.path.join(
                                image_output_folder, img_relative_path
                            )
                            single_image_binary = img_df["image_bins"][i][img_idx]
                            # write image
                            data_access.save_file(
                                path=single_image_path, data=single_image_binary
                            )
                        except Exception as e:
                            logger.warning(
                                f"Got exception accessing or writing image row {i}: {e}"
                            )
                if "blurred_images" in self.export_columns:
                    # check value, read from 'image_bins' or not
                    for img_idx in range(len(img_df["image"][i])):
                        if img_df["blurred_images"][i][img_idx] == None:
                            try:
                                if img_df["image"][i][img_idx].startswith("/"):
                                    img_relative_path = img_df["image"][i][img_idx][1:]
                                else:
                                    img_relative_path = img_df["image"][i][img_idx]
                                single_image_path = os.path.join(
                                    image_output_folder, img_relative_path
                                )
                                single_image_binary = img_df["image_bins"][i][img_idx]
                                data_access.save_file(
                                    path=single_image_path, data=single_image_binary
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Got exception accessing or writing image row {i}: {e}"
                                )
                        else:

                            try:
                                if img_df["image"][i][img_idx].startswith("/"):
                                    img_relative_path = img_df["image"][i][img_idx][1:]
                                else:
                                    img_relative_path = img_df["image"][i][img_idx]
                                single_image_path = os.path.join(
                                    image_output_folder, img_relative_path
                                )
                                # print(single_image_path)
                                single_image_binary = img_df["blurred_images"][i][
                                    img_idx
                                ]
                                data_access.save_file(
                                    path=single_image_path, data=single_image_binary
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Got exception accessing or writing image row {i}: {e}"
                                )

            if not first:
                json_str += separator
            else:
                first = False
            j = row.to_json()
            # Remove the escapes
            j = json.loads(j)
            j = json.dumps(j)
            json_str += j

        if not as_jsonl:
            json_str += "\n]"

        # list of dict. write to byte
        # return json_str.encode("utf-8")
        return json_str

    @staticmethod
    def get_table_from_bytes(byte_array: bytes) -> pa.Table:
        try:
            table = TransformUtils.convert_binary_to_arrow(byte_array)
            if table is not None:
                return table
        except Exception as e:
            logger.warning(f"Could not convert bytes to pyarrow: {e}")

        logger.info(f"Attempting read of pyarrow Table using polars")
        import polars

        df = polars.read_parquet(io.BytesIO(byte_array))
        table = df.to_arrow()

        return table

    @staticmethod
    def convert_bytes_to_image(bytes) -> Image.Image:
        # use imdecode function

        # image = np.asarray(bytearray(bytes), dtype="uint8")
        # image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        image = Image.open(io.BytesIO(bytes))

        if image.mode != "RGB":
            image = image.convert("RGB")

        return image

    @staticmethod
    def convert_numpy_to_image(
        np_array, imformat="PNG"
    ) -> bytes:  # convert a numpy array into encoded bytes
        image = Image.fromarray(np_array)

        buffer = io.BytesIO()
        image.save(buffer, format=imformat)
        buffer.seek(0)

        img_bytes = buffer.getvalue()

        return img_bytes

    @staticmethod
    def show_encoded_bytes(image_bytes: bytes):
        image = Image.open(io.BytesIO(image_bytes))
        image.show()

    @staticmethod
    def convert_PILimage_to_image(image: Image, imformat="PNG") -> bytes:

        buffer = io.BytesIO()
        image.save(buffer, format=imformat)
        buffer.seek(0)

        img_bytes = buffer.getvalue()
        # tmp = JsonUtils.convert_bytes_to_image(img_bytes)
        # print(f"{tmp.format = }")
        return img_bytes

    @staticmethod
    def get_image_lists(table: pa.Table) -> tuple[list[list[bytes], list[list[str]]]]:
        """Retrieves images from pyarrow table as bytes.

        First level of list are the rows, with each row possibly
        containing (multiple images or a single image) as a list.

        Args:
            table (pa.Table): Table to retrieve images from.

        Returns:
            list[list[bytes]]: list of list of bytes of images.
            list[list[str]]: list of paths from which the image was read
        """
        data = []
        paths = []
        columns = table.select(["image_bins", "orig_image_fpaths"])
        images_colum = columns[0].to_pylist()
        paths_column = columns[1].to_pylist()
        assert isinstance(images_colum, list)
        assert isinstance(paths_column, list)
        for i in range(len(images_colum)):
            img_list = images_colum[i]
            path_list = paths_column[i]
            if len(img_list) == len(path_list):
                data.append(img_list)
                paths.append(path_list)
            else:
                data.append([])
                paths.append([])
                logger.warning(
                    f"Row {i} of table has image list ({len(img_list)=}) and path list ({path_list=}) of different lengths"
                )

        return data, paths

    @staticmethod
    def get_batched_image_lists(batch: list[dict]):
        """ """
        batch_of_image_lists = []
        images = batch.get(
            Schema.IMAGES_COLUMN_NAME
        )  # column of images, each cell/row containing a list of images/bytes
        if images is None:
            # TODO: Handle loading images by path
            raise ValueError("Not implemented yet")
        else:
            for row_image_dict in images:  # Over each image list of each row
                image_list_for_row = []
                for image in row_image_dict:
                    b = image.get("bytes")
                    pixels = JsonUtils.convert_bytes_to_image(b)
                    image_list_for_row.append(pixels)
                print(f"{len(image_list_for_row)=}")
                batch_of_image_lists.append(image_list_for_row)

        print(f"{len(batch_of_image_lists)=}")
        return batch_of_image_lists
