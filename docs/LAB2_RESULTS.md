# Lab 2 Results: Reproducing the Paper on the Loan Default Dataset

## Dataset (Lab task 1)
- **Name:** Loan Default Dataset, Kaggle, by M. Yasser H. (CC0 licence). https://www.kaggle.com/datasets/yasserh/loan-default-dataset
- **Size:** 148,670 rows × 34 columns. The rows are well above the 100,000 minimum. The columns are 1 short of 35, which was accepted as "2–3 less is OK".
- **Target:** `Status`, where 1 = default and 0 = repaid. 112,031 loans were repaid and 36,639 defaulted (about 25% defaults).

## Paper (Lab task 2), published after 2020, on this exact dataset
Khoong Tai Wai, Nyo Zhi Ni, Chou Nyet Xing, Ng Pei Chi, Lee Ruo Fan, Au Yong Eu Jin. "Financial Institutions Loan Default Prediction Using Machine Learning Models". *Journal of Wealth Management & Financial Planning*, Vol. 12, August 2025.
https://jwmfp.mfpc.org.my/wp-content/uploads/2025/09/2-Paper-Financial-Institutions-Loan-Default-Prediction-Using-Machine-Learning-Models.pdf

**Models in the paper:** Random Forest, XGBoost, Decision Tree, KNN and Logistic Regression.
We trained the same 5 models, so this is **Scenario A** of the lab instructions.

## Preprocessing (copied from the paper)
1. Dropped `ID` and `year`.
2. Dropped 3 columns with many missing values: `rate_of_interest`, `Interest_rate_spread`, `Upfront_charges`.
3. Dropped 3 constant columns: `construction_type`, `Secured_by`, `Security_Type`.
4. Filled missing values with the mode for text columns and the median for number columns.
5. Removed outliers with the IQR rule on `property_value`, `income`, `LTV` and `dtir1`. This left 121,227 rows; the paper had 121,203.
6. Label-encoded the text columns.
7. Made a stratified 80/20 train/test split with `random_state=42`.
8. Applied `StandardScaler` (fitted on the training set only) for KNN and Logistic Regression.

## Our results compared with the paper (test set, class 1 = default)
| Model | Metric | Paper | Ours | Difference |
|---|---|---|---|---|
| Random Forest | Accuracy | 0.8907 | 0.8912 | +0.0005 |
| Random Forest | Precision | 0.9400 | 0.9387 | -0.0013 |
| Random Forest | Recall | 0.6000 | 0.6008 | +0.0008 |
| Random Forest | F1 | 0.7300 | 0.7327 | +0.0027 |
| Random Forest | AUC | 0.8900 | 0.8885 | -0.0015 |
| XGBoost | Accuracy | 0.8970 | 0.8986 | +0.0016 |
| XGBoost | Precision | 0.9200 | 0.9350 | +0.0150 |
| XGBoost | Recall | 0.6400 | 0.6359 | -0.0041 |
| XGBoost | F1 | 0.7600 | 0.7570 | -0.0030 |
| XGBoost | AUC | 0.8900 | 0.8980 | +0.0080 |
| Decision Tree | Accuracy | 0.8847 | 0.8876 | +0.0029 |
| Decision Tree | Precision | 0.9200 | 0.9380 | +0.0180 |
| Decision Tree | Recall | 0.5900 | 0.5860 | -0.0040 |
| Decision Tree | F1 | 0.7200 | 0.7214 | +0.0014 |
| Decision Tree | AUC | 0.8600 | 0.8648 | +0.0048 |
| KNN | Accuracy | 0.8478 | 0.8554 | +0.0076 |
| KNN | Precision | 0.7700 | 0.7931 | +0.0231 |
| KNN | Recall | 0.5500 | 0.5648 | +0.0148 |
| KNN | F1 | 0.6400 | 0.6597 | +0.0197 |
| KNN | AUC | 0.8100 | 0.8154 | +0.0054 |
| Logistic Regression | Accuracy | 0.7732 | 0.7772 | +0.0040 |
| Logistic Regression | Precision | 0.6300 | 0.6436 | +0.0136 |
| Logistic Regression | Recall | 0.2200 | 0.2297 | +0.0097 |
| Logistic Regression | F1 | 0.3200 | 0.3386 | +0.0186 |
| Logistic Regression | AUC | 0.7400 | 0.7530 | +0.0130 |

Confusion matrices for all 5 models: `docs/confusion_matrices.png`

## Discussion
- All five models reproduce the paper's numbers within about ±0.03 on every metric. XGBoost is the best model in both: our accuracy is 0.8986 against the paper's 0.8970, and our AUC is 0.898 against 0.89.
- The paper does not give hyperparameters. With an unlimited-depth Decision Tree we got about 0.82 accuracy. Setting `max_depth=10` reproduced the paper (0.8876 vs 0.8847), so the authors probably limited the depth.
- The ranking is the same as in the paper: XGBoost > Random Forest > Decision Tree > KNN > Logistic Regression.
- Recall for "default" is only about 0.6 for every model, which means the models miss about 40% of the defaulters. This happens because the classes are unbalanced and no resampling was done, which is the same limitation the paper mentions. SMOTE or class weights are the next improvement.
- **Data leakage warning:** in the raw dataset the three dropped columns (`rate_of_interest` and the other two) are missing almost only for defaulted loans. Keeping them as "missing" flags would give close to 100% accuracy that is not real. Dropping them, as the paper does, avoids that.

## Model deployed in the app
For the app, the preprocessing and an XGBoost model are saved together as one sklearn `Pipeline`. It uses a median imputer and one-hot encoding, so the API can accept raw form values. Its test-set scores are accuracy 0.899, precision 0.940, recall 0.633, F1 0.757 and AUC 0.897. It is saved as `backend/models/model_bundle.joblib`.
