import pytest
from core.profile_schema import ProfileSchema, ExperienceEntry, ProjectEntry
from core.profile_trimmer import ProfileTrimmer


def _make_oversized_profile() -> ProfileSchema:
    return ProfileSchema(
        name="A" * 80,
        role_title="B" * 150,
        role_subtitle="C" * 100,
        profile="Word. " * 120,
        competencies=[f"Competency number {i} with extra words" for i in range(12)],
        education=[f"University {i}" for i in range(6)],
        certifications=[f"Cert {i}" for i in range(6)],
        methodologies=[f"Method {i}" for i in range(10)],
        technologies=["Python", "python", "Java", "Java", "Azure", "AWS", "GCP", "Docker",
                      "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitLab",
                      "Jira", "Confluence", "Salesforce", "SAP", "Oracle", "MySQL",
                      "PostgreSQL", "MongoDB", "Redis", "Kafka"],
        experience=[
            ExperienceEntry(
                employer=f"Employer {i}",
                role="PM",
                date_range="2020–2024",
                employer_bullets=[
                    "Led cross-functional delivery team.",
                    "Managed programme budget.",
                    "Responsible for stakeholder reporting.",
                ],
                projects=[
                    ProjectEntry(
                        project_name=f"Project {j}",
                        date_range="2021–2022",
                        bullets=[
                            "Delivered platform on schedule.",
                            "Worked on integration layer.",
                            "Migrated legacy data to cloud.",
                            "Involved in testing cycles.",
                            "Automated CI/CD pipeline deployment.",
                        ]
                    ) for j in range(6)
                ]
            ) for i in range(7)
        ]
    )


def test_all_limits_enforced():
    trimmer = ProfileTrimmer()
    trimmed = trimmer.trim(_make_oversized_profile())

    assert len(trimmed.name) <= 60
    assert len(trimmed.role_title) <= 120
    assert len(trimmed.role_subtitle) <= 80
    assert len(trimmed.profile) <= 600
    assert len(trimmed.competencies) <= 8
    for c in trimmed.competencies:
        assert len(c) <= 45
    assert len(trimmed.education) <= 3
    assert len(trimmed.certifications) <= 3
    assert len(trimmed.methodologies) <= 6
    assert len(trimmed.technologies) <= 20
    assert len(trimmed.experience) <= 5


def test_generic_bullets_removed():
    trimmer = ProfileTrimmer()
    trimmed = trimmer.trim(_make_oversized_profile())
    for entry in trimmed.experience:
        for b in entry.employer_bullets:
            assert not b.lower().startswith("responsible for")
            assert not b.lower().startswith("worked on")
            assert not b.lower().startswith("involved in")
        for proj in entry.projects:
            for b in proj.bullets:
                assert not b.lower().startswith("responsible for")
                assert not b.lower().startswith("worked on")
                assert not b.lower().startswith("involved in")


def test_tech_deduplication():
    trimmer = ProfileTrimmer()
    trimmed = trimmer.trim(_make_oversized_profile())
    lower_techs = [t.lower() for t in trimmed.technologies]
    assert len(lower_techs) == len(set(lower_techs)), "Duplicate technologies found"


def test_project_bullets_trimmed_to_130():
    trimmer = ProfileTrimmer()
    trimmed = trimmer.trim(_make_oversized_profile())
    for entry in trimmed.experience:
        for proj in entry.projects:
            for b in proj.bullets:
                assert len(b) <= 130
