"""
WB Label Processor v4.4 — Enhanced Vertical Tracking Detection
Handles Waybill labels, barcode parsing, vertical text, and tracking validation.
"""
import re, json, hashlib, base64
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

@dataclass
class ParsedLabel:
    tracking_number: str
    carrier: str
    origin: str
    destination: str
    weight_kg: float
    service_type: str
    barcode_data: str
    raw_text: str
    confidence: float = 0.0
    vertical_detected: bool = False
    anomalies: List[str] = field(default_factory=list)

class WBLabelProcessor:
    CARRIER_PATTERNS = {
        "DHL": r"\b(\d{10,11})\b",
        "FedEx": r"\b(\d{12,14}|\d{20,22})\b",
        "UPS": r"\b(1Z[A-Z0-9]{16})\b",
        "USPS": r"\b(\d{20,22}|\d{13})\b",
        "Amazon": r"\b(TBA\d{12}|TBC\d{12})\b",
        "Generic": r"\b([A-Z]{2}\d{9}[A-Z]{2})\b"
    }

    SERVICE_TYPES = ["STANDARD", "EXPRESS", "OVERNIGHT", "SAME_DAY", "ECONOMY", "PRIORITY"]

    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.vertical_threshold = 0.3

    def process_image_text(self, ocr_text: str, image_metadata: Optional[Dict] = None) -> ParsedLabel:
        """Process OCR-extracted text from a waybill label image."""
        raw = ocr_text.strip()
        vertical = self._detect_vertical_text(raw)

        # Normalize vertical text
        if vertical:
            raw = self._normalize_vertical(raw)

        tracking, carrier = self._extract_tracking(raw)
        origin, destination = self._extract_locations(raw)
        weight = self._extract_weight(raw)
        service = self._extract_service(raw)
        barcode = self._extract_barcode(raw)

        anomalies = []
        if not tracking:
            anomalies.append("No tracking number detected")
        if weight <= 0:
            anomalies.append("Invalid or missing weight")
        if vertical and len(raw) < 20:
            anomalies.append("Vertical text may be truncated")

        confidence = self._compute_confidence(tracking, carrier, weight, service, len(anomalies))

        self.processed_count += 1
        if anomalies:
            self.error_count += 1

        return ParsedLabel(
            tracking_number=tracking or "UNKNOWN",
            carrier=carrier or "UNKNOWN",
            origin=origin or "UNKNOWN",
            destination=destination or "UNKNOWN",
            weight_kg=weight,
            service_type=service or "STANDARD",
            barcode_data=barcode or "",
            raw_text=raw,
            confidence=confidence,
            vertical_detected=vertical,
            anomalies=anomalies
        )

    def _detect_vertical_text(self, text: str) -> bool:
        """Detect if text appears to be vertically oriented."""
        lines = text.split("\n")
        if len(lines) < 3:
            return False
        # Check for short lines (single characters or very short) suggesting vertical layout
        short_lines = sum(1 for l in lines if len(l.strip()) <= 3)
        ratio = short_lines / len(lines) if lines else 0
        return ratio > self.vertical_threshold

    def _normalize_vertical(self, text: str) -> str:
        """Reconstruct horizontal text from vertical layout."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        # Try to read column-wise
        if not lines:
            return text
        max_len = max(len(l) for l in lines)
        result = []
        for col in range(max_len):
            column_chars = []
            for line in lines:
                if col < len(line):
                    column_chars.append(line[col])
            result.append("".join(column_chars))
        return " ".join(result)

    def _extract_tracking(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        for carrier, pattern in self.CARRIER_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1), carrier
        return None, None

    def _extract_locations(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        # Simple regex for city/state or zip patterns
        zip_pattern = r"\b(\d{5}(-\d{4})?)\b"
        zips = re.findall(zip_pattern, text)
        if len(zips) >= 2:
            return zips[0][0], zips[-1][0]
        # Try city extraction
        city_pattern = r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?),?\s*[A-Z]{2}"
        cities = re.findall(city_pattern, text)
        if len(cities) >= 2:
            return cities[0], cities[-1]
        return None, None

    def _extract_weight(self, text: str) -> float:
        patterns = [
            r"(\d+\.?\d*)\s*(kg|kgs|kilos)",
            r"(\d+\.?\d*)\s*(lb|lbs|pounds?)\s*[=~]\s*(\d+\.?\d*)\s*kg",
            r"WT[:\s]*(\d+\.?\d*)"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                if "lb" in pat.lower() and len(match.groups()) > 2:
                    return float(match.group(3)) if match.group(3) else float(match.group(1)) * 0.453592
                return float(match.group(1))
        return 0.0

    def _extract_service(self, text: str) -> Optional[str]:
        upper = text.upper()
        for svc in self.SERVICE_TYPES:
            if svc.replace("_", " ") in upper or svc in upper:
                return svc
        return None

    def _extract_barcode(self, text: str) -> Optional[str]:
        # Look for long numeric strings typical of barcodes
        codes = re.findall(r"\b(\d{15,25})\b", text)
        return codes[0] if codes else None

    def _compute_confidence(self, tracking, carrier, weight, service, anomaly_count) -> float:
        score = 0.0
        if tracking:
            score += 0.3
        if carrier:
            score += 0.2
        if weight > 0:
            score += 0.2
        if service:
            score += 0.1
        score -= anomaly_count * 0.15
        return max(0.0, min(1.0, score))

    def batch_process(self, texts: List[str]) -> List[ParsedLabel]:
        return [self.process_image_text(t) for t in texts]

    def get_stats(self) -> Dict:
        return {
            "processed": self.processed_count,
            "errors": self.error_count,
            "success_rate": round(1 - self.error_count / max(self.processed_count, 1), 3)
        }
