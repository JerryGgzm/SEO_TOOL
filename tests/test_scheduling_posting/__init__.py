"""Test package for scheduling_posting module

This package contains comprehensive tests for the scheduling_posting module:

- Unit tests: Test individual functions and methods
- Integration tests: Test end-to-end workflows  
- Performance tests: Test system performance under load
- Model tests: Test data model validation and serialization

Test Categories:
- test_scheduling_service.py: Core service functionality tests
- test_rules_engine.py: Publishing rules validation tests
- test_models.py: Data model and validation tests
- test_publishing_integration.py: End-to-end workflow tests
- test_performance.py: Performance and load tests
- conftest.py: Test configuration and fixtures

Usage:
    # Run all tests
    pytest tests/test_scheduling_posting/
    
    # Run specific test category
    pytest tests/test_scheduling_posting/test_scheduling_service.py
    pytest tests/test_scheduling_posting/test_performance.py
    
    # Run with coverage
    pytest tests/test_scheduling_posting/ --cov=modules.scheduling_posting
    
    # Run performance tests only
    pytest tests/test_scheduling_posting/test_performance.py -v
    
    # Run integration tests
    pytest tests/test_scheduling_posting/test_publishing_integration.py -v
"""

__version__ = "1.0.0"
__author__ = "Test Suite" 