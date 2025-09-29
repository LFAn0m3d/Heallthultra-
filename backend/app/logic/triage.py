"""Advanced triage business logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .. import schemas


CRITICAL_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "bp_sys": (80, 180),
    "bp_dia": (40, 120),
    "glucose": (60, 300),
    "hr": (40, 160),
}

ELEVATED_THRESHOLDS: Dict[str, Tuple[float, float]] = {
    "bp_sys": (120, 160),
    "bp_dia": (80, 100),
    "glucose": (140, 250),
    "hr": (100, 130),
}

MEDICATION_ALERTS: Dict[str, str] = {
    "metformin": "ตรวจสอบการทำงานของไตเมื่อใช้ metformin",
    "insulin": "ระวังภาวะน้ำตาลต่ำเมื่อใช้ insulin",
}

DRUG_ALLERGY_CONFLICTS: Dict[str, List[str]] = {
    "penicillin": ["amoxicillin", "ampicillin"],
    "nsaid": ["ibuprofen", "naproxen"],
}


@dataclass
class TriageComputation:
    level: str
    score: float
    actions: List[schemas.RecommendationAction]
    rationale: str
    hints: List[str]
    score_breakdown: Dict[str, float]
    external_advice: str | None = None


def _score_vital(code: str, value: float, breakdown: Dict[str, float]) -> float:
    score = 0.0
    critical = CRITICAL_THRESHOLDS.get(code)
    elevated = ELEVATED_THRESHOLDS.get(code)

    if critical:
        low, high = critical
        if value <= low or value >= high:
            breakdown[f"{code}_critical"] = 40.0
            return 40.0

    if elevated:
        low, high = elevated
        if value <= low or value >= high:
            breakdown[f"{code}_elevated"] = 20.0
            return 20.0

    breakdown[f"{code}_normal"] = 0.0
    return score


def _score_comorbidities(comorbidities: Iterable[str], breakdown: Dict[str, float]) -> float:
    score = 0.0
    for condition in comorbidities:
        condition_lower = condition.lower()
        if condition_lower in {"ckd", "cancer", "copd"}:
            score += 10
            breakdown[f"comorbidity_{condition_lower}"] = 10
        elif condition_lower in {"htn", "dm", "asthma"}:
            score += 5
            breakdown[f"comorbidity_{condition_lower}"] = 5
    return score


def _score_severity(severity: int | None, breakdown: Dict[str, float]) -> float:
    if severity is None:
        return 0.0
    value = float(severity)
    breakdown["self_severity"] = value
    return value


def _medication_actions(medications: Iterable[str]) -> List[schemas.RecommendationAction]:
    actions: List[schemas.RecommendationAction] = []
    for med in medications:
        alert = MEDICATION_ALERTS.get(med.lower())
        if alert:
            actions.append(
                schemas.RecommendationAction(label=alert, urgency="routine")
            )
    return actions


def _drug_allergy_conflicts(medications: Iterable[str], allergies: Iterable[str]) -> List[str]:
    conflicts: List[str] = []
    meds_lower = {m.lower() for m in medications}
    allergies_lower = {a.lower() for a in allergies}
    for allergy in allergies_lower:
        for drug in DRUG_ALLERGY_CONFLICTS.get(allergy, []):
            if drug in meds_lower:
                conflicts.append(f"หลีกเลี่ยง {drug} เนื่องจากประวัติแพ้ {allergy}")
    return conflicts


def analyze(payload: schemas.AnalyzeIn) -> TriageComputation:
    """Score the patient data and return triage decision."""

    breakdown: Dict[str, float] = {}
    score = 0.0
    actions: List[schemas.RecommendationAction] = []
    hints: List[str] = []

    for vital in payload.vitals:
        score += _score_vital(vital.measurement_code, vital.value, breakdown)

    score += _score_comorbidities(payload.comorbidities, breakdown)
    score += _score_severity(payload.severity_0_10, breakdown)

    if any(alert.lower().startswith("self-harm") for alert in payload.alerts):
        breakdown["safety_alert"] = 100.0
        score += 100.0
        actions.append(
            schemas.RecommendationAction(
                label="ให้การดูแลใกล้ชิดและส่งต่อสายด่วนวิกฤตทันที",
                urgency="emergent",
            )
        )

    actions.extend(_medication_actions(payload.medications))
    for conflict in _drug_allergy_conflicts(payload.medications, payload.allergies):
        actions.append(schemas.RecommendationAction(label=conflict, urgency="urgent"))
        breakdown["allergy_conflict"] = breakdown.get("allergy_conflict", 0) + 15.0
        score += 15.0

    if score >= 100:
        level = "red"
    elif score >= 60:
        level = "orange"
    elif score >= 30:
        level = "yellow"
    else:
        level = "green"

    if not actions:
        actions.append(
            schemas.RecommendationAction(
                label="รักษาวิถีชีวิตสุขภาพดีและติดตามอาการ",
                urgency="routine",
            )
        )

    if payload.symptoms:
        if any("chest" in s.lower() for s in payload.symptoms):
            hints.append("ติดตามอาการแน่นหน้าอกและพิจารณา EKG")
        if any("dizzy" in s.lower() for s in payload.symptoms):
            hints.append("ตรวจวัดความดันและน้ำตาลซ้ำ")
    if not hints:
        hints.append("ยังไม่มีสัญญาณจำเพาะ ควรติดตามต่อเนื่อง")

    rationale_parts = [f"คะแนนรวม {score:.0f}"]
    if payload.comorbidities:
        rationale_parts.append("มีโรคประจำตัว: " + ", ".join(payload.comorbidities))
    if payload.alerts:
        rationale_parts.append("พบการแจ้งเตือน: " + ", ".join(payload.alerts))

    return TriageComputation(
        level=level,
        score=score,
        actions=actions,
        rationale="; ".join(rationale_parts),
        hints=hints,
        score_breakdown=breakdown,
    )


def provincial_hints(observations: List[schemas.TrendPoint]) -> str:
    """Generate a lightweight description for provincial analytics."""

    if not observations:
        return "ยังไม่มีข้อมูลเพียงพอ"

    avg = sum(p.value for p in observations) / len(observations)
    if avg > 140:
        return "แนวโน้มระดับสูงกว่าค่าปกติ ควรมีคลินิกเคลื่อนที่"
    if avg < 90:
        return "ระดับเฉลี่ยต่ำ ควรประเมินความเสี่ยงภาวะน้ำตาลต่ำ"
    return "สถานการณ์อยู่ในเกณฑ์ควบคุมได้"
