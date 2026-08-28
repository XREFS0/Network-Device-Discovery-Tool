CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    network_range TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    discovery_method TEXT NOT NULL,
    device_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    mac_address TEXT NOT NULL DEFAULT 'Unknown',
    hostname TEXT NOT NULL DEFAULT 'Unknown',
    vendor TEXT NOT NULL DEFAULT 'Unknown',
    status TEXT NOT NULL DEFAULT 'Unknown',
    method TEXT NOT NULL DEFAULT 'Unknown',
    response_time_ms REAL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    discovery_count INTEGER DEFAULT 1,
    FOREIGN KEY(scan_id) REFERENCES scans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_devices_scan_id ON devices(scan_id);
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
