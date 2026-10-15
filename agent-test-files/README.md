# Agent test files

Sample inputs for testing every SAVIA agent by hand and checking its output.

All files describe one fictional project: **Northwind Pharma** moving its stock sync between
SAP S/4HANA and the Manhattan WMS from a nightly file to real-time events, piloted at Rotterdam.
Each file has facts planted in it (to check the agent uses them) and leaves things out on
purpose (to check the agent does not make them up).

## Two ways to test

**In the app (manual).** Start the backend and frontend, open http://localhost:5173/work,
upload the file from the table below, click *Find my agents*, check the recommendation, run the
agent, then check the output on the Writing and Document screens against the checklist.

**With the script (quick).** With the backend running, from the repo root:

```bash
backend/.venv-mac/bin/python agent-test-files/run_all.py            # every case
backend/.venv-mac/bin/python agent-test-files/run_all.py mom test   # some cases
```

It uploads each file, asks the recommender, runs the agent, saves the output to
`outputs/<case>.json` and does a quick keyword check. A `PASS` means the planted facts are
present; it does **not** prove nothing was invented, so still read the outputs against the
checklist. Outputs are not committed.

## Checklist per agent

| # | Agent | Upload | The output must have | It must NOT have (invented) |
|---|---|---|---|---|
| 1 | MOM | `inputs/01_mom_meeting_transcript.txt` | 4 attendees with roles (Priya, Tom, Ken, Aisha). 2 decisions: event-based sync; Rotterdam-only pilot. 3 actions: Tom, event schema, 14 November; Ken, SAP interface, 10 November; Aisha, UAT plan. 1 open question: who owns the reconciliation report | A due date on Aisha's action (she gave none). Any budget figure. People or teams who were not in the meeting |
| 2 | Agile Stories | `inputs/02_agile_stories_requirements.txt` | One story per requirement REQ-01 to REQ-05. Given/When/Then criteria using the stated numbers: **5 minutes**, **15 minutes**. Users: planner, integration support, QA auditor | Stories for other sites or SAP core changes (out of scope) |
| 3 | Solution Analyzer | `inputs/03_solution_analyzer_problem_statement.txt` | Problem and constraints taken from the input (GxP, no SAP core change, SFTP today). A proposed approach with components and a roadmap. `needs_info` asking for volumes, budget and go-live date | Any cost, saving or ROI figure (no currency amounts). Volumes or dates |
| 4 | Gap Analysis & RTM | `inputs/04_gap_analysis_requirements_vs_current.txt` | **Gaps: REQ-01** (no intra-day updates) and **REQ-03** (no alerting). REQ-02, REQ-04 and REQ-05 are already met by SAP | REQ-02/04/05 reported as gaps. Watch `budget_impact_effort` and `timeline_impact_weeks`: the input has no effort data |
| 5 | DDL3 | `inputs/05_ddl3_design_input.txt` | Interface using `BAPI_GOODSMVT_CREATE`. The 8 event fields as listed. Validation: quantity > 0, plant NL01 only, ignore duplicate `movement_id`. Retry policy listed as an **open question** | A specific retry count or interval. Endpoints or fields not in the input |
| 6 | KDD for DAB | `inputs/06_kdd_dab_architecture_design.txt` | 4 decisions. Rejected alternatives: hourly batch, DB replication, with the reasons given. Principles: standard interfaces, clean core, GxP. Validation needed before go-live | **RTO/RPO values**: the input says they are not agreed. Watch `disaster_recovery_rto_rpo` |
| 7 | Change Impact | `inputs/07_change_impact_change_request.txt` | Impacted: SAP, WMS, finance reconciliation report, Power BI dashboard. Dependencies: WMS event publisher before integration testing; re-point the finance report before the file is switched off. 2-week parallel run | Readiness percentages or cutover/rollback details the input does not give |
| 8 | TEST | `inputs/08_test_user_stories.txt` | Test cases traced to US-01, US-02, US-03, using the given data (M-1001, 10 units, MV-500). The quantity-0 rejection and duplicate cases. **Coverage 100%** (computed: every story has a test) | Test data not in the stories |
| 9 | Readiness & Audit | `inputs/09_readiness_audit_deliverable.txt` | Deficits: UAT not started, no performance testing, GxP validation report unsigned, **no rollback plan**, 2 open defects, planners untrained. A score that reflects these (not "ready") | A high readiness score or "go-live ready" |

## Answering open questions on the Document screen

Each file leaves something out on purpose, so SAVIA should list it under **Open Questions** at the
bottom of the Document screen. Type the answer below into that question's box and click
*Answer & Update Document*. The LLM words the question differently on each run; match it by topic.

What should happen:
- Only the card you clicked shows **Updating...**. The other buttons are disabled until the update finishes.
- The agent runs again with your answer. The card turns green and shows your answer as its **Resolution**.
- The answer now appears in the document itself, and the question is not asked again. If you
  answer a second question, the first answer is sent again too, so it is kept.

| File | SAVIA should ask about | Type this answer | Then check the document |
|---|---|---|---|
| `01_mom_meeting_transcript.txt` | Who owns the reconciliation report | `Marta Jansen from Finance owns the reconciliation report.` | Summary and Decisions name Marta Jansen |
| `03_solution_analyzer_problem_statement.txt` | Volumes, budget or go-live date | `About 40,000 stock movements a day at Rotterdam.` | Constraints, risks or roadmap use 40,000 |
| `05_ddl3_design_input.txt` | The retry policy | `Retry 3 times, 5 minutes apart, then alert integration support.` | The design describes 3 retries, 5 minutes apart |
| `06_kdd_dab_architecture_design.txt` | RTO / RPO | `RTO is 4 hours and RPO is 15 minutes.` | The DR / compliance section shows 4 hours and 15 minutes |
| `07_change_impact_change_request.txt` | Cutover date or rollback | `Cutover is planned for 15 March 2027.` | Dependencies or readiness mention 15 March 2027 |
| `08_test_user_stories.txt` | Limits or missing preconditions | `The maximum quantity per movement is 99,999 units.` | A boundary test case uses 99,999 |
| `09_readiness_audit_deliverable.txt` | The rollback plan | `Rollback plan RB-01 re-enables the nightly SFTP batch within 2 hours; signed off by Ken Morita.` | "No rollback plan" is gone from the gaps; the score may go up |

If the update fails, the status message says so and your answer stays in the box. The document does
not pretend it was updated.

## Other formats and multiple files

| Case | Upload | Checks |
|---|---|---|
| Word | `inputs/formats/02_agile_stories_requirements.docx` | Requirements are in a **table**; the stories must still cover REQ-01 to REQ-05 |
| PowerPoint | `inputs/formats/06_kdd_dab_decisions.pptx` | Decisions in a slide table, the RTO/RPO note in the **speaker notes**; KDD output should reflect both |
| PDF | `inputs/formats/09_readiness_audit_pack.pdf` | Same checks as row 9 |
| Several files | `01_mom_meeting_transcript.txt` + `02_agile_stories_requirements.txt` together | Reading shows both files; the stories cover all 5 requirements |

## Also worth trying in the app

- **Empty input:** the agent should refuse with a clear message, not produce a sample document.
- **Recommendation:** for each file, the matching agent should be the top pick
  (`run_all.py` prints the recommender's top 3).
- **Change → Suggestions → Decide:** on the MOM output, ask Savia to "add the meeting date to the
  summary". It should use 3 November 2026 from the transcript, not ask for it.
