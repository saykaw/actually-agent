# Claim Deconstructor — SKILL.md

## What this skill does

Breaks a surface-level claim into its underlying scientific components before
any investigation begins. This ensures every subsequent search investigates the
_right_ question, not just the headline.

## When to invoke

Always first — before any PubMed or Semantic Scholar search. Every investigation starts here.

## How to execute

Given a claim, extract the following four components:

### 1. Core assertion

What is the claim _specifically_ saying? Strip hedging language and media
framing. State it as a falsifiable scientific proposition.

Example:

- Input: "Coffee causes cancer"
- Core assertion: "Regular coffee consumption increases the risk of developing cancer"

### 2. Implied mechanism

_Why_ would this be true if it were? What biological, chemical, or causal
pathway does the claim imply? If unspecified, identify the most likely candidate.

Example:

- "Acrylamide produced during roasting is a known carcinogen; caffeine may
  also play a role via oxidative stress pathways"

### 3. Population and conditions

Who does this apply to? Under what conditions?

- Age group, dosage/frequency, pre-existing conditions
- If unspecified: mark as **UNSPECIFIED** — do not guess
- UNSPECIFIED tells the investigator to check whether studies controlled for these variables

### 4. Timeframe

Short-term or long-term effect?

- If unspecified: mark as **UNSPECIFIED**

## Output format

```json
{
  "core_assertion": "...",
  "implied_mechanism": "...",
  "population": "adults | UNSPECIFIED",
  "timeframe": "chronic long-term | UNSPECIFIED",
  "investigation_angles": [
    "Search PubMed for: acrylamide cancer risk cohort study",
    "Search Semantic Scholar for: caffeine oxidative stress carcinogenicity",
    "Search for contradicting studies: coffee cancer no association"
  ]
}
```

The `investigation_angles` are the specific PubMed/Semantic Scholar queries
the agent will use. Generic claims must generate specific angles. This is what
separates a real investigation from a web search.

## Rules

- Never guess population or timeframe — UNSPECIFIED is correct when not stated
- Generate at least 3 investigation angles, each phrased as a ready-to-use search query
- If the claim is not falsifiable, flag it and explain why
- Log the claim itself as a node via submit_finding before proceeding
