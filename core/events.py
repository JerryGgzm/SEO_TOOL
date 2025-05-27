"""事件驱动通信机制"""
from typing import Dict, List, Callable, Any
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    """事件基类"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventHandler(ABC):
    """事件处理器抽象基类"""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """处理事件"""
        pass


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._sync_handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """订阅事件（异步处理器）"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def subscribe_sync(self, event_name: str, handler: Callable) -> None:
        """订阅事件（同步处理器）"""
        if event_name not in self._sync_handlers:
            self._sync_handlers[event_name] = []
        self._sync_handlers[event_name].append(handler)
    
    async def publish(self, event: Event) -> None:
        """发布事件"""
        # 处理异步处理器
        if event.name in self._handlers:
            tasks = [handler.handle(event) for handler in self._handlers[event.name]]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理同步处理器
        if event.name in self._sync_handlers:
            for handler in self._sync_handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    # 记录错误但不中断其他处理器
                    print(f"Error in sync handler: {e}")
    
    def publish_sync(self, event: Event) -> None:
        """同步发布事件"""
        if event.name in self._sync_handlers:
            for handler in self._sync_handlers[event.name]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in sync handler: {e}")


# 全局事件总线实例
event_bus = EventBus() 