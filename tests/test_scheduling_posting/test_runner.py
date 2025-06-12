#!/usr/bin/env python3
"""Test runner for scheduling_posting module tests

This script provides convenient commands to run different categories of tests
with appropriate configurations and reporting.

Usage:
    python tests/test_scheduling_posting/test_runner.py --help
    python tests/test_scheduling_posting/test_runner.py --unit
    python tests/test_scheduling_posting/test_runner.py --integration  
    python tests/test_scheduling_posting/test_runner.py --performance
    python tests/test_scheduling_posting/test_runner.py --all
    python tests/test_scheduling_posting/test_runner.py --coverage
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with exit code {e.returncode}")
        return False

def run_unit_tests():
    """Run unit tests"""
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_scheduling_posting/test_scheduling_service.py",
        "tests/test_scheduling_posting/test_rules_engine.py", 
        "tests/test_scheduling_posting/test_models.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/test_publishing_integration.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Integration Tests")

def run_performance_tests():
    """Run performance tests"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/test_performance.py", 
        "-v", "--tb=short", "-s"  # -s to show print output for performance metrics
    ]
    return run_command(cmd, "Performance Tests")

def run_all_tests():
    """Run all tests"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "All Tests")

def run_coverage_tests():
    """Run tests with coverage reporting"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/",
        "--cov=modules.scheduling_posting",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]
    return run_command(cmd, "Coverage Tests")

def run_fast_tests():
    """Run fast tests (excluding performance tests)"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/test_scheduling_service.py",
        "tests/test_scheduling_posting/test_rules_engine.py",
        "tests/test_scheduling_posting/test_models.py",
        "tests/test_scheduling_posting/test_publishing_integration.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Fast Tests (No Performance)")

def run_smoke_tests():
    """Run a subset of tests for quick validation"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/test_scheduling_service.py::TestSchedulingService::test_schedule_content_success",
        "tests/test_scheduling_posting/test_rules_engine.py::TestInternalRulesEngine::test_validate_publishing_rules_success",
        "tests/test_scheduling_posting/test_models.py::TestModels::test_schedule_request_validation",
        "tests/test_scheduling_posting/test_publishing_integration.py::TestPublishingIntegration::test_end_to_end_immediate_publishing",
        "-v"
    ]
    return run_command(cmd, "Smoke Tests")

def run_failed_tests():
    """Re-run only failed tests from last run"""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_scheduling_posting/",
        "--lf", "-v"  # --lf = last failed
    ]
    return run_command(cmd, "Failed Tests (Last Failed)")

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = ['pytest', 'pytest-asyncio', 'pytest-cov']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install pytest pytest-asyncio pytest-cov")
        return False
    
    print("✓ All required dependencies are available")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Test runner for scheduling_posting module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --unit                 # Run unit tests only
  %(prog)s --integration          # Run integration tests only  
  %(prog)s --performance          # Run performance tests only
  %(prog)s --all                  # Run all tests
  %(prog)s --coverage             # Run with coverage report
  %(prog)s --fast                 # Run fast tests (no performance)
  %(prog)s --smoke                # Run smoke tests for quick validation
  %(prog)s --failed               # Re-run only failed tests
        """
    )
    
    parser.add_argument('--unit', action='store_true', 
                       help='Run unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance tests')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage reporting')
    parser.add_argument('--fast', action='store_true',
                       help='Run fast tests (excluding performance)')
    parser.add_argument('--smoke', action='store_true',
                       help='Run smoke tests for quick validation')
    parser.add_argument('--failed', action='store_true',
                       help='Re-run only failed tests from last run')
    parser.add_argument('--check-deps', action='store_true',
                       help='Check if required dependencies are installed')
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # If no specific test type specified, show help
    if not any([args.unit, args.integration, args.performance, args.all, 
                args.coverage, args.fast, args.smoke, args.failed, args.check_deps]):
        parser.print_help()
        sys.exit(0)
    
    success = True
    
    if args.check_deps:
        # Already checked above
        sys.exit(0)
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
        
    if args.performance:
        success &= run_performance_tests()
        
    if args.all:
        success &= run_all_tests()
        
    if args.coverage:
        success &= run_coverage_tests()
        
    if args.fast:
        success &= run_fast_tests()
        
    if args.smoke:
        success &= run_smoke_tests()
        
    if args.failed:
        success &= run_failed_tests()
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        print("   Test results look good.")
    else:
        print("❌ Some tests failed!")
        print("   Please review the test output above.")
    print('='*60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 