#!/usr/bin/env python3
"""Test runner script for the MiniMart AI Inventory Management System."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print("Error:", e.stderr)
        if e.stdout:
            print("Output:", e.stdout)
        return False


def main():
    """Run all tests and checks."""
    print("🚀 MiniMart AI Inventory Management System - Test Suite")
    print("="*60)
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    tests_passed = 0
    total_tests = 0
    
    # 1. Backend Tests
    total_tests += 1
    if run_command("python -m pytest tests/ -v --tb=short", "Backend Unit Tests"):
        tests_passed += 1
    
    # 2. API Tests
    total_tests += 1
    if run_command("python -m pytest tests/test_api.py -v --tb=short", "API Integration Tests"):
        tests_passed += 1
    
    # 3. Agent Tests
    total_tests += 1
    if run_command("python -m pytest tests/test_agents.py -v --tb=short", "AI Agent Tests"):
        tests_passed += 1
    
    # 4. Code Quality Checks
    total_tests += 1
    if run_command("python -m flake8 app/ --max-line-length=100 --ignore=E203,W503", "Code Style Check"):
        tests_passed += 1
    
    # 5. Type Checking
    total_tests += 1
    if run_command("python -m mypy app/ --ignore-missing-imports", "Type Checking"):
        tests_passed += 1
    
    # 6. Security Check
    total_tests += 1
    if run_command("python -m bandit -r app/ -f json -o security_report.json", "Security Analysis"):
        tests_passed += 1
    
    # 7. Database Initialization Test
    total_tests += 1
    if run_command("python app/database/init_db.py", "Database Initialization"):
        tests_passed += 1
    
    # 8. Frontend Tests (if available)
    frontend_path = Path("frontend")
    if frontend_path.exists():
        total_tests += 1
        if run_command("cd frontend && npm test -- --watchAll=false", "Frontend Tests"):
            tests_passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! System is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
