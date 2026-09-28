# Team 11 PyInsights dashboard

The dashboard brings together the team's **10 descriptive questions, 30 prescriptive questions, and two completed predictive questions**. The other two predictive questions are listed as pending. A searchable question browser shows each completed question, why the team asked it, the notebook write-up, and its source cell.

## Files to keep together

- `Team11_PyInsights_05_Dashboard.py` — Streamlit dashboard and interactive charts.
- `Team11_PyInsights_05_Findings.json` — snapshot of the question write-ups taken from the team's final notebooks. **Place this beside the `.py` file.**
- `cleaned_data/patient_master.csv` — the team's cleaned master dataset, inside the `cleaned_data` subfolder. This CSV is not included in the dashboard download because your team already has it.

## Run on Manasvi's Mac

1. Put the `.py` and `.json` files in `/Users/manasvi.panchagnula/Desktop/Python_Hackathon_Sep_2026/cardiac_failure`.
2. Confirm that `patient_master.csv` is in that folder's `cleaned_data` subfolder.
3. Open Terminal and run:

   ```bash
   cd /Users/manasvi.panchagnula/Desktop/Python_Hackathon_Sep_2026/cardiac_failure
   python3 -m pip install streamlit pandas numpy matplotlib
   python3 -m streamlit run Team11_PyInsights_05_Dashboard.py
   ```

A teammate can place the two dashboard files beside their own `cleaned_data` folder. If Manasvi's path is not present, the app checks the folder containing the dashboard script.

## What the sections show

| Section | Coverage |
| --- | --- |
| Overview | Cohort outcome rates and readmission by NYHA class |
| Descriptive | Six chart views for severity, heart function, comorbidity, labs, medication, stay, responsiveness, and outcomes; searchable Q1–Q10 write-ups |
| Prescriptive | CCI and CKD/diabetes comparisons; searchable Q1–Q30 write-ups organized by topic |
| Predictive | Held-out Q1 six-month and Q2 28-day readmission results plus full finding write-ups; Q3 prolonged stay and Q4 six-month mortality pending |
| Data & methods | Data source, denominator checks, and interpretation limits |

Sidebar filters update charts and cohort metrics. Notebook findings and model metrics are fixed results from the team's source files; they do not change with filters. Prescriptive Q19–Q27 contain interpretive text that should be checked against their model outputs before presenting a numerical claim. Q28 cannot compare discharge against medical order using its chosen column because that column has no such category. When the team's notebooks change, update the companion findings file to match; the dashboard does not read notebooks at runtime.
