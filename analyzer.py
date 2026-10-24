"""Deterministic skill extraction, requirement classification, and scoring."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass

from skill_dictionary import SKILLS


@dataclass(frozen=True)
class Requirement:
    skill: str
    category: str
    requirement_type: str
    importance: float
    evidence: str
    candidate_evidence: str
    explanation: str


@dataclass(frozen=True)
class Analysis:
    requirements: tuple[Requirement, ...]
    required_coverage: float | None
    preferred_coverage: float | None
    overall_score: float | None
    required_weight: float
    preferred_weight: float
    keywords: tuple[dict[str, str], ...]
    keyword_coverage: float | None
    suggestions: tuple[str, ...]
    experience_alignment: str
    qualification_alignment: str

    def as_dict(self) -> dict:
        result = asdict(self)
        result["requirements"] = [asdict(item) for item in self.requirements]
        return result


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\+\+|#)?|[+#]+", re.IGNORECASE)
_STOP_WORDS = frozenset(
    "a an and are as at be been being by can candidate company could developer "
    "does engineer for from have in into is it job looking must of on or our "
    "preferred qualified required requirements role should skills software the "
    "their this to we with will work years".split()
)
_REQUIRED_CUES = re.compile(
    r"\b(required|requirements|requiring|must have|must|required skills|proficient in|"
    r"proficiency in|experience with|expertise in|strong knowledge of|"
    r"knowledge of|qualification[s]?)\b",
    re.IGNORECASE,
)
_PREFERRED_CUES = re.compile(
    r"\b(preferred|nice to have|bonus|ideally|a plus|optional|desirable)\b",
    re.IGNORECASE,
)
_QUALIFICATION_CUES = re.compile(
    r"\b(bachelor|master|degree|diploma|certification|certified|qualification)\b",
    re.IGNORECASE,
)
_EXPERIENCE_CUES = re.compile(
    r"\b(\d+\+?\s+years?|experience|experienced)\b", re.IGNORECASE
)
_QUALIFICATION_TERMS = ("bachelor", "master", "degree", "diploma", "certification")
_RESPONSIBILITY_TERMS = (
    "build", "develop", "design", "maintain", "collaborate", "lead", "support",
    "implement", "deliver", "manage", "analyze",
)


def normalize_phrase(text: str) -> str:
    """Normalize case and punctuation while retaining C/C++ distinctions."""
    return " ".join(token.lower() for token in _TOKEN_RE.findall(text))


_ALIASES: list[tuple[str, str, str, tuple[str, ...]]] = sorted(
    (
        (normalize_phrase(alias), skill.name, skill.category, tuple(_TOKEN_RE.findall(alias)))
        for skill in SKILLS
        for alias in (skill.name, *skill.aliases)
    ),
    key=lambda item: (-len(item[3]), -len(item[0])),
)


def _matches_in(text: str) -> list[tuple[str, str, str]]:
    normalized = normalize_phrase(text)
    tokens = normalized.split()
    matches: list[tuple[int, int, str, str, str]] = []
    for alias, canonical, category, alias_tokens in _ALIASES:
        size = len(alias_tokens)
        for start in range(len(tokens) - size + 1):
            if tokens[start : start + size] == list(alias_tokens):
                matches.append((start, start + size, canonical, category, alias))
    selected: list[tuple[str, str, str]] = []
    occupied: set[int] = set()
    seen: set[str] = set()
    for start, end, canonical, category, alias in sorted(
        matches, key=lambda item: (-(item[1] - item[0]), item[0], item[2])
    ):
        if canonical in seen or any(index in occupied for index in range(start, end)):
            continue
        occupied.update(range(start, end))
        seen.add(canonical)
        selected.append((canonical, category, alias))
    return selected


def extract_skills(text: str) -> list[str]:
    return sorted({name for name, _, _ in _matches_in(text)})


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _classify_sentence(sentence: str, section: str) -> tuple[str, float]:
    if _PREFERRED_CUES.search(sentence) or section == "preferred":
        return "preferred", 1.0
    if _REQUIRED_CUES.search(sentence) or section == "required":
        return "required", 1.0
    return "inferred", 0.5


def _section_for(sentence: str, current: str) -> str:
    header = sentence.strip(" :-").lower()
    if re.match(r"^(preferred|nice to have|bonus|optional)\b", header):
        return "preferred"
    if re.match(r"^(required|must have|requirements)\b", header):
        return "required"
    if re.match(r"^(responsibilities|about us|company overview|what you.ll do)\b", header):
        return "incidental"
    if re.match(r"^(qualifications|what you.ll need|what we.re looking for)\b", header):
        return "required"
    return current


def _find_candidate_evidence(candidate_text: str, skill_name: str) -> str:
    skill = next(item for item in SKILLS if item.name == skill_name)
    aliases = sorted((skill.name, *skill.aliases), key=len, reverse=True)
    for sentence in _sentences(candidate_text):
        if any(_matches_in(sentence) and name == skill_name for name, _, _ in _matches_in(sentence)):
            return sentence[:240]
        if any(normalize_phrase(alias) in normalize_phrase(sentence) for alias in aliases):
            return sentence[:240]
    return ""


def _coverage(items: list[Requirement]) -> float | None:
    if not items:
        return None
    total = sum(item.importance for item in items)
    matched = sum(item.importance for item in items if item.candidate_evidence)
    return round(matched / total * 100, 2) if total else None


def text_similarity(job_text: str, candidate_text: str) -> float:
    """Return a local TF-IDF cosine similarity percentage."""
    documents = [
        [token.lower() for token in _TOKEN_RE.findall(text)]
        for text in (job_text, candidate_text)
    ]
    if not all(documents):
        return 0.0
    counts = [Counter(document) for document in documents]
    vocabulary = counts[0].keys() | counts[1].keys()
    vectors = []
    for document_counts in counts:
        weights = {
            term: frequency * (math.log(3 / (1 + sum(term in item for item in counts))) + 1)
            for term, frequency in document_counts.items()
        }
        magnitude = math.sqrt(sum(value * value for value in weights.values()))
        vectors.append({term: value / magnitude for term, value in weights.items()})
    return round(
        sum(value * vectors[1].get(term, 0) for term, value in vectors[0].items()) * 100,
        2,
    )


def _extract_keywords(
    job_text: str,
    candidate_text: str,
    allowed_skills: set[str] | None = None,
) -> tuple[dict[str, str], ...]:
    records: dict[tuple[str, str], dict[str, str]] = {}
    job_skills = _matches_in(job_text)
    for name, category, _ in job_skills:
        kind = "professional skills" if category == "Professional skills" else "technical skills"
        found = (
            bool(_find_candidate_evidence(candidate_text, name))
            and (allowed_skills is None or name in allowed_skills)
        )
        records[(name, kind)] = {
            "keyword": name,
            "category": kind,
            "found": "yes" if found else "no",
        }
    words = [
        word.lower()
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", job_text)
        if word.lower() not in _STOP_WORDS
    ]
    for word, _ in Counter(words).most_common(12):
        if any(word in name.lower().split() for name, _, _ in job_skills):
            continue
        if word in _QUALIFICATION_TERMS:
            category = "qualifications"
        elif word in {"year", "years", "experience"}:
            category = "experience-related terms"
        elif word in _RESPONSIBILITY_TERMS:
            category = "responsibilities"
        else:
            category = "general domain terms"
        found = bool(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", candidate_text, re.IGNORECASE))
        records[(word, category)] = {
            "keyword": word,
            "category": category,
            "found": "yes" if found else "no",
        }
    return tuple(records.values())


def analyze(
    job_text: str,
    candidate_text: str,
    required_weight: float = 80,
    preferred_weight: float = 20,
    candidate_skill_names: list[str] | None = None,
) -> Analysis:
    if required_weight < 0 or preferred_weight < 0 or required_weight + preferred_weight <= 0:
        raise ValueError("Weights must be non-negative and at least one must be positive.")
    weight_sum = required_weight + preferred_weight
    required_weight = required_weight / weight_sum * 100
    preferred_weight = preferred_weight / weight_sum * 100

    candidates = [sentence for sentence in _sentences(job_text)]
    section = "unclassified"
    requirements_by_skill: dict[str, tuple[str, float, str]] = {}
    for sentence in candidates:
        section = _section_for(sentence, section)
        if section == "incidental":
            continue
        requirement_type, importance = _classify_sentence(sentence, section)
        for name, _, _ in _matches_in(sentence):
            previous = requirements_by_skill.get(name)
            if previous is None or requirement_type == "required" and previous[0] != "required":
                requirements_by_skill[name] = (requirement_type, importance, sentence[:240])

    requirements: list[Requirement] = []
    allowed_skills = (
        set(candidate_skill_names)
        if candidate_skill_names is not None
        else set(extract_skills(candidate_text))
    )
    for name, (requirement_type, importance, job_evidence) in sorted(requirements_by_skill.items()):
        skill = next(item for item in SKILLS if item.name == name)
        evidence = (
            _find_candidate_evidence(candidate_text, name)
            if candidate_text.strip() and name in allowed_skills
            else ""
        )
        status = (
            f"Matched: candidate evidence contains {name}."
            if evidence
            else f"Not found in the provided candidate evidence; this does not establish that the candidate lacks the skill."
        )
        requirements.append(
            Requirement(
                skill=name,
                category=skill.category,
                requirement_type=requirement_type,
                importance=importance,
                evidence=job_evidence,
                candidate_evidence=evidence,
                explanation=status,
            )
        )
    required = [item for item in requirements if item.requirement_type == "required"]
    preferred = [item for item in requirements if item.requirement_type == "preferred"]
    inferred = [item for item in requirements if item.requirement_type == "inferred"]
    candidate_provided = bool(candidate_text.strip())
    required_coverage = _coverage(required) if candidate_provided else None
    preferred_coverage = _coverage(preferred) if candidate_provided else None
    score_groups = []
    if required_coverage is not None:
        score_groups.append((required_coverage, required_weight))
    if preferred_coverage is not None:
        score_groups.append((preferred_coverage, preferred_weight))
    if inferred and candidate_provided:
        score_groups.append((_coverage(inferred) or 0, max(0, 100 - required_weight - preferred_weight)))
    effective_weight = sum(weight for _, weight in score_groups)
    overall = (
        round(sum(score * weight for score, weight in score_groups) / effective_weight, 2)
        if score_groups and effective_weight
        else None
    )

    keywords = _extract_keywords(
        job_text,
        candidate_text,
        allowed_skills if candidate_skill_names is not None else None,
    )
    keyword_coverage = (
        round(sum(item["found"] == "yes" for item in keywords) / len(keywords) * 100, 2)
        if candidate_provided and keywords
        else None
    )
    suggestions = _suggestions(requirements)
    experience_alignment = _alignment(_EXPERIENCE_CUES, job_text, candidate_text)
    qualification_alignment = _alignment(_QUALIFICATION_CUES, job_text, candidate_text)
    return Analysis(
        tuple(requirements),
        required_coverage,
        preferred_coverage,
        overall,
        round(required_weight, 2),
        round(preferred_weight, 2),
        keywords,
        keyword_coverage,
        tuple(suggestions),
        experience_alignment,
        qualification_alignment,
    )


def _alignment(pattern: re.Pattern, job_text: str, candidate_text: str) -> str:
    if not pattern.search(job_text):
        return "No explicit requirement identified."
    if not candidate_text.strip():
        return "Not assessed because no candidate evidence was provided."
    return (
        "Relevant terms appear in the candidate evidence; review context manually."
        if pattern.search(candidate_text)
        else "Not found in the provided candidate evidence; review the resume for context."
    )


def _suggestions(requirements: list[Requirement]) -> list[str]:
    matched = [item.skill for item in requirements if item.candidate_evidence]
    missing = [item.skill for item in requirements if not item.candidate_evidence]
    suggestions = []
    if matched:
        suggestions.append(
            "Consider making existing evidence for " + ", ".join(matched) + " easy to find in the resume."
        )
    if missing:
        suggestions.append(
            "If you genuinely have experience with " + ", ".join(missing) +
            ", add accurate evidence; otherwise practise before listing these skills."
        )
    if not suggestions:
        suggestions.append("Add a job description with clear requirements and provide candidate evidence for a useful comparison.")
    return suggestions


def sample_job_description() -> str:
    return (
        "Software Engineer\n\nResponsibilities: Build and maintain services and collaborate with the team.\n"
        "Company overview: We serve customers across several industries.\n\n"
        "Required skills: Python, SQL, Git, and communication.\n"
        "Preferred: Docker and machine learning."
    )
