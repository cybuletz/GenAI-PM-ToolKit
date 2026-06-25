from pydantic import BaseModel
from typing import Optional


class ProjectEntry(BaseModel):
    project_name: str
    date_range: str
    bullets: list[str]


class ExperienceEntry(BaseModel):
    employer: str
    role: str
    date_range: str
    employer_bullets: list[str]
    projects: list[ProjectEntry]


class ProfileSchema(BaseModel):
    name: str
    role_title: str
    role_subtitle: str
    profile: str
    competencies: list[str]
    education: list[str]
    certifications: list[str] = []
    methodologies: list[str]
    technologies: list[str]
    experience: list[ExperienceEntry]
