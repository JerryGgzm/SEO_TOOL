"""运行测试脚本"""
import subprocess
import sys
import os

def run_tests():
    """运行所有测试"""
    # 确保我们在正确的目录中
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v",  # 详细输出
        "--tb=short"  # 简短的错误追踪
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")

if __name__ == "__main__":
    run_tests() 