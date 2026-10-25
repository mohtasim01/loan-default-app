# Loan Default Risk Checker: Full-Stack ML App with CI/CD

**Author:** Mohtasim Abbasi (BSSE-7-A, 232043). DevOps Lab, Air University Islamabad.

You enter a borrower's loan application in an **Angular** form. A **Flask** REST API runs a trained **XGBoost** pipeline and returns the probability that the loan will default.

| Item | Details |
|---|---|
| Problem | Binary classification: will the borrower default? (`Status`: 1 = default) |
| Dataset | [Kaggle Loan Default Dataset (yasserh)](https://www.kaggle.com/datasets/yasserh/loan-default-dataset). 148,670 rows × 34 columns, CC0 licence |
| Paper reproduced | Khoong et al., *Financial Institutions Loan Default Prediction Using ML Models*, JWMFP Vol. 12, 2025 |
| Deployed model | Pipeline (imputer + one-hot encoder + XGBoost). Accuracy 0.899, F1 0.757, AUC 0.897 |
| Stack | Python 3, scikit-learn, XGBoost, Flask, Angular 22, Node 24, GitHub Actions, GitHub Pages |

## Project structure
```
backend/       Flask API (app.py), model bundle, tests
data/          sample_inputs.csv (put Loan_Default.csv here to retrain)
docs/          LAB2_RESULTS.md, WORK_LOG.md, DEVOPS_GUIDE.md, metrics + confusion matrices
frontend/      Angular app (form, service, proxy.conf.json)
notebooks/     train_and_compare.py: preprocessing, 5 models, paper comparison, saves the model
```

## Run locally
```powershell
py -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python notebooks\train_and_compare.py      # needs data\Loan_Default.csv
python backend\make_payload.py
python backend\app.py                      # Terminal 1 -> http://127.0.0.1:5000/health
cd frontend ; npm install
ng serve --open --proxy-config proxy.conf.json   # Terminal 2 -> http://localhost:4200
```

## Tests
```powershell
python -m pytest -q backend\tests          # 5 tests
```

## API
- `GET /health`: server status and the number of features
- `GET /schema`: input fields and allowed values
- `POST /predict`: a JSON object with the 25 features. Returns `prediction`, `label` and `default_probability`

## Deployment limitation
GitHub Pages hosts **only the static Angular page**. Predictions need Flask running locally, so the live Pages site shows a notice and disables the button.

## Disclaimer
This is a teaching prototype. It is not a real credit-decision system.
