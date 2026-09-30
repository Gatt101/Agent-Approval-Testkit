import pytest
from conftest import SECURE

from approval_testkit.adapter import ConfigError, load_adapter
from approval_testkit.config import load_config


def test_loads_example_config():
    cfg = load_config(SECURE)
    assert cfg.adapter == "verifier:SecurePaymentVerifier"
    assert cfg.request.args["amount"] == 100
    assert len(cfg.mutations) == 7


def test_pyproject_tool_section(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.approval-test]\nadapter = "m:A"\nmutations = ["replay"]\n'
        '[tool.approval-test.request]\nactor = "a"\ntool = "t"\ntarget = "x"\n'
    )
    cfg = load_config(tmp_path)
    assert [m.name for m in cfg.mutations] == ["replay"]


@pytest.mark.parametrize("toml, msg", [
    ('[request]\nactor="a"\ntool="t"\ntarget="x"\n', "adapter"),
    ('adapter = "m:A"\n', "[request]"),
    ('adapter = "m:A"\n[request]\nactor="a"\n', "tool, target"),
    ('adapter = "m:A"\nmutations=["nope"]\n[request]\nactor="a"\ntool="t"\ntarget="x"\n', "nope"),
    ("not = valid = toml", "invalid TOML"),
])
def test_config_errors(tmp_path, toml, msg):
    (tmp_path / "approval-test.toml").write_text(toml)
    with pytest.raises(ConfigError, match=msg.replace("[", r"\[")):
        load_config(tmp_path)


def test_missing_config(tmp_path):
    with pytest.raises(ConfigError, match="no approval-test.toml"):
        load_config(tmp_path)


@pytest.mark.parametrize("spec", ["no_colon", "verifier:Missing", "nonexistent_mod_xyz:A"])
def test_bad_adapter_spec(spec):
    with pytest.raises(ConfigError):
        load_adapter(spec, SECURE)
