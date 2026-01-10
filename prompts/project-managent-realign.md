**Role:** You are a Senior Technical Project Manager and Lead Software Architect.

**Objective:** Your goal is to re-align the user's codebase with their documentation, identify "Scope Extensions," and provide a professional SDE performance audit.

**Instructions:**
I am providing you with my current codebase and my original requirements/specs (which are now outdated) below. I have been coding without updating the specs, resulting in "documentation drift."

Please perform a **Project Realignment & Audit** by executing the following four steps:

**Phase 1: The Truth Reconciliation (Reverse Engineering)**

* Analyze the code to understand the *current* reality of the system.
* Compare this against the "Original Specs" provided below.
* **Action:** Create a list of discrepancies.
* **Action:** Identify features present in the code but missing from the spec. Label these as **"Scope Extensions."**

**Phase 2: SDE Performance Report**
Based on standard software industry metrics, audit the current implementation:

* **Completeness:** What percentage of the *original* core requirements are fully implemented?
* **Code Quality & Architecture:** Are the recent refactors clean and Pythonic? Is the architecture simpler or more complex than the original design?
* **Scope Extension Value:** Briefly summarize the "Scope Extensions" and their apparent utility/value to the project.

**Phase 3: Documentation Sync (The "Living Doc")**
Rewrite the project documentation to match the current code.

* **Constraint:** Do not make it "cumbersome." Keep requirements behavior-focused (High-Level).
* **Format:** Output updated Markdown specs that reflect the current code reality.
* **Future-Proofing:** For the "Scope Extensions," generate new requirements sections that define them clearly to help with future implementation.

**Phase 4: The Roadmap Check**

* Based on the code state, what is the logical next step?
* Are there any "Zombie Tasks" in the original list that I should officially delete because the architecture has changed?

---

### **Project Context & Data**

**[PART 1: ORIGINAL SPECS & REQUIREMENTS]**
*(Paste your Markdown files, old requirements, or task lists here)*
`.kiro/specs/spyfall-arena-phase-one/requirements.md`
`requirements/requirements-phase-one.md`
`requirements/requirements-project-overview.md`
`README.md`

**[PART 2: CURRENT CODEBASE]**
*(Paste your file tree, critical code files, or Git diffs here)*
`/src`
`/tests`

**[PART 3: ADDITIONAL NOTES]**
*(Optional: Paste any recent informal notes, daily thoughts, or specific focus areas)*
Export this report to the /prompts/project-management/phase-one-report.md