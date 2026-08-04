# Evidence Intelligence Project

## Overview

The Evidence Intelligence Project is a biomedical evidence evaluation system designed to organize research studies, evaluate evidence quality, and estimate confidence in health claims.

The long-term goal is to create a transparent platform that explains:

- What evidence exists for a health claim
- How strong individual studies are
- How consistent the evidence is
- Why a claim receives a certain confidence level

The current prototype focuses on dietary supplement evidence.

---

# How to Run (VS Code)

## One-time setup (already done if you can see a `.venv` folder)

```bash
# From the project root:
python3 -m venv .venv                # creates the project's own Python env
.venv/bin/pip install -r requirements.txt
```

## Run the web app

1. Open this folder in VS Code. It will automatically pick the `.venv` Python
   (if not, click the interpreter in the bottom-right corner and choose the
   one named `.venv`).
2. Open `script/app.py` and press the ▶ **Run** button (or run
   `.venv/bin/python script/app.py` in a terminal).
3. Open http://localhost:5001 in your browser and search a claim ID, e.g. `C0001`.

## Run the pipeline / CLI

```bash
.venv/bin/python script/prototype.py        # full claim evaluation pipeline
.venv/bin/python script/user_interface.py    # interactive menu (search a claim)
.venv/bin/python script/claim_test.py        # quick smoke tests
```

> **Why a venv?** Your Mac also ships a bare Python (`/usr/bin/python3`, v3.9.6)
> that has **none** of this project's libraries. If VS Code ever uses it, every
> script fails with `ModuleNotFoundError`. The `.venv` + `.vscode/settings.json`
> in this repo make VS Code always use the correct Python.

---

# System Architecture

Current data flow:

```

Literature Database
|
| Google Sheets formulas
↓
Machine Database
|
↓
Python Evidence Engine
|
↓
Claim Evaluation Engine
|
↓
Claim Database

```

---

# Database Structure

## Literature Database

Purpose:

Stores collected biomedical research papers.

Role:

- Human research collection
- Literature organization
- Initial study information

---

## Machine Database

Purpose:

Structured evidence database used by Python.

Current columns:

- Study ID
- Claim ID
- Study Type Score
- Randomized
- Blinded
- Placebo controlled
- Risk of bias
- Sample size
- Publication year
- Outcome (+/0/-)
- Effect size
- p-value
- Confidence interval
- Statistical significance

Role:

Provides study-level evidence for evaluation.

---

## Claim Database

Purpose:

Stores health claims being evaluated.

Example:

```

Claim ID: C0001

Claim:
Melatonin improves sleep quality

```

Role:

Connects scientific evidence to interpretable conclusions.

Future outputs:

- Number of supporting studies
- Average study quality
- Claim confidence score
- Evidence classification

---

# Python Components

## data_loader.py

Purpose:

Loads the Machine Database from Google Sheets.

Input:

Machine Database tab

Output:

Pandas DataFrame containing study-level evidence.

---

## claim_loader.py

Purpose:

Loads the Claim Database from Google Sheets.

Input:

Claim Database tab

Output:

Pandas DataFrame containing claim information.

---

## claim_linker.py

Purpose:

Creates the relationship between claims and studies.

Example:

```

Claim C0001

```
    |
    |
    ↓
```

S0001
S0002
S0003
S0004

```

Allows the system to find all evidence associated with a claim.

---

## quality_score.py

Purpose:

Evaluates individual study quality.

Current factors:

- Study design
- Randomization
- Blinding
- Placebo control
- Risk of bias
- Sample size

Output:

Individual study quality score.

Example:

```

S0001 → 43.23
S0002 → 20.00
S0003 → 53.23

```

---

## grouping_claim.py

Purpose:

Groups studies by Claim ID.

Example:

```

C0001

S0001
S0002
S0003
S0004

```

Used for claim-level evaluation.

---

## claim_score.py

Purpose:

Combines study-level evidence into a claim confidence score.

Output example:

```

Claim ID: C0001

Confidence Score: 33.29

Confidence Level:
Low confidence

```

---

## prototype.py

Main execution script.

Current workflow:

1. Load Machine Database
2. Validate database
3. Calculate study quality scores
4. Group studies by claim
5. Calculate claim confidence

---

# Current Development Status

## Completed

- Google Sheets → Python data loading
- Machine Database connection
- Database validation system
- Individual study quality scoring prototype
- Claim grouping system
- Claim Database connection

---

## Currently Building

- Claim evaluation engine
- Automated claim scoring pipeline
- Writing results back to Google Sheets

---

## Future Development

- Automated literature ingestion
- Human review workflow
- More advanced evidence weighting
- Machine learning assistance
- Public evidence intelligence platform

---

# Design Principles

## 1. Transparency

Every confidence score should be explainable.

Users should understand why evidence is considered strong or weak.

---

## 2. Separation of Data and Logic

Data storage:

```

Google Sheets

```

Evaluation:

```

Python Engine

```

Results:

```

Claim Database

```

---

## 3. Scalability

The system should work for:

```

1 claim
↓
10 studies

and eventually

Thousands of claims
↓
Millions of studies

```

---

## 4. Human Oversight

The system is designed to assist evidence evaluation, not replace scientific judgment.

---

# Current Prototype Goal

Build a working evidence intelligence pipeline:

```

Study
↓
Study Quality Score
↓
Claim Relationship
↓
Claim Confidence Score
↓
Evidence Interpretation

