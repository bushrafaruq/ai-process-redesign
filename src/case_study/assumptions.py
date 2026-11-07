"""Every assumption behind the current-state baseline and the business case, in one place.

All figures are ILLUSTRATIVE for a generic 450-bed residential building. They are
plausible orders of magnitude, not measurements from any real organisation. Change
them here and re-run `python -m case_study.run` to regenerate every number in the docs.
"""

SEED = 42

# ---- Operation -------------------------------------------------------------
BEDS = 450
DAYS = 182                      # six months: 1 Aug - 30 Jan
MEAN_REQUESTS_PER_DAY = 40
SEPTEMBER_UPLIFT = 1.6          # move-in month volume multiplier

CHANNEL_MIX = {"email": 0.45, "portal": 0.25, "walk_in": 0.20, "phone": 0.10}

CATEGORY_MIX = {
    "maintenance_plumbing": 0.14, "maintenance_general": 0.18, "heating_hvac": 0.10,
    "access_keys": 0.12, "billing_payments": 0.10, "noise_conduct": 0.06,
    "cleaning_waste": 0.08, "internet_wifi": 0.08, "move_in_out": 0.07,
    "general_enquiry": 0.05, "safety_security": 0.02,
}
TRUE_PRIORITY_MIX = {"P1": 0.06, "P2": 0.34, "P3": 0.60}

# ---- Current (as-is) process ----------------------------------------------
# Shared inbox checked in batches; out-of-hours email waits for the morning shift.
DESK_HOURS = (8, 20)                       # front desk staffed 08:00-20:00
INBOX_CHECK_INTERVAL_MIN = 120             # coordinator works the inbox every ~2 hours
TRIAGE_MINUTES_PER_REQUEST = 4.0           # read, decide, log in CRM, forward
REWORK_MINUTES_PER_MISROUTE = 9.0          # bounce-back, re-read, re-forward, update resident
MISROUTE_RATE = 0.18                       # share sent to the wrong team first time
PRIORITY_INCONSISTENCY = 0.25              # share logged with a different priority than warranted
CHASER_RATE = 0.30                         # share of requests where the resident follows up
MINUTES_PER_CHASER = 5.0

# ---- Future (to-be) process -----------------------------------------------
# Review-mode shares and quick-approve precision come from the evaluation output
# (outputs/eval_*.json) and are read at run time. These are the remaining assumptions.
QUICK_APPROVE_MINUTES = 1.0
FULL_REVIEW_MINUTES = 3.5
ESCALATE_MINUTES = 2.0
FUTURE_TRIAGE_DELAY_MIN = 10               # agent runs on arrival; coordinator works a live queue
REVIEW_CATCH_MISS_RATE = 0.5              # share of agent category errors the reviewer misses
CHASER_REDUCTION = 0.35                    # instant acknowledgement with expected response time

# ---- Money ----------------------------------------------------------------
LOADED_COST_PER_HOUR_EUR = 30.0            # coordinator salary + employer costs + overheads
LLM_COST_PER_REQUEST_EUR = 0.002           # small model, ~600 tokens in/out per request
BUILD_DAYS = 20                            # discovery, build, evaluation, integration, training
DAY_RATE_EUR = 550.0
RUN_COST_PER_MONTH_EUR = 150.0             # hosting, monitoring
SUPPORT_DAYS_PER_QUARTER = 2               # prompt/rule upkeep, re-evaluation

SCENARIOS = {                               # multipliers applied to time savings
    "low": 0.6,
    "base": 1.0,
    "high": 1.25,
}
