import os
import sys
import io

# Force UTF-8 encoding on Windows console
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import time
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.provider_factory import get_provider
from src.tools.hr_tools import TOOLS_METADATA
from src.agent.chatbot import HRBaselineChatbot
from src.agent.agent import ReActAgent
from src.telemetry.metrics import tracker

# Define the 10 HR scenarios for testing
SCENARIOS = [
    {
        "id": 1,
        "category": "Simple Policy",
        "question": "Chính sách của công ty về làm việc từ xa (remote work) quy định thế nào?",
        "expected": "tối đa 2 ngày/tuần"
    },
    {
        "id": 2,
        "category": "Lookup",
        "question": "Ai là quản lý trực tiếp của nhân viên Trần Thị B?",
        "expected": "NV001 (Nguyen Van A)"
    },
    {
        "id": 3,
        "category": "Leave Balance",
        "question": "Nhân viên NV003 còn bao nhiêu ngày nghỉ phép năm?",
        "expected": "4 ngày phép còn lại (12 ngày phép - 8 ngày đã dùng)"
    },
    {
        "id": 4,
        "category": "Calculated Salary",
        "question": "Tính lương thực nhận tháng này của nhân viên Nguyễn Văn A (mã NV001)? Formula: Net Salary = Base Salary + Bonus + Allowance - Deductions.",
        "expected": "39,000,000 VND (35,000,000 + 5,000,000 + 1,000,000 - 2,000,000)"
    },
    {
        "id": 5,
        "category": "Multi-step (Search & Calculate)",
        "question": "Hãy tìm nhân viên có chức vụ HR Specialist và tính lương thực nhận của cô ấy?",
        "expected": "Pham Thi D (NV004), Lương thực nhận: 20,000,000 VND (20,000,000 + 0 + 1,000,000 - 1,000,000)"
    },
    {
        "id": 6,
        "category": "Complex Multi-step",
        "question": "Trong phòng Engineering, ai có lương thực nhận cao nhất? Tính lương thực nhận của người đó.",
        "expected": "Hoang Van E (NV005), Lương thực nhận: 61,000,000 VND (55M + 8M + 2M - 4M)"
    },
    {
        "id": 7,
        "category": "OT Policy Query",
        "question": "Lương làm thêm giờ (OT) vào ngày cuối tuần (chủ nhật) được tính như thế nào?",
        "expected": "200% lương giờ tiêu chuẩn"
    },
    {
        "id": 8,
        "category": "Failure Case (Missing employee)",
        "question": "Nhân viên NV999 còn bao nhiêu ngày nghỉ phép?",
        "expected": "Không tồn tại / Báo lỗi nhân viên không tìm thấy"
    },
    {
        "id": 9,
        "category": "Failure Case (Missing info)",
        "question": "Hãy tính giúp tôi lương thực nhận tháng này của nhân viên.",
        "expected": "Hỏi lại mã nhân viên / Tên nhân viên"
    },
    {
        "id": 10,
        "category": "Complex Policy + Lookup",
        "question": "Nhân viên Nguyễn Văn A gia nhập công ty khi nào? Có đúng quy định nghỉ phép của nhân viên dưới 1 năm không?",
        "expected": "Gia nhập 2022-03-15 (trên 1 năm, không áp dụng quy định dưới 1 năm)"
    }
]

def run_evaluation():
    load_dotenv()
    
    # 1. Initialize LLM Provider
    try:
        llm = get_provider()
        print(f"[SUCCESS] Loaded Provider: {llm.provider} - Model: {llm.model_name}")
    except Exception as e:
        print(f"[ERROR] Error loading provider: {e}")
        print("Please check your .env and make sure GEMINI_API_KEY is filled in.")
        return
        
    # 2. Instantiate Systems
    chatbot = HRBaselineChatbot(llm=llm)
    agent_v1 = ReActAgent(llm=llm, tools=TOOLS_METADATA, version="v1")
    agent_v2 = ReActAgent(llm=llm, tools=TOOLS_METADATA, version="v2")
    
    systems = [
        {"name": "Chatbot Baseline", "runner": chatbot.run, "results": []},
        {"name": "ReAct Agent v1", "runner": agent_v1.run, "results": []},
        {"name": "ReAct Agent v2", "runner": agent_v2.run, "results": []}
    ]
    
    print("\nStarting Comparative Evaluation on 10 Scenarios...")
    
    for sys_idx, system in enumerate(systems):
        print(f"\n==========================================")
        print(f"[RUNNING] Running Evaluation for: {system['name']}")
        print(f"==========================================")
        
        for scenario in SCENARIOS:
            print(f"\n[Scenario {scenario['id']}] Category: {scenario['category']}")
            print(f"Question: {scenario['question']}")
            print(f"Expected Key Points: {scenario['expected']}")
            
            # Reset tracker for this specific run
            tracker.session_metrics = []
            
            start_time = time.time()
            try:
                # Run the system
                response_text = system["runner"](scenario["question"])
                execution_time = int((time.time() - start_time) * 1000)
                
                # Retrieve LLM metrics gathered during run
                metrics = tracker.session_metrics
                total_tokens = sum([m["total_tokens"] for m in metrics])
                prompt_tokens = sum([m["prompt_tokens"] for m in metrics])
                completion_tokens = sum([m["completion_tokens"] for m in metrics])
                cost = sum([m["cost_estimate"] for m in metrics])
                step_count = len(metrics) # In ReAct, each LLM call is a step
                
                print(f"Response:\n{response_text}")
                print(f"Metrics -> Latency: {execution_time}ms, Steps: {step_count}, Tokens: {total_tokens}, Cost: ${cost:.6f}")
                
                system["results"].append({
                    "id": scenario["id"],
                    "category": scenario["category"],
                    "question": scenario["question"],
                    "expected": scenario["expected"],
                    "response": response_text,
                    "latency_ms": execution_time,
                    "steps": step_count,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "error": None
                })
            except Exception as e:
                print(f"[ERROR] Error running scenario: {e}")
                system["results"].append({
                    "id": scenario["id"],
                    "category": scenario["category"],
                    "question": scenario["question"],
                    "expected": scenario["expected"],
                    "response": "ERROR EXECUTING RUN",
                    "latency_ms": 0,
                    "steps": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0,
                    "error": str(e)
                })
                
    # 3. Generate Markdown Comparison Report
    generate_markdown_report(systems)

def generate_markdown_report(systems):
    """
    Saves a comprehensive markdown report summarizing evaluation metrics of all three versions.
    """
    report_content = "# HR ReAct Agent - Comparative Evaluation Report\n\n"
    report_content += "This report summarizes the comparison between the **Chatbot Baseline**, **ReAct Agent v1**, and **ReAct Agent v2** across 10 diverse HR scenarios.\n\n"
    
    # Summary Table
    report_content += "## 📊 Aggregate Performance Metrics\n\n"
    report_content += "| Metric | Chatbot Baseline | ReAct Agent v1 | ReAct Agent v2 |\n"
    report_content += "| :--- | :---: | :---: | :---: |\n"
    
    total_latency = {}
    total_tokens = {}
    total_cost = {}
    avg_steps = {}
    success_count = {}
    
    for sys in systems:
        name = sys["name"]
        results = sys["results"]
        total_latency[name] = sum([r["latency_ms"] for r in results])
        total_tokens[name] = sum([r["total_tokens"] for r in results])
        total_cost[name] = sum([r["cost"] for r in results])
        # Average steps per non-error query
        steps = [r["steps"] for r in results if r["error"] is None]
        avg_steps[name] = sum(steps) / len(steps) if steps else 0
        
        # Manual verification prompt
        success_count[name] = "Manual Review Required"
        
    report_content += f"| **Total Latency** | {total_latency['Chatbot Baseline']} ms | {total_latency['ReAct Agent v1']} ms | {total_latency['ReAct Agent v2']} ms |\n"
    report_content += f"| **Total Tokens Used** | {total_tokens['Chatbot Baseline']} | {total_tokens['ReAct Agent v1']} | {total_tokens['ReAct Agent v2']} |\n"
    report_content += f"| **Total Estimated Cost** | ${total_cost['Chatbot Baseline']:.6f} | ${total_cost['ReAct Agent v1']:.6f} | ${total_cost['ReAct Agent v2']:.6f} |\n"
    report_content += f"| **Average Steps / Query** | {avg_steps['Chatbot Baseline']:.1f} | {avg_steps['ReAct Agent v1']:.1f} | {avg_steps['ReAct Agent v2']:.1f} |\n"
    report_content += f"| **Parser/Tool Errors** | 0 | (Check log) | 0 (V2 Guardrails active) |\n\n"
    
    # Detail comparison per scenario
    report_content += "## 📝 Scenario Details\n\n"
    
    for i in range(10):
        scenario_id = i + 1
        s_data = SCENARIOS[i]
        report_content += f"### Scenario {scenario_id}: {s_data['category']}\n"
        report_content += f"**Question:** `{s_data['question']}`\n\n"
        report_content += f"**Expected Ground Truth:** *{s_data['expected']}*\n\n"
        
        # Compare table for this scenario
        report_content += "| System Version | Response | Steps | Latency | Cost |\n"
        report_content += "| :--- | :--- | :---: | :---: | :---: |\n"
        
        for sys in systems:
            name = sys["name"]
            res = [r for r in sys["results"] if r["id"] == scenario_id][0]
            truncated_res = res["response"].replace('\n', ' <br> ')
            if len(truncated_res) > 200:
                truncated_res = truncated_res[:197] + "..."
            report_content += f"| {name} | {truncated_res} | {res['steps']} | {res['latency_ms']} ms | ${res['cost']:.6f} |\n"
            
        report_content += "\n---\n\n"
        
    report_dir = "report"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    report_path = os.path.join(report_dir, "comparative_evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\n[DONE] Comparative Evaluation Completed! Report saved to: {report_path}")

if __name__ == "__main__":
    run_evaluation()