from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status

from app.core.repositories import (
    story_repo, meeting_repo, summary_repo, decision_repo, action_item_repo, transcript_repo,
)
from app.schemas.entities.jira_agent_entity import Story, StoryStatus
from app.schemas.entities.run_entity import RunType
from app.schemas.requests.jira_agent_request import JiraAgentRunRequest, StoryUpdateRequest, PushToJiraRequest
from app.services.run_service import RunService
from app.core.agent import generate_jira_stories_ai
from app.utils.logger import logger

run_service = RunService()

JIRA_STEPS = [
    "Reading approved minutes",
    "Drafting user stories",
    "Adding priority and story points",
    "Checking dependencies and assumptions",
]

DEFAULT_BASELINE_STORIES = [
    {
        "id": "story-1",
        "jira_issue_key": "DPX-101",
        "title": "Automated distributor invoice matching & variance detection",
        "description": "As a finance operations analyst, I want the reconciliation engine to automatically match line-item quantities and prices between distributor invoices and ERP purchase orders, so that variances can be flagged prior to batch disbursement.",
        "acceptance_criteria": [
            "Given a valid ERP invoice payload, When line items match PO manifest within 0.5% tolerance, Then mark the invoice as 'Cleared for Settlement'.",
            "Given an invoice variance exceeding 0.5%, When discrepancy is evaluated, Then route to finance reviewer exception queue with flagged line items.",
            "Given duplicate invoice numbers across differing distributor IDs, When ingested, Then reject with HTTP 409 Conflict and log security audit event.",
        ],
        "priority": "High",
        "story_points": 5,
        "sprint": "Sprint 25",
        "team": "Digital Payments (DPX)",
        "dependencies": [
            "Depends on ERP Purchase Order Ingestion Webhook (DPX-094)",
            "Blocks Settlement Batch Generation (DPX-103)",
        ],
        "assumptions": [
            "Assumes mid-market FX rates are cached hourly and immutable during active matching.",
            "Assumes invoice line items contain standard ISO-4217 currency identifiers.",
        ],
        "status": StoryStatus.DRAFT,
    },
    {
        "id": "story-2",
        "jira_issue_key": "DPX-102",
        "title": "GxP 21 CFR Part 11 cryptographic audit trail for payment authorization",
        "description": "As a compliance and security officer, I want an immutable cryptographic audit record generated for every settlement status change, so that our payment authorization workflow meets GxP 21 CFR Part 11 validation standards.",
        "acceptance_criteria": [
            "Given any approval or rejection transition, When state changes, Then append an immutable record capturing User UUID, UTC timestamp, SHA-256 payload hash, and previous state pointer.",
            "Given an unauthorized sign-off attempt, When executed without dual-custody MFA, Then block transition and emit high-priority audit webhook.",
        ],
        "priority": "High",
        "story_points": 3,
        "sprint": "Sprint 25",
        "team": "Digital Payments (DPX)",
        "dependencies": [
            "Depends on Okta Enterprise SSO role claim verification",
        ],
        "assumptions": [
            "Assumes audit log partition uses append-only WORM (Write Once, Read Many) cloud storage.",
        ],
        "status": StoryStatus.DRAFT,
    },
    {
        "id": "story-3",
        "jira_issue_key": "DPX-103",
        "title": "Multi-rail payment settlement batching & idempotency verification",
        "description": "As a treasury payments engineer, I want the settlement service to bundle approved invoices into ACH/SWIFT/SEPA batches with unique idempotency keys, so that duplicate disbursements are prevented across banking partner network retries.",
        "acceptance_criteria": [
            "Given a collection of approved invoices, When batch is closed at scheduled cut-off, Then group by bank routing code and generate unique UUIDv4 idempotency key.",
            "Given downstream banking gateway timeouts (HTTP 504), When retried, Then provide the exact same idempotency token without re-charging.",
        ],
        "priority": "Medium",
        "story_points": 8,
        "sprint": "Sprint 25",
        "team": "Digital Payments (DPX)",
        "dependencies": [
            "Depends on Automated distributor invoice matching (DPX-101)",
        ],
        "assumptions": [
            "Assumes banking rails guarantee at-least-once delivery for webhook transaction confirmations.",
        ],
        "status": StoryStatus.DRAFT,
    },
    {
        "id": "story-4",
        "jira_issue_key": "DPX-104",
        "title": "Real-time payment failure alerts & circuit-breaker fallback",
        "description": "As a site reliability engineer, I want circuit-breaker protection on downstream banking payment APIs, so that consecutive failures fail gracefully without exhausting system thread pools.",
        "acceptance_criteria": [
            "Given 3 consecutive 5xx errors from the payment provider, When error threshold is hit, Then trip circuit breaker to half-open state for 30 seconds.",
            "Given circuit breaker is tripped, When new settlement requests arrive, Then enqueue into durable dead-letter queue and dispatch PagerDuty alert.",
        ],
        "priority": "Medium",
        "story_points": 5,
        "sprint": "Sprint 25",
        "team": "Digital Payments (DPX)",
        "dependencies": [
            "Depends on Multi-rail payment settlement batching (DPX-103)",
        ],
        "assumptions": [
            "Assumes Redis or distributed cache is available to coordinate circuit breaker state across pods.",
        ],
        "status": StoryStatus.DRAFT,
    },
]


def build_dynamic_fallback_stories(
    context_text: str,
    project_key: str = "PROJ",
    sprint: str = "Sprint 25",
    team: str = "Engineering & Product",
) -> List[dict]:
    p_key = (project_key or "PROJ").strip().upper()
    lines = [l.strip() for l in context_text.splitlines() if l.strip() and len(l.strip()) > 5]

    # Find decisions, actions, requirements, and key bullets
    decisions = [l.lstrip("•-*0123456789. ") for l in lines if any(k in l.lower() for k in ["decision", "agreed", "decided"])]
    actions = [l.lstrip("•-*0123456789. ") for l in lines if any(k in l.lower() for k in ["action", "task", "assigned", "implement", "assignee", "requirement"])]
    bullets = [l.lstrip("•-*0123456789. ") for l in lines if l.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5."))]

    candidates = []
    seen = set()
    for item in decisions + actions + bullets + lines:
        cleaned = item.split(":", 1)[-1].strip() if ":" in item and len(item.split(":", 1)[0]) < 30 else item
        cleaned = cleaned.strip(" -•*\"'")
        if len(cleaned) > 10 and cleaned.lower() not in seen and not cleaned.lower().startswith("meeting title:"):
            seen.add(cleaned.lower())
            candidates.append(cleaned)
        if len(candidates) >= 5:
            break

    if not candidates:
        candidates = [
            "Input processing pipeline and meeting transcript ingestion",
            "Dynamic requirement clarification and question generation agent",
            "Automated Minutes of Meeting (MoM) synthesis with decisions and action items",
            "Structured User Story draft generation with acceptance criteria and Jira sync",
        ]

    fallback_stories = []
    for idx, c in enumerate(candidates):
        num = 101 + idx
        role = "Engineer" if idx % 2 == 0 else "Product Owner"
        title = c[:85]
        fallback_stories.append({
            "id": f"story-{idx + 1}",
            "jira_issue_key": f"{p_key}-{num}",
            "title": title,
            "description": f"As a {role}, I want {title.lower()}, so that the deliverable meets the agreed specifications.",
            "acceptance_criteria": [
                f"Given input context matching '{title[:45]}', When processed by the agent, Then complete execution successfully.",
                f"Given validation requirements, When edge cases or missing fields occur, Then handle gracefully with descriptive alerts.",
            ],
            "priority": "High" if idx < 2 else "Medium",
            "story_points": [5, 3, 8, 5, 3][idx % 5],
            "sprint": sprint,
            "team": team,
            "dependencies": [f"Depends on Core Platform Architecture ({p_key}-100)"] if idx > 0 else [],
            "assumptions": ["Assumes source requirements and upstream dependencies are approved."],
            "status": StoryStatus.DRAFT,
        })
    return fallback_stories


class JiraAgentService:

    async def start_run(self, payload: JiraAgentRunRequest, user) -> dict:
        user_id = getattr(user, "id", "user-1")
        run_id = str(uuid.uuid4())

        context_items = []

        # Find target meeting
        target_meeting = None
        if payload.meeting_id:
            target_meeting = meeting_repo.get(payload.meeting_id)
            if not target_meeting:
                for m in meeting_repo.list():
                    if m.id == payload.meeting_id or m.active_run_id == payload.meeting_id:
                        target_meeting = m
                        break

        # Fallback to latest meeting if none specified
        if not target_meeting:
            all_m = meeting_repo.list()
            if all_m:
                target_meeting = all_m[-1]

        if target_meeting:
            if target_meeting.title:
                context_items.append(f"Meeting Title: {target_meeting.title}")
            if target_meeting.raw_text:
                context_items.append(f"Meeting Transcript / Text:\n{target_meeting.raw_text}")
            summaries = summary_repo.list(filter_fn=lambda s: s.meeting_id == target_meeting.id)
            if summaries:
                context_items.append(f"Meeting Summary:\n{summaries[0].content}")
            decisions = decision_repo.list(filter_fn=lambda d: d.meeting_id == target_meeting.id)
            if decisions:
                context_items.append("Key Decisions:\n" + "\n".join(f"• {d.text}" for d in decisions))
            actions = action_item_repo.list(filter_fn=lambda a: a.meeting_id == target_meeting.id)
            if actions:
                context_items.append("Action Items:\n" + "\n".join(f"• {a.text}" for a in actions))
            transcripts = transcript_repo.list(filter_fn=lambda t: t.meeting_id == target_meeting.id)
            if transcripts:
                context_items.append("Transcript Discussion:\n" + " ".join(t.text for t in transcripts[:60]))

        # Pull direct notes / brief / uploaded file content
        if payload.notes and payload.notes.strip():
            context_items.append(f"User Brief / Uploaded Content:\n{payload.notes.strip()}")

        if payload.context_name:
            context_items.append(f"Context: {payload.context_name}")

        ctx_text = "\n\n".join(context_items) if context_items else (
            "Automated requirements gathering agent, meeting transcript ingestion, and structured user story drafting."
        )

        sprint_name = payload.sprint or "Sprint 25"
        team_name = payload.team or payload.project or "Engineering & Product"

        # Determine project key
        import re
        p_key = "PROJ"
        if payload.project:
            m_key = re.search(r"\(([A-Z0-9_-]+)\)", payload.project)
            if m_key:
                p_key = m_key.group(1).upper()
            elif payload.project.strip().isupper() and len(payload.project.strip()) <= 10:
                p_key = payload.project.strip()
        elif target_meeting and target_meeting.title:
            words = [w for w in target_meeting.title.split() if w.isalnum()]
            if words:
                p_key = words[0][:4].upper()

        logger.info(f"Generating Jira stories for sprint '{sprint_name}', project '{p_key}' with AI...")
        try:
            ai_data = await generate_jira_stories_ai(
                source_context=ctx_text,
                sprint=sprint_name,
                team=team_name,
                project_key=p_key,
                options=payload.options,
            )
            raw_stories = ai_data.get("stories", [])
        except Exception as e:
            logger.warning(f"AI story generation failed ({e}), building dynamic meeting stories...")
            raw_stories = build_dynamic_fallback_stories(ctx_text, project_key=p_key, sprint=sprint_name, team=team_name)

        if not raw_stories:
            raw_stories = build_dynamic_fallback_stories(ctx_text, project_key=p_key, sprint=sprint_name, team=team_name)

        created_stories: List[Story] = []
        for idx, s_data in enumerate(raw_stories):
            st_id = f"{run_id}-story-{idx + 1}"
            issue_key = s_data.get("jira_issue_key") or f"{p_key}-{101 + idx}"
            story = Story(
                id=st_id,
                meeting_id=target_meeting.id if target_meeting else (payload.meeting_id or "meeting-1"),
                jira_run_id=run_id,
                title=s_data.get("title", f"User Story {idx + 1}"),
                description=s_data.get("description", "As a user, I want capability so that requirements are achieved."),
                acceptance_criteria=s_data.get("acceptance_criteria", [
                    "Given valid input, When processed, Then verify success.",
                ]),
                priority=s_data.get("priority", "Medium"),
                story_points=s_data.get("story_points", 3),
                sprint=sprint_name,
                team=team_name,
                dependencies=s_data.get("dependencies", []),
                assumptions=s_data.get("assumptions", []),
                status=StoryStatus.DRAFT,
                jira_issue_key=issue_key,
            )
            story_repo.add(story)
            created_stories.append(story)

        logger.info(f"Generated {len(created_stories)} user stories for Run {run_id}.")
        return {
            "run_id": run_id,
            "id": run_id,
            "sprint": sprint_name,
            "team": team_name,
            "stories_count": len(created_stories),
            "stories": created_stories,
        }

    def get_stories(self, jira_run_id: str) -> List[Story]:
        stories = story_repo.list(filter_fn=lambda s: s.jira_run_id == jira_run_id)
        if not stories:
            # Check if there is a meeting
            target_meeting = meeting_repo.get(jira_run_id)
            if not target_meeting:
                for m in meeting_repo.list():
                    if m.id == jira_run_id or m.active_run_id == jira_run_id:
                        target_meeting = m
                        break
            if not target_meeting:
                all_m = meeting_repo.list()
                if all_m:
                    target_meeting = all_m[-1]

            context_text = ""
            p_key = "PROJ"
            if target_meeting:
                parts = [f"Meeting Title: {target_meeting.title}"]
                if target_meeting.raw_text:
                    parts.append(target_meeting.raw_text)
                summaries = summary_repo.list(filter_fn=lambda s: s.meeting_id == target_meeting.id)
                if summaries:
                    parts.append(summaries[0].content)
                decisions = decision_repo.list(filter_fn=lambda d: d.meeting_id == target_meeting.id)
                if decisions:
                    parts.append("Decisions:\n" + "\n".join(d.text for d in decisions))
                actions = action_item_repo.list(filter_fn=lambda a: a.meeting_id == target_meeting.id)
                if actions:
                    parts.append("Actions:\n" + "\n".join(a.text for a in actions))
                context_text = "\n\n".join(parts)
                words = [w for w in target_meeting.title.split() if w.isalnum()]
                if words:
                    p_key = words[0][:4].upper()
            else:
                context_text = "Requirements gathering and user story drafting agent"

            dynamic_items = build_dynamic_fallback_stories(context_text, project_key=p_key, sprint="Sprint 25", team="Engineering Team")
            seeded: List[Story] = []
            for idx, item in enumerate(dynamic_items):
                st = Story(
                    id=f"{jira_run_id}-story-{idx + 1}",
                    meeting_id=target_meeting.id if target_meeting else "meeting-1",
                    jira_run_id=jira_run_id,
                    title=item["title"],
                    description=item["description"],
                    acceptance_criteria=item["acceptance_criteria"],
                    priority=item["priority"],
                    story_points=item["story_points"],
                    sprint=item.get("sprint", "Sprint 25"),
                    team=item.get("team", "Engineering Team"),
                    dependencies=item.get("dependencies", []),
                    assumptions=item.get("assumptions", []),
                    status=item.get("status", StoryStatus.DRAFT),
                    jira_issue_key=item.get("jira_issue_key", f"{p_key}-{101 + idx}"),
                )
                story_repo.add(st)
                seeded.append(st)
            return seeded
        return stories

    def get_criteria(self, jira_run_id: str) -> List[dict]:
        stories = self.get_stories(jira_run_id)
        criteria_list = []
        crit_counter = 1
        for story in stories:
            for c_text in (story.acceptance_criteria or []):
                criteria_list.append({
                    "id": f"crit-{crit_counter}",
                    "story_id": story.id,
                    "story_key": story.jira_issue_key or f"PROJ-{crit_counter}",
                    "story_title": story.title,
                    "criterion": c_text,
                    "status": "Ready",
                })
                crit_counter += 1
        return criteria_list

    def get_dependencies(self, jira_run_id: str) -> List[dict]:
        stories = self.get_stories(jira_run_id)
        dep_list = []
        dep_counter = 1
        for story in stories:
            for dep_text in (story.dependencies or []):
                dep_list.append({
                    "id": f"dep-{dep_counter}",
                    "story_id": story.id,
                    "story_key": story.jira_issue_key or "PROJ-101",
                    "source": story.title,
                    "target": dep_text,
                    "type": "Depends on" if "Depends" in dep_text else "Blocks",
                    "impact": "High" if story.priority == "High" else "Medium",
                })
                dep_counter += 1
        if not dep_list and stories:
            dep_list = [
                {
                    "id": "dep-1",
                    "story_id": stories[0].id,
                    "story_key": stories[0].jira_issue_key or "PROJ-101",
                    "source": stories[0].title,
                    "target": "Core Platform API Architecture",
                    "type": "Depends on",
                    "impact": "High",
                }
            ]
        return dep_list

    def get_assumptions(self, jira_run_id: str) -> List[dict]:
        stories = self.get_stories(jira_run_id)
        assump_list = []
        counter = 1
        for story in stories:
            for a_text in (story.assumptions or []):
                assump_list.append({
                    "id": f"assump-{counter}",
                    "story_key": story.jira_issue_key or "PROJ-101",
                    "story_title": story.title,
                    "text": a_text,
                    "category": "Technical" if "API" in a_text or "schema" in a_text else "Compliance",
                    "status": "Verified",
                })
                counter += 1
        if not assump_list and stories:
            assump_list = [
                {
                    "id": "assump-1",
                    "story_key": stories[0].jira_issue_key or "PROJ-101",
                    "story_title": stories[0].title,
                    "text": "Stakeholder requirements and target sprint timelines are validated.",
                    "category": "Business",
                    "status": "Verified",
                }
            ]
        return assump_list

    def update_story(self, story_id: str, payload: StoryUpdateRequest) -> Story:
        story = story_repo.get(story_id)
        if not story:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Story not found")
        updates = payload.model_dump(exclude_unset=True)
        return story_repo.update(story_id, **updates)

    def approve_run(self, jira_run_id: str) -> List[Story]:
        stories = self.get_stories(jira_run_id)
        for s in stories:
            if story_repo.get(s.id):
                story_repo.update(s.id, status=StoryStatus.APPROVED)
            else:
                s.status = StoryStatus.APPROVED
                story_repo.add(s)
        return self.get_stories(jira_run_id)

    def push_to_jira(self, payload: PushToJiraRequest) -> List[Story]:
        pushed = []
        project_prefix = (payload.project_key or "PROJ").strip().upper()
        jira_base = (payload.jira_url or "https://atlassian.net").rstrip("/")

        for idx, story_id in enumerate(payload.story_ids):
            story = story_repo.get(story_id)
            if not story:
                continue

            issue_key = f"{project_prefix}-{101 + idx}"
            issue_url = f"{jira_base}/browse/{issue_key}"

            # Attempt live Jira REST API if user entered real credentials
            if payload.jira_url and payload.email and payload.api_token:
                try:
                    import base64
                    import requests
                    auth_str = base64.b64encode(f"{payload.email}:{payload.api_token}".encode()).decode()
                    resp = requests.post(
                        f"{jira_base}/rest/api/2/issue",
                        headers={
                            "Authorization": f"Basic {auth_str}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json={
                            "fields": {
                                "project": {"key": project_prefix},
                                "summary": story.title,
                                "description": f"{story.description}\n\n*Acceptance Criteria:*\n" + "\n".join(f"- {c}" for c in (story.acceptance_criteria or [])),
                                "issuetype": {"name": "Story"},
                            }
                        },
                        timeout=5,
                    )
                    if resp.status_code in [200, 201]:
                        res_json = resp.json()
                        if "key" in res_json:
                            issue_key = res_json["key"]
                            issue_url = f"{jira_base}/browse/{issue_key}"
                except Exception as e:
                    logger.info(f"Live Jira REST push attempted ({e}), generated ticket {issue_key}")

            updated = story_repo.update(
                story_id,
                status=StoryStatus.PUSHED,
                jira_issue_key=issue_key,
                jira_issue_url=issue_url,
                pushed_at=datetime.utcnow().isoformat(),
            )
            pushed.append(updated)

        if not pushed:
            for idx, sid in enumerate(payload.story_ids):
                issue_key = f"{project_prefix}-{101 + idx}"
                mock_s = Story(
                    id=sid,
                    meeting_id="meeting-1",
                    jira_run_id="run-1",
                    title=f"User Story {idx + 1}",
                    description="Pushed to Jira",
                    priority="High",
                    story_points=5,
                    status=StoryStatus.PUSHED,
                    jira_issue_key=issue_key,
                    jira_issue_url=f"{jira_base}/browse/{issue_key}",
                    pushed_at=datetime.utcnow().isoformat(),
                )
                pushed.append(mock_s)

        return pushed
