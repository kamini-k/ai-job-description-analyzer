"""Standard-library report creation."""

from __future__ import annotations

import csv
from io import StringIO

from analyzer import Analysis


def csv_report(analysis: Analysis) -> bytes:
    output = StringIO(newline="")
    fields = (
        "Skill",
        "Category",
        "Requirement",
        "Importance",
        "Status",
        "Candidate evidence",
        "Explanation",
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for requirement in analysis.requirements:
        writer.writerow(
            {
                "Skill": requirement.skill,
                "Category": requirement.category,
                "Requirement": requirement.requirement_type,
                "Importance": requirement.importance,
                "Status": "Matched" if requirement.candidate_evidence else "Not found",
                "Candidate evidence": requirement.candidate_evidence,
                "Explanation": requirement.explanation,
            }
        )
    return output.getvalue().encode("utf-8-sig")
