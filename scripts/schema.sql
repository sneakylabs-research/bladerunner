-- ============================================
-- BLADERUNNER DATABASE SCHEMA
-- Research system - questions live in Python
-- ============================================

-- ============================================
-- REFERENCE DATA (thin - Python is source of truth)
-- ============================================

CREATE TABLE input_systems (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    name            NVARCHAR(50) NOT NULL UNIQUE,     -- 'ocean_direct', 'narrative'
    created_at      DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE providers (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    name            NVARCHAR(50) NOT NULL UNIQUE,     -- 'claude', 'openai', 'deepseek', 'gemini'
    model_name      NVARCHAR(100),
    rate_limit_per_second DECIMAL(5,2) DEFAULT 1.0,
    created_at      DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE instruments (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    short_name      NVARCHAR(20) NOT NULL UNIQUE,     -- 'levenson', 'bfi' - matches Python class
    name            NVARCHAR(100),
    question_count  INT,
    created_at      DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE profile_sets (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    name            NVARCHAR(100) NOT NULL UNIQUE,
    description     NVARCHAR(500),
    created_at      DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE personality_profiles (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    profile_set_id  INT NOT NULL REFERENCES profile_sets(id),
    profile_index   INT NOT NULL,
    openness        INT NOT NULL,
    conscientiousness INT NOT NULL,
    extraversion    INT NOT NULL,
    agreeableness   INT NOT NULL,
    neuroticism     INT NOT NULL,
    label           NVARCHAR(100),
    
    CONSTRAINT UQ_profile UNIQUE(profile_set_id, profile_index)
);


-- ============================================
-- EXPERIMENT DATA
-- ============================================

CREATE TABLE experiments (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    name            NVARCHAR(200) NOT NULL,
    description     NVARCHAR(MAX),
    profile_set_id  INT NOT NULL REFERENCES profile_sets(id),
    status          NVARCHAR(20) DEFAULT 'pending',
    created_at      DATETIME2 DEFAULT GETUTCDATE(),
    started_at      DATETIME2,
    completed_at    DATETIME2
);

-- What's in this experiment (many-to-many)
CREATE TABLE experiment_config (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    experiment_id   INT NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    input_system_id INT NOT NULL REFERENCES input_systems(id),
    instrument_id   INT NOT NULL REFERENCES instruments(id),
    provider_id     INT NOT NULL REFERENCES providers(id),
    
    CONSTRAINT UQ_config UNIQUE(experiment_id, input_system_id, instrument_id, provider_id)
);

CREATE TABLE test_cases (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    experiment_id   INT NOT NULL REFERENCES experiments(id),
    
    -- Denormalized for query simplicity (no joins needed for basic analysis)
    input_system    NVARCHAR(50) NOT NULL,
    instrument      NVARCHAR(20) NOT NULL,
    provider        NVARCHAR(50) NOT NULL,
    
    -- Profile (denormalized - this is what we're testing)
    profile_id      INT NOT NULL REFERENCES personality_profiles(id),
    O               INT NOT NULL,
    C               INT NOT NULL,
    E               INT NOT NULL,
    A               INT NOT NULL,
    N               INT NOT NULL,
    profile_label   NVARCHAR(100),
    
    -- Job queue
    status          NVARCHAR(20) DEFAULT 'pending',   -- pending/locked/running/complete/failed/retry
    attempts        INT DEFAULT 0,
    worker_id       NVARCHAR(100),
    
    -- Timestamps
    created_at      DATETIME2 DEFAULT GETUTCDATE(),
    locked_at       DATETIME2,
    started_at      DATETIME2,
    completed_at    DATETIME2,
    
    -- Debug
    prompt_sent     NVARCHAR(MAX),                    -- actual personality preamble
    error_message   NVARCHAR(MAX)
);

CREATE TABLE responses (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    test_case_id    INT NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    
    -- Question data (denormalized from Python for analysis)
    question_number INT NOT NULL,
    question_text   NVARCHAR(500),
    factor          NVARCHAR(50),
    is_reversed     BIT,
    
    -- Response data
    raw_response    NVARCHAR(MAX),                    -- what LLM actually returned
    parsed_score    INT,                              -- 1-5
    score_after_reverse INT,                          -- after applying reverse scoring
    
    -- Performance
    response_time_ms INT,
    
    created_at      DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT UQ_response UNIQUE(test_case_id, question_number)
);

CREATE TABLE results (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    test_case_id    INT NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    
    -- Scores
    total_score     DECIMAL(6,2),
    factor_scores   NVARCHAR(MAX),                    -- JSON: {"primary": 72.5, "secondary": 45.0}
    
    -- Completion
    questions_answered INT,
    questions_total INT,
    duration_ms     INT,
    
    created_at      DATETIME2 DEFAULT GETUTCDATE(),
    
    CONSTRAINT UQ_result UNIQUE(test_case_id)
);


-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IX_test_cases_queue ON test_cases(status, provider);
CREATE INDEX IX_test_cases_experiment ON test_cases(experiment_id, status);
CREATE INDEX IX_responses_test_case ON responses(test_case_id);


-- ============================================
-- SEED DATA
-- ============================================

INSERT INTO input_systems (name) VALUES ('ocean_direct'), ('narrative');

INSERT INTO providers (name, model_name, rate_limit_per_second) VALUES
('claude', 'claude-3-5-sonnet-20241022', 1.0),
('openai', 'gpt-4', 3.0),
('deepseek', 'deepseek-chat', 5.0),
('gemini', 'gemini-2.0-flash', 0.5);

INSERT INTO instruments (short_name, name, question_count) VALUES
('levenson', 'Levenson Self-Report Psychopathy Scale', 26),
('bfi', 'Big Five Inventory (BFI-44)', 44);

INSERT INTO profile_sets (name, description) VALUES
('19_strategic', 'Strategic profiles for psychopathy variance');

INSERT INTO personality_profiles (profile_set_id, profile_index, openness, conscientiousness, extraversion, agreeableness, neuroticism, label) VALUES
-- High psychopathy expected (Low A, Low C)
(1, 1, 50, 0, 0, 0, 50, 'low_A_low_C_low_E'),
(1, 2, 50, 0, 100, 0, 50, 'low_A_low_C_high_E'),
(1, 3, 50, 25, 0, 0, 50, 'low_A_medlow_C_low_E'),
(1, 4, 50, 25, 100, 0, 50, 'low_A_medlow_C_high_E'),
(1, 5, 50, 0, 0, 25, 50, 'medlow_A_low_C_low_E'),
(1, 6, 50, 0, 100, 25, 50, 'medlow_A_low_C_high_E'),
(1, 7, 50, 25, 0, 25, 50, 'medlow_A_medlow_C_low_E'),
(1, 8, 50, 25, 100, 25, 50, 'medlow_A_medlow_C_high_E'),
-- Low psychopathy expected (High A, High C)
(1, 9, 50, 75, 0, 75, 50, 'high_A_high_C_low_E'),
(1, 10, 50, 75, 100, 75, 50, 'high_A_high_C_high_E'),
(1, 11, 50, 100, 0, 75, 50, 'high_A_max_C_low_E'),
(1, 12, 50, 100, 100, 75, 50, 'high_A_max_C_high_E'),
(1, 13, 50, 75, 0, 100, 50, 'max_A_high_C_low_E'),
(1, 14, 50, 75, 100, 100, 50, 'max_A_high_C_high_E'),
(1, 15, 50, 100, 0, 100, 50, 'max_A_max_C_low_E'),
(1, 16, 50, 100, 100, 100, 50, 'max_A_max_C_high_E'),
-- Controls
(1, 17, 50, 50, 50, 50, 50, 'neutral'),
(1, 18, 0, 0, 0, 0, 0, 'all_minimum'),
(1, 19, 100, 100, 100, 100, 100, 'all_maximum');

GO
