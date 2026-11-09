import re

from django.urls import reverse

from api import urls as api_urls
from api.views import _openapi_document

from .base import MagpieApiTestCase

HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def _route_to_spec_path(pattern):
    """Map a route regex such as ``^groups/(?P<group_id>...)/?$`` to its spec path."""
    path = pattern.removeprefix("^").removesuffix("$").removesuffix("/?")
    path = re.sub(r"\(\?P<(\w+)>[^)]*\)", r"{\1}", path)
    return f"/api/v1/{path}/"


class OpenApiDocumentTests(MagpieApiTestCase):
    """The served OpenAPI document must describe the API that actually exists."""

    def test_schema_endpoint_serves_document_with_this_server(self):
        """Clients build their tools from /api/schema/, so it must be the full spec."""
        response = self.client.get(reverse("schema"))

        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertEqual(document["info"]["title"], "Magpie API")
        self.assertEqual(document["servers"], [{"url": "http://testserver"}])
        search = document["paths"]["/api/v1/search/{media_type}/"]["get"]
        self.assertIn("search", [p["name"] for p in search["parameters"]])
        add_to_group = document["paths"]["/api/v1/groups/{group_id}/items/"]["post"]
        self.assertIn("requestBody", add_to_group)

    def test_every_route_and_method_is_documented(self):
        """A route or method missing from the spec is invisible to API clients."""
        documented = {
            (path, method)
            for path, operations in _openapi_document()["paths"].items()
            for method in operations
            if method in HTTP_METHODS
        }
        routed = {
            (_route_to_spec_path(route.pattern.regex.pattern), method)
            for route in api_urls.urlpatterns
            for method in HTTP_METHODS
            if hasattr(route.callback.view_class, method)
        }

        self.assertEqual(sorted(routed - documented), [])
        self.assertEqual(sorted(documented - routed), [])
