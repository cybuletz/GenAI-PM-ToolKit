import re
from core.profile_schema import ProfileSchema

GENERIC_BULLETS = {"responsible for", "worked on", "involved in"}

# KEY_PROJECTS content limits
# Reference PPTX (manually done) had: 2-3 employers, 3-5 projects each, 2-3 bullets each
# All at sz=800, 100% line spacing - compact continuous flow
MAX_EMPLOYERS = 3
MAX_PROJECTS_PER_EMPLOYER = 4  # project names are short, pack well
MAX_BULLETS_PER_PROJECT = 2


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
        data["technologies"] = techs[:15]

        data["methodologies"] = data["methodologies"][:5]
        data["education"] = data["education"][:2]
        data["certifications"] = data.get("certifications", [])[:3]

        trimmed_exp = []
        for entry in data["experience"][:MAX_EMPLOYERS]:
            # Drop employer-level bullets entirely - project bullets carry the content
            entry["employer_bullets"] = []
            trimmed_projects = []
            for proj in entry["projects"][:MAX_PROJECTS_PER_EMPLOYER]:
                proj_bullets = [b for b in proj["bullets"] if not _is_generic(b)]
                proj["bullets"] = [
                    _trim_end(b, 120) for b in proj_bullets[:MAX_BULLETS_PER_PROJECT]
                ]
                trimmed_projects.append(proj)
            entry["projects"] = trimmed_projects
            trimmed_exp.append(entry)

        data["experience"] = trimmed_exp
        return ProfileSchema(**data)
