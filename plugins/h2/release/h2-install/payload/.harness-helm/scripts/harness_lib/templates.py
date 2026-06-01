from __future__ import annotations


CANONICAL_TEMPLATES = {
    "plan": "plan.md",
    "design": "design.md",
    "analysis": "analysis.md",
    "review": "review.md",
    "report": "report.md",
    "domain": "domain.md",
    "spec": "spec.md",
    "decision": "decision.md",
    "solution": "solution.md",
    "convention": "convention.md",
    "learning": "learning.md",
    "runbook": "runbook.md",
    "incident": "incident.md",
    "release": "release.md",
}
TEMPLATE_TARGETS = {
    "plan": "docs/01_plan/{feature}.md",
    "design": "docs/02_design/{feature}.md",
    "analysis": "docs/02_design/{feature}.analysis.md",
    "review": "docs/03_review/code/{feature}.md",
    "report": "docs/04_report/{feature}.md",
    "domain": "docs/10_domain/{domain}/{topic}.md",
    "spec": "docs/20_specs/{area}/{topic}.md",
    "decision": "docs/30_decisions/project/{number}-{topic}.{status}.md",
    "solution": "docs/40_knowledge/solutions/{topic}.md",
    "convention": "docs/40_knowledge/conventions/{topic}.md",
    "learning": "docs/40_knowledge/learnings/{topic}.md",
    "runbook": "docs/50_operations/runbooks/{topic}.md",
    "incident": "docs/50_operations/incidents/{topic}.md",
    "release": "docs/50_operations/releases/{topic}.md",
}
