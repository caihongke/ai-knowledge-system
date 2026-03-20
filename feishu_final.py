import requests
import json
import sys
import time
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ========== 基础配置（从环境变量读取，避免凭证泄露） ==========
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
# 关闭日期文件夹（先跑通基础上传，后续可开启）
CREATE_DATE_FOLDER = False
# 网络超时重试次数
RETRY_TIMES = 3
# =============================

def get_token():
    """获取飞书租户Token，带重试机制"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    
    for i in range(RETRY_TIMES):
        try:
            resp = requests.post(url, json=data, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0:
                print(f"❌ Token获取失败（第{i+1}次）: {result}")
                time.sleep(1)
                continue
            return result["tenant_access_token"]
        except Exception as e:
            print(f"❌ Token请求异常（第{i+1}次）: {e}")
            time.sleep(1)
    return None

def upload_markdown_file(token, content, title):
    """极简版上传：只保留必填参数，避免400错误"""
    # 1. 生成带时间戳的文件名（避免重名）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{title}_{timestamp}.md"
    
    # 2. 构造上传参数（只传必填项，避免参数错误）
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"  # 确认是v1（数字1）
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'file_name': (None, file_name, 'text/plain'),
        'parent_type': (None, 'explorer', 'text/plain'),
        'size': (None, str(len(content.encode('utf-8'))), 'text/plain'),
        'file': (file_name, content.encode('utf-8'), 'text/markdown')
    }
    
    # 3. 带重试的上传逻辑
    for i in range(RETRY_TIMES):
        try:
            resp = requests.post(url, headers=headers, files=files, timeout=20)
            print(f"📄 上传响应状态码: {resp.status_code}")
            result = resp.json()
            
            if result.get("code") != 0:
                print(f"❌ 文件上传失败（第{i+1}次）: {result}")
                time.sleep(1)
                continue
            
            # 4. 生成文件访问链接
            file_token = result["data"]["file_token"]
            file_url = f"https://open.feishu.cn/file/{file_token}"
            print(f"✅ 文件上传成功！飞书链接：{file_url}")
            return file_url
        except Exception as e:
            print(f"❌ 文件上传异常（第{i+1}次）: {e}")
            time.sleep(1)
    return ""

def main():
    # 修复：设置脚本编码为UTF-8，避免中文乱码
    sys.stdout.reconfigure(encoding='utf-8')
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="上传Markdown文件到飞书云盘（修复版）")
    parser.add_argument("--content", type=str, help="报告内容（Markdown格式）")
    parser.add_argument("--title", type=str, default="测试报告", help="文件标题")
    parser.add_argument("--file", type=str, help="本地Markdown文件路径（绝对/相对路径均可）")
    args = parser.parse_args()
    
    # 1. 读取内容（自动识别路径，兼容相对/绝对路径）
    content = ""
    if args.content:
        content = args.content
    elif args.file:
        # 修复：自动补全文件绝对路径
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print("❌ 请指定 --content 或 --file 参数！")
        print("示例：python upload_to_feishu.py --file ./test.md --title 测试文档")
        sys.exit(1)
    
    # 2. 获取Token
    token = get_token()
    if not token:
        print("❌ Token获取失败，终止上传")
        sys.exit(1)
    print("✅ Token获取成功")
    
    # 3. 上传文件（极简版，避免参数错误）
    file_url = upload_markdown_file(token, content, args.title)
    if not file_url:
        print("\n❌ 文件上传最终失败，请检查飞书配置或网络")
        sys.exit(1)

if __name__ == "__main__":
    main()