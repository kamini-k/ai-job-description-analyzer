import hashlib
from html import escape

import streamlit as st

from analyzer import Analysis, analyze, extract_skills, sample_job_description, text_similarity
from report_generator import csv_report
from resume_parser import ResumeParseError, extract_resume_text
from skill_dictionary import SKILLS, SKILLS_BY_NAME


st.set_page_config(
    page_title="AI Job Description Analyzer",
    page_icon="💼",
    layout="wide",
)

SAMPLE_CANDIDATE = "Python, Git"

ROADMAP_PROJECTS = {
    "Programming languages": "Build a small command-line program in {skill} that solves a real, well-defined problem. Include input validation, clear structure, and a few tests.",
    "Web development": "Build and publish a small, accessible web feature using {skill}. Check it in a browser at both mobile and desktop sizes.",
    "Databases": "Create a small data-backed application using {skill}. Define the data model, implement create/read/update/delete operations, and verify edge cases.",
    "Data and AI": "Use a public or synthetic dataset to build a small {skill} project. Establish a simple baseline, document your method, and evaluate results on data you did not use to build it.",
    "Development tools": "Use {skill} to manage, inspect, test, or deliver a small software project. Record the workflow and verify that another person can follow it.",
    "Computer science fundamentals": "Create a small, runnable demonstration of {skill}. Compare at least two cases or approaches and explain the trade-offs with measured or observable evidence.",
    "Professional skills": "Apply {skill} during a real or practice collaboration. Agree on a goal, communicate progress, ask for feedback, and write a short reflection with a concrete example.",
    "Cloud and DevOps": "Deploy a small application or service using {skill}. Document the setup and verify deployment, logs, access controls, and a safe cleanup or rollback path.",
}

ROADMAP_TOPICS = {
    "Programming languages": (
        "Core syntax, values, and data types",
        "Conditionals, loops, and functions",
        "Collections, modules, and error handling",
        "Readable program structure and basic testing",
        "Applying the language to a small complete program",
    ),
    "Web development": (
        "How browsers, URLs, HTTP requests, and responses work",
        "Semantic page structure and accessible interactions",
        "Responsive styling and browser behavior",
        "Components, application state, and user input",
        "Connecting a frontend to an API and handling errors",
    ),
    "Databases": (
        "Tables or document models, fields, and data types",
        "Creating, reading, updating, and deleting records",
        "Filtering, sorting, joins, and aggregation where applicable",
        "Constraints, indexes, and query performance",
        "Transactions, validation, and safe data changes",
    ),
    "Data and AI": (
        "Data formats, collection, and data quality",
        "Cleaning, exploration, and summary statistics",
        "Core concepts and methods used by the selected tool or field",
        "Building a simple baseline and choosing suitable measures",
        "Validation, limitations, bias, and communicating results",
    ),
    "Development tools": (
        "The tool's purpose, setup, and essential terminology",
        "The everyday workflow and key commands or features",
        "Organizing and documenting work for collaboration",
        "Testing changes and diagnosing common failures",
        "Safe, repeatable use in a small end-to-end project",
    ),
    "Computer science fundamentals": (
        "Core concepts, vocabulary, and common examples",
        "Data or process representation and how it operates",
        "Correctness, edge cases, and failure conditions",
        "Efficiency and trade-offs between approaches",
        "Implementing or tracing a small example",
    ),
    "Professional skills": (
        "The skill's core principles and common workplace situations",
        "Active listening, clear communication, and shared expectations",
        "Breaking work into actions and agreeing on responsibilities",
        "Giving, receiving, and applying constructive feedback",
        "Reflecting on outcomes and identifying a next improvement",
    ),
    "Cloud and DevOps": (
        "Cloud or delivery concepts, terminology, and architecture",
        "Setting up a small development environment or workflow",
        "Deploying and verifying a simple service or automation",
        "Logs, monitoring, permissions, and troubleshooting",
        "Cost awareness, security basics, and safe cleanup or rollback",
    ),
}


def _render_analysis(result: Analysis, candidate_text: str) -> None:
    if not result.requirements:
        st.warning(
            "No known skill requirements were identified. Add explicit required or preferred "
            "skills to the job description for a meaningful comparison."
        )
        return
    if result.overall_score is None:
        st.info(
            "No explicitly required or preferred skills were identified for scoring. "
            "Mentions that could not be confidently classified remain inferred; add clear "
            "requirements to the job description for a meaningful comparison."
        )
        return

    st.subheader("Analysis overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall skill match", f"{result.overall_score:.2f}%")
    c2.metric(
        "Required skill coverage",
        f"{result.required_coverage:.2f}%" if result.required_coverage is not None else "N/A",
    )
    c3.metric(
        "Preferred skill coverage",
        f"{result.preferred_coverage:.2f}%" if result.preferred_coverage is not None else "N/A",
    )
    c4.metric(
        "Matched skills",
        sum(bool(item.candidate_evidence) for item in result.requirements),
    )
    if result.required_coverage is not None:
        st.progress(result.required_coverage / 100, text="Required skill coverage")
    if result.preferred_coverage is not None:
        st.progress(result.preferred_coverage / 100, text="Preferred skill coverage")
    st.caption(
        f"Overall score = weighted average of available required coverage "
        f"({result.required_weight:.0f}%) and preferred coverage "
        f"({result.preferred_weight:.0f}%). Empty categories are excluded and remaining "
        "weights are normalized. Inferred requirements are reported separately."
    )

    required = [item for item in result.requirements if item.requirement_type == "required"]
    preferred = [item for item in result.requirements if item.requirement_type == "preferred"]
    inferred = [item for item in result.requirements if item.requirement_type == "inferred"]
    matched = [item for item in result.requirements if item.candidate_evidence]

    with st.expander(f"Matched skills ({len(matched)})", expanded=True):
        if matched:
            for item in matched:
                with st.container(border=True):
                    st.markdown(f"**{item.skill}**")
                    st.text(
                        f"Category: {item.category}\n"
                        f"Requirement: {item.requirement_type.title()}\n"
                        f"Job evidence: {item.evidence}\n"
                        f"Candidate evidence: {item.candidate_evidence}\n"
                        f"Explanation: {item.explanation}"
                    )
        else:
            st.write("No matching skills were detected in the supplied evidence.")

    for title, items in (
        ("Missing required skills", [item for item in required if not item.candidate_evidence]),
        ("Missing preferred skills", [item for item in preferred if not item.candidate_evidence]),
        ("Unclassified or inferred skills", inferred),
    ):
        with st.expander(f"{title} ({len(items)})"):
            if not items:
                st.write("None identified.")
                continue
            for item in items:
                st.markdown(f"**{item.skill}** · {item.category} · {item.requirement_type.title()}")
                st.write(item.explanation)
                if item.requirement_type != "inferred":
                    st.write(
                        "Next step: add truthful evidence if you have this skill, or practise it "
                        "before claiming it."
                    )

    st.subheader("Keyword coverage")
    st.caption(
        "Keyword coverage is a general text signal, not technical skill coverage or a hiring score."
    )
    if result.keyword_coverage is not None:
        st.metric("Important job keyword coverage", f"{result.keyword_coverage:.2f}%")
    if result.keywords:
        rows = "".join(
            "<tr>"
            f"<td>{escape(item['keyword'])}</td>"
            f"<td>{escape(item['category'])}</td>"
            f"<td>{'Found' if item['found'] == 'yes' else 'Not found'}</td>"
            "</tr>"
            for item in result.keywords
        )
        st.markdown(
            "<table>"
            "<thead><tr><th>Keyword</th><th>Category</th><th>Candidate evidence</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>",
            unsafe_allow_html=True,
        )

    st.subheader("Experience and qualifications")
    st.write(f"**Experience:** {result.experience_alignment}")
    st.write(f"**Qualifications:** {result.qualification_alignment}")

    st.subheader("Resume improvement suggestions")
    for suggestion in result.suggestions:
        st.write(f"- {suggestion}")

    missing_names = [
        item.skill
        for item in result.requirements
        if not item.candidate_evidence and item.requirement_type in {"required", "preferred"}
    ]
    if missing_names:
        st.subheader("Learning roadmap")
        for position, name in enumerate(missing_names, start=1):
            skill = SKILLS_BY_NAME[name]
            with st.expander(f"{position}. Learn {name} · {skill.category}"):
                st.write(f"**Why it matters:** This skill appears in the job description.")
                st.markdown(f"**Where to learn:** [{name} learning resource]({skill.resource})")
                st.markdown("**What to study:**")
                for topic in ROADMAP_TOPICS.get(skill.category, ()):
                    st.markdown(f"- [{topic}]({skill.resource})")
                st.write(
                    "**How to study:** Follow the linked material in order. For each topic, "
                    "read or watch one lesson, recreate its example without copy-pasting, then "
                    "change one detail and note what happens."
                )
                st.write(f"**Practice:** {skill.exercise}")
                project = ROADMAP_PROJECTS.get(
                    skill.category,
                    "Build a small, documented project that demonstrates {skill}.",
                ).format(skill=name)
                st.write(f"**Apply it:** {project}")
                st.write(
                    "**Check your progress:** Test the main behavior and at least one edge "
                    "case, write down what you learned, and practise explaining your choices "
                    "and limitations."
                )
                st.caption(
                    "You are ready to move on when you can complete the practice task, "
                    "explain the core concepts, and show evidence from your project."
                )

    st.subheader("Interview preparation")
    if matched:
        for item in matched[:5]:
            st.write(f"- **Technical:** Explain how you used {item.skill}; cite only real examples.")
            st.write(f"- **Project-based:** What trade-offs would you consider when applying {item.skill}?")
    else:
        st.write("- **Technical:** Which requirements in this role are most familiar to you, and why?")
    st.write("- **Scenario:** How would you approach an unfamiliar requirement in this role?")
    st.write("- **Behavioral:** Describe a real example of collaboration or problem-solving.")

    st.download_button(
        "Download skill analysis (CSV)",
        data=csv_report(result),
        file_name="job_analysis_report.csv",
        mime="text/csv",
        width="stretch",
    )
    st.caption(
        f"Text similarity: {text_similarity(st.session_state.job_description, candidate_text):.2f}%. "
        "Scores are text signals, not an ATS score or prediction of hiring success."
    )


st.title("💼 AI Job Description Analyzer")
st.caption("Compare explicitly identified job requirements with evidence you provide.")
st.session_state.setdefault("reset_generation", 0)

sample_col, reset_col = st.columns([1, 1])
if sample_col.button("Load sample data", width="stretch"):
    st.session_state.job_description = sample_job_description()
    st.session_state.candidate_skills = SAMPLE_CANDIDATE
    st.session_state.analysis = None
if reset_col.button("Reset", width="stretch"):
    st.session_state.reset_generation += 1
    for key in (
        "job_description",
        "candidate_skills",
        "pasted_resume",
        "resume_text",
        "resume_digest",
        "reviewed_resume_digest",
        "reviewed_resume_skills",
        "analysis",
        "resume_error",
    ):
        st.session_state.pop(key, None)
    st.rerun()

left, right = st.columns(2)
with left:
    job_text = st.text_area(
        "Complete job description",
        height=310,
        key="job_description",
        placeholder=(
            "Include the role, responsibilities, qualifications, and clearly labeled "
            "required or preferred skills."
        ),
    )
    required_weight = st.slider("Required skills weight", 0, 100, 80)
    preferred_weight = 100 - required_weight
    st.caption(f"Preferred skills weight: {preferred_weight}%")
with right:
    manual_skills = st.text_area(
        "Candidate skills (manual entry)",
        height=110,
        key="candidate_skills",
        placeholder="Example: Python, SQL, Git",
    )
    pasted_resume = st.text_area(
        "Or paste resume text (optional)",
        height=120,
        key="pasted_resume",
    )
    uploaded_file = st.file_uploader(
        "Upload resume (PDF or DOCX, max 10 MB)",
        type=["pdf", "docx"],
        max_upload_size=10,
        key=f"resume_upload_{st.session_state.reset_generation}",
    )
    uploaded_text = ""
    if uploaded_file is not None:
        upload_data = uploaded_file.getvalue()
        digest = hashlib.sha256(upload_data).hexdigest()
        if st.session_state.get("resume_digest") != digest:
            st.session_state.resume_digest = digest
            st.session_state.resume_text = ""
            st.session_state.resume_error = ""
            st.session_state.reviewed_resume_skills = []
            try:
                st.session_state.resume_text = extract_resume_text(uploaded_file.name, upload_data)
            except ResumeParseError as exc:
                st.session_state.resume_error = str(exc)
        if st.session_state.get("resume_error"):
            st.error(st.session_state.resume_error)
        uploaded_text = st.session_state.get("resume_text", "")
        if uploaded_text:
            st.success("Resume text extracted locally.")
            with st.expander("Review extracted resume text"):
                st.text_area("Extracted text preview", uploaded_text, height=180, disabled=True)
    elif st.session_state.get("resume_digest"):
        st.session_state.resume_digest = None
        st.session_state.resume_text = ""
        st.session_state.reviewed_resume_skills = []

resume_text = "\n".join(part for part in (uploaded_text, pasted_resume) if part.strip())
resume_skills = extract_skills(resume_text)
if resume_text.strip():
    st.markdown("**Review skills detected in resume text**")
    review_digest = hashlib.sha256(resume_text.encode("utf-8")).hexdigest()
    if st.session_state.get("reviewed_resume_digest") != review_digest:
        st.session_state.reviewed_resume_digest = review_digest
        st.session_state.reviewed_resume_skills = resume_skills
    st.session_state.reviewed_resume_skills = [
        name
        for name in st.session_state.reviewed_resume_skills
        if name in {item.name for item in SKILLS}
    ]
    reviewed_skills = st.multiselect(
        "Confirm or remove detected skills; you may also add skills you genuinely have",
        options=[item.name for item in SKILLS],
        key="reviewed_resume_skills",
    )
else:
    reviewed_skills = []

analyze_button = st.button("🔎 Analyze job", type="primary", width="stretch")
if analyze_button:
    if not job_text.strip():
        st.warning("Enter the job description before analyzing.")
        st.session_state.analysis = None
    elif not (manual_skills.strip() or resume_text.strip()):
        st.info(
            "Enter candidate skills, paste resume text, or upload a readable resume. "
            "No score is calculated without candidate evidence."
        )
        st.session_state.analysis = None
    elif not (required_weight + preferred_weight):
        st.error("At least one matching weight must be greater than zero.")
        st.session_state.analysis = None
    else:
        with st.spinner("Comparing job requirements with candidate evidence..."):
            candidate_text = "\n".join(
                part
                for part in (manual_skills, resume_text, "\n".join(reviewed_skills))
                if part.strip()
            )
            allowed_skills = sorted(
                set(extract_skills(manual_skills))
                | set(reviewed_skills)
            )
            st.session_state.analysis = analyze(
                job_text,
                candidate_text,
                required_weight=required_weight,
                preferred_weight=preferred_weight,
                candidate_skill_names=allowed_skills,
            )

if st.session_state.get("analysis") is not None:
    candidate_text = "\n".join(
        part
        for part in (
            st.session_state.get("candidate_skills", ""),
            st.session_state.get("pasted_resume", ""),
            st.session_state.get("resume_text", ""),
            "\n".join(st.session_state.get("reviewed_resume_skills", [])),
        )
        if part.strip()
    )
    st.divider()
    _render_analysis(st.session_state.analysis, candidate_text)

with st.sidebar:
    st.header("How matching works")
    st.write("Local deterministic phrase matching; no Gemini API key is required.")
    st.write(
        "Only requirements marked required/preferred are scored in those categories. "
        "Unclassified mentions remain inferred."
    )
    st.caption(
        "Resume processing is local. PDF OCR is not included. Learning suggestions are "
        "recommendations, not claims about completed training."
    )
