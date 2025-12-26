from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class IndexRole(Base):
    __tablename__ = "index_role"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexUserStatus(Base):
    __tablename__ = "index_user_status"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexReleaseStatus(Base):
    __tablename__ = "index_release_status"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexReleaseLinkType(Base):
    __tablename__ = "index_release_link_type"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexProjectStatus(Base):
    __tablename__ = "index_project_status"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexActivityType(Base):
    __tablename__ = "index_activity_type"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexActivitySubtype(Base):
    __tablename__ = "index_activity_subtype"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class IndexActivityStatus(Base):
    __tablename__ = "index_activity_status"

    code = Column(String(3), primary_key=True)
    name = Column(String(32), nullable=False)


class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role_code = Column(String(3), ForeignKey("index_role.code"), nullable=False)
    status_code = Column(String(3), ForeignKey("index_user_status.code"), nullable=False)
    vacation_start = Column(Date, nullable=True)
    vacation_end = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    role = relationship("IndexRole")
    status = relationship("IndexUserStatus")
    activities = relationship("Activity", back_populates="assigned_member")

    __table_args__ = (
        Index("idx_member_role", "role_code"),
        Index("idx_member_status", "status_code"),
    )


class Release(Base):
    __tablename__ = "release"

    id = Column(Integer, primary_key=True)
    release_code = Column(String(64), nullable=False, unique=True)
    status_code = Column(String(3), ForeignKey("index_release_status.code"), nullable=False)
    delivery_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    installation_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    status = relationship("IndexReleaseStatus")
    links = relationship("ReleaseLink", back_populates="release", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_release_status", "status_code"),)


class ReleaseLink(Base):
    __tablename__ = "release_link"

    id = Column(Integer, primary_key=True)
    release_id = Column(Integer, ForeignKey("release.id"), nullable=False)
    label = Column(String(255), nullable=False)
    type_code = Column(String(3), ForeignKey("index_release_link_type.code"), nullable=False)
    url = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    release = relationship("Release", back_populates="links")
    link_type = relationship("IndexReleaseLinkType")

    __table_args__ = (
        Index("idx_release_link_release", "release_id"),
        Index("idx_release_link_type", "type_code"),
    )


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    project_code = Column(String(32), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    pm_responsible = Column(String(255), nullable=False)
    eba_responsible = Column(String(255), nullable=False)
    status_code = Column(String(3), ForeignKey("index_project_status.code"), nullable=False)
    e2e_date = Column(Date, nullable=True)
    target_release_id = Column(Integer, ForeignKey("release.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    status = relationship("IndexProjectStatus")
    target_release = relationship("Release")
    activities = relationship("Activity", back_populates="project")

    __table_args__ = (
        UniqueConstraint("project_code", name="uq_project_code"),
        Index("idx_project_status", "status_code"),
        Index("idx_project_target_release", "target_release_id"),
    )


class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True)
    type_code = Column(String(3), ForeignKey("index_activity_type.code"), nullable=False)
    subtype_code = Column(String(3), ForeignKey("index_activity_subtype.code"), nullable=False)
    ticket_code = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    assigned_member_id = Column(Integer, ForeignKey("member.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=True)
    target_release_id = Column(Integer, ForeignKey("release.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    status_code = Column(String(3), ForeignKey("index_activity_status.code"), nullable=False)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    type = relationship("IndexActivityType")
    subtype = relationship("IndexActivitySubtype")
    status = relationship("IndexActivityStatus")
    assigned_member = relationship("Member", back_populates="activities")
    project = relationship("Project", back_populates="activities")
    target_release = relationship("Release")
    links = relationship("ActivityLink", back_populates="activity", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_activity_status", "status_code"),
        Index("idx_activity_type", "type_code"),
        Index("idx_activity_subtype", "subtype_code"),
        Index("idx_activity_assigned", "assigned_member_id"),
        Index("idx_activity_project", "project_id"),
        Index("idx_activity_target_release", "target_release_id"),
    )


class ActivityLink(Base):
    __tablename__ = "activity_link"

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    label = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    activity = relationship("Activity", back_populates="links")

    __table_args__ = (Index("idx_activity_link_activity", "activity_id"),)
