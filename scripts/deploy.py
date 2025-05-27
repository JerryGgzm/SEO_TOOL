"""部署脚本"""
import subprocess
import sys


def deploy():
    """部署应用"""
    print("开始部署...")
    
    # 安装依赖
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # 初始化数据库
    subprocess.run([sys.executable, "scripts/setup.py"])
    
    print("部署完成！")


if __name__ == "__main__":
    deploy() 