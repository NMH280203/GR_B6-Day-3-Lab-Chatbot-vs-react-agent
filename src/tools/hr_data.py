# Mock HR Database

EMPLOYEES = {
    "NV001": {
        "id": "NV001",
        "name": "Nguyen Van A",
        "department": "Engineering",
        "role": "Senior Software Engineer",
        "manager": "NV005",
        "join_date": "2022-03-15"
    },
    "NV002": {
        "id": "NV002",
        "name": "Tran Thi B",
        "department": "Engineering",
        "role": "Software Engineer",
        "manager": "NV001",
        "join_date": "2023-06-01"
    },
    "NV003": {
        "id": "NV003",
        "name": "Le Van C",
        "department": "Sales",
        "role": "Sales Executive",
        "manager": "NV006",
        "join_date": "2021-01-10"
    },
    "NV004": {
        "id": "NV004",
        "name": "Pham Thi D",
        "department": "HR",
        "role": "HR Specialist",
        "manager": "NV007",
        "join_date": "2020-11-01"
    },
    "NV005": {
        "id": "NV005",
        "name": "Hoang Van E",
        "department": "Engineering",
        "role": "Engineering Manager",
        "manager": "CEO",
        "join_date": "2019-05-10"
    },
    "NV006": {
        "id": "NV006",
        "name": "Vu Thi F",
        "department": "Sales",
        "role": "Sales Manager",
        "manager": "CEO",
        "join_date": "2020-02-15"
    },
    "NV007": {
        "id": "NV007",
        "name": "Do Van G",
        "department": "HR",
        "role": "HR Manager",
        "manager": "CEO",
        "join_date": "2018-08-01"
    }
}

LEAVE_BALANCES = {
    "NV001": {"annual_leave": 14, "used_leave": 4},
    "NV002": {"annual_leave": 12, "used_leave": 2},
    "NV003": {"annual_leave": 12, "used_leave": 8},  # 4 days left
    "NV004": {"annual_leave": 15, "used_leave": 5},
    "NV005": {"annual_leave": 16, "used_leave": 3},
    "NV006": {"annual_leave": 14, "used_leave": 6},
    "NV007": {"annual_leave": 18, "used_leave": 2}
}

PAYROLL = {
    # base_salary, bonus, allowance, deductions
    # NV001 has base salary 35 million, NV002 has 25 million, NV005 has 55 million
    "NV001": {"base_salary": 35000000, "bonus": 5000000, "allowance": 1000000, "deductions": 2000000},
    "NV002": {"base_salary": 25000000, "bonus": 2000000, "allowance": 1000000, "deductions": 1500000},
    "NV003": {"base_salary": 18000000, "bonus": 10000000, "allowance": 1500000, "deductions": 1000000}, # Sales team salary
    "NV004": {"base_salary": 20000000, "bonus": 0, "allowance": 1000000, "deductions": 1000000},
    "NV005": {"base_salary": 55000000, "bonus": 8000000, "allowance": 2000000, "deductions": 4000000},
    "NV006": {"base_salary": 32000000, "bonus": 15000000, "allowance": 2000000, "deductions": 2500000}, # Sales team salary
    "NV007": {"base_salary": 28000000, "bonus": 3000000, "allowance": 1500000, "deductions": 2000000}
}

POLICIES = [
    {
        "category": "Nghỉ phép (Leave Policy)",
        "content": "Mỗi nhân viên chính thức có từ 12-18 ngày nghỉ phép năm hưởng lương tùy cấp bậc. Nhân viên dưới 1 năm làm việc được nghỉ phép tối đa 1 ngày/tháng. Đơn xin nghỉ phép trên 3 ngày cần gửi trước 1 tuần và được phê duyệt bởi Quản lý trực tiếp (Manager)."
    },
    {
        "category": "Giờ làm việc (Working Hours)",
        "content": "Giờ làm việc tiêu chuẩn là 8 giờ/ngày, từ Thứ 2 đến Thứ 6. Thời gian linh hoạt bắt đầu từ 8:00 - 9:30 và kết thúc từ 17:00 - 18:30. Làm việc từ xa (Remote work) được phép tối đa 2 ngày/tuần nếu được Quản lý phê duyệt."
    },
    {
        "category": "Lương và Phúc lợi (Payroll & Benefits)",
        "content": "Lương được chi trả vào ngày cuối cùng của tháng. Lương thực nhận = Lương cơ bản + Thưởng (Bonus) + Phụ cấp (Allowance) - Các khoản khấu trừ (Deductions, ví dụ bảo hiểm xã hội, thuế thu nhập cá nhân). Tăng lương định kỳ được xem xét vào tháng 1 và tháng 7 hàng năm dựa trên KPI."
    },
    {
        "category": "Làm thêm giờ (Overtime Policy)",
        "content": "Làm thêm giờ (OT) phải được Quản lý trực tiếp đăng ký trước. Lương OT ngày thường bằng 150% lương giờ tiêu chuẩn. OT ngày cuối tuần bằng 200% lương giờ tiêu chuẩn. OT ngày lễ bằng 300% lương giờ tiêu chuẩn."
    }
]
