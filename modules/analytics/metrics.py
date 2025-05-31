"""Define metrics"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class AnalyticsMetrics:
    """Analytics metrics"""
    metric_name: str
    value: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    change_percentage: float
    period_comparison: Dict[str, float]
    timestamp: datetime