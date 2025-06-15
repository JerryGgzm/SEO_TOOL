"""Twitter API OAuth 2.0测试

这个文件演示如何正确使用OAuth 2.0 Authorization Code Flow with PKCE
来访问Twitter API v2。
"""

import os
import webbrowser
from dotenv import load_dotenv
from modules.twitter_api.auth import TwitterAuth

load_dotenv('.env')

def test_oauth2_flow():
    """测试完整的OAuth 2.0流程"""
    print("🔍 Twitter API OAuth 2.0 测试")
    print("=" * 50)
    
    # 获取环境变量
    client_id = os.getenv('TWITTER_CLIENT_ID')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET')
    
    print(f"Client ID: {client_id[:10] + '...' + client_id[-4:] if client_id and len(client_id) > 14 else client_id or 'N/A'}")
    print(f"Client Secret: {client_secret[:10] + '...' + client_secret[-4:] if client_secret and len(client_secret) > 14 else client_secret or 'N/A'}")
    
    if not client_id or not client_secret:
        print("❌ 缺少必要的凭证")
        print("\n请在.env文件中设置以下变量:")
        print("TWITTER_CLIENT_ID=你的客户端ID")
        print("TWITTER_CLIENT_SECRET=你的客户端密钥")
        return False
    
    try:
        # 初始化Twitter认证
        auth = TwitterAuth(client_id, client_secret)
        
        # 设置回调URL（需要在Twitter开发者平台配置）
        redirect_uri = os.getenv('TWITTER_CALLBACK_URL', 'https://www.trendxseo.com/auth/twitter/callback')
        
        # 请求的权限范围
        scopes = [
            'tweet.read',        # 读取推文
            'tweet.write',       # 发布推文
            'users.read',        # 读取用户信息
            'follows.read',      # 读取关注信息
            'follows.write',     # 关注/取消关注
            'offline.access'     # 获取刷新令牌
        ]
        
        print(f"\n📝 请求的权限范围: {', '.join(scopes)}")
        print(f"🔗 回调URL: {redirect_uri}")
        
        # 生成授权URL
        auth_url, state, code_verifier = auth.get_authorization_url(
            redirect_uri=redirect_uri,
            scopes=scopes
        )
        
        print("\n🌐 授权URL已生成:")
        print(f"State: {state}")
        print(f"Code Verifier: {code_verifier}")
        print(f"授权URL: {auth_url}")
        
        print("\n📋 下一步操作:")
        print("1. 复制上面的授权URL到浏览器中打开")
        print("2. 登录Twitter并授权应用")
        print("3. 授权成功后，你会被重定向到回调URL")
        print("4. 从回调URL中获取 'code' 参数")
        print("5. 使用这个code来交换访问令牌")
        
        # 可选：自动打开浏览器
        user_input = input("\n是否自动打开浏览器? (y/n): ")
        if user_input.lower() == 'y':
            webbrowser.open(auth_url)
        
        return True
        
    except Exception as e:
        print(f"❌ 生成授权URL失败: {str(e)}")
        return False

def exchange_code_for_token():
    """手动交换授权码获取访问令牌"""
    print("\n🔄 交换授权码获取访问令牌")
    print("=" * 50)
    
    client_id = os.getenv('TWITTER_CLIENT_ID')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ 缺少API凭证")
        return
    
    # 用户输入授权码和验证码
    code = input("请输入从回调URL中获取的授权码 (code): ")
    code_verifier = input("请输入之前生成的code_verifier: ")
    redirect_uri = input("请输入回调URL (默认: https://www.trendxseo.com/auth/twitter/callback): ") or os.getenv('TWITTER_CALLBACK_URL', 'https://www.trendxseo.com/auth/twitter/callback')
    
    if not code or not code_verifier:
        print("❌ 授权码和验证码都是必需的")
        return
    
    try:
        auth = TwitterAuth(client_id, client_secret)
        
        # 交换访问令牌
        token_data = auth.exchange_code_for_token(
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri
        )
        
        if token_data:
            print("✅ 成功获取访问令牌!")
            print(f"访问令牌: {token_data.get('access_token', 'N/A')[:20]}...")
            print(f"令牌类型: {token_data.get('token_type', 'N/A')}")
            print(f"有效期(秒): {token_data.get('expires_in', 'N/A')}")
            print(f"刷新令牌: {'是' if token_data.get('refresh_token') else '否'}")
            print(f"权限范围: {token_data.get('scope', 'N/A')}")
            
            # 测试令牌有效性
            access_token = token_data.get('access_token')
            if access_token and auth.validate_user_token(access_token):
                print("✅ 访问令牌验证成功!")
            else:
                print("❌ 访问令牌验证失败")
                
        else:
            print("❌ 获取访问令牌失败")
            
    except Exception as e:
        print(f"❌ 交换令牌失败: {str(e)}")

def main():
    """主函数"""
    print("Twitter API OAuth 2.0 测试工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 生成授权URL")
        print("2. 交换授权码获取访问令牌") 
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ")
        
        if choice == '1':
            test_oauth2_flow()
        elif choice == '2':
            exchange_code_for_token()
        elif choice == '3':
            print("再见!")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main() 