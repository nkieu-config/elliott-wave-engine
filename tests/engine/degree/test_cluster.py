from __future__ import annotations

from engine.degree.cluster import gann_band_fits


def test_gann_band_fits_within_band() -> None:
    assert gann_band_fits(candidate=15.0, anchor=10.0) is True


def test_gann_band_fits_at_lower_boundary() -> None:
    assert gann_band_fits(candidate=10.0, anchor=30.0) is True


def test_gann_band_fits_at_upper_boundary() -> None:
    assert gann_band_fits(candidate=30.0, anchor=10.0) is True


def test_gann_band_fits_below_lower_boundary() -> None:
    assert gann_band_fits(candidate=3.0, anchor=10.0) is False


def test_gann_band_fits_above_upper_boundary() -> None:
    assert gann_band_fits(candidate=40.0, anchor=10.0) is False


def test_gann_band_fits_degenerate_anchor() -> None:
    assert gann_band_fits(candidate=10.0, anchor=0.0) is True
