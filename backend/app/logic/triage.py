"""Triage business logic."""
from __future__ import annotations

from typing import Dict, List, Tuple


def triage_level_from_inputs(payload: Dict) -> Tuple[str, List[str], str]:
    """Return triage level, actions, and rationale based on payload."""
    actions: List[str] = []
    rationale_parts: List[str] = []
    triage_level = "เขียว"

    bp_sys = payload.get("bp_sys")
    bp_dia = payload.get("bp_dia")
    glucose = payload.get("glucose")
    self_harm = payload.get("self_harm") or payload.get("red_flag_answers", {}).get("self_harm")

    if self_harm:
        triage_level = "แดง"
        actions.extend([
            "โทรหาสายด่วนสุขภาพจิต 1323 หรือพบแพทย์ทันที",
            "อย่าอยู่ลำพัง ขอความช่วยเหลือจากคนใกล้ชิด",
        ])
        rationale_parts.append("มีความเสี่ยงทำร้ายตนเอง")

    if bp_sys is not None and bp_dia is not None and bp_sys >= 180 and bp_dia >= 120:
        triage_level = "แดง"
        actions.extend([
            "ไปห้องฉุกเฉินทันที",
            "หลีกเลี่ยงการขับรถเอง",
        ])
        rationale_parts.append("ความดันโลหิตเข้าเกณฑ์วิกฤต")

    if glucose is not None and glucose >= 300:
        if triage_level != "แดง":
            triage_level = "ส้ม"
        actions.append("ตรวจสอบระดับน้ำตาลและพบแพทย์โดยเร็ว")
        rationale_parts.append("ระดับน้ำตาลสูงกว่าปกติ")

    if not rationale_parts:
        triage_level = "เหลือง" if payload.get("severity", 0) >= 5 else "เขียว"
        if triage_level == "เหลือง":
            actions.append("นัดพบแพทย์ภายใน 24-48 ชั่วโมง")
            rationale_parts.append("ระดับอาการปานกลาง")
        else:
            actions.append("ติดตามอาการและดูแลตนเอง")
            rationale_parts.append("ไม่พบสัญญาณอันตรายเร่งด่วน")

    rationale = "; ".join(dict.fromkeys(rationale_parts)) or "ประเมินไม่พบข้อมูลเพียงพอ"
    actions = list(dict.fromkeys(actions))
    return triage_level, actions, rationale


def mock_condition_hints(payload: Dict) -> List[str]:
    """Provide a naive list of possible conditions for demonstration."""
    hints: List[str] = []
    domain = payload.get("domain")
    symptom = payload.get("primary_symptom", "").lower()

    if domain == "NCD":
        if "เวียน" in symptom or "หน้ามืด" in symptom:
            hints.append("ตรวจระดับน้ำตาลและความดัน")
        if payload.get("bp_sys") and payload.get("bp_sys") > 140:
            hints.append("อาจเกี่ยวข้องกับความดันโลหิตสูง")
        if payload.get("glucose") and payload.get("glucose") > 140:
            hints.append("ติดตามเบาหวาน")
    elif domain == "MH":
        if payload.get("phq9") and payload["phq9"] >= 10:
            hints.append("อาจมีภาวะซึมเศร้าระดับปานกลาง")
        if payload.get("gad7") and payload["gad7"] >= 10:
            hints.append("อาจมีความวิตกกังวลสูง")
        if payload.get("isi") and payload["isi"] >= 15:
            hints.append("ภาวะนอนไม่หลับระดับปานกลาง")

    if not hints:
        hints.append("ควรติดตามอาการเพิ่มเติม")

    return hints
