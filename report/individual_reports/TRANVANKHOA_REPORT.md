# Individual Report: Lab 3 - Chatbot vs ReAct Agent

**Student Name:** Trần Văn Khoa  
**Student ID:** 2A202600827  
**Date:** 01/06/2026

## I. Technical Contribution (15 Points)

**Modules Implemented:**  
`src/agent/react_agent.py` (Trọng tâm nâng cấp từ phiên bản cơ bản **v1** lên phiên bản ổn định **v2**).

### Code Highlights:

**1. Cơ chế Tự sửa lỗi Định dạng (Format Retry):**  
Khi LLM sinh ra chuỗi JSON lỗi ở phần Action, hệ thống không crash mà sẽ gửi feedback kèm ví dụ để LLM thử lại (chỉ áp dụng cho bản v2).

```python
if parser_error:
    # V2 Improvement: Retry once if JSON is malformed
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

**2. Hệ thống Guardrails bảo vệ cuộc gọi Tool:**  
Tự động chặn và trả lỗi nếu tool không tồn tại trong `TOOLS_MAP` hoặc thiếu tham số bắt buộc (`required`) trước khi thực thi code thực tế.

### Documentation:
Đoạn code trên can thiệp trực tiếp vào chu kỳ lặp của ReAct (**Thought → Action → Observation**). Thay vì để Agent dừng đột ngột khi gặp lỗi cú pháp JSON hoặc runtime error, hệ thống biến các lỗi đó thành Observation đặc biệt, giúp LLM tự sửa sai ở lượt suy nghĩ tiếp theo.

---

## II. Debugging Case Study (10 Points)

**Problem Description:**  
Agent rơi vào trạng thái lặp vô hạn hoặc báo lỗi Parser Error do LLM sinh cấu trúc `Action` bên trong khối Markdown code block (` ```json ... ``` `), khiến hàm `json.loads()` không parse được.

**Log Source:**

```plaintext
2026-06-01 14:22:15 - INFO - --- ReAct Step 1/3 ---
2026-06-01 14:22:18 - INFO - LLM Response:
Thought: Tôi cần kiểm tra số ngày phép còn lại của nhân viên NV003.
Action:
```json
{ "tool": "get_leave_balance", "args": { "employee_id": "NV003" } }
```
2026-06-01 14:22:18 - PARSER_ERROR - {"content": "...", "error": "JSON Decode Error on string..."}
```

**Diagnosis:**  
LLM có thói quen tự động bọc JSON trong Markdown code block. Hàm parse ban đầu chỉ cắt chuỗi thô sau chữ `Action:`, dẫn đến đưa cả ký tự ``` vào `json.loads()` gây crash.

**Solution:**  
Cải tiến hàm `_parse_action()` bằng regex để bóc tách JSON ra khỏi Markdown wrapper.

```python
md_match = re.search(r"```(?:json)?\s*(.*?)\s*```", action_str, re.DOTALL)
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

**Reasoning Capability:**

- **Thought** trong ReAct đóng vai trò như **Scratchpad** (bộ nhớ tạm để lập kế hoạch).  
- Khác với **HRBaselineChatbot** (dễ hallucinate), ReAct Agent có khả năng chia nhỏ bài toán phức tạp thành các hành động đơn lẻ có mục tiêu rõ ràng.

**Reliability:**

Agent thường hoạt động **tệ hơn** Chatbot thông thường trong các trường hợp:
- Câu hỏi mang tính tổng quát hoặc hỏi về chính sách chung.
- LLM nền yếu, liên tục sinh JSON sai format → Agent dễ bị kẹt.

**Observation** là điểm mạnh lớn nhất: Nó tạo vòng lặp phản hồi giúp Agent tự sửa sai thông minh.

---

## IV. Future Improvements (5 Points)

**Scalability:**  
Chuyển đổi thực thi tool sang **asynchronous** (`async/await`) hoặc sử dụng Task Queue (Celery) để xử lý tool chậm mà không block Agent.

**Safety:**  
Xây dựng **Guardrail Layer** độc lập (NeMo Guardrails hoặc LLM Supervisor) để kiểm tra an toàn tham số trước khi gọi tool.

**Performance (Many-tool System):**  
Sử dụng **Vector Database + RAG for Tools** để chỉ retrieve 3–5 tools phù hợp nhất thay vì nhét hết mô tả tool vào prompt.

---
**End of Report**
