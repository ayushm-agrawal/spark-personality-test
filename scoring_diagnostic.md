# Scoring Diagnostic Report

## Summary of Issue
Users are seeing 100% for multiple Big Five traits simultaneously, which suggests the scoring/normalization system isn't creating proper differentiation.

---

## 1. Scoring Flow Trace

### Step 1: Score Collection (services.py:596-656)

When a user answers a question:

```python
# For multiple-choice (line 600-602):
if current_question["type"] == "multiple-choice":
    option = current_question["options"].get(selected_key)
    if option:
        session["scores"][trait] += option["score"]  # Score is 0, 1, or 2

# For freeform (line 604-656):
# LLM evaluates and assigns 0-5 score
session["scores"][trait] += eval_json["score"]
```

**Trait count increment (line 660):**
```python
session["trait_counts"][trait] += 1
```

### Step 2: Normalization (services.py:276-302)

```python
def normalize_scores(raw_scores: dict, trait_counts: dict) -> dict:
    normalized = {}
    for trait, raw_score in raw_scores.items():
        question_count = trait_counts.get(trait, 2)  # DEFAULT TO 2 IF NOT TRACKED
        max_possible = question_count * 2  # Max 2 points per question

        if max_possible > 0:
            normalized[trait] = min(100, (raw_score / max_possible) * 100)
        else:
            normalized[trait] = 50  # Default to middle
    return normalized
```

### Step 3: Archetype Matching (services.py:333-412)

```python
def determine_archetype(scores: dict, trait_counts: dict = None) -> dict:
    if trait_counts is None:
        trait_counts = {trait: 2 for trait in scores.keys()}  # DEFAULT FALLBACK

    normalized_scores = normalize_scores(scores, trait_counts)

    # Cosine similarity matching against archetype profiles
    for archetype, profile in ARCHETYPE_PROFILES.items():
        similarity = cosine_similarity(normalized_scores, profile)
```

---

## 2. The Math Problem

### Question Count by Mode

| Mode | Total Questions | Traits | Questions per Trait |
|------|-----------------|--------|---------------------|
| Hackathon | 6 | 5 | ~1.2 (1-2 each) |
| Overall | 10 | 5 | 2 each |
| Deep Dive | 10 | 5 | 2 each |

### Maximum Possible Scores

For a trait with 2 questions:
- Max raw score = 2 questions × 2 points = **4 points**
- Normalized = (4/4) × 100 = **100%**

For a trait with 1 question (hackathon):
- Max raw score = 1 question × 2 points = **2 points**
- Normalized = (2/2) × 100 = **100%**

### The Scoring Gap

**Current option scores from LLM prompt (prompts.py:226-230):**
```json
"options": {
  "a": {"text": "Option A text", "score": <0-2>},
  "b": {"text": "Option B text", "score": <0-2>},
  "c": {"text": "Option C text", "score": <0-2>}
}
```

**Problem:** The prompt doesn't specify HOW to distribute scores. If the LLM gives:
- a: 2, b: 1, c: 0 (proper differentiation) ✓
- a: 2, b: 2, c: 1 (minimal differentiation) ⚠️
- a: 2, b: 2, c: 2 (no differentiation) ✗

---

## 3. Root Cause Analysis

### Primary Issue: LLM Score Assignment Ambiguity

**Location:** prompts.py lines 226-230

The prompt template shows all three options with `<0-2>` but provides **no guidance on differentiation**:
- No instruction that scores should vary
- No instruction that one option should be low-indicator (0)
- No instruction on what 0, 1, 2 mean semantically

### Secondary Issue: Low Question Count

With only 1-2 questions per trait:
- A single high-scoring answer = 100%
- No room for nuance or averaging

### Tertiary Issue: Cosine Similarity with Uniform Scores

If a user scores [100, 100, 100, 100, 100]:
- Cosine similarity measures **angle**, not magnitude
- A perfectly uniform vector has equal similarity to archetypes based on their **balance**, not their actual profiles
- Archetypes with more uniform trait profiles will match better

**Example calculation:**
```
User: [100, 100, 100, 100, 100]
The Gardener: [60, 80, 55, 85, 75] - more balanced
The Alchemist: [95, 55, 35, 60, 70] - more extreme

cosine(user, Gardener) ≈ 0.987
cosine(user, Alchemist) ≈ 0.955

Result: User matches Gardener despite having no actual personality signal!
```

---

## 4. Archetype Profile Requirements

### The Gardener's Big Five Profile (archetypes.py:140-146)

```python
"big_five_profile": {
    "Openness": 60,
    "Conscientiousness": 80,
    "Extraversion": 55,
    "Agreeableness": 85,
    "Emotional_Stability": 75
}
```

### All Archetype Profiles for Reference

| Archetype | O | C | E | A | ES | Sum | Uniformity |
|-----------|---|---|---|---|----|----|------------|
| The Architect | 75 | 85 | 60 | 55 | 70 | 345 | Medium |
| The Catalyst | 90 | 50 | 85 | 65 | 55 | 345 | Low |
| The Strategist | 70 | 80 | 70 | 50 | 85 | 355 | Medium-High |
| The Guide | 75 | 60 | 75 | 90 | 65 | 365 | Medium |
| The Alchemist | 95 | 55 | 35 | 60 | 70 | 315 | Low |
| **The Gardener** | 60 | 80 | 55 | 85 | 75 | **355** | **High** |
| The Luminary | 90 | 45 | 70 | 80 | 60 | 345 | Medium |
| The Sentinel | 50 | 85 | 40 | 65 | 90 | 330 | Low |

**Key insight:** The Gardener has one of the most **uniform/balanced** profiles. If users are scoring uniformly high, they'll match The Gardener!

---

## 5. Code Locations for Reference

| Function | File | Lines | Purpose |
|----------|------|-------|---------|
| `normalize_scores()` | services.py | 276-302 | Converts raw → 0-100 |
| `determine_archetype()` | services.py | 333-412 | Matches user to archetype |
| `cosine_similarity()` | services.py | 305-330 | Vector similarity |
| `submit_response()` | services.py | 553-748 | Score accumulation |
| `finalize_test()` | services.py | 899-1085 | Final scoring |
| Prompt template | prompts.py | 108-250 | LLM scoring instructions |
| Archetype profiles | archetypes.py | 22-190 | Target profiles |

---

## 6. Hypotheses for 100% Scores

### Hypothesis A: LLM Not Differentiating Scores
The LLM is assigning high scores (1-2) to all options because:
- No explicit instruction to create score spread
- "Authentic reactions" framing may lead to validating all responses

### Hypothesis B: Users Selecting Optimal Answers
Even with proper scoring, if users consistently select the 2-point option:
- 2/2 per question = 100% normalized

### Hypothesis C: Trait Count Default Fallback
If `trait_counts` is empty or not passed properly:
- Default = 2 questions per trait
- If actual questions < 2, scores would be UNDER 100%
- If actual questions > 2, scores would be OVER-normalized

---

## 7. What to Investigate Next

1. **Check actual LLM responses:** Are the generated option scores actually varied (0, 1, 2) or uniform (all 2s)?

2. **Check raw scores in Firestore:** Look at `session.scores` and `session.trait_counts` for completed tests

3. **Add logging:** Log raw scores before normalization to see actual values

4. **Review prompt effectiveness:** The prompt at lines 226-230 needs clearer scoring instructions

---

## 8. Recommended Fixes (DO NOT IMPLEMENT YET)

1. **Update prompt to enforce score distribution:**
   ```
   CRITICAL: Each question MUST have varied scores:
   - One option should score 2 (strong indicator of trait)
   - One option should score 1 (moderate indicator)
   - One option should score 0 (low/absent indicator)
   ```

2. **Consider Euclidean distance instead of cosine similarity** - magnitude matters for personality!

3. **Increase questions per trait** in hackathon mode or accept lower confidence

4. **Add score validation** after LLM generation to ensure proper distribution
