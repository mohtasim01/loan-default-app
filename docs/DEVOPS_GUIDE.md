# DevOps Guide: Your Manual Steps (deadline 7 PM)

You do every step in this guide yourself. Each step has the commands and a one-line **Why** you can use when explaining it.

**Project folder** (called ROOT below):
`C:\Users\Mohtasim\Personal_Space\MOHTASIM_PERSONAL_SPACE\M_UNI\BSSE-7-A\DevOps\Devops_Lab\DevOps lab app\loan-default-app`

> **Tip:** the path contains spaces, so always wrap it in quotes `"..."` in PowerShell.

---

## STEP 1: Install Node.js (you only have Python + VS Code)
1. Open a PowerShell window and run:
   ```powershell
   winget install OpenJS.NodeJS.LTS
   ```
   If `winget` doesn't work, download the **LTS** Windows installer from https://nodejs.org/en/download and click Next through it.
2. **Close every VS Code window**, then open VS Code again. The new terminal needs the updated PATH.
3. Check that it worked:
   ```powershell
   node --version
   npm --version
   git --version
   ```
   If `git` is not recognized, install Git from https://git-scm.com/downloads/win (default options), then reopen VS Code.

**Why:** Angular runs on Node.js, and npm is the tool that installs Angular's packages.

## STEP 2: Install the Angular CLI
```powershell
npm install -g @angular/cli@22
ng version
```
If PowerShell blocks `ng.ps1`, use `ng.cmd version` instead, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
If it asks to share usage data, type **N**.

**Why:** `ng` is the command that builds and serves the Angular app.

## STEP 3: Open the project and create the Python virtual environment
In VS Code: **File → Open Folder → loan-default-app**. Then open **Terminal → New Terminal** and run:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```
The prompt should now start with `(.venv)`. If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and try again.

**Why:** the venv keeps this project's Python packages separate from everything else on your computer.

## STEP 4: Re-create the model on YOUR machine (takes about 1 minute)
```powershell
python notebooks\train_and_compare.py
python backend\make_payload.py
python backend\test_pipeline.py
```
You should see the paper comparison table and then `PASS: local inference`.

**Why:** a saved `.joblib` model must be loaded with the same scikit-learn/XGBoost versions that created it. Retraining locally guarantees they match.

## STEP 5: Run the backend in Terminal 1 (leave it running)
```powershell
python backend\app.py
```
Open http://127.0.0.1:5000/health in a browser. You should see `"status": "ok"` and `"features": 25`.

**Why:** Flask serves the model as a REST API.

## STEP 6: Test the API in Terminal 2
Click **+** in the terminal panel to open a new terminal. Then run:
```powershell
.\.venv\Scripts\Activate.ps1
python backend\test_api.py
python -m pytest -q backend\tests
```
You should see `PASS: API request` and `5 passed`.

**Why:** automated tests prove the API works before anything is deployed.

## STEP 7: Run the frontend in Terminal 2 (leave it running)
```powershell
cd frontend
npm install
ng serve --open --proxy-config proxy.conf.json
```
The app opens at http://localhost:4200. Click **Fill sample borrower**, then **Check default risk**. A result card should appear.

**Why:** the Angular dev proxy forwards `/api/...` to Flask, so the browser never has CORS problems.

Open **Terminal 3** (another **+**) for all the Git commands below. Terminals 1 and 2 must stay running.

---

## STEP 8: Create the root `.gitignore` BEFORE `git add`
In VS Code, right-click the project root → **New File** → name it `.gitignore`. Paste this in:
```gitignore
# Python
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env

# Angular
frontend/node_modules/
frontend/dist/
frontend/.angular/

# Big raw dataset (28 MB) - download link is in README
data/Loan_Default.csv

# OS / logs
Thumbs.db
.DS_Store
*.log
```
**Why:** these files are huge, machine-specific, or can be regenerated. Never commit them.

## STEP 9: Initialize Git and make the first commit (Terminal 3, at the project root)
```powershell
git init
git branch -M main
git config --global user.name "Mohtasim Abbasi"
git config --global user.email "YOUR_GITHUB_EMAIL"
git add .
git status --short
```
Check the list. If `.venv`, `node_modules` or `Loan_Default.csv` appear, **stop**, fix `.gitignore`, and run `git restore --staged <path>`. If the list is clean:
```powershell
git commit -m "Initial full-stack ML app: Flask API + Angular form + trained model"
git log --oneline -1
```
**Why:** a commit is a saved snapshot of the code that you can always go back to.

## STEP 10: Create the GitHub repository and push
1. Go to https://github.com → **+** → **New repository**.
2. Name it **`loan-default-app`** and choose **Public** (Pages needs it).
3. **Do not** tick README, .gitignore or licence.
4. Click **Create repository**.
5. Back in Terminal 3:
   ```powershell
   git remote add origin https://github.com/YOUR_USERNAME/loan-default-app.git
   git remote -v
   git push -u origin main
   ```
   If a browser login opens, sign in. Then refresh the GitHub page: `backend/`, `frontend/`, `docs/` and `notebooks/` should all be there.

**Why:** `origin` is the remote copy, and `push` uploads your commits to it.

## STEP 11: Add your instructor as a collaborator (before 7 PM)
On GitHub, go to the repo → **Settings** → **Collaborators** → **Add people**. Enter the instructor's GitHub username or email, then click **Add**. They must accept the invite.

**Why:** this gives them access to review your repository.

## STEP 12: CI with GitHub Actions
Create the file `.github/workflows/ci.yml`. Right-click the root → New File → type `.github/workflows/ci.yml` (VS Code creates the folders). Paste this in:
```yaml
name: Full-stack CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: backend/requirements.txt
      - run: python -m pip install -r backend/requirements.txt
      - run: python -m pytest -q backend/tests/test_structure.py
      # The model file is committed, so the API tests can run in CI too:
      - run: python -m pytest -q backend/tests/test_api.py

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: angular-build
          path: frontend/dist/
```
Then commit and push:
```powershell
git add .github/workflows/ci.yml
git commit -m "Add backend and Angular CI"
git push
```
On GitHub, open **Actions** → **Full-stack CI** and wait for the green ✔.

> **Note:** if `test_api.py` fails in CI with a version error, the model was saved with different library versions. Delete that one `run:` line and push again. That is the "artifact decision" from Stage 13.1 of the manual.

**Why:** CI tests and builds every push automatically on a clean Linux machine, which catches "works on my PC" bugs.

## STEP 13: CD to GitHub Pages (Angular only)
1. On GitHub, go to the repo → **Settings** → **Pages** → **Source: GitHub Actions**.
2. Create `.github/workflows/pages.yml`:
```yaml
name: Deploy Angular to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: github-pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
        working-directory: frontend
      - run: npx ng build --configuration production --base-href /loan-default-app/
        working-directory: frontend
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/dist/frontend/browser
      - id: deployment
        uses: actions/deploy-pages@v4
```
3. Commit and push:
```powershell
git add .github/workflows/pages.yml
git commit -m "Deploy Angular static frontend to GitHub Pages"
git push
```
When the workflow is green, open `https://YOUR_USERNAME.github.io/loan-default-app/`. The form shows a yellow notice and the button is disabled. **That is expected**, because GitHub Pages can't run Python/Flask.

**Why:** CD deploys the latest frontend automatically after every push. `--base-href` must match the repo name, or the page will be blank.

## STEP 14: Show that CI/CD works (good for the demo)
Change the `<h1>` text in `frontend/src/app/app.html`, then run:
```powershell
git add . ; git commit -m "Update UI title" ; git push
```
Watch both workflows run, then refresh the Pages URL to see the new title.

---

## Troubleshooting
| Problem | Fix |
|---|---|
| `node`/`ng` not recognized | Close **all** VS Code windows and reopen; try `ng.cmd` |
| venv activation blocked | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| Angular shows "API error 504/502" | Flask isn't running in Terminal 1 |
| `/api/health` gives 404 | You started `ng serve` without `--proxy-config proxy.conf.json` |
| Port 5000 in use | An old Flask is still running. Press Ctrl+C in that terminal |
| `git push` rejected | You ticked "Add README" when creating the repo. Recreate it empty |
| Pages blank / 404 | Wrong `--base-href`, or Pages Source isn't set to "GitHub Actions" |
