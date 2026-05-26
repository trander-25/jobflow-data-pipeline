import requests
from io import BytesIO
from PIL import Image


class ImageDownloader:
    def __init__(self, timeout: int = 20):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/*",
            }
        )
        self.timeout = timeout

    def process_urls(self, urls: list[str]) -> dict:
        results = {}

        for url in urls:
            try:
                results[url] = self._process_single(url)
            except Exception as e:
                results[url] = None
                print(f"[FAIL] {url} -> {e}")

        return results

    def _process_single(self, url: str) -> bytes:
        """
        Final output: raw bytes of the image (Optimized PNG)
        """
        content = self._download(url)
        
        # Chỉ nén và chuyển thành PNG, không xóa nền
        return self._optimize_image(content)

    def _download(self, url: str) -> bytes:
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.content

    def _optimize_image(self, content: bytes) -> bytes:
        # Mở ảnh bằng Pillow
        img = Image.open(BytesIO(content))
        
        # Lưu lại dưới dạng PNG đã tối ưu dung lượng
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        
        return buffer.getvalue()