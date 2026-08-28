import sqlite3
import logging
from typing import List, Optional, Tuple, Dict, Any
from app.core.models import ScanInfo, Device
from app.core.constants import DiscoveryMethod, DeviceStatus
from app.database.connection import get_db_connection

logger = logging.getLogger(__name__)

class ScanRepository:
    @staticmethod
    def insert_scan(scan: ScanInfo) -> int:
        """Insert a new scan record and return its ID."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scans (start_time, end_time, network_range, interface_name, discovery_method, device_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scan.start_time,
                    scan.end_time,
                    scan.network_range,
                    scan.interface_name,
                    scan.discovery_method.value,
                    scan.device_count,
                )
            )
            conn.commit()
            scan_id = cursor.lastrowid
            if scan_id is None:
                raise sqlite3.Error("Failed to retrieve lastrowid")
            return scan_id
        except sqlite3.Error as e:
            logger.error(f"Error inserting scan: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def update_scan_completion(scan_id: int, end_time: str, device_count: int) -> None:
        """Update the scan's end time and final discovered device count."""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE scans
                SET end_time = ?, device_count = ?
                WHERE id = ?
                """,
                (end_time, device_count, scan_id)
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error updating scan completion: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def insert_device(scan_id: int, device: Device) -> None:
        """Insert a discovered device associated with a scan."""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO devices (
                    scan_id, ip_address, mac_address, hostname, vendor,
                    status, method, response_time_ms, first_seen, last_seen, discovery_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    device.ip_address,
                    device.mac_address,
                    device.hostname,
                    device.vendor,
                    device.status.value,
                    device.method.value,
                    device.response_time_ms,
                    device.first_seen,
                    device.last_seen,
                    device.discovery_count,
                )
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error inserting device: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_all_scans() -> List[ScanInfo]:
        """Retrieve all scans from the database."""
        scans: List[ScanInfo] = []
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, start_time, end_time, network_range, interface_name, discovery_method, device_count FROM scans ORDER BY id DESC")
            for row in cursor.fetchall():
                scans.append(
                    ScanInfo(
                        id=row["id"],
                        start_time=row["start_time"],
                        end_time=row["end_time"],
                        network_range=row["network_range"],
                        interface_name=row["interface_name"],
                        discovery_method=DiscoveryMethod(row["discovery_method"]),
                        device_count=row["device_count"]
                    )
                )
        except sqlite3.Error as e:
            logger.error(f"Error getting scans: {e}")
        finally:
            conn.close()
        return scans

    @staticmethod
    def get_scan_devices(scan_id: int) -> List[Device]:
        """Retrieve all devices discovered during a specific scan."""
        devices: List[Device] = []
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ip_address, mac_address, hostname, vendor, status, method, response_time_ms, first_seen, last_seen, discovery_count
                FROM devices
                WHERE scan_id = ?
                ORDER BY ip_address
                """,
                (scan_id,)
            )
            for row in cursor.fetchall():
                devices.append(
                    Device(
                        ip_address=row["ip_address"],
                        mac_address=row["mac_address"],
                        hostname=row["hostname"],
                        vendor=row["vendor"],
                        status=DeviceStatus(row["status"]),
                        method=DiscoveryMethod(row["method"]),
                        response_time_ms=row["response_time_ms"],
                        first_seen=row["first_seen"],
                        last_seen=row["last_seen"],
                        discovery_count=row["discovery_count"]
                    )
                )
        except sqlite3.Error as e:
            logger.error(f"Error getting devices for scan {scan_id}: {e}")
        finally:
            conn.close()
        return devices

    @staticmethod
    def delete_scan(scan_id: int) -> None:
        """Delete a scan and all its associated device records (cascade)."""
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error deleting scan {scan_id}: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def clear_all_history() -> None:
        """Clear all scan records and device records from the database."""
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM scans")
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error clearing history: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_device_history_summary(ip_address: str, mac_address: str) -> Dict[str, Any]:
        """
        Aggregate history for a device across all scans using IP and MAC.
        Returns first_seen, last_seen, and total times discovered.
        """
        result = {
            "first_seen": "Unknown",
            "last_seen": "Unknown",
            "discovery_count": 0
        }
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # If we have a valid MAC address, search by MAC. Otherwise fallback to IP.
            if mac_address and mac_address.lower() != "unknown":
                cursor.execute(
                    """
                    SELECT MIN(first_seen) as first_s, MAX(last_seen) as last_s, COUNT(DISTINCT scan_id) as count_s
                    FROM devices
                    WHERE mac_address = ?
                    """,
                    (mac_address,)
                )
            else:
                cursor.execute(
                    """
                    SELECT MIN(first_seen) as first_s, MAX(last_seen) as last_s, COUNT(DISTINCT scan_id) as count_s
                    FROM devices
                    WHERE ip_address = ?
                    """,
                    (ip_address,)
                )
            
            row = cursor.fetchone()
            if row and row["count_s"] > 0:
                result["first_seen"] = row["first_s"] if row["first_s"] else "Unknown"
                result["last_seen"] = row["last_s"] if row["last_s"] else "Unknown"
                result["discovery_count"] = row["count_s"]
        except sqlite3.Error as e:
            logger.error(f"Error querying device history summary: {e}")
        finally:
            conn.close()
        return result
