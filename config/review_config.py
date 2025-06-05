# conftest.py - Pytest configuration
"""
Global pytest configuration for review optimization module tests
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test_secret_key",
        "TESTING": True
    }

@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """Mock external dependencies automatically for all tests"""
    with patch.multiple(
        'modules.content_generation',
        ContentGenerationService=Mock,
        create=True
    ), patch.multiple(
        'modules.scheduling_posting', 
        SchedulingPostingService=Mock,
        create=True
    ):
        yield

# requirements-test.txt
"""
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
sqlalchemy>=1.4.0
pydantic>=1.10.0
fastapi>=0.95.0
"""

# test_runner.py
"""
Test runner script for review optimization module
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with coverage"""
    
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install test dependencies
    print("Installing test dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "-r", "../requirements.txt"
    ], check=True)
    
    # Run tests with coverage
    print("\nRunning tests...")
    test_commands = [
        # Run basic tests
        [sys.executable, "-m", "pytest", "test_review_optimization.py", "-v"],
        
        # Run with coverage
        [sys.executable, "-m", "pytest", "test_review_optimization.py", 
         "--cov=modules.review_optimization", "--cov-report=html", "--cov-report=term"],
        
        # Run specific test categories
        [sys.executable, "-m", "pytest", "test_review_optimization.py::TestReviewModels", "-v"],
        [sys.executable, "-m", "pytest", "test_review_optimization.py::TestReviewOptimizationRepository", "-v"],
        [sys.executable, "-m", "pytest", "test_review_optimization.py::TestReviewOptimizationService", "-v"],
    ]
    
    for cmd in test_commands:
        print(f"\nRunning: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Test command failed: {e}")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            return False
    
    print("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)