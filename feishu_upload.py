import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# ========== 飞书凭证（从环境变量读取） ==========
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FOLDER_TOKEN = os.environ.get("FEISHU_FOLDER_TOKEN", "nodcnxYrKoqJ8BP6vYDB9Ispqjf")
# =================================

def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        if result.get("code") != 0:
            print(f"[ERROR] Token获取失败: {result}")
            return None
        return result["tenant_access_token"]
    except Exception as e:
        print(f"[ERROR] Token请求异常: {e}")
    return None

def upload_file(token, file_path, title="自动上传"):
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"[ERROR] 文件不存在: {abs_path}")
        return None
    
    # ✅ 修复：自动检测编码，兼容 UTF-8 / GBK / UTF-16
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(abs_path, 'r', encoding='gbk') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(abs_path, 'r', encoding='utf-16') as f:
                content = f.read()
    
    file_name = f"{title}_{os.path.basename(abs_path)}"
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'file_name': (None, file_name),
        'parent_type': (None, 'explorer'),
        'size': (None, str(len(content.encode('utf-8')))),
        'file': (file_name, content.encode('utf-8'), 'text/markdown')
    }
    
    try:
        resp = requests.post(url, headers=headers, files=files, timeout=20)
        result = resp.json()
        if result.get("code") == 0:
            file_token = result["data"]["file_token"]
            print(f"[SUCCESS] 上传成功！飞书链接: https://open.feishu.cn/file/{file_token}")
            return file_token
        else:
            print(f"[ERROR] 上传失败: {result}")
    except Exception as e:
        print(f"[ERROR] 请求异常: {e}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python feishu_upload.py 文件名.md [标题]")
        sys.exit(1)
    
    token = get_token()
    if not token:
        sys.exit(1)
    
    upload_file(token, sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "报告")