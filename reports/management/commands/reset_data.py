# reports/management/commands/reset_data.py
# -----------------------------------------------------------------------------
# Delete data and reset primary-key sequences for selected apps.
# Works with PostgreSQL, MySQL, and SQLite.
#
# WHY USE THIS:
# - Postgres: TRUNCATE ... RESTART IDENTITY CASCADE
# - MySQL:    TRUNCATE with foreign_key_checks toggled
# - SQLite:   DELETE rows + reset sqlite_sequence + VACUUM
#
# SAFE DEFAULTS:
# - By default, only the "reports" app is wiped.
# - We NEVER touch core Django tables (django_migrations, sessions, etc.)
#   unless you add flags to include them.
#
# USAGE:
#   python manage.py reset_data --force
#   python manage.py reset_data --force --apps reports otherapp
#   python manage.py reset_data --force --all-apps
#   python manage.py reset_data --force --all-apps --include-auth
#   python manage.py reset_data --dry-run --all-apps
#
# NOTES:
# - For SQLite, if your PKs were created without AUTOINCREMENT, the next rowid
#   may still increase; we still clear sqlite_sequence when present and VACUUM.
# - Built-in alternative that wipes the whole DB: `python manage.py flush --noinput`
#   (flush also resets sequences across backends).
# -----------------------------------------------------------------------------

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection, transaction

CORE_APPS = {"contenttypes", "admin", "sessions", "messages", "staticfiles"}
DJANGO_CORE_TABLES = {
    "django_migrations",
    "django_content_type",
    "django_admin_log",
    "django_session",
}
AUTH_APPS = {"auth"}  # only included if --include-auth

def table_names_for_app(app_label: str):
    """Collect model tables + auto-created M2M through tables for an app."""
    tables = set()
    cfg = apps.get_app_config(app_label)
    for model in cfg.get_models():
        tables.add(model._meta.db_table)
        for m2m in model._meta.local_many_to_many:
            thr = m2m.remote_field.through
            if thr._meta.auto_created:
                tables.add(thr._meta.db_table)
    return tables

class Command(BaseCommand):
    help = "Delete rows and reset primary key sequences for selected apps (PostgreSQL/MySQL/SQLite)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Do not prompt for confirmation.")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--apps", nargs="+", default=["reports"], help="App labels to wipe (default: reports).")
        group.add_argument("--all-apps", action="store_true", help="Wipe ALL non-core INSTALLED_APPS.")
        parser.add_argument("--include-auth", action="store_true", help="Also wipe auth users/groups/permissions.")
        parser.add_argument("--dry-run", action="store_true", help="Print SQL that would run, then exit.")

    def handle(self, *args, **opts):
        vendor = connection.vendor  # 'postgresql' | 'mysql' | 'sqlite'
        # ------ resolve target apps ------
        if opts["all_apps"]:
            target_apps = {
                cfg.label
                for cfg in apps.get_app_configs()
                if not cfg.name.startswith("django.")
                and cfg.label not in CORE_APPS
            }
        else:
            target_apps = set(opts["apps"])

        if opts["include_auth"]:
            target_apps |= AUTH_APPS

        # ------ collect tables ------
        tables = set()
        for label in sorted(target_apps):
            try:
                tables |= table_names_for_app(label)
            except LookupError:
                self.stderr.write(self.style.WARNING(f"App '{label}' not in INSTALLED_APPS, skipping."))

        # Never touch these by default
        tables -= DJANGO_CORE_TABLES

        if not tables:
            self.stdout.write(self.style.WARNING("No tables resolved. Nothing to do."))
            return

        quoted = [connection.ops.quote_name(t) for t in sorted(tables)]
        self.stdout.write(self.style.NOTICE(f"Backend: {vendor}"))
        self.stdout.write(self.style.NOTICE(f"Apps: {', '.join(sorted(target_apps))}"))
        self.stdout.write(self.style.NOTICE(f"Tables: {', '.join(sorted(tables))}"))

        if not opts["force"]:
            self.stdout.write(self.style.WARNING("DANGER: This will DELETE ALL ROWS from the tables above and reset IDs."))
            if input("Type 'yes' to proceed: ").strip().lower() != "yes":
                self.stdout.write("Cancelled.")
                return

        if opts["dry_run"]:
            self._print_sql(vendor, quoted)
            return

        if vendor == "postgresql":
            self._run_postgres(quoted)
        elif vendor == "mysql":
            self._run_mysql(quoted)
        elif vendor == "sqlite":
            self._run_sqlite(tables)
        else:
            self.stderr.write(self.style.ERROR(f"Unsupported DB backend: {vendor}. Try `python manage.py flush --noinput`."))
            return

        self.stdout.write(self.style.SUCCESS("Done. Selected tables wiped and ID sequences reset."))

    # ---------- vendor implementations ----------

    def _run_postgres(self, quoted_tables):
        # Single TRUNCATE resets all identities and cascades FKs.
        sql = f"TRUNCATE TABLE {', '.join(quoted_tables)} RESTART IDENTITY CASCADE;"
        with transaction.atomic():
            with connection.cursor() as cur:
                self.stdout.write(self.style.HTTP_INFO("Executing PostgreSQL TRUNCATE ... RESTART IDENTITY CASCADE"))
                cur.execute(sql)

    def _run_mysql(self, quoted_tables):
        # Disable FK checks, TRUNCATE each (resets AUTO_INCREMENT), re-enable.
        with transaction.atomic():
            with connection.cursor() as cur:
                self.stdout.write(self.style.HTTP_INFO("SET foreign_key_checks=0"))
                cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
                for t in quoted_tables:
                    self.stdout.write(self.style.HTTP_INFO(f"TRUNCATE {t}"))
                    cur.execute(f"TRUNCATE TABLE {t};")
                self.stdout.write(self.style.HTTP_INFO("SET foreign_key_checks=1"))
                cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

    def _run_sqlite(self, tables):
        # SQLite has no TRUNCATE; we DELETE rows and reset sqlite_sequence.
        # Also toggle PRAGMA foreign_keys during mass deletes.
        with transaction.atomic():
            with connection.cursor() as cur:
                self.stdout.write(self.style.HTTP_INFO("PRAGMA foreign_keys=OFF"))
                cur.execute("PRAGMA foreign_keys = OFF;")
                for t in sorted(tables):
                    qt = connection.ops.quote_name(t)
                    self.stdout.write(self.style.HTTP_INFO(f"DELETE FROM {qt}"))
                    cur.execute(f"DELETE FROM {qt};")

                # Reset autoincrement counters when present
                try:
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
                    if cur.fetchone():
                        # Clear only for our tables
                        inlist = ", ".join(["?"] * len(tables))
                        self.stdout.write(self.style.HTTP_INFO("Resetting sqlite_sequence"))
                        cur.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({inlist});", list(tables))
                except Exception:
                    # If sqlite_sequence doesn't exist, it's fine.
                    pass

                self.stdout.write(self.style.HTTP_INFO("PRAGMA foreign_keys=ON"))
                cur.execute("PRAGMA foreign_keys = ON;")

                # Reclaim space & compact; also helps rowid reuse in some cases
                self.stdout.write(self.style.HTTP_INFO("VACUUM"))
                cur.execute("VACUUM;")

    def _print_sql(self, vendor, quoted_tables):
        if vendor == "postgresql":
            print(f"TRUNCATE TABLE {', '.join(quoted_tables)} RESTART IDENTITY CASCADE;")
        elif vendor == "mysql":
            print("SET FOREIGN_KEY_CHECKS = 0;")
            for t in quoted_tables:
                print(f"TRUNCATE TABLE {t};")
            print("SET FOREIGN_KEY_CHECKS = 1;")
        elif vendor == "sqlite":
            for t in quoted_tables:
                print(f"DELETE FROM {t};")
            print("-- if present:")
            print("DELETE FROM sqlite_sequence WHERE name IN (...);")
            print("VACUUM;")
        else:
            print("-- Unsupported backend for dry-run SQL.")
