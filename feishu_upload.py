"""飞书云盘文件上传工具（统一版）

合并自 feishu_final.py + feishu_upload.py，保留：
- 重试机制（3次）
- 多编码检测（UTF-8/GBK/UTF-16）
- --file / --content 双模式
- 可作为模块导入（供 CLI sync 命令调用）
"""

import requests
import sys
import time
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

RETRY_TIMES = 3


def get_token(app_id=None, app_secret=None):
    """获取飞书租户 Token，带重试"""
    app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
    app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    for i in range(RETRY_TIMES):
        try:
            resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 0:
                return result["tenant_access_token"]
            print(f"[WARN] Token 获取失败（第{i+1}次）: {result.get('msg')}")
        except Exception as e:
            print(f"[WARN] Token 请求异常（第{i+1}次）: {e}")
        time.sleep(1)
    return None


def read_file(file_path):
    """读取文件内容，自动检测编码（UTF-8 > GBK > UTF-16）"""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"文件不存在: {abs_path}")

    for enc in ("utf-8", "gbk", "utf-16"):
        try:
            with open(abs_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("", b"", 0, 1, f"无法解码文件: {abs_path}")


def set_file_permission(token, file_token):
    """设置文件分享权限为租户内可读，返回是否成功"""
    url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}/permissions/public"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "access": "tenant_readable"  # 租户内所有人可读
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            print(f"[OK] 文件分享权限设置成功")
            return True
        else:
            print(f"[WARN] 权限设置失败: {result.get('msg')}")
            return False
    except Exception as e:
        print(f"[WARN] 权限设置异常: {e}")
        return False


def upload(token, content, title="上传文件"):
    """上传内容到飞书云盘，返回 (file_token, file_url) 或 (None, None)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{title}_{timestamp}.md"
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
    headers = {"Authorization": f"Bearer {token}"}
    encoded = content.encode("utf-8")
    files = {
        "file_name": (None, file_name, "text/plain"),
        "parent_type": (None, "explorer", "text/plain"),
        "size": (None, str(len(encoded)), "text/plain"),
        "file": (file_name, encoded, "text/markdown"),
    }

    for i in range(RETRY_TIMES):
        try:
            resp = requests.post(url, headers=headers, files=files, timeout=20)
            result = resp.json()
            if result.get("code") == 0:
                ft = result["data"]["file_token"]
                # 设置分享权限
                set_file_permission(token, ft)
                return ft, f"https://open.feishu.cn/file/{ft}"
            print(f"[WARN] 上传失败（第{i+1}次）: {result.get('msg')}")
        except Exception as e:
            print(f"[WARN] 上传异常（第{i+1}次）: {e}")
        time.sleep(1)
    return None, None


def upload_file(token, file_path, title="上传文件"):
    """读取本地文件并上传，返回 (file_token, file_url)"""
    content = read_file(file_path)
    return upload(token, content, title)


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="上传 Markdown 文件到飞书云盘")
    parser.add_argument("--file", type=str, help="本地文件路径")
    parser.add_argument("--content", type=str, help="直接传入内容")
    parser.add_argument("--title", type=str, default="报告", help="文件标题")
    args = parser.parse_args()

    if args.file:
        content = read_file(args.file)
    elif args.content:
        content = args.content
    else:
        print("[ERROR] 请指定 --file 或 --content")
        print("示例: python feishu_upload.py --file ./test.md --title 测试")
        sys.exit(1)

    token = get_token()
    if not token:
        print("[ERROR] Token 获取失败，终止上传")
        sys.exit(1)
    print("[OK] Token 获取成功")

    ft, url = upload(token, content, args.title)
    if url:
        print(f"[OK] 上传成功！飞书链接: {url}")
    else:
        print("[ERROR] 上传最终失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
