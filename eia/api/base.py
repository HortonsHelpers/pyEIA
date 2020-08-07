"""
Core documentation for the EIA API can be found at: https://www.eia.gov/opendata/commands.php
"""
import abc
import httpx
import itertools

from typing import Iterator, List
from urllib.parse import urljoin

from eia import settings


def yield_chunks(iterator: Iterator, n: int) -> Iterator:
    """Chunk an iterable into iterables of at most size n.
    """
    iterator = iter(iterator)  # Convert whatever we have into an iterator
    for edge in iterator:  # Exit when iterator is exhausted
        boundary = itertools.islice(iterator, 0, n - 1)
        yield list(itertools.chain([edge], boundary))


class BaseQuery(abc.ABC):

    ROOT = "https://api.eia.gov"

    def __init__(self, apikey: str = None):
        self._configure(apikey)

    def _configure(self, apikey: str):
        """Set instance API key, default parameters and base url.
        """
        # Set authentication
        self.apikey = apikey or settings.APIKEY
        assert self.apikey, "Missing required apikey."

        # Set default API parameters
        self._params = {"api_key": self.apikey, "out": "json"}

        # Set the default endpoint
        endpoint = self.endpoint if self.endpoint.endswith("/") else f"{self.endpoint}/"
        self.url = urljoin(self.ROOT, endpoint)

    async def _get(self, data: dict = {}) -> dict:
        """Asynchronously send a GET request and retrieve a python dict.
        """
        params = {**self._params, **data}
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url, params=params)
        return response.json()

    async def _post(self, data: dict = {}) -> dict:
        """Asynchronously send a POST request and retrieve a python dict.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url, params=self._params, data=data)
        return response.json()

    @abc.abstractmethod
    def to_dict(self):
        raise NotImplementedError

    @abc.abstractmethod
    def to_dataframe(self):
        raise NotImplementedError
