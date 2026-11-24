"""
Import real gyms in Dublin from OpenStreetMap using the Overpass API.

Usage:
    python manage.py import_osm_gyms              # import / update gyms
    python manage.py import_osm_gyms --dry-run    # just show what would be imported
    python manage.py import_osm_gyms --bbox 53.30,-6.35,53.40,-6.15

Running it again is safe: gyms are matched on their OSM reference, so existing
ones are updated instead of duplicated, and fields OSM doesn't have (like
monthly_price and facilities) are left alone.
"""
import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gyms.models import Gym
from gyms.osm import DEFAULT_BBOX, OVERPASS_URLS, build_query, parse_bbox, parse_element

# Overpass asks clients to identify themselves
USER_AGENT = "DublinGymFinder/1.0 (TU Dublin student project; https://github.com/lekkszzy/gym-finder)"


class Command(BaseCommand):
    help = "Import gyms (leisure=fitness_centre) in Dublin from OpenStreetMap via the Overpass API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bbox",
            default=",".join(str(v) for v in DEFAULT_BBOX),
            help="Bounding box as south,west,north,east (default: County Dublin).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse the gyms but don't save anything.",
        )

    def handle(self, *args, **options):
        try:
            bbox = parse_bbox(options["bbox"])
        except ValueError as exc:
            raise CommandError(f"Invalid --bbox: {exc}")

        elements = self.fetch_elements(build_query(bbox))
        gyms = [gym for gym in (parse_element(e) for e in elements) if gym]
        skipped = len(elements) - len(gyms)
        self.stdout.write(f"Overpass returned {len(elements)} gyms ({skipped} skipped: no name or location).")

        if options["dry_run"]:
            for gym in gyms:
                self.stdout.write(f"  {gym['name']}  ({gym['lat']:.4f}, {gym['lon']:.4f})")
            self.stdout.write(self.style.WARNING("Dry run: nothing saved."))
            return

        created, updated = self.save_gyms(gyms)
        self.stdout.write(self.style.SUCCESS(f"Done: {created} gyms created, {updated} updated."))

    def fetch_elements(self, query):
        """POST the query to Overpass, trying each server until one answers."""
        last_error = None
        for url in OVERPASS_URLS:
            self.stdout.write(f"Querying {url} ...")
            try:
                response = requests.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": USER_AGENT},
                    timeout=90,
                )
                response.raise_for_status()
                return response.json().get("elements", [])
            except (requests.RequestException, ValueError) as exc:   # network error, HTTP error or bad JSON
                last_error = exc
                self.stderr.write(f"  Failed: {exc}")
        raise CommandError(f"All Overpass servers failed. Last error: {last_error}")

    @transaction.atomic   # all-or-nothing: a failure part-way leaves the database unchanged
    def save_gyms(self, gyms):
        created = updated = 0
        for gym in gyms:
            defaults = {
                "name": gym["name"],
                "location": Point(gym["lon"], gym["lat"], srid=4326),   # Point takes (x=lng, y=lat)
                "address": gym["address"],
                "website": gym["website"],
                "is_24_hours_open": gym["is_24_hours_open"],
                "opening_time": gym["opening_time"],
                "closing_time": gym["closing_time"],
            }
            _, was_created = Gym.objects.update_or_create(osm_ref=gym["osm_ref"], defaults=defaults)
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated