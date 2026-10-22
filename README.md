# AI Police Case Analyzer & Legal Section Recommender

## Project overview
A small web application for a college mini project. An officer types the details of an
incident into a form. The app uses simple Python keyword rules to suggest possible case
categories and legal provisions for review, then shows a structured **draft case report**
that can be downloaded as a **PDF** or a **PNG image**.

> **Educational prototype.** This is not an official police system. Its output is a
> suggestion for review, not a legal decision, and it never says a person is guilty.

## Main features
- Case entry form (all fields optional, friendly error messages)
- Rule-based category matching (keywords in `legal_rules.json`)
- Matched keywords and a reason shown for every suggestion
- Small legal reference list (Bharatiya Nyaya Sanhita, 2023, India) with source and last-verified date
- 10-section report shown on screen (missing data is labelled "Not provided")
- "Insufficient information" message and no legal sections when the text is unclear
- Download PDF (A4, multi-page) and Download Image (PNG), both created in your browser

## Technologies used
- Frontend: HTML5, CSS3, basic JavaScript
- Backend: Python, Flask
- Export libraries (already included in `static/js`, no internet needed): html2canvas 1.4.1, jsPDF 2.5.1

## Required software
- Python 3.9 or newer (tick **Add Python to PATH** when installing)
- VS Code
- A modern browser (Chrome, Edge or Firefox)

## How to run it (Windows PowerShell)

1. **Extract** `ai-police-case-analyzer.zip` (right-click, Extract All).
2. **Open the folder in VS Code**: File > Open Folder > choose `ai-police-case-analyzer`.
3. Open a terminal in VS Code: Terminal > New Terminal (it should be PowerShell).
4. **Create a virtual environment** (a private box for this project's packages):
   ```powershell
   python -m venv venv
   ```
5. **Activate it** (your prompt will start with `(venv)`):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks this, run the next line once and then activate again:
   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```
6. **Install the packages** (only Flask is needed):
   ```powershell
   pip install -r requirements.txt
   ```
7. **Start the app**:
   ```powershell
   python app.py
   ```
8. Open this address in your browser: **http://127.0.0.1:5000**
9. To stop the app, press `Ctrl + C` in the terminal.

## Example test case
1. On the form, click **Fill Fictional Sample Data** (or type your own fictional details).
2. Click **Generate Case Report**.
3. Expected result: category *Theft-related* with BNS Section 303 suggested for review,
   plus missing-information notes.
4. Try a vague description such as "something happened". The report should show
   *"Insufficient information for a reliable category recommendation. Manual review is required."*
   and no legal sections.

## Downloading the report
- Click **Download PDF** on the report page. The file is saved as `case-report-<reference>.pdf`.
- Click **Download Image** to save the full report as `case-report-<reference>.png`.
- Wait a second or two after clicking; the status line under the buttons shows progress.

## Changing the rules
Open `legal_rules.json`. Each category has `keywords`, `additional_facts` and `legal_refs`.
Save the file and generate a new report (no restart needed).

## Known limitations
- Keyword matching is simple. It does not understand meaning, so it cannot tell
  "he did not steal" from "he stole". Every result needs human review.
- Only five categories and five legal sections are included. Related or more serious
  provisions (for example grievous hurt, robbery, cyber offences) are not covered.
- The PDF is made from an image of the report, so its text cannot be selected or searched.
- Fonts (Poppins/Inter) load from Google Fonts when online; otherwise Arial is used.
- No data is saved. Reports exist only on screen until downloaded.

## Legal verification disclaimer
Legal provisions are suggestions for review only. Verify the current applicable law and
complete facts before relying on this report.

The section numbers in `legal_rules.json` (BNS 2023: 115, 303, 318, 324, 351) were
cross-checked against several secondary sources on 2026-10-22, not against the
official gazette text itself. Please confirm each one in the official Bharatiya Nyaya
Sanhita, 2023 (India Code / eGazette) before presenting it as accurate.
