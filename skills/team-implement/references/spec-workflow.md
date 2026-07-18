# Specification Workflow Reference

This document provides detailed technical specifications for the `team-implement` skill's workflow engine, including input detection, complexity assessment, phase transitions, and quality gates.

**Read this as pseudocode, not literal code.** The Python classes/functions below describe the *conceptual* rules an orchestrating agent follows — there is no actual Python engine executing them. The real "implementation" is the orchestrator LLM reading `.specs/` files and making real tool calls (`Task`, `SendMessage`, `TaskCreate`, `TaskUpdate`, `TaskStop`, or whatever this environment's equivalents are). Don't treat a class/function name here as a tool that exists.

## 1. Input Source Detection

The orchestrator must automatically detect and ingest requirements from various sources based on `$ARGUMENTS`.

### Detection Patterns

Execute detection in this order (first match wins):

```python
import re
from pathlib import Path

def detect_input_source(arguments: str) -> tuple[str, str]:
    """
    Detect input source type and return (source_type, ingestion_command).

    Returns:
        Tuple of (source_type, ingestion_command_or_content)
    """
    args = arguments.strip()

    # 1. Jira ticket: PROJ-123 format
    if re.match(r'^[A-Z]+-\d+$', args):
        return ('jira', f'jira issue view {args} --json')

    # 2. GitHub issue: #123, owner/repo#123, or GitHub issue URL
    if re.match(r'^#\d+$', args):
        return ('github-issue', f'gh issue view {args[1:]} --json title,body,labels,comments')

    if re.match(r'^\w+/\w+#\d+$', args):
        repo, issue = args.split('#')
        return ('github-issue', f'gh issue view {issue} --repo {repo} --json title,body,labels,comments')

    if 'github.com' in args and '/issues/' in args:
        return ('github-issue', f'gh issue view {args} --json title,body,labels,comments')

    # 3. GitHub PR: PR URL or !123 format
    if re.match(r'^!\d+$', args):
        return ('github-pr', f'gh pr view {args[1:]} --json title,body,files,comments,labels')

    if 'github.com' in args and '/pull/' in args:
        return ('github-pr', f'gh pr view {args} --json title,body,files,comments,labels')

    # 4. File path: check if file exists
    file_path = Path(args)
    if file_path.is_file():
        return ('file', str(file_path.absolute()))

    # 5. Directory path: check if directory exists
    if file_path.is_dir():
        return ('directory', str(file_path.absolute()))

    # 6. URL: starts with http:// or https://
    if args.startswith(('http://', 'https://')):
        return ('url', args)

    # 7. Plain text: default fallback
    return ('text', args)
```

### Ingestion Commands

#### Jira Ticket
```bash
# Fetch ticket details as JSON
jira issue view PROJ-123 --json

# Expected fields: key, summary, description, status, assignee, priority, labels
```

#### GitHub Issue
```bash
# Fetch issue details
gh issue view 42 --json title,body,labels,comments

# With repository
gh issue view 42 --repo owner/repo --json title,body,labels,comments

# From URL
gh issue view https://github.com/owner/repo/issues/42 --json title,body,labels,comments
```

#### GitHub PR
```bash
# Fetch PR details including file changes
gh pr view 123 --json title,body,files,comments,labels

# Expected fields: title, body, files[].path, comments[].body, labels[].name
```

#### File Path
```bash
# Read file content using Read tool
# Read(file_path: "/absolute/path/to/requirements.md")
```

#### Directory Path
```bash
# Read key files in priority order:
# 1. README.md
# 2. CLAUDE.md
# 3. docs/requirements.md
# 4. .cursorrules

# Use Glob to find relevant files:
# Glob(pattern: "**/{README.md,CLAUDE.md,requirements.md,.cursorrules}", path: "/dir")
```

#### URL
```bash
# Fetch and extract content
# WebFetch(url: "https://example.com/spec", prompt: "Extract requirements and technical specifications")
```

#### Plain Text
```python
# Use directly as requirements
requirements = arguments
```

### Extraction Strategy

After ingestion, extract structured data:

```python
def extract_requirements(source_type: str, raw_content: str) -> dict:
    """Extract structured requirements from raw content."""
    return {
        'title': extract_title(raw_content),
        'description': extract_description(raw_content),
        'acceptance_criteria': extract_acceptance_criteria(raw_content),
        'technical_constraints': extract_constraints(raw_content),
        'security_requirements': extract_security_requirements(raw_content),
        'performance_requirements': extract_performance_requirements(raw_content),
        'dependencies': extract_dependencies(raw_content),
        'affected_files': extract_affected_files(raw_content) if source_type == 'github-pr' else [],
    }
```

## 2. Complexity Assessment Matrix

Use this scoring system to determine lite vs. full mode.

### Scoring Algorithm

```python
def assess_complexity(requirements: dict, codebase_context: dict) -> tuple[int, str]:
    """
    Assess implementation complexity.

    Returns:
        Tuple of (score, recommendation)
    """
    score = 0
    signals = []

    # 1. Component count (0-2 points)
    components = detect_components(requirements)
    if len(components) >= 3:
        score += 2
        signals.append(f"Multiple components: {', '.join(components)}")
    elif len(components) >= 2:
        score += 1
        signals.append(f"Two components: {', '.join(components)}")

    # 2. Security sensitivity (0-2 points)
    security_keywords = ['auth', 'authentication', 'payment', 'stripe', 'pii', 'personal data',
                         'password', 'token', 'secret', 'credential', 'encrypt']
    if any(keyword in requirements['description'].lower() for keyword in security_keywords):
        score += 2
        signals.append("Security-sensitive feature detected")

    # 3. Performance requirements (0-1 point)
    perf_keywords = ['real-time', 'websocket', 'sla', 'latency', 'performance', 'cache',
                     'optimization', 'scale', '< 100ms', '< 1s']
    if any(keyword in requirements['description'].lower() for keyword in perf_keywords):
        score += 1
        signals.append("Performance requirements detected")

    # 4. External integrations (0-2 points)
    integration_keywords = ['api', 'third-party', 'webhook', 'integration', 'external service',
                           'oauth', 'stripe', 'supabase', 'firebase']
    integration_count = sum(1 for keyword in integration_keywords
                           if keyword in requirements['description'].lower())
    if integration_count >= 2:
        score += 2
        signals.append(f"Multiple external integrations ({integration_count})")
    elif integration_count >= 1:
        score += 1
        signals.append("External integration required")

    # 5. File change estimate (0-2 points)
    estimated_files = estimate_file_changes(requirements, codebase_context)
    if estimated_files >= 15:
        score += 2
        signals.append(f"Large change: ~{estimated_files} files")
    elif estimated_files >= 10:
        score += 1
        signals.append(f"Medium change: ~{estimated_files} files")

    # 6. Domain familiarity (0-1 point)
    unfamiliar_keywords = ['new framework', 'never used', 'unfamiliar', 'learning',
                          'blockchain', 'web3', 'machine learning', 'ai model']
    if any(keyword in requirements['description'].lower() for keyword in unfamiliar_keywords):
        score += 1
        signals.append("Unfamiliar technology domain")

    # Generate recommendation
    if score <= 1:
        recommendation = "LITE"
    elif score <= 3:
        recommendation = "ASK_USER"
    else:
        recommendation = "FULL"

    return score, recommendation, signals
```

### Scoring Matrix

| Signal | Score +2 (High Complexity) | Score +1 (Medium) | Score 0 (Low) |
|--------|---------------------------|-------------------|---------------|
| **Components** | 3+ components (frontend + backend + DB + infra) | 2 components (e.g., frontend + backend) | Single component |
| **Security** | Auth, payments, PII, encryption | Permission checks, input validation | No sensitive data |
| **Performance** | Real-time, SLAs, <100ms latency | Caching, optimization | Standard CRUD |
| **Integration** | 2+ external APIs/services | 1 external API | Self-contained |
| **File changes** | 15+ files estimated | 10-14 files | <10 files |
| **Domain** | Unfamiliar tech, new framework | Partially familiar | Well-understood |

### Decision Thresholds

- **Score 0-1**: Automatically use **LITE mode**
- **Score 2-3**: **ASK USER** with recommendation (default: lite)
- **Score 4+**: Automatically use **FULL mode**

### User Prompt for Borderline Cases

```
Complexity assessment: Score 3/12 (borderline)

Signals detected:
- Two components: frontend + backend
- External integration required
- Medium change: ~12 files

Recommendation: LITE mode (single orchestrator)
- Faster execution
- Lower token usage
- Suitable for well-scoped features

Would you like to proceed with LITE mode, or use FULL mode (multi-agent team)?
[1] LITE mode (recommended)
[2] FULL mode
[3] Show detailed comparison
```

## 3. Short ID Generation

Generate a unique, human-readable identifier for the specification.

### Algorithm

```python
import re
from datetime import datetime
from pathlib import Path

def generate_short_id(title: str, specs_dir: Path = Path('.specs')) -> str:
    """
    Generate unique short ID from title.

    Format: slugified-title-YYYYMMDD[-N]

    Args:
        title: Feature title
        specs_dir: Directory containing existing specs

    Returns:
        Unique short ID
    """
    # 1. Slugify title
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
    slug = re.sub(r'[\s_]+', '-', slug)   # Replace spaces/underscores with hyphens
    slug = re.sub(r'-+', '-', slug)       # Remove consecutive hyphens
    slug = slug.strip('-')                 # Remove leading/trailing hyphens

    # 2. Truncate to max 30 characters
    if len(slug) > 30:
        slug = slug[:30].rstrip('-')

    # 3. Add date suffix
    date_suffix = datetime.now().strftime('%Y%m%d')
    short_id = f"{slug}-{date_suffix}"

    # 4. Handle collisions
    if specs_dir.exists():
        counter = 2
        original_id = short_id
        while (specs_dir / short_id).exists():
            short_id = f"{original_id}-{counter}"
            counter += 1

    return short_id
```

### Examples

| Title | Generated ID | Notes |
|-------|--------------|-------|
| "User Authentication System" | `user-authentication-system-20260205` | Standard case |
| "Add OAuth2 Support for Google & GitHub" | `add-oauth2-support-for-google-20260205` | Special chars removed |
| "Implement Real-Time WebSocket Notifications with Redis Pub/Sub" | `implement-real-time-websocket-20260205` | Truncated to 30 chars |
| "User Authentication System" (duplicate) | `user-authentication-system-20260205-2` | Collision handling |

### Directory Structure

```
.specs/
├── user-authentication-system-20260205/
│   ├── spec.json                    # Phase metadata
│   ├── 00-requirements.md           # Phase 0: Ingested requirements
│   ├── 01-clarifications.md         # Phase 1: Q&A
│   ├── 02-specification.md          # Phase 2: Detailed spec
│   ├── 03-architecture.md           # Phase 3: Architecture doc
│   ├── 04-review-findings.md        # Phase 4: Adversarial review
│   ├── 05-tasks.md                  # Phase 5: Task breakdown
│   └── tasks/                       # Task artifacts
│       ├── task-001-setup-auth-middleware.md
│       └── task-002-implement-login-endpoint.md
└── add-payment-integration-20260205/
    └── ...
```

## 4. Phase Transition Details

Each phase follows a strict entry → action → exit → gate pattern.

### Phase 0: Input Ingestion & Discovery

**Entry Conditions:**
- Skill invoked with `$ARGUMENTS`
- No prior spec exists for this request

**Actions (Full Mode):**
1. Detect input source using pattern matching
2. Execute ingestion command (Bash/Read/WebFetch)
3. Parse and extract structured requirements
4. Perform codebase discovery (Glob for relevant files)
5. Generate short ID
6. Create `.specs/{short_id}/` directory
7. Write `00-requirements.md` and initial `spec.json`
8. Run complexity assessment
9. Decide lite vs. full mode (or ask user)

**Actions (Lite Mode):**
Same as full mode (no agents spawned yet)

**Exit Conditions:**
- Requirements successfully ingested
- Short ID generated and spec directory created
- Complexity assessment complete
- Mode decision made

**Gate Criteria:**
- `spec.json` exists with valid metadata
- `00-requirements.md` contains non-empty requirements
- Mode field set to "lite" or "full"

**Failure Handling:**
- If ingestion fails: prompt user for manual requirements
- If complexity assessment fails: default to lite mode

**Agent Spawning:**
None (orchestrator only)

### Phase 1: Clarifying Questions

**Entry Conditions:**
- Phase 0 complete
- Requirements contain ambiguities or gaps

**Actions (Full Mode):**
1. Spawn product-lead agent
2. Product Lead analyzes requirements
3. Product Lead generates clarifying questions
4. Orchestrator presents questions to user via SendMessage
5. User responds
6. Product Lead validates responses
7. Loop until all ambiguities resolved

**Actions (Lite Mode):**
1. Orchestrator analyzes requirements directly
2. Generate clarifying questions using Claude
3. Present questions to user
4. Collect responses
5. Update requirements

**Exit Conditions:**
- All critical ambiguities resolved
- Acceptance criteria clearly defined
- No BLOCKER-level questions remaining

**Gate Criteria:**
- User has responded to all questions
- Requirements updated with clarifications
- `01-clarifications.md` written

**Failure Handling:**
- If user provides incomplete answers: re-ask with more context
- If questions are unclear: product lead revises

**Agent Spawning (Full Mode):**
- **Wave 1**: product-lead

### Phase 2: Specification

**Entry Conditions:**
- Phase 1 complete
- All clarifications resolved

**Actions (Full Mode):**
1. Product Lead drafts detailed specification
2. Specification includes:
   - Feature overview
   - User stories with acceptance criteria
   - Functional requirements
   - Non-functional requirements (security, performance, accessibility)
   - Success metrics
3. Product Lead self-reviews against the completeness checklist below
4. Write `02-specification.md`

**Actions (Lite Mode):**
1. Orchestrator drafts specification directly
2. Include all required sections
3. Write `02-specification.md`

**Exit Conditions:**
- Specification complete and comprehensive
- All acceptance criteria measurable
- No ambiguous requirements

**Gate Criteria:**
- Specification Review Gate passes
- All user stories have clear acceptance criteria
- Non-functional requirements specified

**Failure Handling:**
- If spec incomplete: product lead revises (max 2 retries)
- If acceptance criteria unclear: loop back to Phase 1

**Agent Spawning:**
None (uses existing Wave 1 agents in full mode)

### Phase 3: Architecture & Design

**Entry Conditions:**
- Phase 2 complete
- Specification approved

**Actions (Full Mode):**
1. Spawn architect agent
2. Architect performs codebase analysis (Grep, Read, Glob)
3. Architect designs solution:
   - System architecture (components, data flow)
   - Technology choices (libraries, frameworks, patterns)
   - Database schema changes
   - API contracts
   - File structure and module organization
4. Generate Mermaid diagrams (architecture, sequence, ER)
5. Write `03-architecture.md`

**Actions (Lite Mode):**
1. Orchestrator performs codebase analysis
2. Design solution architecture
3. Generate Mermaid diagrams
4. Write `03-architecture.md`

**Exit Conditions:**
- Architecture documented with diagrams
- All technical decisions justified
- Implementation approach clear

**Gate Criteria:**
- Architecture addresses all requirements
- Mermaid diagrams render correctly
- Technology choices aligned with codebase

**Failure Handling:**
- If architecture incomplete: architect revises (max 2 retries)
- If diagrams malformed: regenerate

**Agent Spawning (Full Mode):**
- **Wave 2**: architect

### Phase 4: Adversarial Review

**Entry Conditions:**
- Phase 3 complete
- Architecture documented

**Actions (Full Mode):**
1. Spawn adversary-reviewer agent (senior staff engineer persona)
2. Reviewer performs adversarial analysis:
   - Security vulnerabilities (OWASP Top 10)
   - Performance bottlenecks
   - Scalability issues
   - Edge cases and failure scenarios
   - Accessibility gaps
   - Technical debt introduction
3. Reviewer categorizes findings:
   - BLOCKER: Must fix before implementation
   - CRITICAL: Should fix before implementation
   - WARNING: Consider addressing
   - INFO: Nice-to-have improvements
4. Write `04-review-findings.md`
5. If BLOCKERs found: architect revises architecture
6. Loop until zero BLOCKERs

**Actions (Lite Mode):**
1. Orchestrator performs adversarial review
2. Generate findings with severity levels
3. Write `04-review-findings.md`
4. If BLOCKERs found: revise architecture

**Exit Conditions:**
- Adversarial review complete
- Zero BLOCKER findings
- All CRITICAL findings addressed or acknowledged

**Gate Criteria:**
- Adversarial Review Gate passes (0 BLOCKERs)
- Findings documented with severity and remediation
- Architecture revised if needed

**Failure Handling:**
- If BLOCKERs persist after 2 revisions: escalate to user
- If reviewer request is unclear: architect clarifies

**Agent Spawning (Full Mode):**
- **Wave 3**: adversary-reviewer

### Phase 5: Task Decomposition

**Entry Conditions:**
- Phase 4 complete
- Architecture approved (0 BLOCKERs)

**Actions (Full Mode):**
1. Product Lead (from Wave 1) breaks down work into tasks
2. Each task includes:
   - Task ID (sequential)
   - Title and description
   - Acceptance criteria
   - Estimated effort (S/M/L)
   - Dependencies (blocks/blocked-by)
   - Owner (frontend-engineer, backend-engineer, etc.)
   - Files to modify
3. Generate dependency graph (Mermaid)
4. Write `05-tasks.md`
5. Create task files in `.specs/{short_id}/tasks/`
6. Initialize Task Management System with tasks

**Actions (Lite Mode):**
1. Orchestrator breaks down work into tasks
2. Create task list with all metadata
3. Write `05-tasks.md`
4. Initialize Task Management System

**Exit Conditions:**
- All work decomposed into atomic tasks
- Dependencies clearly defined
- Tasks have clear acceptance criteria

**Gate Criteria:**
- No circular dependencies
- All tasks have owners (full mode) or sequential order (lite mode)
- Tasks map to architecture components

**Failure Handling:**
- If task breakdown incomplete: product lead revises
- If dependencies invalid: regenerate task graph

**Agent Spawning:**
None (re-uses Wave 1 product-lead in full mode)

### USER APPROVAL GATE

**Entry Conditions:**
- Phase 5 complete
- All planning artifacts generated

**Actions (Both Modes):**
1. Orchestrator generates summary of plan:
   - Feature overview
   - Architecture highlights
   - Task count and estimated effort
   - Key technical decisions
   - Risk summary
2. Present summary to user with approval options:
   - [1] Approve and proceed to implementation
   - [2] Request changes to specification
   - [3] Request changes to architecture
   - [4] Request changes to tasks
   - [5] Cancel implementation
3. Wait for user response

**Exit Conditions:**
- User selects "Approve" (option 1)

**Gate Criteria:**
- User approval received

**Failure Handling:**
- If user requests changes: jump to corresponding phase
- If user cancels: teardown and exit
- No retry limit (user controls flow)

**Agent Spawning:**
None (gate only)

### Phase 6: Implementation

**Entry Conditions:**
- User approval received
- Task list initialized in Task Management System

**Actions (Full Mode):**
1. Spawn implementation agents in parallel:
   - frontend-engineer (if frontend tasks exist)
   - backend-engineer (if backend tasks exist)
   - infra-engineer (if infrastructure tasks exist)
2. Each agent:
   - Claims tasks from Task Management System
   - Implements according to architecture
   - Writes tests (TDD where applicable)
   - Updates task status (in-progress → completed)
   - Sends completion notification to orchestrator
3. Orchestrator monitors progress and coordinates
4. Handle blockers and dependencies

**Actions (Lite Mode):**
1. Orchestrator processes tasks sequentially
2. For each task:
   - Read task details
   - Implement code changes
   - Write tests
   - Mark task completed
3. Continue until all tasks done

**Exit Conditions:**
- All tasks in "completed" status
- All code changes committed

**Gate Criteria:**
- Task Management System shows 100% completion
- No tasks in "blocked" status
- All files modified as planned

**Failure Handling:**
- If agent fails: orchestrator re-spawns or uses subagent fallback
- If task blocked: orchestrator resolves or escalates to user
- If implementation diverges from spec: trigger architecture review

**Agent Spawning (Full Mode):**
- **Wave 4**: frontend-engineer, backend-engineer, infra-engineer (parallel)

### Phase 7: Quality Assurance

**Entry Conditions:**
- Phase 6 complete
- All tasks implemented

**Actions (Full Mode):**
1. Spawn qa-engineer agent
2. QA engineer executes:
   - Run all tests (unit, integration, E2E)
   - Verify acceptance criteria for each task
   - Test edge cases and error handling
   - Check code coverage (≥80%)
3. If quality issues found:
   - Create bug reports
   - Assign to appropriate dev agent
   - Re-spawn dev agent to fix
   - Re-run QA
4. Optionally spawn specialized agents based on spec:
   - security-engineer (if security-sensitive)
   - performance-engineer (if performance requirements)
   - devops-engineer (if deployment changes)
5. Write QA report

**Actions (Lite Mode):**
1. Orchestrator runs all tests
2. Verify acceptance criteria
3. Check code coverage
4. Generate QA report

**Exit Conditions:**
- All tests passing
- All acceptance criteria verified
- No CRITICAL bugs

**Gate Criteria:**
- Quality Verification Gate passes
- Test coverage ≥80%
- Zero CRITICAL or BLOCKER bugs

**Failure Handling:**
- If tests fail: loop back to Phase 6 (max 3 retries)
- If critical bugs found: assign to dev for fix
- If coverage insufficient: add tests

**Agent Spawning (Full Mode):**
- **Wave 5**: qa-engineer + optional security-engineer, performance-engineer, devops-engineer

### Phase 8: Documentation & Delivery

**Entry Conditions:**
- Phase 7 complete
- All quality gates passed

**Actions (Full Mode):**
1. Spawn tech-writer agent
2. Tech writer generates:
   - User-facing documentation (if UI changes)
   - Developer documentation (API docs, README updates)
   - Migration guide (if breaking changes)
   - Changelog entry
3. Update `.specs/{short_id}/spec.json` with completion status
4. Generate delivery summary
5. Orchestrator sends completion message to user

**Actions (Lite Mode):**
1. Orchestrator generates documentation
2. Update spec.json
3. Generate delivery summary
4. Send completion message

**Exit Conditions:**
- All documentation generated
- Delivery summary complete
- User notified

**Gate Criteria:**
- Final Delivery Gate passes
- All spec artifacts exist
- All tasks marked completed

**Failure Handling:**
- If documentation incomplete: revise (max 1 retry)
- If delivery summary missing details: regenerate

**Agent Spawning (Full Mode):**
- **Wave 6**: tech-writer

### Phase 9: Teardown

**Entry Conditions:**
- Phase 8 complete OR user cancelled

**Actions (Both Modes):**
1. Shut down all active teammates (if full mode)
2. Stop each one with this environment's real stop primitive (`TaskStop` in Claude Code) — don't assume a dedicated "cleanup" call exists
3. Archive spec directory
4. Update global Task Management System
5. Log session metrics (optional)

**Exit Conditions:**
- All teammates shut down
- Team cleaned up
- Orchestrator exits

**Gate Criteria:**
None (always succeeds)

**Failure Handling:**
- If teammate shutdown fails: force cleanup after timeout
- If team cleanup fails: log error and continue

**Agent Spawning:**
None (shutdown only)

## 5. Wave-Based Agent Spawning (Full Mode)

Agents are spawned in waves and shut down when their phase completes to minimize token usage.

### Wave Lifecycle

```python
class AgentWave:
    """Represents a wave of agents spawned for specific phases."""

    def __init__(self, wave_id: int, phase_range: tuple[int, int], agents: list[str]):
        self.wave_id = wave_id
        self.phase_range = phase_range  # (start_phase, end_phase)
        self.agents = agents
        self.spawned = False
        self.active_agent_ids = []

    def should_spawn(self, current_phase: int) -> bool:
        """Check if wave should spawn at current phase."""
        return current_phase == self.phase_range[0] and not self.spawned

    def should_shutdown(self, current_phase: int) -> bool:
        """Check if wave should shut down after current phase."""
        return current_phase > self.phase_range[1] and self.spawned
```

### Wave Definitions

```python
AGENT_WAVES = [
    AgentWave(
        wave_id=1,
        phase_range=(1, 2),  # Phases 1-2: Clarifying Questions & Specification
        agents=['product-lead']
    ),
    AgentWave(
        wave_id=2,
        phase_range=(3, 3),  # Phase 3: Architecture & Design
        agents=['architect']
    ),
    AgentWave(
        wave_id=3,
        phase_range=(4, 4),  # Phase 4: Adversarial Review
        agents=['adversary-reviewer']
    ),
    # Note: Wave 1 product-lead is re-used in Phase 5, not re-spawned
    AgentWave(
        wave_id=4,
        phase_range=(6, 6),  # Phase 6: Implementation
        agents=['frontend-engineer', 'backend-engineer', 'infra-engineer']  # Conditional spawning
    ),
    AgentWave(
        wave_id=5,
        phase_range=(7, 7),  # Phase 7: Quality Assurance
        agents=['qa-engineer']  # + optional security-engineer, performance-engineer, devops-engineer
    ),
    AgentWave(
        wave_id=6,
        phase_range=(8, 8),  # Phase 8: Documentation & Delivery
        agents=['tech-writer']
    ),
]
```

### Conditional Agent Spawning

Some agents are only spawned if needed:

```python
def determine_implementation_agents(tasks: list[Task]) -> list[str]:
    """Determine which implementation agents to spawn based on tasks."""
    agents = []

    # Check task types
    has_frontend = any('frontend' in task.tags for task in tasks)
    has_backend = any('backend' in task.tags for task in tasks)
    has_infra = any('infra' in task.tags or 'deployment' in task.tags for task in tasks)

    if has_frontend:
        agents.append('frontend-engineer')
    if has_backend:
        agents.append('backend-engineer')
    if has_infra:
        agents.append('infra-engineer')

    # Default to backend if no specific tags
    if not agents:
        agents.append('backend-engineer')

    return agents

def determine_qa_agents(spec: dict) -> list[str]:
    """Determine which QA agents to spawn based on specification."""
    agents = ['qa-engineer']  # Always spawn base QA

    # Check for security requirements
    if spec.get('security_requirements') or 'auth' in spec.get('description', '').lower():
        agents.append('security-engineer')

    # Check for performance requirements
    if spec.get('performance_requirements') or 'real-time' in spec.get('description', '').lower():
        agents.append('performance-engineer')

    # Check for infrastructure changes
    if spec.get('deployment_requirements') or 'infrastructure' in spec.get('description', '').lower():
        agents.append('devops-engineer')

    return agents
```

### Agent Shutdown Protocol

```python
async def shutdown_wave(wave: AgentWave, orchestrator: Agent):
    """Gracefully shut down all agents in a wave."""
    for agent_name in wave.active_agent_ids:
        # Send shutdown request
        orchestrator.send_message(
            type='shutdown_request',
            recipient=agent_name,
            content=f'Phase {wave.phase_range[1]} complete. Shutting down {agent_name}.'
        )

        # Wait for shutdown response (max 30 seconds)
        response = await orchestrator.wait_for_response(
            from_agent=agent_name,
            timeout=30
        )

        if not response or not response.get('approve'):
            # Force shutdown after timeout
            logger.warning(f'Force shutting down {agent_name} after timeout')

    wave.spawned = False
    wave.active_agent_ids = []
```

### Agent Re-Use

The product-lead agent from Wave 1 is re-used in Phase 5 (Task Decomposition) instead of being shut down and re-spawned:

```python
# In Phase 2 → Phase 3 transition
# Do NOT shut down product-lead
shutdown_agents = ['product-lead']  # Keep product-lead alive

# In Phase 5
# product-lead is already active from Wave 1
# Send task decomposition request directly
```

## 6. Quality Gate Specifications

Gates enforce quality standards between phases.

### Gate Definitions

```python
class QualityGate:
    """Represents a quality gate between phases."""

    def __init__(self, name: str, phase: int, pass_criteria: list[str],
                 fail_action: str, max_retries: int):
        self.name = name
        self.phase = phase
        self.pass_criteria = pass_criteria
        self.fail_action = fail_action
        self.max_retries = max_retries
        self.retry_count = 0

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        """
        Evaluate gate criteria.

        Returns:
            Tuple of (passed, failure_reason)
        """
        raise NotImplementedError

    def can_retry(self) -> bool:
        """Check if gate can retry after failure."""
        return self.retry_count < self.max_retries

    def record_retry(self):
        """Increment retry counter."""
        self.retry_count += 1
```

### Gate Implementations

#### Clarifying Questions Gate

```python
class ClarifyingQuestionsGate(QualityGate):
    """Gate after Phase 1: Ensure all ambiguities resolved."""

    def __init__(self):
        super().__init__(
            name='Clarifying Questions',
            phase=1,
            pass_criteria=[
                'All critical questions answered',
                'No BLOCKER-level ambiguities',
                'Acceptance criteria clearly defined'
            ],
            fail_action='Ask more questions',
            max_retries=999  # Unlimited
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        clarifications = context.get('clarifications', {})

        # Check if all questions answered
        unanswered = [q for q in clarifications.get('questions', [])
                     if not q.get('answer')]
        if unanswered:
            return False, f'{len(unanswered)} questions unanswered'

        # Check for blocker ambiguities
        blockers = [q for q in clarifications.get('questions', [])
                   if q.get('severity') == 'BLOCKER' and not q.get('resolved')]
        if blockers:
            return False, f'{len(blockers)} BLOCKER ambiguities remain'

        # Check acceptance criteria
        spec = context.get('specification', {})
        if not spec.get('acceptance_criteria'):
            return False, 'Acceptance criteria not defined'

        return True, ''
```

#### Spec Review Gate

```python
class SpecReviewGate(QualityGate):
    """Gate after Phase 2: Ensure specification is complete."""

    def __init__(self):
        super().__init__(
            name='Spec Review',
            phase=2,
            pass_criteria=[
                'All user stories have acceptance criteria',
                'Functional requirements complete',
                'Non-functional requirements specified',
                'Success metrics defined'
            ],
            fail_action='Revise specification',
            max_retries=2
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        spec = context.get('specification', {})

        # Check user stories
        user_stories = spec.get('user_stories', [])
        if not user_stories:
            return False, 'No user stories defined'

        stories_without_criteria = [s for s in user_stories
                                   if not s.get('acceptance_criteria')]
        if stories_without_criteria:
            return False, f'{len(stories_without_criteria)} user stories lack acceptance criteria'

        # Check functional requirements
        if not spec.get('functional_requirements'):
            return False, 'Functional requirements missing'

        # Check non-functional requirements
        required_nfr = ['security', 'performance', 'accessibility']
        missing_nfr = [nfr for nfr in required_nfr
                      if not spec.get(f'{nfr}_requirements')]
        if missing_nfr:
            return False, f'Missing non-functional requirements: {", ".join(missing_nfr)}'

        # Check success metrics
        if not spec.get('success_metrics'):
            return False, 'Success metrics not defined'

        return True, ''
```

#### Adversarial Review Gate

```python
class AdversarialReviewGate(QualityGate):
    """Gate after Phase 4: Ensure zero BLOCKER findings."""

    def __init__(self):
        super().__init__(
            name='Adversarial Review',
            phase=4,
            pass_criteria=[
                'Zero BLOCKER findings',
                'All CRITICAL findings addressed or acknowledged'
            ],
            fail_action='Architect revises architecture',
            max_retries=2
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        findings = context.get('review_findings', {})

        # Check for BLOCKERs
        blockers = [f for f in findings.get('findings', [])
                   if f.get('severity') == 'BLOCKER']
        if blockers:
            blocker_summary = ', '.join(f.get('title') for f in blockers)
            return False, f'{len(blockers)} BLOCKER findings: {blocker_summary}'

        # Check CRITICAL findings are addressed
        criticals = [f for f in findings.get('findings', [])
                    if f.get('severity') == 'CRITICAL']
        unaddressed = [f for f in criticals
                      if not f.get('addressed') and not f.get('acknowledged')]
        if unaddressed:
            return False, f'{len(unaddressed)} CRITICAL findings not addressed'

        return True, ''
```

#### User Approval Gate

```python
class UserApprovalGate(QualityGate):
    """Gate after Phase 5: Require explicit user approval."""

    def __init__(self):
        super().__init__(
            name='User Approval',
            phase=5,
            pass_criteria=['User approved plan'],
            fail_action='Revise or cancel',
            max_retries=999  # Unlimited (user controls)
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        approval = context.get('user_approval')

        if approval is None:
            return False, 'Waiting for user approval'

        if approval.get('action') != 'approve':
            reason = approval.get('feedback', 'User requested changes')
            return False, reason

        return True, ''
```

#### Quality Verification Gate

```python
class QualityVerificationGate(QualityGate):
    """Gate after Phase 7: Ensure all tests pass and no critical bugs."""

    def __init__(self):
        super().__init__(
            name='Quality Verification',
            phase=7,
            pass_criteria=[
                'All tests passing',
                'Test coverage ≥80%',
                'Zero CRITICAL or BLOCKER bugs',
                'All acceptance criteria verified'
            ],
            fail_action='Loop to Phase 6 (Implementation)',
            max_retries=3
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        qa_report = context.get('qa_report', {})

        # Check test results
        test_results = qa_report.get('test_results', {})
        if test_results.get('failed', 0) > 0:
            return False, f'{test_results["failed"]} tests failed'

        # Check coverage
        coverage = test_results.get('coverage', 0)
        if coverage < 80:
            return False, f'Test coverage {coverage}% < 80%'

        # Check for critical bugs
        bugs = qa_report.get('bugs', [])
        critical_bugs = [b for b in bugs
                        if b.get('severity') in ['BLOCKER', 'CRITICAL']]
        if critical_bugs:
            return False, f'{len(critical_bugs)} critical bugs found'

        # Check acceptance criteria
        acceptance = qa_report.get('acceptance_criteria_verification', {})
        failed_criteria = [c for c in acceptance.get('criteria', [])
                          if not c.get('passed')]
        if failed_criteria:
            return False, f'{len(failed_criteria)} acceptance criteria failed'

        return True, ''
```

#### Final Delivery Gate

```python
class FinalDeliveryGate(QualityGate):
    """Gate after Phase 8: Ensure all artifacts exist."""

    def __init__(self):
        super().__init__(
            name='Final Delivery',
            phase=8,
            pass_criteria=[
                'All spec artifacts exist',
                'All tasks completed',
                'Documentation generated',
                'Delivery summary complete'
            ],
            fail_action='Block completion',
            max_retries=1
        )

    async def evaluate(self, context: dict) -> tuple[bool, str]:
        spec_dir = context.get('spec_dir')

        # Check artifacts
        required_artifacts = [
            '00-requirements.md',
            '02-specification.md',
            '03-architecture.md',
            '05-tasks.md',
            'spec.json'
        ]

        missing = [f for f in required_artifacts
                  if not (spec_dir / f).exists()]
        if missing:
            return False, f'Missing artifacts: {", ".join(missing)}'

        # Check all tasks completed
        tasks = context.get('tasks', [])
        incomplete = [t for t in tasks if t.get('status') != 'completed']
        if incomplete:
            return False, f'{len(incomplete)} tasks incomplete'

        # Check documentation
        if not context.get('documentation_generated'):
            return False, 'Documentation not generated'

        # Check delivery summary
        if not context.get('delivery_summary'):
            return False, 'Delivery summary missing'

        return True, ''
```

### Gate Summary Table

| Gate | Phase | Pass Criteria | Fail Action | Max Retries |
|------|-------|--------------|-------------|-------------|
| Clarifying Questions | 1 | All ambiguities resolved | Ask more questions | Unlimited |
| Spec Review | 2 | Requirements complete, criteria clear | Revise specs | 2 |
| Adversarial Review | 4 | Zero BLOCKER findings | Architect revises | 2 |
| User Approval | 5 | User selects "Approve" | Revise or cancel | Unlimited |
| Quality Verification | 7 | All tests pass, no critical security findings | Loop to Phase 6 | 3 |
| Final Delivery | 8 | Spec artifacts exist, all tasks completed | Block completion | 1 |

## 7. Error Recovery

Common failure scenarios and their recovery strategies.

### Teammate Fails to Respond

**Scenario:** Agent doesn't respond to message within timeout.

**Detection:**
```python
async def wait_for_teammate_response(agent_name: str, timeout: int = 60) -> dict | None:
    """Wait for teammate response with timeout."""
    try:
        response = await asyncio.wait_for(
            receive_message(from_agent=agent_name),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.error(f'Timeout waiting for {agent_name} (>{timeout}s)')
        return None
```

**Recovery:**
1. **First attempt**: Re-send message with more context
2. **Second attempt**: Re-spawn agent and retry
3. **Final fallback**: Use subagent to complete task
4. **Escalation**: If all fail, notify user and request manual intervention

```python
async def handle_unresponsive_teammate(agent_name: str, task: dict):
    """Handle unresponsive teammate with fallback strategy."""

    # Attempt 1: Re-send with more context
    logger.warning(f'{agent_name} unresponsive, resending message')
    await send_message(agent_name, task, include_context=True)
    response = await wait_for_teammate_response(agent_name, timeout=120)
    if response:
        return response

    # Attempt 2: Re-spawn agent
    logger.error(f'{agent_name} still unresponsive, re-spawning')
    await shutdown_agent(agent_name, force=True)
    await spawn_agent(agent_name)
    await send_message(agent_name, task)
    response = await wait_for_teammate_response(agent_name, timeout=120)
    if response:
        return response

    # Attempt 3: Subagent fallback
    logger.critical(f'{agent_name} repeatedly unresponsive, using subagent fallback')
    result = await execute_with_subagent(task, subagent_type=determine_subagent_type(agent_name))
    return result

    # Escalation
    if not result:
        await notify_user(
            f'Agent {agent_name} failed to complete task. Manual intervention required.',
            task_details=task
        )
```

### Tests Fail Repeatedly

**Scenario:** Tests fail in Phase 7 after multiple implementation attempts.

**Detection:**
```python
if qa_gate.retry_count >= qa_gate.max_retries:
    logger.error(f'Quality gate failed {qa_gate.retry_count} times (max: {qa_gate.max_retries})')
```

**Recovery:**
1. **First failure**: Send detailed test failures to implementation agents, loop to Phase 6
2. **Second failure**: Re-run adversarial review on implemented code
3. **Third failure**: Escalate to user with diagnostic report

```python
async def handle_repeated_test_failures(qa_report: dict, retry_count: int):
    """Handle repeated test failures with escalation."""

    if retry_count == 1:
        # First failure: detailed feedback to devs
        await send_test_failures_to_devs(qa_report)
        return 'retry'

    elif retry_count == 2:
        # Second failure: re-review implementation
        logger.warning('Tests failed twice, triggering implementation review')
        await spawn_agent('code-reviewer')
        review_result = await request_code_review(qa_report.get('failed_tests'))

        if review_result.get('issues_found'):
            await send_review_findings_to_devs(review_result)
            return 'retry'

    else:
        # Third failure: escalate to user
        diagnostic_report = generate_diagnostic_report(qa_report, retry_count)
        await notify_user(
            'Quality verification failed after 3 attempts. Review required.',
            report=diagnostic_report,
            options=['Continue anyway', 'Revise architecture', 'Cancel']
        )
        return 'escalate'
```

### Adversary Finds Critical Issue After Implementation

**Scenario:** Security or performance issue discovered in Phase 7 that requires architecture change.

**Detection:**
```python
qa_findings = qa_report.get('findings', [])
blocker_findings = [f for f in qa_findings if f.get('severity') == 'BLOCKER']
if blocker_findings:
    logger.critical(f'{len(blocker_findings)} BLOCKER issues found post-implementation')
```

**Recovery:**
1. Create hotfix task with BLOCKER priority
2. Assign to appropriate implementation agent
3. Fast-track through QA (skip Phase 7 loop, run targeted tests only)
4. If fix requires architecture change: notify user and offer options

```python
async def handle_post_implementation_blocker(finding: dict):
    """Handle BLOCKER finding discovered after implementation."""

    # Check if architecture change needed
    requires_arch_change = finding.get('remediation_scope') == 'architecture'

    if requires_arch_change:
        # Escalate to user
        await notify_user(
            f'BLOCKER issue requires architecture change: {finding["title"]}',
            details=finding,
            options=[
                'Revise architecture and re-implement',
                'Accept risk and continue',
                'Cancel implementation'
            ]
        )
    else:
        # Create hotfix task
        hotfix_task = create_hotfix_task(finding)
        await add_task_to_system(hotfix_task, priority='BLOCKER')

        # Assign to appropriate dev
        owner = determine_task_owner(hotfix_task)
        await assign_task(hotfix_task, owner)

        # Fast-track QA
        await execute_targeted_qa(hotfix_task)
```

### Session Interrupted

**Scenario:** Claude Code session ends unexpectedly (user closes, crash, timeout).

**Detection:**
Session interrupt is external and cannot be detected in-process. Recovery happens on next skill invocation.

**Recovery:**
1. Check for existing `.specs/{short_id}/` directory
2. Read `spec.json` to determine last completed phase
3. Offer user resume options
4. Restore agents if in full mode

```python
def check_for_interrupted_session(arguments: str) -> dict | None:
    """Check if there's an interrupted session to resume."""

    specs_dir = Path('.specs')
    if not specs_dir.exists():
        return None

    # Find most recent spec directory
    spec_dirs = sorted(specs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not spec_dirs:
        return None

    recent_spec = spec_dirs[0]
    spec_file = recent_spec / 'spec.json'

    if not spec_file.exists():
        return None

    spec_data = json.loads(spec_file.read_text())

    # Check if session was interrupted (not completed)
    if spec_data.get('status') == 'completed':
        return None

    return {
        'short_id': recent_spec.name,
        'spec_dir': recent_spec,
        'last_phase': spec_data.get('current_phase', 0),
        'mode': spec_data.get('mode', 'lite'),
        'title': spec_data.get('title', 'Unknown'),
    }

async def resume_interrupted_session(session_data: dict):
    """Resume an interrupted session."""

    logger.info(f'Found interrupted session: {session_data["title"]}')

    # Present resume options to user
    response = await prompt_user(
        f'Found interrupted session: {session_data["title"]} (Phase {session_data["last_phase"]})',
        options=[
            f'Resume from Phase {session_data["last_phase"]}',
            f'Restart from Phase 0',
            f'Start new session',
        ]
    )

    if response == 0:  # Resume
        # Restore context
        spec_data = load_spec(session_data['spec_dir'])

        # Re-spawn agents if full mode and in implementation phase
        if session_data['mode'] == 'full' and session_data['last_phase'] >= 6:
            await restore_implementation_agents(spec_data)

        # Continue from last phase + 1
        return session_data['last_phase'] + 1

    elif response == 1:  # Restart
        # Keep spec directory but reset phase
        return 0

    else:  # New session
        return None
```

### Circular Dependencies in Task Graph

**Scenario:** Task decomposition creates circular dependencies.

**Detection:**
```python
def detect_circular_dependencies(tasks: list[dict]) -> list[list[str]]:
    """Detect circular dependencies in task graph using DFS."""

    # Build adjacency list
    graph = {task['id']: task.get('depends_on', []) for task in tasks}

    def dfs(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                return path[cycle_start:]

        rec_stack.remove(node)
        path.pop()
        return None

    cycles = []
    visited = set()

    for task_id in graph:
        if task_id not in visited:
            cycle = dfs(task_id, visited, set(), [])
            if cycle:
                cycles.append(cycle)

    return cycles
```

**Recovery:**
1. Report cycle to product-lead or orchestrator
2. Request task graph revision
3. Re-validate after revision

```python
async def handle_circular_dependencies(cycles: list[list[str]]):
    """Handle circular dependencies in task graph."""

    logger.error(f'Circular dependencies detected: {cycles}')

    # Format cycle description
    cycle_descriptions = []
    for cycle in cycles:
        cycle_str = ' → '.join(cycle + [cycle[0]])
        cycle_descriptions.append(cycle_str)

    # Request revision
    await send_message(
        recipient='product-lead',
        type='message',
        content=f'Circular dependencies detected in task graph:\n\n' +
                '\n'.join(f'- {cd}' for cd in cycle_descriptions) +
                '\n\nPlease revise task dependencies to break these cycles.',
        summary='Circular dependencies found'
    )

    # Wait for revised tasks
    revised_tasks = await wait_for_revised_tasks()

    # Re-validate
    new_cycles = detect_circular_dependencies(revised_tasks)
    if new_cycles:
        logger.error('Circular dependencies persist after revision')
        # Escalate to user if still broken
        await notify_user(
            'Task graph has unresolvable circular dependencies.',
            details={'cycles': new_cycles},
            options=['Manual task editing', 'Regenerate tasks', 'Cancel']
        )
```

### Agent Produces Invalid Output

**Scenario:** Agent returns malformed JSON, invalid Mermaid, or output that doesn't match expected schema.

**Detection:**
```python
try:
    spec_data = json.loads(spec_content)
except json.JSONDecodeError as e:
    logger.error(f'Invalid JSON from {agent_name}: {e}')
```

**Recovery:**
1. Send validation error back to agent with example
2. Request corrected output
3. If second attempt fails: use subagent fallback

```python
async def handle_invalid_agent_output(agent_name: str, output: str,
                                      expected_schema: str, error: str):
    """Handle invalid output from agent."""

    # Attempt 1: Send validation error
    await send_message(
        recipient=agent_name,
        type='message',
        content=f'Output validation failed: {error}\n\n' +
                f'Expected schema:\n```json\n{expected_schema}\n```\n\n' +
                'Please correct and resubmit.',
        summary='Validation error'
    )

    corrected_output = await wait_for_teammate_response(agent_name, timeout=60)

    if corrected_output and validate_output(corrected_output, expected_schema):
        return corrected_output

    # Attempt 2: Subagent fallback
    logger.warning(f'{agent_name} unable to correct output, using subagent fallback')
    result = await execute_with_subagent(
        task={'type': 'correct_output', 'original': output, 'schema': expected_schema},
        subagent_type='general'
    )

    return result
```

---

## Summary

This reference document provides the complete technical specifications for the `team-implement` skill's workflow engine. Key takeaways:

1. **Input detection**: Automatic ingestion from 7 source types with fallback chain
2. **Complexity assessment**: 6-signal scoring matrix with 0-12 scale
3. **Short IDs**: Slugified titles with date suffix and collision handling
4. **Phase transitions**: 10 phases with strict gates and retry limits
5. **Wave spawning**: 7 agent waves with conditional spawning and graceful shutdown
6. **Quality gates**: 6 gates with specific pass criteria and escalation paths
7. **Error recovery**: Comprehensive fallback strategies for 8 common failure scenarios

Use this document as the authoritative reference when implementing the orchestrator logic.
