"""
Database Configuration Module

This module provides comprehensive database configuration for the Ideation System.
It handles connection parameters, pooling settings, and environment-specific configurations.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, quote_plus
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration class with validation and environment support"""
    
    def __init__(self):
        # First set all basic attributes
        self.DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
        self.DATABASE_PORT = int(os.getenv('DATABASE_PORT', '5432'))
        self.DATABASE_NAME = os.getenv('DATABASE_NAME', 'ideation_db')
        self.DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
        self.DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'Tianjin@0430')  # Replace with your password
        
        # Build DATABASE_URL (now all required attributes are defined)
        self.DATABASE_URL = self._get_database_url()
        
        # Connection pool settings
        self.POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
        self.MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
        self.POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))
        self.POOL_RECYCLE = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        self.POOL_PRE_PING = os.getenv('DATABASE_POOL_PRE_PING', 'true').lower() == 'true'
        
        # Connection behavior settings
        self.ECHO_SQL = os.getenv('DATABASE_ECHO_SQL', 'false').lower() == 'true'
        self.AUTOCOMMIT = os.getenv('DATABASE_AUTOCOMMIT', 'false').lower() == 'true'
        self.AUTOFLUSH = os.getenv('DATABASE_AUTOFLUSH', 'false').lower() == 'true'
        
        # Query and transaction settings
        self.QUERY_TIMEOUT = int(os.getenv('DATABASE_QUERY_TIMEOUT', '30'))
        self.STATEMENT_TIMEOUT = int(os.getenv('DATABASE_STATEMENT_TIMEOUT', '60'))
        self.ISOLATION_LEVEL = os.getenv('DATABASE_ISOLATION_LEVEL', 'READ_COMMITTED')
        
        # Migration and maintenance settings
        self.MIGRATION_TIMEOUT = int(os.getenv('DATABASE_MIGRATION_TIMEOUT', '300'))
        self.BACKUP_RETENTION_DAYS = int(os.getenv('DATABASE_BACKUP_RETENTION_DAYS', '30'))
        
        # SSL and security settings
        self.SSL_MODE = os.getenv('DATABASE_SSL_MODE', 'prefer')
        self.SSL_CERT = os.getenv('DATABASE_SSL_CERT')
        self.SSL_KEY = os.getenv('DATABASE_SSL_KEY')
        self.SSL_ROOT_CERT = os.getenv('DATABASE_SSL_ROOT_CERT')
        
        # Environment-specific settings
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Logging settings
        self.LOG_SLOW_QUERIES = os.getenv('DATABASE_LOG_SLOW_QUERIES', 'true').lower() == 'true'
        self.SLOW_QUERY_THRESHOLD = float(os.getenv('DATABASE_SLOW_QUERY_THRESHOLD', '1.0'))
        
    def _get_database_url(self) -> str:
        """Build database URL from environment variables"""
        # URL 编码密码以处理特殊字符
        encoded_password = quote_plus(self.DATABASE_PASSWORD)
        return f"postgresql://{self.DATABASE_USER}:{encoded_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get SQLAlchemy connection parameters"""
        params = {
            'url': self.DATABASE_URL,
            'pool_size': self.POOL_SIZE,
            'max_overflow': self.MAX_OVERFLOW,
            'pool_timeout': self.POOL_TIMEOUT,
            'pool_recycle': self.POOL_RECYCLE,
            'pool_pre_ping': self.POOL_PRE_PING,
            'echo': self.ECHO_SQL,
        }
        
        # Add connection arguments
        connect_args = {}
        
        # Add SSL configuration if specified
        if self.SSL_MODE and self.SSL_MODE != 'disable':
            connect_args['sslmode'] = self.SSL_MODE
            
            if self.SSL_CERT:
                connect_args['sslcert'] = self.SSL_CERT
            if self.SSL_KEY:
                connect_args['sslkey'] = self.SSL_KEY
            if self.SSL_ROOT_CERT:
                connect_args['sslrootcert'] = self.SSL_ROOT_CERT
        
        # Add timeout settings
        if self.QUERY_TIMEOUT:
            connect_args['connect_timeout'] = self.QUERY_TIMEOUT
        
        if connect_args:
            params['connect_args'] = connect_args
        
        return params
    
    def get_session_params(self) -> Dict[str, Any]:
        """Get SQLAlchemy session parameters"""
        return {
            'autocommit': self.AUTOCOMMIT,
            'autoflush': self.AUTOFLUSH,
            'expire_on_commit': True
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate database configuration"""
        errors = []
        warnings = []
        
        # Validate required parameters
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        if not self.DATABASE_NAME:
            errors.append("DATABASE_NAME is required")
        
        # Validate connection pool settings
        if self.POOL_SIZE < 1:
            errors.append("POOL_SIZE must be at least 1")
        
        if self.MAX_OVERFLOW < 0:
            errors.append("MAX_OVERFLOW cannot be negative")
        
        if self.POOL_TIMEOUT < 1:
            errors.append("POOL_TIMEOUT must be at least 1 second")
        
        # Validate port
        if not 1 <= self.DATABASE_PORT <= 65535:
            errors.append("DATABASE_PORT must be between 1 and 65535")
        
        # Validate isolation level
        valid_isolation_levels = [
            'AUTOCOMMIT', 'READ_UNCOMMITTED', 'READ_COMMITTED', 
            'REPEATABLE_READ', 'SERIALIZABLE'
        ]
        if self.ISOLATION_LEVEL not in valid_isolation_levels:
            errors.append(f"ISOLATION_LEVEL must be one of: {', '.join(valid_isolation_levels)}")
        
        # Performance warnings
        if self.POOL_SIZE > 50:
            warnings.append("POOL_SIZE is quite large (>50), consider if this is necessary")
        
        if self.MAX_OVERFLOW > 100:
            warnings.append("MAX_OVERFLOW is very large (>100), this might cause resource issues")
        
        if self.ENVIRONMENT == 'production' and self.ECHO_SQL:
            warnings.append("ECHO_SQL is enabled in production, this may impact performance")
        
        if not self.SSL_MODE or self.SSL_MODE == 'disable':
            if self.ENVIRONMENT == 'production':
                warnings.append("SSL is disabled in production environment")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database connection information (without sensitive data)"""
        parsed_url = urlparse(self.DATABASE_URL)
        return {
            'host': parsed_url.hostname or self.DATABASE_HOST,
            'port': parsed_url.port or self.DATABASE_PORT,
            'database': parsed_url.path.lstrip('/') or self.DATABASE_NAME,
            'username': parsed_url.username or self.DATABASE_USER,
            'ssl_mode': self.SSL_MODE,
            'pool_size': self.POOL_SIZE,
            'max_overflow': self.MAX_OVERFLOW,
            'environment': self.ENVIRONMENT
        }
    
    def get_maintenance_config(self) -> Dict[str, Any]:
        """Get configuration for database maintenance tasks"""
        return {
            'migration_timeout': self.MIGRATION_TIMEOUT,
            'backup_retention_days': self.BACKUP_RETENTION_DAYS,
            'log_slow_queries': self.LOG_SLOW_QUERIES,
            'slow_query_threshold': self.SLOW_QUERY_THRESHOLD,
            'query_timeout': self.QUERY_TIMEOUT,
            'statement_timeout': self.STATEMENT_TIMEOUT
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == 'development'
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.ENVIRONMENT.lower() in ['test', 'testing']


class TestDatabaseConfig(DatabaseConfig):
    """Test-specific database configuration"""
    
    def __init__(self):
        super().__init__()
        
        # Override settings for testing
        self.DATABASE_NAME = os.getenv('TEST_DATABASE_NAME', 'ideation_test_db')
        self.POOL_SIZE = int(os.getenv('TEST_DATABASE_POOL_SIZE', '5'))
        self.MAX_OVERFLOW = int(os.getenv('TEST_DATABASE_MAX_OVERFLOW', '10'))
        self.ECHO_SQL = os.getenv('TEST_DATABASE_ECHO_SQL', 'false').lower() == 'true'
        
        # Rebuild URL with test database name
        self.DATABASE_URL = self._get_test_database_url()
    
    def _get_test_database_url(self) -> str:
        """Build test database URL"""
        test_url = os.getenv('TEST_DATABASE_URL')
        if test_url:
            return test_url
        
        # Build URL with test database name
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', '')
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{self.DATABASE_NAME}"
        else:
            return f"postgresql://{user}@{host}:{port}/{self.DATABASE_NAME}"


# Environment-specific configurations
def get_config() -> DatabaseConfig:
    """Get database configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env in ['test', 'testing']:
        return TestDatabaseConfig()
    else:
        return DatabaseConfig()


# Global configuration instance
database_config = get_config()

# Configuration validation on import
_validation_result = database_config.validate_config()
if not _validation_result['valid']:
    logger.error(f"Database configuration errors: {_validation_result['errors']}")
    if os.getenv('STRICT_CONFIG_VALIDATION', 'false').lower() == 'true':
        raise ValueError(f"Invalid database configuration: {_validation_result['errors']}")

if _validation_result['warnings']:
    for warning in _validation_result['warnings']:
        logger.warning(f"Database configuration warning: {warning}")


# Utility functions
def get_alembic_config() -> Dict[str, str]:
    """Get configuration for Alembic migrations"""
    return {
        'sqlalchemy.url': database_config.DATABASE_URL,
        'script_location': 'migrations',
        'file_template': '%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s',
        'timezone': 'UTC'
    }

def get_connection_string_for_tool(tool_name: str) -> str:
    """Get connection string formatted for specific database tools"""
    if tool_name.lower() == 'psql':
        return f"postgresql://{database_config.DATABASE_USER}@{database_config.DATABASE_HOST}:{database_config.DATABASE_PORT}/{database_config.DATABASE_NAME}"
    elif tool_name.lower() == 'pg_dump':
        return f"postgresql://{database_config.DATABASE_USER}@{database_config.DATABASE_HOST}:{database_config.DATABASE_PORT}/{database_config.DATABASE_NAME}"
    else:
        return database_config.DATABASE_URL

def log_database_startup_info():
    """Log database configuration information at startup"""
    info = database_config.get_database_info()
    logger.info(f"Database configuration loaded:")
    logger.info(f"  Host: {info['host']}:{info['port']}")
    logger.info(f"  Database: {info['database']}")
    logger.info(f"  Username: {info['username']}")
    logger.info(f"  Environment: {info['environment']}")
    logger.info(f"  Pool Size: {info['pool_size']}")
    logger.info(f"  SSL Mode: {info['ssl_mode']}")

# Export public interface
__all__ = [
    'DatabaseConfig',
    'TestDatabaseConfig', 
    'database_config',
    'get_config',
    'get_alembic_config',
    'get_connection_string_for_tool',
    'log_database_startup_info'
]