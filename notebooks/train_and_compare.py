"""
Lab 2 - Loan Default Prediction
Dataset : Kaggle "Loan Default Dataset" (yasserh) - Loan_Default.csv, 148,670 rows x 34 columns
Paper   : Khoong T.W. et al., "Financial Institutions Loan Default Prediction Using
          Machine Learning Models", Journal of Wealth Management & Financial Planning,
          Vol. 12, Aug 2025.

What this script does (run from project root:  python notebooks/train_and_compare.py)
  PART A  Reproduce the paper (Scenario A - same 5 models: RF, XGBoost, DT, KNN, LR)
          using the paper's own preprocessing, then compare our metrics with theirs.
  PART B  Build ONE deployable model (sklearn Pipeline = preprocessing + XGBoost)
          and save it to backend/models/model_bundle.joblib for the Flask API.
"""
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                      # draw plots to files, no window needed
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             ConfusionMatrixDisplay)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent.parent          # project root folder
DATA = ROOT / "data" / "Loan_Default.csv"
DOCS = ROOT / "docs"
MODELS = ROOT / "backend" / "models"
DOCS.mkdir(exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
SEED = 42                                              # same random_state as the paper

# ----------------------------------------------------------------------------
# 1. LOAD + BASIC CHECKS
# ----------------------------------------------------------------------------
df = pd.read_csv(DATA)
print("Raw shape:", df.shape)                          # expect (148670, 34)
TARGET = "Status"                                      # 1 = default, 0 = paid

# ----------------------------------------------------------------------------
# 2. PREPROCESSING EXACTLY AS DESCRIBED IN THE PAPER
# ----------------------------------------------------------------------------
# 2a. drop ID/year + 3 columns with heavy missing data + 3 constant columns
DROP = ["ID", "year",                                  # identifier / single year
        "rate_of_interest", "Interest_rate_spread", "Upfront_charges",  # heavy missing
        "construction_type", "Secured_by", "Security_Type"]             # constant
df = df.drop(columns=DROP)

features = df.drop(columns=[TARGET])
num_cols = features.select_dtypes(include="number").columns.tolist()      # numeric columns
cat_cols = [c for c in features.columns if c not in num_cols]             # text columns

# 2b. missing values: categorical -> mode, numerical -> median
for c in cat_cols:
    df[c] = df[c].fillna(df[c].mode()[0])
for c in num_cols:
    df[c] = df[c].fillna(df[c].median())

# 2c. outlier removal with IQR rule on 4 columns named in the paper
for c in ["property_value", "income", "LTV", "dtir1"]:
    q1, q3 = df[c].quantile([0.25, 0.75])
    iqr = q3 - q1
    df = df[(df[c] >= q1 - 1.5 * iqr) & (df[c] <= q3 + 1.5 * iqr)]
print("After cleaning:", df.shape, "(paper: 121,203 x 27)")

# keep a clean copy (text categories) for the deployable pipeline in PART B
clean = df.copy()

# 2d. label encoding of categorical columns (paper's choice)
enc = df.copy()
for c in cat_cols:
    enc[c] = LabelEncoder().fit_transform(enc[c].astype(str))

X = enc.drop(columns=[TARGET])
y = enc[TARGET]

# 2e. 80:20 split, random_state=42 (stratify keeps the default ratio equal)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                          random_state=SEED, stratify=y)
print("Train:", X_tr.shape, " Test:", X_te.shape)

# 2f. StandardScaler only for KNN and LR (distance / gradient based models)
scaler = StandardScaler().fit(X_tr)                    # fit on TRAIN only (no leakage)
X_tr_s, X_te_s = scaler.transform(X_tr), scaler.transform(X_te)

# ----------------------------------------------------------------------------
# 3. TRAIN THE SAME 5 MODELS AS THE PAPER
# ----------------------------------------------------------------------------
models = {
    "Random Forest": (RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1), False),
    "XGBoost":       (XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                                    eval_metric="logloss", random_state=SEED, n_jobs=-1), False),
    "Decision Tree": (DecisionTreeClassifier(max_depth=10, random_state=SEED), False),  # depth 10 matches paper
    "KNN":           (KNeighborsClassifier(n_neighbors=5, n_jobs=-1), True),
    "Logistic Regression": (LogisticRegression(max_iter=1000), True),
}

# numbers reported in the paper (test set, class 1 = default)
PAPER = {
    "Random Forest":       dict(Accuracy=0.8907, Precision=0.94, Recall=0.60, F1=0.73, AUC=0.89),
    "XGBoost":             dict(Accuracy=0.8970, Precision=0.92, Recall=0.64, F1=0.76, AUC=0.89),
    "Decision Tree":       dict(Accuracy=0.8847, Precision=0.92, Recall=0.59, F1=0.72, AUC=0.86),
    "KNN":                 dict(Accuracy=0.8478, Precision=0.77, Recall=0.55, F1=0.64, AUC=0.81),
    "Logistic Regression": dict(Accuracy=0.7732, Precision=0.63, Recall=0.22, F1=0.32, AUC=0.74),
}

rows = []
fig, axes = plt.subplots(1, 5, figsize=(24, 4.5))
for ax, (name, (model, scaled)) in zip(axes, models.items()):
    Xa, Xb = (X_tr_s, X_te_s) if scaled else (X_tr, X_te)
    model.fit(Xa, y_tr)
    pred = model.predict(Xb)
    prob = model.predict_proba(Xb)[:, 1]
    ours = dict(Accuracy=accuracy_score(y_te, pred),
                Precision=precision_score(y_te, pred),
                Recall=recall_score(y_te, pred),
                F1=f1_score(y_te, pred),
                AUC=roc_auc_score(y_te, prob))
    for metric, value in ours.items():
        rows.append(dict(Model=name, Metric=metric, Ours=round(value, 4),
                         Paper=PAPER[name][metric],
                         Difference=round(value - PAPER[name][metric], 4)))
    ConfusionMatrixDisplay(confusion_matrix(y_te, pred),
                           display_labels=["Paid (0)", "Default (1)"]).plot(ax=ax, colorbar=False)
    ax.set_title(name)
    print(f"{name:20s}", {k: round(v, 4) for k, v in ours.items()})

plt.tight_layout()
plt.savefig(DOCS / "confusion_matrices.png", dpi=120)
comparison = pd.DataFrame(rows)
comparison.to_csv(DOCS / "paper_vs_ours.csv", index=False)
wide = comparison.pivot_table(index="Model", columns="Metric", values=["Ours", "Paper"])
print("\n", wide.round(4).to_string())

# ----------------------------------------------------------------------------
# 4. PART B - DEPLOYABLE MODEL (raw form values in -> prediction out)
#    Preprocessing is INSIDE the pipeline, so Flask can send raw text/numbers.
# ----------------------------------------------------------------------------
Xc = clean.drop(columns=[TARGET])
yc = clean[TARGET]
Xc_tr, Xc_te, yc_tr, yc_te = train_test_split(Xc, yc, test_size=0.2,
                                              random_state=SEED, stratify=yc)
preprocess = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), num_cols),
    ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                      ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols),
])
pipeline = Pipeline([
    ("preprocess", preprocess),
    ("model", XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                            eval_metric="logloss", random_state=SEED, n_jobs=-1)),
])
pipeline.fit(Xc_tr, yc_tr)
p = pipeline.predict(Xc_te)
deploy_metrics = dict(Accuracy=accuracy_score(yc_te, p), Precision=precision_score(yc_te, p),
                      Recall=recall_score(yc_te, p), F1=f1_score(yc_te, p),
                      AUC=roc_auc_score(yc_te, pipeline.predict_proba(Xc_te)[:, 1]))
print("\nDeployable pipeline:", {k: round(v, 4) for k, v in deploy_metrics.items()})

# input schema for the Angular form (name, type, options / ranges)
schema = []
for c in Xc.columns:
    if c in cat_cols:
        schema.append(dict(name=c, kind="category",
                           options=sorted(Xc[c].astype(str).unique().tolist())))
    else:
        schema.append(dict(name=c, kind="number",
                           min=float(Xc[c].min()), max=float(Xc[c].max())))

bundle = {"pipeline": pipeline, "features": list(Xc.columns), "task": "classification",
          "classes": {"0": "Will repay", "1": "Likely to default"},
          "model_version": "1.0", "metrics": deploy_metrics, "schema": schema}
joblib.dump(bundle, MODELS / "model_bundle.joblib")
(DOCS / "feature_schema.json").write_text(json.dumps(schema, indent=2))

# same schema as TypeScript for the Angular form (Stage 9.1 of the lab manual)
LABELS = {"approv_in_adv": "Approved in advance", "Neg_ammortization": "Negative amortization",
          "LTV": "Loan-to-value ratio (%)", "dtir1": "Debt-to-income ratio (%)",
          "term": "Term (months)", "income": "Monthly income",
          "co-applicant_credit_type": "Co-applicant credit bureau",
          "credit_type": "Credit bureau", "age": "Age group"}
ts_fields = []
for f in schema:
    label = LABELS.get(f["name"], f["name"].replace("_", " ").replace("-", " ").strip().capitalize())
    extra = (f", options: {json.dumps(f['options'])}" if f["kind"] == "category"
             else f", min: {f['min']:g}, max: {f['max']:g}")
    ts_fields.append(f"  {{ name: '{f['name']}', label: '{label}', kind: '{f['kind']}', "
                     f"required: true{extra} }},")
sample = Xc_te.head(1).iloc[0]
sample_ts = ",\n".join(
    f"  '{c}': {json.dumps(str(v)) if c in cat_cols else float(v)}" for c, v in sample.items())
(ROOT / "frontend/src/app/feature-schema.ts").write_text(
    "// AUTO-GENERATED by notebooks/train_and_compare.py - exact raw inputs of the model\n"
    "export type Feature = {\n  name: string; label: string; kind: 'number' | 'category';\n"
    "  required: boolean; options?: string[]; min?: number; max?: number;\n};\n\n"
    "export const FEATURES: Feature[] = [\n" + "\n".join(ts_fields) + "\n];\n\n"
    "// one real test-set borrower, used by the 'Fill sample' button\n"
    "export const SAMPLE: Record<string, string | number> = {\n" + sample_ts + "\n};\n",
    encoding="utf-8")

# one sample row (no target) for API tests - Stage 5 of the lab manual
Xc_te.head(1).to_csv(ROOT / "data" / "sample_inputs.csv", index=False)
print("Saved backend/models/model_bundle.joblib and data/sample_inputs.csv")
