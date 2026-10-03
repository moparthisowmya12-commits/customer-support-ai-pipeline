## Multilingual Customer Support AI & Ticket Automation Pipeline

An enterprise-grade Customer Support AI pipeline developed as part of the ElevanceSkills Data Science Internship program. This repository integrates real-time sentiment analysis, dynamic response tone adaptation, automated ticket extraction, priority/SLA evaluation, and intelligent agent routing.

---

## 📌 Features & Core Modules

### Task 1: Multilingual Sentiment Analysis & Escalation Engine
- **Multi-Class Sentiment Detection:** Classifies incoming messages into `positive`, `neutral`, `negative`, `frustrated`, `urgent`, and `sarcastic`.
- **Dynamic Tone Adaptation:** Empathetically adjusts chatbot response prefixes without violating underlying business policies.
- **Automated Escalation Triggers:** Escalates high-risk conditions including account compromise, duplicate payments, and legal threats.
- **Time-Aware Routing:** Routes urgent after-hours complaints to an on-call queue and standard complaints to the next working day. Automatically escalates negative conversations unresolved for >15 minutes.

### Task 2: Ticket Workflow, SLA Counter & Agent Routing Engine
- **Entity Extraction & Masking:** Extracts Order IDs, emails, phone numbers, and issue categories while masking sensitive PII (`***@domain.com`) for agent handoffs.
- **Mandatory Field Verification:** Detects missing mandatory information (Order ID, Contact Email) and pauses ticket creation to request clarification.
- **SLA & Priority Engine:** Calculates priority levels (P1 to P4) based on severity, sentiment, and impact. SLA tracking excludes configured weekends and holidays, generating warnings at 75% consumption.
- **Duplicate Detection & Grouping:** Groups related issues under existing open tickets and flags duplicate requests.
- **Workload-Aware Agent Routing:** Matches incoming tickets to agents based on skills, availability, and active workload.

---

## 📁 Repository Structure

```text
elevanceskills-ai-support-chatbot/
│
├── task1_sentiment_escalation/
│   ├── sentiment_engine.py       # Task 1 Sentiment & Escalation Module
│   └── task1_project_report.md   # Task 1 Technical Documentation
│
├── task2_ticket_workflow/
│   ├── ticket_engine.py          # Task 2 Support Ticket & SLA Engine
│   └── task2_project_report.md   # Task 2 Technical Documentation
│
├── app.py                        # Consolidated Main Pipeline Application
├── requirements.txt              # Python Dependencies
└── README.md                     # Project Overview & Execution Guide
