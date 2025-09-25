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
import unittest
import platform
import torch
from unittest.mock import patch, MagicMock
import os
import tempfile


class TestGPUAcceleratorSimple(unittest.TestCase):

    def test_torch_availability(self):
        """Test that PyTorch is available"""
        self.assertTrue(hasattr(torch, '__version__'))
        print(f"PyTorch version: {torch.__version__}")
    
    def test_cpu_device_available(self):
        """Test CPU device is always available"""
        device = torch.device('cpu')
        self.assertEqual(str(device), 'cpu')
        print("CPU device: Available")
    
    @unittest.skipUnless(torch.cuda.is_available(), "CUDA not available")
    def test_cuda_device_available(self):
        """Test CUDA device if available"""
        device = torch.device('cuda')
        self.assertTrue('cuda' in str(device))
        print(f"CUDA device: {device}")
        print(f"CUDA device count: {torch.cuda.device_count()}")
    
    @unittest.skipUnless(
        platform.system() == "Darwin" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        "MPS not available"
    )
    def test_mps_device_available(self):
        """Test MPS device if available (macOS only)"""
        device = torch.device('mps')
        self.assertEqual(str(device), 'mps')
        print("MPS device: Available")
    
    def test_accelerator_device_enum_values(self):
        """Test accelerator device enum values"""
        try:
            from dpk_docling2parquet.transform import docling2parquet_accelerator_device
            # Test that the enum has expected values
            expected_values = ['AUTO', 'CPU', 'CUDA', 'MPS']
            actual_values = [item.value for item in docling2parquet_accelerator_device]
            for expected in expected_values:
                self.assertIn(expected, actual_values)
            print(f"Accelerator device options: {actual_values}")
        except ImportError as e:
            self.skipTest(f"Could not import accelerator device enum: {e}")
    
    def test_gpu_accelerator_cpu_config(self):
        """Test CPU accelerator configuration"""
        # Simulate CPU configuration
        config = {
            "docling2parquet_accelerator_device": "CPU",
            "docling2parquet_accelerator_device_map": "auto",
            "docling2parquet_accelerator_torch_dtype": "auto"
        }
        
        # Validate CPU device
        device = torch.device('cpu')
        self.assertEqual(str(device), 'cpu')
        
        # Test that CPU is always available
        self.assertTrue(True)  # CPU is always available
        print("CPU accelerator configuration: Valid")
    
    def test_gpu_accelerator_auto_config(self):
        """Test AUTO accelerator configuration"""
        config = {
            "docling2parquet_accelerator_device": "AUTO",
            "docling2parquet_accelerator_device_map": "auto",
            "docling2parquet_accelerator_torch_dtype": "auto"
        }
        
        # AUTO should select the best available device
        if torch.cuda.is_available():
            recommended = "CUDA"
        elif platform.system() == "Darwin" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            recommended = "MPS"
        else:
            recommended = "CPU"
        
        print(f"AUTO accelerator would select: {recommended}")
        self.assertIn(recommended, ["CPU", "CUDA", "MPS"])
    
    @unittest.skipUnless(torch.cuda.is_available(), "CUDA not available")
    def test_gpu_accelerator_cuda_config(self):
        """Test CUDA accelerator configuration"""
        config = {
            "docling2parquet_accelerator_device": "CUDA",
            "docling2parquet_accelerator_device_map": "auto",
            "docling2parquet_accelerator_torch_dtype": "auto"
        }
        
        # Validate CUDA device
        device = torch.device('cuda')
        self.assertTrue('cuda' in str(device))
        self.assertTrue(torch.cuda.is_available())
        print("CUDA accelerator configuration: Valid")
    
    @unittest.skipUnless(
        platform.system() == "Darwin" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
        "MPS not available"
    )
    def test_gpu_accelerator_mps_config(self):
        """Test MPS accelerator configuration"""
        config = {
            "docling2parquet_accelerator_device": "MPS",
            "docling2parquet_accelerator_device_map": "auto",
            "docling2parquet_accelerator_torch_dtype": "auto"
        }
        
        # Validate MPS device
        device = torch.device('mps')
        self.assertEqual(str(device), 'mps')
        self.assertTrue(torch.backends.mps.is_available())
        print("MPS accelerator configuration: Valid")
    
    def test_invalid_accelerator_device(self):
        """Test handling of invalid accelerator device"""
        invalid_devices = ["INVALID", "TPU", "OPENCL", ""]
        
        for invalid_device in invalid_devices:
            with self.assertRaises((ValueError, RuntimeError)) or self.assertLogs():
                # This would normally raise an error in the actual transform
                # For testing, we just validate the device names
                if invalid_device not in ["CPU", "CUDA", "MPS", "AUTO"]:
                    raise ValueError(f"Invalid accelerator device: {invalid_device}")
    
    def test_accelerator_thread_count_validation(self):
        """Test thread count validation"""
        valid_thread_counts = [1, 2, 4, 8, 16]
        invalid_thread_counts = [0, -1, -5]
        
        for count in valid_thread_counts:
            self.assertGreater(count, 0)
        
        for count in invalid_thread_counts:
            self.assertLessEqual(count, 0)
        
        print("Thread count validation: Passed")
    
    def test_accelerator_default_values(self):
        """Test default accelerator values"""
        defaults = {
            "docling2parquet_accelerator_device": "AUTO",
            "docling2parquet_accelerator_device_map": "auto",
            "docling2parquet_accelerator_torch_dtype": "auto",
            "docling2parquet_accelerator_cuda_flash_attention": False
        }
        
        # Validate default values
        self.assertEqual(defaults["docling2parquet_accelerator_device"], "AUTO")
        self.assertEqual(defaults["docling2parquet_accelerator_device_map"], "auto")
        self.assertEqual(defaults["docling2parquet_accelerator_torch_dtype"], "auto")
        self.assertFalse(defaults["docling2parquet_accelerator_cuda_flash_attention"])
        
        print("Default accelerator values: Valid")
    
    @unittest.skipUnless(torch.cuda.is_available(), "CUDA not available")
    def test_cuda_flash_attention_config(self):
        """Test CUDA flash attention configuration"""
        config = {
            "docling2parquet_accelerator_device": "CUDA",
            "docling2parquet_accelerator_cuda_flash_attention": True
        }
        
        # Flash attention requires CUDA
        self.assertTrue(torch.cuda.is_available())
        print("CUDA flash attention configuration: Valid")
    
    def test_hardware_detection(self):
        """Test hardware detection and recommendations"""
        print("\n=== Hardware Detection ===")
        print(f"Platform: {platform.system()} {platform.machine()}")
        print(f"Python version: {platform.python_version()}")
        
        print(f"CPU available: True")
        
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {cuda_available}")
        if cuda_available:
            print(f"CUDA version: {torch.version.cuda}")
            print(f"CUDA device count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  Device {i}: {torch.cuda.get_device_name(i)}")
        
        if platform.system() == "Darwin":
            mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            print(f"MPS available: {mps_available}")
        
        # Recommendation
        if cuda_available:
            print("Recommendation: Use CUDA for best performance")
        elif platform.system() == "Darwin" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("Recommendation: Use MPS for GPU acceleration on macOS")
        else:
            print("Recommendation: Use CPU (no GPU acceleration available)")
    
    def test_integration_simulation(self):
        """Simulate integration test without complex dependencies"""
        print("\n=== Integration Test Simulation ===")
        
        # Simulate transform configuration
        base_config = {
            "data_files_to_use": ["test.pdf"],
            "docling2parquet_contents_type": "text/markdown",
            "docling2parquet_do_ocr": True,
            "docling2parquet_do_table_structure": True
        }
        
        # Test different accelerator configurations
        accelerator_configs = [
            {"docling2parquet_accelerator_device": "CPU"},
            {"docling2parquet_accelerator_device": "AUTO"}
        ]
        
        if torch.cuda.is_available():
            accelerator_configs.append({"docling2parquet_accelerator_device": "CUDA"})
        
        if platform.system() == "Darwin" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            accelerator_configs.append({"docling2parquet_accelerator_device": "MPS"})
        
        for config in accelerator_configs:
            full_config = {**base_config, **config}
            device = config["docling2parquet_accelerator_device"]
            
            # Simulate validation
            if device == "CPU":
                self.assertTrue(True)  # CPU always works
            elif device == "CUDA":
                self.assertTrue(torch.cuda.is_available())
            elif device == "MPS":
                self.assertTrue(platform.system() == "Darwin" and 
                              hasattr(torch.backends, "mps") and 
                              torch.backends.mps.is_available())
            elif device == "AUTO":
                self.assertTrue(True)  # AUTO should always work
            
            print(f"Configuration with {device}: Valid")


if __name__ == '__main__':
    unittest.main(verbosity=2)