from core.profile_schema import ProfileSchema

GENERIC_PHRASES = {"responsible for", "worked on", "involved in"}

# Frame: 36 lines capacity. Layout uses ~25 lines leaving 11 buffer for content wrapping.
# Content char limits set to use that space well without overflowing.
MAX_PROJECTS       = [4, 2, 0]
MAX_EMPLOYER_BULLETS = [2, 2, 2]
MAX_CONTENT_CHARS  = [320, 250, 0]   # project paragraph per tier
MAX_BULLET_CHARS   = 180             # employer_bullets


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
        for idx, entry in enumerate(data["experience"][:3]):
            max_proj = MAX_PROJECTS[idx]
            max_eb   = MAX_EMPLOYER_BULLETS[idx]
            max_cc   = MAX_CONTENT_CHARS[idx]

            eb = [b for b in entry["employer_bullets"] if not _is_generic(b)]
            entry["employer_bullets"] = [_trim_end(b, MAX_BULLET_CHARS) for b in eb[:max_eb]]

            if max_proj == 0:
                entry["projects"] = []
            else:
                trimmed_projects = []
                for proj in entry["projects"][:max_proj]:
                    proj["content"] = _trim_end(proj.get("content", ""), max_cc)
                    trimmed_projects.append(proj)
                entry["projects"] = trimmed_projects

            trimmed_exp.append(entry)

        data["experience"] = trimmed_exp
        return ProfileSchema(**data)
