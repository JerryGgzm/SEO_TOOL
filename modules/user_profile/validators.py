"""Input validation""" 
from typing import List, Optional, Tuple
import re
from pydantic import validator


class UserProfileValidators:
    """User profile validators"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_keywords(keywords: List[str]) -> Tuple[bool, List[str]]:
        """Validate keywords list"""
        issues = []
        
        if not keywords:
            issues.append("Keywords list cannot be empty")
            return False, issues
        
        for keyword in keywords:
            if not keyword.strip():
                issues.append("Keywords cannot be empty")
            elif len(keyword.strip()) > 50:
                issues.append(f"Keyword '{keyword}' cannot exceed 50 characters")
            elif not re.match(r'^[a-zA-Z0-9\s\u4e00-\u9fff_-]+$', keyword.strip()):
                issues.append(f"Keyword '{keyword}' contains invalid characters")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)', re.IGNORECASE)
        return bool(url_pattern.match(url))