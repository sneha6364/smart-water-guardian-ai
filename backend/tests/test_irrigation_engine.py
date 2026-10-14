"""Unit tests for the deterministic irrigation calculation engine."""
import pytest
from app.services.irrigation_engine import (
    IrrigationInputs,
    calculate_irrigation,
    calculate_water_budget,
    run_what_if_scenarios,
    FAO56_KC,
    IRRIGATION_EFFICIENCY,
)


class TestCropCoefficients:
    def test_known_crop_mid_stage(self):
        """Rice mid-season Kc should be 1.20 (FAO-56)."""
        result = calculate_irrigation(
            IrrigationInputs(crop_type="rice", growth_stage="mid", et0_mm_per_day=5.0, forecast_days=1)
        )
        assert result.kc_used == pytest.approx(1.20)

    def test_wheat_initial_stage(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="wheat", growth_stage="initial", et0_mm_per_day=4.0, forecast_days=1)
        )
        assert result.kc_used == pytest.approx(0.30)

    def test_unknown_crop_uses_default(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="unknown_crop_xyz", et0_mm_per_day=5.0, forecast_days=1)
        )
        assert result.kc_used is not None
        assert "unknown_crop_xyz" in " ".join(result.missing_inputs).lower() or \
               result.kc_used == FAO56_KC["default"]["mid"]

    def test_missing_growth_stage_uses_mid(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage=None, et0_mm_per_day=5.0, forecast_days=1)
        )
        assert result.kc_used == pytest.approx(FAO56_KC["maize"]["mid"])


class TestETcCalculation:
    def test_etc_equals_et0_times_kc(self):
        et0 = 6.0
        result = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage="mid", et0_mm_per_day=et0, forecast_days=1)
        )
        expected_kc = FAO56_KC["maize"]["mid"]
        assert result.etc_mm_per_day == pytest.approx(et0 * expected_kc, rel=1e-3)

    def test_fallback_et0_when_missing(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="wheat", growth_stage="mid", et0_mm_per_day=None, forecast_days=1)
        )
        assert result.etc_mm_per_day is not None  # fallback should be set
        assert any("fallback" in a.lower() or "unavailable" in a.lower() for a in result.assumptions)


class TestIrrigationVolume:
    def test_volume_litres_conversion(self):
        """1 mm over 1 ha = 10 000 litres."""
        # net_mm = etc_mm - 0 (no rain), so gross = net / efficiency
        result = calculate_irrigation(
            IrrigationInputs(
                crop_type="maize",
                growth_stage="mid",
                et0_mm_per_day=5.0,
                forecast_days=1,
                area_hectares=1.0,
                irrigation_method="drip",
                water_storage_litres=100_000,
            )
        )
        kc = FAO56_KC["maize"]["mid"]
        etc = 5.0 * kc
        net = etc  # no rain
        gross = net / IRRIGATION_EFFICIENCY["drip"]
        expected_litres = gross * 1.0 * 10_000
        assert result.gross_irrigation_litres == pytest.approx(expected_litres, rel=1e-3)

    def test_no_area_returns_none_litres(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="wheat", growth_stage="mid", et0_mm_per_day=5.0, area_hectares=None)
        )
        assert result.gross_irrigation_litres is None
        assert any("area" in m.lower() for m in result.missing_inputs)


class TestEffectiveRainfall:
    def test_high_probability_rain_reduces_requirement(self):
        no_rain = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage="mid", et0_mm_per_day=5.0, forecast_days=1,
                             forecast_rain_mm=0.0, rain_probability_pct=80)
        )
        with_rain = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage="mid", et0_mm_per_day=5.0, forecast_days=1,
                             forecast_rain_mm=10.0, rain_probability_pct=80)
        )
        assert (with_rain.net_irrigation_mm or 0) < (no_rain.net_irrigation_mm or 0)

    def test_low_probability_rain_ignored(self):
        low_prob = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage="mid", et0_mm_per_day=5.0, forecast_days=1,
                             forecast_rain_mm=20.0, rain_probability_pct=50)
        )
        no_rain = calculate_irrigation(
            IrrigationInputs(crop_type="maize", growth_stage="mid", et0_mm_per_day=5.0, forecast_days=1,
                             forecast_rain_mm=0.0, rain_probability_pct=0)
        )
        # Low-probability rain should not reduce requirement
        assert low_prob.net_irrigation_mm == pytest.approx(no_rain.net_irrigation_mm, rel=1e-3)


class TestWaterBudget:
    def test_days_remaining_calculation(self):
        storage = 50_000
        daily = 5_000
        result = calculate_water_budget(storage, daily)
        assert result["days_remaining"] == pytest.approx(10.0)

    def test_alert_when_less_than_3_days(self):
        result = calculate_water_budget(10_000, 5_000)
        assert result["alert"] is True

    def test_no_alert_when_sufficient(self):
        result = calculate_water_budget(100_000, 5_000)
        assert result["alert"] is False

    def test_zero_demand_returns_none(self):
        result = calculate_water_budget(100_000, 0)
        assert result["days_remaining"] is None


class TestStorageAlert:
    def test_shortage_alert_when_volume_exceeds_storage(self):
        result = calculate_irrigation(
            IrrigationInputs(
                crop_type="rice",
                growth_stage="mid",
                et0_mm_per_day=8.0,
                forecast_days=3,
                area_hectares=2.0,
                irrigation_method="flood",
                water_storage_litres=1_000,  # very low
            )
        )
        assert result.storage_alert is True
        assert "shortage" in result.recommended_action.lower() or \
               "insufficient" in result.recommended_action.lower() or \
               "water" in result.recommended_action.lower()


class TestScenarios:
    def test_four_scenarios_returned(self):
        inputs = IrrigationInputs(
            crop_type="wheat",
            growth_stage="mid",
            et0_mm_per_day=5.0,
            forecast_days=3,
            area_hectares=0.5,
            irrigation_method="drip",
            water_storage_litres=20_000,
            forecast_rain_mm=5.0,
            rain_probability_pct=60,
        )
        scenarios = run_what_if_scenarios(inputs)
        assert len(scenarios) == 4

    def test_irrigate_now_uses_more_water_than_skip(self):
        inputs = IrrigationInputs(
            crop_type="maize",
            growth_stage="mid",
            et0_mm_per_day=5.0,
            forecast_days=1,
            area_hectares=1.0,
            irrigation_method="drip",
            water_storage_litres=50_000,
        )
        scenarios = run_what_if_scenarios(inputs)
        irrigate_now = next(s for s in scenarios if s["scenario_name"] == "Irrigate Now")
        skip = next(s for s in scenarios if s["scenario_name"] == "Skip This Irrigation Cycle")
        assert (irrigate_now["estimated_water_use_litres"] or 0) > (skip["estimated_water_use_litres"] or 0)


class TestMissingInputs:
    def test_missing_et0_flagged(self):
        result = calculate_irrigation(IrrigationInputs(crop_type="wheat", growth_stage="mid"))
        assert any("ET0" in m or "et0" in m.lower() for m in result.missing_inputs)

    def test_missing_area_flagged(self):
        result = calculate_irrigation(
            IrrigationInputs(crop_type="wheat", growth_stage="mid", et0_mm_per_day=5.0)
        )
        assert any("area" in m.lower() for m in result.missing_inputs)
