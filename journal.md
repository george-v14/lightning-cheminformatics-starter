# Learning Journey Notes
This journal will record my observations and learnings during this build. 

# Project Milestones

## Milestone 1 - Development Environment

### Accomplishments

- Created GitHub repository
- Created Lightning AI Python Studio
- Connected GitHub repository to Lightning AI
- Configured Git identity
- Configured Git credential storage
- Established Git workflow (clone, pull, commit, push)
- Created initial project architecture
- Designed repository structure
- Wrote project README
- Added Mermaid architecture diagram
- Created notebook decomposition document

### Lessons Learned

- Lightning AI Studio provides a cloud-native VS Code development environment.
- HTTPS GitHub authentication requires a Personal Access Token.
- Git credential storage significantly reduces development friction.
- Mermaid diagrams render on GitHub but not in the Lightning AI VS Code preview.
- Spending time designing project architecture before coding reduces refactoring later.

### Next Milestone

Execute the original Practical Cheminformatics notebook without modification.

## Milestone 2 – Baseline Notebook Reproduction

**Objective:** Execute the original *Building a Machine Learning Model with BindingDB* notebook from Practical Cheminformatics inside Lightning AI Studio without modifying the scientific workflow.

### Outcome

Successfully executed the notebook end-to-end within a Lightning AI Python Studio environment.

The notebook successfully:

* Loaded the required Python libraries
* Queried the sample BindingDB DuckDB database
* Retrieved PXR assay data
* Cleaned and transformed EC50 values
* Generated molecular descriptors with RDKit
* Trained a LightGBM regression model
* Evaluated model performance
* Produced activity predictions and visualizations

### Environment Setup

Instead of relying on the Google Colab installation cell, project dependencies were managed through a `requirements.txt` file and installed using:

```bash
pip install -r requirements.txt
```

This establishes a reproducible project environment independent of Google Colab.

### Compatibility Issues Encountered

#### Missing project dependencies

The notebook assumes several scientific Python packages are already installed in the execution environment.

Resolution:

* Created a project-level `requirements.txt`
* Installed all dependencies using pip

#### Missing helper module

The notebook dynamically downloads `download_pdb_ids.py` when executed in Google Colab.

Because Lightning AI skips the Colab-specific installation block, this helper module had to be downloaded manually into the notebook directory.

Observation:

Research notebooks often depend on helper scripts that are fetched dynamically. These should eventually become part of the application's source code rather than being downloaded during execution.

#### Pandas missing value compatibility

One notebook cell assumed missing values would be represented as `None`:

```python
if r is None:
```

Within the Lightning AI environment, missing values were represented as `NaN`, resulting in:

```
AttributeError: 'float' object has no attribute 'split'
```

Resolution:

Replaced the `None` check with:

```python
pd.isna(r)
```

This correctly handles both `None` and `NaN` values.

### Key Takeaways

Successfully reproducing a notebook involves much more than executing cells. The process surfaced several categories of reproducibility challenges common in scientific machine learning workflows:

* Environment configuration
* Dependency management
* External helper scripts
* Data compatibility across library versions

These issues are typically minor individually, but collectively represent the work required to transform a research notebook into a reproducible software project.

### Next Milestone

Refactor the notebook into reusable Python modules while preserving the scientific workflow. The notebook will remain the reference implementation, while reusable functionality will be migrated into the `src/` package to support a configurable Streamlit application.

### Lightning AI Port Viewer

Unlike local development, applications running inside Lightning AI Python Studio are not automatically accessible through `localhost`.

Web applications must be exposed through the Lightning AI **Port Viewer** by forwarding the appropriate application port (e.g., Streamlit on port 8501).

This allows the application to be securely accessed through a Lightning-generated URL without exposing the underlying virtual machine.

## Milestone 3 – Initial Streamlit Application

Successfully converted the BindingDB PXR notebook workflow into a first Streamlit application running inside Lightning AI Studio.

The app supports:
- Viewing cleaned BindingDB PXR data
- Training a LightGBM QSAR model
- Saving the trained model artifact
- Predicting pEC50 from user-entered SMILES
- Rendering the input molecule

Key Lightning AI lesson: Streamlit apps running in Python Studio must be exposed through the Port Viewer on port 8501.

### Removed notebook-specific dependency

The original notebook imports `mols2grid` for interactive molecule visualization inside Jupyter.

The Streamlit application replaces this functionality with native Streamlit components (`st.dataframe`) and RDKit molecule rendering, so `mols2grid` is no longer required.

Observation:

Research notebooks frequently include visualization libraries that are tightly coupled to the notebook environment. When converting notebooks into applications, these dependencies can often be removed in favor of the application's native UI framework.



## Common Git Workflow Commands
## Git Lessons from Lightning AI Studio Setup

### 1. Cloning a repository

I cloned my GitHub repository into the Lightning AI Studio using HTTPS:

```bash
git clone https://github.com/george-v14/lightning-cheminformatics-starter.git
cd lightning-cheminformatics-starter
```

This created a local copy of the repository inside the Studio environment.

---

### 2. Checking repository status

Before committing or pulling changes, check the repo state:

```bash
git status
```

This shows:

* which branch I am on
* which files have changed
* which files are staged
* whether there are uncommitted changes

---

### 3. Pulling updates from GitHub

If I make changes directly on GitHub or from another machine, update the Studio copy with:

```bash
git pull origin main
```

This brings the latest remote changes into the local Studio repository.

---

### 4. Configuring Git identity

The first time I tried to commit inside Lightning AI Studio, Git did not know who I was.

Fix:

```bash
git config --global user.name "my name"
git config --global user.email "my-email@gmail.com"
```

Verify:

```bash
git config --global --list
```

Git requires this identity information to create commits.

---

### 5. Understanding `dquote>`

At one point the terminal showed:

```bash
dquote>
```

This means the shell thinks I opened a double quote `"` and never closed it.

Most likely cause: accidentally pasting or typing an unmatched quote.

Ways to exit:

* Press `Ctrl + C`, or
* Type a closing `"` and press Enter

Lesson: paste commands one line at a time when setting up a new environment.

---

### 6. Understanding `(END)` / `less`

When I ran:

```bash
git config --global --list
```

the terminal opened the output in a pager called `less`.

The clue was:

```text
(END)
```

at the bottom of the terminal.

To exit:

```text
q
```

Useful `less` commands:

* `q` = quit
* `Space` = next page
* `b` = previous page
* `/text` = search
* `g` = top
* `G` = bottom

---

### 7. Committing changes

The basic commit workflow:

```bash
git status
git add .
git commit -m "Clear description of change"
```

Example:

```bash
git add .
git commit -m "Add common git commands to journal.md"
```

A commit records a snapshot of the staged changes in the local repository.

---

### 8. Pushing changes to GitHub

After committing locally, push to GitHub:

```bash
git push origin main
```

Because I cloned using HTTPS, GitHub asks for:

```text
Username: george-v14
Password: personal access token
```

GitHub does not allow normal account passwords for Git operations over HTTPS. A personal access token is required.

---

### 9. Personal access token setup

For this project, I used a GitHub personal access token.

Recommended token setup:

* Fine-grained token
* Repository access limited to `lightning-cheminformatics-starter`
* Permission: `Contents: Read and write`

This gives enough access to push code without granting unnecessary permissions.

---

### 10. Avoiding repeated PAT entry

By default, Git asked for my personal access token on every push. This creates friction.

To store credentials in the Studio environment:

```bash
git config --global credential.helper store
```

Then run one more push:

```bash
git push origin main
```

Enter username and PAT one final time. After that, Git stores the credential and should stop prompting for every push.

Tradeoff:

* More convenient
* Less secure because the token is stored in plain text at `~/.git-credentials`

This is acceptable for this learning project because the token is fine-grained and limited to one repository.

Verify credential helper:

```bash
git config --global --get credential.helper
```

Expected output:

```text
store
```

---

### 11. Current working Git loop

My normal workflow inside Lightning AI Studio is now:

```bash
git status
git add .
git commit -m "Describe the change"
git push origin main
```

When GitHub has newer changes:

```bash
git pull origin main
```

---

### 12. Key takeaway

The first useful lesson from this project was not cheminformatics or machine learning. It was understanding the cloud development workflow:

* clone a GitHub repository
* configure Git identity
* make local commits
* authenticate with GitHub
* push changes from a cloud environment
* reduce workflow friction with credential storage

These small setup details matter because they determine whether cloud-based scientific AI development feels smooth or frustrating.


## Trying the Streamlit Studio and AI Builder
Create github repo first. I usually skip this step and create the Lightning AI Studio. 
Lightning AI has pre-configured studio options for this project I selected Streamlit which gives the option to generate app from text prompt. We are using
"Create a Streamlit application for exploring molecular properties using RDKit. The application should allow a user to enter a SMILES string, render the molecule, compute basic molecular descriptors (molecular weight, LogP, TPSA, H-bond donors, H-bond acceptors), and display them in a table. Organize the code cleanly so that cheminformatics functions are separated from the Streamlit UI. Use Python, RDKit, pandas, and streamlit. The application should be designed to be extended later with machine learning models and molecular similarity search."

The Streamlit Studio defaults to building just the Streamlit application and using the AI tool requires credits. Will use the stadnard Python studio for the remainder of project.

## Intro to Studios
A Studio is a cloud supercomputer
Unlike your laptop, a Studio has infinite disk space, GPUs and fast internet. Code together from the browser or connect your local IDE.
What can you do with a Studio?
Code together. Prototype. Train models. Serve models. Host AI apps. Prep data and more.

We recommend you tailor each Studio to a use-case such as a Studio to train a model, another Studio to process a dataset.
Using Studios
Step 1 - Bring your code by cloning repo or uploading
Step 2 - Bring your data
Step 3 - Install packages
Step 4 - Add studio plugins

## Research Notebooks
Research notebooks often depend on small helper scripts that are downloaded dynamically. For a production application, these helper utilities should become part of the project's source code rather than being fetched at runtime.

### Pandas missing values issue

The original notebook checked for missing PDB IDs using `r is None`, but in the Lightning AI environment the missing values appeared as `NaN`, which is represented as a float. This caused an `AttributeError` when the notebook tried to call `.split()` on a float.

Fix: use `pd.isna(r)` to detect both `None` and `NaN`.