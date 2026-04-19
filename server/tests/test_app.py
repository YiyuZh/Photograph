from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient


SERVER_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = SERVER_DIR / "tests_runtime"

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

if RUNTIME_DIR.exists():
    shutil.rmtree(RUNTIME_DIR)

(RUNTIME_DIR / "storage").mkdir(parents=True, exist_ok=True)
(RUNTIME_DIR / "logs").mkdir(parents=True, exist_ok=True)

os.environ["STORAGE_ROOT"] = str((RUNTIME_DIR / "storage").resolve())
os.environ["LOGS_ROOT"] = str((RUNTIME_DIR / "logs").resolve())
os.environ["KNOWLEDGE_ROOT"] = str((SERVER_DIR / "knowledge").resolve())
os.environ["DEFAULT_PASSWORD"] = "test-password-123"
os.environ["APP_BASE_URL"] = "http://testserver"

from app.main import app  # noqa: E402


def test_full_workflow():
    sample_zip = SERVER_DIR / "sample_data" / "minimal_analysis_package.zip"
    with TestClient(app) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-password-123"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["success"] is True

        task_response = client.post(
            "/api/tasks",
            json={"task_type": "reference", "title": "测试拆解任务", "description": "用于自动化测试"},
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        with sample_zip.open("rb") as handle:
            package_response = client.post(
                f"/api/tasks/{task_id}/package",
                files={"package_file": ("minimal_analysis_package.zip", handle, "application/zip")},
            )
        assert package_response.status_code == 200
        assert package_response.json()["data"]["segment_count"] == 3

        prompt_response = client.post(f"/api/tasks/{task_id}/prompts")
        assert prompt_response.status_code == 200
        assert "总体风格判断" in prompt_response.json()["data"]["prompt_text"]
        first_prompt_id = prompt_response.json()["data"]["id"]

        second_prompt_response = client.post(f"/api/tasks/{task_id}/prompts")
        assert second_prompt_response.status_code == 200
        second_prompt_id = second_prompt_response.json()["data"]["id"]
        assert second_prompt_id != first_prompt_id

        set_prompt_response = client.post(f"/api/tasks/{task_id}/prompts/{first_prompt_id}/set-current")
        assert set_prompt_response.status_code == 200
        assert set_prompt_response.json()["data"]["id"] == first_prompt_id

        result_response = client.post(
            f"/api/tasks/{task_id}/results",
            json={
                "source_model": "ChatGPT",
                "source_note": "第一版拆解结果",
                "content_text": "# 总体结论\n这是一支节奏清晰的城市感参考视频。\n\n# 风格标签\n城市夜景、人物背影、快慢结合。\n\n# 调色推测\n整体偏暖，阴影略带青色。\n\n# 剪辑结构分析\n开场快建环境，中段推进，结尾收束。\n\n# 片段拆解\n每段都围绕人物与环境关系展开。\n\n# 疑似 AI 生成片段提示\n暂无明显证据。\n\n# 仿拍方案\n先拍环境镜头，再拍人物推进，最后补特写。",
            },
        )
        assert result_response.status_code == 200
        first_result_id = result_response.json()["data"]["id"]
        assert result_response.json()["data"]["source_note"] == "第一版拆解结果"

        second_result_response = client.post(
            f"/api/tasks/{task_id}/results",
            json={
                "source_model": "DeepSeek",
                "source_note": "第二版修订",
                "content_text": "# 总体结论\n第二版结果。\n\n# 风格标签\n城市夜景。\n\n# 调色推测\n暖色。\n\n# 剪辑结构分析\n三段式。\n\n# 片段拆解\n按节奏推进。\n\n# 疑似 AI 生成片段提示\n暂无。\n\n# 仿拍方案\n控制镜头长度。",
            },
        )
        assert second_result_response.status_code == 200
        second_result_id = second_result_response.json()["data"]["id"]

        set_result_response = client.post(f"/api/tasks/{task_id}/results/{first_result_id}/set-current")
        assert set_result_response.status_code == 200
        assert set_result_response.json()["data"]["id"] == first_result_id

        report_response = client.post(f"/api/tasks/{task_id}/report")
        assert report_response.status_code == 200
        assert report_response.json()["data"]["summary"]
        first_report_id = report_response.json()["data"]["id"]

        set_result_response_back = client.post(f"/api/tasks/{task_id}/results/{second_result_id}/set-current")
        assert set_result_response_back.status_code == 200

        second_report_response = client.post(f"/api/tasks/{task_id}/report")
        assert second_report_response.status_code == 200
        second_report_id = second_report_response.json()["data"]["id"]
        assert second_report_id != first_report_id

        set_report_response = client.post(f"/api/tasks/{task_id}/reports/{first_report_id}/set-current")
        assert set_report_response.status_code == 200
        assert set_report_response.json()["data"]["id"] == first_report_id

        history_response = client.get("/api/tasks")
        assert history_response.status_code == 200
        assert len(history_response.json()["data"]) >= 1

        knowledge_response = client.get("/api/knowledge-items")
        assert knowledge_response.status_code == 200
        assert len(knowledge_response.json()["data"]) >= 5


def test_login_page_uses_relative_stylesheet():
    with TestClient(app) as client:
        response = client.get("/login")
        assert response.status_code == 200
        assert '/static/styles.css?v=' in response.text
        assert 'http://testserver/static/styles.css' not in response.text
