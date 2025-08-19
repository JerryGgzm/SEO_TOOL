#!/usr/bin/env python3
"""
简单测试DataFlowManager的方法
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple():
    """简单测试"""
    try:
        # 直接导入模块
        import database.dataflow_manager
        
        # 获取类
        DataFlowManager = database.dataflow_manager.DataFlowManager
        
        # 检查方法
        print("检查方法:")
        print(f"delete_content_draft: {hasattr(DataFlowManager, 'delete_content_draft')}")
        print(f"delete_scheduled_content: {hasattr(DataFlowManager, 'delete_scheduled_content')}")
        print(f"delete_founder_data: {hasattr(DataFlowManager, 'delete_founder_data')}")
        
        # 获取所有方法
        all_methods = [m for m in dir(DataFlowManager) if not m.startswith('_')]
        delete_methods = [m for m in all_methods if 'delete' in m.lower()]
        print(f"\n所有删除方法: {delete_methods}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple() 