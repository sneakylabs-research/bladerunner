"""
Bladerunner Paper Analytics

Rigorous statistical analysis for publication:
- Fidelity analysis (OCEAN → outcome mapping)
- Bootstrap confidence intervals
- Hartigan's dip test for multimodality
- Residual variance decomposition

Usage: python -m bladerunner_runner.analytics_paper --exp 6
Writes to experiment_6_output/paper_analysis.txt
"""

import math
import json
import random
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime


def calc_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0


def calc_variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0
    mean = calc_mean(values)
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)


def calc_sd(values: List[float]) -> float:
    return math.sqrt(calc_variance(values))


def pearson_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 3:
        return 0.0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
    sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
    
    denominator = math.sqrt(sum_sq_x * sum_sq_y)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def get_experiment_row_id(db, experiment_number: int) -> int:
    """Look up row id from experiment_number."""
    result = db.query(
        "SELECT id FROM experiments WHERE experiment_number = ?",
        (experiment_number,)
    )
    if not result:
        raise ValueError(f"No experiment found with experiment_number = {experiment_number}")
    return result[0]['id']


class PaperAnalyzer:
    """Publication-quality statistical analysis."""
    
    def __init__(self, experiment_number: int):
        self.experiment_number = experiment_number
        from bladerunner_runner.db import get_db
        self.db = get_db()
        self.row_id = get_experiment_row_id(self.db, experiment_number)
        self._results = None
        self._output_lines = []
    
    def _log(self, line: str = ""):
        """Log line to both console and buffer."""
        print(line)
        self._output_lines.append(line)
    
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
                for field in ['O', 'C', 'E', 'A', 'N']:
                    if r[field] is not None:
                        r[field] = float(r[field])
        return self._results
    
    # =========================================================================
    # FIDELITY ANALYSIS: Does OCEAN predict outcomes correctly?
    # =========================================================================
    
    def fidelity_analysis(self) -> Dict:
        """
        Test nomological validity: Do OCEAN assignments predict 
        instrument outcomes as expected?
        """
        results = self.get_results()
        
        ocean_factors = ['O', 'C', 'E', 'A', 'N']
        instruments = list(set(r['instrument'] for r in results))
        
        correlations = {}
        
        for instrument in instruments:
            inst_results = [r for r in results if r['instrument'] == instrument]
            
            correlations[instrument] = {}
            
            for factor in ocean_factors:
                x = [r[factor] for r in inst_results]
                y = [r['total_score'] for r in inst_results]
                
                r = pearson_correlation(x, y)
                correlations[instrument][factor] = r
        
        expected = {
            'levenson': {'O': 0, 'C': -1, 'E': 0, 'A': -1, 'N': 0},
            'dark_triad': {'O': 0, 'C': -1, 'E': 0, 'A': -1, 'N': 0},
            'phq9': {'O': 0, 'C': 0, 'E': -1, 'A': 0, 'N': 1},
            'gad7': {'O': 0, 'C': 0, 'E': -1, 'A': 0, 'N': 1},
            'bfi': {'O': 1, 'C': 1, 'E': 1, 'A': 1, 'N': 1},
        }
        
        fidelity = {}
        for instrument in correlations:
            if instrument in expected:
                matches = 0
                total_expected = 0
                details = {}
                
                for factor in ocean_factors:
                    observed_r = correlations[instrument][factor]
                    expected_dir = expected[instrument][factor]
                    
                    if expected_dir != 0:
                        total_expected += 1
                        observed_dir = 1 if observed_r > 0.1 else (-1 if observed_r < -0.1 else 0)
                        
                        match = (expected_dir == observed_dir)
                        if match:
                            matches += 1
                        
                        details[factor] = {
                            'expected': expected_dir,
                            'observed_r': observed_r,
                            'match': match
                        }
                
                fidelity[instrument] = {
                    'correlations': correlations[instrument],
                    'fidelity_score': matches / total_expected if total_expected > 0 else 0,
                    'matches': matches,
                    'total_expected': total_expected,
                    'details': details
                }
        
        return fidelity
    
    def print_fidelity(self):
        """Print fidelity analysis."""
        self._log()
        self._log("=" * 70)
        self._log("FIDELITY ANALYSIS: OCEAN → Outcome Mapping")
        self._log("=" * 70)
        self._log("\nDoes personality programming produce expected outcomes?")
        
        fidelity = self.fidelity_analysis()
        
        self._log("\n" + "-" * 70)
        self._log("OCEAN-Instrument Correlation Matrix")
        self._log("-" * 70)
        
        header = f"{'Instrument':<15}" + "".join(f"{f:>10}" for f in ['O', 'C', 'E', 'A', 'N'])
        self._log(header)
        self._log("-" * len(header))
        
        for instrument in sorted(fidelity.keys()):
            row = f"{instrument:<15}"
            for factor in ['O', 'C', 'E', 'A', 'N']:
                r = fidelity[instrument]['correlations'][factor]
                row += f"{r:>10.3f}"
            self._log(row)
        
        self._log("\n" + "-" * 70)
        self._log("Fidelity Scores (Direction Match)")
        self._log("-" * 70)
        
        for instrument in sorted(fidelity.keys()):
            f = fidelity[instrument]
            score_pct = f['fidelity_score'] * 100
            indicator = "✓" if score_pct >= 75 else "○" if score_pct >= 50 else "✗"
            self._log(f"  {instrument:<15} {score_pct:>5.0f}% ({f['matches']}/{f['total_expected']}) {indicator}")
            
            for factor, detail in f['details'].items():
                exp = "+" if detail['expected'] > 0 else "-"
                obs = f"{detail['observed_r']:+.3f}"
                match = "✓" if detail['match'] else "✗"
                self._log(f"    {factor}: expected {exp}, observed {obs} {match}")
        
        self._log("\n" + "-" * 70)
        self._log("Key Nomological Predictions")
        self._log("-" * 70)
        
        levenson_a = fidelity.get('levenson', {}).get('correlations', {}).get('A', 0)
        self._log(f"  Low Agreeableness → High Psychopathy: r = {levenson_a:.3f} {'✓' if levenson_a < -0.3 else '✗'}")
        
        phq9_n = fidelity.get('phq9', {}).get('correlations', {}).get('N', 0)
        self._log(f"  High Neuroticism → High Depression:   r = {phq9_n:.3f} {'✓' if phq9_n > 0.3 else '✗'}")
        
        gad7_n = fidelity.get('gad7', {}).get('correlations', {}).get('N', 0)
        self._log(f"  High Neuroticism → High Anxiety:      r = {gad7_n:.3f} {'✓' if gad7_n > 0.3 else '✗'}")
    
    # =========================================================================
    # BOOTSTRAP CONFIDENCE INTERVALS
    # =========================================================================
    
    def bootstrap_ci(self, x: List[float], y: List[float], 
                     n_bootstrap: int = 1000, ci: float = 0.95) -> Tuple[float, float, float]:
        """Calculate bootstrap confidence interval for correlation."""
        if len(x) < 3:
            return (0, 0, 0)
        
        point_estimate = pearson_correlation(x, y)
        
        n = len(x)
        bootstrap_rs = []
        
        random.seed(42)
        
        for _ in range(n_bootstrap):
            indices = [random.randint(0, n-1) for _ in range(n)]
            x_boot = [x[i] for i in indices]
            y_boot = [y[i] for i in indices]
            
            r = pearson_correlation(x_boot, y_boot)
            bootstrap_rs.append(r)
        
        bootstrap_rs.sort()
        alpha = 1 - ci
        lower_idx = int(n_bootstrap * alpha / 2)
        upper_idx = int(n_bootstrap * (1 - alpha / 2))
        
        return (point_estimate, bootstrap_rs[lower_idx], bootstrap_rs[upper_idx])
    
    def cross_model_correlations_with_ci(self) -> Dict:
        """Calculate all cross-model correlations with 95% CIs."""
        results = self.get_results()
        
        grouped = defaultdict(lambda: defaultdict(dict))
        for r in results:
            key = (r['instrument'], r['input_system'], r['profile_label'])
            grouped[r['instrument']][key][r['provider']] = r['total_score']
        
        providers = sorted(set(r['provider'] for r in results))
        correlations_ci = {}
        
        for instrument in grouped:
            correlations_ci[instrument] = {}
            
            for i, p1 in enumerate(providers):
                for p2 in providers[i+1:]:
                    scores1 = []
                    scores2 = []
                    
                    for key, scores in grouped[instrument].items():
                        if p1 in scores and p2 in scores:
                            scores1.append(scores[p1])
                            scores2.append(scores[p2])
                    
                    if len(scores1) >= 10:
                        r, ci_low, ci_high = self.bootstrap_ci(scores1, scores2)
                        correlations_ci[instrument][f"{p1}×{p2}"] = {
                            'r': r,
                            'ci_lower': ci_low,
                            'ci_upper': ci_high,
                            'n': len(scores1)
                        }
        
        return correlations_ci
    
    def print_correlations_with_ci(self):
        """Print cross-model correlations with confidence intervals."""
        self._log()
        self._log("=" * 70)
        self._log("CROSS-MODEL CORRELATIONS WITH 95% CONFIDENCE INTERVALS")
        self._log("=" * 70)
        
        correlations = self.cross_model_correlations_with_ci()
        
        for instrument in sorted(correlations.keys()):
            self._log(f"\n{instrument.upper()}")
            self._log("-" * 50)
            
            for pair in sorted(correlations[instrument].keys()):
                data = correlations[instrument][pair]
                r = data['r']
                ci_low = data['ci_lower']
                ci_high = data['ci_upper']
                n = data['n']
                
                ci_width = ci_high - ci_low
                precision = "tight" if ci_width < 0.1 else "moderate" if ci_width < 0.2 else "wide"
                
                self._log(f"  {pair:<20} r = {r:.3f}  [{ci_low:.3f}, {ci_high:.3f}]  n={n}  ({precision})")
        
        self._log("\n" + "-" * 70)
        self._log("Summary")
        self._log("-" * 70)
        
        all_rs = []
        all_ci_widths = []
        for instrument in correlations:
            for pair, data in correlations[instrument].items():
                all_rs.append(data['r'])
                all_ci_widths.append(data['ci_upper'] - data['ci_lower'])
        
        self._log(f"  Mean correlation: {calc_mean(all_rs):.3f}")
        self._log(f"  Mean CI width: {calc_mean(all_ci_widths):.3f}")
        all_exclude_zero = all(correlations[i][p]['ci_lower'] > 0 for i in correlations for p in correlations[i])
        self._log(f"  All CIs exclude zero: {'Yes' if all_exclude_zero else 'No'}")
    
    # =========================================================================
    # HARTIGAN'S DIP TEST FOR MULTIMODALITY
    # =========================================================================
    
    def hartigans_dip(self, data: List[float]) -> Tuple[float, bool]:
        """Simplified Hartigan's dip test for unimodality."""
        if len(data) < 10:
            return (0, False)
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        def ecdf(x):
            return sum(1 for d in sorted_data if d <= x) / n
        
        max_dip = 0
        
        for i, x in enumerate(sorted_data):
            expected = (i + 0.5) / n
            observed = ecdf(x)
            dip = abs(observed - expected)
            max_dip = max(max_dip, dip)
        
        critical = 0.05 + 0.5 / math.sqrt(n)
        
        is_multimodal = max_dip > critical
        
        return (max_dip, is_multimodal)
    
    def bimodality_coefficient(self, data: List[float]) -> float:
        """Calculate bimodality coefficient. BC > 0.555 suggests bimodality."""
        if len(data) < 4:
            return 0
        
        n = len(data)
        mean = calc_mean(data)
        
        m2 = sum((x - mean) ** 2 for x in data) / n
        m3 = sum((x - mean) ** 3 for x in data) / n
        m4 = sum((x - mean) ** 4 for x in data) / n
        
        if m2 == 0:
            return 0
        
        skewness = m3 / (m2 ** 1.5)
        kurtosis = m4 / (m2 ** 2) - 3
        
        n_factor = 3 * ((n - 1) ** 2) / ((n - 2) * (n - 3))
        bc = (skewness ** 2 + 1) / (kurtosis + n_factor)
        
        return bc
    
    def multimodality_analysis(self) -> Dict:
        """Analyze score distributions for multimodality."""
        results = self.get_results()
        
        by_instrument = defaultdict(list)
        for r in results:
            by_instrument[r['instrument']].append(r['total_score'])
        
        analysis = {}
        
        for instrument, scores in by_instrument.items():
            dip_stat, is_multimodal_dip = self.hartigans_dip(scores)
            bc = self.bimodality_coefficient(scores)
            
            analysis[instrument] = {
                'n': len(scores),
                'mean': calc_mean(scores),
                'sd': calc_sd(scores),
                'dip_statistic': dip_stat,
                'multimodal_dip': is_multimodal_dip,
                'bimodality_coefficient': bc,
                'multimodal_bc': bc > 0.555,
                'conclusion': 'MULTIMODAL' if (is_multimodal_dip or bc > 0.555) else 'UNIMODAL'
            }
        
        return analysis
    
    def print_multimodality(self):
        """Print multimodality analysis."""
        self._log()
        self._log("=" * 70)
        self._log("MULTIMODALITY ANALYSIS: Evidence for Discrete Attractors")
        self._log("=" * 70)
        
        analysis = self.multimodality_analysis()
        
        self._log(f"\n{'Instrument':<15} {'Dip Stat':>10} {'BC':>10} {'Conclusion':<15}")
        self._log("-" * 55)
        
        for instrument in sorted(analysis.keys()):
            data = analysis[instrument]
            self._log(f"{instrument:<15} {data['dip_statistic']:>10.3f} {data['bimodality_coefficient']:>10.3f} {data['conclusion']:<15}")
        
        self._log("\n" + "-" * 70)
        self._log("Interpretation:")
        self._log("  Dip Statistic: Higher values suggest multimodality")
        self._log("  Bimodality Coefficient: BC > 0.555 suggests bimodality")
        
        multimodal = [i for i, d in analysis.items() if d['conclusion'] == 'MULTIMODAL']
        if multimodal:
            self._log(f"\n  Evidence for discrete attractors in: {', '.join(multimodal)}")
        else:
            self._log("\n  No strong evidence for multimodality")
    
    # =========================================================================
    # RESIDUAL VARIANCE DECOMPOSITION
    # =========================================================================
    
    def residual_analysis(self) -> Dict:
        """Decompose residual variance."""
        results = self.get_results()
        
        all_scores = [r['total_score'] for r in results]
        grand_mean = calc_mean(all_scores)
        total_ss = sum((s - grand_mean) ** 2 for s in all_scores)
        
        by_profile = defaultdict(list)
        for r in results:
            by_profile[r['profile_label']].append(r['total_score'])
        
        profile_means = {p: calc_mean(scores) for p, scores in by_profile.items()}
        ss_between_profile = sum(
            len(scores) * (profile_means[p] - grand_mean) ** 2
            for p, scores in by_profile.items()
        )
        
        ss_within_profile = sum(
            sum((s - profile_means[p]) ** 2 for s in scores)
            for p, scores in by_profile.items()
        )
        
        by_profile_provider = defaultdict(lambda: defaultdict(list))
        for r in results:
            by_profile_provider[r['profile_label']][r['provider']].append(r['total_score'])
        
        ss_provider_within_profile = 0
        ss_pure_residual = 0
        
        for profile in by_profile_provider:
            profile_scores = by_profile[profile]
            profile_mean = calc_mean(profile_scores)
            
            for provider, scores in by_profile_provider[profile].items():
                provider_mean = calc_mean(scores)
                
                ss_provider_within_profile += len(scores) * (provider_mean - profile_mean) ** 2
                ss_pure_residual += sum((s - provider_mean) ** 2 for s in scores)
        
        decomposition = {
            'total_ss': total_ss,
            'ss_between_profile': ss_between_profile,
            'ss_within_profile': ss_within_profile,
            'ss_provider_within_profile': ss_provider_within_profile,
            'ss_pure_residual': ss_pure_residual,
            'proportions': {
                'profile': ss_between_profile / total_ss if total_ss > 0 else 0,
                'provider_within_profile': ss_provider_within_profile / total_ss if total_ss > 0 else 0,
                'pure_residual': ss_pure_residual / total_ss if total_ss > 0 else 0,
            }
        }
        
        return decomposition
    
    def print_residual_analysis(self):
        """Print residual variance analysis."""
        self._log()
        self._log("=" * 70)
        self._log("RESIDUAL VARIANCE DECOMPOSITION: What's the 66%?")
        self._log("=" * 70)
        
        decomp = self.residual_analysis()
        
        self._log("\nVariance Components:")
        self._log("-" * 50)
        
        props = decomp['proportions']
        
        components = [
            ('Between profiles', props['profile']),
            ('Provider (within profile)', props['provider_within_profile']),
            ('Pure residual', props['pure_residual']),
        ]
        
        for name, prop in components:
            pct = prop * 100
            bar = "█" * int(pct / 2)
            self._log(f"  {name:<30} {pct:>6.1f}%  {bar}")
        
        self._log("\n" + "-" * 70)
        self._log("Interpretation of Pure Residual:")
        self._log("-" * 70)
        
        pure_residual_pct = props['pure_residual'] * 100
        
        self._log(f"\n  Pure residual = {pure_residual_pct:.1f}%")
        self._log("\n  This captures variance from:")
        self._log("    - Input system differences (within same profile-provider)")
        self._log("    - Instrument differences (within same profile-provider)")
        self._log("    - Random response variation")
        self._log("    - Question-level noise")
        
        if pure_residual_pct > 50:
            self._log("\n  ⚠️  High residual suggests significant unmeasured factors")
        else:
            self._log("\n  ✓  Residual within acceptable range for psychological measurement")
    
    # =========================================================================
    # RUN ALL
    # =========================================================================
    
    def run_full_analysis(self):
        """Run all paper-quality analyses."""
        self._log()
        self._log("=" * 70)
        self._log("BLADERUNNER PAPER ANALYTICS")
        self._log(f"Experiment: {self.experiment_number}")
        self._log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("=" * 70)
        
        self.print_fidelity()
        self.print_correlations_with_ci()
        self.print_multimodality()
        self.print_residual_analysis()
        
        self._log()
        self._log("=" * 70)
        self._log("ANALYSIS COMPLETE")
        self._log("=" * 70)
        
        # Write to file
        output_dir = Path(f"experiment_{self.experiment_number}_output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "paper_analysis.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._output_lines))
        
        print(f"\n📁 Written to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Bladerunner Paper Analytics')
    parser.add_argument('--exp', type=int, required=True, 
                        help='Experiment number (not row id)')
    args = parser.parse_args()
    
    analyzer = PaperAnalyzer(args.exp)
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()