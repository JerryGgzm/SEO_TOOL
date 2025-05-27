"""自定义异常类"""


class IdeationException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(IdeationException):
    """配置错误"""
    pass


class TwitterAPIError(IdeationException):
    """Twitter API错误"""
    pass


class ContentGenerationError(IdeationException):
    """内容生成错误"""
    pass


class DatabaseError(IdeationException):
    """数据库错误"""
    pass


class ValidationError(IdeationException):
    """验证错误"""
    pass


class AuthenticationError(IdeationException):
    """认证错误"""
    pass


class RateLimitError(IdeationException):
    """频率限制错误"""
    pass


class AnalyticsError(IdeationException):
    """分析模块错误"""
    pass


class SchedulingError(IdeationException):
    """调度错误"""
    pass


class RulesEngineError(IdeationException):
    """规则引擎错误"""
    pass 