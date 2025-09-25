# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
import tempfile
from unittest.mock import patch, MagicMock
from dpk_docling2parquet.transform import (
    Docling2ParquetTransform,
    docling2parquet_vlm_model_type,
    docling2parquet_inference_framework,
    docling2parquet_response_format,
    docling2parquet_transformers_model_type,
    docling2parquet_use_vlm_pipeline_key,
    docling2parquet_vlm_model_type_key,
    docling2parquet_vlm_repo_id_key,
    docling2parquet_vlm_prompt_key,
    docling2parquet_vlm_api_url_key,
    docling2parquet_vlm_api_model_key,
    docling2parquet_vlm_inference_framework_key,
    docling2parquet_vlm_response_format_key,
    docling2parquet_vlm_transformers_model_type_key,
    docling2parquet_vlm_scale_key,
    docling2parquet_vlm_temperature_key,
    docling2parquet_vlm_max_new_tokens_key,
    docling2parquet_vlm_timeout_key,
    docling2parquet_vlm_trust_remote_code_key,
    docling2parquet_vlm_load_in_8bit_key,
)


class TestDocling2ParquetVLM(unittest.TestCase):
    """
    Test class for VLM (Vision Language Model) functionality in Docling2Parquet transform.
    Tests VLM configuration, model types, and pipeline initialization.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.base_config = {
            "contents_type": "MARKDOWN",
            "accelerator_device": "CPU",
            "double_precision": 0,
        }

    def test_vlm_enum_values(self):
        """Test that VLM enum values are properly defined"""
        # Test VLM model types
        expected_model_types = [
            "smoldocling_mlx",
            "smoldocling_transformers",
            "granite_vision_transformers",
            "granite_vision_ollama",
            "pixtral_12b_transformers",
            "pixtral_12b_mlx",
            "phi4_transformers",
            "qwen25_vl_3b_mlx",
            "gemma3_12b_mlx",
            "custom_inline",
            "custom_api"
        ]
        actual_model_types = [item.value for item in docling2parquet_vlm_model_type]
        for expected in expected_model_types:
            self.assertIn(expected, actual_model_types)
        

        expected_frameworks = ["mlx", "transformers"]
        actual_frameworks = [item.value for item in docling2parquet_inference_framework]
        for expected in expected_frameworks:
            self.assertIn(expected, actual_frameworks)
        

        expected_formats = ["doctags", "markdown", "html"]
        actual_formats = [item.value for item in docling2parquet_response_format]
        for expected in expected_formats:
            self.assertIn(expected, actual_formats)
        
        print(f"VLM model types: {actual_model_types}")
        print(f"Inference frameworks: {actual_frameworks}")
        print(f"Response formats: {actual_formats}")

    def test_vlm_disabled_configuration(self):
        """Test VLM pipeline when disabled (default behavior)"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: False,
        }
        
        # This should work without VLM dependencies
        try:
            transform = Docling2ParquetTransform(config)
            self.assertIsNotNone(transform)
            print("VLM disabled configuration: Valid")
        except Exception as e:
            self.fail(f"VLM disabled configuration failed: {e}")

    @patch('dpk_docling2parquet.transform.VlmPipeline')
    @patch('dpk_docling2parquet.transform.DocumentConverter')
    def test_vlm_smoldocling_transformers_configuration(self, mock_converter, mock_vlm_pipeline):
        """Test SmolDocling Transformers VLM configuration"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: True,
            docling2parquet_vlm_model_type_key: "SMOLDOCLING_TRANSFORMERS",
            docling2parquet_vlm_repo_id_key: "ds4sd/SmolDocling-256M-preview",
            docling2parquet_vlm_prompt_key: "Convert this page to docling.",
            docling2parquet_vlm_inference_framework_key: "TRANSFORMERS",
            docling2parquet_vlm_response_format_key: "DOCTAGS",
            docling2parquet_vlm_transformers_model_type_key: "AUTOMODEL_VISION2SEQ",
            docling2parquet_vlm_temperature_key: 0.0,
            docling2parquet_vlm_max_new_tokens_key: 4096,
        }
        

        mock_vlm_instance = MagicMock()
        mock_vlm_pipeline.return_value = mock_vlm_instance
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        try:
            transform = Docling2ParquetTransform(config)
            self.assertIsNotNone(transform)
            print("SmolDocling Transformers VLM configuration: Valid")
        except Exception as e:
            self.fail(f"SmolDocling Transformers VLM configuration failed: {e}")

    @patch('dpk_docling2parquet.transform.VlmPipeline')
    @patch('dpk_docling2parquet.transform.DocumentConverter')
    def test_vlm_smoldocling_mlx_configuration(self, mock_converter, mock_vlm_pipeline):
        """Test SmolDocling MLX VLM configuration"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: True,
            docling2parquet_vlm_model_type_key: "SMOLDOCLING_MLX",
            docling2parquet_vlm_repo_id_key: "ds4sd/SmolDocling-256M-preview",
            docling2parquet_vlm_prompt_key: "Convert this page to docling.",
            docling2parquet_vlm_inference_framework_key: "MLX",
            docling2parquet_vlm_response_format_key: "MARKDOWN",
            docling2parquet_vlm_scale_key: 2.0,
            docling2parquet_vlm_temperature_key: 0.1,
            docling2parquet_vlm_max_new_tokens_key: 2048,
        }
        

        mock_vlm_instance = MagicMock()
        mock_vlm_pipeline.return_value = mock_vlm_instance
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        try:
            transform = Docling2ParquetTransform(config)
            self.assertIsNotNone(transform)
            print("SmolDocling MLX VLM configuration: Valid")
        except Exception as e:
            self.fail(f"SmolDocling MLX VLM configuration failed: {e}")

    @patch('dpk_docling2parquet.transform.VlmPipeline')
    @patch('dpk_docling2parquet.transform.DocumentConverter')
    def test_vlm_granite_vision_configuration(self, mock_converter, mock_vlm_pipeline):
        """Test Granite Vision VLM configuration"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: True,
            docling2parquet_vlm_model_type_key: "GRANITE_VISION_TRANSFORMERS",
            docling2parquet_vlm_repo_id_key: "ibm-granite/granite-3.0-8b-instruct",
            docling2parquet_vlm_prompt_key: "Analyze this document page.",
            docling2parquet_vlm_inference_framework_key: "TRANSFORMERS",
            docling2parquet_vlm_response_format_key: "HTML",
            docling2parquet_vlm_transformers_model_type_key: "AUTOMODEL_CAUSALLM",
            docling2parquet_vlm_trust_remote_code_key: True,
            docling2parquet_vlm_load_in_8bit_key: False,
        }
        

        mock_vlm_instance = MagicMock()
        mock_vlm_pipeline.return_value = mock_vlm_instance
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        try:
            transform = Docling2ParquetTransform(config)
            self.assertIsNotNone(transform)
            print("Granite Vision VLM configuration: Valid")
        except Exception as e:
            self.fail(f"Granite Vision VLM configuration failed: {e}")

    @patch('dpk_docling2parquet.transform.VlmPipeline')
    @patch('dpk_docling2parquet.transform.DocumentConverter')
    def test_vlm_custom_api_configuration(self, mock_converter, mock_vlm_pipeline):
        """Test Custom API VLM configuration"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: True,
            docling2parquet_vlm_model_type_key: "CUSTOM_API",
            docling2parquet_vlm_api_url_key: "http://localhost:11434/v1/chat/completions",
            docling2parquet_vlm_api_model_key: "granite3.2-vision:2b",
            docling2parquet_vlm_prompt_key: "Process this document.",
            docling2parquet_vlm_response_format_key: "DOCTAGS",
            docling2parquet_vlm_timeout_key: 60.0,
        }
        
        # Mock the VLM pipeline and converter
        mock_vlm_instance = MagicMock()
        mock_vlm_pipeline.return_value = mock_vlm_instance
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        try:
            transform = Docling2ParquetTransform(config)
            self.assertIsNotNone(transform)
            print("Custom API VLM configuration: Valid")
        except Exception as e:
            self.fail(f"Custom API VLM configuration failed: {e}")

    def test_vlm_parameter_validation(self):
        """Test VLM parameter validation"""

        with self.assertRaises(KeyError):
            config = {
                **self.base_config,
                docling2parquet_use_vlm_pipeline_key: True,
                docling2parquet_vlm_model_type_key: "INVALID_MODEL_TYPE",
            }
            transform = Docling2ParquetTransform(config)
        

        with self.assertRaises(KeyError):
            config = {
                **self.base_config,
                docling2parquet_use_vlm_pipeline_key: True,
                docling2parquet_vlm_model_type_key: "SMOLDOCLING_TRANSFORMERS",
                docling2parquet_vlm_inference_framework_key: "INVALID_FRAMEWORK_TYPE",
            }
            transform = Docling2ParquetTransform(config)
        
        print("VLM parameter validation: Passed")

    def test_vlm_default_values(self):
        """Test VLM default parameter values"""
        from dpk_docling2parquet.transform import (
            docling2parquet_use_vlm_pipeline_default,
            docling2parquet_vlm_model_type_default,
            docling2parquet_vlm_repo_id_default,
            docling2parquet_vlm_prompt_default,
            docling2parquet_vlm_api_url_default,
            docling2parquet_vlm_api_model_default,
            docling2parquet_vlm_inference_framework_default,
            docling2parquet_vlm_response_format_default,
            docling2parquet_vlm_transformers_model_type_default,
            docling2parquet_vlm_scale_default,
            docling2parquet_vlm_temperature_default,
            docling2parquet_vlm_max_new_tokens_default,
            docling2parquet_vlm_timeout_default,
            docling2parquet_vlm_trust_remote_code_default,
            docling2parquet_vlm_load_in_8bit_default,
        )
        

        self.assertFalse(docling2parquet_use_vlm_pipeline_default)
        self.assertEqual(docling2parquet_vlm_model_type_default, docling2parquet_vlm_model_type.SMOLDOCLING_TRANSFORMERS)
        self.assertEqual(docling2parquet_vlm_repo_id_default, "ds4sd/SmolDocling-256M-preview")
        self.assertEqual(docling2parquet_vlm_prompt_default, "Convert this page to docling.")
        self.assertEqual(docling2parquet_vlm_api_url_default, "http://localhost:11434/v1/chat/completions")
        self.assertEqual(docling2parquet_vlm_api_model_default, "granite3.2-vision:2b")
        self.assertEqual(docling2parquet_vlm_inference_framework_default, docling2parquet_inference_framework.TRANSFORMERS)
        self.assertEqual(docling2parquet_vlm_response_format_default, docling2parquet_response_format.DOCTAGS)
        self.assertEqual(docling2parquet_vlm_transformers_model_type_default, docling2parquet_transformers_model_type.AUTOMODEL_VISION2SEQ)
        self.assertEqual(docling2parquet_vlm_scale_default, 2.0)
        self.assertEqual(docling2parquet_vlm_temperature_default, 0.0)
        self.assertEqual(docling2parquet_vlm_max_new_tokens_default, 4096)
        self.assertEqual(docling2parquet_vlm_timeout_default, 120.0)
        self.assertFalse(docling2parquet_vlm_trust_remote_code_default)
        self.assertTrue(docling2parquet_vlm_load_in_8bit_default)
        
        print("VLM default values: Valid")

    @patch('dpk_docling2parquet.transform.VlmPipeline')
    @patch('dpk_docling2parquet.transform.DocumentConverter')
    def test_vlm_options_method(self, mock_converter, mock_vlm_pipeline):
        """Test the _get_vlm_options method"""
        config = {
            **self.base_config,
            docling2parquet_use_vlm_pipeline_key: True,
            docling2parquet_vlm_model_type_key: "SMOLDOCLING_TRANSFORMERS",
        }
        

        mock_vlm_instance = MagicMock()
        mock_vlm_pipeline.return_value = mock_vlm_instance
        mock_converter_instance = MagicMock()
        mock_converter.return_value = mock_converter_instance
        
        try:
            transform = Docling2ParquetTransform(config)
            
            vlm_options = transform._get_vlm_options(docling2parquet_vlm_model_type.SMOLDOCLING_TRANSFORMERS)
            self.assertIsNotNone(vlm_options)
            
            vlm_options = transform._get_vlm_options(docling2parquet_vlm_model_type.SMOLDOCLING_MLX)
            self.assertIsNotNone(vlm_options)
            
            vlm_options = transform._get_vlm_options(docling2parquet_vlm_model_type.CUSTOM_API)
            self.assertIsNotNone(vlm_options)
            
            print("VLM options method: Valid")
        except Exception as e:
            self.fail(f"VLM options method test failed: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)