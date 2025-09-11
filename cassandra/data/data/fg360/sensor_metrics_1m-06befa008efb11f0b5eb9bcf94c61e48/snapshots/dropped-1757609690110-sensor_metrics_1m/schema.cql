CREATE TABLE IF NOT EXISTS fg360.sensor_metrics_1m (
    sensor_id text,
    bucket_date date,
    ts timestamp,
    avg_gas double,
    avg_hum double,
    avg_temp double,
    count bigint,
    max_temp double,
    pm25 double,
    wind double,
    PRIMARY KEY ((sensor_id, bucket_date), ts)
) WITH ID = 06befa00-8efb-11f0-b5eb-9bcf94c61e48
    AND CLUSTERING ORDER BY (ts DESC)
    AND additional_write_policy = '99p'
    AND bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND cdc = false
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
    AND compression = {'chunk_length_in_kb': '16', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND memtable = 'default'
    AND crc_check_chance = 1.0
    AND default_time_to_live = 0
    AND extensions = {}
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair = 'BLOCKING'
    AND speculative_retry = '99p';
