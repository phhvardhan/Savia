import json
import sys
import time
from pathlib import Path

import requests

API = "http://localhost:8000/api/v1"
HERE = Path(__file__).parent
INPUTS = HERE / "inputs"
OUT = HERE / "outputs"

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
    "docx": ("agile-stories", ["formats/02_agile_stories_requirements.docx"], ["5 minutes", "15 minutes", "re-post"], []),
    "pptx": ("kdd-dab", ["formats/06_kdd_dab_decisions.pptx"], ["Integration Suite", "Rotterdam"], []),
    "pdf": ("readiness-audit", ["formats/09_readiness_audit_pack.pdf"], ["rollback", "UAT"], []),
    "multi": ("agile-stories", ["01_mom_meeting_transcript.txt", "02_agile_stories_requirements.txt"],
              ["5 minutes", "15 minutes", "re-post"], []),
}
CHAIN = ["mom", "agile-stories", "test"]


def upload(files: list[str]) -> str:
    handles = [open(INPUTS / f, "rb") for f in files]
    try:
        res = requests.post(f"{API}/ingestion/upload",
                            files=[("files", (Path(f).name, h)) for f, h in zip(files, handles)], timeout=300)
    finally:
        for h in handles:
            h.close()
    res.raise_for_status()
    return res.json()["workflow_id"]


def run_agent(agent: str, workflow_id: str) -> dict:
    started = requests.post(f"{API}/agents/{agent}/runs", json={"workflow_id": workflow_id}, timeout=60)
    started.raise_for_status()
    run_id = started.json()["id"]
    deadline = time.time() + 900
    while time.time() < deadline:
        run = requests.get(f"{API}/agents/runs/{run_id}", timeout=30).json()
        if run["status"] in ("done", "failed"):
            return run
        time.sleep(2)
    return {"status": "failed", "error": "timed out"}


def run_case(case: str) -> bool:
    agent, files, must, must_not = CASES[case]
    try:
        workflow_id = upload(files)
    except requests.RequestException as e:
        print(f"FAIL   {case:18} upload: {e}")
        return False

    rec = requests.post(f"{API}/savia/recommend", json={"workflow_id": workflow_id}, timeout=120)
    picks = [a["agent"] for a in rec.json().get("recommended_agents", []) if a.get("matched")][:3] if rec.ok else []

    started = time.time()
    run = run_agent(agent, workflow_id)
    seconds = time.time() - started
    if run["status"] != "done":
        print(f"FAIL   {case:18} agent run failed: {run.get('error')}")
        return False

    content = run["result"]["content"]
    quality = run["result"].get("quality", {})
    (OUT / f"{case}.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    text = json.dumps(content, ensure_ascii=False).lower()
    missing = [w for w in must if w.lower() not in text]
    invented = [w for w in must_not if w.lower() in text]
    unsupported = quality.get("unsupported_figures", [])
    ok = not missing and not invented and not unsupported

    rec_note = "top pick" if picks[:1] == [agent] else ("in top 3" if agent in picks else "NOT recommended")
    usage = run.get("usage", {})
    print(f"{'PASS' if ok else 'CHECK':6} {case:18} {seconds:4.0f}s  {usage.get('prompt_tokens', 0)}+"
          f"{usage.get('completion_tokens', 0)} tokens  recommender: {rec_note} {picks}")
    if missing:
        print(f"         missing from output:  {missing}")
    if invented:
        print(f"         should not appear:    {invented}")
    if unsupported:
        print(f"         figures not in input: {unsupported}")
    if quality.get("dangling_references"):
        print(f"         unknown references:   {quality['dangling_references']}")
    return ok


def run_chain() -> bool:
    workflow_id = upload(["01_mom_meeting_transcript.txt", "02_agile_stories_requirements.txt"])
    previous = None
    for agent in CHAIN:
        run = run_agent(agent, workflow_id)
        if run["status"] != "done":
            print(f"FAIL   chain              {agent} failed: {run.get('error')}")
            return False
        result = run["result"]
        expected = [previous] if previous else []
        if result["upstream_used"] != expected:
            print(f"CHECK  chain              {agent} used {result['upstream_used']}, expected {expected}")
            return False
        requests.post(f"{API}/workflows/{workflow_id}/approve",
                      json={"artifact_id": result["artifact_id"], "user_id": "eval"}, timeout=30).raise_for_status()
        previous = result["artifact_id"]
    print(f"PASS   chain              {' -> '.join(CHAIN)}, each on the approved output before it")
    return True


def main() -> None:
    cases = sys.argv[1:] or [*CASES, "chain"]
    unknown = [c for c in cases if c not in CASES and c != "chain"]
    if unknown:
        sys.exit(f"Unknown case(s) {unknown}. Choose from: {', '.join(CASES)}, chain")
    try:
        requests.get(f"{API.rsplit('/api', 1)[0]}/health", timeout=5).raise_for_status()
    except requests.RequestException:
        sys.exit("Backend is not running on http://localhost:8000.")
    OUT.mkdir(exist_ok=True)
    passed = sum(run_chain() if c == "chain" else run_case(c) for c in cases)
    print(f"\n{passed}/{len(cases)} passed. Outputs are in {OUT.relative_to(HERE.parent)}/; read them against README.md.")
    sys.exit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
