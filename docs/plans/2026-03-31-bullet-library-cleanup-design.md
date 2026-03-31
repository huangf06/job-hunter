# Bullet Library Cleanup & Narrative Enforcement

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve resume narrative coherence by enforcing recommended_sequences, cleaning up bullet library noise, and preparing for ML template human review.

**Architecture:** No structural redesign. The current template_registry + bullet_library architecture is correct. Changes are: (1) prompt enforcement, (2) content pruning, (3) human review preparation.

**Tech Stack:** YAML config changes, prompt text edits. No code changes.

---

## Action 1: Make recommended_sequences binding in C2 prompt

**Files:**
- Modify: `config/ai_config.yaml` (C2 tailor prompt, narrative composition rules)

Change the recommended_sequences instruction from advisory to mandatory:
- Old: "If a RECOMMENDED SEQUENCE is shown for a section, follow that ordering"
- New: "If a RECOMMENDED SEQUENCE exists for this role type, you MUST use exactly those bullets in that order. Do not cherry-pick, reorder, or substitute. You may OMIT the last bullet(s) if space is tight, but the remaining bullets must stay in sequence order. If no sequence matches the target role, fall back to narrative_role ordering."

## Action 2: Clean up bullet library

**Files:**
- Modify: `assets/bullet_library.yaml`
- Modify: `config/ai_config.yaml` (project_keys list)

### 2a: Remove all deprecated bullets
Delete deprecated bullet entries that are already marked but still present in the file.

### 2b: Remove B.Eng thesis project entirely
Delete the `bsc_thesis` project section (5 bullets: bsc_java_production, bsc_data_pipeline_sql, bsc_security_rbac, bsc_domain_modeling, bsc_testing_monitoring). 2010 Java/SQL Server project has zero relevance to 2026 Data/AI roles.

### 2c: Remove deprecated project entries
Delete `evolutionary_robotics_legacy` (replaced by evolutionary_robotics_research).
Delete `deribit_options` reference if still in project_keys.

### 2d: Reduce optional bullets
For each company and project, keep at most 1 optional bullet. Remove the least impactful optional bullets.

## Action 3: Verify Backend template narrative coherence

**Files:**
- Review: `config/template_registry.yaml` Backend section

Check that GLP title "Software Engineer & Team Lead" and Ele.me title "Software Engineer" are defensible title variants, and that the bio + bullets tell a coherent story.

## Action 4: Prepare ML template for human review

**Files:**
- Read: `templates/Fei_Huang_ML_Resume.svg`
- Read: `config/template_registry.yaml` ML section

Present ML template content in readable format, highlight differences from DE template, flag potential issues for user review.
