# Báo cáo Cá nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên học viên (Student Name)**: Nguyễn Văn Duy
- **Mã sinh viên (Student ID)**: 2A202600725
- **Ngày thực hiện (Date)**: 01/06/2026
- **Ngày sinh**: 01/06/2005

---

## I. Đóng góp Kỹ thuật (Technical Contribution) (15 Điểm)

*Mô tả đóng góp cụ thể của bạn vào mã nguồn hệ thống.*

- **Các module đã triển khai (Modules Implemented)**: 
  * **LLM Provider Factory (`src/core/provider_factory.py`)**: Triển khai thiết kế nhà máy động cho phép tự động phân tích cấu hình từ file `.env` để khởi tạo nhà cung cấp LLM phù hợp (OpenAI, Gemini, hoặc Local) dưới dạng lazy loading, tránh lỗi import crash khi thiếu thư viện tùy chọn.
  * **HR Database & Tools (`src/tools/hr_data.py` & `src/tools/hr_tools.py`)**: Xây dựng cơ sở dữ liệu giả lập chứa thông tin nhân sự và ánh xạ chúng thành 5 công cụ chức năng có định dạng Schema JSON chặt chẽ cho tham số đầu vào.
  * **Enhanced ReAct Loop (`src/agent/agent.py`)**: Triển khai vòng lặp cốt lõi Thought-Action-Observation kết hợp phân tích cú pháp khối hành động JSON, cơ chế tự động thử lại khi lỗi cú pháp (retry) và hệ thống kiểm tra đối số đầu vào (guardrail).

- **Điểm sáng Code (Code Highlights)**:
  Đoạn mã xử lý rào chắn tự phục hồi (self-healing retry guardrail) khi LLM trả về khối hành động JSON bị lỗi cú pháp tại tệp `src/agent/agent.py`:
  ```python
  # Trích xuất từ src/agent/agent.py
  # Xử lý tự phục hồi khi phân tích JSON Action bị lỗi cú pháp
  if parser_error:
      # Cải tiến trong bản V2: Thử lại 1 lần nếu JSON bị lỗi định dạng
      if self.version == "v2" and steps < self.max_steps:
          feedback = (
              f"Observation: Error: Invalid JSON action block format. "
              f"Please output the action strictly as a JSON object after Action: e.g.\n"
              f"Action: {{\"tool\": \"tool_name\", \"args\": {{\"param\": \"value\"}}}}\n"
              f"Please try again."
          )
          logger.info(f"V2 Retry Triggered: {feedback}")
          current_prompt += f"\n{feedback}\n"
          continue
  ```

- **Tài liệu hướng dẫn (Documentation)**:
  Mã nguồn trên tích hợp trực tiếp vào ReAct loop tại `agent.py`. Khi LLM sinh ra Action, bộ phân tích cú pháp sẽ tách chuỗi JSON sau từ khóa `Action:`. Nếu xảy ra ngoại lệ `ValueError` do lỗi cú pháp, thay vì crash toàn bộ tiến trình như bản V1, bản V2 sẽ đóng gói thông tin lỗi gửi ngược lại ngữ cảnh (context) cho LLM tự sửa sai ở bước (Step) tiếp theo.

---

## II. Nghiên cứu Tình huống Gỡ lỗi (Debugging Case Study) (10 Điểm)

*Phân tích một trường hợp lỗi cụ thể mà bạn gặp phải trong quá trình làm lab bằng cách sử dụng hệ thống log.*

- **Mô tả vấn đề (Problem Description)**:
  Khi chạy thử nghiệm Agent v1 trên các truy vấn tìm kiếm nhân viên bằng tên (ví dụ: *"Ai là quản lý của Trần Thị B?"*), tác nhân thường xuyên bị thất bại. Thay vì sử dụng công cụ `get_employee` trước để lấy mã ID thích hợp, LLM tự động đoán mò ID (`NV002`) hoặc truyền trực tiếp chuỗi `"Trần Thị B"` vào tham số yêu cầu mã ID của các công cụ `get_leave_balance` hay `calculate_payroll`, gây ra lỗi không tìm thấy dữ liệu.

- **Nguồn Log hệ thống (Log Source)**:
  Trích xuất từ tệp log giám sát `logs/2026-06-01.log` ghi lại lỗi gọi công cụ sai tham số:
  ```json
  {"timestamp": "2026-06-01T06:04:45.002", "event": "TOOL_CALL", "data": {"tool": "get_leave_balance", "args": {"employee_id": "Trần Thị B"}}}
  {"timestamp": "2026-06-01T06:04:45.105", "event": "TOOL_RESULT", "data": {"tool": "get_leave_balance", "result": "Error: Employee ID 'Trần Thị B' not found in leave records."}}
  ```

- **Chẩn đoán (Diagnosis)**:
  Mô hình LLM giả định rằng các công cụ hoạt động linh hoạt nên truyền trực tiếp tên `"Trần Thị B"` thay vì ID nhân viên. Trong khi đó, Schema metadata đầu vào của các công cụ trong V1 chỉ ghi nhận tham số `employee_id` và bắt buộc nhập mã ID có dạng `NVxxx`, dẫn đến việc công cụ không thể đối chiếu dữ liệu cục bộ.

- **Giải pháp (Solution)**:
  Để khắc phục hoàn toàn vấn đề này, tôi đã triển khai gói giải pháp tối ưu hóa 3 lớp:
  1. Đổi tên tham số công cụ trong cả chữ ký hàm Python và Schema metadata trong `TOOLS_METADATA` thành `employee_id_or_name` để chỉ dẫn rõ ràng cho LLM.
  2. Bổ sung Rule số 2 vào Prompt hệ thống của Agent khẳng định các công cụ hỗ trợ xử lý cả tên lẫn ID trực tiếp, loại bỏ việc bắt buộc gọi `get_employee` làm lãng phí số bước thực thi.
  3. Triển khai thanh trượt điều chỉnh số bước tối đa **"Max ReAct Steps"** động trên giao diện Streamlit (phạm vi 1-5, mặc định là 3) để kiểm soát nghiêm ngặt chi phí token phát sinh.
  
  *Kết quả*: Agent có khả năng gọi thẳng các công cụ tính lương hay ngày phép chỉ với 1 bước duy nhất bằng tên nhân viên, tiết kiệm 50% thời gian trễ và chi phí.

---

## III. Nhận thức Cá nhân: Chatbot vs ReAct (10 Điểm)

*Phản ánh về sự khác biệt trong khả năng suy luận giữa hai mô hình.*

1.  **Khả năng suy luận (Reasoning)**:
    Khối suy nghĩ `Thought` hoạt động như một "bảng nháp tư duy" cho LLM. Thay vì ép buộc mô hình đưa ra ngay câu trả lời cuối cùng dễ dẫn đến sai sót và phán đoán mò, `Thought` giúp LLM phân tích mục tiêu lớn phức tạp thành chuỗi các hành động nhỏ logic. Ví dụ: *"Trước tiên tôi cần lấy thông tin bảng lương của NV005, sau đó mới tính tổng net salary."* Điều này khớp hoàn toàn với quy trình giải quyết vấn đề của con người.

2.  **Độ tin cậy (Reliability)**:
    Mặc dù ReAct Agent vượt trội về độ chính xác dữ liệu thực tế, nhưng nó vẫn hoạt động kém hơn Chatbot Baseline trong 2 trường hợp:
    * **Độ trễ (Latency)**: ReAct yêu cầu nhiều vòng lặp gọi API LLM liên tục và chạy các hàm Python cục bộ. Một câu hỏi kiến thức phổ thông đơn giản, Chatbot Baseline chỉ mất dưới 1 giây để trả lời, trong khi ReAct Agent mất 3-4 giây do chạy các bước Thought/Action dư thừa.
    * **Lỗi lan truyền (Error Propagation)**: Khi một công cụ gặp lỗi hoặc trả về kết quả quan sát (`Observation`) gây hiểu lầm, Agent có thể rơi vào vòng lặp vô hạn nhằm cố gắng khắc phục lỗi, gây bùng nổ chi phí token API.

3.  **Kết quả quan sát (Observation)**:
    Phản hồi từ môi trường (`Observation`) là "mắt và tai" của tác nhân. Khi một công cụ Python trả về kết quả lỗi hoặc cảnh báo, Agent thông minh sẽ phân tích phản hồi đó để thay đổi chiến thuật ở bước Thought tiếp theo (ví dụ: đổi từ khóa tìm kiếm hay sửa đổi tham số đầu vào) thay vì mù quáng lặp lại hành động lỗi trước đó.

---

## IV. Cải tiến trong Tương lai (Future Improvements) (5 Điểm)

*Làm thế nào để bạn mở rộng hệ thống này cho một hệ thống AI Agent cấp độ thương mại thực tế?*

- **Khả năng mở rộng (Scalability)**:
  Hỗ trợ thực thi công cụ song song không đồng bộ (Asynchronous Parallel Tool Calls) bằng cách sử dụng thư viện `asyncio` trong Python. Khi cần xử lý hoặc tính toán bảng lương cho hàng loạt nhân viên cùng lúc, việc thực thi song song sẽ giảm thiểu tối đa thời gian trễ hệ thống so với việc chạy tuần tự từng nhân viên.

- **Tính an toàn (Safety)**:
  Tích hợp Kiểm soát truy cập dựa trên vai trò (Role-Based Access Control - RBAC) ngay ở cấp độ công cụ của Agent. Do dữ liệu nhân sự và tiền lương rất nhạy cảm, Agent bắt buộc phải xác thực vai trò/quyền hạn của tài khoản người dùng đang đăng nhập trước khi cho phép gọi các công cụ nhạy cảm như `calculate_payroll`.

- **Hiệu năng (Performance)**:
  Thay thế bộ tìm kiếm từ khóa thủ công trong `search_policy` bằng giải pháp Hybrid RAG kết hợp với cơ sở dữ liệu Vector (Vector Database như ChromaDB/PGVector). Điều này giúp Agent có thể tìm kiếm chính xác các quy định dựa trên ngữ nghĩa của câu hỏi (ví dụ: tìm hiểu về chế độ nghỉ sinh nở sẽ tự động ánh xạ sang quy định nghỉ thai sản) thay vì so khớp ký tự cứng nhắc.

---
