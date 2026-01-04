"""
Bladerunner Expanded Analytics

Adds:
- H4: Factor-level reliability
- H5: Provider bias
- H6: Variance decomposition
- H7: Attractor detection
- PHQ9 Deep Dive

Usage: python -m bladerunner_runner.analytics_expanded --exp 6
Writes to experiment_{number}_output/expanded_analysis.txt
"""

import math
import json
import argparse
from pathlib import Path
from typing import Dict, List
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


def pearson_correlation(x: List[float], y: List[float]):
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 3:
        return 0.0, 0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
    sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
    
    denominator = math.sqrt(sum_sq_x * sum_sq_y)
    
    if denominator == 0:
        return 0.0, n
    
    return numerator / denominator, n


def get_experiment_row_id(db, experiment_number: int) -> int:
    """Look up row id from experiment_number."""
    result = db.query(
        "SELECT id FROM experiments WHERE experiment_number = ?",
        (experiment_number,)
    )
    if not result:
        raise ValueError(f"No experiment found with experiment_number = {experiment_number}")
    return result[0]['id']


class ExpandedAnalyzer:
    """Extended analysis for Bladerunner experiments."""
    
    def __init__(self, experiment_number: int):
        self.experiment_number = experiment_number
        from bladerunner_runner.db import get_db
        self.db = get_db()
        
        # Look up row id from experiment_number
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
        return self._results
    
    # =========================================================================
    # H4: Factor-Level Reliability
    # =========================================================================
    
    def h4_factor_reliability(self) -> Dict:
        """Analyze reliability at factor level, not just total scores."""
        results = self.get_results()
        
        factor_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        for r in results:
            if not r['factor_scores']:
                continue
            
            try:
                factors = json.loads(r['factor_scores']) if isinstance(r['factor_scores'], str) else r['factor_scores']
            except:
                continue
            
            key = (r['instrument'], r['input_system'], r['profile_label'])
            for factor_name, score in factors.items():
                factor_data[r['instrument']][factor_name][key][r['provider']] = float(score)
        
        factor_reliability = {}
        
        for instrument, factors in factor_data.items():
            factor_reliability[instrument] = {}
            
            for factor_name, profiles in factors.items():
                all_providers = set()
                for profile_scores in profiles.values():
                    all_providers.update(profile_scores.keys())
                providers = sorted(all_providers)
                
                if len(providers) < 2:
                    continue
                
                correlations = []
                for i, p1 in enumerate(providers):
                    for p2 in providers[i+1:]:
                        scores1 = []
                        scores2 = []
                        for profile_scores in profiles.values():
                            if p1 in profile_scores and p2 in profile_scores:
                                scores1.append(profile_scores[p1])
                                scores2.append(profile_scores[p2])
                        
                        if len(scores1) >= 3:
                            r, _ = pearson_correlation(scores1, scores2)
                            correlations.append(r)
                
                if correlations:
                    factor_reliability[instrument][factor_name] = {
                        'mean_r': calc_mean(correlations),
                        'sd_r': calc_sd(correlations),
                        'n_pairs': len(correlations)
                    }
        
        return factor_reliability
    
    def print_h4(self):
        """Print H4 factor-level reliability analysis."""
        self._log()
        self._log("=" * 70)
        self._log("H4: FACTOR-LEVEL RELIABILITY")
        self._log("=" * 70)
        
        reliability = self.h4_factor_reliability()
        
        for instrument in sorted(reliability.keys()):
            self._log(f"\n{instrument.upper()}")
            self._log("-" * 40)
            
            factors = reliability[instrument]
            for factor in sorted(factors.keys(), key=lambda x: factors[x]['mean_r'], reverse=True):
                stats = factors[factor]
                self._log(f"  {factor:20} r = {stats['mean_r']:.3f} (SD={stats['sd_r']:.3f}, n={stats['n_pairs']})")
    
    # =========================================================================
    # H5: Provider Bias
    # =========================================================================
    
    def h5_provider_bias(self) -> Dict:
        """Analyze baseline personality tendencies by provider."""
        results = self.get_results()
        
        provider_scores = defaultdict(lambda: defaultdict(list))
        
        for r in results:
            provider_scores[r['provider']][r['instrument']].append(r['total_score'])
        
        bias = {}
        for provider in sorted(provider_scores.keys()):
            bias[provider] = {}
            for instrument in sorted(provider_scores[provider].keys()):
                scores = provider_scores[provider][instrument]
                bias[provider][instrument] = {
                    'mean': calc_mean(scores),
                    'sd': calc_sd(scores),
                    'n': len(scores)
                }
        
        return bias
    
    def print_h5(self):
        """Print H5 provider bias analysis."""
        self._log()
        self._log("=" * 70)
        self._log("H5: PROVIDER BIAS (Baseline Personality Fingerprints)")
        self._log("=" * 70)
        
        bias = self.h5_provider_bias()
        
        instruments = set()
        for provider_data in bias.values():
            instruments.update(provider_data.keys())
        instruments = sorted(instruments)
        
        header = f"{'Provider':<12}" + "".join(f"{inst:>12}" for inst in instruments)
        self._log(f"\n{header}")
        self._log("-" * len(header))
        
        for provider in sorted(bias.keys()):
            row = f"{provider:<12}"
            for inst in instruments:
                if inst in bias[provider]:
                    row += f"{bias[provider][inst]['mean']:>12.1f}"
                else:
                    row += f"{'--':>12}"
            self._log(row)
        
        self._log("-" * len(header))
        row = f"{'MEAN':<12}"
        for inst in instruments:
            all_means = [bias[p][inst]['mean'] for p in bias if inst in bias[p]]
            row += f"{calc_mean(all_means):>12.1f}"
        self._log(row)
    
    # =========================================================================
    # H6: Variance Decomposition
    # =========================================================================
    
    def h6_variance_decomposition(self) -> Dict:
        """Decompose variance by factor."""
        results = self.get_results()
        
        all_scores = [r['total_score'] for r in results]
        total_var = calc_variance(all_scores)
        grand_mean = calc_mean(all_scores)
        
        def variance_explained_by(factor_key):
            groups = defaultdict(list)
            for r in results:
                groups[r[factor_key]].append(r['total_score'])
            
            group_means = {k: calc_mean(v) for k, v in groups.items()}
            ssb = sum(len(v) * (group_means[k] - grand_mean) ** 2 
                     for k, v in groups.items())
            
            sst = sum((s - grand_mean) ** 2 for s in all_scores)
            
            return ssb / sst if sst > 0 else 0
        
        decomposition = {
            'total_variance': total_var,
            'grand_mean': grand_mean,
            'n': len(all_scores),
            'proportion_explained': {
                'instrument': variance_explained_by('instrument'),
                'provider': variance_explained_by('provider'),
                'input_system': variance_explained_by('input_system'),
                'profile': variance_explained_by('profile_label'),
            }
        }
        
        explained = sum(decomposition['proportion_explained'].values())
        decomposition['proportion_explained']['residual'] = max(0, 1 - explained)
        
        return decomposition
    
    def print_h6(self):
        """Print H6 variance decomposition."""
        self._log()
        self._log("=" * 70)
        self._log("H6: VARIANCE DECOMPOSITION")
        self._log("=" * 70)
        
        decomp = self.h6_variance_decomposition()
        
        self._log(f"\nTotal variance: {decomp['total_variance']:.2f}")
        self._log(f"Grand mean: {decomp['grand_mean']:.2f}")
        self._log(f"N: {decomp['n']}")
        
        self._log("\nProportion of variance explained by:")
        self._log("-" * 40)
        
        props = decomp['proportion_explained']
        for factor in sorted(props.keys(), key=lambda x: props[x], reverse=True):
            pct = props[factor] * 100
            bar = "█" * int(pct / 2)
            self._log(f"  {factor:<15} {pct:>6.1f}%  {bar}")
    
    # =========================================================================
    # H7: Attractor Detection
    # =========================================================================
    
    def h7_attractor_detection(self) -> Dict:
        """Analyze score distributions for evidence of discrete attractors."""
        results = self.get_results()
        
        by_instrument = defaultdict(list)
        for r in results:
            by_instrument[r['instrument']].append(r['total_score'])
        
        analysis = {}
        
        for instrument, scores in by_instrument.items():
            mean = calc_mean(scores)
            sd = calc_sd(scores)
            
            bin_width = 5
            bins = defaultdict(int)
            for s in scores:
                bin_idx = int(s / bin_width) * bin_width
                bins[bin_idx] += 1
            
            sorted_bins = sorted(bins.keys())
            peaks = []
            for i, b in enumerate(sorted_bins):
                count = bins[b]
                prev_count = bins[sorted_bins[i-1]] if i > 0 else 0
                next_count = bins[sorted_bins[i+1]] if i < len(sorted_bins)-1 else 0
                
                if count > prev_count and count >= next_count and count > len(scores) * 0.05:
                    peaks.append({'bin': b, 'count': count, 'pct': count/len(scores)*100})
            
            coefficient_of_variation = sd / mean if mean > 0 else 0
            
            analysis[instrument] = {
                'n': len(scores),
                'mean': mean,
                'sd': sd,
                'cv': coefficient_of_variation,
                'min': min(scores),
                'max': max(scores),
                'range': max(scores) - min(scores),
                'peaks': peaks,
                'n_peaks': len(peaks),
                'distribution': dict(bins),
            }
        
        return analysis
    
    def print_h7(self):
        """Print H7 attractor detection analysis."""
        self._log()
        self._log("=" * 70)
        self._log("H7: ATTRACTOR DETECTION (Score Distribution Analysis)")
        self._log("=" * 70)
        
        analysis = self.h7_attractor_detection()
        
        for instrument in sorted(analysis.keys()):
            data = analysis[instrument]
            self._log(f"\n{instrument.upper()}")
            self._log("-" * 50)
            self._log(f"  N: {data['n']}, Mean: {data['mean']:.1f}, SD: {data['sd']:.1f}")
            self._log(f"  Range: {data['min']:.1f} - {data['max']:.1f} ({data['range']:.1f} points)")
            self._log(f"  CV: {data['cv']:.3f}")
            
            if data['peaks']:
                self._log(f"  Peaks detected: {data['n_peaks']}")
                for peak in sorted(data['peaks'], key=lambda x: x['count'], reverse=True)[:5]:
                    self._log(f"    Score ~{peak['bin']}: {peak['count']} ({peak['pct']:.1f}%)")
            
            self._log(f"\n  Distribution (5-point bins):")
            max_count = max(data['distribution'].values()) if data['distribution'] else 1
            for bin_start in sorted(data['distribution'].keys()):
                count = data['distribution'][bin_start]
                bar_len = int(count / max_count * 30)
                self._log(f"    {bin_start:>3}-{bin_start+5:<3}: {'█' * bar_len} {count}")
    
    # =========================================================================
    # PHQ9 Deep Dive
    # =========================================================================
    
    def phq9_deep_dive(self) -> Dict:
        """Detailed analysis of PHQ9 as the reliability outlier."""
        results = self.get_results()
        
        phq9_results = [r for r in results if r['instrument'] == 'phq9']
        
        if not phq9_results:
            return {'error': 'No PHQ9 data found'}
        
        grouped = defaultdict(lambda: defaultdict(dict))
        for r in phq9_results:
            key = (r['input_system'], r['profile_label'])
            grouped[r['input_system']][r['profile_label']][r['provider']] = r['total_score']
        
        providers = sorted(set(r['provider'] for r in phq9_results))
        
        by_input_system = {}
        for inp_sys in grouped:
            provider_scores = {p: [] for p in providers}
            
            for profile, scores in grouped[inp_sys].items():
                if all(p in scores for p in providers):
                    for p in providers:
                        provider_scores[p].append(scores[p])
            
            correlations = {}
            for i, p1 in enumerate(providers):
                for p2 in providers[i+1:]:
                    if len(provider_scores[p1]) >= 3:
                        r, _ = pearson_correlation(provider_scores[p1], provider_scores[p2])
                        correlations[f"{p1}×{p2}"] = r
            
            by_input_system[inp_sys] = {
                'correlations': correlations,
                'mean_r': calc_mean(list(correlations.values())) if correlations else 0
            }
        
        all_grouped = defaultdict(dict)
        for r in phq9_results:
            key = (r['input_system'], r['profile_label'])
            all_grouped[key][r['provider']] = r['total_score']
        
        by_provider_pair = {}
        for i, p1 in enumerate(providers):
            for p2 in providers[i+1:]:
                pair = f"{p1}×{p2}"
                scores1 = []
                scores2 = []
                for key, scores in all_grouped.items():
                    if p1 in scores and p2 in scores:
                        scores1.append(scores[p1])
                        scores2.append(scores[p2])
                
                if len(scores1) >= 3:
                    r, _ = pearson_correlation(scores1, scores2)
                    by_provider_pair[pair] = r
        
        by_provider = defaultdict(list)
        for r in phq9_results:
            by_provider[r['provider']].append(r['total_score'])
        
        provider_stats = {}
        for provider, scores in by_provider.items():
            provider_stats[provider] = {
                'mean': calc_mean(scores),
                'sd': calc_sd(scores),
                'min': min(scores),
                'max': max(scores),
                'n': len(scores)
            }
        
        return {
            'n_total': len(phq9_results),
            'by_input_system': by_input_system,
            'by_provider_pair': by_provider_pair,
            'provider_stats': provider_stats,
        }
    
    def print_phq9_deep_dive(self):
        """Print PHQ9 deep dive analysis."""
        self._log()
        self._log("=" * 70)
        self._log("PHQ9 DEEP DIVE: Why r=0.82?")
        self._log("=" * 70)
        
        data = self.phq9_deep_dive()
        
        if 'error' in data:
            self._log(f"\n{data['error']}")
            return
        
        self._log(f"\nTotal PHQ9 test cases: {data['n_total']}")
        
        self._log("\nCorrelations by Provider Pair:")
        self._log("-" * 40)
        for pair in sorted(data['by_provider_pair'].keys(), 
                          key=lambda x: data['by_provider_pair'][x], reverse=True):
            r = data['by_provider_pair'][pair]
            indicator = "✓" if r > 0.85 else "○" if r > 0.75 else "✗"
            self._log(f"  {pair:<20} r = {r:.3f} {indicator}")
        
        self._log("\nMean Correlation by Input System:")
        self._log("-" * 40)
        for inp_sys in sorted(data['by_input_system'].keys(),
                             key=lambda x: data['by_input_system'][x]['mean_r'], reverse=True):
            mean_r = data['by_input_system'][inp_sys]['mean_r']
            indicator = "✓" if mean_r > 0.85 else "○" if mean_r > 0.75 else "✗"
            self._log(f"  {inp_sys:<15} r = {mean_r:.3f} {indicator}")
        
        self._log("\nPHQ9 Score Distribution by Provider:")
        self._log("-" * 40)
        for provider in sorted(data['provider_stats'].keys()):
            stats = data['provider_stats'][provider]
            self._log(f"  {provider:<12} Mean={stats['mean']:>5.1f}  SD={stats['sd']:>5.1f}  "
                  f"Range={stats['min']:.0f}-{stats['max']:.0f}")
    
    # =========================================================================
    # Run All
    # =========================================================================
    
    def run_full_analysis(self):
        """Run all expanded analyses."""
        self._log()
        self._log("=" * 70)
        self._log("BLADERUNNER EXPANDED ANALYSIS")
        self._log(f"Experiment: {self.experiment_number}")
        self._log(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("=" * 70)
        
        self.print_h4()
        self.print_h5()
        self.print_h6()
        self.print_h7()
        self.print_phq9_deep_dive()
        
        self._log()
        self._log("=" * 70)
        self._log("ANALYSIS COMPLETE")
        self._log("=" * 70)
        
        # Write to file
        output_dir = Path(f"experiment_{self.experiment_number}_output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "expanded_analysis.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._output_lines))
        
        print(f"\n📁 Written to: {output_file}")


def analyze_expanded(experiment_number: int):
    """Run expanded analysis."""
    analyzer = ExpandedAnalyzer(experiment_number)
    analyzer.run_full_analysis()


def main():
    parser = argparse.ArgumentParser(description='Bladerunner Expanded Analytics')
    parser.add_argument('--exp', type=int, required=True, 
                        help='Experiment number (not row id)')
    args = parser.parse_args()
    
    analyze_expanded(args.exp)


if __name__ == "__main__":
    main()