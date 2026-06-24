from typer.testing import CliRunner

from mountain_retreat_x1.cli import app

runner = CliRunner()


def test_help_works() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Mountain Retreat X1" in result.output


def test_validate_default_config() -> None:
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert "Configuration validation completed" in result.output


def test_validate_rejects_invalid_config_dir() -> None:
    result = runner.invoke(app, ["validate", "--config-dir", "does-not-exist"])

    assert result.exit_code != 0


def test_generate_commands_are_registered() -> None:
    for command in ("all", "pdf", "excel", "drawings"):
        result = runner.invoke(app, ["generate", command])

        assert result.exit_code == 0
        assert "placeholder completed" in result.output


def test_clean_placeholder() -> None:
    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 0
    assert "Clean placeholder completed" in result.output
