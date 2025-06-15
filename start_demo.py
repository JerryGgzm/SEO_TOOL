#!/usr/bin/env python3
"""
演示启动脚本
============

这是一个简化的启动脚本，帮助您快速运行完整工作流程演示。

使用方法:
    python start_demo.py

该脚本会：
1. 检查环境配置
2. 启动API服务器（如果需要）
3. 运行完整演示流程
"""

import os
import sys
import subprocess
import time
import signal
import threading
from typing import Optional

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def check_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True

def find_main_app_file() -> Optional[str]:
    """查找主应用程序文件"""
    possible_files = [
        'main.py',
        'app.py', 
        'server.py',
        'api/main.py',
        'core/main.py'
    ]
    
    for file_path in possible_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            return file_path
    
    return None

def start_server() -> Optional[subprocess.Popen]:
    """启动API服务器"""
    print("🚀 启动API服务器...")
    
    # 检查是否已有服务器运行
    if check_port_in_use(8000):
        print("✅ 检测到端口8000已有服务运行")
        return None
    
    # 查找主应用程序文件
    main_file = find_main_app_file()
    if not main_file:
        print("❌ 未找到主应用程序文件")
        print("请确保有以下文件之一: main.py, app.py, server.py")
        return None
    
    try:
        # 尝试使用uvicorn启动
        if main_file.endswith('.py'):
            module_name = main_file.replace('/', '.').replace('.py', '')
            cmd = ['uvicorn', f'{module_name}:app', '--host', '0.0.0.0', '--port', '8000']
        else:
            cmd = ['python', main_file]
            
        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root
        )
        
        # 等待服务器启动
        print("等待服务器启动...")
        time.sleep(3)
        
        # 检查服务器是否成功启动
        if process.poll() is None:  # 进程仍在运行
            print("✅ API服务器启动成功")
            return process
        else:
            print("❌ API服务器启动失败")
            stdout, stderr = process.communicate()
            print(f"标准输出: {stdout.decode()}")
            print(f"错误输出: {stderr.decode()}")
            return None
            
    except FileNotFoundError:
        print("❌ 未找到uvicorn，请安装: pip install uvicorn")
        return None
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        return None

def setup_environment():
    """设置环境"""
    print("🔧 检查环境配置...")
    
    # 检查必需的包
    required_packages = ['requests', 'dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必需的包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    # 检查环境变量文件
    env_file = os.path.join(project_root, '.env')
    if not os.path.exists(env_file):
        print("⚠️  未找到.env文件,将创建示例文件")
        create_example_env()
    
    print("✅ 环境配置检查完成")
    return True

def create_example_env():
    """创建示例环境变量文件"""
    env_content = """# Twitter API配置
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
TWITTER_REDIRECT_URI=http://localhost:8000/auth/twitter/callback

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/ideation_db

# 安全配置
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key

# AI配置 (可选)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 调试模式
DEBUG=true
"""
    
    env_file = os.path.join(project_root, '.env.example')
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"📝 已创建示例环境文件: {env_file}")
    print("请复制为.env文件并填入真实配置")

def run_demo():
    """运行演示"""
    print("🎯 启动完整工作流程演示...")
    
    try:
        # 运行演示脚本
        cmd = [sys.executable, 'demo_complete_workflow.py', '--demo']
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 运行演示时出错: {e}")
        return False

def cleanup_server(server_process: Optional[subprocess.Popen]):
    """清理服务器进程"""
    if server_process and server_process.poll() is None:
        print("\n🛑 正在关闭API服务器...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✅ API服务器已关闭")
        except subprocess.TimeoutExpired:
            print("⚠️  强制关闭API服务器...")
            server_process.kill()

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n🛑 接收到中断信号，正在清理...")
    sys.exit(0)

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 SEO工具完整工作流程演示")
    print("=" * 60)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    server_process = None
    
    try:
        # 1. 环境设置
        if not setup_environment():
            sys.exit(1)
        
        # 2. 启动服务器
        server_process = start_server()
        
        # 3. 运行演示
        success = run_demo()
        
        if success:
            print("\n🎉 演示完成！")
        else:
            print("\n❌ 演示失败")
            
    except KeyboardInterrupt:
        print("\n⚠️  演示被用户中断")
    finally:
        cleanup_server(server_process)
    
    print("\n感谢使用SEO工具演示系统！")

if __name__ == "__main__":
    main() 