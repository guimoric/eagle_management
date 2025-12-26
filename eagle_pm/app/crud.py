from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, rules


def seed_index_tables(session: Session) -> None:
    mapping: Iterable[Tuple[type, list]] = [
        (models.IndexRole, rules.index_rows("index_role")),
        (models.IndexUserStatus, rules.index_rows("index_user_status")),
        (models.IndexReleaseStatus, rules.index_rows("index_release_status")),
        (models.IndexReleaseLinkType, rules.index_rows("index_release_link_type")),
        (models.IndexProjectStatus, rules.index_rows("index_project_status")),
        (models.IndexActivityType, rules.index_rows("index_activity_type")),
        (models.IndexActivitySubtype, rules.index_rows("index_activity_subtype")),
        (models.IndexActivityStatus, rules.index_rows("index_activity_status")),
    ]

    for model_cls, rows in mapping:
        existing = set(session.execute(select(model_cls.code)).scalars().all())
        for code, name in rows:
            if code not in existing:
                session.add(model_cls(code=code, name=name))


def update_release_statuses(session: Session, today: date | None = None) -> None:
    today = today or date.today()
    releases = session.execute(select(models.Release)).scalars().all()
    for rel in releases:
        new_status = rules.release_status_for_dates(rel.start_date, rel.installation_date, today)
        if rel.status_code != new_status:
            rel.status_code = new_status
            rel.updated_at = datetime.utcnow()
    session.flush()


def set_activity_status(activity: models.Activity, new_status_code: str, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    was_closed = rules.activity_is_closed(activity.status_code)
    will_be_closed = rules.activity_is_closed(new_status_code)
    activity.status_code = new_status_code
    if will_be_closed:
        if activity.end_date is None:
            activity.end_date = now
    else:
        if was_closed:
            activity.end_date = None


# --- Members CRUD helpers ---

def _ensure_index_code(session: Session, model_cls, code: str) -> None:
    if not code:
        raise ValueError("Codigo obrigatorio.")
    exists = session.execute(select(model_cls).where(model_cls.code == code)).scalar_one_or_none()
    if not exists:
        raise ValueError("Codigo de indice invalido.")


def get_index_options(session: Session, model_cls) -> list[tuple[str, str]]:
    rows = session.execute(select(model_cls).order_by(model_cls.code)).scalars().all()
    return [(row.code, row.name) for row in rows]


def list_members(session: Session, name_like: str | None = None, role_code: str | None = None, status_code: str | None = None):
    stmt = select(models.Member).order_by(models.Member.name)
    if name_like:
        stmt = stmt.where(models.Member.name.ilike(f"%{name_like}%"))
    if role_code:
        stmt = stmt.where(models.Member.role_code == role_code)
    if status_code:
        stmt = stmt.where(models.Member.status_code == status_code)
    return session.execute(stmt).scalars().all()


def create_member(
    session: Session,
    name: str,
    role_code: str,
    status_code: str,
    vacation_start: date | None = None,
    vacation_end: date | None = None,
) -> models.Member:
    name_clean = (name or "").strip()
    if not name_clean:
        raise ValueError("Nome obrigatorio.")
    _ensure_index_code(session, models.IndexRole, role_code)
    _ensure_index_code(session, models.IndexUserStatus, status_code)
    if vacation_start and vacation_end and vacation_end < vacation_start:
        raise ValueError("Data fim de ferias antes do inicio.")
    member = models.Member(name=name_clean, role_code=role_code, status_code=status_code)
    active_code = rules.INDEX_VALUES["index_user_status"][0][0]
    if status_code == active_code:
        vacation_start = None
        vacation_end = None
    member.vacation_start = vacation_start
    member.vacation_end = vacation_end
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def get_member(session: Session, member_id: int) -> models.Member | None:
    return session.get(models.Member, member_id)


def update_member(
    session: Session,
    member_id: int,
    name: str,
    role_code: str,
    status_code: str,
    vacation_start: date | None = None,
    vacation_end: date | None = None,
) -> models.Member:
    member = get_member(session, member_id)
    if not member:
        raise ValueError("Member nao encontrado.")
    name_clean = (name or "").strip()
    if not name_clean:
        raise ValueError("Nome obrigatorio.")
    _ensure_index_code(session, models.IndexRole, role_code)
    _ensure_index_code(session, models.IndexUserStatus, status_code)
    if vacation_start and vacation_end and vacation_end < vacation_start:
        raise ValueError("Data fim de ferias antes do inicio.")
    active_code = rules.INDEX_VALUES["index_user_status"][0][0]
    if status_code == active_code:
        vacation_start = None
        vacation_end = None
    member.name = name_clean
    member.role_code = role_code
    member.status_code = status_code
    member.vacation_start = vacation_start
    member.vacation_end = vacation_end
    member.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(member)
    return member


def delete_member(session: Session, member_id: int) -> None:
    member = get_member(session, member_id)
    if not member:
        return
    session.delete(member)
    session.commit()


# --- Releases CRUD helpers ---

def list_releases(session: Session, code_like: str | None = None, status_code: str | None = None):
    stmt = select(models.Release).order_by(models.Release.release_code)
    if code_like:
        stmt = stmt.where(models.Release.release_code.ilike(f"%{code_like}%"))
    if status_code:
        stmt = stmt.where(models.Release.status_code == status_code)
    return session.execute(stmt).scalars().all()


def create_release(session: Session, release_code: str, delivery_date: date, start_date: date, installation_date: date) -> models.Release:
    code = (release_code or "").strip()
    if not code:
        raise ValueError("Release code obrigatorio.")
    existing = session.execute(select(models.Release).where(models.Release.release_code == code)).scalar_one_or_none()
    if existing:
        raise ValueError("Release code ja existe.")
    if not delivery_date or not start_date or not installation_date:
        raise ValueError("Datas obrigatorias.")
    status_code = rules.release_status_for_dates(start_date, installation_date, date.today())
    rel = models.Release(
        release_code=code,
        status_code=status_code,
        delivery_date=delivery_date,
        start_date=start_date,
        installation_date=installation_date,
    )
    session.add(rel)
    session.commit()
    session.refresh(rel)
    return rel


def get_release(session: Session, release_id: int) -> models.Release | None:
    return session.get(models.Release, release_id)


def update_release(
    session: Session,
    release_id: int,
    delivery_date: date,
    start_date: date,
    installation_date: date,
) -> models.Release:
    rel = get_release(session, release_id)
    if not rel:
        raise ValueError("Release nao encontrada.")
    if rules.release_is_installed(rel.status_code):
        raise ValueError("Release INSTALLED nao pode ser editada.")
    if not delivery_date or not start_date or not installation_date:
        raise ValueError("Datas obrigatorias.")
    rel.delivery_date = delivery_date
    rel.start_date = start_date
    rel.installation_date = installation_date
    rel.status_code = rules.release_status_for_dates(start_date, installation_date, date.today())
    rel.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(rel)
    return rel


def release_dropdown_options(session: Session) -> list[tuple[int, str]]:
    stmt = select(models.Release).where(models.Release.status_code != rules.STATUS_RELEASE_INSTALLED).order_by(models.Release.release_code)
    rows = session.execute(stmt).scalars().all()
    return [(row.id, row.release_code) for row in rows]


# --- Projects CRUD helpers ---

def list_projects(session: Session, code_or_title: str | None = None, status_code: str | None = None, target_release_id: int | None = None):
    stmt = select(models.Project).order_by(models.Project.project_code)
    if code_or_title:
        like = f"%{code_or_title}%"
        stmt = stmt.where((models.Project.project_code.ilike(like)) | (models.Project.title.ilike(like)))
    if status_code:
        stmt = stmt.where(models.Project.status_code == status_code)
    if target_release_id:
        stmt = stmt.where(models.Project.target_release_id == target_release_id)
    return session.execute(stmt).scalars().all()


def create_project(
    session: Session,
    project_code: str,
    title: str,
    pm_responsible: str,
    eba_responsible: str,
    status_code: str,
    e2e_date: date | None,
    target_release_id: int | None,
) -> models.Project:
    code = (project_code or "").strip()
    if not rules.project_code_is_valid(code):
        raise ValueError("Project code invalido (formato PR + digitos).")
    existing = session.execute(select(models.Project).where(models.Project.project_code == code)).scalar_one_or_none()
    if existing:
        raise ValueError("Project code ja existe.")
    if not title or not pm_responsible or not eba_responsible:
        raise ValueError("Campos obrigatorios ausentes.")
    _ensure_index_code(session, models.IndexProjectStatus, status_code)
    if target_release_id:
        rel = get_release(session, target_release_id)
        if not rel or rules.release_is_installed(rel.status_code):
            raise ValueError("Target release invalida (INSTALLED nao permitido).")
    proj = models.Project(
        project_code=code,
        title=title.strip(),
        pm_responsible=pm_responsible.strip(),
        eba_responsible=eba_responsible.strip(),
        status_code=status_code,
        e2e_date=e2e_date,
        target_release_id=target_release_id,
    )
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return proj


def get_project(session: Session, project_id: int) -> models.Project | None:
    return session.get(models.Project, project_id)


def update_project(
    session: Session,
    project_id: int,
    title: str,
    pm_responsible: str,
    eba_responsible: str,
    status_code: str,
    e2e_date: date | None,
    target_release_id: int | None,
) -> models.Project:
    proj = get_project(session, project_id)
    if not proj:
        raise ValueError("Project nao encontrado.")
    if not title or not pm_responsible or not eba_responsible:
        raise ValueError("Campos obrigatorios ausentes.")
    _ensure_index_code(session, models.IndexProjectStatus, status_code)
    if target_release_id:
        rel = get_release(session, target_release_id)
        if not rel or rules.release_is_installed(rel.status_code):
            raise ValueError("Target release invalida (INSTALLED nao permitido).")
    proj.title = title.strip()
    proj.pm_responsible = pm_responsible.strip()
    proj.eba_responsible = eba_responsible.strip()
    proj.status_code = status_code
    proj.e2e_date = e2e_date
    proj.target_release_id = target_release_id
    proj.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(proj)
    return proj


def project_dropdown_options(session: Session) -> list[tuple[int, str]]:
    stmt = select(models.Project).where(models.Project.status_code != rules.STATUS_PROJECT_CLOSED).order_by(models.Project.project_code)
    rows = session.execute(stmt).scalars().all()
    return [(row.id, row.project_code) for row in rows]


# --- Activities CRUD helpers ---

def list_activities(
    session: Session,
    status_code: str | None = None,
    project_id: int | None = None,
    assigned_member_id: int | None = None,
    title_like: str | None = None,
):
    stmt = select(models.Activity).order_by(models.Activity.created_at.desc())
    if status_code:
        stmt = stmt.where(models.Activity.status_code == status_code)
    if project_id:
        stmt = stmt.where(models.Activity.project_id == project_id)
    if assigned_member_id:
        stmt = stmt.where(models.Activity.assigned_member_id == assigned_member_id)
    if title_like:
        stmt = stmt.where(models.Activity.title.ilike(f"%{title_like}%"))
    return session.execute(stmt).scalars().all()


def create_activity(
    session: Session,
    type_code: str,
    subtype_code: str,
    title: str,
    status_code: str,
    ticket_code: str | None = None,
    assigned_member_id: int | None = None,
    project_id: int | None = None,
    target_release_id: int | None = None,
    start_date: date | None = None,
) -> models.Activity:
    if not title:
        raise ValueError("Titulo obrigatorio.")
    _ensure_index_code(session, models.IndexActivityType, type_code)
    _ensure_index_code(session, models.IndexActivitySubtype, subtype_code)
    _ensure_index_code(session, models.IndexActivityStatus, status_code)
    if project_id:
        proj = get_project(session, project_id)
        if not proj or rules.project_is_closed(proj.status_code):
            raise ValueError("Projeto invalido (CLOSED nao permitido).")
    if target_release_id:
        rel = get_release(session, target_release_id)
        if not rel or rules.release_is_installed(rel.status_code):
            raise ValueError("Target release invalida (INSTALLED nao permitido).")
    act = models.Activity(
        type_code=type_code,
        subtype_code=subtype_code,
        title=title.strip(),
        status_code=status_code,
        ticket_code=ticket_code.strip() if ticket_code else None,
        assigned_member_id=assigned_member_id,
        project_id=project_id,
        target_release_id=target_release_id,
        start_date=start_date,
    )
    set_activity_status(act, status_code)
    session.add(act)
    session.commit()
    session.refresh(act)
    return act


def get_activity(session: Session, activity_id: int) -> models.Activity | None:
    return session.get(models.Activity, activity_id)


def update_activity(
    session: Session,
    activity_id: int,
    type_code: str,
    subtype_code: str,
    title: str,
    status_code: str,
    ticket_code: str | None = None,
    assigned_member_id: int | None = None,
    project_id: int | None = None,
    target_release_id: int | None = None,
    start_date: date | None = None,
) -> models.Activity:
    act = get_activity(session, activity_id)
    if not act:
        raise ValueError("Activity nao encontrada.")
    if not title:
        raise ValueError("Titulo obrigatorio.")
    _ensure_index_code(session, models.IndexActivityType, type_code)
    _ensure_index_code(session, models.IndexActivitySubtype, subtype_code)
    _ensure_index_code(session, models.IndexActivityStatus, status_code)
    if project_id:
        proj = get_project(session, project_id)
        if not proj or rules.project_is_closed(proj.status_code):
            raise ValueError("Projeto invalido (CLOSED nao permitido).")
    if target_release_id:
        rel = get_release(session, target_release_id)
        if not rel or rules.release_is_installed(rel.status_code):
            raise ValueError("Target release invalida (INSTALLED nao permitido).")
    act.type_code = type_code
    act.subtype_code = subtype_code
    act.title = title.strip()
    act.ticket_code = ticket_code.strip() if ticket_code else None
    act.assigned_member_id = assigned_member_id
    act.project_id = project_id
    act.target_release_id = target_release_id
    act.start_date = start_date
    set_activity_status(act, status_code)
    act.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(act)
    return act


def activity_dropdown_options(session: Session):
    stmt = select(models.Activity).order_by(models.Activity.title)
    rows = session.execute(stmt).scalars().all()
    return [(row.id, row.title) for row in rows]
