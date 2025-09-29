"""Triage logic for NCD & mental health assessments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..schemas import AnalyzeRequest, AnalyzeResponse


@dataclass
class TriageResult:
    triage_level: str
    actions: List[str]
    rationale: List[str]
    condition_hints: List[str]

    def to_response(self) -> AnalyzeResponse:
        return AnalyzeResponse(
            triage_level=self.triage_level,
            actions=self.actions,
            rationale=self.rationale,
            condition_hints=self.condition_hints,
        )


RED_FLAG_BP_SYS = 180
RED_FLAG_BP_DIA = 120
HIGH_GLUCOSE = 300


def analyze_case(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Assess the request and return a triage recommendation."""
    triage_level = "เขียว"
    actions: List[str] = ["ติดตามอาการและสุขภาพอย่างต่อเนื่อง"]
    rationale: List[str] = []
    hints: List[str] = []

    # Red flag: self harm
    if payload.red_flag_answers.self_harm:
        triage_level = "แดง"
        actions = [
            "ติดต่อสายด่วนสุขภาพจิต 1323",
            "ไปโรงพยาบาลทันทีหรือโทร 1669",
        ]
        rationale.append("ผู้ป่วยรายงานความคิดทำร้ายตนเอง")
        hints.append("วิกฤตสุขภาพจิต")
        return TriageResult(triage_level, actions, rationale, hints).to_response()

    # Blood pressure checks
    if payload.bp_sys is not None and payload.bp_dia is not None:
        if payload.bp_sys >= RED_FLAG_BP_SYS and payload.bp_dia >= RED_FLAG_BP_DIA:
            triage_level = "แดง"
            actions = ["ไปห้องฉุกเฉินทันที"]
            rationale.append("ค่าความดันอยู่ในช่วงวิกฤต (≥180/120)")
        elif payload.bp_sys >= 160 or payload.bp_dia >= 100:
            triage_level = max_priority(triage_level, "ส้ม")
            actions.append("พบแพทย์เพื่อปรับการรักษาความดัน")
            rationale.append("ความดันสูงกว่าช่วงที่ควบคุมได้")
        elif payload.bp_sys >= 140 or payload.bp_dia >= 90:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("ตรวจติดตามความดันภายใน 1-2 สัปดาห์")
            rationale.append("ความดันเริ่มสูง")
        if payload.bp_sys >= 140 or payload.bp_dia >= 90:
            hints.append("ความดันควบคุมไม่ดี")

    # Glucose checks
    if payload.glucose is not None:
        if payload.glucose >= HIGH_GLUCOSE:
            triage_level = max_priority(triage_level, "ส้ม")
            actions.append("ไปโรงพยาบาลเพื่อตรวจภาวะ DKA/HHS")
            rationale.append("ระดับน้ำตาลสูงมาก ≥300 mg/dL")
        elif payload.glucose >= 180:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("ปรึกษาแพทย์เรื่องการควบคุมน้ำตาล")
            rationale.append("ระดับน้ำตาลสูง")
        if payload.glucose >= 140:
            hints.append("เบาหวานควบคุมไม่ดี")

    # Mental health scales
    mh_hints: List[str] = []
    if payload.phq9 is not None:
        mh_hints.append("ภาวะซึมเศร้าควรได้รับการติดตาม")
        if payload.phq9 >= 20:
            triage_level = max_priority(triage_level, "ส้ม")
            actions.append("พบจิตแพทย์หรือผู้เชี่ยวชาญโดยด่วน")
            rationale.append("คะแนน PHQ-9 สูงมาก")
        elif payload.phq9 >= 15:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("นัดพบผู้เชี่ยวชาญด้านสุขภาพจิตภายใน 1 สัปดาห์")
            rationale.append("คะแนน PHQ-9 สูง")
        elif payload.phq9 >= 10:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("เริ่มการดูแลสุขภาพจิตและติดตามต่อเนื่อง")
            rationale.append("คะแนน PHQ-9 อยู่ในช่วงปานกลาง")
    if payload.gad7 is not None:
        mh_hints.append("ภาวะวิตกกังวลควรได้รับการติดตาม")
        if payload.gad7 >= 15:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("เข้ารับการประเมินสุขภาพจิตเพิ่มเติม")
            rationale.append("คะแนน GAD-7 สูง")
        elif payload.gad7 >= 10:
            triage_level = max_priority(triage_level, "เหลือง")
            actions.append("พิจารณาปรึกษาผู้เชี่ยวชาญด้านสุขภาพจิต")
            rationale.append("คะแนน GAD-7 อยู่ในช่วงปานกลาง")
    hints.extend(mh_hints)

    # Default rationale
    if not rationale:
        rationale.append("ไม่พบสัญญาณอันตรายเร่งด่วน")

    # Deduplicate outputs while preserving order
    actions = dedupe(actions)
    rationale = dedupe(rationale)
    hints = dedupe(hints)

    return TriageResult(triage_level, actions, rationale, hints).to_response()


PRIORITY_ORDER = {"แดง": 3, "ส้ม": 2, "เหลือง": 1, "เขียว": 0}


def max_priority(current: str, candidate: str) -> str:
    return candidate if PRIORITY_ORDER[candidate] > PRIORITY_ORDER[current] else current


def dedupe(items: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered
