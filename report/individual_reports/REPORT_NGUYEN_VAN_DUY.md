# Báo cáo Cá nhân: Lab 3 - Chatbot vs ReAct Agent

- **Họ và tên**: Nguyễn Văn Duy
- **Mã sinh viên**: 2A202600725
- **Ngày sinh**: 01/06/2005
- **Ngày thực hiện**: 01/06/2026

---

## I. Đóng góp Kỹ thuật (Technical Contribution) (15 Điểm)

*Mô tả đóng góp cụ thể của bạn vào mã nguồn hệ thống.*

- **Modules Implementated**: 
  * **Cơ sở dữ liệu nhân sự giả lập (`src/tools/hr_data.py`)**: Thiết kế và cấu trúc cơ sở dữ liệu Mock dạng cấu trúc từ điển (Dictionary) lưu trữ thông tin thực tế của nhân viên (`EMPLOYEES`), số dư ngày phép năm (`LEAVE_BALANCES`), thông số lương gồm lương cơ bản, thưởng, phụ cấp, khấu trừ (`PAYROLL`) và tệp quy chế chính sách HR nội bộ (`POLICIES`).
  * **Bộ công cụ HR tích hợp (`src/tools/hr_tools.py`)**: Lập trình toàn bộ logic nghiệp vụ cho 5 công cụ (tools) chính để cung cấp khả năng truy xuất cho Agent, bao gồm:
    * `get_employee`: Tra cứu thông tin hồ sơ nhân viên (phòng ban, chức vụ, ngày tham gia) hỗ trợ tìm kiếm không dấu và khớp một phần tên.
    * `get_leave_balance`: Tra cứu phép năm và số ngày phép còn lại.
    * `calculate_payroll`: Tính toán thực nhận (Net Salary) dựa trên công thức cấu trúc.
    * `search_policy`: Tìm kiếm từ khóa chính sách.
    * `list_department_employees`: Liệt kê danh sách nhân sự theo phòng ban.
  * **Thiết lập metadata và ánh xạ công cụ (`src/tools/hr_tools.py`)**: Thiết kế bộ Schema JSON mô tả tham số chi tiết (`TOOLS_METADATA`) và bảng ánh xạ (`TOOLS_MAP`) để ReAct Agent có thể nhận diện và thực thi động thông qua LLM.

- **Code Highlights**:
  Đoạn mã lập trình thuật toán chuẩn hóa tiếng Việt không dấu (`strip_accents`) và tìm kiếm gần đúng thông tin nhân viên (`get_employee`) hỗ trợ tìm kiếm thông minh từ tệp `src/tools/hr_tools.py`:
  ```python
  # Trích xuất từ src/tools/hr_tools.py
  def strip_accents(text: str) -> str:
      """
      Loại bỏ dấu tiếng Việt và chuẩn hóa ký tự sang dạng chữ thường
      giúp Agent hỗ trợ tìm kiếm không dấu linh hoạt, tránh lỗi gõ phím.
      """
      normalized = unicodedata.normalize('NFD', text)
      stripped = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
      return stripped.replace('đ', 'd').replace('Đ', 'd').lower().strip()

  def get_employee(employee_id_or_name: str) -> str:
      """Tra cứu thông tin nhân viên theo ID hoặc Tên (hỗ trợ khớp một phần và không dấu)."""
      employee_id_or_name = employee_id_or_name.strip()
      
      # 1. Tìm kiếm chính xác theo mã ID (Không phân biệt hoa thường)
      upper_id = employee_id_or_name.upper()
      if upper_id in EMPLOYEES:
          return json.dumps(EMPLOYEES[upper_id], ensure_ascii=False)
          
      # 2. Tìm kiếm theo Tên (Hỗ trợ không dấu, khớp một phần)
      query_clean = strip_accents(employee_id_or_name)
      matches = []
      for emp_id, emp in EMPLOYEES.items():
          name_clean = strip_accents(emp["name"])
          if query_clean in name_clean:
              matches.append(emp)
              
      if len(matches) == 1:
          return json.dumps(matches[0], ensure_ascii=False)
      elif len(matches) > 1:
          return f"Multiple employees found: " + json.dumps(matches, ensure_ascii=False)
          
      return f"Error: Employee '{employee_id_or_name}' not found."
  ```

- **Documentation**:
  Công cụ `strip_accents` sử dụng module `unicodedata` để tách các dấu thanh ra khỏi chữ cái gốc và loại bỏ chúng bằng cách lọc nhóm ký tự `Mn` (Mark, Nonspacing). Hàm `get_employee` sau đó so sánh chuỗi truy vấn đã loại bỏ dấu với cơ sở dữ liệu nhân sự để tự động trả về thông tin dạng chuỗi JSON thô phục vụ bước quan sát (`Observation`) của ReAct Agent. 5 công cụ này được đăng ký thông qua `TOOLS_METADATA` và `TOOLS_MAP` tại `hr_tools.py` để ReAct Agent có thể gọi động thông qua các hành động `Action` JSON.

---

## II. Debugging Case Study (10 Points)

*Phân tích một trường hợp lỗi cụ thể mà bạn gặp phải trong quá trình làm lab bằng cách sử dụng hệ thống log.*

- **Problem Description**:
  Khi chạy thử nghiệm Agent v1 trên các truy vấn tìm kiếm nhân viên bằng tên (ví dụ: *"Ai là quản lý của Trần Thị B?"*), tác nhân thường xuyên bị thất bại. Thay vì sử dụng công cụ `get_employee` trước để lấy mã ID thích hợp, LLM tự động đoán mò ID (`NV002`) hoặc truyền trực tiếp chuỗi `"Trần Thị B"` vào tham số yêu cầu mã ID của các công cụ `get_leave_balance` hay `calculate_payroll`, gây ra lỗi không tìm thấy dữ liệu.

- **Log Source**:
  Trích xuất từ tệp log giám sát `logs/2026-06-01.log` ghi lại lỗi gọi công cụ sai tham số:
  ```json
  {"timestamp": "2026-06-01T06:04:45.002", "event": "TOOL_CALL", "data": {"tool": "get_leave_balance", "args": {"employee_id": "Trần Thị B"}}}
  {"timestamp": "2026-06-01T06:04:45.105", "event": "TOOL_RESULT", "data": {"tool": "get_leave_balance", "result": "Error: Employee ID 'Trần Thị B' not found in leave records."}}
  ```

- **Diagnosis**:
  Mô hình LLM giả định rằng các công cụ hoạt động linh hoạt nên truyền trực tiếp tên `"Trần Thị B"` thay vì ID nhân viên. Trong khi đó, Schema metadata đầu vào của các công cụ trong V1 chỉ ghi nhận tham số `employee_id` và bắt buộc nhập mã ID có dạng `NVxxx`, dẫn đến việc công cụ không thể đối chiếu dữ liệu cục bộ.

- **Solution**:
  Với tư cách là người phụ trách bộ công cụ, để khắc phục hoàn toàn vấn đề này và tối ưu hóa số bước gọi của Agent, tôi đã triển khai nâng cấp trực tiếp bộ công cụ:
  1. Đổi tên tham số công cụ trong cả chữ ký hàm Python của `get_leave_balance` & `calculate_payroll` và Schema metadata tương ứng thành `employee_id_or_name` để chỉ dẫn rõ ràng cho LLM.
  2. Lập trình thêm bước **Tự động phân giải Tên sang ID** ở ngay phần đầu logic của công cụ `get_leave_balance` và `calculate_payroll`. Khi nhận giá trị, công cụ sẽ tự động gọi hàm tra cứu thông tin nhân sự để xác thực và trích xuất mã ID tương ứng trước khi xử lý, cho phép LLM gọi thẳng công cụ mục tiêu bằng Tên mà không cần qua bước trung gian.
  
  *Kết quả*: Agent có khả năng gọi thẳng các công cụ tính lương hay ngày phép chỉ với 1 bước duy nhất bằng tên nhân viên, tiết kiệm 50% thời gian trễ và chi phí.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Phản ánh về sự khác biệt trong khả năng suy luận giữa hai mô hình.*

1.  **Reasoning**:
    Khối suy nghĩ `Thought` hoạt động như một "bản nháp tư duy" cho LLM. Thay vì ép buộc mô hình đưa ra ngay câu trả lời cuối cùng dễ dẫn đến sai sót và phán đoán mò, `Thought` giúp LLM phân tích mục tiêu lớn phức tạp thành chuỗi các hành động nhỏ logic. Ví dụ: *"Trước tiên tôi cần lấy thông tin bảng lương của NV005, sau đó mới tính tổng net salary."* Điều này khớp hoàn toàn với quy trình giải quyết vấn đề của con người.

2.  **Reliability**:
    Mặc dù ReAct Agent vượt trội về độ chính xác dữ liệu thực tế nhờ có các công cụ HR Database hỗ trợ truy vấn chính xác, nhưng nó vẫn hoạt động kém hơn Chatbot Baseline trong 2 trường hợp:
    * **Độ trễ (Latency)**: ReAct yêu cầu nhiều vòng lặp gọi API LLM liên tục và chạy các hàm Python cục bộ. Một câu hỏi kiến thức phổ thông đơn giản, Chatbot Baseline chỉ mất dưới 1 giây để trả lời, trong khi ReAct Agent mất 3-4 giây do chạy các bước Thought/Action dư thừa.
    * **Lỗi lan truyền (Error Propagation)**: Khi một công cụ gặp lỗi hoặc trả về kết quả quan sát (`Observation`) gây hiểu lầm, Agent có thể rơi vào vòng lặp vô hạn nhằm cố gắng khắc phục lỗi, gây bùng nổ chi phí token API.

3.  **Observation**:
    Phản hồi từ môi trường (`Observation`) là "mắt và tai" của tác nhân. Khi một công cụ Python trả về kết quả lỗi hoặc cảnh báo, Agent thông minh sẽ phân tích phản hồi đó để thay đổi chiến thuật ở bước Thought tiếp theo (ví dụ: đổi từ khóa tìm kiếm hay sửa đổi tham số đầu vào) thay vì mù quáng lặp lại hành động lỗi trước đó.

---

## IV. Future Improvements (5 Points)

*Làm thế nào để bạn mở rộng hệ thống này cho một hệ thống AI Agent cấp độ thương mại thực tế?*

- **Scalability**:
  Hỗ trợ thực thi công cụ song song không đồng bộ (Asynchronous Parallel Tool Calls) bằng cách sử dụng thư viện `asyncio` trong Python. Khi cần xử lý hoặc tính toán bảng lương cho hàng loạt nhân viên cùng lúc, việc thực thi song song sẽ giảm thiểu tối đa thời gian trễ hệ thống so với việc chạy tuần tự từng nhân viên.

- **Safety**:
  Tích hợp Kiểm soát truy cập dựa trên vai trò (Role-Based Access Control - RBAC) ngay ở cấp độ công cụ của Agent. Do dữ liệu nhân sự và tiền lương rất nhạy cảm, Agent bắt buộc phải xác thực vai trò/quyền hạn của tài khoản người dùng đang đăng nhập trước khi cho phép gọi các công cụ nhạy cảm như `calculate_payroll`.

- **Performance**:
  Thay thế bộ tìm kiếm từ khóa thủ công trong `search_policy` bằng giải pháp Hybrid RAG kết hợp với cơ sở dữ liệu Vector (Vector Database như ChromaDB/PGVector). Điều này giúp Agent có thể tìm kiếm chính xác các quy định dựa trên ngữ nghĩa của câu hỏi (ví dụ: tìm hiểu về chế độ nghỉ sinh nở sẽ tự động ánh xạ sang quy định nghỉ thai sản) thay vì so khớp ký tự cứng nhắc.

---
