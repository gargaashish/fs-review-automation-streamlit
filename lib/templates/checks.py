import re
from lib.templates.types import ContentCheck

# Generic instructional-boilerplate detector, based on conventions common to
# corporate document templates in general (imperative "fill this in" phrasing,
# angle-bracket placeholders, TBD/NA markers) - not tied to any single
# organization's specific template wording.
GENERIC_PLACEHOLDER_PATTERNS: list[re.Pattern] = [
    re.compile(r"<<[^<>]{0,300}>>"),
    re.compile(r"\[\[[^\[\]]{0,300}\]\]"),
    re.compile(
        r"^\s*(specify|explain|describe|detail|indicate|outline|provide|summarize|list)\s+(the|any|what|how|all)\b[^.\n]{0,300}\.?",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(r"\bTBD\b"),
    re.compile(r"^\s*N/A\s*$", re.IGNORECASE | re.MULTILINE),
]

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_APPROVAL_KEYWORDS = re.compile(r"\b(approved|approval|from:|sent:|subject:|to:|re:)\b", re.IGNORECASE)

transport_approval_email_check = ContentCheck(
    id="transport-approval-email",
    test=lambda stripped, raw: bool(_EMAIL_PATTERN.search(stripped)) or bool(_APPROVAL_KEYWORDS.search(stripped)),
    severity_if_failed="Critical Missing",
    issue_type="Missing Transport Request Approval Evidence",
    description=(
        "This section does not contain a pasted approval email, sender/subject line, or explicit approver "
        "confirmation for the transport request."
    ),
    why_it_matters=(
        "Without documented approval evidence, the transport request cannot be audited or confirmed as "
        "authorized before it moves to production."
    ),
    suggested_question=(
        "Can you paste the approval email (From, Subject, approver name) or an equivalent written approval "
        "into this section?"
    ),
)

_TEST_RESULT_KEYWORDS = re.compile(
    r"\b(pass|fail|test case|test result|executed|expected output|actual output)\b", re.IGNORECASE
)

testing_results_check = ContentCheck(
    id="testing-results-evidence",
    test=lambda stripped, raw: bool(_TEST_RESULT_KEYWORDS.search(stripped)) and len(stripped.split()) >= 10,
    severity_if_failed="Critical Missing",
    issue_type="Missing Testing Results",
    description=(
        "This section does not contain concrete testing results (test cases, expected/actual output, or "
        "pass/fail status)."
    ),
    why_it_matters="Without recorded test results, the manager cannot confirm the change was actually validated before go-live.",
    suggested_question="Can you add the executed test cases and their pass/fail outcomes to this section?",
)
