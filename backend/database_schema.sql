-- ============================================================
-- 0. ORGANIZATIONS & USERS (Auth Layer)
-- ============================================================

CREATE TABLE IF NOT EXISTS organizations (
    org_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    tier VARCHAR(50) NOT NULL DEFAULT 'FREE',
    node_limit INTEGER NOT NULL DEFAULT 10,
    contact_email VARCHAR(255),
    next_payment_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    org_id INTEGER REFERENCES organizations(org_id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================================
-- 1. SYSTEMS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS systems (
    system_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    org_id INTEGER REFERENCES organizations(org_id) ON DELETE SET NULL,
    system_name VARCHAR(255) NOT NULL UNIQUE,
    system_uuid UUID,
    comp_id VARCHAR(255),
    hostname VARCHAR(255) NOT NULL,
    ip_address INET,
    os VARCHAR(100),
    os_version VARCHAR(50),
    cpu_model VARCHAR(255),
    ram_gb DECIMAL(10,2),
    gpu_model VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_systems_hostname 
    ON systems(hostname);

CREATE INDEX IF NOT EXISTS idx_systems_active_last_seen 
    ON systems(is_active, last_seen);


-- ============================================================
-- 2. SYSTEM METRICS TABLE (PARTITIONED MONTHLY)
-- ============================================================

CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id BIGSERIAL,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cpu_usage DECIMAL(5,2) CHECK (cpu_usage BETWEEN 0 AND 100),
    ram_usage DECIMAL(5,2) CHECK (ram_usage BETWEEN 0 AND 100),
    gpu_usage DECIMAL(5,2) CHECK (gpu_usage BETWEEN 0 AND 100),
    temperature DECIMAL(5,2),
    network_rx_mb DECIMAL(12,2),
    network_tx_mb DECIMAL(12,2),
    PRIMARY KEY (metric_id, timestamp)
) PARTITION BY RANGE (timestamp);


-- ============================================================
-- 2A. Partition Auto-Creation Function
-- ============================================================

CREATE OR REPLACE FUNCTION create_system_metrics_partition(target_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + INTERVAL '1 month';
    partition_name :=
        'system_metrics_y' || EXTRACT(YEAR FROM start_date) ||
        'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    EXECUTE FORMAT(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF system_metrics
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;


-- Create current month partition
SELECT create_system_metrics_partition(CURRENT_DATE::DATE);

-- Create next month partition (prevent downtime)
SELECT create_system_metrics_partition((CURRENT_DATE + INTERVAL '1 month')::DATE);


-- Indexes for partitions
CREATE INDEX IF NOT EXISTS idx_system_metrics_system_timestamp
    ON system_metrics(system_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp
    ON system_metrics(timestamp);


-- ============================================================
-- 3. AGGREGATED METRICS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS aggregated_metrics (
    agg_id BIGSERIAL PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(10) CHECK (period_type IN ('hourly','daily')),
    avg_cpu_usage DECIMAL(5,2),
    avg_ram_usage DECIMAL(5,2),
    avg_gpu_usage DECIMAL(5,2),
    avg_temperature DECIMAL(5,2),
    total_network_rx_mb DECIMAL(12,2),
    total_network_tx_mb DECIMAL(12,2),
    data_points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_aggregated_metrics_unique
    ON aggregated_metrics(system_id, period_start, period_type);

CREATE INDEX IF NOT EXISTS idx_aggregated_metrics_system_period
    ON aggregated_metrics(system_id, period_type, period_start DESC);


-- ============================================================
-- 4. DAILY + HOURLY AGGREGATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION aggregate_daily_metrics(
    target_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day'
)
RETURNS VOID AS $$
BEGIN

    -- Hourly aggregation
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT
        system_id,
        DATE_TRUNC('hour', timestamp),
        DATE_TRUNC('hour', timestamp) + INTERVAL '1 hour',
        'hourly',
        AVG(cpu_usage),
        AVG(ram_usage),
        AVG(gpu_usage),
        AVG(temperature),
        SUM(network_rx_mb),
        SUM(network_tx_mb),
        COUNT(*)
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('hour', timestamp)
    ON CONFLICT (system_id, period_start, period_type)
    DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;


    -- Daily aggregation
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT
        system_id,
        DATE_TRUNC('day', timestamp),
        DATE_TRUNC('day', timestamp) + INTERVAL '1 day',
        'daily',
        AVG(cpu_usage),
        AVG(ram_usage),
        AVG(gpu_usage),
        AVG(temperature),
        SUM(network_rx_mb),
        SUM(network_tx_mb),
        COUNT(*)
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('day', timestamp)
    ON CONFLICT (system_id, period_start, period_type)
    DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;

END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- 5. PARTITION CLEANUP (RETENTION POLICY)
-- ============================================================

CREATE OR REPLACE FUNCTION cleanup_old_partitions()
RETURNS VOID AS $$
DECLARE
    rec RECORD;
    cutoff DATE := CURRENT_DATE - INTERVAL '30 days';
BEGIN
    FOR rec IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'system_metrics_y%m__'
    LOOP
        EXECUTE FORMAT(
            'DROP TABLE IF EXISTS %I',
            rec.tablename
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;
