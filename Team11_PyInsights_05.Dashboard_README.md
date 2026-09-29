# Team 11 PyInsights — final dashboard

This Streamlit app brings together the team's **10 descriptive, 30 prescriptive, and four predictive questions**. Charts recalculate from the final cleaned master CSV. A searchable question browser presents the final notebooks' reasons and findings, including each question's source notebook and cell.

## Files and folder layout

Keep these two files together in your `cardiac_failure` project folder:

- `Team11_PyInsights_05.Dashboard.py` — dashboard app.
- `Team11_PyInsights_05.Findings.json` — question and findings snapshot from the final notebooks.

The final cleaned master must be here:

```text
cardiac_failure/
├── Team11_PyInsights_05.Dashboard.py
├── Team11_PyInsights_05.Findings.json
└── cleaned_data/
    └── patient_master.csv
```

The attached dataset may download as `patient_master(1).csv`. If so, rename your final file to `patient_master.csv` in the `cleaned_data` folder; the app expects that exact name. The other seven component cleaned CSVs and four notebooks document the team's work but are not needed to *run* the dashboard after the master CSV has been created.

## Run locally

Open Terminal. Type `cd ` (including the space), drag your `cardiac_failure` folder into Terminal, and press Return. Then run these commands on separate lines:

```bash
python3 -m pip install streamlit pandas numpy matplotlib
python3 -m streamlit run Team11_PyInsights_05.Dashboard.py
```

The install command is only needed once per Python environment. The dashboard opens in a browser, usually at `http://localhost:8501`; keep the Terminal process running while viewing it. The app uses `use_container_width=True` for compatibility with older Streamlit versions.

## What to show

| Section | Final coverage |
| --- | --- |
| Overview | Four outcome rates, readmission across time windows, and NYHA comparisons |
| Descriptive | Six chart views and findings for Q1–Q10 |
| Prescriptive | CCI, CKD/diabetes, GFR, and discharge-destination comparisons; searchable Q1–Q30 |
| Predictive | Q1 six-month readmission, Q2 28-day readmission, Q3 prolonged stay (>10 days), and Q4 six-month mortality |
| Data & methods | Source validation, denominators, and interpretation limits |

The **Explore a patient group** sidebar filters by recorded age band, gender, and NYHA class. It updates cohort metrics and exploratory charts. The notebook findings and model results stay fixed because they were evaluated on their original analysis groups. In particular, Q1 and Q2 use held-out test sets, Q3 uses five-fold cross-validation, and Q4 uses repeated five-fold cross-validation; their AUCs should not be treated as a direct head-to-head comparison. Q28 uses discharge destination, which is observed after admission and therefore is not an eligible predictor for the initial-admission models.

The team should interpret subgroup differences as associations. No model here has been externally validated for clinical use. If the team edits a final notebook, regenerate or revise the companion findings JSON so the dashboard text stays aligned with the notebook.
