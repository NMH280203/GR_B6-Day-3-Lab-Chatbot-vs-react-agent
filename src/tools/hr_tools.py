from src.tools.hr_data import EMPLOYEES, LEAVE_BALANCES, PAYROLL, POLICIES
import json
import unicodedata

def strip_accents(text: str) -> str:
    """
    Removes Vietnamese accents/tones and normalizes character representation
    to support highly flexible, accent-insensitive searches.
    """
    normalized = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return stripped.replace('đ', 'd').replace('Đ', 'd').lower().strip()

def get_employee(employee_id_or_name: str) -> str:
    """Get employee details by ID or Name (supports accent-insensitive fuzzy match)."""
    employee_id_or_name = employee_id_or_name.strip()
    
    # 1. Search by exact ID (case-insensitive)
    upper_id = employee_id_or_name.upper()
    if upper_id in EMPLOYEES:
        emp = EMPLOYEES[upper_id]
        return json.dumps(emp, ensure_ascii=False)
        
    # 2. Search by Name (accent-insensitive, substring)
    query_clean = strip_accents(employee_id_or_name)
    matches = []
    for emp_id, emp in EMPLOYEES.items():
        name_clean = strip_accents(emp["name"])
        if query_clean in name_clean:
            matches.append(emp)
            
    if len(matches) == 1:
        return json.dumps(matches[0], ensure_ascii=False)
    elif len(matches) > 1:
        return f"Multiple employees found matching '{employee_id_or_name}': " + json.dumps(matches, ensure_ascii=False)
        
    return f"Error: Employee '{employee_id_or_name}' not found."

def get_leave_balance(employee_id_or_name: str) -> str:
    """Get annual leave, used leave, and remaining leave balances."""
    employee_id_or_name = employee_id_or_name.strip()
    if employee_id_or_name not in LEAVE_BALANCES:
        # Try to resolve name to ID first
        emp_res = get_employee(employee_id_or_name)
        if "Error" not in emp_res and "Multiple employees" not in emp_res:
            emp = json.loads(emp_res)
            employee_id = emp["id"]
        else:
            return f"Error: Employee '{employee_id_or_name}' not found in leave records."
    else:
        employee_id = employee_id_or_name
            
    balance = LEAVE_BALANCES[employee_id]
    emp_name = EMPLOYEES[employee_id]["name"]
    remaining = balance["annual_leave"] - balance["used_leave"]
    result = {
        "employee_id": employee_id,
        "name": emp_name,
        "annual_leave": balance["annual_leave"],
        "used_leave": balance["used_leave"],
        "remaining_leave": remaining
    }
    return json.dumps(result, ensure_ascii=False)

def calculate_payroll(employee_id_or_name: str, month: str = "this month") -> str:
    """Calculate the net take-home pay for an employee: base_salary + bonus + allowance - deductions."""
    employee_id_or_name = employee_id_or_name.strip()
    if employee_id_or_name not in PAYROLL:
        # Try to resolve name to ID first
        emp_res = get_employee(employee_id_or_name)
        if "Error" not in emp_res and "Multiple employees" not in emp_res:
            emp = json.loads(emp_res)
            employee_id = emp["id"]
        else:
            return f"Error: Employee '{employee_id_or_name}' not found in payroll records."
    else:
        employee_id = employee_id_or_name
            
    pay = PAYROLL[employee_id]
    emp_name = EMPLOYEES[employee_id]["name"]
    net_pay = pay["base_salary"] + pay["bonus"] + pay["allowance"] - pay["deductions"]
    
    result = {
        "employee_id": employee_id,
        "name": emp_name,
        "month": month,
        "base_salary": pay["base_salary"],
        "bonus": pay["bonus"],
        "allowance": pay["allowance"],
        "deductions": pay["deductions"],
        "net_salary": net_pay
    }
    return json.dumps(result, ensure_ascii=False)

def search_policy(query: str) -> str:
    """Search for HR policy guidelines using keywords."""
    query = query.lower().strip()
    matches = []
    for policy in POLICIES:
        if query in policy["category"].lower() or query in policy["content"].lower():
            matches.append(policy)
            
    if matches:
        return json.dumps(matches, ensure_ascii=False)
    return f"No policies found matching the query '{query}'."

def list_department_employees(department: str) -> str:
    """List all employees belonging to a specific department (e.g. 'Engineering', 'Sales', 'HR')."""
    department = department.strip().lower()
    matches = []
    for emp_id, emp in EMPLOYEES.items():
        if emp["department"].lower() == department:
            matches.append(emp)
            
    if matches:
        return json.dumps(matches, ensure_ascii=False)
    return f"No employees found in department '{department}'."


# Map tool name string to actual python function
TOOLS_MAP = {
    "get_employee": get_employee,
    "get_leave_balance": get_leave_balance,
    "calculate_payroll": calculate_payroll,
    "search_policy": search_policy,
    "list_department_employees": list_department_employees
}

# Metadata schemas for Agent prompts
TOOLS_METADATA = [
    {
        "name": "get_employee",
        "description": "Retrieves comprehensive employee profile details including ID, name, department, role, manager ID, and join date. Use this when you need to find an employee's ID from their name, or query their department/role/manager.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id_or_name": {
                    "type": "string",
                    "description": "The exact ID (e.g. 'NV003') or full/partial name of the employee (e.g. 'Nguyen Van A')."
                }
            },
            "required": ["employee_id_or_name"]
        }
    },
    {
        "name": "get_leave_balance",
        "description": "Retrieves the annual leave balance, used leave, and remaining leave days for a specific employee. Crucial for answering questions about remaining leaves.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id_or_name": {
                    "type": "string",
                    "description": "The employee ID (e.g. 'NV003') or employee name (e.g. 'Tran Thi B')."
                }
            },
            "required": ["employee_id_or_name"]
        }
    },
    {
        "name": "calculate_payroll",
        "description": "Calculates the net monthly salary (take-home pay) for a specific employee. Formula: Net Salary = Base Salary + Bonus + Allowance - Deductions. Month defaults to 'this month'.",
        "parameters": {
            "type": "object",
            "properties": {
                "employee_id_or_name": {
                    "type": "string",
                    "description": "The employee ID (e.g. 'NV003') or employee name (e.g. 'Nguyen Van A')."
                },
                "month": {
                    "type": "string",
                    "description": "Optional month identifier, e.g. 'this month', 'June'."
                }
            },
            "required": ["employee_id_or_name"]
        }
    },
    {
        "name": "search_policy",
        "description": "Searches and retrieves company policies matching the keyword query (e.g., leave, remote work, OT, working hours, bonus).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keyword search query (e.g. 'remote', 'overtime', ' nghỉ phép')."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_department_employees",
        "description": "Lists all employees belonging to a specific department. Valid departments are: 'Engineering', 'Sales', 'HR'.",
        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "The department name (e.g., 'Engineering', 'Sales', 'HR')."
                }
            },
            "required": ["department"]
        }
    }
]
