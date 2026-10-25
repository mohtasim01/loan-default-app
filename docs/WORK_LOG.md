# Work Log: what was done, why, and how (one line each)

Each line has three parts: **What**, then *why* (after the →), then `how` (after the second →).

## Part 1: Dataset and paper (Lab 2, done by Claude)
1. **Picked the dataset** → it has 148,670 rows (≥100k) and 34 columns (about 35), it isn't on the class list, and it is a real business problem → *Kaggle "Loan Default Dataset" (yasserh)*.
2. **Found a paper published after 2020 on this exact dataset** → the lab requires results that are already benchmarked → *Khoong et al., JWMFP Vol. 12, Aug 2025, which tests RF, XGBoost, DT, KNN and LR*.
3. **Chose Scenario A** → our models are the same 5 the paper uses → *we re-implemented the paper and compared metrics*.

## Part 2: Preprocessing and training (done by Claude, `notebooks/train_and_compare.py`)
4. **Dropped ID, year, 3 columns with heavy missing values, and 3 constant columns** → they carry no useful signal, or they leak the answer (a missing interest rate means default 100% of the time) → `df.drop(columns=DROP)`.
5. **Filled missing values** → models can't train on NaN → *mode for text columns, median for number columns, with `fillna`*.
6. **Removed outliers with IQR** → extreme incomes and property values distort the models → *kept rows within Q1−1.5·IQR to Q3+1.5·IQR*.
7. **Label-encoded the text columns** → the models need numbers → `LabelEncoder`.
8. **Split the data 80/20, stratified, random_state=42** → it matches the paper and keeps the 25% default rate in both sets → `train_test_split`.
9. **Scaled the features for KNN and LR only** → distance-based and gradient-based models are sensitive to feature scale → *`StandardScaler` fitted on the training set only (no leakage)*.
10. **Trained the 5 models and computed Accuracy, Precision, Recall, F1, AUC and the confusion matrix** → to compare with the paper → `sklearn.metrics` *gives* `docs/paper_vs_ours.csv` *and* `confusion_matrices.png`.
11. **Matched the paper within ±0.03, with XGBoost best (89.9% accuracy)** → this shows the reproduction is valid → *see `docs/LAB2_RESULTS.md`*.
12. **Built the deployable model** → the API must accept raw form values, so the preprocessing has to live inside the model → *a `Pipeline(ColumnTransformer + XGBoost)` saved with `joblib` as `backend/models/model_bundle.joblib`*.

## Part 3: Backend (Flask, done by Claude, lab manual stages 5–7)
13. **`backend/app.py`** → a REST API that serves the model → `GET /health`, `GET /schema` and `POST /predict` *(checks the inputs, returns the prediction and the default probability)*.
14. **`make_payload.py` and `test_payload.json`** → one real test borrower, used for testing → *converts `data/sample_inputs.csv` to JSON*.
15. **`test_pipeline.py`** → proves the model works without Flask → *loads the bundle and predicts*.
16. **`test_api.py` and `tests/test_api.py`** → prove the API works, including error cases → *Requests call to the running server, plus 4 pytest tests (all pass)*.
17. **`tests/test_structure.py`** → a CI-safe test that does not need the model → *checks that the key files exist*.

## Part 4: Frontend (Angular 22, done by Claude, lab manual stages 8–10)
18. **`ng new frontend`** → creates the Angular project skeleton → *standalone app (`app.ts`, `app.html`, `app.css`)*.
19. **`feature-schema.ts`** → defines the 25 form fields (names, dropdown options, ranges) → *generated automatically by the training script from the real data*.
20. **`prediction.service.ts` and `provideHttpClient()`** → let Angular call Flask → *`POST /api/predict`*.
21. **`proxy.conf.json`** → in local dev, forwards `/api` to Flask on port 5000 → *avoids CORS problems*.
22. **`app.ts`, `app.html`, `app.css`** → the form, plus "Fill sample borrower", input validation and a result card with a risk bar → *uses Angular signals and template-driven forms*.
23. **Verified end to end** → Angular → proxy → Flask → model → result shows "Will repay, 7.4%" → *`npm run build` passes and a browser test passes*.

## Part 5: DevOps (YOU do this, see `docs/DEVOPS_GUIDE.md`)
24. Install Node, the Angular CLI and the Python venv. Run both servers.
25. Write `.gitignore`, then `git init`, commit, create the GitHub repo and push.
26. Add your instructor as a collaborator.
27. Add a GitHub Actions CI workflow (tests + build).
28. Deploy the Angular site to GitHub Pages with GitHub Actions.
