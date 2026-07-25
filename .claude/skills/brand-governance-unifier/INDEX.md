# Brand Governance Unifier — Complete Index

Welcome. This directory contains a complete, production-ready skill for consolidating scattered brand, communication, and sales governance documents into one unified system.

---

## Quick Navigation

| Document | Purpose |
|----------|---------|
| **SKILL.md** | Main skill definition—read this first |
| **README.md** | Quick-start guide and typical workflow |
| **PACKAGE_SUMMARY.md** | Overview of what's included and how to use it |
| **references/phase-1-analysis-template.md** | Checklist for analyzing documents before rewriting |
| **references/phase-2-execution-checklist.md** | Step-by-step guide for rewriting documents |
| **evals/evals.json** | Four test cases (WebStaffr, HVAC, SaaS, copy audit) |
| **evals/assertions.json** | Evaluation framework (what success looks like) |

---

## Getting Started in 5 Minutes

1. **Read**: SKILL.md (you are here)
2. **Understand**: Two-phase methodology (Phase 1: analyze, Phase 2: rewrite)
3. **Gather**: Your governance documents
4. **Invoke**: Ask Claude to consolidate them using this skill
5. **Review**: Results against the quality checklist

---

## The Core Methodology

### Phase 1: Analysis & Strategic Planning (Understanding)
Before rewriting anything, analyze:
- Philosophy, positioning, voice, strategy across all documents
- Contradictions, redundancies, gaps
- Brand rules and non-negotiables
- What the new document architecture should be

**Output**: A detailed analysis plan

### Phase 2: Production & Standardization (Building)
Then rewrite each document using:
- Governing principles established in Phase 1
- Two communication styles (Executive for internal, Commercial for customers)
- Consistent philosophy throughout
- Clear document roles with minimal overlap

**Output**: Consolidated governance system + reconciliation memo

---

## Communication Standards Enforced

### Executive (Internal, Leadership, Strategy)
- Elevated vocabulary
- Precise language
- Calm authority
- Accuracy before persuasion

### Commercial (Customers, Marketing)
- Grade 8 reading level
- Simple language
- Outcome-focused
- High readability
- Premium metaphors without sacrificing clarity

---

## What Success Looks Like

A consolidated governance system that:
- ✓ Reads as one cohesive system
- ✓ Has no contradictions between documents
- ✓ Gives every document a clear, distinct purpose
- ✓ Reinforces core philosophy consistently
- ✓ Feels intentional, premium, authoritative
- ✓ Could serve as the long-term company manual

---

## WebStaffr-Specific (If Applicable)

When consolidating WebStaffr governance, these rules are enforced:

**Typography**: "WebStaffr" is always Garamond Bold Italic, 1 size larger
**Colors**: #1f4d78 unified OR #999999 (Web) + #bf9000 (Staffr)
**Forbidden**: No em dashes anywhere
**Philosophy**: "We absorb complexity so customers experience clarity"
**Positioning**: Outcome-focused (never feature-focused)
**References**: Never mention old iterations or legacy decisions

---

## Files in This Directory

### Core Skill Definition
- **SKILL.md** — Complete methodology, standards, quality checklist (read first)
- **README.md** — Quick-start, workflow, philosophy

### Reference Materials
- **references/phase-1-analysis-template.md** — Comprehensive checklist for Phase 1
- **references/phase-2-execution-checklist.md** — Step-by-step guide for Phase 2

### Testing & Evaluation
- **evals/evals.json** — 4 test cases with detailed prompts
- **evals/assertions.json** — Evaluation framework with 10+ assertions per test
- **PACKAGE_SUMMARY.md** — Overview of test cases and how to run them

### Documentation
- **INDEX.md** — This file
- **README.md** — Quick-start guide

---

## How This Skill Works in Practice

### Scenario 1: Consolidating Multiple Documents
```
User: "Our governance docs are scattered and contradictory. 
        Can you make them coherent?"

Claude: [Invokes brand-governance-unifier]
→ Phase 1: Analyzes all docs for philosophy, contradictions, gaps
→ Phase 2: Rewrites each doc using unified principles
→ Delivers: Consolidated system + reconciliation memo
```

### Scenario 2: Auditing New Copy
```
User: "Is this new marketing copy on-brand?"

Claude: [Invokes brand-governance-unifier]
→ Audits copy against existing governance standards
→ Identifies specific violations
→ Provides rewrite matching standards
```

### Scenario 3: Setting Up Governance from Scratch
```
User: "We need governance docs. Start from these principles..."

Claude: [Invokes brand-governance-unifier]
→ Phase 1: Establishes principles, architecture
→ Phase 2: Creates each document (visual, editorial, sales, strategic)
→ Delivers: Complete governance manual
```

---

## Evaluation Framework

### What Gets Measured

**Qualitative** (human judgment):
- Contradiction resolution
- Philosophy consistency
- Communication style separation
- Tone appropriateness
- Clarity improvement

**Quantitative** (objective):
- Redundancy percentage
- Brand rule compliance (no em dashes, colors documented, etc.)
- Reading level (Grade 8 for commercial, 10-14 for executive)
- Legacy reference removal

---

## Test Cases Available

### 1. WebStaffr Repo Docs (Real)
5 actual repo governance documents (CLAUDE.md, TASKS.md, CODE_REVIEW.md, STRATEGY.md, LEGACY_AUDIT.md)
- Tests real-world complexity and multi-document consolidation
- Measures philosophy consistency and role clarity

### 2. Home Service Brand (Generic)
HVAC company with conflicting positioning ("AI-powered" vs. "fix your furnace")
- Tests contradiction resolution
- Measures tone consistency and tradesperson-friendliness

### 3. SaaS Voice Audit (Enterprise)
4 conflicting docs (logo, enterprise sales, casual website, investor pitch)
- Tests visual identity documentation
- Measures two-voice separation and consistency

### 4. Copy Audit & Fix (Tactical)
Sample marketing copy vs. existing governance standards
- Tests audit capability
- Measures rewrite quality and standard compliance

---

## Quick Answers

### "How do I use this skill?"
Provide documents (via text, paste, or file) and ask Claude to consolidate them using the brand-governance-unifier skill.

### "What does it produce?"
A unified governance system (reorganized docs) + a reconciliation memo explaining decisions.

### "How long does it take?"
Phase 1: 15-30 minutes (analysis)
Phase 2: 30-60 minutes (rewriting)
Total: 1-2 hours for typical 3-5 document consolidation

### "Can I iterate?"
Yes. Review results against the quality checklist, provide feedback, Claude adjusts.

### "Can I use this for other brands?"
Absolutely. This is a reusable skill for any company's governance consolidation.

### "Is there an em-dash rule?"
For WebStaffr specifically, yes—no em dashes anywhere. For other brands, you define the rules.

---

## The Philosophy Behind This Skill

This skill embodies these core principles:
- **Customers buy outcomes, not technology**
- **Complexity belongs inside the company, clarity belongs outside**
- **Clarity is a competitive advantage**
- **Premium organizations communicate with confidence, restraint, and consistency**
- **Every sentence should support trust, operational excellence, and measurable value**

When applied correctly, this skill transforms scattered, contradictory governance into a premium manual that actually functions as the company's long-term guide.

---

## Next Steps

1. **Review SKILL.md** — Understand the full methodology
2. **Gather your documents** — Collect all governance materials
3. **Invoke the skill** — Ask Claude to analyze and consolidate
4. **Review results** — Check against the quality checklist
5. **Iterate if needed** — Provide feedback, Claude adjusts
6. **Implement** — Use the consolidated system as your long-term manual

---

## Support & Iteration

This skill is designed to improve based on feedback. Potential enhancements:

- Industry-specific templates (HVAC, SaaS, agencies, etc.)
- Automated readability checking (Flesch-Kincaid, etc.)
- Brand rule templates (common font/color combinations)
- Common contradictions database with resolution examples
- Integration with design systems and component libraries

---

## File Structure

```
brand-governance-unifier/
├── SKILL.md                    (main definition)
├── README.md                   (quick-start)
├── PACKAGE_SUMMARY.md          (overview)
├── INDEX.md                    (this file)
├── references/
│   ├── phase-1-analysis-template.md
│   └── phase-2-execution-checklist.md
└── evals/
    ├── evals.json              (test cases)
    └── assertions.json         (evaluation framework)
```

---

## Version Info

- **Skill Name**: brand-governance-unifier
- **Version**: 1.0
- **Created**: 2026-07-18
- **Platform**: Claude Code / Cowork
- **Status**: Production-ready

---

## Ready to Consolidate?

1. Open SKILL.md (full details)
2. Gather your documents
3. Ask Claude to consolidate them using this skill
4. The two-phase methodology will handle the rest

Your governance documents are about to feel like they came from one elite consultancy.

---

**Start here**: [SKILL.md](./SKILL.md)
