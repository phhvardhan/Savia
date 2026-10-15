"""
Runs every agent on its sample input through the live backend, saves each output
and does a quick grounding check. Read the saved outputs against README.md.

Usage (backend running on :8000), from the repo root:
    backend/.venv-mac/bin/python agent-test-files/run_all.py              # every case
    backend/.venv-mac/bin/python agent-test-files/run_all.py mom test     # some cases
"""
import json
import sys
import time
from pathlib import Path

import requests

API = "http://localhost:8000/api/v1"
HERE = Path(__file__).parent
INPUTS = HERE / "inputs"
OUT = HERE / "outputs"

# case -> (agent, input files, facts the output must mention, things it must not contain)
CASES = {
    "mom": ("mom", ["01_mom_meeting_transcript.txt"],
            ["Priya", "Tom", "Ken", "Aisha", "Rotterdam", "14 November", "10 November", "reconciliation"], []),
    "agile-stories": ("agile-stories", ["02_agile_stories_requirements.txt"],
                     ["5 minutes", "15 minutes", "audit", "re-post"], []),
    "solution-analyzer": ("solution-analyzer", ["03_solution_analyzer_problem_statement.txt"],
                 ["Rotterdam", "GxP", "SFTP"], ["$", "€", "£"]),
    "gap-analysis": ("gap-analysis", ["04_gap_analysis_requirements_vs_current.txt"],
                     ["REQ-01", "REQ-03"], []),
    "ddl3": ("ddl3", ["05_ddl3_design_input.txt"],
             ["BAPI_GOODSMVT_CREATE", "NL01", "movement_id", "duplicate"], []),
    "kdd-dab": ("kdd-dab", ["06_kdd_dab_architecture_design.txt"],
                    ["Integration Suite", "hourly", "replication", "Rotterdam"], []),
    "change-impact": ("change-impact", ["07_change_impact_change_request.txt"],
                      ["reconciliation", "Power BI", "publisher"], []),
    "test": ("test", ["08_test_user_stories.txt"],
             ["US-01", "US-02", "US-03", "M-1001", "MV-500"], []),
    "readiness-audit": ("readiness-audit", ["09_readiness_audit_deliverable.txt"],
                          ["rollback", "UAT", "performance", "validation"], []),
    # Same agents, other file formats: checks the file readers as well as the agent.
    "docx": ("agile-stories", ["formats/02_agile_stories_requirements.docx"], ["5 minutes", "15 minutes", "re-post"], []),
    "pptx": ("kdd-dab", ["formats/06_kdd_dab_decisions.pptx"], ["Integration Suite", "Rotterdam"], []),
    "pdf": ("readiness-audit", ["formats/09_readiness_audit_pack.pdf"], ["rollback", "UAT"], []),
    # Several files in one upload: the stories should use both the meeting and the BRD.
    "multi": ("agile-stories", ["01_mom_meeting_transcript.txt", "02_agile_stories_requirements.txt"],
              ["5 minutes", "15 minutes", "re-post"], []),
}


def run_case(case: str) -> bool:
    agent, files, must, must_not = CASES[case]
    handles = [open(INPUTS / f, "rb") for f in files]
    try:
        up = requests.post(f"{API}/ingestion/upload",
                           files=[("files", (Path(f).name, h)) for f, h in zip(files, handles)], timeout=300)
    finally:
        for h in handles:
            h.close()
    if not up.ok:
        print(f"FAIL   {case:18} upload HTTP {up.status_code}: {up.text[:200]}")
        return False
    workflow_id = up.json()["workflow_id"]

    rec = requests.post(f"{API}/savia/recommend", json={"workflow_id": workflow_id}, timeout=120)
    picks = [a["agent"] for a in rec.json().get("recommended_agents", []) if a.get("matched")][:3] if rec.ok else []

    started = time.time()
    res = requests.post(f"{API}/agents/{agent}", json={"workflow_id": workflow_id, "bypass_approval": True}, timeout=600)
    seconds = time.time() - started
    if not res.ok:
        print(f"FAIL   {case:18} agent HTTP {res.status_code}: {res.text[:200]}")
        return False

    content = res.json()["content"]
    (OUT / f"{case}.json").write_text(json.dumps(content, indent=2, ensure_ascii=False))
    text = json.dumps(content, ensure_ascii=False).lower()
    missing = [w for w in must if w.lower() not in text]
    invented = [w for w in must_not if w.lower() in text]
    ok = not missing and not invented

    rec_note = "top pick" if picks[:1] == [agent] else ("in top 3" if agent in picks else "NOT recommended")
    print(f"{'PASS' if ok else 'CHECK':6} {case:18} {seconds:4.0f}s  recommender: {rec_note} {picks}")
    if missing:
        print(f"         missing from output: {missing}")
    if invented:
        print(f"         should not appear:   {invented}")
    return ok


def main() -> None:
    cases = sys.argv[1:] or list(CASES)
    unknown = [c for c in cases if c not in CASES]
    if unknown:
        sys.exit(f"Unknown case(s) {unknown}. Choose from: {', '.join(CASES)}")
    try:
        requests.get(f"{API.rsplit('/api', 1)[0]}/health", timeout=5).raise_for_status()
    except requests.RequestException:
        sys.exit("Backend is not running on http://localhost:8000.")
    OUT.mkdir(exist_ok=True)
    passed = sum(run_case(c) for c in cases)
    print(f"\n{passed}/{len(cases)} passed the quick check. Outputs are in {OUT.relative_to(HERE.parent)}/; "
          "read them against README.md.")


if __name__ == "__main__":
    main()
