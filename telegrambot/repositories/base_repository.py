from collections import defaultdict
from urllib.parse import urljoin

from jsonapi_client.resourceobject import ResourceObject
from api_client.document import CustomDocument
from context import set_hmac

from api_client import AsyncClientSession


class JsonApiBaseRepository:
    def __init__(self, api_client: AsyncClientSession):
        self.api_client = api_client

    async def _fresh_document(self, url):
        # Mutable preferences must not use the session's ten-minute document cache.
        with set_hmac(True):
            _, payload, _ = await self.api_client.http_request_async("GET", url)
        return CustomDocument(self.api_client, payload, url, no_cache=True), payload

    async def _fresh_resources(self, resource_type):
        url = str(self.api_client._url_for_resource(resource_type))
        visited = set()
        while url:
            if url in visited:
                raise ValueError("Cyclic JSON:API pagination")
            visited.add(url)
            document, payload = await self._fresh_document(url)
            for resource in document.resources:
                yield resource
            next_link = payload.get("links", {}).get("next")
            if isinstance(next_link, dict):
                next_link = next_link.get("href")
            url = urljoin(url, next_link) if next_link else None

    @staticmethod
    def _separate_included_resources(document):
        if not getattr(document, "included", None):
            return {}

        grouped: dict[str, dict[str, ResourceObject]] = defaultdict(dict)
        for resource in document.included:
            grouped[resource.type][resource.id] = resource

        return dict(grouped)
