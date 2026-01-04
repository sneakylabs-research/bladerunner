# -*- coding: utf-8 -*-
"""
Item-level reliability analysis for Bladerunner
"""

import pyodbc
import pandas as pd
import numpy as np
from itertools import combinations

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=BladerunnerDev;'
    'Trusted_Connection=yes;'
)

query = """
SELECT 
    r.question_number,
    r.question_text,
    r.factor,
    r.parsed_score,
    tc.provider,
    tc.instrument,
    tc.profile_label,
    tc.input_system
FROM responses r
JOIN test_cases tc ON r.test_case_id = tc.id
WHERE tc.experiment_id = 6
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"Loaded {len(df)} responses")

results = []

for (instrument, qnum), item_df in df.groupby(['instrument', 'question_number']):
    
    pivot = item_df.pivot_table(
        index=['profile_label', 'input_system'],
        columns='provider',
        values='parsed_score',
        aggfunc='first'
    ).dropna()
    
    if len(pivot) < 5:
        continue
    
    providers = [c for c in ['claude', 'deepseek', 'gemini', 'openai'] if c in pivot.columns]
    
    if len(providers) < 2:
        continue
        
    corrs = []
    for p1, p2 in combinations(providers, 2):
        if pivot[p1].std() > 0 and pivot[p2].std() > 0:
            r = pivot[p1].corr(pivot[p2])
            if not np.isnan(r):
                corrs.append(r)
    
    if corrs:
        question_text = item_df['question_text'].iloc[0][:80]
        factor = item_df['factor'].iloc[0]
        
        results.append({
            'instrument': instrument,
            'question_number': qnum,
            'factor': factor,
            'question_text': question_text,
            'mean_r': np.mean(corrs),
            'sd_r': np.std(corrs),
            'n_pairs': len(corrs),
            'n_observations': len(pivot)
        })

out_df = pd.DataFrame(results)
out_df = out_df.sort_values(['instrument', 'question_number'])
out_df.to_csv('item_reliability.csv', index=False)

print(f"Saved {len(out_df)} items to item_reliability.csv")
print(f"\nBy instrument:")
print(out_df.groupby('instrument')['mean_r'].agg(['mean', 'std', 'count']))