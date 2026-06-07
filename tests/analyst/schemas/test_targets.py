from analyst.schemas.targets import Target, TargetSet


def test_target_fields():
    t = Target(
        name="s1_to_s3_1.618",
        price=222.85,
        type="internal",
        theory_page=110,
        derivation="s1.end + 1.618 * size(s1)",
    )
    assert t.type == "internal"
    assert t.price == 222.85


def test_target_set_separates_confirmation_and_flow():
    inv = Target(name="s5_close", price=198.23, type="invalidation",
                 theory_page=22, derivation="s5.end")
    ts = TargetSet(
        confirmation_targets=(),
        fib_flow_targets=(),
        invalidation=inv,
    )
    assert ts.invalidation.price == 198.23
