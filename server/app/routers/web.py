from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import SERVER_DIR, get_settings
from app.deps import get_db, get_optional_user
from app.models import Report, Task, User
from app.routers.serializers import serialize_knowledge_item
from app.services.auth_service import authenticate_user
from app.services.knowledge_service import get_knowledge_item, list_knowledge_items
from app.services.package_service import get_latest_package, upload_package
from app.services.prompt_service import generate_prompt, get_current_prompt, list_prompts, set_current_prompt
from app.services.report_service import generate_report, get_current_report, list_reports, set_current_report
from app.services.result_service import get_current_result, list_results, save_result_text, save_result_upload, set_current_result
from app.services.settings_service import list_settings, update_settings
from app.services.task_service import create_task, delete_task, get_task, list_tasks, recent_reports, update_task


templates = Jinja2Templates(directory=str((SERVER_DIR / "app" / "templates").resolve()))
router = APIRouter()
STYLE_ASSET_VERSION = int((SERVER_DIR / "app" / "static" / "styles.css").stat().st_mtime)


def redirect_login() -> RedirectResponse:
    return RedirectResponse("/login", status_code=303)


def render(request: Request, template_name: str, context: dict, user: User | None):
    base_context = {
        "request": request,
        "current_user": user,
        "asset_version": STYLE_ASSET_VERSION,
    }
    base_context.update(context)
    return templates.TemplateResponse(request, template_name, base_context)


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", {"error": None}, user)


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return render(request, "login.html", {"error": "用户名或密码错误"}, None)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout_submit(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    all_tasks = list_tasks(db, user.id)
    tasks = all_tasks[:5]
    settings_items = list_settings(db)
    knowledge_items = list_knowledge_items(db)
    reports = recent_reports(db, user.id, limit=4)
    report_count = (
        db.query(Report)
        .join(Task, Task.id == Report.task_id)
        .filter(Task.user_id == user.id, Task.deleted_at.is_(None))
        .count()
    )
    default_templates = {
        item.setting_key: item.setting_value
        for item in settings_items
        if item.setting_key in ["default_prompt_template_reference", "default_prompt_template_improve"]
    }
    return render(
        request,
        "dashboard.html",
        {
            "recent_tasks": tasks,
            "settings_items": settings_items,
            "knowledge_count": len(knowledge_items),
            "recent_reports": reports,
            "task_count": len(all_tasks),
            "active_task_count": sum(1 for task in all_tasks if task.status != "report_ready"),
            "report_count": report_count,
            "default_templates": default_templates,
        },
        user,
    )


@router.get("/tasks")
def tasks_page(
    request: Request,
    task_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    tasks = list_tasks(db, user.id, task_type=task_type, status=status)
    return render(request, "tasks.html", {"tasks": tasks, "filters": {"task_type": task_type, "status": status}}, user)


@router.get("/tasks/new")
def new_task_page(request: Request, user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    return render(request, "task_new.html", {"error": None}, user)


@router.post("/tasks/new")
def new_task_submit(
    request: Request,
    task_type: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    package_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    task = create_task(db, user.id, task_type, title, description or None)
    if package_file and package_file.filename:
        try:
            upload_package(db, task, package_file)
        except Exception as exc:  # noqa: BLE001
            return render(request, "task_new.html", {"error": str(exc)}, user)
    return RedirectResponse(f"/tasks/{task.id}", status_code=303)


@router.get("/tasks/{task_id}")
def task_detail_page(task_id: int, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    package = get_latest_package(task)
    prompt = get_current_prompt(task)
    result = get_current_result(task)
    report = get_current_report(task)
    return render(
        request,
        "task_detail.html",
        {
            "task": task,
            "package": package,
            "prompt": prompt,
            "result": result,
            "report": report,
            "segments": sorted(package.segments, key=lambda item: item.segment_index)[:12] if package else [],
            "package_files": package.files[:20] if package else [],
            "result_history": list_results(task),
            "report_history": list_reports(task),
            "prompt_history": list_prompts(task),
        },
        user,
    )


@router.post("/tasks/{task_id}/edit")
def task_edit_submit(
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    update_task(task, title=title, description=description or None)
    db.add(task)
    db.commit()
    return RedirectResponse(f"/tasks/{task.id}", status_code=303)


@router.post("/tasks/{task_id}/package")
def task_package_submit(
    task_id: int,
    package_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    upload_package(db, task, package_file)
    return RedirectResponse(f"/tasks/{task.id}", status_code=303)


@router.post("/tasks/{task_id}/delete")
def task_delete_submit(task_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if task:
        delete_task(db, task)
    return RedirectResponse("/tasks", status_code=303)


@router.get("/tasks/{task_id}/prompt")
def prompt_page(task_id: int, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    prompt = get_current_prompt(task)
    return render(request, "prompt.html", {"task": task, "prompt": prompt, "prompt_history": list_prompts(task)}, user)


@router.post("/tasks/{task_id}/prompt/generate")
def prompt_generate_submit(task_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    generate_prompt(db, task)
    return RedirectResponse(f"/tasks/{task.id}/prompt", status_code=303)


@router.post("/tasks/{task_id}/prompt/{prompt_id}/current")
def prompt_set_current_submit(task_id: int, prompt_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    set_current_prompt(db, task, prompt_id)
    return RedirectResponse(f"/tasks/{task.id}/prompt", status_code=303)


@router.get("/tasks/{task_id}/fillback")
def fillback_page(task_id: int, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    result = get_current_result(task)
    prompt = get_current_prompt(task)
    return render(
        request,
        "fillback.html",
        {"task": task, "result": result, "prompt": prompt, "result_history": list_results(task), "error": None},
        user,
    )


@router.post("/tasks/{task_id}/fillback")
def fillback_submit(
    task_id: int,
    request: Request,
    source_model: str = Form(""),
    source_note: str = Form(""),
    content_text: str = Form(""),
    result_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    try:
        if result_file and result_file.filename:
            save_result_upload(db, task, result_file, source_model or None, source_note or None)
        else:
            save_result_text(db, task, content_text, source_model or None, source_note or None)
    except Exception as exc:  # noqa: BLE001
        return render(
            request,
            "fillback.html",
            {"task": task, "result": None, "prompt": get_current_prompt(task), "result_history": list_results(task), "error": str(exc)},
            user,
        )
    return RedirectResponse(f"/tasks/{task.id}/fillback", status_code=303)


@router.post("/tasks/{task_id}/fillback/{result_id}/current")
def fillback_set_current_submit(task_id: int, result_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    set_current_result(db, task, result_id)
    return RedirectResponse(f"/tasks/{task.id}/fillback", status_code=303)


@router.get("/tasks/{task_id}/report")
def report_page(task_id: int, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    report = get_current_report(task)
    report_payload = json.loads(report.structured_content) if report else None
    return render(
        request,
        "report.html",
        {"task": task, "report": report, "report_payload": report_payload, "report_history": list_reports(task)},
        user,
    )


@router.post("/tasks/{task_id}/report/generate")
def report_generate_submit(task_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    generate_report(db, task)
    return RedirectResponse(f"/tasks/{task.id}/report", status_code=303)


@router.post("/tasks/{task_id}/report/{report_id}/current")
def report_set_current_submit(task_id: int, report_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    task = get_task(db, task_id, user.id)
    if not task:
        return RedirectResponse("/tasks", status_code=303)
    set_current_report(db, task, report_id)
    return RedirectResponse(f"/tasks/{task.id}/report", status_code=303)


@router.get("/knowledge")
def knowledge_page(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    items = list_knowledge_items(db, category=category, query=q)
    all_items = list_knowledge_items(db)
    categories = sorted({item.category for item in all_items})
    category_counts = Counter(item.category for item in all_items)
    tag_counts: Counter[str] = Counter()
    for item in all_items:
        if not item.tags:
            continue
        for tag in item.tags.split(","):
            cleaned = tag.strip()
            if cleaned:
                tag_counts[cleaned] += 1
    return render(
        request,
        "knowledge.html",
        {
            "items": [serialize_knowledge_item(item) for item in items],
            "filters": {"q": q or "", "category": category or ""},
            "categories": categories,
            "knowledge_total": len(all_items),
            "category_counts": dict(category_counts),
            "popular_tags": tag_counts.most_common(8),
        },
        user,
    )


@router.get("/knowledge/{item_id}")
def knowledge_detail_page(item_id: int, request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    item = get_knowledge_item(db, item_id)
    if not item:
        return RedirectResponse("/knowledge", status_code=303)
    related_items = [
        serialize_knowledge_item(related)
        for related in list_knowledge_items(db, category=item.category)
        if related.id != item.id
    ][:4]
    return render(
        request,
        "knowledge_detail.html",
        {"item": serialize_knowledge_item(item), "related_items": related_items},
        user,
    )


@router.get("/settings")
def settings_page(request: Request, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    return render(request, "settings.html", {"settings_items": list_settings(db)}, user)


@router.post("/settings")
async def settings_submit(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    form = dict((await request.form()).items())
    updates = {key.replace("setting__", ""): value for key, value in form.items() if key.startswith("setting__")}
    update_settings(db, updates)
    return RedirectResponse("/settings", status_code=303)


@router.get("/files/{relative_path:path}")
def storage_file(relative_path: str, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    if not user:
        return redirect_login()
    settings = get_settings()
    file_path = (settings.storage_root / relative_path).resolve()
    if not str(file_path).startswith(str(settings.storage_root.resolve())) or not file_path.exists():
        return RedirectResponse("/", status_code=303)
    return FileResponse(file_path)


@router.get("/reports/{report_id}/download/{format_name}")
def report_download(
    report_id: int,
    format_name: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if not user:
        return redirect_login()
    report = db.get(Report, report_id)
    if not report or report.task.user_id != user.id:
        return RedirectResponse("/", status_code=303)
    relative_path = report.markdown_path if format_name == "markdown" else report.txt_path
    if not relative_path:
        return RedirectResponse(f"/tasks/{report.task_id}/report", status_code=303)
    settings = get_settings()
    file_path = settings.storage_root / relative_path
    return FileResponse(file_path, filename=file_path.name)
