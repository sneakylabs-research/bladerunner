"""
Experiment 7: O/N Disentanglement

Supplementary profiles to separate Openness and Neuroticism effects.
The original 19 strategic profiles had O and N perfectly correlated.

9 profiles × 4 providers × 5 instruments × 6 input systems = 1,080 test cases
"""

from bladerunner_runner.db import get_db

def create_experiment_7():
    """Create Experiment 7 with O/N disentanglement profiles."""
    
    db = get_db()
    
    # Define the 9 O/N disentanglement profiles
    # Hold C, E, A at 50 to isolate O/N effects
    profiles = [
        # Label, O, C, E, A, N
        ("high_O_low_N", 100, 50, 50, 50, 0),      # O without N
        ("low_O_high_N", 0, 50, 50, 50, 100),      # N without O
        ("high_O_high_N", 100, 50, 50, 50, 100),   # Both high
        ("low_O_low_N", 0, 50, 50, 50, 0),         # Both low
        ("mid_O_high_N", 50, 50, 50, 50, 100),     # N gradient high
        ("mid_O_low_N", 50, 50, 50, 50, 0),        # N gradient low
        ("high_O_mid_N", 100, 50, 50, 50, 50),     # O gradient high
        ("low_O_mid_N", 0, 50, 50, 50, 50),        # O gradient low
        ("mid_O_mid_N", 50, 50, 50, 50, 50),       # Baseline neutral
    ]
    
    providers = ["claude", "openai", "deepseek", "gemini"]
    instruments = ["levenson", "bfi", "dark_triad", "phq9", "gad7"]
    input_systems = ["ocean_direct", "narrative", "hexaco", "behavioral", "scenario", "exemplar"]
    
    # Get profile set (already exists from earlier runs)
    profile_set = db.query("""
        SELECT id FROM profile_sets WHERE name = ?
    """, ("O/N Disentanglement",))
    
    if not profile_set:
        raise Exception("Profile set 'O/N Disentanglement' not found")
    
    profile_set_id = profile_set[0]['id']
    print(f"Using Profile Set {profile_set_id}")
    
    # Get profile IDs (already created from earlier runs)
    profile_rows = db.query("""
        SELECT id, label FROM personality_profiles 
        WHERE profile_set_id = ?
    """, (profile_set_id,))
    
    profile_ids = {r['label']: r['id'] for r in profile_rows}
    print(f"Found {len(profile_ids)} profiles")
    
    for label, pid in profile_ids.items():
        print(f"  {label}: ID {pid}")
    
    # Create experiment
    db.execute("""
        INSERT INTO experiments (name, description, status, profile_set_id)
        VALUES (?, ?, 'created', ?)
    """, ("Experiment 7: O/N Disentanglement", 
          "9 profiles isolating Openness and Neuroticism effects. "
          "Supplementary to Experiment 6 to resolve O/N confound.",
          profile_set_id))
    
    # Query for the experiment ID we just created
    exp_row = db.query("""
        SELECT MAX(id) as id FROM experiments 
        WHERE name = ? AND profile_set_id = ?
    """, ("Experiment 7: O/N Disentanglement", profile_set_id))
    
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
    
    print(f"Created {test_case_count} test cases")
    
    # Update experiment status
    db.execute("""
        UPDATE experiments 
        SET status = 'ready',
            test_cases_total = ?
        WHERE id = ?
    """, (test_case_count, experiment_id))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"EXPERIMENT 7: O/N DISENTANGLEMENT")
    print(f"{'='*60}")
    print(f"Profiles: {len(profiles)}")
    print(f"Providers: {len(providers)}")
    print(f"Instruments: {len(instruments)}")
    print(f"Input Systems: {len(input_systems)}")
    print(f"Total Test Cases: {test_case_count}")
    print(f"Estimated Completions: ~{test_case_count * 22:,}")
    print(f"{'='*60}")
    
    print("\nProfiles:")
    for label, O, C, E, A, N in profiles:
        print(f"  {label:<20} O={O:>3} C={C:>3} E={E:>3} A={A:>3} N={N:>3}")
    
    print(f"\nRun with: python -m bladerunner_runner.runner {experiment_id}")
    
    return experiment_id


if __name__ == "__main__":
    create_experiment_7()