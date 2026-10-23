"""Validate this repository's instruction-only skill package without dependencies."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    skills = sorted((ROOT / ".agents/skills").glob("*/SKILL.md"))
    if len(skills) != 6:
        errors.append("Expected six tutor skills.")
    for path in skills:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\nname: ([a-z0-9]+(?:-[a-z0-9]+)*)\ndescription: ([^\n]+)\n---\n", text)
        if not match:
            errors.append(f"Invalid simple YAML front matter: {path.relative_to(ROOT)}")
            continue
        name, description = match.groups()
        if name != path.parent.name or len(name) > 64 or not 1 <= len(description) <= 1024:
            errors.append(f"Invalid skill metadata: {name}")
        if "TODO" in text:
            errors.append(f"Unfinished skill: {name}")
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or "private" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if re.match(r"[a-z]+://|#", target):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                errors.append(f"Broken local link in {path.relative_to(ROOT)}: {target}")
    protected = ["private/progress.json", "private/test.session.md", "recordings/test.wav", ".env"]
    ignored = subprocess.run(["git", "check-ignore", "--no-index", *protected], cwd=ROOT,
                             capture_output=True, text=True)
    if ignored.returncode != 0 or set(ignored.stdout.splitlines()) != set(protected):
        errors.append("Personal record ignore rules failed.")
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    for item in tracked.stdout.splitlines():
        if item.startswith(("private/", "progress/", "session-logs/", "recordings/")) or item == ".env":
            errors.append(f"Personal data path is tracked: {item}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Validated six skill manifests, local Markdown links, and private-path Git exclusions.")


if __name__ == "__main__":
    main()
