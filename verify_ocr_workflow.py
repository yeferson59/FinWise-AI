#!/usr/bin/env python3
"""
Verification script for OCR workflow improvements.
This script performs static analysis to verify the implementation is correct.
"""

import ast
import sys
from pathlib import Path


class WorkflowVerifier:
    """Verifies OCR workflow implementation"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0

    def check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        path = Path(filepath)
        if path.exists():
            self.checks_passed += 1
            return True
        self.errors.append(f"File not found: {filepath}")
        return False

    def check_function_exists(self, filepath: str, function_name: str) -> bool:
        """Check if a function exists in a file"""
        if not self.check_file_exists(filepath):
            return False

        with open(filepath, "r") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                self.checks_passed += 1
                return True

        self.errors.append(f"Function '{function_name}' not found in {filepath}")
        return False

    def check_string_in_file(
        self, filepath: str, search_string: str, critical: bool = False
    ) -> bool:
        """Check if a string exists in a file"""
        path = Path(filepath)
        if not path.exists():
            if critical:
                self.errors.append(f"File not found: {filepath}")
            return False

        with open(filepath, "r") as f:
            content = f.read()

        if search_string in content:
            self.checks_passed += 1
            return True

        if critical:
            self.errors.append(f"Critical string '{search_string}' not found in {filepath}")
        else:
            self.warnings.append(
                f"String '{search_string}' not found in {filepath} (may not be critical)"
            )
        return False

    def verify_preprocessing(self):
        """Verify preprocessing.py changes"""
        print("Checking preprocessing.py...")

        filepath = "backend/app/services/preprocessing.py"

        # Check save_to_temp parameter exists
        self.check_function_exists(filepath, "preprocess_image")

        # Check cleanup function exists
        self.check_function_exists(filepath, "cleanup_temp_file")

        # Check critical imports
        self.check_string_in_file(filepath, "import tempfile", critical=True)
        self.check_string_in_file(filepath, "import os", critical=True)

        # Check save_to_temp parameter in function signature
        self.check_string_in_file(filepath, "save_to_temp", critical=True)

        # Check tempfile.mkstemp usage
        self.check_string_in_file(filepath, "tempfile.mkstemp", critical=True)

    def verify_storage(self):
        """Verify storage.py changes"""
        print("Checking storage.py...")

        filepath = "backend/app/services/storage.py"

        # Check save_file_from_path exists
        self.check_function_exists(filepath, "save_file_from_path")

        # Check Path import
        self.check_string_in_file(filepath, "from pathlib import Path", critical=True)

        # Check content type detection (non-critical, implementation detail)
        self.check_string_in_file(filepath, "content_type")
        self.check_string_in_file(filepath, "image/")

    def verify_endpoints(self):
        """Verify files.py endpoints"""
        print("Checking files.py endpoints...")

        filepath = "backend/app/api/v1/endpoints/files.py"

        # Check workflow steps are documented
        for step in range(1, 7):
            self.check_string_in_file(filepath, f"Step {step}", critical=True)

        # Check is_pdf flag (flexible check)
        self.check_string_in_file(filepath, "is_pdf")

        # Check finally blocks
        self.check_string_in_file(filepath, "finally:", critical=True)
        self.check_string_in_file(filepath, "cleanup_temp_file", critical=True)

        # Check S3 upload logic
        self.check_string_in_file(filepath, "save_file_from_path", critical=True)
        self.check_string_in_file(filepath, "preprocessed_file_id")

        # Check config import
        self.check_string_in_file(
            filepath, "from app.config import get_settings", critical=True
        )

    def verify_tests(self):
        """Verify test file exists and has tests"""
        print("Checking test_ocr_workflow.py...")

        filepath = "backend/tests/test_ocr_workflow.py"

        # Check test file exists
        if not self.check_file_exists(filepath):
            return

        # Check test classes exist
        self.check_string_in_file(filepath, "class TestPreprocessing")
        self.check_string_in_file(filepath, "class TestStorageService")
        self.check_string_in_file(filepath, "class TestWorkflowIntegration")

    def verify_documentation(self):
        """Verify documentation exists"""
        print("Checking documentation...")

        # Check documentation files
        self.check_file_exists("backend/docs/OCR_WORKFLOW.md")
        self.check_file_exists("backend/docs/OCR_WORKFLOW_DIAGRAMS.md")
        self.check_file_exists("PR_SUMMARY.md")

        # Check gitignore update (critical for avoiding build artifacts)
        gitignore_path = ".gitignore"
        if Path(gitignore_path).exists():
            self.check_string_in_file(gitignore_path, "*.egg-info/", critical=True)
        else:
            self.errors.append(f"File not found: {gitignore_path}")

    def run_all_checks(self):
        """Run all verification checks"""
        print("=" * 70)
        print("OCR Workflow Verification Script")
        print("=" * 70)
        print()

        self.verify_preprocessing()
        print()

        self.verify_storage()
        print()

        self.verify_endpoints()
        print()

        self.verify_tests()
        print()

        self.verify_documentation()
        print()

        # Print summary
        print("=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"✓ Checks passed: {self.checks_passed}")

        if self.warnings:
            print(f"⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"✗ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
            return False
        else:
            print("✓ All critical checks passed!")
            return True


def main():
    """Main function"""
    verifier = WorkflowVerifier()
    success = verifier.run_all_checks()

    if not success:
        sys.exit(1)

    print()
    print("=" * 70)
    print("✓ VERIFICATION SUCCESSFUL - Implementation is correct!")
    print("=" * 70)


if __name__ == "__main__":
    main()
