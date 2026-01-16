# APSCA Requirements Repository

This repository serves as the single source of truth for APSCA requirements, features, epics, stories, and releases. It is designed to be edited by Project Managers (PMs) using AI assistance and published automatically to a read-only dashboard.

## 📄 Live Documentation

**GitHub Pages:** https://foomstack-framework.github.io/APSCA/story-map.html

> **Note:** GitLab Pages deployment is pending server configuration. Once enabled, the documentation will also be available via GitLab Pages.

---

## 🚀 Workflow for Project Managers

### 1. Setup
1.  **Clone the Repository** to your local machine.
2.  Ensure you have **Python 3** installed.

### 2. Making Changes (The Cycle)
You do not edit the JSON data files manually. You use an AI assistant to make changes safely.

1.  **Pull Latest Changes:** Always start by pulling the latest code from GitLab.
    ```bash
    git pull
    ```
2.  **Run the AI Assistant:** Open your AI tool (e.g., Cursor, Claude Code) in this folder.
3.  **Instruction:** Tell the AI what you want to do.
    > "Add a new feature for 'Student Exam Registration' with a business value of 'High'."
    > "Create a new story under the 'Student Exam Registration' epic for 'Validate Student ID'."
4.  **Verification:** The AI will use the `scripts/mutate.py` tool to update the data.
5.  **Preview:** Run the build script to generate the dashboard locally.
    ```bash
    python scripts/render_docs.py
    ```
    Open `docs/index.html` in your browser to verify your changes look correct.
6.  **Commit & Push:**
    ```bash
    git add .
    git commit -m "Added Student Exam Registration feature"
    git push
    ```
    > **Dual-Remote Setup:** This repository is configured to push to both GitLab and GitHub simultaneously. A single `git push` updates both remotes, triggering CI pipelines on both platforms.

### 3. Merging Changes
If you are working with other PMs, you may encounter "Merge Conflicts" if you both edit the same file (e.g., `stories.json`) at the same time.
*   **Best Practice:** Communicate with your team. "I'm updating the Stories today."
*   **Resolution:** If a conflict occurs, ask your AI assistant to "Fix the JSON syntax errors in stories.json" or resolve the git conflict for you.

---

## 🏗️ Architecture

### 1. Canonical Storage (The Truth)
All data lives in `data/`. These are JSON files that act as our database.
*   `data/domain.json`: Registry of business policies and rules.
*   `data/requirements.json`: High-level system requirements.
*   `data/features.json`: Major capabilities.
*   `data/epics.json`: Large groupings of work.
*   `data/stories.json`: Executable units of work.
*   `data/releases.json`: Delivery timeline.

### 2. Generated Documentation (The View)
The `docs/` folder contains the HTML dashboard. **Do not edit files in `docs/` manually** (except `docs/domain/*.md`). They are overwritten every time the scripts run.

### 3. Scripts
*   `scripts/mutate.py`: The safe way to edit data.
*   `scripts/render_docs.py`: Generates the HTML website.
*   `scripts/validate.py`: Checks that all data is correct (no missing IDs, no broken links).

---

## 🧩 Artifact Taxonomy

**Hierarchy:**
`Domain` → `Requirements` → `Features` → `Epics` → `Stories`

**Delivery:**
`Releases` bind specific versions of Epics and Stories to a date.

---

## 🤖 AI Commands (Advanced)

If using Claude Code or a compatible agent, you can use these slash commands:

*   **/input-requirements**: Paste raw notes/transcripts to parse them into structured approval files.
*   **/integrate-changes**: Execute the changes from an approval file.

---

## Engineering Notes

*   **No Dependencies:** This project uses only the Python Standard Library. No `pip install` required.
*   **Validation:** Run `python scripts/validate.py` to ensure data integrity.

---

## 🔗 Repository Mirrors

This project is mirrored to two remotes:

| Platform | Repository URL | CI/CD |
|----------|----------------|-------|
| GitLab | https://gitlab.ksensetech.com/client-project-documentation-experimental/apsca-react-docs | GitLab CI (Pages pending) |
| GitHub | https://github.com/foomstack-framework/APSCA | GitHub Actions → GitHub Pages |

### Setting Up Dual-Remote Push (New Clone)

If you clone this repository fresh, you can configure `git push` to update both remotes:

```bash
# Add GitHub as a push target for origin
git remote set-url --add --push origin https://gitlab.ksensetech.com/client-project-documentation-experimental/apsca-react-docs.git
git remote set-url --add --push origin https://github.com/foomstack-framework/APSCA.git
```

After this, `git push` will update both GitLab and GitHub simultaneously.
