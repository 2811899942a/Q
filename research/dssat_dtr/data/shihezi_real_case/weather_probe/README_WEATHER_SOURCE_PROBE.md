# Shihezi 2019-2020 weather-source probe

Experiment coordinate: 44.324444 N, 85.996389 E (Guo 2025).
Priority: real station hourly temperature > real station daily > reanalysis fallback.

| Source | Year/window | Status | Usable | Type | Detail |
|---|---|---:|---|---|---|
| NOAA Global Hourly 51356099999 | 2019 | 404 | False | station_hourly | rows=None; header=[]; content_type=text/html; charset=iso-8859-1 |
| NOAA Global Hourly 51356099999 | 2020 | 404 | False | station_hourly | rows=None; header=[]; content_type=text/html; charset=iso-8859-1 |
| NOAA GSOD 51356099999 | 2019 | 404 | False | station_daily | rows=None; header=[]; content_type=text/html; charset=iso-8859-1 |
| NOAA GSOD 51356099999 | 2020 | 404 | False | station_daily | rows=None; header=[]; content_type=text/html; charset=iso-8859-1 |
| NOAA Global Hourly directory search WMO 51356 | 2019 | 200 | False | station_hourly_index | hits=[] count=0 |
| NOAA Global Hourly directory search WMO 51356 | 2020 | 200 | False | station_hourly_index | hits=[] count=0 |
| Meteostat bulk hourly 51356 | 2019 | 404 | False | station_hourly | bytes=595; content_type=text/html; charset=iso-8859-1 |
| Meteostat bulk hourly 51356 | 2019 | 404 | False | station_hourly | bytes=595; content_type=text/html; charset=iso-8859-1 |
| Meteostat bulk hourly 51356 | 2020 | 404 | False | station_hourly | bytes=595; content_type=text/html; charset=iso-8859-1 |
| Meteostat bulk hourly 51356 | 2020 | 404 | False | station_hourly | bytes=595; content_type=text/html; charset=iso-8859-1 |
| Meteostat station metadata | all | 200 | True | station_metadata | bytes=806578; content_type=application/x-gzip; matches_51356=[]; nearby_count=2; nearby=[{'id': '51243', 'name': {'en': 'Karamay'}, 'country': 'CN', 'region': 'XJ', 'identifiers': {'national': None, 'wmo': '51243', 'icao': None}, 'location': {'latitude': 45.6, 'longitude': 84.85, 'elevation': 428}, 'timezone': 'Asia/Urumqi', 'inventory': {'model': {'start': '2021-01-01', 'end': '2026-03-19'}, 'hourly': {'start': None, 'end': None}, 'daily': {'start': '1956-01-01', 'end': '2027-12-30'}, 'monthly': {'start': 1956, 'end': 2022}, 'normals': {'start': 1961, 'end': 2020}}}, {'id': 'ZWWW0', 'name': {'en': 'Diwopu / Urumqi /  Dihua'}, 'country': 'CN', 'region': 'XJ', 'identifiers': {'national': None |
| Ogimet SYNOP 51356 | 2019-06 | 200 | False | station_synop | bytes=25; station_mentions=0; year_mentions=0; content_type=text/html |
| Ogimet SYNOP 51356 | 2019-07 | 200 | False | station_synop | bytes=25; station_mentions=0; year_mentions=0; content_type=text/html |
| Ogimet SYNOP 51356 | 2019-08 | 200 | True | station_synop | bytes=8894; station_mentions=2; year_mentions=0; content_type=text/html |
| Ogimet SYNOP 51356 | 2020-06 | 200 | False | station_synop | bytes=7698; station_mentions=0; year_mentions=0; content_type=text/html |
| Ogimet SYNOP 51356 | 2020-07 | 200 | True | station_synop | bytes=8894; station_mentions=2; year_mentions=1; content_type=text/html |
| Ogimet SYNOP 51356 | 2020-08 | 200 | False | station_synop | bytes=7698; station_mentions=0; year_mentions=0; content_type=text/html |
| NASA POWER hourly T2M | 2019 | 200 | True | reanalysis_fallback | bytes=70221; content_type=application/json; hourly_T2M_count=3696 |
| NASA POWER hourly T2M | 2020 | 200 | True | reanalysis_fallback | bytes=70200; content_type=application/json; hourly_T2M_count=3696 |

## Decision

At least one real/subdaily station-data route responded with usable data. Inspect saved raw files first and prefer this route for the formal M15 validation.
