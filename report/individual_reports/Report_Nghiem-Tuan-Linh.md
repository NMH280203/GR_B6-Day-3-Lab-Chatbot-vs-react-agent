# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Nghiêm Tuấn Linh]
- **Student ID**: [2A202600897]
- **Date**: [1/6/2026]

---

## I. Technical Contribution (15 Points)



Đóng góp chính của tôi là triển khai lớp trừu tượng cho LLM Provider, giúp hệ thống có thể chuyển đổi linh hoạt giữa nhiều backend mô hình khác nhau như OpenAI, Google Gemini, Ollama và mô hình local .gguf mà không cần thay đổi logic chính của ứng dụng.

Modules
src/core/llm_provider.py
src/core/openai_provider.py
src/core/gemini_provider.py
src/core/ollama_provider.py
src/core/local_provider.py
src/core/provider_factory.py
Code Highlights

Tôi triển khai LLMProvider như một abstract base class, định nghĩa interface chung cho tất cả provider. Mỗi provider đều cần có hai phương thức chính: generate() để sinh phản hồi thông thường và stream() để hỗ trợ phản hồi dạng streaming.

provider = get_provider()
response = provider.generate(prompt, system_prompt)

Ngoài ra, tôi xây dựng các provider riêng cho OpenAI, Gemini, Ollama và local model, đồng thời triển khai provider_factory.py để đọc cấu hình từ file .env và tự động khởi tạo provider phù hợp dựa trên DEFAULT_PROVIDER.

Documentation

Phần code này đóng vai trò là model execution layer trong ReAct loop. ReAct loop chỉ cần gọi interface chung của provider thay vì phụ thuộc trực tiếp vào từng API cụ thể. Điều này giúp hệ thống modular hơn, dễ mở rộng và dễ chuyển đổi giữa cloud model và local model.

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: [e.g., Agent caught in an infinite loop with `Action: search(None)`]
- **Log Source**: [Link or snippet from `logs/YYYY-MM-DD.log`]
- **Diagnosis**: [Why did the LLM do this? Was it the prompt, the model, or the tool spec?]
- **Solution**: [How did you fix it? (e.g., updated `Thought` examples in the system prompt)]

---


Trong quá trình thực hiện lab, tôi gặp một lỗi liên quan đến việc agent chọn sai công cụ khi xử lý yêu cầu của người dùng. Cụ thể, người dùng nhập: “Tìm cho tôi lương của role HR specialist”. Tuy nhiên, thay vì tìm kiếm thông tin mức lương theo vị trí công việc, agent lại gọi công cụ calculate_payroll với tham số "employee_id_or_name": "HR Specialist".

Problem Description

Agent hiểu nhầm "HR Specialist" là tên nhân viên hoặc mã nhân viên, trong khi đây thực chất là tên một vị trí công việc. Vì vậy, công cụ calculate_payroll trả về lỗi:

Error: Employee 'HR Specialist' not found in payroll records.

Sau lỗi này, agent không thử dùng công cụ khác mà kết luận rằng không tìm thấy nhân viên và yêu cầu người dùng kiểm tra lại danh sách nhân sự.

Log Source
{
  "event": "TOOL_CALL",
  "data": {
    "tool": "calculate_payroll",
    "args": {
      "employee_id_or_name": "HR Specialist"
    }
  }
}
{
  "event": "TOOL_RESULT",
  "data": {
    "tool": "calculate_payroll",
    "result": "Error: Employee 'HR Specialist' not found in payroll records."
  }
}
Diagnosis

Nguyên nhân chính là do LLM chưa phân biệt rõ giữa yêu cầu tính lương cho một nhân viên cụ thể và yêu cầu tra cứu mức lương theo vai trò công việc. Cụm từ “role HR Specialist” cho thấy người dùng đang hỏi về mức lương của một vị trí, không phải bảng lương của một cá nhân. Lỗi này có thể đến từ prompt hoặc tool specification chưa mô tả rõ khi nào nên dùng calculate_payroll.

Solution

Để khắc phục, cập nhật phần hướng dẫn trong system prompt và mô tả công cụ. Cụ thể, tôi bổ sung quy tắc rằng calculate_payroll chỉ được dùng khi người dùng cung cấp tên hoặc mã nhân viên cụ thể. Nếu người dùng hỏi về lương theo role, job title hoặc position, agent cần dùng công cụ tìm kiếm thông tin lương hoặc truy vấn dữ liệu vị trí công việc trước.

Ví dụ cập nhật prompt:

Use calculate_payroll only when the user provides a specific employee name or employee ID.
If the user asks about salary by role, job title, or position, do not treat the role as an employee name.

Sau khi cập nhật, agent có thể tránh gọi sai công cụ và xử lý đúng ý định của người dùng trong ReAct loop.

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
3.  **Observation**: How did the environment feedback (observations) influence the next steps?

---
Reasoning: Thought block giúp agent thể hiện rõ quá trình suy luận trước khi hành động. Nhờ đó, agent không chỉ trả lời trực tiếp như chatbot mà còn phân tích yêu cầu, chọn công cụ phù hợp và quyết định bước tiếp theo.
Reliability: Agent có thể hoạt động kém hơn chatbot khi hiểu sai ý định người dùng hoặc chọn sai tool. Ví dụ, agent có thể gọi công cụ tính lương cho nhân viên trong khi người dùng chỉ muốn tra cứu lương theo vị trí công việc.
Observation: Observation cung cấp phản hồi từ môi trường sau mỗi lần gọi tool. Dựa vào kết quả này, agent có thể biết hành động trước đó đúng hay sai, từ đó điều chỉnh hướng xử lý hoặc đưa ra câu trả lời cuối cùng.

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: [e.g., Use an asynchronous queue for tool calls]
- **Safety**: [e.g., Implement a 'Supervisor' LLM to audit the agent's actions]
- **Performance**: [e.g., Vector DB for tool retrieval in a many-tool system]

---
**Scalability**: Dùng asynchronous queue để xử lý nhiều tool calls đồng thời và tránh nghẽn hệ thống.
**Safety**: Thêm Supervisor LLM hoặc guardrail để kiểm tra action trước khi thực thi.
**Performance**: Dùng vector database để chọn tool phù hợp, cache kết quả và giới hạn số ReAct steps.

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
