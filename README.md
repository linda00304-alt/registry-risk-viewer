> **Notice:** This service is an educational text-parsing tool and does not constitute legal advice or formal document review. Always consult a licensed attorney (변호사) or certified real estate broker (공인중개사) before signing contracts.

**Status:** Step 0 done (environment + first screen). Next: Week 1 PDF parsing. Development log: [`report/00_intro.md`](report/00_intro.md)

---

# Registry Risk Viewer (Open-Source Edition)

Final Term Project Design Specification & Technical Architecture

| **Item**       | **Detail**                                                                                                                                |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Project Title  | Registry Risk Viewer (Legal-Tech: AI-Powered Property Registry Risk Analysis & Visual Markup Platform)                                    |
| Author / Track | Legal Studies & Legal-Tech Track                                                                                                          |
| Target Stack   | Streamlit Community Cloud, Python 3.11+, PyMuPDF (fitz), Anthropic Claude API (optional; model name set by configuration), GitHub Actions |
| Version        | Draft v0.3 (Open-Source Legal Grounding Edition), revised from v0.2                                                                       |
| Date           | November 3, 2026                                                                                                                          |

## Revision Notes (v0.2 → v0.3)

| **\#** | **Section**       | **Change**                                                                                                                                                                                                                   |
|--------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1      | 2.2 Rule A2       | Trigger corrected from 'R ≥ 0.70 or R ≥ 0.80' to 'R ≥ 0.70'. Yellow for 0.70 ≤ R \< 0.80; Red for R ≥ 0.80.                                                                                                                  |
| 2      | Target Stack, 1.3 | Hard-coded model name 'claude-3-5-sonnet' removed. The model name is now a configuration value (ANTHROPIC_MODEL in Secrets). The LLM remains optional and never makes risk decisions.                                        |
| 3      | 2.2 Rule A11      | Lookup now selects the table row by Date_Pivot (earliest security-right registration), not by the current date. Current table and previous table (2021-05-11 to 2023-02-20) added. Verification status updated in Section 4. |
| 4      | Section 4         | Two court-case citations (A9, B2) moved to \[Unverified\] until the case numbers are checked against the primary source.                                                                                                     |
| 5      | Formatting        | Stray text artifacts ('None') removed; formulas written in plain text.                                                                                                                                                       |

## 1. System Overview & Open-Stack Architecture

### 1.1 Overview & Problem Statement

First-time renters (such as university students and young adults) frequently struggle to interpret official Korean Property Registries (등기사항전부증명서). These 4-to-8 page documents contain dense legal jargon and complex historical encumbrances (근저당권, 가압류, 가등기, 신탁).

The Registry Risk Viewer is an open-source, interactive web application that parses uploaded PDF registries, runs a deterministic Python rule engine grounded in South Korean civil and housing statutes, and presents a dual-pane UI:

- Left Pane: a visual document viewer rendering color-coded highlights (Red = High Risk, Yellow = Caution, Gray = Cancelled/Informational) over flagged clauses.

- Right Pane: an interactive panel with a Deposit Safety Bar, filter controls, and plain-language explanation cards mapped to statutory references.

### 1.2 System Principles

1.  Deterministic Legal Reasoning: the LLM does not decide legal risks or calculate financial ratios. All risk logic is executed by an auditable Python rule engine.

2.  Absolute Non-Commerciality & Educational Disclaimer: in line with Article 109 of the Attorney-at-Law Act (변호사법), the tool never issues definitive verdicts (e.g., 'Safe to sign' or 'Unsafe'). Green/Safe badges are strictly prohibited.

3.  Zero-Persistence Privacy: document text, extracted bounding boxes, and calculated deposit metrics exist only within the active browser session (st.session_state) and are purged upon tab closure or explicit deletion.

4.  Graceful Fallback (No-Key Demo Mode): if API keys are unconfigured or external dependencies fail, the app falls back to pre-parsed synthetic sample registries.

### 1.3 High-Level System Architecture

<table>
<colgroup>
<col style="width: 27%" />
<col style="width: 72%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Layer</strong></th>
<th><strong>Components</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Visitor Browser</td>
<td>Uploaded PDF and deposit inputs → Streamlit UI (split screen: page viewer with highlight overlay + explanation cards).</td>
</tr>
<tr class="even">
<td>Streamlit Community Cloud (Python runtime)</td>
<td><p>1. Ingestion &amp; Validation: PDF stream → memory buffer (PyMuPDF / fitz).</p>
<p>2. Document Segmentation: 표제부 (Title) / 갑구 (Ownership) / 을구 (Encumbrance).</p>
<p>3. Entry Parser &amp; Cancelled-Line Detector: strike-through bounding-box mapping.</p>
<p>4. Deterministic Rule Engine (Groups A–D): Python statutory logic.</p>
<p>5. Card &amp; Glossary Mapping: local JSON/YAML static content library.</p></td>
</tr>
<tr class="odd">
<td>Anthropic Claude API (optional)</td>
<td>Format mapping and plain-language glossary Q&amp;A under a strict JSON schema. Model name read from configuration.</td>
</tr>
<tr class="even">
<td>GitHub Repository / Actions</td>
<td>Static code and rule configs; automated Pytest verification.</td>
</tr>
</tbody>
</table>

## 2. Deterministic Rule Engine Logic (Draft v0.3)

All risk logic is governed by deterministic Python functions. Below are the specifications, formulas, thresholds, and statutory grounds for Groups A through D.

### 2.1 Pre-Processing & Timeline Normalization

1.  Normalization: parse each entry into Entry(id, section, rank_no, receipt_date, purpose, cause, holder, amount, status: ACTIVE \| CANCELLED, bboxes).

2.  Extinguishment Pivot (말소기준권리): identify the earliest receipt_date among all active 근저당권 (mortgage), 압류 (seizure), 가압류 (provisional seizure), and 경매개시결정 (auction commencement order), per Civil Execution Act Art. 91(2). This date is called Date_Pivot.

3.  Lease Timeline Placement: calculate the tenant's Opposition Power (대항력) date as planned move-in report (전입신고) date + 1 day at 00:00 KST (Housing Lease Protection Act Art. 3(1)).

4.  Senior Claims Sum (S): S = Σ active maximum secured amounts (채권최고액) + Σ senior lease deposits (선순위 전세금 / 임차권등기).

5.  Deposit Risk Ratio (R): R = (S + D) / V, where D = user deposit amount and V = user-entered property market value.

### 2.2 Group A: Civil Act, Civil Execution Act, & Housing Lease Protection Act

| **ID** | **Trigger Condition**                       | **Legal Basis**                                                            | **Severity**                                           | **Formula / Calculation**                                                                                                                   | **Action & Output**                                                                                                        |
|--------|---------------------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| A1     | Active 근저당권설정 in Eul-gu               | Civil Act Art. 357, 186; Civil Execution Act Art. 91(2)                    | Yellow (Caution)                                       | Extract 채권최고액 (maximum secured amount) and add to senior claims S.                                                                     | Card explains that 채권최고액 is typically about 120%–130% of the actual loan. Prompts confirmation with the lender.       |
| A2     | Risk ratio R ≥ 0.70                         | Housing Lease Protection Act Art. 3-2(2); Civil Act Art. 357               | Yellow (0.70 ≤ R \< 0.80) / Red (R ≥ 0.80)             | R = (S + D) / V. Yellow if 0.70 ≤ R \< 0.80; Red if R ≥ 0.80.                                                                               | Deposit Safety Bar fills dynamically. Red flag warns of potential deposit loss in foreclosure.                             |
| A3     | Active 경매개시결정 in Gap-gu               | Civil Execution Act Art. 83(1), 91; Housing Lease Protection Act Art. 8(1) | Red (High Risk)                                        | Boolean: purpose contains 경매개시결정.                                                                                                     | Immediate high-risk alert. Explains that leases made after the auction registration lose priority repayment rights.        |
| A4     | Active 압류 or 체납처분압류 in Gap-gu       | Civil Execution Act Art. 83, 91(3); National Tax Collection Act Art. 24    | Red (High Risk)                                        | Boolean: purpose contains 압류 or tax-office seizure.                                                                                       | Warns that a government body or creditor has an enforcement lock; a public auction may follow.                             |
| A5     | Active 가압류 in Gap-gu                     | Civil Execution Act Art. 276, 91(3)                                        | Red (High Risk)                                        | Boolean: purpose contains 가압류.                                                                                                           | Highlights a monetary-claim freeze prior to forced sale.                                                                   |
| A6     | Active 가처분 (e.g., 처분금지) in Gap-gu    | Civil Execution Act Art. 300                                               | Red (High Risk)                                        | Boolean: purpose contains 가처분.                                                                                                           | Warns of a pending ownership or disposition dispute.                                                                       |
| A7     | Active 전세권설정 preceding lease date      | Civil Act Art. 303; Civil Execution Act Art. 91(4)                         | Yellow (Red if R ≥ 0.80)                               | Check receipt_date \< Lease Date. Add 보증금 to S.                                                                                          | Senior leasehold claim; paid before the user in auction unless waived.                                                     |
| A8     | Active 지상권 or 지역권                     | Civil Act Art. 279, 291; Civil Execution Act Art. 91(3)                    | Yellow (Caution)                                       | Boolean check. Flag as informational if a mortgage exists (담보지상권).                                                                     | Land-use restrictions that survive auction.                                                                                |
| A9     | Active 환매특약 in Gap-gu                   | Civil Act Art. 590, 591, 592                                               | Red (High Risk), if within the 5-year statutory period | Check registration date + 5 years against the current date.                                                                                 | Seller's repurchase right can extinguish later-registered claims upon exercise (case citation: see Section 4, Unverified). |
| A10    | Active 임차권등기명령 in Eul-gu             | Housing Lease Protection Act Art. 3-3                                      | Red (High Risk)                                        | Boolean trigger. Add registered amount to S.                                                                                                | Flags that a prior tenant was not refunded their deposit upon moving out.                                                  |
| A11    | Small-Tenant Eligibility Check (소액임차인) | Housing Lease Protection Act Art. 8; Enforcement Decree Art. 10, 11        | Informational (No Color)                               | Select the table row by Date_Pivot (the extinguishment pivot date, 2.1 step 2), NOT the lease date. Check D ≤ deposit limit for the region. | Displays the maximum priority repayment amount (최우선변제금). Does not guarantee recovery. See lookup tables below.       |
| A12    | Timing & Compliance Checklist               | Housing Lease Protection Act Art. 3, 3-2                                   | Informational (No Color)                               | Always rendered in summary view.                                                                                                            | Checklist for 전입신고, 확정일자, occupancy maintenance, and demand for distribution (배당요구).                           |

**Statutory Lookup Tables for Rule A11 (select by Date_Pivot)**

The small-tenant ceiling and priority amount depend on the enforcement decree in force on the Date_Pivot, not on the lease date or today's date. The engine therefore stores each table with its effective period and picks the matching one.

**Table A11-1: Date_Pivot on or after 2023-02-21 (current)**

| **Region**                                                                                                | **Deposit limit (D ≤)** | **Priority repayment cap** |
|-----------------------------------------------------------------------------------------------------------|-------------------------|----------------------------|
| Seoul Special City                                                                                        | 165,000,000 KRW         | 55,000,000 KRW             |
| Overcrowded Control Region (excl. Seoul) / Sejong / Yongin / Hwaseong / Gimpo                             | 145,000,000 KRW         | 48,000,000 KRW             |
| Metropolitan Cities (excl. Overcrowded Control Region), plus Ansan / Gwangju / Paju / Icheon / Pyeongtaek | 85,000,000 KRW          | 28,000,000 KRW             |
| Other regions                                                                                             | 75,000,000 KRW          | 25,000,000 KRW             |

**Table A11-2: Date_Pivot from 2021-05-11 to 2023-02-20 (previous)**

| **Region**                                                                                         | **Deposit limit (D ≤)** | **Priority repayment cap** |
|----------------------------------------------------------------------------------------------------|-------------------------|----------------------------|
| Seoul Special City                                                                                 | 150,000,000 KRW         | 50,000,000 KRW             |
| Overcrowded Control Region (excl. Seoul) / Sejong / Yongin / Hwaseong                              | 130,000,000 KRW         | 43,000,000 KRW             |
| Metropolitan Cities (excl. Overcrowded), plus Ansan / Gwangju / Paju / Icheon / Pyeongtaek / Gimpo | 70,000,000 KRW          | 23,000,000 KRW             |
| Other regions                                                                                      | 60,000,000 KRW          | 20,000,000 KRW             |

Fallback: if Date_Pivot is earlier than 2021-05-11 or cannot be determined, the app shows 'Reference table not available for this date. Please check the decree in force on the pivot date.' and does not display a number. The cap is also limited to one half of the sale proceeds of the house (Housing Lease Protection Act Art. 8(3)); the card states this limit.

*Source note: the Seoul rows of both tables were cross-checked against secondary 2026 articles. The non-Seoul rows and the regional group definitions must be checked against the decree text on law.go.kr before the status changes to \[Verified\] (see Section 4).*

### 2.3 Group B: Act on Ownership and Management of Buildings (집합건물법)

| **ID** | **Trigger Condition**                                                  | **Legal Basis**                                                                          | **Severity**                                                               | **Logic & Handling**                                                                             |
|--------|------------------------------------------------------------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| B1     | Pyojebeu shows no Land Right (대지권 미등기) for a multi-unit property | Act on Ownership & Management of Buildings Art. 20; Real Estate Registration Act Art. 61 | Yellow (Caution)                                                           | Parse Pyojebeu. Trigger if property type is 집합건물 and 대지권의 표시 is missing or unrecorded. |
| B2     | Pyojebeu contains a note on separate land registration (토지별도등기)  | Act on Ownership & Management of Buildings Art. 20 (supporting case law: see Section 4)  | Yellow (prompt to upload land registry) / Red (if land encumbrances exist) | Scan Pyojebeu text for the string 토지별도등기있음.                                              |
| B3     | Joint collateral (공동담보) listed across multiple units               | Act on Ownership & Management of Buildings Art. 21; Civil Act Art. 368                   | Yellow (Caution)                                                           | Scan Eul-gu for 공동담보 references.                                                             |

### 2.4 Group C: Act on Security by Provisional Registration (가등기담보법)

| **ID** | **Trigger Condition**                                     | **Legal Basis**                                              | **Severity**    | **Logic & Handling**                                                                          |
|--------|-----------------------------------------------------------|--------------------------------------------------------------|-----------------|-----------------------------------------------------------------------------------------------|
| C1     | Active 소유권이전청구권가등기 in Gap-gu                   | Real Estate Registration Act Art. 88, 91, 92                 | Red (High Risk) | Parse Gap-gu for an active 가등기.                                                            |
| C2     | Provisional registration treated as security (담보가등기) | Act on Security by Provisional Registration Art. 2, 3, 4, 12 | Red (High Risk) | Evaluated alongside C1. Treat as mortgage-equivalent with settlement restrictions (청산기간). |
| C3     | Cause contains 매매예약 or 대물변제예약                   | Act on Security by Provisional Registration Art. 1, 2        | Red (High Risk) | Keyword matching in registration cause (등기원인).                                            |

### 2.5 Group D: Act on Real Estate Real-Name Registration (부동산실명법)

| **ID** | **Trigger Condition**                                                                     | **Legal Basis**                                           | **Severity**             | **Logic & Handling**                                                                              |
|--------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------|--------------------------|---------------------------------------------------------------------------------------------------|
| D1     | Lessor name input differs from Gap-gu current owner, or lessor is an agent                | Civil Act Art. 186, 114; Real-Name Act Art. 3, 4          | Red (High Risk)          | Compare UserInputs.lessor_name with Gap-gu.current_owner_name.                                    |
| D2     | User indicates the lessor claims to be the 'Real Owner' while registered under a relative | Real Estate Real-Name Registration Act Art. 3(1), 4(1)    | Red (High Risk)          | Input toggle check on lessor relationship.                                                        |
| D3     | Indirect indicators: recent title transfer + non-resident address                         | Real Estate Real-Name Registration Act Art. 3(1)          | Yellow (Question Prompt) | Flag if title transfer occurred within 12 months AND owner address differs from property address. |
| D4     | Registered trust (신탁등기) in Gap-gu                                                     | Trust Act Art. 2, 4; Real Estate Registration Act Art. 81 | Red (High Risk)          | Parse Gap-gu for 신탁.                                                                            |

## 3. Data Storage, Privacy Rules & Key Protection

### 3.1 Zero-Persistence Data Pipeline

- No Database Architecture: the application operates strictly without SQL/NoSQL databases.

- In-Memory Volatility: Streamlit processes PDF streams directly in RAM via io.BytesIO. Bounding-box coordinates and extracted text reside exclusively in st.session_state.

- Session Purge: closing the browser tab, clicking 'Delete My Data Now', or idling beyond the 12-hour Streamlit container reset purges all active session variables.

### 3.2 Secrets & Key Protection

- Environment Isolation: API keys (ANTHROPIC_API_KEY) and the model name (ANTHROPIC_MODEL) are managed strictly via .streamlit/secrets.toml locally and the Streamlit Cloud Secrets Manager in production.

- Version Control Exclusion: .gitignore explicitly includes .streamlit/secrets.toml, .env, and all PDF test samples.

- Sanitized Error Logging: exception handlers intercept raw traces to prevent leaking document snippets or API request parameters into public error logs.

## 4. Verification Labels (Auditability Matrix)

All external technical assertions and legal references are categorized by verification level. Status changes only after the check is actually done and recorded in the report.

| **Label**      | **Item**                                                               | **Status / Basis**                                                                                             |
|----------------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| \[Verified\]   | PyMuPDF bbox extraction                                                | Verified via local Python 3.11 execution.                                                                      |
| \[Verified\]   | Streamlit session memory & 12-hour container reset                     | Verified via Streamlit Cloud official documentation.                                                           |
| \[Verified\]   | Attorney-at-Law Act Art. 109                                           | Verified via statute text and legal news summaries.                                                            |
| \[Reported\]   | A11 Seoul row (165M / 55M since 2023-02-21; 150M / 50M before)         | Consistent across several secondary 2026 articles (checked Nov 2026). Primary decree text still to be checked. |
| \[Reported\]   | A11 non-Seoul rows and regional group definitions                      | Secondary summaries only. Previous-table non-Seoul values need primary check.                                  |
| \[Reported\]   | HUG guarantee limits (90% valuation rule)                              | Secondary real-estate guides (2026).                                                                           |
| \[Unverified\] | Supreme Court 2000Da27411 (cited for A9)                               | Case number to be checked against the court database.                                                          |
| \[Unverified\] | Supreme Court 2025Da218240 (cited for B2)                              | Case number and holding to be checked against the court database.                                              |
| \[Unverified\] | Exact vector-line strike-through parsing in complex registries         | Handled via fallback user-confirmation prompts.                                                                |
| \[Unverified\] | Land registry note wording (토지별도등기있음) across regional variants | Needs sample check.                                                                                            |
| \[Unverified\] | Rule logic as a whole                                                  | Requires practitioner review before any production deployment.                                                 |

## 5. 4-Week Implementation Roadmap, Milestones & Test Plan

*Week 1: PDF Ingestion & Parsing → Week 2: Statutory Rule Engine → Week 3: Split-Screen UI → Week 4: Hardening & Test*

### 5.1 Weekly Milestones

| **Week**                                    | **Deliverable**                                                                                            | **Exit Check**                                                                                   |
|---------------------------------------------|------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| 1: Document Parsing & Coordinate Extraction | Python module using PyMuPDF to parse PDF registries into JSON with page numbers and word bounding boxes.   | ≥ 90% parsing accuracy on 15 test PDF samples.                                                   |
| 2: Rule Engine & Legal Card Integration     | Rule Groups A–D and Deposit Safety Bar math.                                                               | 100% match between automated rule outputs and hand-labeled test answers.                         |
| 3: Streamlit Interface & Dual-Pane Sync     | Split-screen Streamlit app rendering PDF page previews with highlight overlays synced to right-pane cards. | A test user can go from PDF upload to reviewing a flagged risk clause without external guidance. |
| 4: Hardening, Verification & Deployment     | Session auto-delete validation, Streamlit Cloud deployment, automated Pytest via GitHub Actions.           | Zero key exposure; all 30+ unit tests pass.                                                      |

### 5.2 Automated Testing Strategy (Pytest)

1.  Mock Ingestion Test: verifies that the parsing pipeline processes sample JSON without external network access.

2.  Rule Engine Unit Tests: evaluates synthetic entries against Groups A–D (e.g., an R = 0.85 calculation must trigger Rule A2 Red).

3.  A11 Table Selection Test: Date_Pivot of 2022-06-01 must use Table A11-2; 2024-01-01 must use Table A11-1; 2020-01-01 must trigger the fallback message.

4.  Privacy Canary Test: injects a unique string into input fields and verifies its complete absence from logs and disk storage after session reset.

## 6. Legal Compliance Guidelines (Attorney-at-Law Act Art. 109)

1.  No Legal Consultation / Representation: the platform is positioned as an educational document-reading assistant and checklist parser.

2.  Strict Non-Commerciality: 100% free of charge with no ad revenue, paid tiers, or affiliate lawyer referral fees.

3.  Prohibition of 'Safe' Claims: the UI never presents green badges, safety scores, or phrases such as 'Safe contract' or 'Low risk'. Clean documents are labeled: 'No items matched our automated statutory checklist. This does not guarantee safety.'

4.  Mandatory Disclaimer: every analysis view persistently displays: 'Notice: This service is an educational text-parsing tool and does not constitute legal advice or formal document review. Always consult a licensed attorney (변호사) or certified real estate broker (공인중개사) before signing contracts.'

