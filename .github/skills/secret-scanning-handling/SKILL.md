# SKILL: Secret Scanning Handling

**Purpose**: Guide agents on how to prevent and remediate secret leakage in git repositories.

## Prevention
1.  **Never commit real secrets**. Use placeholders (e.g., `YOUR_TOKEN`) or environment variables.
2.  **Configuration Files**: For tools like MCP (`mcp.json`) or VS Code (`settings.json`), use syntax that references environment variables if supported, or ensure the file is `.gitignore`d if it must contain secrets.
3.  **Audit before Commit**: Run `git diff --cached` and look for keys, tokens, or passwords.

## Remediation (If blocked by GitHub Push Protection)
1.  **Identify the Secret**: The error message will list the file and line number.
2.  **Remove the Secret**: Edit the file to replace the secret with a placeholder or remove it entirely.
3.  **Amend the Commit** (if it was just committed locally):
    ```bash
    git add <file>
    git commit --amend
    ```
4.  **Re-push**:
    ```bash
    git push origin <branch>
    ```
5.  **If the secret is deep in history**: You may need an interactive rebase (dangerous/advanced) or to use tools like `git-filter-repo`. For immediate unblocking, refer to the GitHub link provided in the error message to "Resolve" the alert if it's a false positive or test credential.

## Agent Instruction
- When writing configuration files, default to secure patterns (placeholders/env vars).
- If a push fails due to secrets, perform the Remediation steps immediately.
