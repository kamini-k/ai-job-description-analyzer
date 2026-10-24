import csv
import io
import unittest
from zipfile import ZipFile

from pypdf import PdfWriter

from analyzer import analyze, extract_skills, normalize_phrase
from report_generator import csv_report
from resume_parser import ResumeParseError, extract_resume_text


class SkillExtractionTests(unittest.TestCase):
    def test_normalizes_punctuation_and_case(self):
        self.assertEqual(normalize_phrase(" POSTGRE SQL "), "postgre sql")
        self.assertEqual(extract_skills("Postgre SQL"), ["PostgreSQL"])

    def test_aliases_map_to_canonical_skills(self):
        examples = {
            "JS": "JavaScript",
            "React.js": "React",
            "ReactJS": "React",
            "OOPs": "Object-oriented programming",
            "DSA": "Data structures and algorithms",
            "RESTful API": "REST API",
            "ML": "Machine learning",
            "DL": "Deep learning",
            "GCP": "Google Cloud",
            "MS Azure": "Microsoft Azure",
            "NodeJS": "Node.js",
        }
        for alias, canonical in examples.items():
            with self.subTest(alias=alias):
                self.assertEqual(extract_skills(alias), [canonical])

    def test_multi_word_skills_and_longest_phrase(self):
        self.assertEqual(
            extract_skills("Data structures and algorithms, generative AI, web development"),
            ["Data structures and algorithms", "Generative AI", "Web development"],
        )
        self.assertEqual(
            extract_skills("C++ and C language"),
            ["C", "C++"],
        )

    def test_no_substring_or_generic_title_matches(self):
        self.assertEqual(extract_skills("Software Engineer"), [])
        self.assertEqual(extract_skills("candidate has excellent communication"), ["Communication"])
        self.assertNotIn("C", extract_skills("The candidate can communicate clearly."))
        self.assertNotIn("C", extract_skills("The candidate used C# tooling."))
        self.assertEqual(extract_skills("JavaScript"), ["JavaScript"])


class MatchingTests(unittest.TestCase):
    def test_backend_required_coverage_and_evidence(self):
        result = analyze(
            "Software Engineer required skills: Python, SQL, Git, and communication.",
            "Python, Git",
        )
        self.assertEqual(
            [item.skill for item in result.requirements if item.candidate_evidence],
            ["Git", "Python"],
        )
        self.assertEqual(
            [item.skill for item in result.requirements if not item.candidate_evidence],
            ["Communication", "SQL"],
        )
        self.assertEqual(result.required_coverage, 50.0)
        self.assertEqual(result.overall_score, 50.0)
        self.assertTrue(all(item.explanation for item in result.requirements))
        self.assertTrue(all(item.evidence for item in result.requirements))

    def test_frontend_match(self):
        result = analyze(
            "Frontend Developer requiring HTML, CSS, JavaScript, and React.",
            "HTML, CSS, React",
        )
        self.assertEqual(result.required_coverage, 75.0)
        self.assertEqual(
            [item.skill for item in result.requirements if not item.candidate_evidence],
            ["JavaScript"],
        )

    def test_preferred_coverage_and_empty_category_weight_normalization(self):
        result = analyze(
            "Required: Python. Preferred: Docker and Kubernetes.",
            "Python, Docker",
        )
        self.assertEqual(result.required_coverage, 100.0)
        self.assertEqual(result.preferred_coverage, 50.0)
        self.assertEqual(result.overall_score, 90.0)
        only_preferred = analyze("Preferred: Docker.", "Docker")
        self.assertEqual(only_preferred.overall_score, 100.0)

    def test_configurable_weights_normalize(self):
        result = analyze(
            "Required: Python. Preferred: Docker.",
            "Python",
            required_weight=2,
            preferred_weight=1,
        )
        self.assertEqual(result.required_weight, 66.67)
        self.assertEqual(result.preferred_weight, 33.33)
        self.assertEqual(result.overall_score, 66.67)
        with self.assertRaises(ValueError):
            analyze("Required: Python.", "Python", 0, 0)

    def test_long_description_skill_requirements_are_found(self):
        description = (
            "Company overview: " + "We build products for customers. " * 20
            + "\nResponsibilities: collaborate and maintain services.\n"
            + "Required skills: Python, SQL, Git."
        )
        result = analyze(description, "Python, SQL, Git")
        self.assertEqual(
            {item.skill for item in result.requirements},
            {"Python", "SQL", "Git"},
        )
        self.assertEqual(result.required_coverage, 100.0)

    def test_unclassified_mentions_are_not_claimed_as_explicit_requirements(self):
        result = analyze("Our company uses Python. Software Engineer.", "Python")
        self.assertEqual(result.requirements[0].requirement_type, "inferred")

    def test_empty_inputs_do_not_create_scores(self):
        empty_candidate = analyze("Required: Python and SQL.", "")
        self.assertIsNone(empty_candidate.overall_score)
        self.assertIsNone(empty_candidate.required_coverage)
        empty_job = analyze("", "Python")
        self.assertEqual(empty_job.requirements, ())
        self.assertIsNone(empty_job.overall_score)

    def test_reviewed_skills_filter_resume_detections(self):
        result = analyze(
            "Required: Python and SQL.",
            "Python SQL",
            candidate_skill_names=["Python"],
        )
        self.assertEqual(result.required_coverage, 50.0)
        self.assertTrue(next(item for item in result.requirements if item.skill == "SQL").candidate_evidence == "")

    def test_local_operation_does_not_need_gemini(self):
        result = analyze("Required: Python.", "Python")
        self.assertEqual(result.overall_score, 100.0)


class ResumeAndReportTests(unittest.TestCase):
    def test_empty_and_malformed_resume_errors(self):
        with self.assertRaisesRegex(ResumeParseError, "empty"):
            extract_resume_text("resume.pdf", b"")
        with self.assertRaisesRegex(ResumeParseError, "corrupted or unreadable"):
            extract_resume_text("resume.pdf", b"not a pdf")

    def test_scanned_or_blank_pdf_error(self):
        buffer = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(buffer)
        with self.assertRaisesRegex(ResumeParseError, "No readable text"):
            extract_resume_text("resume.pdf", buffer.getvalue())

    def test_docx_text_extraction(self):
        buffer = io.BytesIO()
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Python experience</w:t></w:r></w:p></w:body></w:document>"
        )
        with ZipFile(buffer, "w") as archive:
            archive.writestr("word/document.xml", xml)
        self.assertEqual(extract_resume_text("resume.docx", buffer.getvalue()), "Python experience")

    def test_csv_report(self):
        report = csv_report(analyze("Required: Python and SQL.", "Python"))
        rows = list(csv.DictReader(io.StringIO(report.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Skill"], "Python")
        self.assertEqual(rows[0]["Status"], "Matched")
        self.assertEqual(rows[1]["Status"], "Not found")


if __name__ == "__main__":
    unittest.main()
