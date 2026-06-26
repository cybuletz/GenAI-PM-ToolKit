from core.profile_schema import ProfileSchema

GENERIC_BULLETS = {"responsible for", "worked on", "involved in"}

# Entry 0 = most recent employer (full detail)
# Entry 1 = second employer (moderate detail)
# Entry 2 = aggregated "Previous Experience" (employer_bullets only, no projects)
MAX_PROJECTS = [4, 2, 0]
MAX_BULLETS_PER_PROJECT = [3, 2, 0]
MAX_EMPLOYER_BULLETS = [2, 2, 3]


def _trim_to_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')
    return truncated[:last_period + 1] if last_period > 0 else truncated.rstrip()


def _trim_end(text: str, max_chars: int) -> str:
    return text[:max_chars] if len(text) > max_chars else text


def _is_generic(bullet: str) -> bool:
    lower = bullet.strip().lower()
    return any(lower.startswith(g) for g in GENERIC_BULLETS)


class ProfileTrimmer:
    def trim(self, profile: ProfileSchema) -> ProfileSchema:
        data = profile.model_dump()

        data["profile"] = _trim_to_sentence(data["profile"], 700)
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
            max_bpp = MAX_BULLETS_PER_PROJECT[idx]
            max_eb = MAX_EMPLOYER_BULLETS[idx]

            eb = [b for b in entry["employer_bullets"] if not _is_generic(b)]
            entry["employer_bullets"] = [_trim_end(b, 160) for b in eb[:max_eb]]

            if max_proj == 0:
                entry["projects"] = []
            else:
                trimmed_projects = []
                for proj in entry["projects"][:max_proj]:
                    bullets = [b for b in proj["bullets"] if not _is_generic(b)]
                    proj["bullets"] = [_trim_end(b, 160) for b in bullets[:max_bpp]]
                    trimmed_projects.append(proj)
                entry["projects"] = trimmed_projects

            trimmed_exp.append(entry)

        data["experience"] = trimmed_exp
        return ProfileSchema(**data)
