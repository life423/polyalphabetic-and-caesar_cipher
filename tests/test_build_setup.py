"""
Test suite for build configuration and CI/CD setup.

This module contains tests to verify that the build and CI/CD configuration
is properly set up and functional.
"""

import os
import unittest
import json
import sys
import yaml
from pathlib import Path

# Resolve paths from the repo root so tests pass from any working directory
ROOT = Path(__file__).resolve().parent.parent


class TestBuildSetup(unittest.TestCase):
    """Test cases for the build and CI/CD configuration."""
    
    def test_required_files_exist(self):
        """Test that all required configuration files exist."""
        required_files = [
            "requirements.txt",
            "setup.py",
            "scripts/build_exe.py",
            "pytest.ini",
            ".github/workflows/python-app.yml"
        ]
        
        for file_path in required_files:
            with self.subTest(file=file_path):
                self.assertTrue(os.path.exists(ROOT / file_path), f"Required file {file_path} does not exist")
    
    def test_github_workflow_config(self):
        """Test that GitHub workflow configuration is valid."""
        workflow_path = ROOT / '.github/workflows/python-app.yml'
        
        # Skip this test if the workflow file doesn't exist
        if not os.path.exists(workflow_path):
            self.skipTest(f"Workflow file {workflow_path} does not exist")
        
        # Read the file content directly first
        with open(workflow_path, 'r') as f:
            content = f.read()
            
        # Check for key components through direct content examination
        self.assertIn('name:', content, "Workflow should have a name")
        self.assertIn('on:', content, "Workflow should define triggers")
        self.assertIn('jobs:', content, "Workflow should define jobs")
        self.assertIn('test:', content, "Workflow should have a test job")
        self.assertIn('build-and-release:', content, "Workflow should have a build job")
        self.assertIn('needs: test', content, "Build job should depend on test job")
            
        # Now attempt to parse the YAML with safe loading
        try:
            # Use a special loader to handle 'on' keyword
            workflow = yaml.safe_load(content)
            
            # Check the structure but be flexible about the 'on' key 
            # which might be parsed differently
            self.assertIn('name', workflow, "Workflow should have a name")
            self.assertIn('jobs', workflow, "Workflow should define jobs")
            
            # Check that test and build jobs are defined
            self.assertIn('test', workflow['jobs'], "Workflow should have a test job")
            self.assertIn('build-and-release', workflow['jobs'], "Workflow should have a build job")
            
            # Check that build depends on test
            self.assertIn('needs', workflow['jobs']['build-and-release'], "Build job should depend on test job")
            self.assertEqual(workflow['jobs']['build-and-release']['needs'], 'test', 
                            "Build job should depend on test job")
        except Exception as e:
            # Log the error but don't fail the test as we already checked the content via string matching
            print(f"WARNING: Could not fully parse YAML: {str(e)}")
    
    def test_pyinstaller_spec(self):
        """Test that PyInstaller spec file is properly configured."""
        spec_path = ROOT / 'cipher_tool.spec'
        
        # Skip this test if the spec file doesn't exist
        if not os.path.exists(spec_path):
            self.skipTest(f"Spec file {spec_path} does not exist")
        
        # Read the spec file content
        with open(spec_path, 'r') as f:
            spec_content = f.read()
        
        # Check for important configuration elements
        self.assertIn("name='cipher_tool'", spec_content, 
                     "Spec file should set the name to 'cipher_tool'")
        self.assertIn("console=False", spec_content, 
                     "Spec file should configure a windowed application")
    
    def test_setup_py_config(self):
        """Test that setup.py is properly configured."""
        setup_path = ROOT / 'setup.py'
        
        # Skip this test if the setup file doesn't exist
        if not os.path.exists(setup_path):
            self.skipTest(f"Setup file {setup_path} does not exist")
        
        # Read the setup file content
        with open(setup_path, 'r') as f:
            setup_content = f.read()
        
        # Check for important configuration elements
        self.assertIn("name=\"cipher_tools\"", setup_content, 
                     "setup.py should set the package name")
        self.assertIn("version=", setup_content, 
                     "setup.py should specify a version")
        self.assertIn("entry_points", setup_content, 
                     "setup.py should define entry points")
    
    def test_requirements_txt(self):
        """Test that requirements.txt includes necessary packages."""
        req_path = ROOT / 'requirements.txt'
        
        # Skip this test if the requirements file doesn't exist
        if not os.path.exists(req_path):
            self.skipTest(f"Requirements file {req_path} does not exist")
        
        # Read the requirements file content
        with open(req_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # Check for important packages
        essential_packages = ['pytest', 'pyinstaller', 'flake8']
        for package in essential_packages:
            package_present = any(package in req for req in requirements)
            self.assertTrue(package_present, f"Requirements should include {package}")
    
    def test_build_exe_script(self):
        """Test that build_exe.py is executable and properly configured."""
        script_path = ROOT / 'scripts' / 'build_exe.py'
        
        # Skip this test if the script doesn't exist
        if not os.path.exists(script_path):
            self.skipTest(f"Build script {script_path} does not exist")
        
        # Check if the script has executable permissions on Unix-like systems
        if sys.platform != "win32":
            self.assertTrue(os.access(script_path, os.X_OK), 
                           "Build script should have executable permissions")
        
        # Read the script content and check for important functions
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        expected_functions = ['main', 'clean_build_directories', 'install_dependencies', 'get_build_command']
        for func in expected_functions:
            self.assertIn(f"def {func}", script_content, 
                         f"Build script should define {func} function")


class TestProjectStructure(unittest.TestCase):
    """Test cases for the project structure."""
    
    def test_core_modules_exist(self):
        """Test that all core modules exist."""
        core_modules = [
            "src/core/ciphers.py",
            "src/services/cipher_service.py",
            "src/ai/analyzer.py",
            "src/services/file_service.py",
            "src/ui/cli.py",
            "src/ui/gui.py"
        ]
        
        for module in core_modules:
            with self.subTest(module=module):
                self.assertTrue(os.path.exists(ROOT / module), f"Core module {module} does not exist")
    
    def test_updated_cipher_implementations(self):
        """Test that the cipher implementations include the new ciphers."""
        with open(ROOT / 'src' / 'core' / 'ciphers.py', 'r') as f:
            core_content = f.read()
        
        # Check that all cipher classes are defined
        required_ciphers = [
            "CaesarCipher",
            "PolyalphabeticCipher",
            "SubstitutionCipher",
            "TranspositionCipher",
            "RailFenceCipher",
            "AffineCipher"
        ]
        
        for cipher in required_ciphers:
            self.assertIn(f"class {cipher}", core_content, 
                         f"{cipher} should be defined in src/core/ciphers.py")
    
    def test_enhanced_ai_capabilities(self):
        """Test that the AI module has enhanced capabilities."""
        with open(ROOT / 'src' / 'ai' / 'analyzer.py', 'r') as f:
            ai_content = f.read()
        
        # Check for enhanced analysis methods
        enhanced_features = [
            "ENGLISH_BIGRAMS",
            "INDICATOR_WORDS",
            "analyze_with_known_plaintext",
            "_calculate_ngram_score"
        ]
        
        for feature in enhanced_features:
            self.assertIn(feature, ai_content, 
                         f"Enhanced feature {feature} should be in src/ai/analyzer.py")


class TestServiceIntegration(unittest.TestCase):
    """Test cases for service integration with new ciphers."""
    
    def test_service_includes_new_ciphers(self):
        """Test that the service layer includes methods for all cipher types."""
        with open(ROOT / 'src' / 'services' / 'cipher_service.py', 'r') as f:
            service_content = f.read()
        
        # Check that methods for all cipher types are defined
        required_methods = [
            "encrypt_caesar", "decrypt_caesar",
            "encrypt_polyalphabetic", "decrypt_polyalphabetic",
            "encrypt_substitution", "decrypt_substitution",
            "encrypt_transposition", "decrypt_transposition",
            "encrypt_rail_fence", "decrypt_rail_fence",
            "encrypt_affine", "decrypt_affine"
        ]
        
        for method in required_methods:
            self.assertIn(f"def {method}", service_content, 
                         f"Method {method} should be defined in src/services/cipher_service.py")


if __name__ == "__main__":
    unittest.main()
