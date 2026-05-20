"""Management command to clean and repopulate the database."""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from app.models import Card, Deck


class Command(BaseCommand):
    """Wipe the database and reimport all cards and decks."""

    help = "Clean the database and repopulate with fresh cards and decks."

    def handle(self, *args, **options):
        """Execute the database cleanup and repopulation."""
        self.stdout.write("Cleaning database...")

        deleted_decks, _ = Deck.objects.all().delete()
        self.stdout.write(f"Deleted {deleted_decks} decks.")

        deleted_cards, _ = Card.objects.all().delete()
        self.stdout.write(f"Deleted {deleted_cards} cards.")

        self.stdout.write("Database cleaned. Starting repopulation...")

        self.stdout.write("Importing cards...")
        call_command("import_cards")

        self.stdout.write("Importing decks from StatsRoyale (local file)...")
        call_command("import_statsroyale_decks", file=r"..\page.html")

        self.stdout.write(self.style.SUCCESS("Successfully repopulated the database."))
