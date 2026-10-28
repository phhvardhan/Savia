RUBRIC_CONFIGS = {
    "Enterprise SDLC Standard (ISO/IEC 25010 & GxP)": {
        "benchmark": "Enterprise SDLC Quality Benchmark combining ISO/IEC 25010 Software Quality and GxP 21 CFR Part 11 Regulatory Compliance.",
        "default_dimensions": [
            {"id": "dim-1", "name": "Completeness & Scope", "weight": 25, "desc": "Explicit boundary demarcations, preconditions, postconditions, and edge exception handling."},
            {"id": "dim-2", "name": "Clarity & Precision", "weight": 20, "desc": "Unambiguous requirement statements, objective terminology without subjective adjectives (e.g. 'fast', 'friendly')."},
            {"id": "dim-3", "name": "GxP / Regulatory Audit", "weight": 20, "desc": "Immutable audit trails, 21 CFR Part 11 electronic signature validation, data integrity (ALCOA+), encryption at rest/transit."},
            {"id": "dim-4", "name": "Testability & Boundaries", "weight": 20, "desc": "Quantified, verifiable acceptance criteria, explicit latency percentiles (p95/p99) and load concurrency limits."},
            {"id": "dim-5", "name": "Cross-Artifact Consistency", "weight": 15, "desc": "Unified entity naming, schema alignment with Jira user stories, and architectural diagram nomenclature."},
        ],
        "default_criteria": [
            ("Completeness & Scope", "Unambiguous scope definitions and boundary conditions"),
            ("Testability & Boundaries", "Quantified performance latency SLAs (p95/p99 defined)"),
            ("GxP / Regulatory Audit", "Audit logging for authorization state transitions (21 CFR Part 11)"),
            ("Clarity & Precision", "Absence of untestable or subjective adjectives"),
            ("Cross-Artifact Consistency", "Traceability to downstream Jira stories and component contracts"),
        ],
    },
    "ISO/IEC 25010 Software Quality Standard": {
        "benchmark": "International standard ISO/IEC 25010 Software and Data Quality model evaluating system characteristics.",
        "default_dimensions": [
            {"id": "dim-1", "name": "Functional Suitability & Completeness", "weight": 25, "desc": "Degree to which specified functions meet stated and implied needs when used under specified conditions."},
            {"id": "dim-2", "name": "Performance Efficiency & Latency", "weight": 20, "desc": "Quantified throughput (RPS), response latency percentiles (p99), and resource capacity constraints."},
            {"id": "dim-3", "name": "Compatibility & Interface Standards", "weight": 15, "desc": "Interoperability, schema standard compliance, API versioning, and co-existence with existing enterprise services."},
            {"id": "dim-4", "name": "Reliability & Fault Tolerance", "weight": 20, "desc": "System availability SLAs (99.9x%), circuit breakers, graceful degradation, and disaster recovery RTO/RPO limits."},
            {"id": "dim-5", "name": "Maintainability & Modularity", "weight": 20, "desc": "Architectural modularity, separation of concerns, testability, and clear modification boundaries."},
        ],
        "default_criteria": [
            ("Functional Suitability", "Specification of complete functional journeys with preconditions and postconditions"),
            ("Performance Efficiency", "Quantified latency percentiles (p95/p99) under specified concurrency loads"),
            ("Compatibility", "Standard REST/gRPC/OAuth contract specifications with versioning guidelines"),
            ("Reliability", "Fault tolerance, circuit breaker fallback protocols, and recovery SLAs"),
            ("Maintainability", "Modular domain boundaries and decoupling between submodules"),
        ],
    },
    "GxP Audit & Regulatory Compliance Benchmark": {
        "benchmark": "Strict Life Sciences Pharmaceutical & Medical Device compliance (FDA 21 CFR Part 11, EU Annex 11, GAMP 5, ALCOA+ data integrity).",
        "default_dimensions": [
            {"id": "dim-1", "name": "21 CFR Part 11 Audit Trail Integrity", "weight": 25, "desc": "Computer-generated, time-stamped, immutable audit trails capturing operator ID, action timestamp, and prior values."},
            {"id": "dim-2", "name": "Electronic Signatures & Dual Custody", "weight": 20, "desc": "Multi-party sign-off workflows, cryptographic binding, non-repudiation, and explicit meaning-of-signature captures."},
            {"id": "dim-3", "name": "Data Integrity & ALCOA+ Principles", "weight": 20, "desc": "Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, and Enduring data governance."},
            {"id": "dim-4", "name": "Security & Segregation of Duties", "weight": 20, "desc": "Strict role-based access control (RBAC), least privilege principle, MFA, and administrative role segregation."},
            {"id": "dim-5", "name": "Validation Traceability Matrix (VTM)", "weight": 15, "desc": "Bi-directional traceability between user requirements (URS), functional specs (FS), and IQ/OQ/PQ validation test scripts."},
        ],
        "default_criteria": [
            ("Audit Trail Integrity", "Immutable audit trail specifications with timestamp, user ID, and reason for change"),
            ("Electronic Signatures", "Dual-custody approval workflows with cryptographic signature binding"),
            ("Data Integrity", "Adherence to ALCOA+ standards across data generation, transmission, and archival"),
            ("Security & Access", "Strict role segregation preventing operational operators from altering audit records"),
            ("Validation Traceability", "Traceability mapping from user requirements to validation test protocols"),
        ],
    },
    "Agile Lean Spec & Acceptance Criteria Benchmark": {
        "benchmark": "Agile Product Management benchmark based on INVEST criteria, Given-When-Then BDD scenarios, and Lean MVP boundary scoping.",
        "default_dimensions": [
            {"id": "dim-1", "name": "INVEST User Story Compliance", "weight": 25, "desc": "Independent, Negotiable, Valuable, Estimable, Small, and Testable user story decomposition."},
            {"id": "dim-2", "name": "Given-When-Then Acceptance Criteria", "weight": 25, "desc": "Concrete, automated-test-ready Given/When/Then scenario definitions covering happy path and edge conditions."},
            {"id": "dim-3", "name": "Lean Scope & MVP Demarcation", "weight": 20, "desc": "Rigorous separation of Must-Have MVP scope from out-of-scope backlog items to prevent sprint bloat."},
            {"id": "dim-4", "name": "Cross-Story Dependency Mapping", "weight": 15, "desc": "Explicit prerequisite tracking, architectural blocking dependencies, and external team handoffs."},
            {"id": "dim-5", "name": "Estimation Feasibility & Testability", "weight": 15, "desc": "Clarity of technical assumptions enabling accurate engineering sizing and deterministic QA verification."},
        ],
        "default_criteria": [
            ("INVEST Compliance", "User stories deliver standalone stakeholder value and are appropriately sized"),
            ("Acceptance Criteria", "Given/When/Then BDD acceptance scenarios defined for every requirement"),
            ("Lean MVP Demarcation", "Explicit demarcation between current sprint MVP and future backlog phases"),
            ("Dependency Mapping", "Upstream API dependencies and blocking integration prerequisites documented"),
            ("Testability", "Objective verification criteria without ambiguous or subjective quality assertions"),
        ],
    },
}
