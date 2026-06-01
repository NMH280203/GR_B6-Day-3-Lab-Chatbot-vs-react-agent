import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.hr_tools import TOOLS_MAP

class ReActAgent:
    """
    A robust ReAct-style Agent that follows the Thought-Action-Observation loop.
    Supports both Version 1 (basic) and Version 2 (enhanced with retries and guardrails).
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 3, version: str = "v2"):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.version = version.lower()
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Generates the system prompt instructing the agent to follow the ReAct framework.
        Includes available tools, their descriptions, and exact format instructions.
        """
        tool_descriptions = ""
        for t in self.tools:
            tool_descriptions += f"- {t['name']}: {t['description']}\n"
            tool_descriptions += f"  Parameters: {json.dumps(t.get('parameters', {}), ensure_ascii=False)}\n"
            
        return f"""You are an advanced HR Agent for internal human resource management only.
Your allowed scope is strictly limited to HR topics such as employee profiles, departments, roles, managers, join dates, leave balances, payroll, benefits, working hours, remote work, overtime, and company HR policies.

If the user asks anything outside HR management, do not answer the external question and do not call any tool.
Instead, respond with:
Thought: The request is outside my HR management scope.
Final Answer: Xin lỗi, tôi chỉ có thể hỗ trợ các câu hỏi liên quan đến quản lý nhân sự như thông tin nhân viên, ngày phép, lương, phòng ban và chính sách HR của công ty.

You have access to the following HR tools:
{tool_descriptions}

You must solve the user's request step-by-step using the ReAct framework (Thought-Action-Observation loop).
For every step, write a Thought first, and then either an Action to call a tool, or a Final Answer to respond to the user.

Format guidelines:
To call a tool, use this exact format (output JSON in Action):
Thought: <your line of reasoning on what to do next>
Action: {{ "tool": "tool_name", "args": {{ "param_name": "param_value" }} }}

To finish and give the response to the user, use this exact format:
Thought: <your final line of reasoning explaining that you have gathered all information>
Final Answer: <your final response to the user, answering their request in detail and in Vietnamese>

Crucial rules:
1. Only answer HR management questions. Refuse all non-HR requests using the exact out-of-scope Final Answer above.
2. Do not hallucinate or make up employee records, leave balances, or salaries. Use the tools to query all HR information.
3. You can query employees by either ID (e.g. 'NV003') or name (e.g. 'Le Van C'). Tools such as get_leave_balance and calculate_payroll accept either ID or name directly. You do not need to call get_employee first if you already have the employee's name!
4. The Action must be a valid JSON object. Do not add any text after the JSON object in the Action block.
5. Keep max steps in mind. If you cannot solve it, output a Final Answer explaining what went wrong in Vietnamese.
"""

    def run(self, user_input: str) -> str:
        """
        Executes the ReAct loop logic.
        """
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "version": self.version
        })
        
        current_prompt = f"User Request: {user_input}\n"
        steps = 0
        self.history = []
        
        while steps < self.max_steps:
            steps += 1
            logger.info(f"--- ReAct Step {steps}/{self.max_steps} ---")
            
            # 1. Generate LLM Response
            response = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = response.get("content", "").strip()
            logger.info(f"LLM Response:\n{content}\n")
            
            # Append LLM output to prompt history
            current_prompt += f"\n{content}\n"
            
            # Extract Thought
            thought = ""
            thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", content, re.DOTALL)
            if thought_match:
                thought = thought_match.group(1).strip()
            else:
                thought = content
            
            # 2. Check for Final Answer
            if "Final Answer:" in content:
                final_answer_idx = content.find("Final Answer:")
                final_answer = content[final_answer_idx + 13:].strip()
                logger.log_event("AGENT_END", {"steps": steps, "status": "success"})
                self.history.append({
                    "step": steps,
                    "thought": thought,
                    "action": {"tool": "Final Answer", "args": {}},
                    "observation": final_answer
                })
                return final_answer
                
            # 3. Parse Action
            action_data = None
            parser_error = None
            try:
                action_data = self._parse_action(content)
            except Exception as e:
                parser_error = str(e)
                
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
                else:
                    logger.log_event("PARSER_ERROR", {"content": content, "error": parser_error})
                    logger.log_event("AGENT_END", {"steps": steps, "status": "parser_error"})
                    return f"Error parsing Agent Action: {parser_error}"
            
            if not action_data:
                # No action and no final answer found
                feedback = "Observation: Error: You did not specify an Action or a Final Answer. Please follow the format guidelines."
                current_prompt += f"\n{feedback}\n"
                continue
                
            # 4. Execute Action with Guardrails (V2)
            tool_name = action_data.get("tool")
            tool_args = action_data.get("args", {})
            
            logger.log_event("TOOL_CALL", {"tool": tool_name, "args": tool_args})
            
            # V2 Improvement: Guardrails for Tool Name validation
            if self.version == "v2":
                if not tool_name or tool_name not in TOOLS_MAP:
                    available_tools = ", ".join(TOOLS_MAP.keys())
                    observation = f"Observation: Error: Tool '{tool_name}' not found. Available tools are: [{available_tools}]."
                    logger.info(observation)
                    current_prompt += f"\n{observation}\n"
                    continue
                    
                # V2 Improvement: Argument Validation
                validation_error = self._validate_args(tool_name, tool_args)
                if validation_error:
                    observation = f"Observation: Error: {validation_error}"
                    logger.info(observation)
                    current_prompt += f"\n{observation}\n"
                    continue
                    
            # Execute tool
            observation_result = self._execute_tool(tool_name, tool_args)
            logger.log_event("TOOL_RESULT", {"tool": tool_name, "result": observation_result})
            
            logger.info(f"Tool Observation: {observation_result}\n")
            current_prompt += f"\nObservation: {observation_result}\n"
            
            self.history.append({
                "step": steps,
                "thought": thought,
                "action": action_data,
                "observation": observation_result
            })
            
        logger.log_event("AGENT_END", {"steps": steps, "status": "timeout"})
        return "Error: Agent exceeded the maximum number of steps without reaching a Final Answer."

    def _parse_action(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parses the JSON Action block out of the LLM response content.
        Handles nested formatting and markdown code blocks gracefully.
        """
        idx = content.find("Action:")
        if idx == -1:
            return None
            
        action_str = content[idx + 7:].strip()
        
        # Check for markdown code blocks e.g. ```json ... ```
        md_match = re.search(r"```(?:json)?\s*(.*?)\s*```", action_str, re.DOTALL)
        if md_match:
            json_str = md_match.group(1).strip()
        else:
            # Extract the raw JSON block
            start = action_str.find("{")
            end = action_str.rfind("}")
            if start != -1 and end != -1:
                json_str = action_str[start:end+1].strip()
            else:
                json_str = action_str
                
        try:
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"JSON Decode Error on string: '{json_str}'. Details: {e}")

    def _validate_args(self, tool_name: str, args: Dict[str, Any]) -> Optional[str]:
        """
        Validates arguments passed to a tool against its metadata schemas.
        """
        # Find tool metadata
        tool_meta = None
        for t in self.tools:
            if t["name"] == tool_name:
                tool_meta = t
                break
                
        if not tool_meta:
            return f"Tool '{tool_name}' metadata not found."
            
        # Check required fields
        required_params = tool_meta.get("parameters", {}).get("required", [])
        for req in required_params:
            if req not in args or args[req] is None or str(args[req]).strip() == "":
                return f"Missing required parameter '{req}' for tool '{tool_name}'."
                
        return None

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Executes a custom tool dynamically by mapping name to implementation.
        """
        if tool_name not in TOOLS_MAP:
            return f"Error: Tool '{tool_name}' is not registered."
            
        try:
            # Dynamically unpack keyword arguments
            func = TOOLS_MAP[tool_name]
            return func(**args)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"
