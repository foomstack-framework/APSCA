<!-- CONTEXT -->
These user stories are meant to be added To the proper epics under the examination system feature. It is critical that the stories are properly added to the correct epics and to the examination system feature. Please don't miss this.

---

# Feature Input: Examination System — User Stories

These user stories are for demo purposes, representing key workflows across the Examination System feature.

---

## User Stories

### STORY-001: Auditor Schedules Part 1 Exam

**As an** auditor,
**I want to** purchase and schedule my Part 1 certification exam,
**So that** I can begin my certification journey with a confirmed exam date.

- **Feature**: Examination System
- **Epic**: Exam Eligibility & Invoice Generation, Exam Scheduling & Integration
- **Priority**: High

**Acceptance Criteria**:
1. Auditor can generate a Part 1 exam invoice from their dashboard
2. Auditor can pay the invoice via Stripe
3. After payment, auditor can select an available ProctorU time slot
4. System enforces 14-day minimum lead time
5. Auditor receives confirmation email with exam details and backup launch link

---

### STORY-002: Firm Purchases Exams in Bulk

**As a** firm supervisor,
**I want to** select multiple auditors and purchase their exams in a single transaction,
**So that** I can efficiently manage exam costs for my team without processing individual invoices.

- **Feature**: Examination System
- **Epic**: Firm Bulk Exam Purchasing
- **Priority**: High

**Acceptance Criteria**:
1. Firm supervisor can view list of associated auditors
2. Firm supervisor can multi-select auditors for exam purchase
3. System validates each auditor's eligibility individually
4. Ineligible auditors are flagged and excluded with explanation
5. System generates a single consolidated invoice for all eligible auditors
6. Each exam line item is recorded as "paid by firm"

---

### STORY-003: Auditor Reschedules Exam

**As an** auditor,
**I want to** reschedule my exam to a different date,
**So that** I can accommodate a scheduling conflict without losing my exam fee.

- **Feature**: Examination System
- **Epic**: Cancellations, Rescheduling & Fees
- **Priority**: Medium

**Acceptance Criteria**:
1. Auditor sees "Reschedule" button on scheduled exam
2. System calculates applicable fee based on days until exam (per Fee Schedule)
3. If fee applies, auditor is prompted to confirm or cancel
4. If original invoice was firm-paid, auditor must select payer (self or firm)
5. Auditor selects new date from available slots
6. Dashboard and confirmation email reflect new exam date

---

### STORY-004: Auditor Launches Exam

**As an** auditor,
**I want to** launch my proctored exam directly from my dashboard,
**So that** I can access my exam session without manually logging into ProctorU.

- **Feature**: Examination System
- **Epic**: Exam Launch & Proctoring
- **Priority**: High

**Acceptance Criteria**:
1. "Start Exam" button appears on dashboard 15 minutes before scheduled time
2. "Reschedule" and "Cancel" buttons are hidden once Start Exam appears
3. Clicking "Start Exam" opens ProctorU session with auto-authentication
4. Exam status updates to "In Progress"
5. If platform is inaccessible, auditor can use backup link from confirmation email

---

### STORY-005: Admin Overrides Scheduling Rules

**As an** APSCA administrator,
**I want to** schedule an exam on behalf of an auditor while bypassing the standard lead time requirement,
**So that** I can resolve special circumstances without the auditor being blocked by system rules.

- **Feature**: Examination System
- **Epic**: Admin Exam Management
- **Priority**: Medium

**Acceptance Criteria**:
1. Admin can search for auditor by name or member number
2. Admin can initiate exam scheduling on auditor's behalf
3. System allows booking within normally restricted lead time window
4. Admin must enter a reason for the override
5. Action is logged with timestamp, admin ID, and override reason
6. Auditor receives standard confirmation email

---

## Summary

| Story | Actor | Epic(s) | Priority |
|-------|-------|---------|----------|
| STORY-001 | Auditor | Eligibility, Scheduling | High |
| STORY-002 | Firm Supervisor | Bulk Purchasing | High |
| STORY-003 | Auditor | Cancellations & Fees | Medium |
| STORY-004 | Auditor | Launch & Proctoring | High |
| STORY-005 | Admin | Admin Management | Medium |

<!-- INTENT INTERPRETATION -->
## Parsed Records

### Features
*No new features identified. All stories belong to existing Feature FEAT-001 (Examination System).*

### Epics
*No new epics identified. All stories map to existing epics under FEAT-001.*

### Requirements
*No new requirements identified. Stories reference existing requirements.*

### Business Artifacts
*No new business artifacts identified.*

### User Stories
| ID | Story | Parent Epic(s) | Release | Status | Notes |
|----|-------|----------------|---------|--------|-------|
| STORY-NEW-001 | As an auditor, I want to purchase and schedule my Part 1 certification exam, so that I can begin my certification journey with a confirmed exam date. | EPIC-001, EPIC-003 | REL-2026-06-01 | backlog | Spans eligibility/invoice and scheduling epics |
| STORY-NEW-002 | As a firm supervisor, I want to select multiple auditors and purchase their exams in a single transaction, so that I can efficiently manage exam costs for my team without processing individual invoices. | EPIC-002 | REL-2026-06-01 | backlog | Firm bulk purchasing workflow |
| STORY-NEW-003 | As an auditor, I want to reschedule my exam to a different date, so that I can accommodate a scheduling conflict without losing my exam fee. | EPIC-004 | REL-2026-06-01 | backlog | Rescheduling with fee logic |
| STORY-NEW-004 | As an auditor, I want to launch my proctored exam directly from my dashboard, so that I can access my exam session without manually logging into ProctorU. | EPIC-006 | REL-2026-06-01 | backlog | Exam launch workflow |
| STORY-NEW-005 | As an APSCA administrator, I want to schedule an exam on behalf of an auditor while bypassing the standard lead time requirement, so that I can resolve special circumstances without the auditor being blocked by system rules. | EPIC-010 | REL-2026-06-01 | backlog | Admin override capability |

### Releases
*No new releases identified. Stories target existing REL-2026-06-01.*

## Validation Notes
- All 5 stories correctly map to existing epics under FEAT-001 (Examination System)
- STORY-NEW-001 spans two epics (EPIC-001 and EPIC-003) as it covers both eligibility/invoice and scheduling
- All stories target the existing planned release REL-2026-06-01
- Each story includes acceptance criteria that will be captured

## Epic Mapping Detail
| Story | Epic ID | Epic Title |
|-------|---------|------------|
| STORY-NEW-001 | EPIC-001 | Exam Eligibility & Invoice Generation |
| STORY-NEW-001 | EPIC-003 | Exam Scheduling & Integration |
| STORY-NEW-002 | EPIC-002 | Firm Bulk Exam Purchasing |
| STORY-NEW-003 | EPIC-004 | Cancellations, Rescheduling & Fees |
| STORY-NEW-004 | EPIC-006 | Exam Launch & Proctoring |
| STORY-NEW-005 | EPIC-010 | Admin Exam Management |

<!-- END INTERPRETATION -->
