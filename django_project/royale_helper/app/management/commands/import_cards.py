"""Management command to import cards from the Clash Royale API."""

import os

import requests
from django.core.management.base import BaseCommand, CommandError

from app.models import Card

BASE_URL = "https://api.clashroyale.com/v1"


class Command(BaseCommand):
    """Import all cards from the official Clash Royale API into the database."""

    help = "Import all cards from the official Clash Royale API."

    def handle(self, *args, **options):
        """Execute the card import process."""
        token = os.getenv("CLASH_ROYALE_API_TOKEN")
        if not token:
            raise CommandError(
                "CLASH_ROYALE_API_TOKEN environment variable is not set. "
                "Add it to the .env file in the project root."
            )

        url = f"{BASE_URL}/cards"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        self.stdout.write(f"Fetching cards from {url}...")
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code != 200:
            raise CommandError(f"API request failed: {resp.status_code} {resp.text}")

        data = resp.json()
        items = data.get("items", [])
        self.stdout.write(f"Found {len(items)} cards")

        created = 0
        updated = 0

        for item in items:
            api_id = item.get("id")
            name = item.get("name")
            if api_id is None or not name:
                continue

            icon_urls = item.get("iconUrls") or {}
            defaults = {
                "name": name,
                "max_level": item.get("maxLevel"),
                "max_evolution_level": item.get("maxEvolutionLevel"),
                "max_star_level": item.get("maxStarLevel"),
                "icon_url": icon_urls.get("medium") or "",
            }

            _, created_flag = Card.objects.update_or_create(
                api_id=api_id, defaults=defaults
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. Created: {created}, updated: {updated}.")
        )
