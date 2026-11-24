"""Unit tests for the OpenStreetMap import helpers (gyms/osm.py). No database or network needed."""
from datetime import time

from django.test import SimpleTestCase

from gyms.osm import build_address, build_query, clean_website, parse_bbox, parse_element, parse_opening_hours


class ParseOpeningHoursTests(SimpleTestCase):
    def test_24_7(self):
        self.assertEqual(parse_opening_hours("24/7"), (True, None, None))

    def test_simple_range(self):
        self.assertEqual(parse_opening_hours("Mo-Fr 06:00-22:00; Sa-Su 08:00-20:00"),
                         (False, time(6, 0), time(22, 0)))

    def test_midnight_closing(self):
        self.assertEqual(parse_opening_hours("06:00-24:00"), (False, time(6, 0), time(23, 59)))

    def test_unknown_format(self):
        self.assertEqual(parse_opening_hours("by appointment"), (False, None, None))

    def test_missing(self):
        self.assertEqual(parse_opening_hours(None), (False, None, None))


class AddressAndWebsiteTests(SimpleTestCase):
    def test_full_address(self):
        tags = {"addr:housenumber": "12", "addr:street": "Main Street",
                "addr:suburb": "Rathmines", "addr:postcode": "D06 X1Y2"}
        self.assertEqual(build_address(tags), "12 Main Street, Rathmines, D06 X1Y2")

    def test_empty_address(self):
        self.assertEqual(build_address({}), "")

    def test_website_adds_scheme(self):
        self.assertEqual(clean_website({"website": "www.flyefit.ie"}), "https://www.flyefit.ie")

    def test_website_too_long_is_dropped(self):
        self.assertEqual(clean_website({"website": "https://example.com/" + "a" * 300}), "")


class ParseElementTests(SimpleTestCase):
    def test_node(self):
        element = {"type": "node", "id": 42, "lat": 53.35, "lon": -6.26,
                   "tags": {"name": "Test Gym", "opening_hours": "24/7"}}
        gym = parse_element(element)
        self.assertEqual(gym["osm_ref"], "node/42")
        self.assertEqual((gym["lat"], gym["lon"]), (53.35, -6.26))
        self.assertTrue(gym["is_24_hours_open"])

    def test_way_uses_center(self):
        element = {"type": "way", "id": 7, "center": {"lat": 53.3, "lon": -6.2},
                   "tags": {"name": "Outline Gym"}}
        self.assertEqual(parse_element(element)["lat"], 53.3)

    def test_unnamed_gym_is_skipped(self):
        self.assertIsNone(parse_element({"type": "node", "id": 1, "lat": 53.3, "lon": -6.2, "tags": {}}))


class QueryTests(SimpleTestCase):
    def test_bbox_parsing(self):
        self.assertEqual(parse_bbox("53.2,-6.55,53.64,-6.0"), (53.2, -6.55, 53.64, -6.0))

    def test_bbox_wrong_order_rejected(self):
        with self.assertRaises(ValueError):
            parse_bbox("53.64,-6.55,53.2,-6.0")

    def test_query_contains_bbox(self):
        self.assertIn('node["leisure"="fitness_centre"](53.2,-6.55,53.64,-6.0)',
                      build_query((53.2, -6.55, 53.64, -6.0)))