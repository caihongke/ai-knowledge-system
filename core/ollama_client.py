"""Ollama 本地大模型客户端

提供与本地 Ollama 服务的交互能力，支持对话、模型管理等功能。
"""

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class OllamaMessage:
    """对话消息"""

    role: str  # system, user, assistant
    content: str


class OllamaClient:
    """Ollama 客户端"""

    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5:7b"

    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = host or self.DEFAULT_HOST
        self.model = model or self.DEFAULT_MODEL
        self._available = None

    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        if self._available is not None:
            return self._available
        try:
            req = urllib.request.Request(
                f"{self.host}/api/tags",
                method="GET",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                self._available = resp.status == 200
                return self._available
        except Exception:
            self._available = False
            return False

    def list_models(self) -> list[dict]:
        """获取已安装的模型列表"""
        try:
            req = urllib.request.Request(
                f"{self.host}/api/tags",
                method="GET",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("models", [])
        except Exception:
            return []

    def has_model(self, model_name: str) -> bool:
        """检查指定模型是否已安装"""
        models = self.list_models()
        return any(m.get("name") == model_name or m.get("model") == model_name for m in models)

    def pull_model(self, model_name: str) -> Iterator[str]:
        """拉取模型（流式输出进度）"""
        try:
            data = json.dumps({"name": model_name}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/pull",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "status" in chunk:
                                yield chunk["status"]
                            if "completed" in chunk and chunk.get("total"):
                                pct = int(chunk["completed"] / chunk["total"] * 100)
                                yield f"下载中... {pct}%"
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"错误: {e}"

    def chat(self, messages: list[OllamaMessage], stream: bool = False) -> str | Iterator[str]:
        """发送对话请求

        Args:
            messages: 对话历史
            stream: 是否流式输出

        Returns:
            完整回复文本，或流式生成器

        """
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        if stream:
            return self._chat_stream(req)
        return self._chat_sync(req)

    def _chat_sync(self, req: urllib.request.Request) -> str:
        """同步对话（一次性返回）"""
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                full_response = []
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                full_response.append(chunk["message"]["content"])
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                return "".join(full_response)
        except urllib.error.HTTPError as e:
            return f"[错误] HTTP {e.code}: {e.reason}"
        except Exception as e:
            return f"[错误] 请求失败: {e}"

    def _chat_stream(self, req: urllib.request.Request) -> Iterator[str]:
        """流式对话（逐字返回）"""
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"[错误] {e}"

    def generate(self, prompt: str, system: str | None = None) -> str:
        """简单文本生成（单次问答）

        Args:
            prompt: 用户输入
            system: 系统提示词（可选）

        Returns:
            AI 回复文本

        """
        messages = []
        if system:
            messages.append(OllamaMessage(role="system", content=system))
        messages.append(OllamaMessage(role="user", content=prompt))
        return self.chat(messages, stream=False)


class OllamaHelper:
    """Ollama 辅助工具类"""

    @staticmethod
    def get_status() -> dict:
        """获取 Ollama 服务状态"""
        client = OllamaClient()
        available = client.is_available()
        models = client.list_models() if available else []
        return {
            "available": available,
            "host": client.host,
            "default_model": client.DEFAULT_MODEL,
            "installed_models": [m.get("name", m.get("model", "unknown")) for m in models],
            "model_count": len(models),
        }

    @staticmethod
    def recommend_model() -> str:
        """根据系统配置推荐模型"""
        import psutil

        mem_gb = psutil.virtual_memory().total / (1024**3)

        # 检测是否有 NVIDIA GPU
        has_gpu = False
        try:
            import subprocess
            result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=2)
            has_gpu = result.returncode == 0
        except Exception:
            pass

        if has_gpu and mem_gb >= 16:
            return "qwen2.5:14b"  # 大模型，质量更好
        if mem_gb >= 8:
            return "qwen2.5:7b"   # 平衡选择
        if mem_gb >= 4:
            return "qwen2.5:1.8b" # 轻量级
        return "phi3:mini"    # 超轻量


# 便捷函数
def quick_ask(prompt: str, system: str | None = None, model: str | None = None) -> str:
    """快速提问，无需实例化客户端"""
    client = OllamaClient(model=model)
    if not client.is_available():
        return "[错误] Ollama 服务未启动，请先运行 `ollama serve`"
    return client.generate(prompt, system=system)


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("Ollama 客户端测试")
    print("=" * 50)

    status = OllamaHelper.get_status()
    print(f"\n服务状态: {'在线' if status['available'] else '离线'}")
    print(f"服务地址: {status['host']}")
    print(f"默认模型: {status['default_model']}")
    print(f"已安装模型: {', '.join(status['installed_models']) or '无'}")

    if status["available"]:
        print(f"\n推荐模型: {OllamaHelper.recommend_model()}")
        print("\n测试对话...")
        client = OllamaClient()
        response = client.generate("你好，请用一句话介绍自己。", system="你是AI助手，回答简洁。")
        print(f"回复: {response}")
