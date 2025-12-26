from __future__ import annotations

from datetime import date, datetime
import subprocess
import threading
import os
from pathlib import Path
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import crud, models, rules, export as export_utils
from .db import get_session

TEMPLATES_DIR = Path(__file__).parent / "templates"
ROOT_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


def _parse_date(value: str | None, field_name: str) -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Data invalida em {field_name}") from exc


@router.get("/")
def root():
    return RedirectResponse(url="/dashboards/daily-meeting", status_code=302)


@router.get("/health")
def health():
    return {"status": "ok"}


def _run_git_commit_push() -> str:
    """Run git add/commit/push with timestamp message; return status text."""
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    try:
        status_result = subprocess.run(
            ["git", "-C", str(ROOT_DIR), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if not status_result.stdout.strip():
            return "No changes to commit."
        subprocess.run(["git", "-C", str(ROOT_DIR), "add", "."], check=True)
        subprocess.run(["git", "-C", str(ROOT_DIR), "commit", "-m", now_str], check=True)
        subprocess.run(["git", "-C", str(ROOT_DIR), "push"], check=True)
        return f"Committed and pushed at {now_str}."
    except subprocess.CalledProcessError as exc:
        return f"Git operation failed: {exc}"


def _schedule_shutdown():
    def _exit():
        os._exit(0)
    threading.Timer(1.0, _exit).start()


@router.post("/shutdown")
def shutdown(request: Request):
    git_status = _run_git_commit_push()
    _schedule_shutdown()
    html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <script>
          setTimeout(function() {{
            try {{
              window.close();
            }} catch(e) {{}}
          }}, 300);
        </script>
      </head>
      <body>
        <p>Shutting down... {git_status}</p>
        <p>If this tab does not close automatically, you can close it manually.</p>
      </body>
    </html>
    """
    return Response(content=html, media_type="text/html")


@router.get("/dashboards/daily-meeting")
def daily_meeting(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    today = date.today()
    active_members = session.execute(
        select(models.Member).order_by(models.Member.name)
    ).scalars().all()
    open_activities = session.execute(
        select(models.Activity).where(models.Activity.status_code != rules.STATUS_ACTIVITY_CLOSED)
    ).scalars().all()
    role_map = {m.id: m for m in active_members}
    return templates.TemplateResponse(
        "daily_meeting.html",
        {
            "request": request,
            "title": "Daily Meeting",
            "members": active_members,
            "activities": open_activities,
            "role_map": role_map,
            "today": today,
        },
    )


@router.get("/dashboards/project-control")
def project_control(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    projects = session.execute(
        select(models.Project).where(models.Project.status_code != rules.STATUS_PROJECT_CLOSED)
    ).scalars().all()
    activities = session.execute(select(models.Activity).where(models.Activity.status_code != rules.STATUS_ACTIVITY_CLOSED)).scalars().all()
    status_options = [(code, name) for code, name in crud.get_index_options(session, models.IndexProjectStatus) if code != rules.STATUS_PROJECT_CLOSED]
    projects_by_status: dict[str, list[models.Project]] = {code: [] for code, _ in status_options}
    for proj in projects:
        projects_by_status.setdefault(proj.status_code, []).append(proj)
    for proj_list in projects_by_status.values():
        proj_list.sort(key=lambda p: p.project_code)
    return templates.TemplateResponse(
        "project_control.html",
        {
            "request": request,
            "title": "Project Control",
            "status_options": status_options,
            "projects_by_status": projects_by_status,
            "activities": activities,
        },
    )


@router.get("/members")
def members(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    q = request.query_params.get("q")
    role_filter = request.query_params.get("role")
    status_filter = request.query_params.get("status")
    message = request.query_params.get("msg")

    members_list = crud.list_members(session, name_like=q, role_code=role_filter, status_code=status_filter)
    role_options = crud.get_index_options(session, models.IndexRole)
    status_options = crud.get_index_options(session, models.IndexUserStatus)

    return templates.TemplateResponse(
        "members.html",
        {
            "request": request,
            "title": "Members",
            "members": members_list,
            "role_options": role_options,
            "status_options": status_options,
            "filters": {"q": q or "", "role": role_filter or "", "status": status_filter or ""},
            "message": message,
        },
    )


@router.get("/members/export")
def export_members(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    q = request.query_params.get("q")
    role_filter = request.query_params.get("role")
    status_filter = request.query_params.get("status")
    members_list = crud.list_members(session, name_like=q, role_code=role_filter, status_code=status_filter)
    headers = ["name", "role", "status", "created_at", "updated_at"]
    rows = [
        [
            m.name,
            m.role.name if m.role else m.role_code,
            m.status.name if m.status else m.status_code,
            m.created_at,
            m.updated_at,
        ]
        for m in members_list
    ]
    csv_data = export_utils.rows_to_csv(headers, rows)
    filename = f"members_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/members")
def create_member(
    request: Request,
    session: Session = Depends(get_session),
    name: str = Form(...),
    role_code: str = Form(...),
    status_code: str = Form(...),
    vacation_start: str = Form(None),
    vacation_end: str = Form(None),
):
    try:
        crud.create_member(
            session,
            name=name,
            role_code=role_code,
            status_code=status_code,
            vacation_start=_parse_date(vacation_start, "vacation_start"),
            vacation_end=_parse_date(vacation_end, "vacation_end"),
        )
    except ValueError as exc:
        members_list = crud.list_members(session)
        role_options = crud.get_index_options(session, models.IndexRole)
        status_options = crud.get_index_options(session, models.IndexUserStatus)
        return templates.TemplateResponse(
            "members.html",
            {
                "request": request,
                "title": "Members",
                "members": members_list,
                "role_options": role_options,
                "status_options": status_options,
                "filters": {"q": "", "role": "", "status": ""},
                "error": str(exc),
                "form_data": {
                    "name": name,
                    "role_code": role_code,
                    "status_code": status_code,
                    "vacation_start": vacation_start,
                    "vacation_end": vacation_end,
                },
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/members?msg=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/members/{member_id}/edit")
def edit_member(request: Request, member_id: int, session: Session = Depends(get_session)):
    member = crud.get_member(session, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    role_options = crud.get_index_options(session, models.IndexRole)
    status_options = crud.get_index_options(session, models.IndexUserStatus)
    return templates.TemplateResponse(
        "member_edit.html",
        {
            "request": request,
            "title": "Edit Member",
            "member": member,
            "role_options": role_options,
            "status_options": status_options,
        },
    )


@router.post("/members/{member_id}/edit")
def update_member(
    request: Request,
    member_id: int,
    session: Session = Depends(get_session),
    name: str = Form(...),
    role_code: str = Form(...),
    status_code: str = Form(...),
    vacation_start: str = Form(None),
    vacation_end: str = Form(None),
):
    try:
        crud.update_member(
            session,
            member_id=member_id,
            name=name,
            role_code=role_code,
            status_code=status_code,
            vacation_start=_parse_date(vacation_start, "vacation_start"),
            vacation_end=_parse_date(vacation_end, "vacation_end"),
        )
    except ValueError as exc:
        role_options = crud.get_index_options(session, models.IndexRole)
        status_options = crud.get_index_options(session, models.IndexUserStatus)
        member = crud.get_member(session, member_id)
        return templates.TemplateResponse(
            "member_edit.html",
            {
                "request": request,
                "title": "Edit Member",
                "member": member,
                "role_options": role_options,
                "status_options": status_options,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/members?msg=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/members/{member_id}/delete")
def delete_member(member_id: int, session: Session = Depends(get_session)):
    crud.delete_member(session, member_id)
    return RedirectResponse(url="/members?msg=deleted", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/releases")
def releases(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    code_filter = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    msg = request.query_params.get("msg")
    releases_list = crud.list_releases(session, code_like=code_filter, status_code=status_filter)
    status_options = crud.get_index_options(session, models.IndexReleaseStatus)
    return templates.TemplateResponse(
        "releases.html",
        {
            "request": request,
            "title": "Releases",
            "releases": releases_list,
            "status_options": status_options,
            "filters": {"q": code_filter or "", "status": status_filter or ""},
            "message": msg,
        },
    )


@router.get("/releases/export")
def export_releases(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    code_filter = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    releases_list = crud.list_releases(session, code_like=code_filter, status_code=status_filter)
    headers = ["release_code", "status", "delivery_date", "start_date", "installation_date", "created_at", "updated_at"]
    rows = [
        [
            r.release_code,
            r.status.name if r.status else r.status_code,
            r.delivery_date,
            r.start_date,
            r.installation_date,
            r.created_at,
            r.updated_at,
        ]
        for r in releases_list
    ]
    csv_data = export_utils.rows_to_csv(headers, rows)
    filename = f"releases_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'})


@router.post("/releases")
def create_release(
    request: Request,
    session: Session = Depends(get_session),
    release_code: str = Form(...),
    delivery_date: str = Form(...),
    start_date: str = Form(...),
    installation_date: str = Form(...),
):
    try:
        crud.create_release(
            session,
            release_code=release_code,
            delivery_date=_parse_date(delivery_date, "delivery_date"),
            start_date=_parse_date(start_date, "start_date"),
            installation_date=_parse_date(installation_date, "installation_date"),
        )
    except ValueError as exc:
        code_filter = ""
        status_filter = ""
        releases_list = crud.list_releases(session)
        status_options = crud.get_index_options(session, models.IndexReleaseStatus)
        return templates.TemplateResponse(
            "releases.html",
            {
                "request": request,
                "title": "Releases",
                "releases": releases_list,
                "status_options": status_options,
                "filters": {"q": code_filter, "status": status_filter},
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/releases?msg=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/releases/{release_id}/edit")
def edit_release(request: Request, release_id: int, session: Session = Depends(get_session)):
    rel = crud.get_release(session, release_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Release not found")
    status_options = crud.get_index_options(session, models.IndexReleaseStatus)
    return templates.TemplateResponse(
        "release_edit.html",
        {
            "request": request,
            "title": "Edit Release",
            "release": rel,
            "status_options": status_options,
        },
    )


@router.post("/releases/{release_id}/edit")
def update_release(
    request: Request,
    release_id: int,
    session: Session = Depends(get_session),
    delivery_date: str = Form(...),
    start_date: str = Form(...),
    installation_date: str = Form(...),
):
    try:
        crud.update_release(
            session,
            release_id=release_id,
            delivery_date=_parse_date(delivery_date, "delivery_date"),
            start_date=_parse_date(start_date, "start_date"),
            installation_date=_parse_date(installation_date, "installation_date"),
        )
    except ValueError as exc:
        rel = crud.get_release(session, release_id)
        status_options = crud.get_index_options(session, models.IndexReleaseStatus)
        return templates.TemplateResponse(
            "release_edit.html",
            {
                "request": request,
                "title": "Edit Release",
                "release": rel,
                "status_options": status_options,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/releases?msg=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/projects")
def projects(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    q = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    target_release_filter = request.query_params.get("target_release_id")
    msg = request.query_params.get("msg")
    projects_list = crud.list_projects(
        session,
        code_or_title=q,
        status_code=status_filter,
        target_release_id=int(target_release_filter) if target_release_filter else None,
    )
    status_options = crud.get_index_options(session, models.IndexProjectStatus)
    release_options = crud.release_dropdown_options(session)
    return templates.TemplateResponse(
        "projects.html",
        {
            "request": request,
            "title": "Projects",
            "projects": projects_list,
            "status_options": status_options,
            "release_options": release_options,
            "filters": {"q": q or "", "status": status_filter or "", "target_release_id": target_release_filter or ""},
            "message": msg,
        },
    )


@router.get("/projects/export")
def export_projects(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    q = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    target_release_filter = request.query_params.get("target_release_id")
    projects_list = crud.list_projects(
        session,
        code_or_title=q,
        status_code=status_filter,
        target_release_id=int(target_release_filter) if target_release_filter else None,
    )
    headers = ["project_code", "title", "pm_responsible", "eba_responsible", "status", "e2e_date", "target_release", "created_at", "updated_at"]
    rows = [
        [
            p.project_code,
            p.title,
            p.pm_responsible,
            p.eba_responsible,
            p.status.name if p.status else p.status_code,
            p.e2e_date if p.e2e_date else "",
            p.target_release.release_code if p.target_release else "",
            p.created_at,
            p.updated_at,
        ]
        for p in projects_list
    ]
    csv_data = export_utils.rows_to_csv(headers, rows)
    filename = f"projects_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'})


@router.post("/projects")
def create_project(
    request: Request,
    session: Session = Depends(get_session),
    project_code: str = Form(...),
    title: str = Form(...),
    pm_responsible: str = Form(...),
    eba_responsible: str = Form(...),
    status_code: str = Form(...),
    e2e_date: str = Form(None),
    target_release_id: str = Form(None),
):
    try:
        crud.create_project(
            session,
            project_code=project_code,
            title=title,
            pm_responsible=pm_responsible,
            eba_responsible=eba_responsible,
            status_code=status_code,
            e2e_date=_parse_date(e2e_date, "e2e_date"),
            target_release_id=int(target_release_id) if target_release_id else None,
        )
    except ValueError as exc:
        status_options = crud.get_index_options(session, models.IndexProjectStatus)
        release_options = crud.release_dropdown_options(session)
        projects_list = crud.list_projects(session)
        return templates.TemplateResponse(
            "projects.html",
            {
                "request": request,
                "title": "Projects",
                "projects": projects_list,
                "status_options": status_options,
                "release_options": release_options,
                "filters": {"q": "", "status": "", "target_release_id": ""},
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/projects?msg=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/projects/{project_id}/edit")
def edit_project(request: Request, project_id: int, session: Session = Depends(get_session)):
    proj = crud.get_project(session, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    status_options = crud.get_index_options(session, models.IndexProjectStatus)
    release_options = crud.release_dropdown_options(session)
    return templates.TemplateResponse(
        "project_edit.html",
        {
            "request": request,
            "title": "Edit Project",
            "project": proj,
            "status_options": status_options,
            "release_options": release_options,
        },
    )


@router.post("/projects/{project_id}/edit")
def update_project(
    request: Request,
    project_id: int,
    session: Session = Depends(get_session),
    title: str = Form(...),
    pm_responsible: str = Form(...),
    eba_responsible: str = Form(...),
    status_code: str = Form(...),
    e2e_date: str = Form(None),
    target_release_id: str = Form(None),
):
    try:
        crud.update_project(
            session,
            project_id=project_id,
            title=title,
            pm_responsible=pm_responsible,
            eba_responsible=eba_responsible,
            status_code=status_code,
            e2e_date=_parse_date(e2e_date, "e2e_date"),
            target_release_id=int(target_release_id) if target_release_id else None,
        )
    except ValueError as exc:
        proj = crud.get_project(session, project_id)
        status_options = crud.get_index_options(session, models.IndexProjectStatus)
        release_options = crud.release_dropdown_options(session)
        return templates.TemplateResponse(
            "project_edit.html",
            {
                "request": request,
                "title": "Edit Project",
                "project": proj,
                "status_options": status_options,
                "release_options": release_options,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/projects?msg=updated", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/activities")
def activities(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    msg = request.query_params.get("msg")
    next_url = request.query_params.get("next") or "/activities"
    q = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    project_filter = request.query_params.get("project_id")
    member_filter = request.query_params.get("assigned_member_id")
    activities_list = crud.list_activities(
        session,
        status_code=status_filter,
        project_id=int(project_filter) if project_filter else None,
        assigned_member_id=int(member_filter) if member_filter else None,
        title_like=q,
    )
    type_options = crud.get_index_options(session, models.IndexActivityType)
    subtype_options = crud.get_index_options(session, models.IndexActivitySubtype)
    status_options = crud.get_index_options(session, models.IndexActivityStatus)
    member_options = [(m.id, m.name) for m in crud.list_members(session)]
    project_options = crud.project_dropdown_options(session)
    release_options = crud.release_dropdown_options(session)
    return templates.TemplateResponse(
        "activities.html",
        {
            "request": request,
            "title": "Activities",
            "activities": activities_list,
            "type_options": type_options,
            "subtype_options": subtype_options,
            "status_options": status_options,
            "member_options": member_options,
            "project_options": project_options,
            "release_options": release_options,
            "message": msg,
            "next_url": next_url,
            "filters": {
                "q": q or "",
                "status": status_filter or "",
                "project_id": project_filter or "",
                "assigned_member_id": member_filter or "",
            },
        },
    )


@router.get("/activities/export")
def export_activities(request: Request, session: Session = Depends(get_session)):
    crud.update_release_statuses(session)
    q = request.query_params.get("q")
    status_filter = request.query_params.get("status")
    project_filter = request.query_params.get("project_id")
    member_filter = request.query_params.get("assigned_member_id")
    activities_list = crud.list_activities(
        session,
        status_code=status_filter,
        project_id=int(project_filter) if project_filter else None,
        assigned_member_id=int(member_filter) if member_filter else None,
        title_like=q,
    )
    headers = ["title", "type", "subtype", "status", "project", "assigned_member", "target_release", "ticket_code", "start_date", "end_date", "created_at", "updated_at"]
    rows = []
    for a in activities_list:
        rows.append(
            [
                a.title,
                a.type.name if a.type else a.type_code,
                a.subtype.name if a.subtype else a.subtype_code,
                a.status.name if a.status else a.status_code,
                a.project.project_code if a.project else "",
                a.assigned_member.name if a.assigned_member else "",
                a.target_release.release_code if a.target_release else "",
                a.ticket_code or "",
                a.start_date or "",
                a.end_date or "",
                a.created_at,
                a.updated_at,
            ]
        )
    csv_data = export_utils.rows_to_csv(headers, rows)
    filename = f"activities_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'})


@router.post("/activities")
def create_activity(
    request: Request,
    session: Session = Depends(get_session),
    type_code: str = Form(...),
    subtype_code: str = Form(...),
    title: str = Form(...),
    status_code: str = Form(...),
    ticket_code: str = Form(None),
    assigned_member_id: str = Form(None),
    project_id: str = Form(None),
    target_release_id: str = Form(None),
    start_date: str = Form(None),
    next_url: str = Form(None),
):
    redirect_target = next_url or request.query_params.get("next") or "/activities"
    try:
        crud.create_activity(
            session,
            type_code=type_code,
            subtype_code=subtype_code,
            title=title,
            status_code=status_code,
            ticket_code=ticket_code,
            assigned_member_id=int(assigned_member_id) if assigned_member_id else None,
            project_id=int(project_id) if project_id else None,
            target_release_id=int(target_release_id) if target_release_id else None,
            start_date=_parse_date(start_date, "start_date"),
        )
    except ValueError as exc:
        type_options = crud.get_index_options(session, models.IndexActivityType)
        subtype_options = crud.get_index_options(session, models.IndexActivitySubtype)
        status_options = crud.get_index_options(session, models.IndexActivityStatus)
        member_options = [(m.id, m.name) for m in crud.list_members(session)]
        project_options = crud.project_dropdown_options(session)
        release_options = crud.release_dropdown_options(session)
        activities_list = crud.list_activities(session)
        return templates.TemplateResponse(
            "activities.html",
            {
                "request": request,
                "title": "Activities",
                "activities": activities_list,
                "type_options": type_options,
                "subtype_options": subtype_options,
                "status_options": status_options,
                "member_options": member_options,
                "project_options": project_options,
                "release_options": release_options,
                "error": str(exc),
                "next_url": redirect_target,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url=f"{redirect_target}?msg=created", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/activities/{activity_id}/edit")
def edit_activity(request: Request, activity_id: int, session: Session = Depends(get_session)):
    act = crud.get_activity(session, activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    type_options = crud.get_index_options(session, models.IndexActivityType)
    subtype_options = crud.get_index_options(session, models.IndexActivitySubtype)
    status_options = crud.get_index_options(session, models.IndexActivityStatus)
    member_options = [(m.id, m.name) for m in crud.list_members(session)]
    project_options = crud.project_dropdown_options(session)
    release_options = crud.release_dropdown_options(session)
    next_url = request.query_params.get("next") or "/activities"
    return templates.TemplateResponse(
        "activity_edit.html",
        {
            "request": request,
            "title": "Edit Activity",
            "activity": act,
            "type_options": type_options,
            "subtype_options": subtype_options,
            "status_options": status_options,
            "member_options": member_options,
            "project_options": project_options,
            "release_options": release_options,
            "next_url": next_url,
        },
    )


@router.post("/activities/{activity_id}/edit")
def update_activity(
    request: Request,
    activity_id: int,
    session: Session = Depends(get_session),
    type_code: str = Form(...),
    subtype_code: str = Form(...),
    title: str = Form(...),
    status_code: str = Form(...),
    ticket_code: str = Form(None),
    assigned_member_id: str = Form(None),
    project_id: str = Form(None),
    target_release_id: str = Form(None),
    start_date: str = Form(None),
    next_url: str = Form(None),
):
    redirect_target = next_url or request.query_params.get("next") or "/activities"
    try:
        crud.update_activity(
            session,
            activity_id=activity_id,
            type_code=type_code,
            subtype_code=subtype_code,
            title=title,
            status_code=status_code,
            ticket_code=ticket_code,
            assigned_member_id=int(assigned_member_id) if assigned_member_id else None,
            project_id=int(project_id) if project_id else None,
            target_release_id=int(target_release_id) if target_release_id else None,
            start_date=_parse_date(start_date, "start_date"),
        )
    except ValueError as exc:
        act = crud.get_activity(session, activity_id)
        type_options = crud.get_index_options(session, models.IndexActivityType)
        subtype_options = crud.get_index_options(session, models.IndexActivitySubtype)
        status_options = crud.get_index_options(session, models.IndexActivityStatus)
        member_options = [(m.id, m.name) for m in crud.list_members(session)]
        project_options = crud.project_dropdown_options(session)
        release_options = crud.release_dropdown_options(session)
        return templates.TemplateResponse(
            "activity_edit.html",
            {
                "request": request,
                "title": "Edit Activity",
                "activity": act,
                "type_options": type_options,
                "subtype_options": subtype_options,
                "status_options": status_options,
                "member_options": member_options,
                "project_options": project_options,
                "release_options": release_options,
                "error": str(exc),
                "next_url": redirect_target,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url=f"{redirect_target}?msg=updated", status_code=status.HTTP_303_SEE_OTHER)
