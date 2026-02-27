# Strike7 Multi-Model Benchmark Comparison System

**Project:** Multi-Model AI Agent Benchmarking & Intelligence Layer  
**Author:** Atheeque  
**Date:** February 2026  
**Status:** PLANNING  
**Related:** PIL (Predictive Intelligence Layer), Strike7 Pentest Engine, Strike7 Agent Activity Feed  

---

## 1. EXECUTIVE SUMMARY

### What Are We Building?

A system that runs Strike7's existing benchmark challenges against multiple LLM providers and model tiers, collects structured performance data (time, tokens, steps, cost, success rate), displays real-time comparison results on the Strike7 Agent Activity Feed dashboard, stores intelligence data for consumption by both PIL and the Strike7 pentest engine's model-swapping feature, and generates comparison reports.

### Why This Matters

**Evidence from initial tests (Image 1 — Agent Activity Feed):**
- Same benchmarks run with two different models showed dramatic timing differences
- S7BEN-EASY-001: 59.3s (Attempt 1, Gemini) vs 1136.0s (Attempt 2, Claude) — **~19x slower**
- S7BEN-HARD-023: 89.9s (Attempt 1) vs 210.5s (Attempt 2) — **~2.3x slower**

**Evidence from JWT Forgery comparison (Image 2 — Model Comparison Chart):**
- Gemini 3 Flash: ~15s, ~3K tokens, ~5 steps
- Claude Opus 4.6: ~100s, ~200K tokens, ~30 steps
- Claude Sonnet 4.5: ~115s, ~75K tokens, ~15 steps
- Grok 3 Latest: ~40s, ~10K tokens, ~5 steps

**Key insight:** Lower-tier, cheaper models can outperform expensive flagship models on specific task categories. This has massive implications for:
1. **Strike7 Pentest Engine** — Intelligent model routing per sub-agent and task type
2. **PIL** — Training data for cost/time optimization models
3. **Cost reduction** — Avoiding token waste when a Flash model solves it in 3K tokens vs Opus at 200K

### Referenced Resources
- **KryptSec/OASIS** (github.com/KryptSec/oasis) — Similar multi-model benchmarking for security tasks; reference for methodology and visualization
- **LinkedIn article by Arafat Ansari** — Open-source AI security benchmarking approaches; demonstrates community validation of this concept

---

## 2. SCOPE — MODELS TO BENCHMARK

### Phase 1: Core Three Providers (Initial Implementation)

| Provider | Models | Tier Classification |
|----------|--------|-------------------|
| **Google (Gemini)** | Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 2.0 Flash | Budget, Mid, Flash |
| **Anthropic (Claude)** | Claude Haiku 4.5, Claude Sonnet 4.5, Claude Opus 4.6 | Budget, Mid, Flagship |
| **OpenAI (Codex/GPT)** | GPT-4.1 mini, GPT-4.1, o3-mini, o4-mini | Budget, Mid, Reasoning |

> **Note:** Model names above reflect what's available as of the knowledge cutoff. Verify exact model strings and availability before implementation. The system should be provider-agnostic and easily extensible for new models.

### Phase 2: Extended (Future)

| Provider | Models | Notes |
|----------|--------|-------|
| **xAI (Grok)** | Grok 3, Grok 3 Mini | Already tested in JWT Forgery comparison |
| **Mistral** | Mistral Large, Codestral | European provider, potentially good for compliance |
| **DeepSeek** | DeepSeek V3, DeepSeek R1 | Cost-efficient reasoning |

### Tier Classification System

Each model gets classified into a tier for routing intelligence:

```
TIER 1 — FLASH/MINI:    Fastest, cheapest, limited reasoning
TIER 2 — STANDARD:      Balanced speed/capability
TIER 3 — PRO/FLAGSHIP:  Maximum capability, highest cost
TIER 4 — REASONING:     Extended thinking, specialized tasks
```

---

## 3. METRICS TO COLLECT

### Primary Metrics (Per Benchmark Run)

| Metric | Description | Unit | Why It Matters |
|--------|-------------|------|----------------|
| **time_to_flag** | Wall-clock time from benchmark start to flag capture | Seconds | Speed comparison |
| **total_tokens** | Input + output tokens consumed | Integer | Cost driver |
| **input_tokens** | Prompt/input tokens | Integer | Context efficiency |
| **output_tokens** | Completion/output tokens | Integer | Verbosity indicator |
| **steps_taken** | Number of tool calls / iterations | Integer | Approach efficiency |
| **cost_usd** | Calculated cost based on provider pricing | Float | Direct cost comparison |
| **flag_captured** | Whether the flag was successfully captured | Boolean | Success/failure |
| **error_type** | If failed: timeout, loop, wrong approach, API error | Enum | Failure analysis |

### Derived Metrics (Calculated Post-Run)

| Metric | Formula | What It Tells You |
|--------|---------|-------------------|
| **pass@k** | `1 - (1 - p)^k` | Capability: Can this model solve this at all? |
| **pass^k** | `p^k` | Reliability: Does it work every time? |
| **tokens_per_second** | `total_tokens / time_to_flag` | Processing throughput |
| **cost_per_flag** | `cost_usd` (only successful runs) | Cost efficiency |
| **efficiency_score** | `min_steps / actual_steps × 100` | How direct was the approach? |
| **loop_detection_rate** | `loops_detected / total_runs` | Tendency to get stuck |
| **consistency_score** | `std_dev(time_to_flag) / mean(time_to_flag)` | How predictable is performance? |

### Aggregate Metrics (Cross-Model)

| Metric | Description |
|--------|-------------|
| **best_model_per_difficulty** | Which model wins at EASY/MED/HARD/VHARD/CVE |
| **best_model_per_vuln_type** | Which model wins at SQLi/XSS/AuthBypass/etc. |
| **cost_efficiency_ranking** | Sorted by cost_per_flag across all benchmarks |
| **reliability_matrix** | pass^k for each model × each benchmark |

---

## 4. BENCHMARK TEST MATRIX

### Minimum Coverage for Meaningful Comparison

Run **at least 2 benchmarks per difficulty tier** across **all models**:

```
                    EASY    MED     HARD    VHARD   CVE
                    ────    ───     ────    ─────   ───
Gemini Flash        ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
Gemini Pro          ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
Claude Haiku        ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
Claude Sonnet       ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
Claude Opus         ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
GPT-4.1 mini        ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
GPT-4.1             ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
o3-mini             ✓✓      ✓✓      ✓✓      ✓✓      ✓✓
```

**Minimum:** 8 models × 5 tiers × 2 benchmarks × 2 attempts (for pass@k) = **160 runs**

### Recommended: Statistical Significance

For reliable pass@k and pass^k calculations: **k=5 attempts per model per benchmark**

8 models × 10 benchmarks × 5 attempts = **400 runs**

### Run Strategy

```
Phase A — Quick Sweep (1-2 days):
  - 1 benchmark per tier × all models × 1 attempt
  - Purpose: Quick capability map, identify obvious failures
  - Runs: ~40

Phase B — Deep Comparison (3-5 days):
  - 2 benchmarks per tier × all models × 3 attempts
  - Purpose: Reliable metrics, identify patterns
  - Runs: ~240

Phase C — Statistical Validation (ongoing):
  - Same as Phase B but k=5 with targeted reruns on interesting findings
  - Purpose: Publishable data, PIL training set
  - Runs: ~400+
```

---

## 5. DATA SCHEMA — STORAGE DESIGN

### 5.1 Primary Table: `model_benchmark_runs`

```sql
CREATE TABLE model_benchmark_runs (
    -- Identity
    run_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Benchmark Info
    benchmark_id        VARCHAR(50) NOT NULL,          -- e.g., "S7BEN-EASY-001"
    benchmark_name      VARCHAR(200),                   -- e.g., "Basic SQL Injection"
    difficulty_tier     VARCHAR(10) NOT NULL,           -- EASY, MED, HARD, VHARD, CVE
    vuln_category       VARCHAR(50),                    -- sqli, xss, auth_bypass, ssrf, etc.
    owasp_category      VARCHAR(10),                    -- A01, A02, ..., A10
    
    -- Model Info
    provider            VARCHAR(20) NOT NULL,           -- google, anthropic, openai, xai
    model_id            VARCHAR(100) NOT NULL,          -- exact API model string
    model_display_name  VARCHAR(100),                   -- human-readable name
    model_tier          VARCHAR(20),                    -- flash, standard, pro, reasoning
    
    -- Results
    flag_captured       BOOLEAN NOT NULL DEFAULT FALSE,
    flag_value          VARCHAR(200),                   -- the actual flag (for verification)
    time_to_flag_s      FLOAT,                          -- seconds to capture (NULL if failed)
    total_duration_s    FLOAT NOT NULL,                 -- total run duration including cleanup
    attempt_number      INTEGER NOT NULL DEFAULT 1,     -- which attempt (for pass@k)
    
    -- Token Metrics
    total_tokens        INTEGER,
    input_tokens        INTEGER,
    output_tokens       INTEGER,
    
    -- Step Metrics
    steps_taken         INTEGER,                        -- total tool calls / iterations
    http_requests_made  INTEGER,                        -- requests to target
    unique_endpoints    INTEGER,                        -- distinct paths hit
    
    -- Cost
    cost_usd            FLOAT,                          -- calculated from provider pricing
    
    -- Failure Analysis (if flag_captured = FALSE)
    failure_reason      VARCHAR(50),                    -- timeout, loop, wrong_approach, api_error, crash
    failure_details     TEXT,                            -- detailed error message
    loop_detected       BOOLEAN DEFAULT FALSE,
    loop_count          INTEGER DEFAULT 0,
    
    -- Metadata
    container_port      INTEGER,
    run_config          JSONB,                          -- any special config (temperature, etc.)
    agent_transcript    TEXT,                            -- full agent reasoning/tool call log
    
    -- Indexes
    CONSTRAINT valid_tier CHECK (difficulty_tier IN ('EASY', 'MED', 'HARD', 'VHARD', 'CVE')),
    CONSTRAINT valid_provider CHECK (provider IN ('google', 'anthropic', 'openai', 'xai', 'mistral', 'deepseek'))
);

-- Performance indexes
CREATE INDEX idx_mbr_benchmark ON model_benchmark_runs(benchmark_id);
CREATE INDEX idx_mbr_model ON model_benchmark_runs(provider, model_id);
CREATE INDEX idx_mbr_tier ON model_benchmark_runs(difficulty_tier);
CREATE INDEX idx_mbr_timestamp ON model_benchmark_runs(run_timestamp);
CREATE INDEX idx_mbr_success ON model_benchmark_runs(flag_captured);
```

### 5.2 Aggregate Table: `model_benchmark_summary`

Pre-computed for dashboard performance (refreshed after each run batch):

```sql
CREATE TABLE model_benchmark_summary (
    summary_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    last_updated        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Grouping
    provider            VARCHAR(20) NOT NULL,
    model_id            VARCHAR(100) NOT NULL,
    model_display_name  VARCHAR(100),
    difficulty_tier     VARCHAR(10),                    -- NULL = all tiers combined
    benchmark_id        VARCHAR(50),                    -- NULL = all benchmarks combined
    
    -- Aggregate Metrics
    total_runs          INTEGER NOT NULL,
    successful_runs     INTEGER NOT NULL,
    pass_rate           FLOAT NOT NULL,                 -- successful / total
    pass_at_k           FLOAT,                          -- calculated at k=5
    pass_power_k        FLOAT,                          -- calculated at k=5
    
    -- Time
    avg_time_to_flag_s  FLOAT,
    min_time_to_flag_s  FLOAT,
    max_time_to_flag_s  FLOAT,
    stddev_time_s       FLOAT,
    
    -- Tokens
    avg_total_tokens    FLOAT,
    avg_input_tokens    FLOAT,
    avg_output_tokens   FLOAT,
    
    -- Steps
    avg_steps           FLOAT,
    min_steps           INTEGER,
    max_steps           INTEGER,
    
    -- Cost
    avg_cost_usd        FLOAT,
    total_cost_usd      FLOAT,
    
    -- Efficiency
    efficiency_score    FLOAT,                          -- 0-100
    consistency_score   FLOAT,                          -- lower stddev = higher
    loop_rate           FLOAT,                          -- % of runs with loops
    
    UNIQUE(provider, model_id, difficulty_tier, benchmark_id)
);
```

### 5.3 Model Registry: `benchmark_models`

```sql
CREATE TABLE benchmark_models (
    model_id            VARCHAR(100) PRIMARY KEY,       -- exact API string
    provider            VARCHAR(20) NOT NULL,
    display_name        VARCHAR(100) NOT NULL,
    tier                VARCHAR(20) NOT NULL,
    input_cost_per_1m   FLOAT,                          -- $ per 1M input tokens
    output_cost_per_1m  FLOAT,                          -- $ per 1M output tokens
    max_context_window  INTEGER,
    supports_tools      BOOLEAN DEFAULT TRUE,
    supports_streaming  BOOLEAN DEFAULT TRUE,
    api_base_url        VARCHAR(200),
    is_active           BOOLEAN DEFAULT TRUE,
    notes               TEXT,
    added_at            TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.4 Where to Store This

**Option A — PostgreSQL on VPS (Recommended)**
- Already discussed for MCP Gateway audit logs
- Co-locate with the existing benchmark infrastructure on 139.59.80.137
- Single source of truth for all benchmark intelligence
- PIL can connect directly when ready

**Option B — SQLite (Quick Start)**
- Faster to implement, no additional service needed
- Lives alongside the Flask dashboard
- Migrate to Postgres later when PIL needs it

**Recommendation:** Start with SQLite for rapid iteration, migrate to Postgres when the MCP Gateway goes live (they share the same DB requirement).

---

## 6. DASHBOARD — AGENT ACTIVITY FEED ENHANCEMENTS

### 6.1 Current State

The Agent Activity Feed currently shows:
- Sequential log of benchmark starts, flag captures, and stops
- Summary stats: Solved, Attempted, Pass Rate, Flag Attempts
- Difficulty breakdown: EASY x/y, MED x/y, etc.
- Single-model view (one run at a time)

### 6.2 New Features Required

#### Feature 1: Model Comparison View (New Tab/Mode)

```
┌─────────────────────────────────────────────────────────────────┐
│  Strike7 Agent Activity Feed          [Live Feed] [Comparison]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BENCHMARK COMPARISON: S7BEN-EASY-001 — Basic SQL Injection     │
│                                                                  │
│  ┌─────────────┬──────────┬──────────┬────────┬────────────┐    │
│  │ Model       │ Time (s) │ Tokens   │ Steps  │ Cost ($)   │    │
│  ├─────────────┼──────────┼──────────┼────────┼────────────┤    │
│  │ 🥇 Gem Flash│   15.2   │   3,041  │   5    │  $0.001    │    │
│  │ 🥈 Grok 3   │   40.1   │  10,220  │   5    │  $0.008    │    │
│  │ 🥉 Gem Pro  │   32.5   │   5,891  │   4    │  $0.004    │    │
│  │    Sonnet   │  115.3   │  75,430  │  15    │  $0.45     │    │
│  │    Opus     │  100.8   │ 200,102  │  30    │  $2.10     │    │
│  │    GPT-4.1  │   58.7   │  42,310  │  10    │  $0.38     │    │
│  └─────────────┴──────────┴──────────┴────────┴────────────┘    │
│                                                                  │
│  [Bar Chart: Time] [Bar Chart: Tokens] [Bar Chart: Steps]       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Feature 2: Model Performance Heatmap

A grid showing pass/fail and relative speed across all benchmarks:

```
                    Gem Flash   Gem Pro   Haiku    Sonnet   Opus     GPT-4.1m  GPT-4.1
S7BEN-EASY-001      🟢 15s     🟢 33s   🟢 22s   🟢 59s   🟢 100s  🟢 28s    🟢 45s
S7BEN-EASY-002      🟢 12s     🟢 25s   🟢 18s   🟢 59s   🟢 89s   🟢 20s    🟢 38s
S7BEN-MED-020       🟢 20s     🟢 41s   🟡 85s   🟢 51s   🟢 120s  🟡 90s    🟢 55s
S7BEN-HARD-023      🔴 FAIL    🟢 80s   🔴 FAIL  🟢 90s   🟢 210s  🔴 FAIL   🟢 130s
S7BEN-VHARD-XXX     🔴 FAIL    🔴 FAIL  🔴 FAIL  🔴 FAIL  🟡 450s  🔴 FAIL   🟡 380s

Color Legend: 🟢 Fast success  🟡 Slow success  🔴 Failed
```

#### Feature 3: Live Comparison Feed

When running a comparison batch, show side-by-side progress:

```
┌─ COMPARISON RUN: S7BEN-EASY-001 ────────────────────────────┐
│                                                               │
│  17:28:13  ▶ Gemini Flash started on port 5001               │
│  17:28:28  🏁 Gemini Flash: FLAG CAPTURED! 15.2s ✓           │
│  17:28:30  ▶ Claude Sonnet started on port 5001              │
│  17:29:29  🏁 Claude Sonnet: FLAG CAPTURED! 59.3s ✓          │
│  17:29:31  ▶ GPT-4.1 started on port 5001                   │
│  17:30:29  🏁 GPT-4.1: FLAG CAPTURED! 58.7s ✓               │
│  17:30:31  ▶ Claude Opus started on port 5001                │
│  17:32:11  🏁 Claude Opus: FLAG CAPTURED! 100.8s ✓           │
│                                                               │
│  WINNER: Gemini Flash (15.2s, 3041 tokens, $0.001)          │
└───────────────────────────────────────────────────────────────┘
```

#### Feature 4: Summary Statistics (Enhanced Header)

Replace current single-line stats with model-aware summary:

```
Current:  Solved: 8  Attempted: 15  Pass Rate: 100%  Flag Attempts: 8

Enhanced: 
┌──────────────────────────────────────────────────────────┐
│  Models Tested: 8    Benchmarks: 10    Total Runs: 240   │
│  Overall Pass Rate: 78%                                   │
│                                                           │
│  Best Overall: Gemini 2.5 Pro (92% pass, avg 45s)        │
│  Most Efficient: Gemini Flash (avg 3.2K tokens)          │
│  Most Capable: Claude Opus (only model to solve VHARD)   │
│  Best Value: Claude Haiku ($0.02/flag avg)               │
└──────────────────────────────────────────────────────────┘
```

#### Feature 5: Report Generation

Export comparison data as:
- **PDF Report** — Executive summary with charts for stakeholders
- **JSON Export** — Raw data for PIL ingestion
- **CSV Export** — For spreadsheet analysis
- **Markdown Report** — For Confluence/documentation

Report sections:
1. Executive Summary (key findings)
2. Model Ranking by Difficulty Tier
3. Cost Analysis (token consumption × pricing)
4. Efficiency Analysis (steps, loops, approach patterns)
5. Capability Matrix (what each model can/cannot solve)
6. Recommendations for Strike7 Engine (routing suggestions)

---

## 7. INTEGRATION WITH STRIKE7 PENTEST ENGINE

### The Model-Swapping Intelligence Loop

```
                    BENCHMARK DATA
                         │
                         ▼
              ┌──────────────────────┐
              │  model_benchmark_runs │
              │  (SQLite / Postgres)  │
              └──────────┬───────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │   PIL    │  │  Strike7 │  │ Dashboard │
     │ (Future) │  │  Engine  │  │  (Visual) │
     └──────────┘  └─────┬────┘  └──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  INTELLIGENT ROUTING  │
              │                      │
              │  IF task = SQLi_EASY  │
              │    USE gemini-flash   │
              │    (15s, 3K tokens)   │
              │                      │
              │  IF task = HARD_chain │
              │    USE claude-opus    │
              │    (only model that   │
              │     solves VHARD)     │
              │                      │
              │  IF agent_in_loop    │
              │    AND current=opus  │
              │    SWAP to sonnet    │
              │    (different        │
              │     reasoning path)  │
              └──────────────────────┘
```

### How This Feeds Into Model Swapping

The benchmark data creates a **Model Capability Matrix** that the Strike7 engine can query:

```json
{
  "routing_rules": [
    {
      "condition": "vuln_type == 'sqli' AND estimated_difficulty <= 'MED'",
      "recommended_model": "gemini-2.5-flash",
      "reason": "Solves 100% of EASY/MED SQLi in avg 15s at $0.001/run",
      "fallback": "claude-sonnet-4-5"
    },
    {
      "condition": "vuln_type == 'auth_bypass' AND estimated_difficulty == 'HARD'",
      "recommended_model": "claude-sonnet-4-5",
      "reason": "Best balance of capability and cost for complex auth chains",
      "fallback": "claude-opus-4-6"
    },
    {
      "condition": "difficulty == 'VHARD' OR multi_step_chain == true",
      "recommended_model": "claude-opus-4-6",
      "reason": "Only model with >50% pass rate on VHARD",
      "fallback": null
    },
    {
      "condition": "agent_stuck_in_loop AND loop_count > 3",
      "action": "swap_model",
      "swap_to": "different_provider_same_tier",
      "reason": "Different model = different reasoning path = breaks loop"
    }
  ]
}
```

### Sub-Agent Level Routing

Each Strike7 sub-agent can have its own model assignment:

```
ORCHESTRATOR  → Claude Opus (complex decision-making, low volume)
RECON AGENT   → Gemini Flash (fast, cheap, simple enumeration tasks)
ENUM AGENT    → Gemini Pro (balanced, good at structured output)
TRIAGE AGENT  → Claude Sonnet (good reasoning at moderate cost)
SPECIALIST    → Varies by vuln type (use benchmark data to decide)
VALIDATION    → Gemini Flash (fast confirmation, simple checks)
REPORTING     → Claude Sonnet (good writing quality)
```

This alone could reduce per-engagement cost by **60-80%** compared to running Opus everywhere.

---

## 8. INTEGRATION WITH PIL

### Data Flow: Benchmarks → PIL Training

```
model_benchmark_runs  →  PIL Data Export Adapter  →  PIL Training Dataset
                                                            │
                                                            ▼
                                                   PIL Features:
                                                   F1: Cost Prediction
                                                   F2: Target Clustering
                                                   F5: Zero-Yield Detection
                                                   
                                                   NEW Features:
                                                   F7: Model Selection
                                                   F8: Loop Prediction
                                                   F9: Token Budget Estimation
```

### New PIL Features Enabled By Benchmark Data

| Feature | Description | Training Signal |
|---------|-------------|-----------------|
| **F7: Model Selector** | Given (vuln_type, difficulty, defense_level), predict best model | benchmark runs with flag_captured + cost |
| **F8: Loop Predictor** | Predict probability of loop for (model, benchmark_type) | loop_detected, loop_count, steps_taken |
| **F9: Token Budgeter** | Estimate token budget before engagement starts | avg_total_tokens per (model, difficulty) |
| **F10: Swap Recommender** | When current model is struggling, recommend swap target | failed runs vs successful runs on same benchmark |

### PIL Advisory Example

```
PIL Advisory (Non-Blocking):
{
  "advisory_type": "model_recommendation",
  "confidence": 0.87,
  "recommendation": {
    "primary_model": "gemini-2.5-flash",
    "expected_time_s": 18.5,
    "expected_tokens": 4200,
    "expected_cost": 0.002,
    "pass_probability": 0.95
  },
  "alternatives": [
    {
      "model": "claude-haiku-4.5",
      "expected_time_s": 25.0,
      "expected_tokens": 8500,
      "pass_probability": 0.90
    }
  ],
  "reasoning": "Based on 45 prior runs of EASY-tier SQLi benchmarks, Gemini Flash achieves 95% pass rate with lowest cost."
}
```

---

## 9. TECHNICAL ARCHITECTURE — HOW TO RUN MULTI-MODEL BENCHMARKS

### 9.1 Runner Architecture

The benchmark runner needs to be **model-agnostic** — same benchmark, different LLM backend:

```
┌─────────────────────────────────────────────────────────┐
│                  BENCHMARK RUNNER                         │
│                                                           │
│  ┌──────────────┐    ┌────────────────┐                  │
│  │ Run Config   │───▶│  Model Router  │                  │
│  │              │    │                │                  │
│  │ benchmark_id │    │ IF provider == │                  │
│  │ model_id     │    │   "google"     │──▶ Gemini API   │
│  │ attempt_num  │    │   "anthropic"  │──▶ Claude API   │
│  │ timeout      │    │   "openai"     │──▶ OpenAI API   │
│  └──────────────┘    └────────┬───────┘                  │
│                               │                          │
│                    ┌──────────▼──────────┐               │
│                    │  Agent Scaffold     │               │
│                    │                     │               │
│                    │  - MCP tools        │               │
│                    │  - HTTP tools       │               │
│                    │  - Token counter    │               │
│                    │  - Step counter     │               │
│                    │  - Loop detector    │               │
│                    │  - Timeout handler  │               │
│                    └──────────┬──────────┘               │
│                               │                          │
│                    ┌──────────▼──────────┐               │
│                    │  Results Collector  │               │
│                    │                     │               │
│                    │  - Parse flag       │               │
│                    │  - Record metrics   │               │
│                    │  - Store to DB      │               │
│                    │  - Push to dashboard│               │
│                    └────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 9.2 Execution Modes

**Mode 1: Sequential (Current — Safest)**
Run benchmarks one at a time, cycling through models:
```
Benchmark X → Model A → record → Model B → record → Model C → record
Benchmark Y → Model A → record → ...
```
- Pro: Simple, no port conflicts, predictable resource usage
- Con: Slow (400 runs × avg 60s = ~6.7 hours minimum)

**Mode 2: Parallel by Model (Recommended)**
Run same benchmark across models simultaneously on different ports:
```
Benchmark X:
  Port 5001 → Model A ─┐
  Port 5002 → Model B ─┼──▶ Compare results
  Port 5003 → Model C ─┘
```
- Pro: ~3x faster, direct comparison timing
- Con: Higher resource usage, need port management
- Constraint: 4GB VPS limits to ~3-4 concurrent containers

**Mode 3: Batch (Recommended for large runs)**
Queue all runs, execute with configurable parallelism:
```python
batch_config = {
    "benchmarks": ["S7BEN-EASY-001", "S7BEN-EASY-002", ...],
    "models": ["gemini-flash", "claude-sonnet", "gpt-4.1", ...],
    "attempts_per_combination": 3,
    "max_concurrent": 3,
    "timeout_per_run_s": 600
}
```

### 9.3 Model Provider Abstraction Layer

```python
# Pseudocode for provider abstraction
class ModelProvider(ABC):
    @abstractmethod
    def create_completion(self, messages, tools, **kwargs) -> CompletionResult:
        """Returns standardized response with token counts"""
        pass

class GeminiProvider(ModelProvider):
    def create_completion(self, messages, tools, **kwargs):
        response = genai.generate_content(...)
        return CompletionResult(
            content=response.text,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            ...
        )

class AnthropicProvider(ModelProvider):
    def create_completion(self, messages, tools, **kwargs):
        response = anthropic.messages.create(...)
        return CompletionResult(
            content=response.content,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            ...
        )

class OpenAIProvider(ModelProvider):
    def create_completion(self, messages, tools, **kwargs):
        response = openai.chat.completions.create(...)
        return CompletionResult(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            ...
        )
```

---

## 10. REPORT GENERATION

### Report Types

| Report | Format | Audience | Content |
|--------|--------|----------|---------|
| **Executive Summary** | PDF | CTO, Stakeholders | Key findings, cost analysis, recommendations |
| **Technical Comparison** | Markdown / HTML | Engineering Team | Full metrics, charts, per-benchmark breakdown |
| **Model Capability Matrix** | JSON | Strike7 Engine / PIL | Machine-readable routing rules |
| **Raw Data Export** | CSV / JSON | Data Analysis | All runs with full metrics |

### Chart Types to Generate (like Image 2)

1. **Bar Chart: Execution Time by Model** (per benchmark)
2. **Bar Chart: Token Consumption by Model** (per benchmark)
3. **Bar Chart: Steps Taken by Model** (per benchmark)
4. **Heatmap: Model × Benchmark success/failure matrix**
5. **Scatter Plot: Cost vs Time** (Pareto frontier — which models are on the efficient frontier)
6. **Line Chart: pass@k curves** (success probability vs number of attempts)
7. **Stacked Bar: Token breakdown** (input vs output per model)
8. **Radar Chart: Multi-dimensional model comparison** (speed, cost, reliability, capability)

### Report Generation Tech

- **Charts:** matplotlib + seaborn (Python, already used per Image 2)
- **PDF:** ReportLab or WeasyPrint
- **Markdown:** Jinja2 templates
- **JSON:** Direct from DB query results

---

## 11. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1-2)

```
GOAL: Run benchmarks across 3 providers, store results, basic dashboard view

Tasks:
□ Create model_benchmark_runs SQLite schema
□ Build ModelProvider abstraction (Gemini, Claude, OpenAI)
□ Build benchmark runner with model routing
□ Implement token counting per provider
□ Implement cost calculation per provider
□ Add run results storage (SQLite)
□ Add basic API endpoint: GET /api/comparison/{benchmark_id}
□ Add "Comparison" tab to Agent Activity Feed
□ Basic table view of results

Deliverable: Can run any benchmark with any model, see results in dashboard
```

### Phase 2: Metrics & Visualization (Week 3)

```
GOAL: Rich comparison charts and metrics on dashboard

Tasks:
□ Implement pass@k and pass^k calculations
□ Implement efficiency scoring
□ Implement loop detection during runs
□ Build comparison chart components (bar, heatmap, scatter)
□ Add model performance heatmap to dashboard
□ Add live comparison feed (side-by-side model progress)
□ Implement enhanced summary statistics header
□ Add difficulty tier filtering

Deliverable: Full visual comparison experience on dashboard
```

### Phase 3: Batch Runner & Reports (Week 4)

```
GOAL: Automated batch runs and exportable reports

Tasks:
□ Build batch runner with configurable parallelism
□ Implement run queue with status tracking
□ Build report generation pipeline (PDF, MD, JSON, CSV)
□ Create chart generation (matplotlib/seaborn)
□ Implement model_benchmark_summary aggregate table
□ Add report download button to dashboard
□ API endpoint: POST /api/comparison/batch (start batch run)
□ API endpoint: GET /api/comparison/report/{format}

Deliverable: Run 400-benchmark comparison batch, generate full report
```

### Phase 4: Intelligence Integration (Week 5-6)

```
GOAL: Connect benchmark data to Strike7 engine and PIL

Tasks:
□ Build Model Capability Matrix JSON export
□ Create routing rules generator from benchmark data
□ Design PIL F7/F8/F9/F10 feature schemas
□ Build data export adapter for PIL
□ Document API for Strike7 engine consumption
□ Implement model recommendation endpoint
□ Migrate SQLite → PostgreSQL (if MCP Gateway is ready)

Deliverable: Strike7 engine can query benchmark intelligence for model routing
```

---

## 12. RISK REGISTER

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API costs spiral during large batch runs | HIGH | MEDIUM | Set budget caps per run batch. Start with cheapest models. Use token limits. |
| Models update/deprecate mid-comparison | MEDIUM | LOW | Pin model versions. Store exact model string per run. |
| VPS resource exhaustion during parallel runs | HIGH | MEDIUM | Limit to 3 concurrent containers. Monitor with `docker stats`. |
| Inconsistent benchmarks across runs (non-deterministic) | MEDIUM | HIGH | Run k=5 attempts. Use temperature=0 where possible. Statistical significance testing. |
| Provider rate limiting during batch runs | MEDIUM | MEDIUM | Add exponential backoff. Stagger requests across providers. |
| Benchmark containers leak/don't cleanup | MEDIUM | LOW | Timeout-based auto-cleanup. Docker prune after batch. |
| Token counting inconsistent across providers | LOW | HIGH | Verify token counts against provider dashboards. Document discrepancies. |

---

## 13. COST ESTIMATION

### Per-Run Cost (Approximate, based on Image 2 data)

| Model | Avg Tokens | Est. Cost/Run | Notes |
|-------|-----------|---------------|-------|
| Gemini Flash | ~3K | $0.001 | Extremely cheap |
| Gemini Pro | ~6K | $0.004 | Still very affordable |
| Claude Haiku | ~8K | $0.005 | Budget Anthropic |
| Claude Sonnet | ~75K | $0.45 | Mid-range |
| Claude Opus | ~200K | $2.10 | Expensive per run |
| GPT-4.1 mini | ~10K | $0.003 | Very affordable |
| GPT-4.1 | ~40K | $0.35 | Mid-range |

### Batch Cost Estimates

| Scenario | Runs | Est. Total Cost |
|----------|------|-----------------|
| Phase A: Quick Sweep | 40 | ~$15-25 |
| Phase B: Deep Comparison | 240 | ~$80-150 |
| Phase C: Statistical (k=5) | 400 | ~$150-250 |

> **Budget recommendation:** Allocate $300 for the full comparison exercise. This is a one-time intelligence-gathering investment that saves money long-term through optimized model routing.

---

## 14. SUCCESS CRITERIA

This initiative is successful when:

1. **Data exists:** ≥200 benchmark runs across ≥6 models stored with full metrics
2. **Patterns emerge:** Clear model-tier recommendations per difficulty level and vuln type
3. **Dashboard shows it:** Comparison view is live on Agent Activity Feed with charts
4. **Reports work:** Can generate PDF/MD/JSON comparison reports on demand
5. **Intelligence is actionable:** Model Capability Matrix is queryable by Strike7 engine
6. **Cost savings quantified:** Can demonstrate X% cost reduction potential vs Opus-everywhere approach
7. **PIL has data:** Structured benchmark data is available for PIL F7-F10 feature training

---

## 15. OPEN QUESTIONS TO RESOLVE

1. **API Keys:** Do we have API keys for all three providers (Google, Anthropic, OpenAI)? Budget approved?
2. **Which specific benchmarks** for the initial sweep? Suggest: S7BEN-EASY-001, S7BEN-EASY-005, S7BEN-MED-020, S7BEN-HARD-023, and one CVE — these are already proven working.
3. **Temperature setting:** Use 0 for reproducibility or default for realistic comparison?
4. **Agent scaffold:** Same scaffold/prompt for all models, or provider-optimized prompts?
5. **Timeout per run:** Fixed (e.g., 10 min) or tier-based (EASY=5min, HARD=15min)?
6. **Should we test reasoning modes?** (o3-mini with extended thinking vs standard mode)
7. **Dashboard priority:** New tab on existing Feed, or separate page entirely?
8. **VPS or local?** Run benchmarks on VPS (139.59.80.137) or local WSL2? VPS = consistent, local = no SSH overhead.

---

## 16. REFERENCES

- **KryptSec/OASIS:** github.com/KryptSec/oasis — Multi-model security benchmarking tool
- **LinkedIn (Arafat Ansari):** Open-source AI security benchmarking approaches
- **XBOW:** Existing benchmark reference for AI pentest agent evaluation
- **Anthropic Agent Evals:** pass@k, pass^k methodology
- **PIL Planning Docs:** /PIL/docs/ — Data schema, architecture, features
- **Strike7 Dashboard:** 139.59.80.137:5500/agent-feed

---

*This document is the 80% planning. Once questions in Section 15 are resolved, we move to the 20% building phase.*
