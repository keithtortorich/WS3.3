# Brand Governance Unifier — Package Summary

## What's Included

This skill package contains everything needed to consolidate scattered brand, communication, and sales governance documents into one unified, premium system.

### Core Files

- **SKILL.md** — Main skill definition with full two-phase methodology, communication standards, quality checklist, and WebStaffr-specific brand rules
- **README.md** — Quick-start guide, typical workflow, communication styles, quality checklist, WebStaffr notes
- **PACKAGE_SUMMARY.md** — This file

### Evaluation & Testing

- **evals/evals.json** — Four test cases:
  1. WebStaffr repo docs consolidation (using actual CLAUDE.md, TASKS.md, CODE_REVIEW.md, STRATEGY.md, LEGACY_AUDIT.md)
  2. Home-service brand consolidation (generic HVAC example)
  3. SaaS voice audit and fix (enterprise vs. casual voice)
  4. New copy against existing standards (audit and rewrite)

- **evals/assertions.json** — Quantitative and qualitative evaluation framework:
  - 10 assertions for repo-docs test
  - 3 assertions for home-service test
  - 3 assertions for SaaS test
  - 3 assertions for copy-audit test

### Reference Materials

- **references/phase-1-analysis-template.md** — Complete checklist/template for conducting Phase 1 analysis on any set of governance documents

---

## How to Use This Skill

### In Claude (any session in this repo)

Simply mention governance consolidation, brand unification, or style guide conflicts:

```
"Our governance docs contradict each other. 
Use the brand-governance-unifier skill to consolidate them."
```

Claude will automatically invoke the skill because it's in `.claude/skills/`.

### Outside This Repo

Copy the skill directory to another Claude Code project's `.claude/skills/` folder.

---

## The Two-Phase Methodology

### Phase 1: Analysis & Strategic Planning
1. Read every document completely
2. Identify philosophy, contradictions, redundancies, gaps
3. Establish governing principles
4. Define new document architecture

**Output**: A detailed analysis plan

### Phase 2: Production & Standardization
1. Rewrite all documents using governing principles
2. Maintain two communication styles (Executive & Commercial)
3. Remove contradictions, redundancy, ambiguity
4. Verify against quality checklist

**Output**: Consolidated governance system + reconciliation memo

---

## Communication Standards Built In

### Executive Style (internal, leadership, strategy)
- Elevated vocabulary
- Precise language
- Calm authority
- Accuracy before persuasion

### Commercial Style (customers, marketing)
- Grade 8 reading level
- Simple language
- Outcome-focused
- High readability
- Tradesperson-friendly
- Premium metaphors without sacrificing clarity

---

## WebStaffr-Specific Rules (if applicable)

When consolidating WebStaffr documents, these rules are enforced:

- **Logo/Brand Name**: Garamond Bold Italic, 1 size larger than surrounding text
- **Colors**: #1f4d78 (unified) OR #999999 (Web) + #bf9000 (Staffr)
- **Forbidden**: No em dashes anywhere
- **Core Principle**: "We absorb complexity so customers experience clarity"
- **Positioning**: Outcome-focused (not feature-focused)
- **No Legacy References**: Never mention old decisions, previous vendors, or historical paths

---

## Quality Assurance

The skill includes a comprehensive quality checklist:

- [ ] All documents read as one cohesive system
- [ ] No documents contradict each other
- [ ] Every document has a clear, distinct purpose
- [ ] Philosophy is consistent throughout
- [ ] Writing feels intentional, premium, authoritative
- [ ] Finished work could serve as long-term governance manual
- [ ] All brand rules followed (no em dashes, correct fonts, color codes)
- [ ] Two communication styles clearly separated with examples

---

## Test Cases Included

### 1. WebStaffr Repo Docs (Real Example)
**Input**: 5 repo governance docs (CLAUDE.md, TASKS.md, CODE_REVIEW.md, STRATEGY.md, LEGACY_AUDIT.md)
**Expected Output**: Consolidated system with clear roles, reconciliation memo, no contradictions
**Key Assertion**: No legacy references, philosophy consistent, two styles separated

### 2. Home Service Brand (Generic Example)
**Input**: 3 conflicting docs (AI-focused positioning + "fix furnace fast" + complexity principle)
**Expected Output**: Unified governance, premium but tradesperson-friendly
**Key Assertion**: Contradiction resolved, tone consistent, document roles clear

### 3. SaaS Voice Audit (Enterprise Example)
**Input**: 4 scattered docs (logo treatment, enterprise sales, casual website, investor pitch)
**Expected Output**: Consolidated governance with visual rules, editorial standards, reconciliation memo
**Key Assertion**: Style violations identified, two voices clearly separated

### 4. Copy Audit & Fix (Tactical Example)
**Input**: Sample customer copy + existing governance standards
**Expected Output**: Audit report + rewritten copy matching standards
**Key Assertion**: Violations correctly identified, rewrite matches standards

---

## Evaluation Framework

### Qualitative Assertions (human judgment)
- Contradiction resolution
- Philosophy consistency
- Communication style separation
- Tone appropriateness
- Structure and role clarity
- Clarity improvement over originals

### Quantitative Assertions (measurable)
- Redundancy elimination (% duplicate words)
- Em-dash removal (% compliance)
- Reading level (Flesch-Kincaid Grade)
- Brand rule compliance (hex codes present, fonts documented)
- Legacy reference removal (keyword grep)

---

## How to Run Tests

### Using the skill in Claude:

1. Provide the governance documents (via text, file upload, or referencing files)
2. Ask Claude to consolidate them using the brand-governance-unifier skill
3. Claude will perform Phase 1 analysis and Phase 2 production
4. Review results against the quality checklist

### Measuring Success:

- No contradictions between docs
- Philosophy stated clearly in every doc
- Executive and Commercial voice examples provided
- No em dashes or other forbidden elements
- Documents have distinct, non-overlapping roles
- Reconciliation memo explains consolidation decisions
- Finished work reads as cohesive system

---

## Next Steps

1. **Try Test Case 1** (WebStaffr repo docs) with your actual governance docs
2. **Review results** against the quality checklist
3. **Iterate** if needed based on feedback
4. **Validate** that the consolidated system actually works in practice (is it used, is it clear, does it guide decisions?)

---

## Philosophy Behind This Skill

This skill embodies these principles:
- **Customers buy outcomes, not technology**
- **Complexity belongs inside, clarity outside**
- **Clarity is a competitive advantage**
- **Premium organizations communicate with confidence, restraint, consistency**
- **Every sentence supports trust, operational excellence, and measurable value**

When used correctly, this skill transforms fragmented governance into a premium manual that could have been written by an elite consultancy—and actually functions as a long-term guide for the company's brand and operations.

---

## Version & Last Updated

- **Version**: 1.0
- **Last Updated**: 2026-07-18
- **Platform**: Claude Code / Cowork
- **Status**: Ready for testing and iteration

---

## Support & Iteration

This skill is designed to be iterated based on feedback. Common improvements:

- Add more test cases for specific industries
- Expand reference materials (e.g., tone examples, vocabulary lists)
- Add automated readability checking (Flesch-Kincaid, etc.)
- Create industry-specific templates (HVAC, SaaS, agencies, etc.)
- Build a "common contradictions" database with resolution templates
