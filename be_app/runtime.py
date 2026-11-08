"""Fail clearly before importing the scientific UI when launched outside the locked environment."""

import sys
from pathlib import Path

import streamlit as st

REQUIRED_STREAMLIT = "1.66.1"


def runtime_issue(python_version: tuple[int, ...], streamlit_version: str) -> str | None:
    issues = []
    if not (3, 11) <= python_version[:2] < (3, 14):
        issues.append("Python của dự án cần phiên bản 3.11–3.13")
    if streamlit_version != REQUIRED_STREAMLIT:
        issues.append(f"Streamlit của dự án cần đúng phiên bản {REQUIRED_STREAMLIT}")
    return "; ".join(issues) if issues else None


def launch():
    issue = runtime_issue(tuple(sys.version_info[:3]), st.__version__)
    if issue:
        root = Path(__file__).resolve().parents[1]
        st.set_page_config(page_title="Chọn đúng môi trường BE", layout="centered")
        st.error("Ứng dụng đang được khởi chạy bằng môi trường ngoài cấu hình đã khóa. " + issue + ".")
        st.write(f"Đang dùng Python {sys.version.split()[0]} và Streamlit {st.__version__}.")
        st.caption(f"Python đang chạy: {sys.executable}")
        st.write("Dừng tiến trình hiện tại bằng Ctrl+C, rồi chạy file run_app.cmd trong thư mục dự án:")
        st.code(r".\run_app.cmd", language="powershell")
        st.write("Hoặc chạy trực tiếp bằng Python của môi trường dự án:")
        st.code(
            f'& "{root / ".venv" / "Scripts" / "python.exe"}" -m streamlit run "{root / "app.py"}"',
            language="powershell",
        )
        st.write("Nếu chưa cài môi trường dự án:")
        st.code("uv sync --locked --extra dev", language="powershell")
        st.stop()
    from be_app.ui import main

    main()
