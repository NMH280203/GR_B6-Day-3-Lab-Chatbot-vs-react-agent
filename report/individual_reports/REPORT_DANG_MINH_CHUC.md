# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đặng Minh Chức 
- **Student ID**: 2A202600611
- **Date**: 01/06/2026

---

## I. Đóng góp kỹ thuật (15 điểm)

*Mô tả đóng góp cụ thể: Thiết kế và phát triển kịch bản đo lường chuẩn (benchmark) sau khi nhóm đã hoàn thiện các mô hình, nhằm nghiệm thu và so sánh hiệu năng thực tế.*

- **Mô-đun đã triển khai**: Xây dựng độc lập script `test_hr_agent.py` đóng vai trò là công cụ tự động đánh giá chéo 3 hệ thống: Baseline Chatbot, ReAct v1 và ReAct v2.
- **Điểm nổi bật trong mã**: 
  - Thiết kế mảng 10 kịch bản `SCENARIOS` bao phủ các trường hợp đa dạng từ tra cứu đơn giản, tính toán nhiều bước đến các trường hợp cố tình gây lỗi (thông tin thiếu, nhân viên không tồn tại) để kiểm tra giới hạn của agent.
  - Tích hợp bộ đếm tự động đo lường độ trễ (latency_ms), số bước (steps), tổng token tiêu thụ và chi phí ước tính (cost) qua vòng lặp `for sys_idx, system in enumerate(systems)`.
- **Tài liệu**: Script hoạt động bằng cách cô lập từng hệ thống, chạy tuần tự các câu hỏi, bắt lỗi (try-except) để đảm bảo toàn bộ quá trình nghiệm thu không bị gián đoạn, sau đó tự động tổng hợp kết quả ra file `comparative_evaluation_report.md`.

---

## II. Nghiên cứu trường hợp gỡ lỗi (10 điểm)

*Đứng từ góc độ kiểm thử ở giai đoạn cuối, phân tích lỗi phát hiện được khi chạy benchmark chéo giữa các phiên bản.*

- **Mô tả vấn đề**: Khi chạy kịch bản nghiệm thu tổng thể, tôi ghi nhận ReAct Agent v1 không vượt qua được các test case tính toán hoặc gọi tool, hệ thống trả về ngoại lệ hoặc crash (ví dụ: lỗi `JSONDecodeError`). 
- **Nguồn log**: Lỗi được `test_hr_agent.py` bắt qua khối `except Exception as e` và in trực tiếp ra console, ghi nhận trạng thái `ERROR EXECUTING RUN` tại các scenario gọi tool.
- **Chuẩn đoán**: Dựa trên log sinh ra lúc chạy script, tôi xác định nguyên nhân là LLM ở bản v1 không tuân thủ nghiêm ngặt định dạng JSON khi sinh ra `Action`, hoặc gửi thiếu tham số (như thiếu `employee_id_or_name` khi gọi `calculate_payroll`) khiến backend Python không thể thực thi.
- **Giải pháp (Góc độ nghiệm thu)**: Thay vì trực tiếp sửa code, tôi sử dụng bảng báo cáo tự động từ `test_hr_agent.py` để xác nhận chéo rằng cấu trúc mới của nhóm ở bản v2 đã khắc phục hoàn toàn vấn đề này. Dữ liệu nghiệm thu cho thấy cột báo lỗi "Parser/Tool Errors" của v2 đã giảm về 0 (nhờ cơ chế Guardrails và Self-healing), khẳng định bản v2 đã sẵn sàng đưa vào sử dụng.

---

## III. Nhận định cá nhân: Chatbot vs ReAct (10 điểm)

*Đánh giá năng lực của các mô hình dựa trên số liệu thu thập được từ script benchmark do bản thân xây dựng.*

1. **Suy luận**: Thông qua script đánh giá, có thể thấy rõ khối `Thought` giúp ReAct Agent vượt trội ở các bài toán khó. Agent giải quyết chính xác 100% các câu hỏi logic/tính toán (như tính lương Net) nhờ việc tự động tra cứu dữ liệu cục bộ thay vì bịa đặt thông tin (hallucination) như Chatbot cơ sở.
2. **Độ tin cậy**: Ở góc độ hiệu năng hệ thống, báo cáo nghiệm thu cho thấy Chatbot Baseline có lợi thế tuyệt đối về độ trễ và chi phí đối với các câu hỏi giao tiếp thông thường. ReAct Agent tỏ ra cồng kềnh, tiêu tốn nhiều thời gian (độ trễ có thể lên tới 5200ms) và token (trung bình 1200 tokens/tác vụ) hơn mức cần thiết cho những truy vấn đơn giản.
3. **Observation**: Quá trình chạy kịch bản thử nghiệm số 8 và 9 (các trường hợp thiếu thông tin) chứng minh vai trò của Observation. Khi gọi tool không ra kết quả, Observation trả về lỗi giúp Agent nhận thức được giới hạn, từ đó chủ động hỏi lại người dùng hoặc thông báo lỗi một cách an toàn.

---

## IV. Cải tiến tương lai (5 điểm)

*Đề xuất nâng cấp quy trình kiểm thử và đánh giá khi triển khai dự án vào thực tế doanh nghiệp.*

- **Tự động hóa hoàn toàn (CI/CD Testing)**: Chuyển đổi `test_hr_agent.py` thành một luồng kiểm thử hồi quy (regression test) tự động chạy trên GitHub Actions hoặc GitLab CI mỗi khi có ai đó trong nhóm cập nhật mã nguồn công cụ hay thay đổi prompt.
- **LLM-as-a-judge**: Chấm dứt việc phải "Manual Review Required" (kiểm tra thủ công bằng mắt) đối với file báo cáo. Thay vào đó, sử dụng một LLM độc lập để tự động chấm điểm độ chính xác giữa phản hồi của Agent và cột `expected` của kịch bản, giúp mở rộng số lượng test case từ 10 lên hàng nghìn.
- **Giám sát trực quan**: Thay vì chỉ xuất log ra console và file markdown, có thể tích hợp script kiểm thử với hệ thống telemetry chuyên dụng như LangSmith để có giao diện UI theo dõi chi tiết từng bước Thought/Action/Observation, giúp quá trình nghiệm thu (QA) dễ dàng hơn.