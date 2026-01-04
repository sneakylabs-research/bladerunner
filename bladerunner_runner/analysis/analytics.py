"""
Bladerunner Analytics Module - Publication Quality

Generates:
- Omnibus report (Markdown + HTML)
- CSV exports (raw, correlations, summary)
- Visualizations (bar chart, heatmap)

Usage: python -m bladerunner_runner.analytics --exp 6
Target: AI researchers, devs, investors
"""

import os
import math
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CorrelationResult:
    """Result of correlation between two providers."""
    provider1: str
    provider2: str
    instrument: str
    input_system: str
    correlation: float
    p_value: float
    n: int


@dataclass 
class DescriptiveStats:
    """Descriptive statistics for a group."""
    n: int
    mean: float
    sd: float
    min_val: float
    max_val: float
    median: float


def pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Calculate Pearson r and p-value."""
    x = [float(v) for v in x]
    y = [float(v) for v in y]
    
    if len(x) != len(y) or len(x) < 3:
        return 0.0, 1.0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
    
    if denominator == 0:
        return 0.0, 1.0
    
    r = numerator / denominator
    
    # Calculate p-value using t-distribution approximation
    if abs(r) >= 1:
        p_value = 0.0 if abs(r) == 1 else 1.0
    else:
        t_stat = r * math.sqrt((n - 2) / (1 - r ** 2))
        # Two-tailed p-value approximation
        p_value = two_tailed_t_pvalue(t_stat, n - 2)
    
    return r, p_value


def two_tailed_t_pvalue(t: float, df: int) -> float:
    """Approximate two-tailed p-value for t-distribution."""
    if df <= 0:
        return 1.0
    
    # Simple approximation using normal for large df
    if df > 30:
        z = abs(t)
        # Rough CDF approximation
        p_value = 2 * (1 - (1 / (1 + math.exp(-1.7 * z))))
        return min(1.0, max(0.0, p_value))
    
    # For smaller df, use crude approximation
    x = df / (df + t ** 2)
    a = 0.5 * df
    
    # Regularized incomplete beta approximation
    p_one_tail = 0.5 * (1 - math.copysign(1, t) * (1 - x ** a))
    return min(1.0, max(0.0, 2 * min(p_one_tail, 1 - p_one_tail)))


def independent_t_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Independent samples t-test. Returns t-statistic and p-value."""
    n1, n2 = len(group1), len(group2)
    
    if n1 < 2 or n2 < 2:
        return 0.0, 1.0
    
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)
    
    # Pooled standard error
    se = math.sqrt(var1 / n1 + var2 / n2)
    
    if se == 0:
        return 0.0, 1.0
    
    t_stat = (mean1 - mean2) / se
    
    # Welch's degrees of freedom
    if var1 / n1 + var2 / n2 == 0:
        df = n1 + n2 - 2
    else:
        df = ((var1 / n1 + var2 / n2) ** 2) / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )
    
    p_value = two_tailed_t_pvalue(t_stat, int(df))
    
    return t_stat, p_value


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1 = sum(group1) / n1
    mean2 = sum(group2) / n2
    
    var1 = sum((x - mean1) ** 2 for x in group1) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in group2) / (n2 - 1)
    
    # Pooled standard deviation
    pooled_sd = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_sd == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_sd


def calc_descriptive_stats(values: List[float]) -> DescriptiveStats:
    """Calculate descriptive statistics."""
    if not values:
        return DescriptiveStats(0, 0, 0, 0, 0, 0)
    
    n = len(values)
    mean = sum(values) / n
    
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        sd = math.sqrt(variance)
    else:
        sd = 0
    
    sorted_vals = sorted(values)
    median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    
    return DescriptiveStats(
        n=n,
        mean=mean,
        sd=sd,
        min_val=min(values),
        max_val=max(values),
        median=median
    )


def get_experiment_row_id(db, experiment_number: int) -> int:
    """Look up row id from experiment_number."""
    result = db.query(
        "SELECT id FROM experiments WHERE experiment_number = ?",
        (experiment_number,)
    )
    if not result:
        raise ValueError(f"No experiment found with experiment_number = {experiment_number}")
    return result[0]['id']


class ExperimentAnalyzer:
    """Full experiment analysis for publication."""
    
    # Instrument classification for H1 test
    INSTRUMENT_TYPES = {
        'levenson': 'Clinical',
        'phq9': 'Clinical',
        'gad7': 'Clinical',
        'dark_triad': 'Mixed',
        'bfi': 'Normal',
    }
    
    def __init__(self, experiment_number: int):
        self.experiment_number = experiment_number
        from bladerunner_runner.db import get_db
        self.db = get_db()
        
        # Look up row id from experiment_number
        self.row_id = get_experiment_row_id(self.db, experiment_number)
        
        # Load experiment info
        self.experiment = self.db.query_one(
            "SELECT * FROM experiments WHERE id = ?", (self.row_id,)
        )
        
        # Cache for computed results
        self._results = None
        self._correlations = None
    
    def get_results(self) -> List[Dict]:
        """Get all completed results."""
        if self._results is None:
            self._results = self.db.query("""
                SELECT 
                    tc.id as test_case_id,
                    tc.provider,
                    tc.instrument,
                    tc.input_system,
                    tc.O, tc.C, tc.E, tc.A, tc.N,
                    tc.profile_label,
                    r.total_score,
                    r.factor_scores,
                    r.questions_answered,
                    r.questions_total
                FROM test_cases tc
                JOIN results r ON r.test_case_id = tc.id
                WHERE tc.experiment_id = ?
                  AND tc.status = 'complete'
                ORDER BY tc.instrument, tc.input_system, tc.profile_label, tc.provider
            """, (self.row_id,))

            for r in self._results:
                if r['total_score'] is not None:
                    r['total_score'] = float(r['total_score'])

        return self._results
    
    def get_experiment_config(self) -> Dict:
        """Get experiment configuration."""
        results = self.get_results()
        
        if not results:
            return {}
        
        providers = sorted(set(r['provider'] for r in results))
        instruments = sorted(set(r['instrument'] for r in results))
        input_systems = sorted(set(r['input_system'] for r in results))
        profiles = sorted(set(r['profile_label'] for r in results))
        
        return {
            'providers': providers,
            'instruments': instruments,
            'input_systems': input_systems,
            'profiles': profiles,
            'n_providers': len(providers),
            'n_instruments': len(instruments),
            'n_input_systems': len(input_systems),
            'n_profiles': len(profiles),
            'n_test_cases': len(results),
            'n_completions': sum(r['questions_answered'] for r in results),
        }
    
    def calc_cross_provider_correlations(self) -> List[CorrelationResult]:
        """Calculate all cross-provider correlations."""
        if self._correlations is not None:
            return self._correlations
        
        results = self.get_results()
        
        if not results:
            return []
        
        # Group by instrument, input_system, profile_label
        grouped = {}
        for r in results:
            key = (r['instrument'], r['input_system'], r['profile_label'])
            if key not in grouped:
                grouped[key] = {}
            grouped[key][r['provider']] = r['total_score']
        
        config = self.get_experiment_config()
        providers = config['providers']
        instruments = config['instruments']
        input_systems = config['input_systems']
        
        correlations = []
        
        for instrument in instruments:
            for inp_sys in input_systems:
                # Build aligned score vectors
                provider_scores = {p: [] for p in providers}
                
                for (inst, inp, profile), scores in grouped.items():
                    if inst != instrument or inp != inp_sys:
                        continue
                    
                    if all(p in scores for p in providers):
                        for p in providers:
                            provider_scores[p].append(scores[p])
                
                # Pairwise correlations
                for i, p1 in enumerate(providers):
                    for p2 in providers[i+1:]:
                        if len(provider_scores[p1]) >= 3:
                            r, p_val = pearson_correlation(
                                provider_scores[p1], 
                                provider_scores[p2]
                            )
                            correlations.append(CorrelationResult(
                                provider1=p1,
                                provider2=p2,
                                instrument=instrument,
                                input_system=inp_sys,
                                correlation=r,
                                p_value=p_val,
                                n=len(provider_scores[p1])
                            ))
        
        self._correlations = correlations
        return correlations
    
    def calc_reliability_by_instrument(self) -> Dict[str, Dict]:
        """Calculate mean reliability per instrument with stats."""
        correlations = self.calc_cross_provider_correlations()
        
        by_instrument = {}
        for c in correlations:
            if c.instrument not in by_instrument:
                by_instrument[c.instrument] = []
            by_instrument[c.instrument].append(c.correlation)
        
        results = {}
        for instrument, corrs in by_instrument.items():
            stats = calc_descriptive_stats(corrs)
            results[instrument] = {
                'type': self.INSTRUMENT_TYPES.get(instrument, 'Unknown'),
                'mean_r': stats.mean,
                'sd_r': stats.sd,
                'min_r': stats.min_val,
                'max_r': stats.max_val,
                'n_pairs': stats.n,
            }
        
        return results
    
    def calc_reliability_by_input_system(self) -> Dict[str, Dict]:
        """Calculate mean reliability per input system."""
        correlations = self.calc_cross_provider_correlations()
        
        by_system = {}
        for c in correlations:
            if c.input_system not in by_system:
                by_system[c.input_system] = []
            by_system[c.input_system].append(c.correlation)
        
        results = {}
        for system, corrs in by_system.items():
            stats = calc_descriptive_stats(corrs)
            results[system] = {
                'mean_r': stats.mean,
                'sd_r': stats.sd,
                'n_pairs': stats.n,
            }
        
        return results
    
    def calc_descriptive_by_instrument(self) -> Dict[str, DescriptiveStats]:
        """Calculate descriptive stats for total scores by instrument."""
        results = self.get_results()
        
        by_instrument = {}
        for r in results:
            if r['instrument'] not in by_instrument:
                by_instrument[r['instrument']] = []
            by_instrument[r['instrument']].append(r['total_score'])
        
        return {
            inst: calc_descriptive_stats(scores)
            for inst, scores in by_instrument.items()
        }
    
    def test_h1(self) -> Dict:
        """
        Test H1: Clinical/dark traits form discrete attractors.
        
        Compare clinical instrument reliability vs normal.
        """
        reliability = self.calc_reliability_by_instrument()
        
        clinical_rs = []
        mixed_rs = []
        normal_rs = []
        
        for instrument, stats in reliability.items():
            if stats['type'] == 'Clinical':
                clinical_rs.append(stats['mean_r'])
            elif stats['type'] == 'Mixed':
                mixed_rs.append(stats['mean_r'])
            elif stats['type'] == 'Normal':
                normal_rs.append(stats['mean_r'])
        
        result = {
            'clinical_mean': sum(clinical_rs) / len(clinical_rs) if clinical_rs else 0,
            'clinical_n': len(clinical_rs),
            'mixed_mean': sum(mixed_rs) / len(mixed_rs) if mixed_rs else 0,
            'mixed_n': len(mixed_rs),
            'normal_mean': sum(normal_rs) / len(normal_rs) if normal_rs else 0,
            'normal_n': len(normal_rs),
        }
        
        # Statistical test: clinical vs normal
        if clinical_rs and normal_rs:
            # Get all individual correlations for each type
            correlations = self.calc_cross_provider_correlations()
            
            clinical_all = [c.correlation for c in correlations 
                          if self.INSTRUMENT_TYPES.get(c.instrument) == 'Clinical']
            normal_all = [c.correlation for c in correlations 
                         if self.INSTRUMENT_TYPES.get(c.instrument) == 'Normal']
            
            if len(clinical_all) >= 2 and len(normal_all) >= 2:
                t_stat, p_value = independent_t_test(clinical_all, normal_all)
                d = cohens_d(clinical_all, normal_all)
                
                result['t_statistic'] = t_stat
                result['p_value'] = p_value
                result['cohens_d'] = d
                result['effect_size'] = (
                    'Large' if abs(d) >= 0.8 else
                    'Medium' if abs(d) >= 0.5 else
                    'Small' if abs(d) >= 0.2 else
                    'Negligible'
                )
        
        # Verdict
        if result['clinical_mean'] > 0.7 and result['normal_mean'] < 0.5:
            result['verdict'] = 'SUPPORTED'
        elif result['clinical_mean'] > result['normal_mean']:
            result['verdict'] = 'PARTIALLY SUPPORTED'
        else:
            result['verdict'] = 'NOT SUPPORTED'
        
        return result
    
    def generate_report(self) -> str:
        """Generate full omnibus report in Markdown."""
        config = self.get_experiment_config()
        
        if not config:
            return "# Error\n\nNo data available for this experiment."
        
        reliability = self.calc_reliability_by_instrument()
        reliability_by_system = self.calc_reliability_by_input_system()
        descriptive = self.calc_descriptive_by_instrument()
        h1_result = self.test_h1()
        correlations = self.calc_cross_provider_correlations()
        
        lines = []
        
        # Title
        exp_name = self.experiment['name'] if self.experiment else f"Experiment {self.experiment_number}"
        lines.append(f"# Bladerunner Experiment Report: {exp_name}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Experiment:** {self.experiment_number}")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"**H1 Result:** {h1_result['verdict']}")
        lines.append("")
        lines.append(f"- Clinical instruments mean r = {h1_result['clinical_mean']:.3f}")
        lines.append(f"- Normal instruments mean r = {h1_result['normal_mean']:.3f}")
        if 'p_value' in h1_result:
            p_str = f"p < .001" if h1_result['p_value'] < 0.001 else f"p = {h1_result['p_value']:.3f}"
            lines.append(f"- Difference: t = {h1_result['t_statistic']:.2f}, {p_str}")
            lines.append(f"- Effect size: Cohen's d = {h1_result['cohens_d']:.2f} ({h1_result['effect_size']})")
        lines.append("")
        
        # Methods
        lines.append("## Methods")
        lines.append("")
        lines.append("### Design")
        lines.append("")
        lines.append(f"- **Providers:** {config['n_providers']} ({', '.join(config['providers'])})")
        lines.append(f"- **Instruments:** {config['n_instruments']} ({', '.join(config['instruments'])})")
        lines.append(f"- **Input Systems:** {config['n_input_systems']} ({', '.join(config['input_systems'])})")
        lines.append(f"- **Personality Profiles:** {config['n_profiles']}")
        lines.append(f"- **Total Test Cases:** {config['n_test_cases']}")
        lines.append(f"- **Total Completions:** {config['n_completions']:,}")
        lines.append("")
        
        lines.append("### Instruments")
        lines.append("")
        lines.append("| Instrument | Type | Questions |")
        lines.append("|------------|------|-----------|")
        instrument_questions = {
            'levenson': 26, 'bfi': 44, 'dark_triad': 27, 'phq9': 9, 'gad7': 7
        }
        for inst in config['instruments']:
            inst_type = self.INSTRUMENT_TYPES.get(inst, 'Unknown')
            n_q = instrument_questions.get(inst, '?')
            lines.append(f"| {inst} | {inst_type} | {n_q} |")
        lines.append("")
        
        lines.append("### Hypothesis")
        lines.append("")
        lines.append("**H1:** Clinical/dark personality traits form discrete attractors in LLM parameter space,")
        lines.append("while normal personality variation represents noise.")
        lines.append("")
        lines.append("**Predictions:**")
        lines.append("- Clinical instruments (Levenson, PHQ9, GAD7): r > 0.8")
        lines.append("- Mixed instruments (Dark Triad): r ≈ 0.6")
        lines.append("- Normal instruments (BFI): r < 0.4")
        lines.append("")
        
        # Results
        lines.append("## Results")
        lines.append("")
        
        # Table 1: Descriptive Statistics
        lines.append("### Table 1: Descriptive Statistics by Instrument")
        lines.append("")
        lines.append("| Instrument | Type | N | Mean | SD | Min | Max |")
        lines.append("|------------|------|---|------|-----|-----|-----|")
        for inst in sorted(descriptive.keys()):
            stats = descriptive[inst]
            inst_type = self.INSTRUMENT_TYPES.get(inst, '?')
            lines.append(f"| {inst} | {inst_type} | {stats.n} | {stats.mean:.1f} | {stats.sd:.1f} | {stats.min_val:.1f} | {stats.max_val:.1f} |")
        lines.append("")
        
        # Table 2: H1 Test Results
        lines.append("### Table 2: Cross-Model Reliability by Instrument (H1 Test)")
        lines.append("")
        lines.append("| Instrument | Type | Mean r | SD | Range | Prediction | Result |")
        lines.append("|------------|------|--------|-----|-------|------------|--------|")
        
        predictions = {
            'Clinical': '> 0.8',
            'Mixed': '≈ 0.6', 
            'Normal': '< 0.4'
        }
        
        for inst in sorted(reliability.keys(), key=lambda x: reliability[x]['mean_r'], reverse=True):
            r = reliability[inst]
            pred = predictions.get(r['type'], '?')
            
            # Determine if prediction met
            if r['type'] == 'Clinical':
                result_mark = '✓' if r['mean_r'] > 0.8 else '○' if r['mean_r'] > 0.6 else '✗'
            elif r['type'] == 'Mixed':
                result_mark = '✓' if 0.5 < r['mean_r'] < 0.75 else '○'
            elif r['type'] == 'Normal':
                result_mark = '✓' if r['mean_r'] < 0.4 else '○' if r['mean_r'] < 0.6 else '✗'
            else:
                result_mark = '?'
            
            range_str = f"{r['min_r']:.2f}-{r['max_r']:.2f}"
            lines.append(f"| {inst} | {r['type']} | {r['mean_r']:.3f} | {r['sd_r']:.3f} | {range_str} | {pred} | {result_mark} |")
        lines.append("")
        
        # Table 3: Input System Comparison
        lines.append("### Table 3: Reliability by Input System")
        lines.append("")
        lines.append("| Input System | Mean r | SD | N |")
        lines.append("|--------------|--------|-----|---|")
        for system in sorted(reliability_by_system.keys(), key=lambda x: reliability_by_system[x]['mean_r'], reverse=True):
            r = reliability_by_system[system]
            lines.append(f"| {system} | {r['mean_r']:.3f} | {r['sd_r']:.3f} | {r['n_pairs']} |")
        lines.append("")
        
        # Table 4: Full Correlation Matrix
        lines.append("### Table 4: Cross-Provider Correlations by Instrument")
        lines.append("")
        
        # Group by provider pair
        pair_corrs = {}
        for c in correlations:
            pair = f"{c.provider1} × {c.provider2}"
            if pair not in pair_corrs:
                pair_corrs[pair] = {}
            if c.instrument not in pair_corrs[pair]:
                pair_corrs[pair][c.instrument] = []
            pair_corrs[pair][c.instrument].append(c.correlation)
        
        # Average across input systems
        instruments = sorted(config['instruments'])
        header = "| Provider Pair | " + " | ".join(instruments) + " |"
        separator = "|---------------|" + "|".join(["------"] * len(instruments)) + "|"
        lines.append(header)
        lines.append(separator)
        
        for pair in sorted(pair_corrs.keys()):
            row = [pair]
            for inst in instruments:
                if inst in pair_corrs[pair]:
                    mean_r = sum(pair_corrs[pair][inst]) / len(pair_corrs[pair][inst])
                    row.append(f"{mean_r:.3f}")
                else:
                    row.append("-")
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        
        # Statistical Tests
        lines.append("### Statistical Tests")
        lines.append("")
        lines.append("**H1 Test: Clinical vs Normal Reliability**")
        lines.append("")
        if 'p_value' in h1_result:
            p_str = "p < .001" if h1_result['p_value'] < 0.001 else f"p = {h1_result['p_value']:.4f}"
            lines.append(f"- t({h1_result.get('clinical_n', 0) + h1_result.get('normal_n', 0) - 2}) = {h1_result['t_statistic']:.3f}, {p_str}")
            lines.append(f"- Cohen's d = {h1_result['cohens_d']:.3f} ({h1_result['effect_size']} effect)")
            lines.append(f"- Clinical mean r = {h1_result['clinical_mean']:.3f} (n = {h1_result['clinical_n']})")
            lines.append(f"- Normal mean r = {h1_result['normal_mean']:.3f} (n = {h1_result['normal_n']})")
        lines.append("")
        
        # Conclusion
        lines.append("## Conclusion")
        lines.append("")
        
        if h1_result['verdict'] == 'SUPPORTED':
            lines.append("**H1 is supported.** Clinical and dark personality traits show significantly higher ")
            lines.append("cross-model reliability than normal personality traits. This suggests that pathological ")
            lines.append("personality constructs form stable attractors in LLM parameter space, while normal ")
            lines.append("personality variation is largely noise.")
        elif h1_result['verdict'] == 'PARTIALLY SUPPORTED':
            lines.append("**H1 is partially supported.** Clinical traits show higher reliability than normal traits, ")
            lines.append("but the difference may not meet all predicted thresholds. Further investigation is needed.")
        else:
            lines.append("**H1 is not supported.** The predicted pattern of clinical > normal reliability ")
            lines.append("was not observed in this experiment.")
        lines.append("")
        
        # Appendix: Methods Detail
        lines.append("## Appendix: Technical Details")
        lines.append("")
        lines.append("### Correlation Calculation")
        lines.append("Pearson correlation coefficients were calculated between provider pairs for each ")
        lines.append("instrument × input system combination. Scores were aligned by personality profile.")
        lines.append("")
        lines.append("### Statistical Significance")
        lines.append("P-values calculated using t-distribution. Effect sizes reported as Cohen's d.")
        lines.append("")
        lines.append("---")
        lines.append(f"*Report generated by Bladerunner Analytics v1.0*")
        
        return "\n".join(lines)
    
    def export_raw_csv(self, filepath: str):
        """Export all raw results to CSV."""
        results = self.get_results()
        
        if not results:
            print("No results to export.")
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'test_case_id', 'provider', 'instrument', 'input_system',
                'O', 'C', 'E', 'A', 'N', 'profile_label',
                'total_score', 'factor_scores', 'questions_answered', 'questions_total'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"Exported {len(results)} results to {filepath}")
    
    def export_correlations_csv(self, filepath: str):
        """Export all correlations to CSV."""
        correlations = self.calc_cross_provider_correlations()
        
        if not correlations:
            print("No correlations to export.")
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'instrument', 'input_system', 'provider1', 'provider2',
                'correlation', 'p_value', 'n'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for c in correlations:
                writer.writerow({
                    'instrument': c.instrument,
                    'input_system': c.input_system,
                    'provider1': c.provider1,
                    'provider2': c.provider2,
                    'correlation': c.correlation,
                    'p_value': c.p_value,
                    'n': c.n
                })
        
        print(f"Exported {len(correlations)} correlations to {filepath}")
    
    def export_summary_csv(self, filepath: str):
        """Export summary statistics to CSV."""
        reliability = self.calc_reliability_by_instrument()
        descriptive = self.calc_descriptive_by_instrument()
        
        rows = []
        for inst in reliability.keys():
            r = reliability[inst]
            d = descriptive.get(inst, DescriptiveStats(0, 0, 0, 0, 0, 0))
            rows.append({
                'instrument': inst,
                'type': r['type'],
                'n_test_cases': d.n,
                'score_mean': d.mean,
                'score_sd': d.sd,
                'score_min': d.min_val,
                'score_max': d.max_val,
                'reliability_mean_r': r['mean_r'],
                'reliability_sd': r['sd_r'],
                'reliability_min': r['min_r'],
                'reliability_max': r['max_r'],
                'n_correlation_pairs': r['n_pairs'],
            })
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(rows[0].keys()) if rows else []
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"Exported summary to {filepath}")
    
    def generate_visualizations(self, output_dir: str):
        """Generate publication-quality visualizations."""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib not installed. Skipping visualizations.")
            print("Install with: pip install matplotlib")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        reliability = self.calc_reliability_by_instrument()
        
        if not reliability:
            print("No reliability data for visualizations.")
            return
        
        # Figure 1: H1 Bar Chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        instruments = sorted(reliability.keys(), key=lambda x: reliability[x]['mean_r'], reverse=True)
        means = [reliability[i]['mean_r'] for i in instruments]
        sds = [reliability[i]['sd_r'] for i in instruments]
        types = [reliability[i]['type'] for i in instruments]
        
        colors = {'Clinical': '#2ecc71', 'Mixed': '#f39c12', 'Normal': '#e74c3c'}
        bar_colors = [colors.get(t, '#95a5a6') for t in types]
        
        bars = ax.bar(instruments, means, yerr=sds, capsize=5, color=bar_colors, edgecolor='black')
        
        ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.7, label='Clinical threshold (0.8)')
        ax.axhline(y=0.4, color='red', linestyle='--', alpha=0.7, label='Normal threshold (0.4)')
        
        ax.set_ylabel('Mean Cross-Model Correlation (r)', fontsize=12)
        ax.set_xlabel('Instrument', fontsize=12)
        ax.set_title('H1 Test: Cross-Model Reliability by Instrument Type', fontsize=14)
        ax.set_ylim(0, 1.0)
        ax.legend(loc='upper right')
        
        # Add type labels
        for i, (bar, inst_type) in enumerate(zip(bars, types)):
            ax.text(bar.get_x() + bar.get_width()/2, 0.02, inst_type, 
                   ha='center', va='bottom', fontsize=9, color='white', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path / 'h1_reliability.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Saved: {output_path / 'h1_reliability.png'}")
        
        # Figure 2: Correlation Heatmap
        correlations = self.calc_cross_provider_correlations()
        config = self.get_experiment_config()
        
        if correlations and len(config.get('providers', [])) > 1:
            try:
                import numpy as np
            except ImportError:
                print("numpy not installed. Skipping heatmap.")
                return
            
            # Build matrix: instruments × provider pairs
            instruments = config['instruments']
            
            # Get unique provider pairs
            pairs = []
            for i, p1 in enumerate(config['providers']):
                for p2 in config['providers'][i+1:]:
                    pairs.append(f"{p1}×{p2}")
            
            if not pairs:
                return
            
            matrix = np.zeros((len(instruments), len(pairs)))
            counts = np.zeros((len(instruments), len(pairs)))
            
            for c in correlations:
                pair = f"{c.provider1}×{c.provider2}"
                if pair in pairs and c.instrument in instruments:
                    i = instruments.index(c.instrument)
                    j = pairs.index(pair)
                    matrix[i, j] += c.correlation
                    counts[i, j] += 1
            
            # Average where we have multiple input systems
            for i in range(len(instruments)):
                for j in range(len(pairs)):
                    if counts[i, j] > 0:
                        matrix[i, j] /= counts[i, j]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
            
            ax.set_xticks(range(len(pairs)))
            ax.set_xticklabels(pairs, rotation=45, ha='right')
            ax.set_yticks(range(len(instruments)))
            ax.set_yticklabels(instruments)
            
            # Add values
            for i in range(len(instruments)):
                for j in range(len(pairs)):
                    val = matrix[i, j]
                    color = 'white' if val < 0.5 else 'black'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center', color=color, fontsize=10)
            
            ax.set_title('Cross-Model Correlation Matrix', fontsize=14)
            plt.colorbar(im, ax=ax, label='Pearson r')
            
            plt.tight_layout()
            plt.savefig(output_path / 'correlation_matrix.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Saved: {output_path / 'correlation_matrix.png'}")
    
    def generate_full_output(self, output_dir: str):
        """Generate complete output package."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        data_path = output_path / 'data'
        data_path.mkdir(exist_ok=True)
        
        figures_path = output_path / 'figures'
        figures_path.mkdir(exist_ok=True)
        
        print(f"\nGenerating output to: {output_path}")
        print("=" * 50)
        
        # Generate report
        print("\n[1/5] Generating report...")
        report = self.generate_report()
        
        with open(output_path / 'report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  Saved: report.md")
        
        # Generate HTML version
        try:
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bladerunner Experiment Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        h1, h2, h3 {{ color: #333; }}
        h1 {{ border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
    </style>
</head>
<body>
{markdown_to_html(report)}
</body>
</html>"""
            with open(output_path / 'report.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"  Saved: report.html")
        except Exception as e:
            print(f"  HTML generation failed: {e}")
        
        # Export CSVs
        print("\n[2/5] Exporting raw data...")
        self.export_raw_csv(str(data_path / 'raw_results.csv'))
        
        print("\n[3/5] Exporting correlations...")
        self.export_correlations_csv(str(data_path / 'correlations.csv'))
        
        print("\n[4/5] Exporting summary...")
        self.export_summary_csv(str(data_path / 'summary_statistics.csv'))
        
        # Generate visualizations
        print("\n[5/5] Generating visualizations...")
        self.generate_visualizations(str(figures_path))
        
        print("\n" + "=" * 50)
        print("COMPLETE!")
        print(f"\nOutput directory: {output_path}")
        print("\nFiles generated:")
        print("  - report.md (Markdown report)")
        print("  - report.html (HTML report)")
        print("  - data/raw_results.csv")
        print("  - data/correlations.csv")
        print("  - data/summary_statistics.csv")
        print("  - figures/h1_reliability.png")
        print("  - figures/correlation_matrix.png")


def markdown_to_html(md: str) -> str:
    """Simple markdown to HTML conversion."""
    import re
    
    html = md
    
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    
    # Tables (simple conversion)
    lines = html.split('\n')
    in_table = False
    new_lines = []
    
    for line in lines:
        if line.startswith('|') and '|' in line[1:]:
            if not in_table:
                new_lines.append('<table>')
                in_table = True
            
            if '---' in line:
                continue  # Skip separator
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if new_lines[-1] == '<table>':
                row = '<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>'
            else:
                row = '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
            new_lines.append(row)
        else:
            if in_table:
                new_lines.append('</table>')
                in_table = False
            new_lines.append(line)
    
    if in_table:
        new_lines.append('</table>')
    
    html = '\n'.join(new_lines)
    
    # Paragraphs
    html = re.sub(r'\n\n', '</p><p>', html)
    html = '<p>' + html + '</p>'
    
    return html


def analyze(experiment_number: int, output_dir: str = None):
    """Quick analysis with full output."""
    analyzer = ExperimentAnalyzer(experiment_number)
    
    if output_dir is None:
        output_dir = f"experiment_{experiment_number}_output"
    
    analyzer.generate_full_output(output_dir)


def main():
    parser = argparse.ArgumentParser(description='Bladerunner Analytics')
    parser.add_argument('--exp', type=int, required=True, 
                        help='Experiment number (not row id)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory (default: experiment_N_output)')
    args = parser.parse_args()
    
    analyze(args.exp, args.output)


if __name__ == "__main__":
    main()