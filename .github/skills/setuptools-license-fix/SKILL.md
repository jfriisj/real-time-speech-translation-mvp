# SKILL: Setuptools License Fix (SPDX)

**Purpose**: Fix the `SetuptoolsDeprecationWarning` regarding `project.license` as a table.

## The Issue
`pyproject.toml` contains:
```toml
[project]
license = {text = "MIT"}  # Deprecated table format
```

## The Fix
Change it to a simple string using a valid SPDX identifier:
```toml
[project]
license = "MIT"  # Correct string format
```

## Agent Instruction
- When creating or editing `pyproject.toml`, always use the string format for `license`.
- If you see a build warning about this, apply the fix proactively.
