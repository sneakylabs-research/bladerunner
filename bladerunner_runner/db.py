"""
Database layer for Bladerunner.
Thin wrapper around pyodbc. Raw SQL, no ORM.
"""

import os
import json
import pyodbc
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class Database:
    """SQL Server connection and query execution."""
    
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self._connection: Optional[pyodbc.Connection] = None
    
    def _build_connection_string(self) -> str:
        server = os.getenv('DB_SERVER', 'localhost')
        database = os.getenv('DB_NAME', 'BladerunnerDev')
        trusted = os.getenv('DB_TRUSTED_CONNECTION', 'yes').lower() == 'yes'
        
        if trusted:
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
            )
    
    def connect(self) -> pyodbc.Connection:
        """Get or create connection."""
        if self._connection is None:
            self._connection = pyodbc.connect(self.connection_string)
        return self._connection
    
    def close(self):
        """Close connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute SQL, return rows affected."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """Execute SQL with multiple parameter sets."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        return cursor.rowcount
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute query, return list of dicts."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query, return single row or None."""
        results = self.query(sql, params)
        return results[0] if results else None
    
    def query_scalar(self, sql: str, params: tuple = ()) -> Any:
        """Execute query, return single value."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return row[0] if row else None
    
    def insert_returning_id(self, sql: str, params: tuple = ()) -> int:
        """Insert and return the generated ID."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql + "; SELECT @@IDENTITY", params)
        cursor.nextset()
        new_id = cursor.fetchone()[0]
        conn.commit()
        return int(new_id)

# Singleton instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get the database singleton."""
    global _db
    if _db is None:
        _db = Database()
    return _db


# === EXPERIMENT OPERATIONS ===

def create_experiment(name: str, description: str, profile_set: str,
                      input_systems: List[str], instruments: List[str], 
                      providers: List[str], is_longitudinal: bool = False) -> int:
    """Create experiment and generate all test cases. Returns experiment_id."""
    
    if not description:
        raise ValueError("Description is required")
    
    db = get_db()
    
    # Get profile_set_id
    profile_set_id = db.query_scalar(
        "SELECT id FROM profile_sets WHERE name = ?", (profile_set,)
    )
    if not profile_set_id:
        raise ValueError(f"Unknown profile set: {profile_set}")
    
    # Get next experiment_number
    max_num = db.query_scalar("SELECT MAX(experiment_number) FROM experiments")
    experiment_number = (max_num or 0) + 1
    
    # Create experiment
    experiment_id = db.insert_returning_id(
        """INSERT INTO experiments (name, description, profile_set_id, status, experiment_number, is_longitudinal)
           VALUES (?, ?, ?, 'pending', ?, ?)""",
        (name, description, profile_set_id, experiment_number, 1 if is_longitudinal else 0)
    )
    
    # Get reference IDs
    input_system_ids = {
        row['name']: row['id'] 
        for row in db.query("SELECT id, name FROM input_systems WHERE name IN ({})".format(
            ','.join('?' * len(input_systems))), tuple(input_systems))
    }
    
    instrument_ids = {
        row['short_name']: row['id']
        for row in db.query("SELECT id, short_name FROM instruments WHERE short_name IN ({})".format(
            ','.join('?' * len(instruments))), tuple(instruments))
    }
    
    provider_ids = {
        row['name']: row['id']
        for row in db.query("SELECT id, name FROM providers WHERE name IN ({})".format(
            ','.join('?' * len(providers))), tuple(providers))
    }
    
    # Insert experiment config
    for inp in input_systems:
        for inst in instruments:
            for prov in providers:
                db.execute(
                    """INSERT INTO experiment_config 
                       (experiment_id, input_system_id, instrument_id, provider_id)
                       VALUES (?, ?, ?, ?)""",
                    (experiment_id, input_system_ids[inp], instrument_ids[inst], provider_ids[prov])
                )
    
    # Generate test cases (Cartesian product)
    profiles = db.query(
        """SELECT id, openness, conscientiousness, extraversion, 
                  agreeableness, neuroticism, label
           FROM personality_profiles WHERE profile_set_id = ?""",
        (profile_set_id,)
    )
    
    test_case_params = []
    for inp in input_systems:
        for inst in instruments:
            for prov in providers:
                for profile in profiles:
                    test_case_params.append((
                        experiment_id,
                        inp,
                        inst,
                        prov,
                        profile['id'],
                        profile['openness'],
                        profile['conscientiousness'],
                        profile['extraversion'],
                        profile['agreeableness'],
                        profile['neuroticism'],
                        profile['label']
                    ))
    
    db.execute_many(
        """INSERT INTO test_cases 
           (experiment_id, input_system, instrument, provider, profile_id,
            O, C, E, A, N, profile_label)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        test_case_params
    )
    
    return experiment_id


def start_experiment(experiment_id: int):
    """Mark experiment as running with start timestamp."""
    db = get_db()
    db.execute(
        """UPDATE experiments 
           SET status = 'running', started_at = GETUTCDATE()
           WHERE id = ? AND started_at IS NULL""",
        (experiment_id,)
    )


def complete_experiment(experiment_id: int):
    """Mark experiment as complete with end timestamp."""
    db = get_db()
    db.execute(
        """UPDATE experiments 
           SET status = 'complete', completed_at = GETUTCDATE()
           WHERE id = ?""",
        (experiment_id,)
    )


def claim_test_case(provider: str, worker_id: str) -> Optional[Dict[str, Any]]:
    """Claim next pending test case for a provider. Returns test case or None."""
    
    db = get_db()
    
    # Atomic claim with row locking
    # READPAST skips locked rows, UPDLOCK takes update lock
    result = db.query_one(
        """UPDATE TOP(1) test_cases WITH (ROWLOCK, READPAST)
           SET status = 'locked', 
               locked_at = GETUTCDATE(), 
               worker_id = ?
           OUTPUT INSERTED.*
           WHERE status IN ('pending', 'retry') 
             AND provider = ?""",
        (worker_id, provider)
    )
    
    return result


def start_test_case(test_case_id: int, prompt_sent: str):
    """Mark test case as running, record the prompt."""
    db = get_db()
    db.execute(
        """UPDATE test_cases 
           SET status = 'running', 
               started_at = GETUTCDATE(), 
               attempts = attempts + 1,
               prompt_sent = ?
           WHERE id = ?""",
        (prompt_sent, test_case_id)
    )


def save_response(test_case_id: int, question_number: int, question_text: str,
                  factor: str, is_reversed: bool, raw_response: str,
                  parsed_score: int, score_after_reverse: int, response_time_ms: int,
                  sequence_position: int = None, context_tokens: int = None):
    """Save a single question response."""
    db = get_db()
    db.execute(
        """INSERT INTO responses 
           (test_case_id, question_number, question_text, factor, is_reversed,
            raw_response, parsed_score, score_after_reverse, response_time_ms,
            sequence_position, context_tokens)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (test_case_id, question_number, question_text, factor, is_reversed,
         raw_response, parsed_score, score_after_reverse, response_time_ms,
         sequence_position, context_tokens)
    )


def complete_test_case(test_case_id: int, total_score: float, 
                       factor_scores: Dict[str, float],
                       questions_answered: int, questions_total: int,
                       duration_ms: int):
    """Mark test case complete and save results."""
    db = get_db()
    
    with db.transaction():
        db.execute(
            """UPDATE test_cases 
               SET status = 'complete', completed_at = GETUTCDATE()
               WHERE id = ?""",
            (test_case_id,)
        )
        
        db.execute(
            """INSERT INTO results 
               (test_case_id, total_score, factor_scores, 
                questions_answered, questions_total, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (test_case_id, total_score, json.dumps(factor_scores),
             questions_answered, questions_total, duration_ms)
        )


def fail_test_case(test_case_id: int, error_message: str, retry: bool = True):
    """Mark test case as failed or retry."""
    db = get_db()
    
    if retry:
        attempts = db.query_scalar(
            "SELECT attempts FROM test_cases WHERE id = ?", (test_case_id,)
        )
        status = 'retry' if attempts < 3 else 'failed'
    else:
        status = 'failed'
    
    db.execute(
        """UPDATE test_cases 
           SET status = ?, error_message = ?, locked_at = NULL, worker_id = NULL
           WHERE id = ?""",
        (status, error_message, test_case_id)
    )


def get_experiment_status(experiment_id: int) -> Dict[str, Any]:
    """Get experiment progress."""
    db = get_db()
    return db.query_one(
        """SELECT 
               e.id, e.name, e.status, e.created_at, e.started_at, e.completed_at,
               e.experiment_number, e.is_longitudinal,
               COUNT(*) as total,
               SUM(CASE WHEN tc.status = 'complete' THEN 1 ELSE 0 END) as complete,
               SUM(CASE WHEN tc.status = 'failed' THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN tc.status IN ('pending', 'retry') THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN tc.status IN ('locked', 'running') THEN 1 ELSE 0 END) as running
           FROM experiments e
           LEFT JOIN test_cases tc ON tc.experiment_id = e.id
           WHERE e.id = ?
           GROUP BY e.id, e.name, e.status, e.created_at, e.started_at, e.completed_at,
                    e.experiment_number, e.is_longitudinal""",
        (experiment_id,)
    )


def get_pending_count(provider: str) -> int:
    """Get count of pending test cases for a provider."""
    db = get_db()
    return db.query_scalar(
        """SELECT COUNT(*) FROM test_cases 
           WHERE provider = ? AND status IN ('pending', 'retry')""",
        (provider,)
    )

def get_pending_test_cases_for_experiment(experiment_id: int) -> List[Dict[str, Any]]:
    """Get pending test cases for a specific experiment."""
    db = get_db()
    return db.query(
        """SELECT * FROM test_cases 
           WHERE experiment_id = ? AND status IN ('pending', 'retry')
           ORDER BY id""",
        (experiment_id,)
    )


def get_pending_test_cases(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get pending test cases across all experiments."""
    db = get_db()
    if limit:
        return db.query(
            f"""SELECT TOP({limit}) * FROM test_cases 
               WHERE status IN ('pending', 'retry')
               ORDER BY experiment_id, id"""
        )
    return db.query(
        """SELECT * FROM test_cases 
           WHERE status IN ('pending', 'retry')
           ORDER BY experiment_id, id"""
    )


def update_test_case_status(test_case_id: int, status: str, error_message: str = None):
    """Update test case status."""
    db = get_db()
    if error_message:
        db.execute(
            "UPDATE test_cases SET status = ?, error_message = ? WHERE id = ?",
            (status, error_message, test_case_id)
        )
    else:
        db.execute(
            "UPDATE test_cases SET status = ? WHERE id = ?",
            (status, test_case_id)
        )


def insert_response(response: Dict[str, Any]):
    """Insert a response record."""
    db = get_db()
    db.execute(
        """INSERT INTO responses 
           (test_case_id, question_number, question_text, factor, is_reversed,
            raw_response, parsed_score, response_time_ms, sequence_position, context_tokens)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (response['test_case_id'], response['question_number'], 
         response['question_text'], response['factor'], response['is_reversed'],
         response['raw_response'], response['parsed_score'], response.get('response_time_ms'),
         response.get('sequence_position'), response.get('context_tokens'))
    )


def insert_result(result: Dict[str, Any]):
    """Insert a result record."""
    db = get_db()
    db.execute(
        """INSERT INTO results 
           (test_case_id, total_score, factor_scores, questions_answered, questions_total)
           VALUES (?, ?, ?, ?, ?)""",
        (result['test_case_id'], result['total_score'], result['factor_scores'],
         result['questions_answered'], result['questions_total'])
    )