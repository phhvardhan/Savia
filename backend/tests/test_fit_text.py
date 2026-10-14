from app.core.agent import fit_text


def _files(*bodies):
    n = len(bodies)
    return "\n\n".join(f"===== FILE {i} of {n}: f{i}.txt (txt) =====\n{b}" for i, b in enumerate(bodies, 1))


def test_short_text_untouched():
    assert fit_text("hello", 100) == "hello"


def test_single_file_keeps_head():
    assert fit_text("a" * 50, 10) == "a" * 10


def test_every_file_gets_a_share():
    text = _files("A" * 5000, "B" * 5000, "C" * 5000)
    out = fit_text(text, 3000)
    for i, letter in enumerate("ABC", 1):
        assert f"FILE {i} of 3" in out and letter * 500 in out
    assert len(out) <= 3000 + 3 * 60  # plus the "omitted" notes


def test_short_file_share_goes_to_others():
    text = _files("S" * 100, "L" * 9000)
    out = fit_text(text, 2000)
    assert "S" * 100 in out  # small file kept whole
    assert out.count("L") > 1000  # big file got the unused share
