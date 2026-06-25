# -*- coding: utf-8 -*-
"""飞书 RAG 系统配置"""
import os
from pathlib import Path

# 优先级（低→高）：Streamlit secrets → .streamlit/secrets.toml → .env
# Streamlit 的 st.secrets 内部会无条件调用 os.environ[k]=v，因此必须在其之后
# 用 override=True 重新加载 .env，确保本地 .env 始终拥有最高优先级。

# Step 1: Streamlit secrets（最低优先级，仅在 Streamlit Cloud 无 .env 时生效）
def _inject_secrets_from_dict(d: dict):
    """将 secrets dict 注入 os.environ（仅补全空缺，不覆盖已有值）"""
    for k, v in d.items():
        if isinstance(v, str) and (k not in os.environ or not (os.environ.get(k) or "").strip()):
            os.environ[k] = v
        elif isinstance(v, dict):
            _inject_secrets_from_dict(v)  # 嵌套 section

try:
    import streamlit as st
    if hasattr(st, "secrets") and st.secrets:
        # 注意：st.secrets 访问时 Streamlit 内部会调用 _maybe_set_environment_variable
        # 无条件覆盖 os.environ，因此此处只做记录，后续 .env 会以 override=True 覆盖回来
        _inject_secrets_from_dict(dict(st.secrets))
except Exception:
    pass

# Step 2: 本地运行时，手动解析 secrets.toml（优先于 Streamlit secrets）
import re as _re
for _secrets_path in [
    Path(__file__).resolve().parent / ".streamlit" / "secrets.toml",
    Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml",
]:
    if _secrets_path.exists():
        try:
            _text = _secrets_path.read_text(encoding="utf-8")
            for _m in _re.finditer(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"', _text, _re.M):
                _k, _v = _m.group(1), _m.group(2)
                if _k not in os.environ or not (os.environ.get(_k) or "").strip():
                    os.environ[_k] = _v
        except Exception:
            pass
        break

# Step 3: .env（最高优先级）——override=True 确保本地 .env 始终覆盖 Streamlit secrets
try:
    from dotenv import load_dotenv
    _env = Path(__file__).resolve().parent / ".env"
    if _env.exists():
        load_dotenv(_env, override=True)
except ImportError:
    pass

# 飞书应用
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# 文档分享授权码（可选）：当文档为保密/仅链接可访问时，可填写分享时获得的授权码 pt-xxx
FEISHU_PERMISSION_TOKEN = os.getenv("FEISHU_PERMISSION_TOKEN", "")

# 文档 ID 列表（逗号分隔，支持 doc_token、document_id、wiki、bitable 链接）
def _parse_doc_ids(raw: str) -> tuple:
    """返回 (ids, urls)：ids 为 [(source, doc_id), ...]，urls 为 [原始链接, ...]"""
    import re
    ids = []
    urls = []
    for x in raw.split(","):
        x = x.strip()
        if not x:
            continue
        url = x if x.startswith("http") else ""
        # wiki 链接
        if "wiki/" in x or "feishu.cn/wiki" in x:
            m = re.search(r"wiki/([A-Za-z0-9]+)", x)
            if m:
                ids.append(("wiki", m.group(1)))
                urls.append(url or f"https://feishu.cn/wiki/{m.group(1)}")
            else:
                ids.append(("doc", x))
                urls.append(url or x)
        # 多维表格 base/ 链接
        elif "base/" in x or "feishu.cn/base" in x:
            m = re.search(r"base/([A-Za-z0-9]+)", x)
            table_m = re.search(r"[?&]table=([A-Za-z0-9]+)", x)
            if m:
                app_token = m.group(1)
                table_id = table_m.group(1) if table_m else ""
                ids.append(("bitable", (app_token, table_id)))
                if url:
                    urls.append(url)
                else:
                    u = f"https://feishu.cn/base/{app_token}"
                    if table_id:
                        u += f"?table={table_id}"
                    urls.append(u)
            else:
                ids.append(("doc", x))
                urls.append(url or x)
        else:
            ids.append(("doc", x))
            urls.append(url or f"https://feishu.cn/docx/{x}" if re.match(r"^[A-Za-z0-9]+$", x) else x)
    return ids, urls

_parsed = _parse_doc_ids(os.getenv("FEISHU_DOC_IDS", ""))
FEISHU_DOC_IDS = _parsed[0]
FEISHU_DOC_URLS = _parsed[1]  # 与 FEISHU_DOC_IDS 一一对应的可访问链接

# 向量库路径
FEISHU_RAG_ROOT = Path(__file__).resolve().parent
VECTOR_DB_PATH = os.getenv("FEISHU_VECTOR_DB_PATH", str(FEISHU_RAG_ROOT / "vector_db"))

# 同步间隔（秒）
SYNC_INTERVAL = int(os.getenv("FEISHU_SYNC_INTERVAL", "300"))

# 嵌入模型：使用本地 HuggingFace（BGE），无需 API
EMBEDDING_MODEL = os.getenv("FEISHU_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

# LLM 配置：DeepSeek（OpenAI 兼容）
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_API_BASE = os.getenv("DEEPSEEK_API_BASE") or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com"
if LLM_API_BASE and not LLM_API_BASE.rstrip("/").endswith("/v1"):
    LLM_API_BASE = LLM_API_BASE.rstrip("/") + "/v1"
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# RAG 参数
CHUNK_SIZE = int(os.getenv("FEISHU_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("FEISHU_CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("FEISHU_RAG_TOP_K", "100"))  # 默认检索 100 个块
TOP_K_LIST = int(os.getenv("FEISHU_RAG_TOP_K_LIST", "100"))  # 查询所有/列表时用更大值
