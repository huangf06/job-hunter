# Data Scientist Resume Template Design

**Date:** 2026-04-07
**Status:** Approved

## Problem

The ML template currently catches "data scientist" roles but positions the candidate as "ML Engineer / Data Scientist" with emphasis on PyTorch, Deep RL, and model deployment. For analytics-heavy DS roles (e.g., Polarsteps "Data Scientist Growth Analytics"), this positioning is wrong.

## Solution

Add a dedicated DS template entry in `config/template_registry.yaml` with analytics-first positioning. No code changes needed — the routing system is already generic.

## Changes

### 1. New DS entry in template_registry.yaml

- `target_roles`: data scientist, data analyst, analytics, experimentation, statistical
- `bio_positioning`: "Data Scientist"
- Bio leads with statistical modeling, A/B testing, feature engineering
- Experience: GLP (feature eng + decision engine), BQ (statistical modeling), Ele.me (anomaly detection + A/B testing + query optimization)
- Projects: Expedia (LTR), IMU Sensor or Thesis
- Skills: statistical testing first, PyTorch/Deep RL deprioritized, Tableau added

### 2. ML template cleanup

Remove `data scientist` and `data analyst` from ML's `target_roles`.

### 3. SVG/PDF

Deferred — no SVG/PDF yet. DS roles will route through ADAPT_TEMPLATE or FULL_CUSTOMIZE paths.
