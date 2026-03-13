---
description: Publish Sanitized Code to GitHub
---

This workflow automates the process of committing and pushing to a public repository while keeping local credentials and project IDs private.

## Prerequisites
-   Correct remote repository URL (e.g., `https://github.com/caugusto/adk_nano_banana2.git`)
-   File exclusions configured in local `.gitignore`.

## Steps

1.  **Prepare Sanitized Workspace**
    Create a temporary directory copy and remove unwanted files listed in your `.gitignore` to avoid pushing them.
    ```bash
    mkdir -p /tmp/sanitized_adk
    # Copy all files from current workspace to temp folder
    cp -R . /tmp/sanitized_adk/
    cd /tmp/sanitized_adk
    # Clean files based on your local workspace setup
    rm -rf .adk .venv __pycache__
    ```

2.  **Sanitize Configurations**
    Use `sed` to replace sensitive values (like `agentspace-452714`) with `<CHANGE-ME>` placeholders.
    ```bash
    sed -i '' 's/agentspace-452714/<CHANGE-ME>/g' agent.py test_live_agent.py deploy_global_env.py run_local_agent.py test_recursive_editing.py README.md
    ```

3.  **Validate Sanitization**
    Check if substitutions were applied properly before pushing.
    ```bash
    grep -H "<CHANGE-ME>" agent.py test_live_agent.py deploy_global_env.py run_local_agent.py test_recursive_editing.py README.md
    ```

4.  **Push to Remote Repo**
    Initialize Git, add the correct remote location, and force-push.
    ```bash
    git init
    # Add your target sanitized repository here
    git remote add origin YOUR_REMOTE_URL_HERE
    git add .
    git commit -m "Initial commit of sanitized code"
    GIT_TERMINAL_PROMPT=0 git push origin main --force
    ```

5.  **Clean up**
    Remove the temporary folder.
    ```bash
    rm -rf /tmp/sanitized_adk
    ```
