"""飞书上传集成测试 - 验证统一上传脚本"""

import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name} {detail}")
        failed += 1


def run_script(args):
    result = subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        cwd=PROJECT_ROOT, timeout=30,
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    return result.returncode, stdout, stderr


# ====== 1. Token 获取 ======
print("1. Token 获取测试")
code, out, err = run_script(["-c", """
import sys; sys.stdout.reconfigure(encoding='utf-8')
from feishu_upload import get_token
token = get_token()
print(f"token_ok={token is not None}")
print(f"token_len={len(token) if token else 0}")
"""])
check("Token 获取成功", "token_ok=True" in out)
check("Token 非空", "token_len=0" not in out)


# ====== 2. --file 上传 ======
print("\n2. feishu_upload.py --file 上传")
code, out, err = run_script(["feishu_upload.py", "--file", "test.md", "--title", "集成测试_file"])
check("退出码为 0", code == 0, f"(got {code})")
check("Token 成功", "[OK] Token" in out)
check("上传成功", "上传成功" in out)
check("返回飞书链接", "open.feishu.cn/file/" in out)


# ====== 3. --content 上传 ======
print("\n3. feishu_upload.py --content 上传")
code, out, err = run_script([
    "feishu_upload.py", "--content", "# 测试\n内容测试", "--title", "集成测试_content",
])
check("退出码为 0", code == 0, f"(got {code})")
check("上传成功", "上传成功" in out)


# ====== 4. 模块导入测试 ======
print("\n4. 模块导入测试")
code, out, err = run_script(["-c", """
import sys; sys.stdout.reconfigure(encoding='utf-8')
from feishu_upload import get_token, upload, upload_file, read_file
print("import_ok=True")
token = get_token()
ft, url = upload(token, "# 模块测试\\n测试内容", "模块导入测试")
print(f"upload_ok={url is not None}")
"""])
check("模块可导入", "import_ok=True" in out)
check("模块上传成功", "upload_ok=True" in out)


# ====== 5. 中文文件上传 ======
print("\n5. 中文内容上传")
test_cn = os.path.join(PROJECT_ROOT, "tests", "tmp_中文.md")
with open(test_cn, "w", encoding="utf-8") as f:
    f.write("# 中文标题\n\n- 列表项\n- **加粗**\n")
code, out, err = run_script(["feishu_upload.py", "--file", test_cn, "--title", "中文测试"])
check("中文上传成功", "上传成功" in out)
if os.path.exists(test_cn):
    os.remove(test_cn)


# ====== 6. 错误处理 ======
print("\n6. 错误处理")
code, out, err = run_script(["feishu_upload.py"])
check("无参数退出非 0", code != 0)
code, out, err = run_script(["feishu_upload.py", "--file", "不存在.md"])
check("不存在文件退出非 0", code != 0)


# ====== 汇总 ======
print(f"\n{'='*50}")
print(f"飞书上传集成测试: {passed} 通过, {failed} 失败")
print(f"{'='*50}")
sys.exit(1 if failed else 0)
