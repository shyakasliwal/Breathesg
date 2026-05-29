from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ingest.models import DataSource, Organization, OrganizationMembership
from ingest.services import ingest_uploaded_file

User = get_user_model()
SAMPLE_DIR = Path(__file__).resolve().parents[4] / "sample_data"


class Command(BaseCommand):
    help = "Seed demo org, analyst user, and sample ingests"

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug="acme-industrial",
            defaults={"name": "ACME Industrial GmbH"},
        )

        user, created = User.objects.get_or_create(
            username="analyst@demo.local",
            defaults={"email": "analyst@demo.local", "first_name": "Jordan"},
        )
        if created:
            user.set_password("demo12345")
            user.save()

        OrganizationMembership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={"role": OrganizationMembership.Role.ANALYST},
        )

        sources = {
            "sap": "SAP MM movement export",
            "utility": "Utility portal CSV",
            "travel": "Concur-style travel export",
        }
        for source_type, display_name in sources.items():
            DataSource.objects.get_or_create(
                organization=org,
                source_type=source_type,
                defaults={"display_name": display_name},
            )

        for source_type in sources:
            path = SAMPLE_DIR / f"{source_type}_sample.csv"
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"Missing sample file: {path}"))
                continue
            source = DataSource.objects.get(organization=org, source_type=source_type)
            with path.open("rb") as handle:
                class _Upload:
                    name = path.name

                    def read(self_inner):
                        return handle.read()

                ingest_uploaded_file(
                    organization=org,
                    source=source,
                    uploaded_file=_Upload(),
                    user=user,
                )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Login: analyst@demo.local / demo12345")
