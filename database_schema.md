# Sys_Logger Database Schema

This document outlines the database schema for the Sys_Logger project, designed to handle system monitoring data efficiently. The schema includes tables for system registration, time-series metrics, and aggregated data with appropriate partitioning, indexing, and retention strategies.

## Overview

The schema consists of three main tables:
- `systems`: Stores system registration and metadata
- `system_metrics`: Time-series data for raw metrics with monthly partitioning
- `aggregated_metrics`: Long-term aggregated averages

### Assumptions
- Database: PostgreSQL (recommended for partitioning support)
- Timezone: All timestamps stored in UTC
- Data types: Standard SQL types with appropriate constraints

## Tables

### systems

This table stores information about registered systems being monitored.

```sql
CREATE TABLE systems (
    system_id SERIAL PRIMARY KEY,
    system_name VARCHAR(255) NOT NULL UNIQUE,
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

-- Indexes
CREATE UNIQUE INDEX idx_systems_hostname ON systems(hostname);
CREATE INDEX idx_systems_active_last_seen ON systems(is_active, last_seen);
```

**Columns:**
- `system_id`: Auto-incrementing primary key
- `system_name`: User-defined name for the system
- `hostname`: System hostname
- `ip_address`: IP address (optional)
- `os`: Operating system name
- `os_version`: OS version
- `cpu_model`: CPU model information
- `ram_gb`: Installed RAM in GB
- `gpu_model`: GPU model information
- `created_at`: Registration timestamp
- `last_seen`: Last time system reported metrics
- `is_active`: Flag for active monitoring

### system_metrics

This table stores raw time-series metrics with monthly partitioning for efficient data management.

```sql
-- Base table (not directly used for inserts)
CREATE TABLE system_metrics (
    metric_id BIGSERIAL,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cpu_usage DECIMAL(5,2) CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
    ram_usage DECIMAL(5,2) CHECK (ram_usage >= 0 AND ram_usage <= 100),
    gpu_usage DECIMAL(5,2) CHECK (gpu_usage >= 0 AND gpu_usage <= 100),
    temperature DECIMAL(5,2), -- Celsius
    network_rx_mb DECIMAL(12,2), -- MB received
    network_tx_mb DECIMAL(12,2), -- MB transmitted
    PRIMARY KEY (metric_id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Monthly partitions (create as needed)
-- Example for current month
CREATE TABLE system_metrics_y2024m11 PARTITION OF system_metrics
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

-- Function to create monthly partitions automatically
CREATE OR REPLACE FUNCTION create_system_metrics_partition(target_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'system_metrics_y' || EXTRACT(YEAR FROM start_date) || 'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    EXECUTE FORMAT('CREATE TABLE IF NOT EXISTS %I PARTITION OF system_metrics FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;

-- Indexes (create on base table - inherited by partitions)
CREATE INDEX idx_system_metrics_system_timestamp ON system_metrics(system_id, timestamp);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
```

**Columns:**
- `metric_id`: Auto-incrementing ID (BIGSERIAL for high volume)
- `system_id`: Foreign key to systems table
- `timestamp`: Metric collection timestamp (UTC)
- `cpu_usage`: CPU utilization percentage
- `ram_usage`: RAM utilization percentage
- `gpu_usage`: GPU utilization percentage
- `temperature`: System temperature in Celsius
- `network_rx_mb`: Network bytes received (MB)
- `network_tx_mb`: Network bytes transmitted (MB)

### aggregated_metrics

This table stores daily and hourly aggregated averages for long-term analysis.

```sql
CREATE TABLE aggregated_metrics (
    agg_id BIGSERIAL PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES systems(system_id),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    period_type VARCHAR(10) CHECK (period_type IN ('hourly', 'daily')),
    avg_cpu_usage DECIMAL(5,2),
    avg_ram_usage DECIMAL(5,2),
    avg_gpu_usage DECIMAL(5,2),
    avg_temperature DECIMAL(5,2),
    total_network_rx_mb DECIMAL(12,2),
    total_network_tx_mb DECIMAL(12,2),
    data_points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_aggregated_metrics_unique ON aggregated_metrics(system_id, period_start, period_type);
CREATE INDEX idx_aggregated_metrics_system_period ON aggregated_metrics(system_id, period_type, period_start DESC);
```

**Columns:**
- `agg_id`: Auto-incrementing primary key
- `system_id`: Foreign key to systems table
- `period_start`: Start of aggregation period
- `period_end`: End of aggregation period
- `period_type`: 'hourly' or 'daily'
- `avg_cpu_usage`: Average CPU usage over period
- `avg_ram_usage`: Average RAM usage over period
- `avg_gpu_usage`: Average GPU usage over period
- `avg_temperature`: Average temperature over period
- `total_network_rx_mb`: Total network received over period
- `total_network_tx_mb`: Total network transmitted over period
- `data_points`: Number of raw data points aggregated
- `created_at`: When aggregation was performed

## Retention Strategy

- **Raw Metrics (system_metrics)**: Retain for 30 days
- **Aggregated Metrics**: Retain indefinitely (or based on business rules)

After 30 days, raw metrics are aggregated into the aggregated_metrics table and the corresponding partitions are dropped.

## Aggregation Jobs

Daily aggregation job runs at midnight UTC to process the previous day's data:

```sql
-- Daily aggregation function
CREATE OR REPLACE FUNCTION aggregate_daily_metrics(target_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day')
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'system_metrics_y' || EXTRACT(YEAR FROM target_date) || 'm' || LPAD(EXTRACT(MONTH FROM target_date)::TEXT, 2, '0');

    -- Aggregate hourly data
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT
        system_id,
        DATE_TRUNC('hour', timestamp) AS period_start,
        DATE_TRUNC('hour', timestamp) + INTERVAL '1 hour' AS period_end,
        'hourly'::VARCHAR(10) AS period_type,
        AVG(cpu_usage) AS avg_cpu_usage,
        AVG(ram_usage) AS avg_ram_usage,
        AVG(gpu_usage) AS avg_gpu_usage,
        AVG(temperature) AS avg_temperature,
        SUM(network_rx_mb) AS total_network_rx_mb,
        SUM(network_tx_mb) AS total_network_tx_mb,
        COUNT(*) AS data_points
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('hour', timestamp)
    ON CONFLICT (system_id, period_start, period_type) DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;

    -- Aggregate daily data
    INSERT INTO aggregated_metrics (
        system_id, period_start, period_end, period_type,
        avg_cpu_usage, avg_ram_usage, avg_gpu_usage, avg_temperature,
        total_network_rx_mb, total_network_tx_mb, data_points
    )
    SELECT
        system_id,
        DATE_TRUNC('day', timestamp) AS period_start,
        DATE_TRUNC('day', timestamp) + INTERVAL '1 day' AS period_end,
        'daily'::VARCHAR(10) AS period_type,
        AVG(cpu_usage) AS avg_cpu_usage,
        AVG(ram_usage) AS avg_ram_usage,
        AVG(gpu_usage) AS avg_gpu_usage,
        AVG(temperature) AS avg_temperature,
        SUM(network_rx_mb) AS total_network_rx_mb,
        SUM(network_tx_mb) AS total_network_tx_mb,
        COUNT(*) AS data_points
    FROM system_metrics
    WHERE DATE(timestamp) = target_date
    GROUP BY system_id, DATE_TRUNC('day', timestamp)
    ON CONFLICT (system_id, period_start, period_type) DO UPDATE SET
        avg_cpu_usage = EXCLUDED.avg_cpu_usage,
        avg_ram_usage = EXCLUDED.avg_ram_usage,
        avg_gpu_usage = EXCLUDED.avg_gpu_usage,
        avg_temperature = EXCLUDED.avg_temperature,
        total_network_rx_mb = EXCLUDED.total_network_rx_mb,
        total_network_tx_mb = EXCLUDED.total_network_tx_mb,
        data_points = EXCLUDED.data_points;
END;
$$ LANGUAGE plpgsql;

-- Scheduled job (requires pg_cron extension or external scheduler)
-- SELECT cron.schedule('daily-aggregation', '0 0 * * *', 'SELECT aggregate_daily_metrics();');
```

## Cleanup Logic

Monthly cleanup job removes partitions older than 30 days:

```sql
-- Cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_partitions()
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    cutoff_date DATE;
    rec RECORD;
BEGIN
    cutoff_date := CURRENT_DATE - INTERVAL '30 days';

    -- Find and drop old partitions
    FOR rec IN
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'system_metrics_y%m__'
        AND tablename > 'system_metrics_y' || EXTRACT(YEAR FROM cutoff_date) || 'm' || LPAD(EXTRACT(MONTH FROM cutoff_date)::TEXT, 2, '0')
    LOOP
        EXECUTE FORMAT('DROP TABLE IF EXISTS %I', rec.tablename);
        RAISE NOTICE 'Dropped partition: %', rec.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Scheduled monthly cleanup (requires pg_cron)
-- SELECT cron.schedule('monthly-cleanup', '0 2 1 * *', 'SELECT cleanup_old_partitions();');
```

## Additional Considerations

- **Monitoring**: Set up alerts for partition creation failures and cleanup job status
- **Backup**: Ensure aggregated data is included in backup strategies
- **Performance**: Monitor query performance and adjust indexes as needed
- **Scaling**: Consider read replicas for aggregated data queries
- **Security**: Implement appropriate access controls and encryption for sensitive data

## Migration Notes

When implementing this schema:
1. Create tables in order: systems, system_metrics, aggregated_metrics
2. Set up initial partitions for current and next month
3. Implement aggregation and cleanup functions
4. Configure scheduled jobs
5. Update application code to insert into partitioned tables