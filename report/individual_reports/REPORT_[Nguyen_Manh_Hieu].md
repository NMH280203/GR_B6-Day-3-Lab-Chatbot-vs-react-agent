# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Mạnh Hiếu
- **Student ID**: 2A202600887
- **Date**: 1/6/2026

## I. Đóng góp kỹ thuật (15 điểm)

- **Mô-đun đã triển khai**: `src/tools/hr_tools.py` (mô phỏng công cụ truy vấn dữ liệu nhân sự) và cập nhật nhẹ `src/agent/chatbot.py` để log thêm các bước tư duy khi agent dùng ReAct.
- **Điểm nổi bật trong mã**: Tôi thêm hàm `query_employee_by_id` trong `hr_tools.py` để trả về dữ liệu mẫu (tên, vị trí, phòng ban). Trong `chatbot.py` tôi thêm một khối log cho `Thought` và `Action` để dễ track luồng ReAct.
- **Tài liệu**: Trong phần comment của `hr_tools.py` tôi giải thích cách công cụ này được gọi bởi vòng lặp ReAct: agent gửi `Action` dạng `query_employee(id)`; công cụ trả về `Observation` chứa thông tin, agent dùng observation để suy luận tiếp.

---

## II. Nghiên cứu trường hợp gỡ lỗi (10 điểm)

- **Mô tả vấn đề**: Trong quá trình phát triển, agent đôi khi bị lặp vòng với các hành động giống nhau (ví dụ: `Action: query_employee(123)` rồi nhận `Observation: not found`, nhưng agent vẫn tiếp tục gọi lại cùng action nhiều lần).
- **Nguồn log**: Các log liên quan được sinh ra bởi `telemetry/logger.py` và lưu theo ngày; ví dụ dòng log dạng `Thought: ... Action: query_employee(123) Observation: not found` giúp lần mò nguyên nhân.
- **Chuẩn đoán**: Nguyên nhân chính là prompt của agent thiếu điều kiện dừng/chi nhánh rõ ràng khi nhận observation `not found`. Mô hình LLM có xu hướng chuỗi suy luận lặp lại nếu không có ví dụ rõ ràng cho trường hợp thất bại hoặc không có thông tin.
- **Giải pháp**: Tôi bổ sung hai thay đổi: (1) Cập nhật prompt mẫu trong `agent/agent.py` để thêm ví dụ cho trường hợp `Observation: not found` và kèm hướng dẫn rõ ràng cho bước tiếp theo (ví dụ: thử action khác hoặc trả về câu hỏi cho người dùng). (2) Thêm một giới hạn số lần thử cho mỗi tool call trong `hr_tools.py` (ví dụ tối đa 3 lần) và log cảnh báo khi vượt ngưỡng.

---

## III. Nhận định cá nhân: Chatbot vs ReAct (10 điểm)

1. **Suy luận**: Khối `Thought` giúp agent minh bạch quá trình suy luận — thay vì trả lời trực tiếp, ReAct buộc agent phải diễn đạt các bước trung gian (tại sao chọn tool nào, giả định nào đang được sử dụng). Điều này hữu ích khi cần kiểm tra hoặc gỡ lỗi hành vi của agent.

2. **Độ tin cậy**: Trong một số trường hợp, agent hoạt động kém hơn Chatbot truyền thống: khi câu hỏi đơn giản và không cần truy vấn công cụ (ví dụ hỏi định nghĩa ngắn), ReAct có thể tốn thêm bước (suy nghĩ + quyết định dùng tool) khiến phản hồi chậm hơn và đôi khi thừa bước. Ngoài ra, nếu tool không đủ thông tin hoặc phản hồi mơ hồ, ReAct có thể lúng túng hơn.

3. **Ảnh hưởng của Observation**: Observation đóng vai trò là phản hồi của môi trường — nó giúp agent cập nhật niềm tin và điều chỉnh hành động tiếp theo (chọn tool khác, hỏi thêm thông tin, hoặc trả kết quả). Trong thực nghiệm, agent thường đưa ra hành động hữu ích hơn sau khi có observation rõ ràng.

---

## IV. Cải tiến tương lai (5 điểm)

- **Khả năng mở rộng**: Dùng hàng đợi bất đồng bộ (async queue) cho các tool call và worker pool để xử lý song song nhiều yêu cầu tool. Điều này giúp scale khi có nhiều user hoặc nhiều tool nặng.
- **An toàn**: Thêm một LLM “giám sát” (supervisor) để rà soát các action của agent trước khi gọi tool nhạy cảm; áp đặt các policy (rate limit, blacklist) cho các tool nhất định.
- **Hiệu năng**: Sử dụng vector database cho caching kết quả tool và embedding retrieval khi hệ thống có nhiều tool, để giảm số lần gọi model và tăng tốc phản hồi.

---

