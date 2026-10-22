"""AI Police Case Analyzer & Legal Section Recommender.

An educational prototype. It uses simple keyword rules (see legal_rules.json)
to organise case details into a draft report. It is NOT an official police
system and its output is NOT a legal decision.
"""

import json
import re
from datetime import datetime, date
from pathlib import Path

from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent
RULES_FILE = BASE_DIR / "legal_rules.json"

app = Flask(__name__)

NOT_PROVIDED = "Not provided"
INSUFFICIENT_MESSAGE = (
    "Insufficient information for a reliable category recommendation. "
    "Manual review is required."
)
NO_MATCH_MESSAGE = (
    "No rule matched the description, so no category is suggested. "
    "Manual review is required."
)

# (form field name, label shown to the user, max length)
FIELDS = [
    ("case_ref", "Case reference number", 50),
    ("incident_date", "Incident date", 10),
    ("incident_time", "Incident time", 5),
    ("location", "Incident location", 200),
    ("station", "Police station name", 120),
    ("officer", "Reporting officer designation", 120),
    ("incident_type", "Type of incident", 60),
    ("description", "Incident description", 3000),
    ("circumstances", "Circumstances surrounding the incident", 3000),
    ("complainant", "Complainant details", 1000),
    ("suspect", "Suspect details", 1000),
    ("witness", "Witness information", 1000),
    ("evidence", "Evidence description", 2000),
    ("observations", "Additional observations", 2000),
]
LABELS = {name: label for name, label, _ in FIELDS}
MAX_LEN = {name: size for name, _, size in FIELDS}


def load_rules():
    """Read the rules file each time so edits apply without restarting."""
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def clean(value):
    """Trim spaces and collapse very long runs of blank lines."""
    value = (value or "").replace("\r\n", "\n").strip()
    return re.sub(r"\n{3,}", "\n\n", value)


def read_form(source):
    return {name: clean(source.get(name)) for name, _, _ in FIELDS}


def validate(form):
    """Return a list of friendly error messages (empty list = valid)."""
    errors = []

    if not any(form.values()):
        errors.append("The form is empty. Please fill in at least one field "
                      "(the incident description is the most useful one).")

    for name, max_len in MAX_LEN.items():
        if len(form[name]) > max_len:
            errors.append(f"'{LABELS[name]}' is too long (maximum {max_len} characters).")

    if form["case_ref"] and not re.fullmatch(r"[A-Za-z0-9/\-_. ]+", form["case_ref"]):
        errors.append("Case reference number may contain only letters, numbers, "
                      "spaces and the characters / - _ .")

    if form["incident_date"]:
        try:
            d = datetime.strptime(form["incident_date"], "%Y-%m-%d").date()
            if d > date.today():
                errors.append("Incident date cannot be in the future.")
        except ValueError:
            errors.append("Incident date is not a valid date.")

    if form["incident_time"]:
        try:
            datetime.strptime(form["incident_time"], "%H:%M")
        except ValueError:
            errors.append("Incident time is not valid (use HH:MM).")

    return errors


def keyword_pattern(keyword):
    """Match a keyword at a word start, allowing simple endings (s, ed, ing...)."""
    return re.compile(r"\b" + re.escape(keyword) + r"(?:s|es|ed|en|ing|ly)?\b")


def find_keywords(text, keywords):
    found = []
    for kw in keywords:
        if keyword_pattern(kw.lower()).search(text):
            found.append(kw)
    return found


def strength_label(count):
    if count >= 3:
        return "Higher indicative match"
    if count == 2:
        return "Moderate indicative match"
    return "Low indicative match"


def analyze(form, rules):
    """Rule-based analysis. Returns a dict describing the outcome."""
    text = " ".join([form["description"], form["circumstances"], form["incident_type"]])
    text = re.sub(r"\s+", " ", text.lower()).strip()
    word_count = len(re.findall(r"[a-z0-9']+", form["description"].lower() + " " + form["circumstances"].lower()))
    min_words = rules.get("settings", {}).get("min_words_for_analysis", 5)

    if word_count < min_words:
        return {"status": "insufficient", "message": INSUFFICIENT_MESSAGE,
                "candidates": [], "text": text}

    candidates = []
    for cat in rules["categories"]:
        matched = find_keywords(text, cat["keywords"])
        if not matched:
            continue
        candidates.append({
            "id": cat["id"],
            "name": cat["name"],
            "matched": matched,
            "strength": strength_label(len(matched)),
            "score": len(matched),
            "reason": ("Suggested because the entered text contains: "
                       + ", ".join(f'"{m}"' for m in matched)
                       + ". Keyword matches are only a hint and do not prove "
                         "that an offence occurred."),
            "additional_facts": cat.get("additional_facts", []),
            "legal_refs": cat.get("legal_refs", []),
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)

    if not candidates:
        return {"status": "no_match", "message": NO_MATCH_MESSAGE,
                "candidates": [], "text": text}

    return {"status": "matched", "message": "", "candidates": candidates, "text": text}


def build_summary(form):
    """Plain-language summary made ONLY from submitted fields."""
    parts = []
    if form["case_ref"]:
        parts.append(f"Case reference: {form['case_ref']}.")
    when = " ".join(x for x in [form["incident_date"], form["incident_time"]] if x)
    if when:
        parts.append(f"The incident is recorded as occurring on/at: {when}.")
    if form["location"]:
        parts.append(f"Location entered: {form['location']}.")
    if form["incident_type"]:
        parts.append(f"The officer selected the incident type: {form['incident_type']}.")
    if form["description"]:
        parts.append("The officer's description is reproduced under Incident Details below.")
    else:
        parts.append("No incident description was provided.")
    return " ".join(parts)


def missing_information(form, analysis):
    """Blank form fields plus category-specific facts to clarify."""
    items = []
    for name in ["case_ref", "incident_date", "incident_time", "location", "station",
                 "officer", "description", "circumstances", "complainant",
                 "suspect", "witness", "evidence"]:
        if not form[name]:
            items.append(f"{LABELS[name]}: Requires clarification (not provided).")
    seen = set()
    for cand in analysis["candidates"]:
        for fact in cand["additional_facts"]:
            if fact not in seen:
                seen.add(fact)
                items.append(f"{cand['name']}: {fact}")
    return items


def next_steps(form, analysis, rules):
    """General steps for the officer to CONSIDER. No coercive actions are suggested."""
    steps = ["Review the incident description for accuracy and completeness."]
    text = analysis["text"]

    urgent = rules.get("urgent_keywords", {})
    if find_keywords(text, urgent.get("medical", [])):
        steps.append("The text mentions possible injury. Consider referring any urgent "
                     "medical concern to the appropriate medical or supervisory personnel.")
    if find_keywords(text, urgent.get("safety", [])):
        steps.append("The text mentions a possible safety risk. Consider whether urgent "
                     "safety measures are needed and inform the appropriate supervisor.")

    if any(not form[n] for n in ["case_ref", "incident_date", "location", "description",
                                  "complainant", "witness", "evidence"]):
        steps.append("Identify and record the missing information listed in the "
                     "'Missing Information' section.")

    if form["evidence"]:
        steps.append("Review the available evidence and preserve it in accordance with "
                     "applicable procedures.")
    else:
        steps.append("Determine whether any evidence exists or can be identified.")

    if form["witness"]:
        steps.append("Consider whether the listed witnesses need to be contacted.")
    else:
        steps.append("Consider whether there are witnesses who should be identified.")

    if analysis["candidates"]:
        steps.append("Verify the candidate legal provisions against the current official "
                     "text and the complete facts before relying on them.")
    else:
        steps.append("Review the case manually to decide on a suitable category.")

    steps.append("Follow the applicable police procedures and obtain supervisor guidance "
                 "where needed. This report does not replace human judgement.")
    return steps


@app.route("/", methods=["GET", "POST"])
def index():
    """View 1: the case entry form. POST is used only to refill the form
    when the user clicks 'Back to Case Form' on the report page."""
    values = read_form(request.form) if request.method == "POST" else {}
    return render_template("index.html", values=values, errors=[], today=date.today().isoformat())


@app.route("/report", methods=["POST"])
def report():
    """View 2: validate the form, analyse it and show the report."""
    form = read_form(request.form)
    errors = validate(form)
    if errors:
        return render_template("index.html", values=form, errors=errors,
                               today=date.today().isoformat()), 400

    rules = load_rules()
    analysis = analyze(form, rules)

    data = {
        "form": form,
        "analysis": analysis,
        "summary": build_summary(form),
        "missing": missing_information(form, analysis),
        "steps": next_steps(form, analysis, rules),
        "generated_on": datetime.now().strftime("%d %b %Y, %H:%M"),
        "not_provided": NOT_PROVIDED,
    }
    return render_template("report.html", **data)


if __name__ == "__main__":
    app.run(debug=True)
