# AI Job Description Analyzer

A local Streamlit application that compares job requirements with candidate-provided evidence. Matching is deterministic and dictionary-based; results are guidance, not an ATS score, hiring probability, or assessment of a person's ability.

## Features

- Extracts canonical skills from a complete job description, including text near the end.
- Separates explicitly required, preferred, and unclassified/inferred mentions.
- Supports manual skills, pasted resume text, selectable-text PDF, and DOCX resumes.
- Displays extracted text and lets users review, remove, or add resume skills before matching.
- Shows candidate evidence for matches and explains that missing evidence does not prove lack of ability.
- Reports required/preferred coverage, keyword coverage, experience/qualification text alignment, local recommendations, and interview prompts.
- Exports a CSV report. Resume parsing and analysis happen locally.

## Requirements and installation

- Python 3.11 or newer
- Windows, macOS, or Linux

On Windows, open a terminal in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Test

The automated tests use Python's standard-library `unittest` runner and synthetic resume files:

```powershell
python -m unittest discover -s tests -v
```

## Inputs and privacy

- Candidate skills can be entered manually; resume text can also be pasted.
- PDF and DOCX uploads are limited to 10 MB. PDF parsing requires selectable text; encrypted, corrupt, empty, and unreadable files produce an error.
- DOCX text is extracted from the document XML using the Python standard library; no `python-docx` installation is needed.
- OCR is not implemented. Scanned PDFs need OCR processing before upload.
- Parsing is local; the project does not send uploaded resume content to an external service.

## Matching and score

Canonical skills, categories, aliases, and learning resources live in `skill_dictionary.py`; matching and scoring live in `analyzer.py`.

Coverage for each requirement class is:

`coverage = matched applicable requirement weight / total applicable requirement weight * 100`

Requirements in the current dictionary have equal importance. The default weights are 80% required and 20% preferred. The interface lets you adjust these weights; the analyzer normalizes any non-negative pair to 100%. The overall score is the weighted average of the available required and preferred coverage, with weights renormalized when a category has no requirements. Inferred mentions are shown separately and are not treated as confirmed requirements or included in the score. No score is shown without candidate evidence or identifiable job skills.

Text similarity and general keyword coverage are supplementary text signals, not skill claims.

## Extend the skill dictionary

Add a `Skill` entry in `skill_dictionary.py` with its canonical name, category, aliases, learning-resource URL, and practice exercise. Phrase matching uses token boundaries, normalizes case/punctuation, and prioritizes longer phrases to avoid common substring errors such as confusing C and C++.

## Gemini and reports

The inspected project did not contain Gemini integration. This version remains entirely local and does not require or attempt Gemini calls or credentials.

CSV reports are supported using Python's standard `csv` module. PDF report generation is not included; no additional PDF-generation dependency is installed.

## Limitations

- Requirement classification uses explicit labels and phrase cues. Ambiguous mentions are marked inferred; review them before relying on the result.
- The hand-maintained dictionary cannot recognize every technology, qualification, or synonym.
- Experience and qualification alignment checks for relevant text; they do not validate years, degrees, or eligibility.
- Learning and interview suggestions are generic prompts based on listed skills; they do not claim completed training, projects, or experience.
- Do not upload personal information unless you are authorized to process it.
