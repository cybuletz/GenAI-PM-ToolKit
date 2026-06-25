import pytest
from unittest.mock import MagicMock
import json
from core.profile_extractor import ProfileExtractor
from core.profile_schema import ProfileSchema

SAMPLE_JSON = {
    "name": "Jane Smith",
    "role_title": "Senior Project Manager | Digital Transformation",
    "role_subtitle": "Senior Project Manager",
    "profile": "Jane Smith is a senior project manager with over 10 years of experience delivering digital transformation programmes across financial services and retail sectors.",
    "competencies": ["Agile Delivery", "Stakeholder Management", "Risk Management", "Budget Control"],
    "education": ["MSc Computer Science, University of Edinburgh, 2010"],
    "certifications": ["PMP", "PRINCE2 Practitioner"],
    "methodologies": ["Scrum", "Kanban", "PRINCE2"],
    "technologies": ["Jira", "Confluence", "Azure DevOps", "Salesforce"],
    "experience": [
        {
            "employer": "Acme Corp",
            "role": "Senior PM",
            "date_range": "2020–2024",
            "employer_bullets": ["Led delivery of a £5M digital platform migration."],
            "projects": [
                {
                    "project_name": "Core Banking Migration",
                    "date_range": "2021–2023",
                    "bullets": ["Managed a 40-person cross-functional team.", "Delivered on time and within budget."]
                }
            ]
        }
    ]
}


def test_extract_returns_schema():
    mock_client = MagicMock()
    mock_client.complete.return_value = json.dumps(SAMPLE_JSON)
    extractor = ProfileExtractor(mock_client)
    result = extractor.extract("Some raw profile text")
    assert isinstance(result, ProfileSchema)
    assert result.name == "Jane Smith"


def test_no_first_person_in_profile():
    mock_client = MagicMock()
    mock_client.complete.return_value = json.dumps(SAMPLE_JSON)
    extractor = ProfileExtractor(mock_client)
    result = extractor.extract("Some raw profile text")
    profile_lower = result.profile.lower()
    for word in [" i ", " my ", " we ", " our "]:
        assert word not in profile_lower, f"First-person language found: '{word}'"


def test_list_length_limits():
    mock_client = MagicMock()
    data = dict(SAMPLE_JSON)
    data["competencies"] = [f"Comp {i}" for i in range(12)]
    data["technologies"] = [f"Tech {i}" for i in range(25)]
    mock_client.complete.return_value = json.dumps(data)
    extractor = ProfileExtractor(mock_client)
    result = extractor.extract("Some raw profile text")
    # Schema itself does not enforce limits — trimmer does. Just assert we get a schema back.
    assert isinstance(result, ProfileSchema)
    assert len(result.competencies) == 12


def test_strip_markdown_fences():
    mock_client = MagicMock()
    mock_client.complete.return_value = "```json\n" + json.dumps(SAMPLE_JSON) + "\n```"
    extractor = ProfileExtractor(mock_client)
    result = extractor.extract("text")
    assert result.name == "Jane Smith"


def test_invalid_json_raises_value_error():
    mock_client = MagicMock()
    mock_client.complete.return_value = "This is not JSON at all."
    extractor = ProfileExtractor(mock_client)
    with pytest.raises(ValueError, match="invalid JSON"):
        extractor.extract("text")
