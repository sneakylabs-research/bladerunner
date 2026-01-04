"""
Experiment 9: PHQ Affect Isolation

PHQ-9 (control) vs PHQ-6-BC (behavioral/cognitive) vs PHQ-3-A (affective)
under longitudinal conditions.

9 profiles x 4 providers x 3 instruments x 6 input systems = 648 test cases
"""

from bladerunner_runner.db import get_db


def create_experiment_9():
    """Create Experiment 9: PHQ Affect Isolation."""
    
    db = get_db()
    
    profiles = [
        ("high_O_low_N", 100, 50, 50, 50, 0),
        ("low_O_high_N", 0, 50, 50, 50, 100),
        ("high_O_high_N", 100, 50, 50, 50, 100),
        ("low_O_low_N", 0, 50, 50, 50, 0),
        ("mid_O_high_N", 50, 50, 50, 50, 100),
        ("mid_O_low_N", 50, 50, 50, 50, 0),
        ("high_O_mid_N", 100, 50, 50, 50, 50),
        ("low_O_mid_N", 0, 50, 50, 50, 50),
        ("mid_O_mid_N", 50, 50, 50, 50, 50),
    ]
    
    providers = ["claude", "openai", "deepseek", "gemini"]
    instruments = ["phq9", "phq6_bc", "phq3_a"]
    input_systems = ["ocean_direct", "narrative", "hexaco", "behavioral", "scenario", "exemplar"]
    
    # Get profile set
    profile_set = db.query("""
        SELECT id FROM profile_sets WHERE name = ?
    """, ("O/N Disentanglement",))
    
    if not profile_set:
        raise Exception("Profile set 'O/N Disentanglement' not found")
    
    profile_set_id = profile_set[0]['id']
    print(f"Using Profile Set {profile_set_id}")
    
    # Get profile IDs
    profile_rows = db.query("""
        SELECT id, label FROM personality_profiles 
        WHERE profile_set_id = ?
    """, (profile_set_id,))
    
    profile_ids = {r['label']: r['id'] for r in profile_rows}
    print(f"Found {len(profile_ids)} profiles")
    
    # Create experiment - LONGITUDINAL
    db.execute("""
        INSERT INTO experiments (name, description, status, profile_set_id, is_longitudinal, experiment_number)
        VALUES (?, ?, 'created', ?, 1, 9)
    """, ("Experiment 9: PHQ Affect Isolation", 
          "PHQ-9 (control) vs PHQ-6-BC (behavioral/cognitive) vs PHQ-3-A (affective) "
          "under longitudinal conditions. Tests affect-instability hypothesis.",
          profile_set_id))
    
    exp_row = db.query("""
        SELECT MAX(id) as id FROM experiments
    """)
    
    experiment_id = exp_row[0]['id']
    print(f"Created Experiment {experiment_id}")
    
    # Create test cases
    test_case_count = 0
    
    for label, O, C, E, A, N in profiles:
        profile_id = profile_ids[label]
        
        for provider in providers:
            for instrument in instruments:
                for input_system in input_systems:
                    db.execute("""
                        INSERT INTO test_cases 
                        (experiment_id, provider, instrument, input_system, 
                         profile_id, O, C, E, A, N, profile_label, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (experiment_id, provider, instrument, input_system,
                          profile_id, O, C, E, A, N, label))
                    test_case_count += 1
    
    # Update status
    db.execute("""
        UPDATE experiments SET status = 'ready' WHERE id = ?
    """, (experiment_id,))
    
    print(f"\nCreated {test_case_count} test cases")
    print(f"Estimated completions: ~3,888")
    print(f"  - phq9: 1,944")
    print(f"  - phq6_bc: 1,296")
    print(f"  - phq3_a: 648")
    print(f"\nRun with: python -m bladerunner_runner.runner {experiment_id}")
    
    return experiment_id


if __name__ == "__main__":
    create_experiment_9()