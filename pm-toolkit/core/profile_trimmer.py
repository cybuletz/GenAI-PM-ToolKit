from core.profile_schema import ProfileSchema

GENERIC_PHRASES = {"responsible for", "worked on", "involved in"}

# 2-entry structure: current employer (up to 5 projects) + previous summary (1 project)
# Frame budget: ~5500 chars at 8pt. Current employer gets the bulk.
MAX_PROJECTS         = [5, 1]      # current: 5 projects, previous summary: 1
MAX_EMPLOYER_BULLETS = [0, 0]      # no employer-level bullets; content goes in projects
MAX_CONTENT_CHARS    = [650, 600]  # per project content ceiling
MAX_BULLET_CHARS     = 200


def _trim_end(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    return truncated[:last_period + 1].strip() if last_period > 0 else truncated.rstrip()


def _is_generic(text: str) -> bool:
    lower = text.strip().lower()
    return any(lower.startswith(g) for g in GENERIC_PHRASES)


class ProfileTrimmer:
    def trim(self, profile: ProfileSchema) -> ProfileSchema:
        data = profile.model_dump()

        data["profile"] = _trim_end(data["profile"], 700)
        data["name"] = _trim_end(data["name"], 60)
        data["role_title"] = _trim_end(data["role_title"], 120)
        data["role_subtitle"] = _trim_end(data["role_subtitle"], 80)
        data["competencies"] = [_trim_end(c, 45) for c in data["competencies"]][:8]

        seen = set()
        techs = []
        for t in data["technologies"]:
            norm = t.strip()
            if norm.lower() not in seen:
                seen.add(norm.lower())
                techs.append(norm)
        data["technologies"] = techs[:15]

        data["methodologies"] = data["methodologies"][:5]
        data["education"] = data["education"][:2]
        data["certifications"] = data.get("certifications", [])[:3]

        trimmed_exp = []
        for idx, entry in enumerate(data["experience"][:2]):
            max_proj = MAX_PROJECTS[idx] if idx < len(MAX_PROJECTS) else 1
            max_cc   = MAX_CONTENT_CHARS[idx] if idx < len(MAX_CONTENT_CHARS) else 400

            # No employer-level bullets in this structure
            entry["employer_bullets"] = []

            trimmed_projects = []
            for proj in entry["projects"][:max_proj]:
                proj["content"] = _trim_end(proj.get("content", ""), max_cc)
                trimmed_projects.append(proj)
            entry["projects"] = trimmed_projects

            trimmed_exp.append(entry)

        data["experience"] = trimmed_exp
        return ProfileSchema(**data)
