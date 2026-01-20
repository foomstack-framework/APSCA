<!-- CONTEXT -->
This document contains the ten remaining features that are not yet in the system, along with some epics that apply to those features.

---

# APSCA Remaining Features Scaffold

This document outlines the 10 remaining Features (Examination System already completed) with known Epics identified through RFP analysis, discovery call transcripts, and discussion. Requirements and Business Artifacts are TBD for workshop elaboration.

---

## Feature 2: Auditor Lifecycle Management

**Description**: Management of an auditor's journey from enrollment through certification, including status automation, level progression, and lapse/restoration logic.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Enrollment & Onboarding** | Firm submits new auditor, admin review, member number assignment, login activation. Visibility rules during draft/pending states. |
| 2 | **Employment Management** | Auditor-firm associations, active/inactive employments, visibility permissions, duplicate prevention, disassociation workflows. |
| 3 | **Audit Log Submission** | Auditor submits individual audit activity records (dates, firm, country, standard). Progress tracking toward 20-day requirement. Date collision blocking, 5-year age limit, 10-day cap on second-party audits. |
| 4 | **Audit Log Verification** | Firm supervisor approval workflow. Per-entry approve/reject. External delegate verification via unique links. Confidentiality masking for third-party audits. |
| 5 | **Status Automation** | Rules engine for automatic status transitions (e.g., unpaid fees → lapsed, lapsed > 24 months → expired). Daily/weekly cron jobs. |
| 6 | **Level Progression** | ASCA → CSCA transition upon Part 3 pass. Level assignment, certificate generation, digital ID updates. |
| 7 | **Lapse & Expiration** | Logic for membership lapse triggers (unpaid invoices, unsigned FOA, CPD non-compliance). Expiration after extended lapse period. |
| 8 | **Status Restoration** | Checklist-based restoration (pay fees, sign FOA, complete CPD). Automated status update upon checklist completion. |

### Known Business Artifacts
- Auditor Status Definitions (status names, transitions, triggers)
- Audit Log Validation Rules (age limits, day caps, eligible standards)
- Enrollment Checklist
- Lapse/Restoration Checklist

---

## Feature 3: CPD Management

**Description**: Tracking and enforcement of Continuing Professional Development requirements for certified auditors, including course submissions, approvals, and annual compliance.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **CPD Submission & Tracking** | Auditors submit CPD records (course, hours, date). Progress visualization toward annual requirement. |
| 2 | **Firm CPD Approval** | Firm supervisors review and approve auditor CPD submissions. |
| 3 | **Training Course Recognition** | Firms submit courses for APSCA recognition. Admin review workflow. Public/private course designation. Badge generation upon approval. |
| 4 | **Annual CPD Compliance** | Year-end compliance check. Status impacts (lapse trigger if non-compliant). CPD override for auditors who passed exams in current year. |
| 5 | **CPD Reporting** | Dashboards showing compliance rates, submissions pending review, auditor progress. |

### Known Business Artifacts
- CPD Requirements Policy (hours required, eligible categories, compliance period)
- Approved Training Courses List
- CPD Badge Templates

---

## Feature 4: Financial Management

**Description**: Invoicing, payment processing, and financial integration for exam fees, membership fees, and firm reporting fees.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Invoice Generation** | Creation of invoices for exams, membership, cancellation fees, etc. Line item management. |
| 2 | **Payment Processing** | Stripe integration for credit card payments. Payment status tracking. Receipt generation. |
| 3 | **QuickBooks Integration** | Two-way sync of invoices, payments, and customer records with QuickBooks Online. |
| 4 | **Firm Self-Invoicing** | Firms report monthly audit totals and auto-generate their own invoices based on per-audit fee. |
| 5 | **Anomaly Detection** | Flagging of unusual self-reported figures (e.g., significantly lower than historical average). |
| 6 | **Bulk Credits & Drawdown** | Firms pay lump sums; individual auditor fees draw down from credit balance. |
| 7 | **Membership Fee Processing** | Annual membership fee invoicing. Inactive member discounts. Fee waivers and adjustments. |

### Known Business Artifacts
- Fee Schedule (all fee types, amounts, conditions)
- QuickBooks Account Mapping
- Anomaly Detection Thresholds

---

## Feature 5: User Identity & Access Control

**Description**: Authentication, authorization, and role management for all platform users.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Authentication & MFA** | Login flow, multi-factor authentication, password reset, session management. |
| 2 | **Role-Based Access Control** | Role definitions (Auditor, Firm Contact, Firm Supervisor, Admin, etc.). Permission matrices. |
| 3 | **Multi-Role Management** | Users with multiple roles (e.g., auditor who is also firm contact). Role toggle within platform. |
| 4 | **Role-Specific Redirects** | Dashboard routing based on active role. Homepage assignment per role. |
| 5 | **Profile Validation** | Required fields enforcement (e.g., country of residence before exam scheduling). Profile completeness checks. |

### Known Business Artifacts
- Role Definitions & Permissions Matrix
- Required Profile Fields by User Type
- MFA Configuration

---

## Feature 6: Membership Management

**Description**: Management of firm and individual membership status, categories, agreements, and annual renewals.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Firm Membership Status** | Active, suspended, terminated states. Status change workflows. |
| 2 | **Individual Membership Status** | Auditor membership tiers and states (Provisional, Full, Lapsed, Expired). |
| 3 | **Member Categories** | Firm categorization (A/B/C). Category assignment and change logic. |
| 4 | **Agreements & Consent Tracking** | Form of Acceptance, Code of Conduct, Confidentiality Framework. Signature tracking, expiration, renewal. |
| 5 | **Annual Renewal Processing** | Yearly renewal workflow. FOA signature requirement. Fee generation. Status updates. |

### Known Business Artifacts
- Membership Status Definitions
- Member Category Criteria
- Agreement Templates (FOA, Code of Conduct, etc.)
- Renewal Checklist

---

## Feature 7: Firm Profile Management

**Description**: Firm self-service capabilities for profile management, auditor associations, and accreditation tracking.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Firm Profile Updates** | Self-service editing of firm details (logo, contact info, website, addresses). |
| 2 | **Auditor Association Management** | View associated auditors. Manage employment relationships. Access restrictions on PII for active/disassociated auditors. |
| 3 | **Accreditation Management** | Programs/brands the firm is accredited for (SMETA, BSCI, Disney, etc.). Self-service updates. |
| 4 | **Geographic Coverage** | Countries/regions where firm conducts audits. Self-service updates. |
| 5 | **Embeddable Public Lists** | Auto-updating HTML embeds for public website (member firm lists, accredited programs). |

### Known Business Artifacts
- Accreditation Program List
- Country/Region Taxonomy
- Public List Embed Configuration

---

## Feature 8: Reporting & Analytics

**Description**: Dashboards, reports, and data visualization for internal stakeholders and external data sharing.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Real-Time Dashboards** | Live views of key metrics (auditor counts by level/region, exam pass rates, CPD compliance). |
| 2 | **Geographic Visualizations** | Map-based displays of auditor capacity by country. Interactive filtering. |
| 3 | **Custom Report Builder** | Admin ability to create ad-hoc reports from available data sets. |
| 4 | **Metabase Integration** | Connection to Metabase for advanced analytics and visualization. |
| 5 | **Progress Tracking Visualizations** | Visual progress bars for audit log, CPD, certification journey. Color-coded status indicators. |

### Known Business Artifacts
- Dashboard Metric Definitions
- Standard Report Templates
- Metabase Connection Configuration

---

## Feature 9: Data Governance & Security

**Description**: Data protection, audit trails, retention policies, and system security.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Audit Trail & Logging** | Record of all status changes, data modifications, admin actions. Timestamp, user, before/after values. |
| 2 | **Data Encryption** | Encryption at rest and in transit. Key management. |
| 3 | **Data Retention & Archiving** | Retention policies by data category. Archival process. Secure deletion at end-of-life. |
| 4 | **Backup & Recovery** | Automated backups. Disaster recovery procedures. Restore testing. |
| 5 | **Incident Response** | Security monitoring. Failed login detection. Breach response procedures. |
| 6 | **Email Deliverability** | SendGrid authentication. CNAME/SPF/DKIM configuration. Spam filter avoidance. |

### Known Business Artifacts
- Data Retention Policy
- Backup Schedule & Recovery SLAs
- Incident Response Playbook
- Email Authentication Records

---

## Feature 10: External Integrations & APIs

**Description**: Integrations with external systems and APIs for partner data exchange and public information publishing.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Partner Verification API** | REST API for partners (Sedex, BSCI) to verify auditor/firm status in real-time. Replaces manual CSV uploads. |
| 2 | **LMS Integration** | Data exchange with Learning Management System for exam scheduling, CPD course completion, training records. |
| 3 | **Public Register Embeds** | Auto-updating public website content (member firm list, recognized training courses, certified auditors). |
| 4 | **ZenDesk Integration** | Knowledge base widget. Role-specific article display. Support ticket creation. |

### Known Business Artifacts
- API Authentication & Rate Limiting Rules
- Partner API Data Schema
- LMS Data Mapping
- Public Register Configuration

---

## Feature 11: Ethics & Compliance

**Description**: Management of ethics cases and compliance monitoring workflows.

### Known Epics

| # | Epic | Scope |
|---|------|-------|
| 1 | **Ethics Case Management** | TBD — requires dedicated discovery |
| 2 | **Compliance Data Tracking** | TBD — requires dedicated discovery |

### Known Business Artifacts
- TBD — sparse information in current sources

**Note**: This feature requires dedicated discovery sessions to define epics and requirements. Current sources mention ethics and compliance data exists but do not detail the workflows.

---

## Summary

| Feature | Epics Identified | Status |
|---------|------------------|--------|
| Examination System | 10 | ✅ Complete (separate document) |
| Auditor Lifecycle Management | 8 | Scaffolded |
| CPD Management | 5 | Scaffolded |
| Financial Management | 7 | Scaffolded |
| User Identity & Access Control | 5 | Scaffolded |
| Membership Management | 5 | Scaffolded |
| Firm Profile Management | 5 | Scaffolded |
| Reporting & Analytics | 5 | Scaffolded |
| Data Governance & Security | 6 | Scaffolded |
| External Integrations & APIs | 4 | Scaffolded |
| Ethics & Compliance | 2 (TBD) | Needs Discovery |

**Total**: 11 Features, 62 Epics identified (excluding Examination System's 10)

<!-- INTENT INTERPRETATION -->
## Parsed Records

### Features
| ID | Title | Status | Notes |
|----|-------|--------|-------|
| FEAT-NEW-001 | Auditor Lifecycle Management | draft | Management of auditor journey from enrollment through certification |
| FEAT-NEW-002 | CPD Management | draft | Continuing Professional Development tracking and enforcement |
| FEAT-NEW-003 | Financial Management | draft | Invoicing, payment processing, and financial integration |
| FEAT-NEW-004 | User Identity & Access Control | draft | Authentication, authorization, and role management |
| FEAT-NEW-005 | Membership Management | draft | Firm and individual membership status, agreements, renewals |
| FEAT-NEW-006 | Firm Profile Management | draft | Firm self-service capabilities and accreditation tracking |
| FEAT-NEW-007 | Reporting & Analytics | draft | Dashboards, reports, and data visualization |
| FEAT-NEW-008 | Data Governance & Security | draft | Data protection, audit trails, retention policies |
| FEAT-NEW-009 | External Integrations & APIs | draft | External system integrations and partner APIs |
| FEAT-NEW-010 | Ethics & Compliance | draft | Ethics cases and compliance monitoring (needs discovery) |

### Epics

#### Auditor Lifecycle Management (FEAT-NEW-001)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-001 | Enrollment & Onboarding | FEAT-NEW-001 | TBD | draft | Firm submits new auditor, admin review, member number assignment |
| EPIC-NEW-002 | Employment Management | FEAT-NEW-001 | TBD | draft | Auditor-firm associations, visibility permissions |
| EPIC-NEW-003 | Audit Log Submission | FEAT-NEW-001 | TBD | draft | Individual audit activity records submission and tracking |
| EPIC-NEW-004 | Audit Log Verification | FEAT-NEW-001 | TBD | draft | Firm supervisor approval workflow |
| EPIC-NEW-005 | Status Automation | FEAT-NEW-001 | TBD | draft | Rules engine for automatic status transitions |
| EPIC-NEW-006 | Level Progression | FEAT-NEW-001 | TBD | draft | ASCA to CSCA transition upon Part 3 pass |
| EPIC-NEW-007 | Lapse & Expiration | FEAT-NEW-001 | TBD | draft | Membership lapse triggers and expiration logic |
| EPIC-NEW-008 | Status Restoration | FEAT-NEW-001 | TBD | draft | Checklist-based restoration workflow |

#### CPD Management (FEAT-NEW-002)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-009 | CPD Submission & Tracking | FEAT-NEW-002 | TBD | draft | Auditor CPD record submission and progress visualization |
| EPIC-NEW-010 | Firm CPD Approval | FEAT-NEW-002 | TBD | draft | Firm supervisor review and approval of CPD |
| EPIC-NEW-011 | Training Course Recognition | FEAT-NEW-002 | TBD | draft | Firm course submission for APSCA recognition |
| EPIC-NEW-012 | Annual CPD Compliance | FEAT-NEW-002 | TBD | draft | Year-end compliance check and status impacts |
| EPIC-NEW-013 | CPD Reporting | FEAT-NEW-002 | TBD | draft | Compliance dashboards and progress tracking |

#### Financial Management (FEAT-NEW-003)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-014 | Invoice Generation | FEAT-NEW-003 | TBD | draft | Invoice creation for exams, membership, fees |
| EPIC-NEW-015 | Payment Processing | FEAT-NEW-003 | TBD | draft | Stripe integration and receipt generation |
| EPIC-NEW-016 | QuickBooks Integration | FEAT-NEW-003 | TBD | draft | Two-way sync with QuickBooks Online |
| EPIC-NEW-017 | Firm Self-Invoicing | FEAT-NEW-003 | TBD | draft | Firms report monthly audit totals |
| EPIC-NEW-018 | Anomaly Detection | FEAT-NEW-003 | TBD | draft | Flagging unusual self-reported figures |
| EPIC-NEW-019 | Bulk Credits & Drawdown | FEAT-NEW-003 | TBD | draft | Lump sum payments with credit balance drawdown |
| EPIC-NEW-020 | Membership Fee Processing | FEAT-NEW-003 | TBD | draft | Annual membership fee invoicing and adjustments |

#### User Identity & Access Control (FEAT-NEW-004)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-021 | Authentication & MFA | FEAT-NEW-004 | TBD | draft | Login flow, MFA, password reset, session management |
| EPIC-NEW-022 | Role-Based Access Control | FEAT-NEW-004 | TBD | draft | Role definitions and permission matrices |
| EPIC-NEW-023 | Multi-Role Management | FEAT-NEW-004 | TBD | draft | Users with multiple roles and role toggle |
| EPIC-NEW-024 | Role-Specific Redirects | FEAT-NEW-004 | TBD | draft | Dashboard routing based on active role |
| EPIC-NEW-025 | Profile Validation | FEAT-NEW-004 | TBD | draft | Required fields enforcement and completeness checks |

#### Membership Management (FEAT-NEW-005)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-026 | Firm Membership Status | FEAT-NEW-005 | TBD | draft | Active, suspended, terminated states |
| EPIC-NEW-027 | Individual Membership Status | FEAT-NEW-005 | TBD | draft | Auditor membership tiers and states |
| EPIC-NEW-028 | Member Categories | FEAT-NEW-005 | TBD | draft | Firm categorization (A/B/C) |
| EPIC-NEW-029 | Agreements & Consent Tracking | FEAT-NEW-005 | TBD | draft | FOA, Code of Conduct signature tracking |
| EPIC-NEW-030 | Annual Renewal Processing | FEAT-NEW-005 | TBD | draft | Yearly renewal workflow and fee generation |

#### Firm Profile Management (FEAT-NEW-006)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-031 | Firm Profile Updates | FEAT-NEW-006 | TBD | draft | Self-service editing of firm details |
| EPIC-NEW-032 | Auditor Association Management | FEAT-NEW-006 | TBD | draft | View and manage employment relationships |
| EPIC-NEW-033 | Accreditation Management | FEAT-NEW-006 | TBD | draft | Programs/brands firm is accredited for |
| EPIC-NEW-034 | Geographic Coverage | FEAT-NEW-006 | TBD | draft | Countries/regions where firm conducts audits |
| EPIC-NEW-035 | Embeddable Public Lists | FEAT-NEW-006 | TBD | draft | Auto-updating HTML embeds for public website |

#### Reporting & Analytics (FEAT-NEW-007)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-036 | Real-Time Dashboards | FEAT-NEW-007 | TBD | draft | Live views of key metrics |
| EPIC-NEW-037 | Geographic Visualizations | FEAT-NEW-007 | TBD | draft | Map-based displays of auditor capacity |
| EPIC-NEW-038 | Custom Report Builder | FEAT-NEW-007 | TBD | draft | Admin ad-hoc report creation |
| EPIC-NEW-039 | Metabase Integration | FEAT-NEW-007 | TBD | draft | Connection to Metabase for advanced analytics |
| EPIC-NEW-040 | Progress Tracking Visualizations | FEAT-NEW-007 | TBD | draft | Visual progress bars and status indicators |

#### Data Governance & Security (FEAT-NEW-008)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-041 | Audit Trail & Logging | FEAT-NEW-008 | TBD | draft | Record of all status changes and data modifications |
| EPIC-NEW-042 | Data Encryption | FEAT-NEW-008 | TBD | draft | Encryption at rest and in transit |
| EPIC-NEW-043 | Data Retention & Archiving | FEAT-NEW-008 | TBD | draft | Retention policies and secure deletion |
| EPIC-NEW-044 | Backup & Recovery | FEAT-NEW-008 | TBD | draft | Automated backups and disaster recovery |
| EPIC-NEW-045 | Incident Response | FEAT-NEW-008 | TBD | draft | Security monitoring and breach response |
| EPIC-NEW-046 | Email Deliverability | FEAT-NEW-008 | TBD | draft | SendGrid authentication and spam avoidance |

#### External Integrations & APIs (FEAT-NEW-009)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-047 | Partner Verification API | FEAT-NEW-009 | TBD | draft | REST API for partner status verification |
| EPIC-NEW-048 | LMS Integration | FEAT-NEW-009 | TBD | draft | Data exchange with Learning Management System |
| EPIC-NEW-049 | Public Register Embeds | FEAT-NEW-009 | TBD | draft | Auto-updating public website content |
| EPIC-NEW-050 | ZenDesk Integration | FEAT-NEW-009 | TBD | draft | Knowledge base widget and support tickets |

#### Ethics & Compliance (FEAT-NEW-010)
| ID | Title | Parent | Release | Status | Notes |
|----|-------|--------|---------|--------|-------|
| EPIC-NEW-051 | Ethics Case Management | FEAT-NEW-010 | TBD | draft | TBD - requires dedicated discovery |
| EPIC-NEW-052 | Compliance Data Tracking | FEAT-NEW-010 | TBD | draft | TBD - requires dedicated discovery |

### Requirements
No requirements in this input - document indicates "Requirements and Business Artifacts are TBD for workshop elaboration."

### Business Artifacts
The document references known Business Artifacts but does not provide specifications - marked as TBD:
- Auditor Status Definitions
- Audit Log Validation Rules
- Enrollment Checklist
- Lapse/Restoration Checklist
- CPD Requirements Policy
- Approved Training Courses List
- CPD Badge Templates
- Fee Schedule (already exists as ART-001)
- QuickBooks Account Mapping
- Anomaly Detection Thresholds
- Role Definitions & Permissions Matrix
- Required Profile Fields by User Type
- MFA Configuration
- Membership Status Definitions
- Member Category Criteria
- Agreement Templates
- Renewal Checklist
- Accreditation Program List
- Country/Region Taxonomy
- Public List Embed Configuration
- Dashboard Metric Definitions
- Standard Report Templates
- Metabase Connection Configuration
- Data Retention Policy
- Backup Schedule & Recovery SLAs
- Incident Response Playbook
- Email Authentication Records
- API Authentication & Rate Limiting Rules
- Partner API Data Schema
- LMS Data Mapping
- Public Register Configuration

### User Stories
None identified in this input.

### Releases
None identified in this input.

## Validation Notes
- **No release assigned**: Epics do not have release_ref specified. Integration will require a release to be created or assigned.
- **Feature 11 (Ethics & Compliance)**: Marked as needing dedicated discovery - epics are placeholders only.
- **No Requirements captured**: Document explicitly states requirements are TBD for workshop elaboration.
- **Business Artifacts referenced but not specified**: Multiple artifacts mentioned but lack detailed specifications.
- **ID Mapping**: FEAT-NEW-001 through FEAT-NEW-010 will map to FEAT-002 through FEAT-011 based on existing FEAT-001.
- **Epic Mapping**: EPIC-NEW-001 through EPIC-NEW-052 will map to EPIC-011 through EPIC-062 based on existing EPIC-001 through EPIC-010.

<!-- END INTERPRETATION -->
