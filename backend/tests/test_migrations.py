from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_head_includes_showcases_read_model() -> None:
    config = Config("backend/alembic.ini")
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == "20260603_0017"
    revisions = {rev.revision for rev in script.walk_revisions()}
    assert "20260602_0002" in revisions
    assert "20260602_0005" in revisions


def test_empty_foundation_migration_has_no_domain_tables() -> None:
    migration = Path("backend/migrations/versions/20260602_0001_empty_foundation.py").read_text()

    assert "create_table" not in migration
    assert "drop_table" not in migration
