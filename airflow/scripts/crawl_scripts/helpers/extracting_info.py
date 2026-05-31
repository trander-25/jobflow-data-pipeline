import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _safe_text(element) -> Optional[str]:
    try:
        return element.get_text(strip=True)
    except Exception:
        logger.warning(f"Failed to extract text from {element}.")
        return None

    # def _safe_text(element, context: str = "Unknown") -> Optional[str]:
    #     # 1. Chặn đứng giá trị None ngay từ đầu để điều tra nguồn gốc
    #     if element is None:
    #         try:
    #             # Thu thập thông tin về dòng code đã gọi hàm này ở file bên ngoài
    #             caller_frame = inspect.stack()[1]
    #             caller_file = caller_frame.filename     # Tên file gọi
    #             caller_line = caller_frame.lineno       # Dòng số mấy
    #             caller_code = caller_frame.code_context[0].strip() if caller_frame.code_context else "Không rõ"

    #             logger.warning(
    #                 f"\n[DEBUG NONE] PHÁT HIỆN BIẾN BỊ NONE TRUYỀN VÀO HÀM _SAFE_TEXT!\n"
    #                 f"  - Tại file: {caller_file}\n"
    #                 f"  - Dòng số: {caller_line}\n"
    #                 f"  - Đoạn code gọi lỗi: {caller_code}\n"
    #                 f"  - Ngữ cảnh được truyền: {context}\n"
    #             )
    #         except Exception as log_err:
    #             logger.warning(f"[DEBUG NONE] Không thể lấy thông tin caller: {log_err}")

    #         return None

    # 2. Nếu element hợp lệ, chạy bình thường
    try:
        return element.get_text(strip=True)
    except Exception as e:
        logger.warning(f"Failed to extract text từ element {element}. Lỗi: {e}")
        return None


def _safe_attr(element, attr: str) -> Optional[str]:
    try:
        return element[attr]
    except Exception:
        logger.warning(f"Failed to extract attribute '{attr}' from element.")
        return None


def _safe_find(parent, *args, **kwargs):
    try:
        return parent.find(*args, **kwargs)
    except Exception:
        logger.warning(f"Failed to find element with args: {args}, kwargs: {kwargs}.")
        return None
