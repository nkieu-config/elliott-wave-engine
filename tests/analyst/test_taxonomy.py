from analyst.taxonomy import humanize_family_codes


def test_humanize_family_codes_translates_every_family():
    assert humanize_family_codes("Incomplete 5W_SIDEWAY (needs 5 legs)") == (
        "Incomplete 5-Wave Sideway (needs 5 legs)"
    )
    assert "3-Wave" in humanize_family_codes("3W has too few legs")


def test_humanize_family_codes_link_se_not_mangled_by_link_s():
    assert humanize_family_codes("LINK_SE") == "Link-Wave (+SE)"
    assert humanize_family_codes("LINK_S") == "Link-Wave (+S)"
