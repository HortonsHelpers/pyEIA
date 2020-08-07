import asyncio
import pandas as pd

from typing import List

from .base import BaseQuery, yield_chunks


class Series(BaseQuery):
    """Retrieve one or more series from the series API.

    Example:

        .. code-block::python

            from eia.api import Series
            
            S = Series(
                "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A", 
                "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
            )
            S.to_dataframe()
    """

    endpoint = "series"

    def __post_init__(self, *series_ids: str):
        # Create a structure to send batch requests
        # The EIA API supports up to 100 series in a single request
        self.series_ids = [";".join(chunk) for chunk in yield_chunks(series_ids, 100)]

    async def _get_data(self):
        """Send a request for each batch of series ids and await their results.
        """
        for series_ids in self.series_ids:
            response = await self._post(data={"series_id": series_ids})
            yield response

    async def parse(self) -> List[dict]:
        """
        Collect one dict per series and drop request metadata.
        """
        data_generator = self._get_data()
        output = []
        async for group in data_generator:
            for series in group.get("series", []):
                output.append(series)
        return output

    def to_dataframe(self, include_metadata: bool = True) -> pd.DataFrame:
        """Return the input series as a dataframe.
        """
        # Get all our data first with async
        # Note that all our pandas work will tax CPU so we wouldn't expect any
        # performance gains from doing the data parsing as a callback
        records = asyncio.run(self.parse())
        data = []
        for series in records:
            df = pd.DataFrame(series.pop("data"), columns=["period", "value"])
            if include_metadata:
                df = df.assign(**series)
            data.append(df)
        return pd.concat(data, ignore_index=True)

    def to_dict(self) -> List[dict]:
        """Return the input series as a list of dictionaries.
        """
        return asyncio.run(self.parse())
