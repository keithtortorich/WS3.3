# Brand Governance Unifier

A reusable skill for consolidating scattered brand, communication, and sales governance documents into one unified, premium system.

## Quick Start

### When to Use

Invoke this skill whenever:
- You have multiple conflicting brand/style/communication documents
- A user asks to "unify," "reconcile," or "consolidate" governance docs
- You need to audit new copy against existing brand standards
- Documents feel disjointed or contradictory
- You want a company's governance to "feel like one consultancy wrote it"

### Typical Workflow

1. **Gather all governance documents** (strategy, style guides, brand positioning, sales doctrine, internal process docs)
2. **Invoke the skill** with the documents as input
3. **Claude performs Phase 1** (analysis, principles, architecture)
4. **Claude performs Phase 2** (production, rewriting, validation)
5. **Review the consolidated system** against the quality checklist
6. **Iterate** if needed

---

## What This Skill Does

### Phase 1: Analysis & Strategic Planning

- Reads all supplied documents completely
- Identifies core philosophy, contradictions, redundancies, gaps
- Establishes governing principles
- Defines document architecture before rewriting

### Phase 2: Production & Standardization

- Rewrites documents using governing principles
- Maintains two communication styles: Executive and Commercial
- Removes contradictions, redundancy, and ambiguity
- Increases clarity and authority
- Ensures all documents reinforce core philosophy

---

## Communication Styles Maintained

### Executive
Used for leadership, investors, engineering, strategy, internal governance.
- Elevated vocabulary
- Precise language
- Calm authority
- Accuracy before persuasion

### Commercial
Used for customers, marketing, websites, sales.
- Grade 8 reading level
- Simple language
- Outcome-focused
- High readability
- Tradesperson-friendly
- Premium metaphors without sacrificing clarity

---

## Quality Checklist

The skill verifies:
- All documents read as one cohesive system
- No documents contradict each other
- Every document has a clear, distinct purpose
- Philosophy is consistent throughout
- Writing feels intentional, premium, authoritative
- Finished work could serve as long-term governance manual

---

## WebStaffr-Specific Notes

If consolidating WebStaffr governance, the skill maintains:
- Garamond Bold Italic for brand name (1 size larger)
- Color palette: #1f4d78 or split (#999999 / #bf9000)
- No em dashes (hard rule)
- Core principle: "We absorb complexity so customers experience clarity"
- No legacy references or historical apologies
- Outcome-focused positioning (not feature-focused)

---

## Example Usage

```
Consolidate these five WebStaffr docs into one unified governance system:
1. CLAUDE.md (operational control)
2. TASKS.md (live status)
3. CODE_REVIEW.md (code findings)
4. STRATEGY.md (product strategy)
5. LEGACY_AUDIT.md (inherited decisions)

Use the complexity principle and maintain two clear communication styles: 
Executive (for internal) and Commercial (for customers, Grade 8 level).
```

Result: A consolidated manual with clear roles, no contradictions, consistent philosophy throughout.

---

## For Developers

This skill is defined in `.claude/skills/brand-governance-unifier/SKILL.md` and can be invoked by Claude in any session within this repo.

To test the skill, use the test cases in `evals/evals.json`:
1. Home-service brand consolidation (generic example)
2. SaaS voice audit and fix (with voice/tone standardization)
3. New copy against existing standards (audit and rewrite)
4. WebStaffr repo docs consolidation (using actual repo governance)

---

## Philosophy

This skill embodies these principles:
- **Customers buy outcomes, not technology**
- **Complexity belongs inside, clarity outside**
- **Clarity is a competitive advantage**
- **Premium organizations communicate with confidence, restraint, consistency**
- **Every sentence supports trust, operational excellence, and measurable value**
