from io import BytesIO

import requests
from PIL import Image


class ImageDownloader:
    """Download and optimize company logo images for storage."""

    def __init__(self, timeout: int = 20):
        """Create a requests session configured for image downloads."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/*",
            }
        )
        self.timeout = timeout

    def process_urls(self, urls: list[str]) -> dict:
        """Download and optimize multiple image URLs.

        Args:
            urls: Image URLs to process.

        Returns:
            A mapping from URL to optimized image bytes, or None for failed URLs.
        """
        results = {}

        for url in urls:
            try:
                results[url] = self._process_single(url)
            except Exception as e:
                results[url] = None
                print(f"[FAIL] {url} -> {e}")

        return results

    def _process_single(self, url: str) -> bytes:
        """Download one image and return optimized PNG bytes."""
        content = self._download(url)
        return self._optimize_image(content)

    def _download(self, url: str) -> bytes:
        """Download raw image bytes from a URL."""
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.content

    def _optimize_image(self, content: bytes) -> bytes:
        """Convert image bytes to an optimized PNG payload."""
        img = Image.open(BytesIO(content))

        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)

        return buffer.getvalue()
