import re
from core.profile_schema import ProfileSchema, ExperienceEntry, ProjectEntry

GENERIC_BULLETS = {"responsible for", "worked on", "involved in"}


def _trim_to_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    if last_period > 0:
        return truncated[:last_period + 1]
    return truncated.rstrip()


def _trim_end(text: str, max_chars: int) -> str:
    return text[:max_chars] if len(text) > max_chars else text


def _is_generic(bullet: str) -> bool:
    lower = bullet.strip().lower()
    return any(lower.startswith(g) for g in GENERIC_BULLETS)


def _normalize_tech(tech: str) -> str:
    return tech.strip()


class ProfileTrimmer:
    def trim(self, profile: ProfileSchema) -> ProfileSchema:
        data = profile.model_dump()

        data["profile"] = _trim_to_sentence(data["profile"], 600)
        data["name"] = _trim_end(data["name"], 60)
        data["role_title"] = _trim_end(data["role_title"], 120)
        data["role_subtitle"] = _trim_end(data["role_subtitle"], 80)

        comps = [_trim_end(c, 45) for c in data["competencies"]]
        data["competencies"] = comps[:8]

        seen = set()
        techs = []
        for t in data["technologies"]:
            norm = _normalize_tech(t)
            if norm.lower() not in seen:
                seen.add(norm.lower())
                techs.append(norm)
        data["technologies"] = techs[:20]

        data["methodologies"] = data["methodologies"][:6]
        data["education"] = data["education"][:3]
        data["certifications"] = data.get("certifications", [])[:3]

        trimmed_exp = []
        for entry in data["experience"][:5]:
            bullets = [b for b in entry["employer_bullets"] if not _is_generic(b)]
            entry["employer_bullets"] = bullets[:2]

            trimmed_projects = []
            for proj in entry["projects"][:3]:  # max 3 projects per employer
                proj_bullets = [b for b in proj["bullets"] if not _is_generic(b)]
                proj["bullets"] = [_trim_end(b, 130) for b in proj_bullets[:2]]  # max 2 bullets per project
                trimmed_projects.append(proj)
            entry["projects"] = trimmed_projects
            trimmed_exp.append(entry)

        data["experience"] = trimmed_exp
        return ProfileSchema(**data)
