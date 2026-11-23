"""HubAuthClientConfig._heal_migration_history: it may only record 0004 when 0006
is already recorded, never on a database where this app's migrations haven't run.

Each test sets up the django_migrations rows it needs itself, so the tests don't
depend on migrations having run (0005 uses PostgreSQL-only SQL, so the SQLite
test database can't apply them; run with --nomigrations there).
"""

import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

APP = "hub_auth_client"
HEALED = "0004_apiendpointmapping"
MERGE = "0006_merge_20251210_1139"
BEFORE_HEALED = ["0001_initial", "0002_rls_models", "0003_azure_ad_config"]

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def only_these_rows():
    """Start every test with no hub_auth_client rows in django_migrations."""
    # Plain DDL: with --nomigrations the table doesn't exist, and Django's schema
    # editor can't create it inside SQLite's test transaction.
    if MigrationRecorder.Migration._meta.db_table not in connection.introspection.table_names():
        _execute(
            "CREATE TABLE django_migrations (id INTEGER PRIMARY KEY, app VARCHAR(255) NOT NULL,"
            " name VARCHAR(255) NOT NULL, applied TIMESTAMP NOT NULL)",
            [],
        )
    _execute("DELETE FROM django_migrations WHERE app = %s", [APP])


def _execute(sql: str, params: list) -> None:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def _record(*names: str) -> None:
    for name in names:
        _execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, CURRENT_TIMESTAMP)",
            [APP, name],
        )


def _recorded() -> list:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM django_migrations WHERE app = %s ORDER BY name", [APP]
        )
        return [row[0] for row in cursor.fetchall()]


def _heal() -> None:
    apps.get_app_config(APP)._heal_migration_history()


def test_does_not_record_0004_when_app_never_migrated():
    """An existing project adding this app: django_migrations exists, but none of
    our migrations are recorded. Recording 0004 here broke the next migrate."""
    _heal()
    assert _recorded() == []


def test_does_not_record_0004_when_merge_not_yet_applied():
    """Partway through migrating: migrate will apply 0004 itself."""
    _record(*BEFORE_HEALED)
    _heal()
    assert HEALED not in _recorded()


def test_records_0004_when_merge_applied_without_it():
    """The state the healing exists for: 0006 recorded, 0004 missing."""
    _record(*BEFORE_HEALED, MERGE)
    _heal()
    assert HEALED in _recorded()


def test_is_a_no_op_when_0004_already_recorded():
    _record(*BEFORE_HEALED, HEALED, MERGE)
    _heal()
    _heal()
    assert _recorded().count(HEALED) == 1
