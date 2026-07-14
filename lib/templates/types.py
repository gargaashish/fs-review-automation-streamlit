from dataclasses import dataclass, field
from typing import Callable, Optional, Pattern


@dataclass
class ContentCheck:
    id: str
    test: Callable[[str, str], bool]
    severity_if_failed: str
    issue_type: str
    description: str
    why_it_matters: str
    suggested_question: str


@dataclass
class RequiredSectionDef:
    key: str
    aliases: list[str]
    severity_if_missing: str
    min_word_count: int
    why_it_matters: str
    suggested_question: str
    placeholder_patterns: list[Pattern] = field(default_factory=list)
    content_checks: list[ContentCheck] = field(default_factory=list)


@dataclass
class TemplateDefinition:
    id: str
    name: str
    description: str
    required_sections: list[RequiredSectionDef]
    disallow_extra_sections: bool = False
