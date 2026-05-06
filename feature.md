# Phân tích các Feature của hệ thống RAG (SmartDoc AI)

## Yêu cầu 1: Phân tích Expected Output cho từng Feature

### 1. Base RAG (Naive RAG)
*   **Dùng để làm gì:** Truy xuất các đoạn văn bản (chunks) tương đồng ngữ nghĩa nhất từ Vector DB và đưa vào LLM để sinh câu trả lời.
*   **Loại câu hỏi phù hợp nhất:** Tìm kiếm thông tin trực tiếp, fact-checking, khái niệm đơn lẻ (Factoid questions).
*   **Pipeline logic:** User Query -> Embed Query -> Vector Search (Top K) -> Prompt (Context + Query) -> LLM -> Output.
*   **Output mong đợi:** Câu trả lời đi thẳng vào vấn đề, bám sát các đoạn văn bản được retrieve.
*   **Khác gì Base RAG:** (Đây chính là baseline để so sánh).
*   **Khi nào phát huy hiệu quả:** Khi thông tin nằm gọn trong 1-2 đoạn văn và câu hỏi có ngữ nghĩa rõ ràng, tường minh.
*   **Ví dụ câu hỏi:** *"Kiến trúc Transformer được giới thiệu vào năm nào và bởi ai?"*
*   **Answer style mong đợi:** *"Kiến trúc Transformer được giới thiệu vào năm 2017 bởi đội ngũ nghiên cứu của Google."*

### 2. Self-RAG (Kèm Rerank, Query Rewriting, Multi-hop, Confidence)
*   **Dùng để làm gì:** Hệ thống có khả năng "tự nhận thức": tự viết lại câu hỏi cho rõ, tự đánh giá xem tài liệu tìm được có liên quan không, và tự chấm điểm độ tin cậy (Confidence Score) cho câu trả lời của chính mình.
*   **Loại câu hỏi phù hợp nhất:** Câu hỏi phức tạp, mơ hồ, sai chính tả, hoặc yêu cầu tổng hợp thông tin từ nhiều nơi (multi-hop).
*   **Pipeline logic:** Query -> Query Rewriting -> Retrieval -> Reranker/Filter -> LLM Generate -> LLM Self-Critique (Có hỗ trợ không? Có rác không?) -> Output + Score.
*   **Output mong đợi:** Câu trả lời cực kỳ chặt chẽ, kèm theo điểm tự tin. Nếu không tìm thấy thông tin, hệ thống sẽ chủ động từ chối trả lời thay vì hallucination (bịaa chuyện).
*   **Khác gì Base RAG:** Khắc phục triệt để tình trạng "đáp bừa" của Base RAG.
*   **Khi nào phát huy hiệu quả:** Kho dữ liệu có nhiều nhiễu (noise), user là người dùng cuối không rành kỹ thuật đặt câu hỏi (prompt).
*   **Ví dụ câu hỏi:** *"Mô hình R-CNN và Fast R-CNN khác nhau chỗ nào trong việc xử lý object detection?"* (Yêu cầu multi-hop tìm 2 thông tin rồi so sánh).
*   **Answer style mong đợi:** *"Dựa trên tài liệu, R-CNN trích xuất vùng ứng viên trước rồi mới chạy CNN, trong khi Fast R-CNN chạy toàn bộ ảnh qua CNN trước... **[Độ tin cậy: 95% - Thông tin được đối chiếu từ 2 nguồn tài liệu]**."*

### 3. Hybrid Search
*   **Dùng để làm gì:** Kết hợp tìm kiếm theo Từ khóa (Lexical/BM25) và Ngữ nghĩa (Vector/Dense) để không bỏ sót kết quả.
*   **Loại câu hỏi phù hợp nhất:** Câu hỏi chứa mã lỗi, tên biến, ID, thuật ngữ chuyên ngành đặc thù.
*   **Pipeline logic:** Query -> Song song (Vector Search + BM25 Search) -> Gộp kết quả (Reciprocal Rank Fusion - RRF) -> LLM.
*   **Output mong đợi:** Trả lời chính xác những chi tiết kỹ thuật nhỏ nhất.
*   **Khác gì Base RAG:** Base RAG thường "bỏ rơi" các chunk chứa chính xác mã lỗi (vì khoảng cách vector của mã lỗi đôi khi không sát với ngôn ngữ tự nhiên). Hybrid bắt được hết.
*   **Khi nào phát huy hiệu quả:** Xử lý tài liệu API, code, thông số kỹ thuật.
*   **Ví dụ câu hỏi:** *"Lỗi OOM Exception khi train ResNet50 với batch size 256 xử lý thế nào?"*
*   **Answer style mong đợi:** Bắt trúng phóc đoạn tài liệu có chữ `OOM Exception` và `batch size 256` để đưa ra cách giải quyết cụ thể.

### 4. Conversational RAG
*   **Dùng để làm gì:** Cho phép chat nhiều lượt (multi-turn), hệ thống "nhớ" được ngữ cảnh của các câu hỏi trước đó.
*   **Loại câu hỏi phù hợp nhất:** Câu hỏi follow-up, chứa đại từ thay thế ("nó", "phương pháp đó", "vậy còn cái này thì sao").
*   **Pipeline logic:** (Lịch sử Chat + Câu hỏi mới) -> LLM Contextualize (Viết lại thành câu hỏi độc lập) -> Retrieval -> Generate.
*   **Output mong đợi:** Dòng chảy hội thoại mượt mà tự nhiên.
*   **Khác gì Base RAG:** Base RAG coi mỗi lần chat là một user mới hoàn toàn.
*   **Khi nào phát huy hiệu quả:** Giao diện Chatbot (như ChatGPT), user cần drill-down (đào sâu) vấn đề.
*   **Ví dụ câu hỏi:** (Sau câu hỏi 1 về Transformer) *"Vậy cơ chế Attention trong nó giải quyết vấn đề gì?"*
*   **Answer style mong đợi:** *"Cơ chế Attention trong kiến trúc Transformer giải quyết vấn đề..."* (Hệ thống tự hiểu "nó" là Transformer).

### 5. Citation / Source Tracking
*   **Dùng để làm gì:** Cung cấp minh chứng (tên file, số trang, chunk text) cho từng luận điểm trong câu trả lời.
*   **Loại câu hỏi phù hợp nhất:** Câu hỏi cần tính minh bạch, kiểm toán (audit), nghiên cứu khoa học.
*   **Pipeline logic:** Retrieve chunks (chứa metadata) -> Ép LLM sinh output kèm marker `[1], [2]` map với chunks -> Output format.
*   **Output mong đợi:** Văn bản học thuật có footnote hoặc inline citation có thể click vào để xem bản gốc.
*   **Khác gì Base RAG:** Có bằng chứng rõ ràng, tăng độ trust của user.
*   **Khi nào phát huy hiệu quả:** Ứng dụng doanh nghiệp (Legal, Medical, Finance).
*   **Ví dụ câu hỏi:** *"Tỷ lệ sai số của mô hình YOLOv8 trên tập dữ liệu COCO là bao nhiêu?"*
*   **Answer style mong đợi:** *"Tỷ lệ sai số của mô hình là 4.2% [1]. Khi test ở điều kiện thiếu sáng, tỷ lệ tăng lên 8% [2]. \n\n**Nguồn:**\n[1] YOLO_v8_paper.pdf - Trang 5.\n[2] YOLO_v8_paper.pdf - Trang 12."*

### 6. GraphRAG
*   **Dùng để làm gì:** Xây dựng Knowledge Graph (thực thể & mối quan hệ) từ tài liệu để trả lời các câu hỏi mang tính toàn cục (Global).
*   **Loại câu hỏi phù hợp nhất:** Câu hỏi tóm tắt, bao quát bức tranh tổng thể, kết nối các điểm mù rải rác trong nhiều file.
*   **Pipeline logic:** Indexing: Dùng LLM trích xuất Entities/Relationships -> Xây Graph -> Tạo Communities. Query: Duyệt qua Graph/Communities -> Map Reduce tóm tắt -> Output.
*   **Output mong đợi:** Một bài luận tóm tắt cực kỳ đầy đủ, bao phủ nhiều khía cạnh của tài liệu.
*   **Khác gì Base RAG:** Base RAG giống "thầy bói xem voi", chỉ nhìn thấy vài đoạn text rời rạc. GraphRAG nhìn thấy "cả con voi" nhờ đồ thị tri thức.
*   **Khi nào phát huy hiệu quả:** Hỏi tóm tắt cuốn sách, tóm tắt sự kiện.
*   **Ví dụ câu hỏi:** *"Hãy tóm tắt sự phát triển của các công ty công nghệ lớn trong lĩnh vực Generative AI từ tài liệu này."*
*   **Answer style mong đợi:** Trình bày cấu trúc rõ ràng: Các công ty (OpenAI, Google, Meta) -> Mối liên hệ giữa họ (Đầu tư, Cạnh tranh mô hình mở/đóng) -> Tổng kết. Khác hẳn Base RAG chỉ trả về thông tin ngẫu nhiên của 1 công ty.
