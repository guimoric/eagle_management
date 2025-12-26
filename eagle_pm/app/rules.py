from __future__ import annotations

import re
from datetime import date
from typing import List, Tuple

PROJECT_CODE_PATTERN = re.compile(r"^PR\d+$")

INDEX_VALUES = {
    "index_role": [("001", "BA"), ("002", "QA"), ("003", "DEV")],
    "index_user_status": [("001", "ACTIVE"), ("002", "VACATION")],
    "index_release_status": [("001", "PLANNED"), ("002", "IN_PROGRESS"), ("003", "INSTALLED")],
    "index_release_link_type": [("001", "REQUIREMENT"), ("002", "JIRA"), ("003", "OTHER")],
    "index_project_status": [
        ("001", "PENDING_HLE"),
        ("002", "PENDING_APPROVAL"),
        ("003", "APPROVED"),
        ("004", "PLANNED"),
        ("005", "IN_PROGRESS"),
        ("006", "E2E"),
        ("007", "CLOSED"),
        ("008", "BLOCKED"),
    ],
    "index_activity_type": [("001", "JIRA"), ("002", "INTERNAL")],
    "index_activity_subtype": [
        ("001", "STORY"),
        ("002", "BUG"),
        ("003", "PRODDEF"),
        ("004", "OPY"),
        ("005", "INTERNAL"),
    ],
    "index_activity_status": [
        ("001", "PLANNED"),
        ("002", "OPEN"),
        ("003", "BLOCKED"),
        ("004", "IN_PROGRESS"),
        ("005", "CLOSED"),
    ],
}

STATUS_RELEASE_INSTALLED = "003"
STATUS_RELEASE_PLANNED = "001"
STATUS_RELEASE_IN_PROGRESS = "002"

STATUS_PROJECT_CLOSED = "007"

STATUS_ACTIVITY_CLOSED = "005"


def project_code_is_valid(code: str) -> bool:
    return bool(code and PROJECT_CODE_PATTERN.fullmatch(code))


def release_status_for_dates(start_date: date, installation_date: date, today: date) -> str:
    if today >= installation_date:
        return STATUS_RELEASE_INSTALLED
    if today >= start_date:
        return STATUS_RELEASE_IN_PROGRESS
    return STATUS_RELEASE_PLANNED


def release_is_installed(status_code: str) -> bool:
    return status_code == STATUS_RELEASE_INSTALLED


def project_is_closed(status_code: str) -> bool:
    return status_code == STATUS_PROJECT_CLOSED


def activity_is_closed(status_code: str) -> bool:
    return status_code == STATUS_ACTIVITY_CLOSED


def index_rows(key: str) -> List[Tuple[str, str]]:
    return list(INDEX_VALUES.get(key, []))
