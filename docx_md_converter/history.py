import os
import csv
from datetime import datetime
from typing import Dict, Any, Optional

STANDARD_FIELDS = ["file_path", "file_mtime", "converted_at", "output_path", "status", "error_message"]

class ConversionHistory:
    def __init__(self, csv_path: str = "conversion_history.csv"):
        self.csv_path = csv_path
        self.records: Dict[str, Dict[str, Any]] = {}
        self.all_metadata_keys = set()
        self._load()

    def _normalize_path(self, path: str) -> str:
        return os.path.normpath(os.path.abspath(path))

    def _load(self):
        if not os.path.exists(self.csv_path):
            return

        try:
            with open(self.csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    for field in reader.fieldnames:
                        if field not in STANDARD_FIELDS:
                            self.all_metadata_keys.add(field)
                for row in reader:
                    norm_path = self._normalize_path(row.get("file_path", ""))
                    if norm_path:
                        self.records[norm_path] = row
        except Exception as e:
            print(f"Aviso ao carregar histórico '{self.csv_path}': {e}")

    def is_processed(self, docx_path: str) -> bool:
        norm_path = self._normalize_path(docx_path)
        if norm_path not in self.records:
            return False

        record = self.records[norm_path]
        if record.get("status") != "SUCCESS":
            return False

        try:
            saved_mtime = float(record.get("file_mtime", 0))
            current_mtime = os.path.getmtime(norm_path)
            # Considera processado se a data de modificação for idêntica ou menor
            return abs(current_mtime - saved_mtime) < 1e-4
        except (ValueError, TypeError, OSError):
            return False

    def record(
        self,
        docx_path: str,
        output_path: str,
        metadata: Optional[Dict[str, str]] = None,
        status: str = "SUCCESS",
        error_message: str = ""
    ):
        norm_path = self._normalize_path(docx_path)
        try:
            current_mtime = str(os.path.getmtime(norm_path))
        except OSError:
            current_mtime = "0"

        row = {
            "file_path": docx_path,
            "file_mtime": current_mtime,
            "converted_at": datetime.now().isoformat(timespec="seconds"),
            "output_path": output_path,
            "status": status,
            "error_message": error_message
        }

        if metadata:
            for k, v in metadata.items():
                row[k] = v
                self.all_metadata_keys.add(k)

        self.records[norm_path] = row

    def save(self):
        fieldnames = list(STANDARD_FIELDS) + sorted(list(self.all_metadata_keys))
        
        # Garante criação da pasta pai se o csv estiver em um subdiretório
        parent_dir = os.path.dirname(self.csv_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(self.csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in self.records.values():
                writer.writerow(record)
