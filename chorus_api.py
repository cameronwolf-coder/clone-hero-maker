"""
Chorus Encore API Client
Search and download charts from the Chorus Encore database.
"""

import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class SortType(Enum):
    """Available sort types."""
    NAME = "name"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"
    CHARTER = "charter"
    LENGTH = "length"
    MODIFIED_TIME = "modifiedTime"


class SortDirection(Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"


class Instrument(Enum):
    """Instruments for filtering."""
    GUITAR = "guitar"
    BASS = "bass"
    RHYTHM = "rhythm"
    DRUMS = "drums"
    KEYS = "keys"
    GHL_GUITAR = "ghlGuitar"
    GHL_BASS = "ghlBass"
    VOCALS = "vocals"


@dataclass
class Chart:
    """Represents a chart from Chorus Encore."""
    chartId: int
    songId: int
    groupId: int
    versionGroupId: int
    md5: str
    chartHash: str

    # Metadata
    name: str
    artist: str
    album: str = ""
    genre: str = ""
    year: str = ""
    charter: str = ""

    # Difficulty ratings
    diff_guitar: int = -1
    diff_bass: int = -1
    diff_rhythm: int = -1
    diff_drums: int = -1
    diff_drums_real: int = -1
    diff_keys: int = -1
    diff_guitarghl: int = -1
    diff_bassghl: int = -1
    diff_vocals: int = -1

    # Properties
    song_length: int = 0
    hasVideoBackground: bool = False
    modifiedTime: int = 0

    # Features
    hasSoloSections: bool = False
    hasForcedNotes: bool = False
    hasOpenNotes: bool = False
    hasTapNotes: bool = False
    hasLyrics: bool = False
    hasVocals: bool = False
    hasRollLanes: bool = False
    has2xKick: bool = False
    isModchart: bool = False

    def get_download_url(self, include_video: bool = True) -> str:
        """Get the CDN download URL for this chart."""
        base_url = "https://files.enchor.us"
        suffix = ".sng" if include_video else "_novideo.sng"
        return f"{base_url}/{self.md5}{suffix}"


@dataclass
class SearchParams:
    """Parameters for chart search."""
    query: str = "*"
    page: int = 0
    per_page: int = 25

    # Sorting
    sort_type: Optional[SortType] = None
    sort_direction: SortDirection = SortDirection.ASC

    # Filters
    instrument: Optional[Instrument] = None
    difficulty: Optional[int] = None
    drums_reviewed: bool = False

    # Advanced filters (for /search/advanced)
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[str] = None
    charter: Optional[str] = None

    # Numeric ranges
    length_min: Optional[int] = None
    length_max: Optional[int] = None
    intensity_min: Optional[int] = None
    intensity_max: Optional[int] = None

    # Boolean features
    has_solo_sections: Optional[bool] = None
    has_forced_notes: Optional[bool] = None
    has_open_notes: Optional[bool] = None
    has_tap_notes: Optional[bool] = None
    has_lyrics: Optional[bool] = None
    has_vocals: Optional[bool] = None
    has_video: Optional[bool] = None
    is_modchart: Optional[bool] = None


@dataclass
class SearchResult:
    """Result from chart search."""
    charts: List[Chart] = field(default_factory=list)
    page: int = 0
    total_found: int = 0
    search_time: float = 0.0


class ChorusAPI:
    """Client for the Chorus Encore API."""

    BASE_URL = "https://api.enchor.us"
    CDN_URL = "https://files.enchor.us"

    def __init__(self, source: str = "CloneHeroChartMaker"):
        """
        Initialize the API client.

        Args:
            source: Identifier for your application
        """
        self.source = source
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

    def search(self, params: SearchParams) -> SearchResult:
        """
        Search for charts using general search.

        Args:
            params: Search parameters

        Returns:
            SearchResult with matching charts
        """
        url = f"{self.BASE_URL}/search"

        payload = {
            "search": params.query,
            "per_page": params.per_page,
            "page": params.page,
            "source": self.source
        }

        # Add optional filters
        if params.instrument:
            payload["instrument"] = params.instrument.value

        if params.difficulty is not None:
            payload["difficulty"] = params.difficulty

        if params.drums_reviewed:
            payload["drumsReviewed"] = True

        # Add sorting
        if params.sort_type:
            payload["sort"] = {
                "type": params.sort_type.value,
                "direction": params.sort_direction.value
            }

        # Make request with retry logic
        max_retries = 10
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=30)
                response.raise_for_status()

                data = response.json()
                return self._parse_search_result(data)

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise Exception(f"Search failed after {max_retries} attempts: {e}")

    def advanced_search(self, params: SearchParams) -> SearchResult:
        """
        Search for charts using advanced search.

        Args:
            params: Search parameters with advanced filters

        Returns:
            SearchResult with matching charts
        """
        url = f"{self.BASE_URL}/search/advanced"

        payload = {
            "search": params.query,
            "per_page": params.per_page,
            "page": params.page,
            "source": self.source
        }

        # Basic filters
        if params.instrument:
            payload["instrument"] = params.instrument.value
        if params.difficulty is not None:
            payload["difficulty"] = params.difficulty
        if params.drums_reviewed:
            payload["drumsReviewed"] = True

        # Metadata filters
        if params.artist:
            payload["artist"] = params.artist
        if params.album:
            payload["album"] = params.album
        if params.genre:
            payload["genre"] = params.genre
        if params.year:
            payload["year"] = params.year
        if params.charter:
            payload["charter"] = params.charter

        # Numeric ranges
        if params.length_min is not None or params.length_max is not None:
            payload["length"] = {}
            if params.length_min:
                payload["length"]["min"] = params.length_min
            if params.length_max:
                payload["length"]["max"] = params.length_max

        if params.intensity_min is not None or params.intensity_max is not None:
            payload["intensity"] = {}
            if params.intensity_min:
                payload["intensity"]["min"] = params.intensity_min
            if params.intensity_max:
                payload["intensity"]["max"] = params.intensity_max

        # Boolean features
        if params.has_solo_sections is not None:
            payload["hasSoloSections"] = params.has_solo_sections
        if params.has_forced_notes is not None:
            payload["hasForcedNotes"] = params.has_forced_notes
        if params.has_open_notes is not None:
            payload["hasOpenNotes"] = params.has_open_notes
        if params.has_tap_notes is not None:
            payload["hasTapNotes"] = params.has_tap_notes
        if params.has_lyrics is not None:
            payload["hasLyrics"] = params.has_lyrics
        if params.has_vocals is not None:
            payload["hasVocals"] = params.has_vocals
        if params.has_video is not None:
            payload["hasVideoBackground"] = params.has_video
        if params.is_modchart is not None:
            payload["isModchart"] = params.is_modchart

        # Sorting
        if params.sort_type:
            payload["sort"] = {
                "type": params.sort_type.value,
                "direction": params.sort_direction.value
            }

        # Make request with retry logic
        max_retries = 10
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=30)
                response.raise_for_status()

                data = response.json()
                return self._parse_search_result(data)

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"Advanced search failed after {max_retries} attempts: {e}")

    def _parse_search_result(self, data: Dict[str, Any]) -> SearchResult:
        """Parse API response into SearchResult."""
        charts = []

        for chart_data in data.get("data", []):
            chart = Chart(
                chartId=chart_data.get("chartId", 0),
                songId=chart_data.get("songId", 0),
                groupId=chart_data.get("groupId", 0),
                versionGroupId=chart_data.get("versionGroupId", 0),
                md5=chart_data.get("md5", ""),
                chartHash=chart_data.get("chartHash", ""),
                name=chart_data.get("name", ""),
                artist=chart_data.get("artist", ""),
                album=chart_data.get("album", ""),
                genre=chart_data.get("genre", ""),
                year=chart_data.get("year", ""),
                charter=chart_data.get("charter", ""),
                diff_guitar=chart_data.get("diff_guitar", -1),
                diff_bass=chart_data.get("diff_bass", -1),
                diff_rhythm=chart_data.get("diff_rhythm", -1),
                diff_drums=chart_data.get("diff_drums", -1),
                diff_drums_real=chart_data.get("diff_drums_real", -1),
                diff_keys=chart_data.get("diff_keys", -1),
                diff_guitarghl=chart_data.get("diff_guitarghl", -1),
                diff_bassghl=chart_data.get("diff_bassghl", -1),
                diff_vocals=chart_data.get("diff_vocals", -1),
                song_length=chart_data.get("song_length", 0),
                hasVideoBackground=chart_data.get("hasVideoBackground", False),
                modifiedTime=chart_data.get("modifiedTime", 0),
                hasSoloSections=chart_data.get("hasSoloSections", False),
                hasForcedNotes=chart_data.get("hasForcedNotes", False),
                hasOpenNotes=chart_data.get("hasOpenNotes", False),
                hasTapNotes=chart_data.get("hasTapNotes", False),
                hasLyrics=chart_data.get("hasLyrics", False),
                hasVocals=chart_data.get("hasVocals", False),
                hasRollLanes=chart_data.get("hasRollLanes", False),
                has2xKick=chart_data.get("has2xKick", False),
                isModchart=chart_data.get("isModchart", False),
            )
            charts.append(chart)

        return SearchResult(
            charts=charts,
            page=data.get("page", 0),
            total_found=data.get("found", 0),
            search_time=data.get("searchTime", 0.0)
        )

    def download_chart(
        self,
        chart: Chart,
        output_path: str,
        include_video: bool = True,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Download a chart file.

        Args:
            chart: Chart to download
            output_path: Where to save the file
            include_video: Whether to include video background
            progress_callback: Function to call with progress updates (percent: float)

        Returns:
            True if successful, False otherwise
        """
        url = chart.get_download_url(include_video)

        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(percent)

            return True

        except Exception as e:
            print(f"Download failed: {e}")
            return False


if __name__ == "__main__":
    # Test the API client
    print("Chorus API Client Test")
    print("=" * 60)

    api = ChorusAPI()

    # Test search
    print("\nSearching for 'Through the Fire and Flames'...")
    params = SearchParams(
        query="Through the Fire and Flames",
        per_page=5
    )

    result = api.search(params)
    print(f"Found {result.total_found} results ({result.search_time:.2f}s)")

    for chart in result.charts[:5]:
        print(f"\n  {chart.name} - {chart.artist}")
        print(f"  Charter: {chart.charter}")
        print(f"  Difficulties: G:{chart.diff_guitar} B:{chart.diff_bass} D:{chart.diff_drums}")
        print(f"  MD5: {chart.md5}")
        print(f"  Download: {chart.get_download_url(False)}")

    # Test advanced search
    print("\n" + "=" * 60)
    print("\nAdvanced search for expert guitar charts...")
    adv_params = SearchParams(
        query="*",
        instrument=Instrument.GUITAR,
        difficulty=6,  # Expert
        per_page=5
    )

    adv_result = api.advanced_search(adv_params)
    print(f"Found {adv_result.total_found} expert guitar charts")

    for chart in adv_result.charts[:3]:
        print(f"\n  {chart.name} - {chart.artist}")
        print(f"  Expert Guitar: {chart.diff_guitar}")
