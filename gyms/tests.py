from django.contrib.auth.models import User
from django.contrib.gis.geos import LineString, Point, Polygon
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Area, Gym, Route

# Structure adapted from my Lab 5 proximity tests (cities_api/test_proximity.py)

NEAREST_URL = "/api/gyms/nearest/"
RADIUS_URL = "/api/gyms/within-radius/"
GYMS_URL = "/api/gyms/"

# Search point: O'Connell Street, Dublin city centre
CITY_CENTRE = {"lat": 53.3498, "lng": -6.2603}

# name, lng, lat (real gyms from the sample data)
TEST_GYMS = [
    ("FlyeFit Jervis", -6.2660, 53.3483),
    ("Trinity Sport Centre", -6.2546, 53.3438),
    ("Swan Leisure Rathmines", -6.2650, 53.3225),
    ("DCU Sport", -6.2564, 53.3861),
    ("Energie Fitness Balbriggan", -6.1995, 53.6035),
]


class GymAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        for name, lng, lat in TEST_GYMS:
            Gym.objects.create(name=name, location=Point(lng, lat, srid=4326))

        # Same rectangle as the "City Centre" area in the sample data
        cls.area = Area.objects.create(
            name="City Centre",
            boundary=Polygon(
                ((-6.300, 53.336), (-6.245, 53.336), (-6.245, 53.356),
                 (-6.300, 53.356), (-6.300, 53.336)),
                srid=4326,
            ),
        )

        cls.owner = User.objects.create_user(username="owner", password="testpass123")
        cls.other_user = User.objects.create_user(username="other", password="testpass123")
        cls.admin = User.objects.create_user(username="admin", password="testpass123", is_staff=True)

        # Same line as the "Rathmines to City Centre" route in the sample data
        cls.route = Route.objects.create(
            name="Rathmines to City Centre",
            path=LineString(
                (-6.2650, 53.3220), (-6.2600, 53.3290), (-6.2590, 53.3360),
                (-6.2580, 53.3440), (-6.2600, 53.3470),
                srid=4326,
            ),
            owner=cls.owner,
        )

    def names(self, response):
        """Gym names from a GeoJSON response."""
        return [f["properties"]["name"] for f in response.data["gyms"]["features"]]

    # ----- Nearest -----
    def test_nearest_returns_closest_first(self):
        response = self.client.get(NEAREST_URL, {**CITY_CENTRE, "limit": 3})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_found"], 3)
        self.assertEqual(self.names(response), ["FlyeFit Jervis", "Trinity Sport Centre", "Swan Leisure Rathmines"])

    def test_nearest_invalid_limit_rejected(self):
        for limit in (0, 51, "abc"):
            response = self.client.get(NEAREST_URL, {**CITY_CENTRE, "limit": limit})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=f"limit={limit!r}")

    # ----- Radius -----
    def test_radius_5km_excludes_balbriggan(self):
        response = self.client.get(RADIUS_URL, {**CITY_CENTRE, "radius_km": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_found"], 4)
        self.assertNotIn("Energie Fitness Balbriggan", self.names(response))

    def test_radius_40km_includes_balbriggan(self):
        response = self.client.get(RADIUS_URL, {**CITY_CENTRE, "radius_km": 40})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_found"], 5)
        self.assertIn("Energie Fitness Balbriggan", self.names(response))

    def test_invalid_radius_rejected(self):
        for radius in (0, -5, 51, "abc"):
            response = self.client.get(RADIUS_URL, {**CITY_CENTRE, "radius_km": radius})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=f"radius_km={radius!r}")

    # ----- Area (containment) -----
    def test_area_returns_only_gyms_inside(self):
        response = self.client.get(f"/api/areas/{self.area.id}/gyms/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(self.names(response)), ["FlyeFit Jervis", "Trinity Sport Centre"])

    def test_missing_area_returns_404(self):
        response = self.client.get("/api/areas/999/gyms/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----- Route (buffer) -----
    def test_route_500m_buffer(self):
        response = self.client.get(f"/api/routes/{self.route.id}/gyms/", {"buffer_m": 500})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = self.names(response)
        self.assertEqual(sorted(names), ["FlyeFit Jervis", "Swan Leisure Rathmines", "Trinity Sport Centre"])
        self.assertNotIn("DCU Sport", names)

    def test_route_smaller_buffer_finds_fewer(self):
        response = self.client.get(f"/api/routes/{self.route.id}/gyms/", {"buffer_m": 100})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.names(response), ["Swan Leisure Rathmines"])

    def test_invalid_buffer_rejected(self):
        for buffer_m in (0, 5001, "abc"):
            response = self.client.get(f"/api/routes/{self.route.id}/gyms/", {"buffer_m": buffer_m})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=f"buffer_m={buffer_m!r}")

    # ----- Invalid / missing coordinates -----
    def test_location_outside_ireland_rejected(self):
        for params in ({"lat": 40, "lng": -6.26}, {"lat": 53.35, "lng": 2.35}):
            response = self.client.get(NEAREST_URL, params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)

    def test_missing_or_non_numeric_coordinates_rejected(self):
        for params in ({}, {"lat": 53.35}, {"lng": -6.26}, {"lat": "abc", "lng": -6.26}):
            for url in (NEAREST_URL, RADIUS_URL):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=f"{url} {params}")

    # ----- Methods -----
    def test_post_not_allowed_on_search(self):
        # Logged in, so the permission check passes and the method check (GET only) is tested
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(NEAREST_URL, CITY_CENTRE, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ----- Permissions -----
    def test_anyone_can_view_gyms(self):
        response = self.client.get(GYMS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 5)

    def test_logged_out_user_cannot_create_gym(self):
        response = self.client.post(GYMS_URL, {"name": "Fake Gym"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_normal_user_cannot_delete_gym(self):
        gym = Gym.objects.get(name="DCU Sport")
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/gyms/{gym.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_gym(self):
        gym = Gym.objects.get(name="DCU Sport")
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(f"/api/gyms/{gym.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Gym.objects.filter(id=gym.id).exists())

    def test_other_user_cannot_edit_route(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(f"/api/routes/{self.route.id}/", {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_edit_route(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(f"/api/routes/{self.route.id}/", {"name": "My Commute"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db()
        self.assertEqual(self.route.name, "My Commute")