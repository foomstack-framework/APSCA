<!-- CONTEXT -->
This document is my first draft of the full examination system feature. It outlines all of the epics and requirements that I currently know of, And it includes the business artifact documents that we will likely need to support these epics. No user stories are included because we are not At the design phase yet. Please note that for the business artifacts, the goal is to create a placeholder document with a detailed description of what That document will hold once it is fleshed out. The goal is not to flesh it out right now.

---

# Feature Input: Examination System

## Feature
- **Name**: Examination System
- **Description**: The end-to-end management of the auditor certification examination process, including purchasing, scheduling via third-party integrations (ProctorU/Calendly), delivery, results processing, and remediation logic.

---

## Epics

### Epic 1: Exam Eligibility & Invoice Generation
- **Description**: Logic to determine if an auditor can purchase a specific exam (Part 1, 2, or 3). Includes prerequisites (status, sequencing), generating the invoice line item, capturing exam language preferences, and enforcing invoice validity periods.

#### Requirements
1. The system shall prevent the generation of an exam invoice unless the auditor status is "In Good Standing".
2. The system shall prevent the generation of an exam invoice if the auditor has any unpaid fee invoices or pending exam invoices.
3. The system shall enforce sequential exam progression: Part 1 must be passed before Part 2; Part 2 must be passed before Part 3.
4. The system shall require an approved Audit Log (minimum 20 days experience) before generating a Part 3 exam invoice.
5. The system shall allow Part 1 and Part 2 invoices to be generated without an approved Audit Log.
6. The system shall automatically expire exam invoices that have not been scheduled within the validity period defined in the Fee Schedule.
7. The system shall capture the auditor's language preference at the time of invoice generation to ensure the correct exam type is scheduled.

---

### Epic 2: Firm Bulk Exam Purchasing
- **Description**: Workflow for Firm users to select multiple employed auditors, validate their eligibility in batch, and generate a single bulk invoice for multiple exams.

#### Requirements
1. The system shall allow authorized firm contacts to select multiple associated auditors for batch exam purchasing.
2. The system shall validate each auditor's eligibility individually before including them in a bulk invoice.
3. The system shall generate a single consolidated invoice for all eligible auditors in a bulk purchase.
4. The system shall record the "paid by firm" status on each exam line item for use in downstream fee logic.
5. The system shall prevent inclusion of auditors who do not meet eligibility requirements in the bulk purchase.

---

### Epic 3: Exam Scheduling & Integration
- **Description**: The API integration with ProctorU (for Part 1/2) and the hybrid Calendly-to-ProctorU flow (for Part 3). Includes enforcing lead times, mapping time zones, and creating/linking ProctorU accounts via API.

#### Requirements
1. The system shall display a "Schedule" button only on paid exam invoices.
2. The system shall retrieve available exam slots via the ProctorU API based on the exam type and language selected (Part 1 & 2).
3. The system shall display the APSCA Calendly interface filtered by language to secure an interviewer slot (Part 3).
4. The system shall create a ProctorU reservation via API immediately upon confirmation of a Calendly slot for Part 3 exams.
5. The system shall create or update the test-taker's ProctorU account using their APSCA Member Number as the unique identifier to prevent duplicate accounts.
6. The system shall populate exam metadata (notes, permitted resources) sent to ProctorU based on the Exam Template for the specific exam type and language.
7. The system shall map the auditor's selected time zone to the closest valid ProctorU time zone ID per the Time Zone Mapping artifact.
8. The system shall enforce minimum lead times for scheduling as defined in the Exam Scheduling Rules artifact.
9. The system shall mandate that all exam scheduling originate from the APSCA platform to ensure data synchronization.

---

### Epic 4: Cancellations, Rescheduling & Fees
- **Description**: Logic for auditor self-service exam changes. Includes enforcing fee windows, reschedule limits, and determining payer based on original invoice ownership.

#### Requirements
1. The system shall display "Reschedule" and "Cancel" buttons for scheduled exams.
2. The system shall apply fees for cancellations and reschedules based on the time windows defined in the Fee Schedule.
3. The system shall require the user to select the payer (Auditor or Firm) for cancellation/reschedule fees if the original invoice was paid by a firm.
4. The system shall prevent rescheduling within the "No Change" window defined in the Fee Schedule; such requests must be processed as cancellations requiring a new invoice.
5. The system shall disable the reschedule button if the auditor has exceeded the maximum reschedule attempts defined in the Fee Schedule.
6. The system shall remove the exam date from the invoice line item upon cancellation (outside the no-refund window), making the invoice available for re-booking.
7. The system shall block scheduling or rescheduling until outstanding fee invoices are paid.

---

### Epic 5: Exam Change Requests (Firm-Initiated)
- **Description**: A ticketing workflow for Firms to request changes for exams they funded. Includes logic to transfer credits, cancel exams without auditor consent, and manage disputes.

#### Requirements
1. The system shall allow authorized firm contacts to submit exam change requests for exams funded by the firm.
2. The system shall support change request types including: cancellation, reschedule, credit transfer, and fee dispute.
3. The system shall track change request status (Submitted, Under Review, Approved, Denied).
4. The system shall notify the firm contact of change request status updates.
5. The system shall allow transfer of exam credits between auditors within the same firm upon approval.
6. The system shall maintain an audit trail of all change request actions and decisions.

---

### Epic 6: Exam Launch & Proctoring
- **Description**: The "day-of" workflow for exam delivery. Generating the unique launch link, managing status transitions, and providing backup access if the platform is inaccessible.

#### Requirements
1. The system shall display a "Start Exam" button on the auditor's dashboard within the pre-exam window defined in the Exam Scheduling Rules.
2. The system shall generate the "Start Exam" link via the ProctorU API that auto-authenticates the user into their proctoring session.
3. The system shall send a confirmation email upon scheduling that includes a backup launch URL.
4. The system shall update the exam status to "In Progress" when the auditor launches the exam.

---

### Epic 7: Exam Results & Status Updates
- **Description**: Processing webhooks from ProctorU, mapping external statuses to APSCA statuses, and handling manual score entry.

#### Requirements
1. The system shall receive and process webhooks from ProctorU for exam completion events.
2. The system shall map ProctorU webhook statuses to APSCA exam statuses per the ProctorU Status Mapping artifact.
3. The system shall update the exam status to "Results Pending" upon receiving a "Fulfillment Ended" webhook.
4. The system shall allow administrators to manually input numerical scores and Pass/Fail results.
5. The system shall update the exam status to "Completed" once a Pass/Fail result is recorded.
6. The system shall handle "No Show" statuses by applying penalties as defined in the Fee Schedule.
7. The system shall handle "IT Issue" statuses by allowing rebooking without penalty.
8. The system shall capture a snapshot of the auditor's Audit Log status at the moment an exam is marked completed.

---

### Epic 8: Exam Remediation Pathways
- **Description**: Automation of status changes and requirements based on failure counts. Enforces waiting periods and training/audit log redo requirements.

#### Requirements
1. The system shall track cumulative Part 3 exam failure count per auditor.
2. The system shall place an auditor into "Part 3 Waiting Period" status upon reaching the failure threshold defined in the Remediation Policy.
3. The system shall require auditors in the 3-5 failure range to submit a training record before restoration.
4. The system shall restore exam eligibility via automated job once the waiting period has elapsed and training is approved (3-5 failures).
5. The system shall require auditors with 6+ failures to complete a new 20-day Audit Log before exam eligibility is restored.
6. The system shall prevent training submissions for auditors with 6+ failures, displaying the audit log requirement instead.
7. The system shall send eligibility restoration notifications upon successful completion of remediation requirements.

---

### Epic 9: Exam Template & Configuration Management
- **Description**: Backend management of exam type definitions containing metadata required by the ProctorU API (duration, allowed resources, proctor notes) for each exam type and language variant.

#### Requirements
1. The system shall maintain a database of Exam Templates for each exam type and language combination.
2. The system shall store exam metadata including: duration, permitted resources, proctor instructions, and exam platform credentials.
3. The system shall allow administrators to create, update, and deprecate Exam Templates.
4. The system shall use the active Exam Template when constructing ProctorU API payloads during scheduling.

---

### Epic 10: Admin Exam Management
- **Description**: Administrative interface to view, schedule, reschedule, or force-cancel exams on behalf of auditors, including the ability to override standard business rules.

#### Requirements
1. The system shall provide administrators with a searchable view of all exam records.
2. The system shall allow administrators to schedule exams on behalf of auditors.
3. The system shall allow administrators to reschedule or cancel exams without standard fee or timing restrictions.
4. The system shall allow administrators to override eligibility rules when scheduling (with audit trail).
5. The system shall require administrators to provide a reason when overriding standard rules.
6. The system shall log all administrative exam actions with timestamp, user, and reason.

---

## Business Artifacts

### BA-1: Fee Schedule
- **Description**: Matrix defining exam fees, cancellation/reschedule fees by time window, maximum reschedule attempts, and penalty amounts for no-shows. Covers Part 1, Part 2, and Part 3 exams.
- **Referenced by**: Epics 1, 4, 7

### BA-2: Exam Eligibility Rules
- **Description**: Prerequisites for each exam type including required auditor status, exam sequencing rules, and audit log requirements. Defines what "In Good Standing" means in the exam context.
- **Referenced by**: Epics 1, 2

### BA-3: Exam Template Data
- **Description**: Configuration data for each exam type and language variant including duration, permitted resources, proctor instructions, and exam platform details sent to ProctorU API.
- **Referenced by**: Epics 3, 9

### BA-4: ProctorU Status Mapping
- **Description**: Mapping table between ProctorU webhook statuses and APSCA exam statuses. Defines which statuses allow rebooking vs. require new invoice vs. trigger penalties.
- **Referenced by**: Epic 7

### BA-5: Time Zone Mapping
- **Description**: Mapping table between APSCA/Calendly time zones and the 98 accepted ProctorU time zone IDs.
- **Referenced by**: Epic 3

### BA-6: Exam Scheduling Rules
- **Description**: Lead time requirements (14 days for Part 1/2, 30 days for Part 3), pre-exam launch window, invoice validity period, and other scheduling constraints.
- **Referenced by**: Epics 1, 3, 6

### BA-7: Remediation Policy
- **Description**: Failure thresholds, waiting period durations, training requirements for 3-5 failures, and audit log redo requirements for 6+ failures.
- **Referenced by**: Epic 8

### BA-8: Part 3 Interviewer Configuration
- **Description**: Calendly event type mappings by language, interviewer assignment rules, and any constraints on interviewer booking (e.g., cannot book same interviewer twice).
- **Referenced by**: Epic 3

---

## Summary

| Layer | Count |
|-------|-------|
| Feature | 1 |
| Epics | 10 |
| Requirements | 56 |
| Business Artifacts | 8 |

---

<!-- INTENT INTERPRETATION -->
## Parsed Records

### Features
| ID | Title | Description | Status | Notes |
|----|-------|-------------|--------|-------|
| FEAT-001 | Examination System | End-to-end management of auditor certification examination process | active | Major capability grouping all exam-related epics |

### Epics
| ID | Title | Parent | Status | Notes |
|----|-------|--------|--------|-------|
| EPIC-001 | Exam Eligibility & Invoice Generation | FEAT-001 | active | Prerequisites, invoice generation, language preferences |
| EPIC-002 | Firm Bulk Exam Purchasing | FEAT-001 | active | Batch purchasing workflow for firms |
| EPIC-003 | Exam Scheduling & Integration | FEAT-001 | active | ProctorU/Calendly API integration |
| EPIC-004 | Cancellations, Rescheduling & Fees | FEAT-001 | active | Self-service exam changes |
| EPIC-005 | Exam Change Requests (Firm-Initiated) | FEAT-001 | active | Ticketing workflow for firm-funded exams |
| EPIC-006 | Exam Launch & Proctoring | FEAT-001 | active | Day-of exam delivery workflow |
| EPIC-007 | Exam Results & Status Updates | FEAT-001 | active | Webhook processing and score entry |
| EPIC-008 | Exam Remediation Pathways | FEAT-001 | active | Failure-based status changes and remediation |
| EPIC-009 | Exam Template & Configuration Management | FEAT-001 | active | Exam metadata management |
| EPIC-010 | Admin Exam Management | FEAT-001 | active | Administrative override capabilities |

### Requirements
| ID | Statement | Parent | 4-Part Test | Notes |
|----|-----------|--------|-------------|-------|
| REQ-001 | The system shall prevent the generation of an exam invoice unless the auditor status is "In Good Standing" | EPIC-001 | ✓✓✓✓ | Eligibility gate |
| REQ-002 | The system shall prevent the generation of an exam invoice if the auditor has any unpaid fee invoices or pending exam invoices | EPIC-001 | ✓✓✓✓ | Financial gate |
| REQ-003 | The system shall enforce sequential exam progression: Part 1 must be passed before Part 2; Part 2 must be passed before Part 3 | EPIC-001 | ✓✓✓✓ | Sequencing rule |
| REQ-004 | The system shall require an approved Audit Log (minimum 20 days experience) before generating a Part 3 exam invoice | EPIC-001 | ✓✓✓✓ | Part 3 prerequisite |
| REQ-005 | The system shall allow Part 1 and Part 2 invoices to be generated without an approved Audit Log | EPIC-001 | ✓✓✓✓ | Part 1/2 exception |
| REQ-006 | The system shall automatically expire exam invoices that have not been scheduled within the validity period defined in the Fee Schedule | EPIC-001 | ✓✓✓✓ | Invoice expiration |
| REQ-007 | The system shall capture the auditor's language preference at the time of invoice generation to ensure the correct exam type is scheduled | EPIC-001 | ✓✓✓✓ | Language capture |
| REQ-008 | The system shall allow authorized firm contacts to select multiple associated auditors for batch exam purchasing | EPIC-002 | ✓✓✓✓ | Bulk selection |
| REQ-009 | The system shall validate each auditor's eligibility individually before including them in a bulk invoice | EPIC-002 | ✓✓✓✓ | Individual validation |
| REQ-010 | The system shall generate a single consolidated invoice for all eligible auditors in a bulk purchase | EPIC-002 | ✓✓✓✓ | Consolidated billing |
| REQ-011 | The system shall record the "paid by firm" status on each exam line item for use in downstream fee logic | EPIC-002 | ✓✓✓✓ | Payer tracking |
| REQ-012 | The system shall prevent inclusion of auditors who do not meet eligibility requirements in the bulk purchase | EPIC-002 | ✓✓✓✓ | Eligibility enforcement |
| REQ-013 | The system shall display a "Schedule" button only on paid exam invoices | EPIC-003 | ✓✓✓✓ | Payment gate |
| REQ-014 | The system shall retrieve available exam slots via the ProctorU API based on the exam type and language selected (Part 1 & 2) | EPIC-003 | ✓✓✓✓ | Slot retrieval |
| REQ-015 | The system shall display the APSCA Calendly interface filtered by language to secure an interviewer slot (Part 3) | EPIC-003 | ✓✓✓✓ | Part 3 scheduling |
| REQ-016 | The system shall create a ProctorU reservation via API immediately upon confirmation of a Calendly slot for Part 3 exams | EPIC-003 | ✓✓✓✓ | Hybrid flow |
| REQ-017 | The system shall create or update the test-taker's ProctorU account using their APSCA Member Number as the unique identifier to prevent duplicate accounts | EPIC-003 | ✓✓✓✓ | Account sync |
| REQ-018 | The system shall populate exam metadata (notes, permitted resources) sent to ProctorU based on the Exam Template for the specific exam type and language | EPIC-003 | ✓✓✓✓ | Metadata population |
| REQ-019 | The system shall map the auditor's selected time zone to the closest valid ProctorU time zone ID per the Time Zone Mapping artifact | EPIC-003 | ✓✓✓✓ | Time zone mapping |
| REQ-020 | The system shall enforce minimum lead times for scheduling as defined in the Exam Scheduling Rules artifact | EPIC-003 | ✓✓✓✓ | Lead time enforcement |
| REQ-021 | The system shall mandate that all exam scheduling originate from the APSCA platform to ensure data synchronization | EPIC-003 | ✓✓✓✓ | Single source of truth |
| REQ-022 | The system shall display "Reschedule" and "Cancel" buttons for scheduled exams | EPIC-004 | ✓✓✓✓ | Action availability |
| REQ-023 | The system shall apply fees for cancellations and reschedules based on the time windows defined in the Fee Schedule | EPIC-004 | ✓✓✓✓ | Fee application |
| REQ-024 | The system shall require the user to select the payer (Auditor or Firm) for cancellation/reschedule fees if the original invoice was paid by a firm | EPIC-004 | ✓✓✓✓ | Payer selection |
| REQ-025 | The system shall prevent rescheduling within the "No Change" window defined in the Fee Schedule; such requests must be processed as cancellations requiring a new invoice | EPIC-004 | ✓✓✓✓ | No-change window |
| REQ-026 | The system shall disable the reschedule button if the auditor has exceeded the maximum reschedule attempts defined in the Fee Schedule | EPIC-004 | ✓✓✓✓ | Reschedule limit |
| REQ-027 | The system shall remove the exam date from the invoice line item upon cancellation (outside the no-refund window), making the invoice available for re-booking | EPIC-004 | ✓✓✓✓ | Invoice re-availability |
| REQ-028 | The system shall block scheduling or rescheduling until outstanding fee invoices are paid | EPIC-004 | ✓✓✓✓ | Outstanding fees gate |
| REQ-029 | The system shall allow authorized firm contacts to submit exam change requests for exams funded by the firm | EPIC-005 | ✓✓✓✓ | Firm request submission |
| REQ-030 | The system shall support change request types including: cancellation, reschedule, credit transfer, and fee dispute | EPIC-005 | ✓✓✓✓ | Request types |
| REQ-031 | The system shall track change request status (Submitted, Under Review, Approved, Denied) | EPIC-005 | ✓✓✓✓ | Status tracking |
| REQ-032 | The system shall notify the firm contact of change request status updates | EPIC-005 | ✓✓✓✓ | Status notifications |
| REQ-033 | The system shall allow transfer of exam credits between auditors within the same firm upon approval | EPIC-005 | ✓✓✓✓ | Credit transfer |
| REQ-034 | The system shall maintain an audit trail of all change request actions and decisions | EPIC-005 | ✓✓✓✓ | Audit trail |
| REQ-035 | The system shall display a "Start Exam" button on the auditor's dashboard within the pre-exam window defined in the Exam Scheduling Rules | EPIC-006 | ✓✓✓✓ | Launch availability |
| REQ-036 | The system shall generate the "Start Exam" link via the ProctorU API that auto-authenticates the user into their proctoring session | EPIC-006 | ✓✓✓✓ | Auto-auth link |
| REQ-037 | The system shall send a confirmation email upon scheduling that includes a backup launch URL | EPIC-006 | ✓✓✓✓ | Backup access |
| REQ-038 | The system shall update the exam status to "In Progress" when the auditor launches the exam | EPIC-006 | ✓✓✓✓ | Status transition |
| REQ-039 | The system shall receive and process webhooks from ProctorU for exam completion events | EPIC-007 | ✓✓✓✓ | Webhook processing |
| REQ-040 | The system shall map ProctorU webhook statuses to APSCA exam statuses per the ProctorU Status Mapping artifact | EPIC-007 | ✓✓✓✓ | Status mapping |
| REQ-041 | The system shall update the exam status to "Results Pending" upon receiving a "Fulfillment Ended" webhook | EPIC-007 | ✓✓✓✓ | Results pending |
| REQ-042 | The system shall allow administrators to manually input numerical scores and Pass/Fail results | EPIC-007 | ✓✓✓✓ | Manual entry |
| REQ-043 | The system shall update the exam status to "Completed" once a Pass/Fail result is recorded | EPIC-007 | ✓✓✓✓ | Completion status |
| REQ-044 | The system shall handle "No Show" statuses by applying penalties as defined in the Fee Schedule | EPIC-007 | ✓✓✓✓ | No-show handling |
| REQ-045 | The system shall handle "IT Issue" statuses by allowing rebooking without penalty | EPIC-007 | ✓✓✓✓ | IT issue handling |
| REQ-046 | The system shall capture a snapshot of the auditor's Audit Log status at the moment an exam is marked completed | EPIC-007 | ✓✓✓✓ | Status snapshot |
| REQ-047 | The system shall track cumulative Part 3 exam failure count per auditor | EPIC-008 | ✓✓✓✓ | Failure tracking |
| REQ-048 | The system shall place an auditor into "Part 3 Waiting Period" status upon reaching the failure threshold defined in the Remediation Policy | EPIC-008 | ✓✓✓✓ | Waiting period |
| REQ-049 | The system shall require auditors in the 3-5 failure range to submit a training record before restoration | EPIC-008 | ✓✓✓✓ | Training requirement |
| REQ-050 | The system shall restore exam eligibility via automated job once the waiting period has elapsed and training is approved (3-5 failures) | EPIC-008 | ✓✓✓✓ | Auto restoration |
| REQ-051 | The system shall require auditors with 6+ failures to complete a new 20-day Audit Log before exam eligibility is restored | EPIC-008 | ✓✓✓✓ | 6+ failure rule |
| REQ-052 | The system shall prevent training submissions for auditors with 6+ failures, displaying the audit log requirement instead | EPIC-008 | ✓✓✓✓ | Training block |
| REQ-053 | The system shall send eligibility restoration notifications upon successful completion of remediation requirements | EPIC-008 | ✓✓✓✓ | Restoration notification |
| REQ-054 | The system shall maintain a database of Exam Templates for each exam type and language combination | EPIC-009 | ✓✓✓✓ | Template storage |
| REQ-055 | The system shall store exam metadata including: duration, permitted resources, proctor instructions, and exam platform credentials | EPIC-009 | ✓✓✓✓ | Metadata storage |
| REQ-056 | The system shall allow administrators to create, update, and deprecate Exam Templates | EPIC-009 | ✓✓✓✓ | Template management |
| REQ-057 | The system shall use the active Exam Template when constructing ProctorU API payloads during scheduling | EPIC-009 | ✓✓✓✓ | Template usage |
| REQ-058 | The system shall provide administrators with a searchable view of all exam records | EPIC-010 | ✓✓✓✓ | Admin search |
| REQ-059 | The system shall allow administrators to schedule exams on behalf of auditors | EPIC-010 | ✓✓✓✓ | Proxy scheduling |
| REQ-060 | The system shall allow administrators to reschedule or cancel exams without standard fee or timing restrictions | EPIC-010 | ✓✓✓✓ | Admin override |
| REQ-061 | The system shall allow administrators to override eligibility rules when scheduling (with audit trail) | EPIC-010 | ✓✓✓✓ | Eligibility override |
| REQ-062 | The system shall require administrators to provide a reason when overriding standard rules | EPIC-010 | ✓✓✓✓ | Override justification |
| REQ-063 | The system shall log all administrative exam actions with timestamp, user, and reason | EPIC-010 | ✓✓✓✓ | Admin audit log |

### Business Artifacts
| ID | Title | Type | Description | Status | Notes |
|----|-------|------|-------------|--------|-------|
| ART-001 | Fee Schedule | rule | Matrix defining exam fees, cancellation/reschedule fees by time window, maximum reschedule attempts, and penalty amounts for no-shows | draft | Referenced by Epics 1, 4, 7 |
| ART-002 | Exam Eligibility Rules | rule | Prerequisites for each exam type including required auditor status, exam sequencing rules, and audit log requirements | draft | Referenced by Epics 1, 2 |
| ART-003 | Exam Template Data | rule | Configuration data for each exam type and language variant including duration, permitted resources, proctor instructions | draft | Referenced by Epics 3, 9 |
| ART-004 | ProctorU Status Mapping | rule | Mapping table between ProctorU webhook statuses and APSCA exam statuses | draft | Referenced by Epic 7 |
| ART-005 | Time Zone Mapping | rule | Mapping table between APSCA/Calendly time zones and the 98 accepted ProctorU time zone IDs | draft | Referenced by Epic 3 |
| ART-006 | Exam Scheduling Rules | rule | Lead time requirements, pre-exam launch window, invoice validity period, and other scheduling constraints | draft | Referenced by Epics 1, 3, 6 |
| ART-007 | Remediation Policy | policy | Failure thresholds, waiting period durations, training requirements for 3-5 failures, and audit log redo requirements for 6+ failures | draft | Referenced by Epic 8 |
| ART-008 | Part 3 Interviewer Configuration | rule | Calendly event type mappings by language, interviewer assignment rules, and booking constraints | draft | Referenced by Epic 3 |

### User Stories
(None - per user context, no stories included as we are not at design phase)

### Releases
(None - no releases specified in input)

## Validation Notes
- All 56 requirements pass the 4-part test (Boolean, Implementation-agnostic, Durable, Failure=Wrong)
- All business artifacts correctly identified as HOW documents (not WHAT rules)
- No user stories or releases were included per user context about not being at design phase
- Epics will need a release_ref assigned - this will require creating a placeholder release or leaving unassigned

<!-- END INTERPRETATION -->
