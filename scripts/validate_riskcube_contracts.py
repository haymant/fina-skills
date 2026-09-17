import json
from pathlib import Path
from jsonschema import Draft202012Validator

root = Path(__file__).resolve().parents[1]
schema_dir = root / "schema" / "riskcube"
for path in sorted(schema_dir.glob("*.schema.json")):
    document = json.loads(path.read_text())
    Draft202012Validator.check_schema(document)
    print(f"valid schema: {path.relative_to(root)}")

required_refs = [
    root / "refs/riskcube/scenario-version-contract.md",
    root / "refs/riskcube/report-management.md",
    root / "refs/riskcube/columnar-storage-and-olap.md",
    root / "refs/riskcube/finap-routes-and-actions.md",
    root / "refs/riskcube/dev-agent-prompt.md",
]
for path in required_refs:
    assert path.exists() and path.stat().st_size > 0, path
    print(f"present reference: {path.relative_to(root)}")

for path in [root / "skills/fina-risk/SKILL.md", root / "skills/fina-olap/SKILL.md", root / "skills/finap-dev/SKILL.md"]:
    text = path.read_text()
    assert "riskcube" in text.lower(), path
    print(f"wired skill: {path.relative_to(root)}")
