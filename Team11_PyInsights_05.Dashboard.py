"""Team 11 PyInsights heart-failure dashboard.

Run with: streamlit run Team11_PyInsights_05.Dashboard.py
Charts recalculate from the team's cleaned Team11_PyInsights_cleaned_data.csv. The companion
findings JSON preserves the question write-ups from the team's final notebooks.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="PyInsights | Heart failure", page_icon="♥", layout="wide")

# Put this script and its findings JSON in the project folder, with the master
# CSV inside a cleaned_data subfolder. This works on each teammate's computer.
DATA_PATH = Path(__file__).resolve().parent
CLEANED_PATH = DATA_PATH / "cleaned_data"
MASTER_PATH = CLEANED_PATH / "Team11_PyInsights_cleaned_data.csv"
FINDINGS_PATH = Path(__file__).resolve().with_name("Team11_PyInsights_05.Findings.json")

COLORS = {"navy": "#183153", "blue": "#3975B7", "teal": "#168A83",
          "amber": "#D9923B", "red": "#B65359", "light": "#E8EFF5"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False})

REQUIRED_COLUMNS = [
    "inpatient_number", "age_category", "gender",
    "nyha_cardiac_function_classification", "killip_grade",
    "cci_score", "diabetes", "moderate_to_severe_chronic_kidney_disease",
    "re_admission_within_28_days", "re_admission_within_3_months",
    "re_admission_within_6_months", "death_within_6_months",
]


@st.cache_data(show_spinner=False)
def read_master(path: str, modified_at: float) -> pd.DataFrame:
    """Read one cleaned master; the timestamp invalidates cache after an update."""
    data = pd.read_csv(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing:
        raise ValueError(f"Master CSV is missing expected columns: {missing}")
    if data["inpatient_number"].isna().any() or data["inpatient_number"].duplicated().any():
        raise ValueError("The master must have one unique, nonmissing patient ID per row.")
    return data


def outcome_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Count known outcomes, not missing outcomes as negative events."""
    items = [
        ("Readmission within 28 days", "re_admission_within_28_days"),
        ("Readmission within 3 months", "re_admission_within_3_months"),
        ("Readmission within 6 months", "re_admission_within_6_months"),
        ("Death within 6 months", "death_within_6_months"),
    ]
    rows = []
    for label, column in items:
        known = pd.to_numeric(data[column], errors="coerce")
        known = known[known.isin([0, 1])]
        rows.append({"Outcome": label, "Patients": len(known),
                     "Events": int(known.sum()),
                     "Rate (%)": 100 * known.mean() if len(known) else np.nan})
    return pd.DataFrame(rows)


def grouped_rates(data: pd.DataFrame, group: str, outcome: str,
                  order: list | None = None) -> pd.DataFrame:
    """Give each displayed percentage its patient and event denominator."""
    analysis = data[[group, outcome]].copy()
    analysis[outcome] = pd.to_numeric(analysis[outcome], errors="coerce")
    analysis = analysis.loc[analysis[group].notna() & analysis[outcome].isin([0, 1])]
    report = (analysis.groupby(group, observed=True)[outcome]
              .agg(Patients="size", Events="sum").reset_index())
    report["Rate (%)"] = 100 * report["Events"] / report["Patients"]
    if order:
        report[group] = pd.Categorical(report[group], categories=order, ordered=True)
        report = report.sort_values(group)
    return report.reset_index(drop=True)


def plot_rates(report: pd.DataFrame, label_col: str, title: str,
               color: str = COLORS["blue"]):
    """A horizontal chart with the actual count beside each percentage."""
    fig, ax = plt.subplots(figsize=(8, max(3.1, len(report) * 0.62 + 1.2)))
    positions = np.arange(len(report))
    rates = report["Rate (%)"].to_numpy(dtype=float)
    ax.barh(positions, rates, color=color, height=0.68)
    ax.set_yticks(positions, report[label_col].astype(str).tolist())
    ax.invert_yaxis()
    ax.set_xlabel("Observed outcome rate (%)")
    ax.set_title(title, loc="left", fontsize=13, weight="bold")
    ax.set_xlim(0, max(55, np.nanmax(rates) * 1.25) if len(rates) else 55)
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    for position, (_, row) in enumerate(report.iterrows()):
        ax.text(row["Rate (%)"] + 0.65, position,
                f"{row['Rate (%)']:.1f}%  ({int(row['Events'])}/{int(row['Patients'])})",
                va="center", fontsize=9)
    fig.tight_layout()
    return fig


def plot_counts(data: pd.Series, title: str, top: int = 10):
    counts = data.dropna().astype(str).value_counts().head(top).sort_values()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(counts.index, counts.values, color=COLORS["blue"])
    ax.set_title(title, loc="left", weight="bold")
    ax.set_xlabel("Patients")
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    return fig


def plot_distribution(data: pd.Series, title: str, xlabel: str, bins: int = 25):
    values = pd.to_numeric(data, errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    if not values.empty:
        ax.hist(values, bins=bins, color=COLORS["teal"], edgecolor="white")
        ax.axvline(values.median(), color=COLORS["red"], ls="--",
                   label=f"Median {values.median():.1f}")
        ax.legend()
    ax.set_title(title, loc="left", weight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Patients")
    fig.tight_layout()
    return fig


def show_figure(fig):
    st.pyplot(fig)
    plt.close(fig)


@st.cache_data(show_spinner=False)
def read_findings(path: str, modified_at: float):
    with open(path, encoding="utf-8") as handle:
        entries = json.load(handle)["questions"]
    counts = {phase: sum(entry["phase"] == phase for entry in entries)
              for phase in ("Descriptive", "Prescriptive", "Predictive")}
    if counts != {"Descriptive": 10, "Prescriptive": 30, "Predictive": 4}:
        raise ValueError(f"Question catalogue is incomplete: {counts}")
    return entries


def question_browser(entries, phase: str, key: str):
    """Search the complete notebook findings; do not recompute notebook models."""
    chosen = [entry for entry in entries if entry["phase"] == phase]
    if phase == "Prescriptive":
        families = list(dict.fromkeys(entry["section"] for entry in chosen))
        family = st.selectbox("Topic", ["All topics", *families], key=f"{key}_family")
        if family != "All topics":
            chosen = [entry for entry in chosen if entry["section"] == family]
    query = st.text_input("Find a question or topic", key=f"{key}_search",
                          placeholder="For example: kidney, mortality, medication")
    if query.strip():
        chosen = [entry for entry in chosen if query.lower() in
                  (entry["question"] + " " + entry["why"] + " " + entry["finding"]).lower()]
    if not chosen:
        st.info("No questions match that search. Clear the search to see all questions.")
        return
    labels = [f"Q{entry['number']} · {entry['question']}" for entry in chosen]
    selected = st.selectbox(f"Browse {phase.lower()} questions ({len(chosen)} shown)",
                            range(len(chosen)), format_func=lambda index: labels[index],
                            key=f"{key}_question")
    entry = chosen[selected]
    st.markdown(f"#### Q{entry['number']}. {entry['question']}")
    st.markdown("**Why we asked**")
    st.write(entry["why"] or "See the team notebook for the original rationale.")
    st.markdown("**What the notebook reports**")
    if entry["status"] != "Reported finding":
        st.caption(f"Status: {entry['status']}")
    st.markdown(entry["finding"])
    st.caption(f"Source: {entry['source_notebook']} · notebook cell(s) "
               + ", ".join(map(str, entry["source_cells"])))


def cci_groups(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    score = pd.to_numeric(result["cci_score"], errors="coerce")
    result["CCI group"] = pd.cut(score, [-0.1, 1, 2, np.inf],
                                 labels=["CCI 0–1", "CCI 2", "CCI 3+"])
    return result


def comorbidity_profiles(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    ckd = pd.to_numeric(result["moderate_to_severe_chronic_kidney_disease"], errors="coerce")
    diabetes = pd.to_numeric(result["diabetes"], errors="coerce")
    names = {(0, 0): "Neither", (0, 1): "Diabetes only",
             (1, 0): "CKD only", (1, 1): "Both"}
    result["CKD + diabetes"] = [names.get((a, b), np.nan) for a, b in zip(ckd, diabetes)]
    return result


if not MASTER_PATH.is_file():
    st.error(f"Could not find Team11_PyInsights_cleaned_data.csv at {MASTER_PATH}. Place the app beside a cleaned_data folder, or edit DATA_PATH near the top of the file.")
    st.stop()

try:
    df = read_master(str(MASTER_PATH), MASTER_PATH.stat().st_mtime)
except (ValueError, OSError) as exc:
    st.error(f"Could not load the cleaned master: {exc}")
    st.stop()

if not FINDINGS_PATH.is_file():
    st.error(f"Missing companion file {FINDINGS_PATH.name}. Place it beside this dashboard script.")
    st.stop()
try:
    findings = read_findings(str(FINDINGS_PATH), FINDINGS_PATH.stat().st_mtime)
except (ValueError, OSError, json.JSONDecodeError) as exc:
    st.error(f"Could not load the team question catalogue: {exc}")
    st.stop()

st.title("Heart failure patient insights")
st.caption("Team 11 PyInsights · 10 descriptive, 30 prescriptive and 4 completed predictive questions")
st.markdown("**Explore the patient profile, subgroup comparisons, and admission-time prediction questions.**")

# The cohort and group charts respond to filters. Notebook model metrics are
# snapshots of their original held-out or cross-validated evaluations.
st.sidebar.header("Explore a patient group")
ages = sorted(df["age_category"].dropna().astype(str).unique().tolist())
genders = sorted(df["gender"].dropna().astype(str).unique().tolist())
nyha_values = sorted(df["nyha_cardiac_function_classification"].dropna().unique().tolist())
selected_ages = st.sidebar.multiselect("Recorded age bands", ages)
selected_genders = st.sidebar.multiselect("Gender", genders)
selected_nyha = st.sidebar.multiselect("NYHA class", nyha_values)

filtered = df.copy()
if selected_ages:
    filtered = filtered[filtered["age_category"].astype(str).isin(selected_ages)]
if selected_genders:
    filtered = filtered[filtered["gender"].astype(str).isin(selected_genders)]
if selected_nyha:
    filtered = filtered[filtered["nyha_cardiac_function_classification"].isin(selected_nyha)]

st.sidebar.caption(f"Selected: {len(filtered):,} of {len(df):,} patients. Empty selections mean all patients.")
if filtered.empty:
    st.warning("No patients match these filters. Change a sidebar selection.")
    st.stop()

# Match the team's prescriptive Q11–Q18 denominator for subgroup readmission
# charts. The full-cohort outcome cards keep the descriptive notebook's 2,008
# patient denominator; only subgroup comparisons omit contradictory event rows.
if "event_time_contradiction_flag" in filtered.columns:
    contradiction = filtered["event_time_contradiction_flag"].astype(str).str.lower().isin(["true", "1"])
    group_data = filtered.loc[~contradiction].copy()
else:
    group_data = filtered.copy()

full = outcome_summary(df).set_index("Outcome")
active = outcome_summary(filtered).set_index("Outcome")
metric_columns = st.columns(4)
for location, name, label in zip(metric_columns,
                                 ["Readmission within 28 days", "Readmission within 6 months",
                                  "Death within 6 months", "Readmission within 3 months"],
                                 ["28-day readmission", "6-month readmission",
                                  "6-month mortality", "3-month readmission"]):
    record = active.loc[name]
    location.metric(label, f"{record['Rate (%)']:.1f}%")
    location.caption(f"{int(record['Events'])} of {int(record['Patients'])} selected patients")

overview, descriptive, prescriptive, prediction, methods = st.tabs([
    "Overview", "Descriptive · Q1–Q10", "Prescriptive · Q1–Q30",
    "Predictive · Q1–Q4", "Data & methods"
])

with overview:
    st.subheader("How often do patients return?")
    st.caption("Charts use the sidebar selection. Group comparisons omit records flagged for contradictory event timing, as in the team's prescriptive analysis. Event/patient counts appear beside each rate.")
    left, right = st.columns(2)
    with left:
        time_report = active.loc[["Readmission within 28 days",
                                  "Readmission within 3 months",
                                  "Readmission within 6 months"]].reset_index()
        fig = plot_rates(time_report, "Outcome", "Readmission by follow-up window", COLORS["teal"])
        show_figure(fig)
    with right:
        severity = grouped_rates(group_data, "nyha_cardiac_function_classification",
                                 "re_admission_within_6_months")
        severity["NYHA class"] = severity["nyha_cardiac_function_classification"].map(
            lambda value: f"Class {int(value)}")
        fig = plot_rates(severity, "NYHA class", "Six-month readmission by NYHA class")
        show_figure(fig)
    baseline = full.loc["Readmission within 6 months"]
    st.info(f"Full-cohort anchor: {int(baseline['Events']):,} of {int(baseline['Patients']):,} "
            f"patients ({baseline['Rate (%)']:.1f}%) had recorded six-month readmission. "
            "Filtered percentages describe the selected group only.")

with descriptive:
    st.subheader("What does the patient cohort look like?")
    st.caption("Charts recalculate from the selected patients. The question browser below contains the team's full-cohort notebook write-ups, which do not change with sidebar filters.")
    chart_topic = st.selectbox("Choose a descriptive view", [
        "Admission severity", "Heart function and comorbidities", "Clinical labs",
        "Medication use", "Hospital stay and responsiveness", "Outcome windows"
    ], key="descriptive_view")
    left, right = st.columns(2)
    if chart_topic == "Admission severity":
        with left:
            show_figure(plot_counts(filtered["nyha_cardiac_function_classification"], "NYHA class"))
        with right:
            show_figure(plot_counts(filtered["killip_grade"], "Killip grade"))
    elif chart_topic == "Heart function and comorbidities":
        with left:
            show_figure(plot_distribution(filtered["lvef"], "LVEF when measured", "LVEF (%)"))
            st.caption(f"LVEF measured in {filtered['lvef'].notna().sum():,} of {len(filtered):,} selected patients.")
        with right:
            show_figure(plot_distribution(filtered["cci_score"], "Comorbidity score", "CCI score", 12))
    elif chart_topic == "Clinical labs":
        with left:
            show_figure(plot_distribution(filtered["brain_natriuretic_peptide"], "BNP when measured", "BNP (pg/mL)"))
        with right:
            show_figure(plot_distribution(filtered["glomerular_filtration_rate"], "Kidney function when measured", "GFR"))
    elif chart_topic == "Medication use":
        with left:
            show_figure(plot_distribution(filtered["total_drug_count"], "Number of recorded drugs", "Drug count", 20))
        with right:
            drugs = filtered.filter(regex=r"^drug_").apply(pd.to_numeric, errors="coerce")
            top_drugs = drugs.eq(1).sum().nlargest(10).sort_values()
            fig, ax = plt.subplots(figsize=(7, 3.5))
            ax.barh(top_drugs.index.str.replace("drug_", "", regex=False), top_drugs.values, color=COLORS["amber"])
            ax.set_title("Most frequently recorded drugs", loc="left", weight="bold")
            ax.set_xlabel("Patients")
            fig.tight_layout()
            show_figure(fig)
    elif chart_topic == "Hospital stay and responsiveness":
        with left:
            show_figure(plot_distribution(filtered["dischargeday"], "Length of stay", "Days"))
        with right:
            show_figure(plot_counts(filtered["consciousness"], "Recorded consciousness"))
            st.caption(f"GCS median: {pd.to_numeric(filtered['gcs'], errors='coerce').median():.0f} in the selected group.")
    else:
        with left:
            show_figure(plot_rates(active.reset_index(), "Outcome", "Readmission and death windows"))
        with right:
            st.dataframe(active.reset_index().round(1), use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### All descriptive questions and findings")
    question_browser(findings, "Descriptive", "descriptive")

with prescriptive:
    st.subheader("Which patient groups have different observed outcomes?")
    st.caption("Charts recalculate from the sidebar selection. The question browser contains the final notebook's full-cohort analyses; those findings do not change with filters. These are associations, not tested interventions.")
    prescriptive_view = st.selectbox("Choose a patient-group comparison", [
        "Comorbidity score and diagnoses", "Kidney function and discharge destination"
    ], key="prescriptive_view")
    left, right = st.columns(2)
    if prescriptive_view == "Comorbidity score and diagnoses":
        with left:
            cci = grouped_rates(cci_groups(group_data), "CCI group",
                                "re_admission_within_6_months",
                                ["CCI 0–1", "CCI 2", "CCI 3+"])
            show_figure(plot_rates(cci, "CCI group", "Six-month readmission by comorbidity score", COLORS["amber"]))
        with right:
            profiles = grouped_rates(comorbidity_profiles(group_data), "CKD + diabetes",
                                     "re_admission_within_6_months",
                                     ["Neither", "Diabetes only", "CKD only", "Both"])
            show_figure(plot_rates(profiles, "CKD + diabetes", "Six-month readmission by recorded diagnoses", COLORS["blue"]))
    else:
        # Admission GFR and discharge destination have different measurement
        # times. Died during admission is not a post-discharge risk group.
        renal_data = group_data.copy()
        gfr = pd.to_numeric(renal_data["glomerular_filtration_rate"], errors="coerce")
        renal_data["GFR group"] = np.where(gfr < 60, "GFR <60", "GFR ≥60")
        renal_data.loc[gfr.isna(), "GFR group"] = np.nan
        renal = grouped_rates(renal_data, "GFR group", "re_admission_within_6_months",
                              ["GFR ≥60", "GFR <60"])
        discharge_data = filtered.loc[filtered["destination_discharge"] != "Died"]
        discharge = grouped_rates(discharge_data, "destination_discharge",
                                  "re_admission_within_6_months",
                                  ["Unknown", "Home", "Healthcare Facility"])
        with left:
            show_figure(plot_rates(renal, "GFR group", "Six-month readmission by kidney function", COLORS["teal"]))
        with right:
            show_figure(plot_rates(discharge, "destination_discharge", "Six-month readmission by discharge destination", COLORS["amber"]))
        st.caption("GFR is a measured kidney-function estimate. Discharge destination is known later, so its chart is descriptive and cannot be used as an initial-admission model input. The 14 patients recorded as 'Died' at discharge are excluded from this comparison.")
    st.markdown("**How to read the charts:** each label gives a rate and its event/patient count. Small filtered groups can have unstable percentages.")
    with st.expander("View underlying group counts"):
        if prescriptive_view == "Comorbidity score and diagnoses":
            st.dataframe(cci.round(1), use_container_width=True, hide_index=True)
            st.dataframe(profiles.round(1), use_container_width=True, hide_index=True)
        else:
            st.dataframe(renal.round(1), use_container_width=True, hide_index=True)
            st.dataframe(discharge.round(1), use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("### All prescriptive questions and findings")
    st.caption("The browser follows the final prescriptive notebook, including revised measured findings for Q19–Q28. Q29 and Q30 are exploratory bridges to predictive analysis.")
    question_browser(findings, "Prescriptive", "prescriptive")

with prediction:
    st.subheader("Four admission-time prediction questions")
    st.caption("These are measured results from the final predictive notebook. Sidebar filters do not refit models or change the original evaluation results.")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Q1 · Six-month readmission")
        st.write("Can initial-admission information identify patients at higher risk of readmission within six months?")
        st.metric("Held-out ROC AUC", "0.540")
        st.write("Average precision **0.429**; 193 readmissions among **502** test patients. At the preselected 0.50 threshold, recall was **14.0%** (27 of 193 found).")
        st.caption("Interpretation: a weak ranking signal; probability error did not improve over the constant-risk baseline. Exploratory, not ready for patient-level decisions.")
    with p2:
        st.markdown("#### Q2 · 28-day readmission")
        st.write("Can initial-admission information identify patients at higher risk of readmission within 28 days?")
        st.metric("Held-out ROC AUC", "0.619")
        st.write("Average precision **0.163**; 34 readmissions among **497** test patients. At a training-selected 0.319 threshold, recall was **76.5%** (26 of 34 found).")
        st.caption("Interpretation: many patients must be flagged to find most early readmissions; 64.0% of the test set was flagged. Exploratory and not externally validated.")
    p3, p4 = st.columns(2)
    with p3:
        st.markdown("#### Q3 · Prolonged hospital stay")
        st.write("Can initial-admission information identify stays lasting more than 10 days?")
        st.metric("5-fold cross-validated ROC AUC", "0.663")
        st.write("**498 of 2,008** patients stayed more than 10 days. Average precision was **0.388**; the severity-only AUC was **0.545**. At a 0.50 threshold, recall was **57.2%** and precision **36.4%**.")
        st.caption("Interpretation: modest group-level signal, below the team's prespecified 0.70 discrimination target. Not externally validated.")
    with p4:
        st.markdown("#### Q4 · Six-month mortality")
        st.write("Can initial-admission information identify patients at higher risk of death within six months?")
        st.metric("Repeated cross-validated ROC AUC", "0.795")
        st.write("**57 of 2,008** patients died within six months. Mean PR AUC was **0.186**. The top-risk 20% contained **36 of 57 deaths (63.2%)**, but precision was **9.0%**.")
        st.caption("Interpretation: stronger discrimination in internal validation; estimates remain uncertain with only 57 deaths and no external validation.")
    st.info("The four outcomes and validation designs differ: Q1–Q2 use held-out test sets, Q3 uses 5-fold cross-validation, and Q4 uses 5-fold × 10 repeated cross-validation. AUCs are context, not a direct competition between models.")
    st.divider()
    st.markdown("### All predictive questions: full notebook findings")
    question_browser(findings, "Predictive", "predictive")

with methods:
    st.subheader("What this dashboard uses")
    st.write(f"**Source:** `cleaned_data/Team11_PyInsights_cleaned_data.csv` · **Patients:** {len(df):,} · **Columns:** {df.shape[1]:,} · **One row per patient:** {df['inpatient_number'].is_unique}.")
    st.write("Charts and counts are calculated from the CSV whenever it changes. Question write-ups are a snapshot from the team's descriptive, prescriptive, and combined predictive notebooks; sidebar filters do not change notebook findings or refit models.")
    st.write("**Coverage:** 10 descriptive questions, 30 prescriptive questions, and four completed predictive questions.")
    st.write("**Source files:** `Team11_PyInsights_05.Findings.json` (the notebook write-up snapshot) and `cleaned_data/Team11_PyInsights_cleaned_data.csv` (live chart data). Update the findings snapshot when team notebooks change.")
    st.markdown("**Data check**")
    st.dataframe(outcome_summary(df).round(1), hide_index=True, use_container_width=True)
    st.markdown("**Interpretation limits**")
    st.write("The cohort is observational and from one hospital. Group differences are associations. Missing predictors, uncertain measurement timing, competing death, and lack of external validation limit clinical use of the models.")
    st.caption("Source study: PhysioNet Hospitalized Patients with Heart Failure (Zigong). The team's cleaning, descriptive, prescriptive, and predictive notebooks document the detailed steps.")
