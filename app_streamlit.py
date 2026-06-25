# -*- coding: utf-8 -*-
"""
Streamlit Cloud 入口：将工作目录切换到 feishu-rag 子目录后运行主应用。
"""
import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.join(_here, "feishu-rag")

# 切换到 feishu-rag 目录，确保相对路径（.env、vector_db 等）正确解析
os.chdir(_app_dir)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

# 运行真正的应用
exec(open(os.path.join(_app_dir, "app_streamlit.py"), encoding="utf-8").read())
