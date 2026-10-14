"""
Deterministic Irrigation Calculation Engine
============================================
All numeric irrigation estimates come from this module.
Groq / AI is used only for explanations — never for calculating agronomy values.

References used for crop coefficients (Kc):
  FAO Irrigation and Drainage Paper 56 — Allen et al. 1998
  https://www.fao.org/3/x0490e/x0490e0b.htm
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


# ── Crop coefficient table ────────────────────────────────────────────────────
# Source: FAO-56, Table 12 (single crop coefficient approach)
# Format: crop_name → {growth_stage: Kc}
# Growth stages: initial, development, mid, late
FAO56_KC: Dict[str, Dict[str, float]] = {
    "rice": {"initial": 1.05, "development": 1.15, "mid": 1.20, "late": 0.90},
    "wheat": {"initial": 0.30, "development": 0.75, "mid": 1.15, "late": 0.40},
    "maize": {"initial": 0.30, "development": 0.70, "mid": 1.20, "late": 0.60},
    "sorghum": {"initial": 0.30, "development": 0.65, "mid": 1.00, "late": 0.55},
    "cotton": {"initial": 0.35, "development": 0.70, "mid": 1.20, "late": 0.60},
    "sunflower": {"initial": 0.35, "development": 0.75, "mid": 1.15, "late": 0.55},
    "sugarcane": {"initial": 0.40, "development": 0.80, "mid": 1.25, "late": 0.75},
    "potato": {"initial": 0.50, "development": 0.75, "mid": 1.15, "late": 0.75},
    "tomato": {"initial": 0.60, "development": 0.75, "mid": 1.15, "late": 0.80},
    "onion": {"initial": 0.50, "development": 0.70, "mid": 1.05, "late": 0.75},
    "groundnut": {"initial": 0.40, "development": 0.75, "mid": 1.15, "late": 0.60},
    "soybean": {"initial": 0.40, "development": 0.80, "mid": 1.15, "late": 0.50},
    "chickpea": {"initial": 0.40, "development": 0.70, "mid": 1.05, "late": 0.55},
    "banana": {"initial": 0.50, "development": 0.80, "mid": 1.10, "late": 1.00},
    "default": {"initial": 0.50, "development": 0.75, "mid": 1.00, "late": 0.75},
}

# Irrigation efficiency factors (fraction of applied water reaching the crop root zone)
IRRIGATION_EFFICIENCY: Dict[str, float] = {
    "drip": 0.90,
    "sprinkler": 0.80,
    "flood": 0.60,
    "furrow": 0.65,
    "default": 0.70,
}

# Effective rainfall fraction (simplified from FAO-56 guidelines)
# Fraction of forecast rainfall that is actually available to the crop
EFFECTIVE_RAINFALL_FRACTION = 0.75  # conservative estimate

# Minimum safe water-storage threshold (fraction of current storage → trigger alert)
STORAGE_ALERT_THRESHOLD_FRACTION = 0.15


@dataclass
class IrrigationInputs:
    """All validated inputs required for irrigation calculations."""
    # Farm
    area_hectares: Optional[float] = None
    irrigation_method: Optional[str] = None
    water_storage_litres: Optional[float] = None

    # Crop
    crop_type: Optional[str] = None
    growth_stage: Optional[str] = None
    soil_moisture_pct: Optional[float] = None

    # Weather
    et0_mm_per_day: Optional[float] = None         # Reference ET from Open-Meteo
    forecast_rain_mm: Optional[float] = None        # Forecast total rainfall (mm)
    rain_probability_pct: Optional[float] = None    # % probability of rain
    forecast_days: int = 1


@dataclass
class IrrigationResults:
    """Deterministic calculation outputs."""
    # Crop coefficients
    kc_used: Optional[float] = None
    kc_source: str = "FAO-56 Table 12"

    # ETc (crop evapotranspiration) in mm/day
    etc_mm_per_day: Optional[float] = None

    # Irrigation requirement
    net_irrigation_mm: Optional[float] = None       # ETc − effective rainfall
    gross_irrigation_mm: Optional[float] = None     # net / efficiency
    gross_irrigation_litres: Optional[float] = None # gross × area × 1000 (ha→L: 1 mm/ha = 10 000 L)

    # Water budget
    daily_demand_litres: Optional[float] = None
    days_water_remaining: Optional[float] = None
    storage_alert: bool = False

    # Effective rainfall
    effective_rainfall_mm: Optional[float] = None

    # Recommendation
    recommended_action: str = "Insufficient data — more information needed"
    reason: str = ""
    assumptions: List[str] = field(default_factory=list)
    missing_inputs: List[str] = field(default_factory=list)
    uncertainty: str = ""

    # Efficiency used
    efficiency_used: Optional[float] = None
    efficiency_source: str = ""


def _normalise_crop(crop: Optional[str]) -> str:
    if not crop:
        return "default"
    c = crop.lower().strip()
    for key in FAO56_KC:
        if key in c or c in key:
            return key
    return "default"


def _normalise_stage(stage: Optional[str]) -> str:
    if not stage:
        return "mid"
    s = stage.lower().strip()
    mapping = {
        "initial": "initial", "germination": "initial", "seedling": "initial",
        "dev": "development", "development": "development", "vegetative": "development",
        "growing": "development",
        "mid": "mid", "flowering": "mid", "reproductive": "mid",
        "late": "late", "harvest": "late", "maturity": "late", "ripening": "late",
    }
    for key, value in mapping.items():
        if key in s:
            return value
    return "mid"


def _normalise_method(method: Optional[str]) -> str:
    if not method:
        return "default"
    m = method.lower().strip()
    for key in IRRIGATION_EFFICIENCY:
        if key in m:
            return key
    return "default"


def calculate_irrigation(inputs: IrrigationInputs) -> IrrigationResults:
    """
    Main deterministic irrigation calculation.

    Uses ETc = ET0 × Kc (FAO-56 single-crop coefficient method).
    Returns structured results with all assumptions stated.
    """
    results = IrrigationResults()
    missing: list[str] = []
    assumptions: list[str] = []

    # ── 1. Crop coefficient ──────────────────────────────────────────────────
    crop_key = _normalise_crop(inputs.crop_type)
    stage_key = _normalise_stage(inputs.growth_stage)
    kc = FAO56_KC[crop_key][stage_key]
    results.kc_used = kc

    if crop_key == "default":
        missing.append("Crop type not recognised — using default Kc=1.00 (mid-season)")
        assumptions.append(f"Kc assumed from FAO-56 defaults (crop: '{inputs.crop_type}')")
    else:
        assumptions.append(f"Kc={kc} for {crop_key} at {stage_key} stage (FAO-56 Table 12)")

    if not inputs.growth_stage:
        missing.append("Growth stage not provided — mid-season assumed")

    # ── 2. ETc = ET0 × Kc ───────────────────────────────────────────────────
    if inputs.et0_mm_per_day is not None and inputs.et0_mm_per_day > 0:
        etc = inputs.et0_mm_per_day * kc * inputs.forecast_days
        results.etc_mm_per_day = inputs.et0_mm_per_day * kc
        assumptions.append(
            f"ETc = ET0 × Kc = {inputs.et0_mm_per_day:.2f} × {kc} "
            f"= {results.etc_mm_per_day:.2f} mm/day (FAO-56)"
        )
    else:
        missing.append("ET0 (reference evapotranspiration) not available from weather service")
        # Fallback: estimate ET0 from typical tropical average (~5 mm/day)
        fallback_et0 = 5.0
        etc = fallback_et0 * kc * inputs.forecast_days
        results.etc_mm_per_day = fallback_et0 * kc
        assumptions.append(
            f"ET0 unavailable — fallback ET0={fallback_et0} mm/day assumed "
            "(typical tropical/subtropical average; verify locally)"
        )

    # ── 3. Effective rainfall ────────────────────────────────────────────────
    eff_rain = 0.0
    if inputs.forecast_rain_mm is not None and inputs.forecast_rain_mm > 0:
        prob = inputs.rain_probability_pct or 100.0
        # Apply probability discount: treat as uncertain if < 70 %
        if prob < 70:
            eff_rain = 0.0
            assumptions.append(
                f"Forecast rainfall {inputs.forecast_rain_mm:.1f} mm ignored: "
                f"probability only {prob:.0f}% (< 70 % threshold) — not safe to rely on"
            )
        else:
            eff_rain = inputs.forecast_rain_mm * EFFECTIVE_RAINFALL_FRACTION
            results.effective_rainfall_mm = eff_rain
            assumptions.append(
                f"Effective rainfall = {inputs.forecast_rain_mm:.1f} × {EFFECTIVE_RAINFALL_FRACTION} "
                f"= {eff_rain:.2f} mm ({prob:.0f}% probability; FAO-56 effective rain fraction)"
            )
    else:
        assumptions.append("No forecast rainfall available — irrigation requirement not reduced")

    # ── 4. Net irrigation requirement ───────────────────────────────────────
    net_mm = max(0.0, etc - eff_rain)
    results.net_irrigation_mm = net_mm

    # ── 5. Efficiency & gross requirement ───────────────────────────────────
    method_key = _normalise_method(inputs.irrigation_method)
    efficiency = IRRIGATION_EFFICIENCY[method_key]
    results.efficiency_used = efficiency
    results.efficiency_source = (
        f"{method_key} irrigation efficiency = {efficiency:.0%} "
        "(FAO irrigation system efficiency guidelines)"
    )

    if inputs.irrigation_method and method_key == "default":
        missing.append(
            f"Irrigation method '{inputs.irrigation_method}' not recognised — "
            "using default efficiency 70%"
        )

    if net_mm > 0:
        gross_mm = net_mm / efficiency
        results.gross_irrigation_mm = gross_mm
        assumptions.append(
            f"Gross irrigation = net / efficiency = {net_mm:.2f} / {efficiency} "
            f"= {gross_mm:.2f} mm"
        )
    else:
        gross_mm = 0.0
        results.gross_irrigation_mm = 0.0

    # ── 6. Convert to litres ─────────────────────────────────────────────────
    # 1 mm over 1 ha = 10 000 litres
    if inputs.area_hectares:
        vol_litres = gross_mm * inputs.area_hectares * 10_000
        results.gross_irrigation_litres = vol_litres
        results.daily_demand_litres = (
            results.gross_irrigation_mm / inputs.forecast_days * inputs.area_hectares * 10_000
            if inputs.forecast_days > 0 else None
        )
        assumptions.append(
            f"Volume = {gross_mm:.2f} mm × {inputs.area_hectares} ha × 10 000 "
            f"= {vol_litres:,.0f} litres"
        )
    else:
        missing.append("Farm area not provided — volume in litres cannot be calculated")

    # ── 7. Water budget & storage alert ──────────────────────────────────────
    if inputs.water_storage_litres is not None and results.daily_demand_litres:
        daily = results.daily_demand_litres
        days_remaining = inputs.water_storage_litres / daily if daily > 0 else None
        results.days_water_remaining = days_remaining

        alert_threshold = inputs.water_storage_litres * STORAGE_ALERT_THRESHOLD_FRACTION
        if results.gross_irrigation_litres and results.gross_irrigation_litres > inputs.water_storage_litres:
            results.storage_alert = True
        elif days_remaining is not None and days_remaining < 3:
            results.storage_alert = True

        assumptions.append(
            f"Water budget: {inputs.water_storage_litres:,.0f} L available, "
            f"~{daily:,.0f} L/day estimated demand → "
            f"~{days_remaining:.1f} days remaining"
            if days_remaining else
            f"Water budget: {inputs.water_storage_litres:,.0f} L available"
        )
    elif inputs.water_storage_litres is None:
        missing.append("Available water storage not provided — water budget cannot be calculated")

    # ── 8. Recommendation ───────────────────────────────────────────────────
    action, reason = _determine_action(inputs, results)
    results.recommended_action = action
    results.reason = reason

    results.missing_inputs = missing
    results.assumptions = assumptions

    # Uncertainty statement
    uncertainty_parts = []
    if missing:
        uncertainty_parts.append(
            f"Estimates are less reliable because: {'; '.join(missing)}."
        )
    if inputs.et0_mm_per_day is None:
        uncertainty_parts.append(
            "ET0 was estimated from a typical average — local conditions may differ."
        )
    if inputs.rain_probability_pct and inputs.rain_probability_pct < 80:
        uncertainty_parts.append(
            f"Forecast rain has only {inputs.rain_probability_pct:.0f}% probability and has not been used."
        )
    results.uncertainty = " ".join(uncertainty_parts) if uncertainty_parts else "Low — all key inputs were available."

    return results


def _determine_action(
    inputs: IrrigationInputs,
    results: IrrigationResults,
) -> tuple[str, str]:
    """Rule-based action determination. Returns (action, reason)."""

    # Critical: water storage is dangerously low
    if (
        inputs.water_storage_litres is not None
        and results.gross_irrigation_litres is not None
        and results.gross_irrigation_litres > inputs.water_storage_litres
    ):
        return (
            "WATER SHORTAGE — Irrigate only the highest-priority crops using minimum water",
            f"Required irrigation volume ({results.gross_irrigation_litres:,.0f} L) exceeds "
            f"available storage ({inputs.water_storage_litres:,.0f} L). "
            "Prioritise crop survival. Consider emergency water sourcing.",
        )

    if results.storage_alert and (
        results.days_water_remaining is not None and results.days_water_remaining < 3
    ):
        return (
            "URGENT — Water critically low. Irrigate minimally and seek additional supply",
            f"Only ~{results.days_water_remaining:.1f} days of water remain at current demand. "
            "Apply minimal irrigation to protect the crop and urgently source additional water.",
        )

    # Sufficient rainfall forecast (≥70 % probability)
    if (
        inputs.forecast_rain_mm is not None
        and inputs.rain_probability_pct is not None
        and inputs.rain_probability_pct >= 70
        and inputs.forecast_rain_mm >= (results.etc_mm_per_day or 0) * inputs.forecast_days * 0.8
    ):
        return (
            "Reassess after forecast rainfall — delay irrigation for now",
            f"Forecast rainfall ({inputs.forecast_rain_mm:.1f} mm, "
            f"{inputs.rain_probability_pct:.0f}% probability) is expected to meet most of the "
            f"estimated crop requirement ({results.etc_mm_per_day or 0:.2f} mm/day × "
            f"{inputs.forecast_days} days). Monitor and reassess after the rain event.",
        )

    # No irrigation needed (ETc met)
    if results.net_irrigation_mm is not None and results.net_irrigation_mm <= 0:
        return (
            "No irrigation required — crop water demand is met",
            "Estimated effective rainfall exceeds crop evapotranspiration demand.",
        )

    # Insufficient data
    if results.missing_inputs and results.gross_irrigation_litres is None:
        return (
            "Insufficient data — provide more information for a reliable recommendation",
            "Key inputs are missing: " + ", ".join(results.missing_inputs[:3]),
        )

    # Normal irrigation recommended
    vol_str = f"{results.gross_irrigation_litres:,.0f} L" if results.gross_irrigation_litres else "volume unknown"
    return (
        f"Irrigate now — estimated requirement: {vol_str}",
        f"Crop evapotranspiration ({results.etc_mm_per_day:.2f} mm/day) exceeds effective rainfall. "
        f"Apply approximately {results.gross_irrigation_mm:.1f} mm gross ({vol_str}) over "
        f"{inputs.forecast_days} day(s) using {inputs.irrigation_method or 'available'} irrigation."
        if results.etc_mm_per_day else
        "Crop water demand estimated from available data — verify with local ET0 values.",
    )


def calculate_water_budget(
    storage_litres: float,
    daily_demand_litres: float,
) -> Dict[str, Any]:
    """Standalone water budget calculator."""
    if daily_demand_litres <= 0:
        return {
            "days_remaining": None,
            "alert": False,
            "message": "Daily demand is zero or negative — check inputs.",
        }
    days = storage_litres / daily_demand_litres
    alert = days < 3 or storage_litres < daily_demand_litres * 3
    return {
        "storage_litres": storage_litres,
        "daily_demand_litres": daily_demand_litres,
        "days_remaining": round(days, 1),
        "alert": alert,
        "message": (
            f"⚠️ Water will run out in approximately {days:.1f} days. Seek additional supply."
            if alert else
            f"Water supply adequate for approximately {days:.1f} days at current demand."
        ),
    }


def run_what_if_scenarios(
    base_inputs: IrrigationInputs,
) -> List[Dict[str, Any]]:
    """
    Generate four comparison scenarios for the What-If Simulator.
    Returns a list of scenario result dicts.
    """
    scenarios = []

    # Scenario 1: Irrigate now
    s1 = calculate_irrigation(base_inputs)
    remaining_1 = (
        (base_inputs.water_storage_litres or 0) - (s1.gross_irrigation_litres or 0)
    )
    scenarios.append({
        "scenario_name": "Irrigate Now",
        "description": "Apply the full estimated irrigation requirement immediately.",
        "estimated_water_use_litres": s1.gross_irrigation_litres,
        "remaining_storage_litres": max(0, remaining_1) if base_inputs.water_storage_litres else None,
        "days_remaining": s1.days_water_remaining,
        "recommendation": s1.recommended_action,
        "assumptions": s1.assumptions,
        "limitations": s1.missing_inputs,
    })

    # Scenario 2: Wait for rain (use forecast rain if ≥50 %)
    import dataclasses as _dc
    rain_inputs = _dc.replace(base_inputs, rain_probability_pct=max(base_inputs.rain_probability_pct or 0, 70))
    s2 = calculate_irrigation(rain_inputs)
    remaining_2 = (
        (base_inputs.water_storage_litres or 0) - (s2.gross_irrigation_litres or 0)
    )
    scenarios.append({
        "scenario_name": "Wait for Forecast Rain",
        "description": "Delay irrigation and reassess after the forecast rain event.",
        "estimated_water_use_litres": s2.gross_irrigation_litres,
        "remaining_storage_litres": max(0, remaining_2) if base_inputs.water_storage_litres else None,
        "days_remaining": s2.days_water_remaining,
        "recommendation": s2.recommended_action,
        "assumptions": s2.assumptions + ["Rain probability assumed ≥70% for planning purposes."],
        "limitations": ["Actual rainfall may differ from forecast.",
                        "Delaying irrigation carries crop-water stress risk if rain does not occur."],
    })

    # Scenario 3: Apply 50 % water budget (conservation mode)
    budget_inputs = _dc.replace(base_inputs)
    s3_full = calculate_irrigation(budget_inputs)
    half_vol = (s3_full.gross_irrigation_litres or 0) / 2
    remaining_3 = (base_inputs.water_storage_litres or 0) - half_vol
    scenarios.append({
        "scenario_name": "50% Water Budget (Conservation)",
        "description": "Apply only half the estimated requirement to conserve storage.",
        "estimated_water_use_litres": half_vol if s3_full.gross_irrigation_litres else None,
        "remaining_storage_litres": max(0, remaining_3) if base_inputs.water_storage_litres else None,
        "days_remaining": (remaining_3 / s3_full.daily_demand_litres) if (s3_full.daily_demand_litres and remaining_3 > 0) else None,
        "recommendation": (
            "Apply 50% of recommended water. Monitor crop for stress signs."
        ),
        "assumptions": [
            "50% application may cause mild crop water stress depending on current soil moisture.",
            "Suitable for short-term water conservation only.",
        ],
        "limitations": [
            "Prolonged deficit irrigation can reduce yield.",
            "Soil moisture should be monitored if this approach is continued.",
        ],
    })

    # Scenario 4: Skip irrigation this cycle
    remaining_4 = base_inputs.water_storage_litres or 0
    daily = s3_full.daily_demand_litres
    scenarios.append({
        "scenario_name": "Skip This Irrigation Cycle",
        "description": "Do not irrigate now. Reassess tomorrow.",
        "estimated_water_use_litres": 0.0,
        "remaining_storage_litres": remaining_4,
        "days_remaining": (remaining_4 / daily) if daily else None,
        "recommendation": (
            "Do NOT skip unless soil moisture is adequate or rain is highly likely. "
            "Risk of crop water stress increases."
        ),
        "assumptions": [
            "Assumes crop can tolerate one cycle without irrigation.",
            "Only safe if current soil moisture is near field capacity.",
        ],
        "limitations": [
            "Skipping irrigation without adequate soil moisture risks yield loss.",
            "Not recommended during mid-season or critical growth stages.",
        ],
    })

    return scenarios
