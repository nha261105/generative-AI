import json
import uuid
from datetime import datetime
from pathlib import Path

# ─── Đường dẫn file ────────────────────────────────────────────────────────────
HISTORY_FILE = Path(__file__).parent / "chat_history.json"


# ─── Helpers ───────────────────────────────────────────────────────────────────
def _now() -> str:
    """Trả về thời gian hiện tại dạng ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


def _generate_id() -> str:
    """Tạo ID duy nhất cho conversation dạng: conv_20260406_103000_a1b2."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:4]
    return f"conv_{timestamp}_{short_uuid}"


def _auto_title(question: str, max_length: int = 40) -> str:
    """
    Tự động đặt tiêu đề conversation từ câu hỏi đầu tiên.
    Cắt bớt nếu quá dài và thêm dấu "...".
    """
    title = question.strip()
    if len(title) > max_length:
        title = title[:max_length].rstrip() + "..."
    return title


def _load_raw() -> dict:
    """Đọc raw JSON từ file, trả về dict rỗng nếu file chưa tồn tại hoặc lỗi."""
    if not HISTORY_FILE.exists():
        return {"conversations": []}
    try:
        content = HISTORY_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return {"conversations": []}
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return {"conversations": []}


def _save_raw(data: dict) -> None:
    """Ghi dict xuống file JSON."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        print(f"[history] Không thể ghi file: {e}")


# ─── Public API ────────────────────────────────────────────────────────────────
def load_conversations() -> list[dict]:
    """
    Đọc toàn bộ danh sách conversations, sắp xếp mới nhất lên đầu.

    Returns:
        list[dict]: danh sách conversation, mỗi phần tử gồm:
            - id         (str)
            - title      (str)
            - doc_name   (str)
            - created_at (str)
            - messages   (list[dict])
    """
    data = _load_raw()
    conversations = data.get("conversations", [])
    # Sắp xếp mới nhất lên đầu
    return sorted(conversations, key=lambda c: c["created_at"], reverse=True)


def get_conversation(conv_id: str) -> dict | None:
    """
    Lấy một conversation theo ID.

    Args:
        conv_id: ID của conversation cần lấy.

    Returns:
        dict conversation nếu tìm thấy, None nếu không có.
    """
    data = _load_raw()
    for conv in data["conversations"]:
        if conv["id"] == conv_id:
            return conv
    return None


def new_conversation(doc_name: str = "") -> dict:
    """
    Tạo một conversation mới (chưa có tin nhắn).
    Lưu xuống file và trả về conversation vừa tạo.

    Args:
        doc_name: tên file PDF đang được hỏi (nếu có).

    Returns:
        dict: conversation mới với id, title, doc_name, created_at, messages=[].
    """
    conv = {
        "id":         _generate_id(),
        "title":      "Đoạn chat mới",
        "doc_name":   doc_name,
        "created_at": _now(),
        "messages":   [],
    }
    data = _load_raw()
    data["conversations"].append(conv)
    _save_raw(data)
    return conv


def add_message(
    conv_id: str,
    question: str,
    answer: str,
    source: str = "",
) -> dict | None:
    """
    Thêm một tin nhắn vào conversation, tự đặt title từ câu hỏi đầu tiên.

    Args:
        conv_id:  ID của conversation đang hoạt động.
        question: câu hỏi của người dùng.
        answer:   câu trả lời từ AI.
        source:   nguồn trích dẫn (ví dụ: "trang 5, chương 2").

    Returns:
        dict: conversation sau khi cập nhật, None nếu không tìm thấy conv_id.
    """
    data = _load_raw()

    for conv in data["conversations"]:
        if conv["id"] != conv_id:
            continue

        # Tự đặt title từ câu hỏi đầu tiên
        if not conv["messages"]:
            conv["title"] = _auto_title(question)

        conv["messages"].append({
            "question":  question,
            "answer":    answer,
            "source":    source,
            "timestamp": _now(),
        })

        _save_raw(data)
        return conv

    return None  # conv_id không tồn tại


def delete_conversation(conv_id: str) -> bool:
    """
    Xóa một conversation theo ID.

    Args:
        conv_id: ID của conversation cần xóa.

    Returns:
        True nếu xóa thành công, False nếu không tìm thấy.
    """
    data = _load_raw()
    original_len = len(data["conversations"])
    data["conversations"] = [
        c for c in data["conversations"] if c["id"] != conv_id
    ]

    if len(data["conversations"]) == original_len:
        return False  # Không tìm thấy

    _save_raw(data)
    return True


def clear_all() -> None:
    """Xóa toàn bộ lịch sử chat."""
    _save_raw({"conversations": []})