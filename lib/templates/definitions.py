from lib.templates.types import RequiredSectionDef, TemplateDefinition
from lib.templates.checks import (
    GENERIC_PLACEHOLDER_PATTERNS,
    transport_approval_email_check,
    testing_results_check,
)


def _sec(key, aliases, severity, min_words, why, question, placeholders=None, checks=None):
    return RequiredSectionDef(
        key=key,
        aliases=aliases,
        severity_if_missing=severity,
        min_word_count=min_words,
        why_it_matters=why,
        suggested_question=question,
        placeholder_patterns=placeholders or [],
        content_checks=checks or [],
    )


COMPANY_SOLUTION_DESIGN_TEMPLATE = TemplateDefinition(
    id="company-solution-design",
    name="Company FS Template (Solution Design Document)",
    description="Matches the company's Solution Design Document FS template, including transport approval and testing-results checks.",
    disallow_extra_sections=True,
    required_sections=[
        _sec(
            "fs_summary",
            ["functional specification summary"],
            "Critical Missing",
            20,
            "Without a clear summary, reviewers cannot quickly judge the context, problem, and proposed solution before reading the full document.",
            "Can you write a single-paragraph summary covering the context, the problem, and the proposed solution?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "transport_request_approval",
            ["transport request approval"],
            "Critical Missing",
            5,
            "A transport request moved without documented approval cannot be audited and may violate change-control policy.",
            "Who approved this transport request, and can the approval email or written confirmation be attached here?",
            checks=[transport_approval_email_check],
        ),
        _sec(
            "background_context",
            ["background and context"],
            "Important Gap",
            20,
            "Without background and context, reviewers cannot judge whether the proposed solution actually fits the underlying business situation.",
            "What is the business background and context driving this change?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "requirements",
            ["requirements"],
            "Critical Missing",
            25,
            "Undefined requirements are the most common cause of rework and scope disputes during build.",
            "Can you break down the specific functional requirements this change must deliver?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "dependencies_constraints",
            ["dependencies / constraints", "dependencies/constraints", "dependencies", "constraints"],
            "Important Gap",
            10,
            "Unstated dependencies and constraints often surface late as blockers during build or testing.",
            "What internal/external dependencies or constraints (schedule, access, data) affect this build?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "security_authorization",
            [
                "security, authorization, integrity, and controls",
                "security authorization integrity and controls",
                "security",
            ],
            "Critical Missing",
            10,
            "Security and authorization gaps found after go-live are expensive to fix and can trigger audit findings.",
            "What security, authorization, or data integrity considerations apply to this change, and who owns them?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "technical_specification",
            ["technical specification / solution", "technical specification/solution", "technical specification"],
            "Important Gap",
            15,
            "Without real technical detail, developers cannot estimate or build the solution without going back to the author.",
            "Can you add the architecture, data flow, configuration, and error-handling detail for this solution?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
        ),
        _sec(
            "test_results",
            ["test results", "testing", "unit testing evidence"],
            "Critical Missing",
            10,
            "Without recorded test results, the manager cannot confirm the change was actually validated before go-live.",
            "Can you attach the executed test cases with expected/actual output and pass/fail status?",
            placeholders=GENERIC_PLACEHOLDER_PATTERNS,
            checks=[testing_results_check],
        ),
    ],
)

TEMPLATES: list[TemplateDefinition] = [COMPANY_SOLUTION_DESIGN_TEMPLATE]


def get_template_by_id(template_id: str) -> TemplateDefinition:
    for t in TEMPLATES:
        if t.id == template_id:
            return t
    raise ValueError(f"Unknown template id: {template_id}")
