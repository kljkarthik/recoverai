# RecoverAI — Autonomous Revenue Recovery Agent

> **Razorpay AI Buildathon — Track 03: AI Revenue Recovery**

RecoverAI is an autonomous revenue recovery agent that detects revenue at risk from failed payments and payment/checkout failures, diagnoses the root cause, selects an appropriate bounded recovery action, executes the action within deterministic safety rules, and measures the revenue recovered.

---

## 📌 Problem Statement

Merchants lose revenue when payment failures, checkout abandonment, and recurring payment failures are not recovered intelligently. Standard recovery mechanisms rely on static retry schedules or generic notifications, which fail to adapt to bank processing errors, customer intent, or payment gateway dynamics, leading to unrecovered revenue and high customer friction.

---

## 💡 Planned Solution Lifecycle

RecoverAI automates the end-to-end revenue recovery lifecycle through a 7-step process:

$$\text{Detect} \longrightarrow \text{Diagnose} \longrightarrow \text{Decide} \longrightarrow \text{Policy Check} \longrightarrow \text{Act} \longrightarrow \text{Measure} \longrightarrow \text{Audit}$$

1. **Detect:** Real-time ingestion of payment failures and abandoned checkout telemetry.
2. **Diagnose:** Root-cause analysis classifying decline codes, network errors, or user behavior.
3. **Decide:** LLM-driven recommendation of the optimal recovery strategy.
4. **Policy Check:** Verification against deterministic safety rules (guardrails).
5. **Act:** Autonomous execution of bounded actions (smart retry, alternate payment link, customer outreach).
6. **Measure:** Tracking recovery outcomes, conversion rates, and net revenue saved.
7. **Audit:** Immutable logging of all agent evaluations, policy checks, and execution trails.

---

## 🛡️ Core Architecture Principle: AI & Safety Engine Separation

> [!IMPORTANT]  
> **Deterministic Safety First:** The LLM agent generates recommendations, but a deterministic **Policy & Safety Engine** decides whether an action is allowed. The AI is strictly bounded and can **never** bypass safety rules, maximum retry limits, discount caps, or escalation thresholds.

---

## 🎯 Planned Recovery Scenarios

1. **Failed Payment Recovery:** Adaptive re-routing or payment link generation upon soft or hard payment declines.
2. **Temporary Payment Degradation / Retry:** Intelligent scheduling of retry attempts during bank outages or gateway slowdowns.
3. **Checkout Abandonment Recovery:** Personalized recovery prompts dispatched to recover high-intent abandoned checkouts.
4. **Failed Subscription Recovery:** Automated dunning and subscription renewal recovery for recurring billing failures.
5. **High-Value or Uncertain Escalations:** Automated routing of high-value transactions or low-confidence cases to human-in-the-loop manual review.

---

## 📊 Evaluation & Metrics (Planned)

The project will use **synthetic transaction data** for benchmarking and evaluation, using **Razorpay Test Mode** for payment lifecycle simulations. Key metrics to be tracked include:

- **Revenue at Risk:** Total monetary value associated with payment failures and abandoned checkouts.
- **Recovery Attempts:** Number of recovery workflows initiated by the agent.
- **Successful Recoveries:** Count of completed transactions following intervention.
- **Recovery Rate:** Percentage of revenue successfully recovered relative to revenue at risk.
- **Revenue Recovered:** Net monetary amount recovered for the merchant.
- **Audit Trail Integrity:** 100% decision traceability for every automated action.

---

## 🛠️ Technology Stack

- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS
- **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy / AsyncPG
- **Database:** PostgreSQL 16 (Relational state & audit logging)
- **Containerization:** Docker & Docker Compose
- **Integrations (Planned):** Razorpay API & Webhooks (Test Mode), AI Agent & Policy Engine

---

## 🚀 Development Roadmap

> [!NOTE]  
> **Current Status:** Phase 0 complete. All integration components, LLM reasoning logic, Razorpay webhooks, and automation pipelines described above are planned features for upcoming phases.

- [x] **Phase 0: Project Foundation** — Repository structure, initial configs, architecture documentation.
- [ ] **Phase 1: Core Backend & Database Infrastructure** — FastAPI setup, PostgreSQL schema, event schemas, data generator.
- [ ] **Phase 2: Autonomous Recovery Agent & Safety Engine** — LLM strategy recommendations, policy guardrails, audit logging.
- [ ] **Phase 3: Razorpay Test Mode Integration** — Webhook listener, payment link creation, synthetic evaluation benchmark pipeline.
- [ ] **Phase 4: Frontend Control Dashboard** — Next.js UI for metrics, recovery logs, and manual escalation queue.
- [ ] **Phase 5: Benchmarking, Testing & Verification** — End-to-end evaluation, failure simulations, project presentation.

---

## 📁 Repository Structure

```
recoverai/
├── README.md               # Project overview and specifications
├── .gitignore              # Multi-language Git ignore configuration
├── .env.example            # Environment variables placeholder template
├── docker-compose.yml      # Container orchestration for local PostgreSQL
├── frontend/               # Next.js frontend application (Phase 4)
├── backend/                # FastAPI backend application (Phase 1)
├── data/                   # Data directory for synthetic benchmarks
│   ├── raw/                # Raw transaction logs and payloads
│   └── processed/          # Processed analytics and benchmark datasets
├── scripts/                # Utility and simulation scripts
├── tests/                  # Test suite
└── docs/                   # Extended project design documents
    └── architecture.md     # High-level architecture specification
```

---

## 📄 License

Submitted for the **Razorpay AI Buildathon — Track 03: AI Revenue Recovery**.
