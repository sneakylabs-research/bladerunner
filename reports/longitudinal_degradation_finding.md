# Bladerunner Project: Longitudinal Degradation Finding

**Status**: Working document  
**Date**: 31 December 2025  
**Author**: SneakyLabs

---

## Summary

Cross-provider reliability degrades under longitudinal (conversational) administration for some instrument/encoding/profile combinations but not others. The original hypothesis—that affect content causes degradation—was tested and **not confirmed**. A new hypothesis emerges: degradation is an interaction effect between instrument framing, encoding richness, and profile extremity.

---

## Experiments

| ID | Name | Mode | Purpose |
|----|------|------|---------|
| 6 | Full Validation v3 | Cross-sectional | Baseline reliability |
| 14 | Longitudinal Full | Longitudinal | Replication with context accumulation |
| 15 | PHQ Affect Isolation | Longitudinal | Test affect hypothesis |

---

## Finding 1: Instrument-Level Degradation

Comparing Experiment 6 (cross-sectional) to Experiment 14 (longitudinal):

| Instrument | Exp 6 | Exp 14 | Δ |
|------------|-------|--------|------|
| PHQ-9 | 0.779 | 0.473 | **-0.306** |
| GAD-7 | 0.868 | 0.717 | **-0.151** |
| BFI | 0.813 | 0.770 | -0.043 |
| Levenson | 0.921 | 0.883 | -0.039 |
| Dark Triad | 0.916 | 0.895 | -0.021 |

**Pattern**: Clinical instruments (PHQ-9, GAD-7) collapsed. Personality instruments (BFI, Levenson, Dark Triad) held stable.

---

## Finding 2: Affect Hypothesis Not Confirmed

**Hypothesis**: Affect-framed items cause degradation because models learned that affect-language fluctuates in human text.

**Test**: Experiment 15 administered three instruments under longitudinal conditions:
- PHQ-3-A: 3 affect-only items
- PHQ-6-BC: 6 behavioral/cognitive items
- PHQ-9: 9 mixed items (control)

**Results**:

| Instrument | Type | Mean item r |
|------------|------|-------------|
| PHQ-3-A | Affect only | 0.903 |
| PHQ-6-BC | Behavioral/Cognitive | 0.827 |
| PHQ-9 | Mixed | 0.839 |

**Conclusion**: Affect items showed *higher* reliability than behavioral items. Hypothesis not supported. The affect/attitude/behavioral distinction does not explain the degradation pattern.

---

## Finding 3: Input System Interaction

Same instruments show different degradation depending on encoding method:

**All instruments**:

| Encoding | Exp 6 | Exp 14 | Δ |
|----------|-------|--------|------|
| ocean_direct | 0.871 | 0.708 | -0.163 |
| exemplar | 0.922 | 0.838 | -0.084 |
| hexaco | 0.886 | 0.835 | -0.051 |
| scenario | 0.929 | 0.880 | -0.049 |
| behavioral | 0.948 | 0.922 | -0.026 |
| narrative | 0.950 | 0.933 | -0.017 |

**Clinical instruments only (PHQ-9 + GAD-7)**:

| Encoding | Exp 6 | Exp 14 | Δ |
|----------|-------|--------|------|
| ocean_direct | 0.918 | 0.627 | -0.291 |
| hexaco | 0.764 | 0.481 | -0.284 |
| exemplar | 0.853 | 0.732 | -0.121 |
| behavioral | 0.915 | 0.811 | -0.104 |
| narrative | 0.887 | 0.792 | -0.094 |
| scenario | 0.846 | 0.818 | **-0.028** |

**Pattern**: Scenario and narrative encodings protect clinical instruments. Ocean_direct and hexaco encodings allow collapse. The effect is stronger for clinical instruments than personality instruments.

---

## Finding 4: Profile Extremity Effect

Degradation varies by profile valence:

| Profile Type | Exp 6 | Exp 14 | Δ |
|--------------|-------|--------|------|
| extreme_negative | 0.869 | 0.629 | **-0.240** |
| negative | 0.892 | 0.813 | -0.078 |
| neutral | 0.905 | 0.935 | +0.030 |
| positive | 0.919 | 0.931 | +0.012 |
| extreme_positive | 0.863 | 0.690 | **-0.173** |

**Pattern**: Both extremes collapse. Moderate profiles hold or improve. This is not about negativity—it's about extremity.

---

## Finding 5: Worst-Case Combinations

Most degraded instrument × encoding combinations:

| Combination | Exp 6 | Exp 14 | Δ |
|-------------|-------|--------|------|
| PHQ-9 × behavioral | 0.859 | 0.302 | -0.556 |
| GAD-7 × hexaco | 0.847 | 0.336 | -0.511 |
| PHQ-9 × ocean_direct | 0.896 | 0.442 | -0.454 |
| GAD-7 × ocean_direct | 0.937 | 0.726 | -0.211 |
| BFI × ocean_direct | 0.922 | 0.724 | -0.198 |

Most stable combinations:

| Combination | Exp 6 | Exp 14 | Δ |
|-------------|-------|--------|------|
| BFI × exemplar | 0.661 | 0.782 | +0.121 |
| Dark Triad × ocean_direct | 0.696 | 0.727 | +0.031 |
| Levenson × ocean_direct | 0.783 | 0.809 | +0.027 |
| GAD-7 × behavioral | 0.948 | 0.947 | -0.001 |

**Pattern**: The effects interact multiplicatively. Clinical instrument + sparse encoding + extreme profile produces catastrophic failure. Personality instrument + any encoding holds.

---

## Current Hypothesis

Degradation is a three-way interaction:

1. **Instrument framing**: Clinical self-assessment ("over the past 2 weeks, how often have you...") vs personality description ("I am someone who...")

2. **Encoding richness**: Sparse/abstract (ocean_direct: "O=80, C=60...") vs rich/narrative (exemplar: "Like Maya, a thoughtful artist who...")

3. **Profile extremity**: Extreme configurations vs moderate configurations

Models appear to maintain character consistency when given human-like descriptions (exemplar, narrative, scenario) but struggle with abstract clinical self-assessment under accumulating context.

**Possible mechanism**: Models are trained on narratives about people, not numerical personality coordinates. Rich encodings match training distribution; sparse encodings do not. Clinical framing asks for moment-to-moment self-assessment, which models have learned should fluctuate. Under longitudinal conditions, these factors compound.

---

## Implications

1. **For methodology**: Prior AI personality research using clinical instruments may be unreliable if administered longitudinally. Cross-sectional findings may not generalize to conversational settings.

2. **For application**: AI systems in extended conversations should avoid clinical self-assessment framing. Character-based personality programming (exemplar, narrative) is more stable than coordinate-based programming.

3. **For theory**: The "personality attractor" concept holds for dispositional content but may not apply uniformly across framing types. Attractors may be deeper for trait-language than state-language, and deeper for rich encodings than sparse encodings.

---

## Next Steps

### Immediate
- [ ] Archive Exp 6, 14, 15 outputs to GitHub
- [ ] Document instrument definitions and encoding methods
- [ ] Preserve analysis scripts

### Probe Series (BR-01 onwards)
- [ ] BR-01: Length degradation (80 items, mixed content)
- [ ] BR-02: Length degradation (affect only)  
- [ ] BR-03: Length degradation (behavioral only)
- [ ] BR-04: Repetition drift (same items at intervals)
- [ ] BR-05: Anchoring test (explicit vs implicit continuity)

### Confirmatory Experiments
- [ ] Test clinical vs personality framing with matched content
- [ ] Test encoding richness with matched instruments
- [ ] Test profile extremity with matched encodings
- [ ] Factorial design: Framing × Encoding × Extremity

---

## Files

### Data
- `x6_vs_x14.csv`: Raw comparison data
- `PHQ9_vs_PHQ6BC_vs_PHQ3A_*.csv`: Experiment 15 outputs

### Analysis
- `exp6_vs_exp14_analysis.py`: Instrument and profile degradation
- `deep_dive_analysis.py`: Interaction analysis
- `phq_split_analysis.py`: Affect hypothesis test

### Instruments
- `br01.py`: Length degradation probe (ready to run)

---

## Changelog

**31 Dec 2025**: Initial writeup. Affect hypothesis falsified. Interaction hypothesis proposed.
