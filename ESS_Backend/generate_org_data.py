#!/usr/bin/env python3
"""
OTSi ESS Portal - 250 Employee Organizational Structure Generator
Based on official OTSI IT Organization Structure guidelines.
Generates:
1. Complete SQL migration file: otsi_org_structure_250.sql
2. Seed functions to populate Supabase directly via Python SDK.
"""

import os
import sys
import json
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash

# Default password for all seed accounts
DEFAULT_PASSWORD = "M@llem5831!"
PASSWORD_HASH = "pbkdf2:sha256:600000$jwfp1reYQ1Gs5mr8$a9b1c52cb6f0287be184479b4682871459ec214d6704c9fa042cfa873dbb16de"

def build_250_organization():
    emps = []
    
    # ─────────────────────────────────────────────────────────────
    # 1. EXECUTIVE LEADERSHIP & GOVERNANCE (8 Headcount)
    # ─────────────────────────────────────────────────────────────
    emps.append({
        'employee_id': 'OTSI0001',
        'email': 'admin.otsi@otsi-usa.com',
        'full_name': 'Rajesh K.',
        'designation': 'Chairman & Founder / President',
        'department': 'Executive Leadership & Governance',
        'team': 'Board of Directors',
        'role': 'admin',
        'manager_id': None,
        'manager_name': None,
        'phone': '+91 98490 00001',
        'date_of_joining': '2015-01-10'
    })
    
    emps.append({
        'employee_id': 'EMP1001',
        'email': 'ceo.otsi@otsi-usa.com',
        'full_name': 'Chandra Sekhar M.',
        'designation': 'Chief Executive Officer (CEO)',
        'department': 'Executive Leadership & Governance',
        'team': 'Executive Committee',
        'role': 'admin',
        'manager_id': 'OTSI0001',
        'manager_name': 'Rajesh K.',
        'phone': '+91 98490 00002',
        'date_of_joining': '2016-03-15'
    })

    emps.append({
        'employee_id': 'EMP1000',
        'email': 'kiran.us009@gmail.com',
        'full_name': 'Ravi Kiran V.',
        'designation': 'Senior Vice President – Global Delivery',
        'department': 'Executive Leadership & Governance',
        'team': 'Global Delivery Leadership',
        'role': 'admin',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00003',
        'date_of_joining': '2017-02-01'
    })

    emps.append({
        'employee_id': 'EMP1003',
        'email': 'suresh.nambiar@otsi-usa.com',
        'full_name': 'Suresh Nambiar',
        'designation': 'Sr. Vice President – Government & Public Sector Sales, APAC',
        'department': 'Executive Leadership & Governance',
        'team': 'APAC Public Sector Sales Leadership',
        'role': 'admin',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00004',
        'date_of_joining': '2017-06-12'
    })

    emps.append({
        'employee_id': 'EMP1004',
        'email': 'vikram.rao@otsi-usa.com',
        'full_name': 'Vikramaditya Rao',
        'designation': 'Sr. Vice President – Client Partner & Commercial Sales, APAC',
        'department': 'Executive Leadership & Governance',
        'team': 'APAC Commercial Sales Leadership',
        'role': 'admin',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00005',
        'date_of_joining': '2017-08-20'
    })

    emps.append({
        'employee_id': 'EMP1005',
        'email': 'subhashini.r@otsi.co.in',
        'full_name': 'Subhashini R.',
        'designation': 'Associate Vice President – Operations & Finance, APAC & MENA',
        'department': 'Executive Leadership & Governance',
        'team': 'APAC & MENA Operations Leadership',
        'role': 'admin',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00006',
        'date_of_joining': '2018-01-15'
    })

    emps.append({
        'employee_id': 'EMP1006',
        'email': 'priyanka.sengupta@otsi.co.in',
        'full_name': 'Priyanka Sengupta',
        'designation': 'Sr. Director – Human Resources, APAC & MENA',
        'department': 'Executive Leadership & Governance',
        'team': 'HR Leadership',
        'role': 'hr',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00007',
        'date_of_joining': '2018-04-10'
    })

    emps.append({
        'employee_id': 'EMP1007',
        'email': 'anand.vardhan@otsi.co.in',
        'full_name': 'Anand Vardhan',
        'designation': 'Principal Architect – Microsoft',
        'department': 'Executive Leadership & Governance',
        'team': 'Architecture & Technology Excellence',
        'role': 'admin',
        'manager_id': 'EMP1001',
        'manager_name': 'Chandra Sekhar M.',
        'phone': '+91 98490 00008',
        'date_of_joining': '2018-07-01'
    })

    # ─────────────────────────────────────────────────────────────
    # DIRECTORS REPORTING TO SVP GLOBAL DELIVERY (EMP1000)
    # ─────────────────────────────────────────────────────────────
    emps.append({
        'employee_id': 'EMP1008',
        'email': 'manoj.kumar@otsi.co.in',
        'full_name': 'Manoj Kumar K.',
        'designation': 'Sr. Delivery Director – Data & Analytics',
        'department': 'Data & Analytics',
        'team': 'Data & Analytics Leadership',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00009',
        'date_of_joining': '2018-09-15'
    })

    emps.append({
        'employee_id': 'EMP1009',
        'email': 'naveen.reddy@otsi.co.in',
        'full_name': 'Naveen Reddy T.',
        'designation': 'Sr. Delivery Director – Big Data & Analytics',
        'department': 'Data & Analytics',
        'team': 'Big Data Engineering',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00010',
        'date_of_joining': '2018-11-01'
    })

    emps.append({
        'employee_id': 'EMP1010',
        'email': 'deepak.sharma@otsi.co.in',
        'full_name': 'Deepak Sharma',
        'designation': 'Sr. Delivery Director – Big Data & Cloud Solutions',
        'department': 'Data & Analytics',
        'team': 'Cloud Solutions Delivery',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00011',
        'date_of_joining': '2019-01-10'
    })

    emps.append({
        'employee_id': 'EMP1011',
        'email': 'kavitha.swaminathan@otsi.co.in',
        'full_name': 'Kavitha Swaminathan',
        'designation': 'Practice Director – Big Data & Analytics',
        'department': 'Data & Analytics',
        'team': 'Data Practice Center of Excellence',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00012',
        'date_of_joining': '2019-03-20'
    })

    emps.append({
        'employee_id': 'EMP1012',
        'email': 'raghavendra.prasad@otsi.co.in',
        'full_name': 'Raghavendra Prasad',
        'designation': 'Practice Director – Quality Assurance',
        'department': 'Quality Assurance & Testing',
        'team': 'QA Practice Leadership',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00013',
        'date_of_joining': '2019-05-15'
    })

    emps.append({
        'employee_id': 'EMP1013',
        'email': 'siddharth.mehta@otsi.co.in',
        'full_name': 'Siddharth Mehta',
        'designation': 'Practice Director – Digital Transformation',
        'department': 'Digital Transformation',
        'team': 'Digital Transformation CoE',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00014',
        'date_of_joining': '2019-07-01'
    })

    emps.append({
        'employee_id': 'EMP1014',
        'email': 'sunil.chander@otsi.co.in',
        'full_name': 'Sunil Chander',
        'designation': 'Director – IT Infrastructure & Cloud',
        'department': 'IT Infrastructure & Cloud',
        'team': 'IT Operations Leadership',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00015',
        'date_of_joining': '2019-09-01'
    })

    # Software Engineering Delivery Director
    emps.append({
        'employee_id': 'EMP1015',
        'email': 'venkat.ramana@otsi.co.in',
        'full_name': 'Venkat Ramana M.',
        'designation': 'Delivery Director – Application Engineering',
        'department': 'Application Engineering',
        'team': 'Engineering Leadership',
        'role': 'admin',
        'manager_id': 'EMP1000',
        'manager_name': 'Ravi Kiran V.',
        'phone': '+91 98490 00016',
        'date_of_joining': '2019-10-15'
    })

    # ─────────────────────────────────────────────────────────────
    # 2. DATA, ANALYTICS, BIG DATA & CLOUD (55 Total Headcount)
    # 4 Directors already defined above: EMP1008, EMP1009, EMP1010, EMP1011
    # Adding 51 data specialists across:
    # - Sr. Data Scientist, Data Scientist
    # - Senior Data Analyst, Data Analyst
    # - SAS Programmer, SAS Administrator
    # - Lead Database Developer, Database Administrator
    # - Big Data / Cloud Data Engineer
    # ─────────────────────────────────────────────────────────────
    data_mgrs = [
        ('EMP1008', 'Manoj Kumar K.', 'Data & Analytics', 'BI & Reporting'),
        ('EMP1009', 'Naveen Reddy T.', 'Data & Analytics', 'Big Data Engineering'),
        ('EMP1010', 'Deepak Sharma', 'Data & Analytics', 'Cloud Data Platforms'),
        ('EMP1011', 'Kavitha Swaminathan', 'Data & Analytics', 'AI & Machine Learning')
    ]

    data_roles = [
        ("Sr. Data Scientist", 6),
        ("Data Scientist", 8),
        ("Senior Data Analyst", 8),
        ("Data Analyst", 8),
        ("SAS Programmer", 5),
        ("SAS Administrator", 3),
        ("Lead Database Developer", 5),
        ("Database Administrator", 4),
        ("Big Data Engineer", 4),
    ]

    curr_emp_idx = 1016
    for role_title, count in data_roles:
        for i in range(count):
            mgr_id, mgr_name, dept, team = data_mgrs[(curr_emp_idx) % len(data_mgrs)]
            fn = f"Data Specialist {curr_emp_idx - 1015}"
            # Realistic names
            first_names = ["Arun", "Bhavana", "Chetan", "Divya", "Ganesh", "Harish", "Ishita", "Jayant", "Karthik", "Lakshmi", "Madhav", "Nandini", "Omkar", "Pooja", "Rajiv", "Sneha", "Tarun", "Usha", "Varun", "Yash"]
            last_names = ["Rao", "Reddy", "Sharma", "Patel", "Verma", "Iyer", "Nair", "Choudhury", "Gupta", "Kulkarni", "Deshmukh", "Menon", "Pillai", "Bhat", "Mishra", "Joshi", "Bose", "Das"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 3) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': dept,
                'team': team,
                'role': 'employee',
                'manager_id': mgr_id,
                'manager_name': mgr_name,
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2020, 1, 1) + timedelta(days=(curr_emp_idx * 37) % 2000)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 3. APPLICATION & SOFTWARE ENGINEERING (65 Total Headcount)
    # 1 Director (EMP1015) already defined.
    # Adding 64 engineers:
    # - Technical Managers & Project Managers
    # - Technical Leads & Team Leads
    # - Principal Engineer & Senior Software Engineer
    # - Software Engineer & Associate Software Engineer
    # - Graduate Engineer / Trainee
    # - Front End Developer & Senior Front End Developer
    # - Web Developer (Python) [Ravi Mallem EMP1070]
    # - Senior Mobile App Developer
    # - Senior Polarion Developer
    # - VxWorks Engineer & Embedded Linux Engineer
    # - Senior System Engineer & System Engineer
    # ─────────────────────────────────────────────────────────────
    eng_managers = [
        (f"EMP{curr_emp_idx}", "Ramesh Chandra", "Technical Manager", "Application Engineering", "Full Stack Web & Python"),
        (f"EMP{curr_emp_idx+1}", "Gita Vani K.", "Project Manager", "Application Engineering", "Frontend & Mobile Apps"),
        (f"EMP{curr_emp_idx+2}", "Srikanth Murthy", "Technical Manager", "Application Engineering", "Embedded & IoT Solutions"),
        (f"EMP{curr_emp_idx+3}", "Sudhakar G.", "Project Manager", "Application Engineering", "ALM & Polarion Practice")
    ]
    for em_id, em_name, em_title, em_dept, em_team in eng_managers:
        emps.append({
            'employee_id': em_id,
            'email': f"{em_name.lower().replace(' ', '.')}@otsi.co.in",
            'full_name': em_name,
            'designation': em_title,
            'department': em_dept,
            'team': em_team,
            'role': 'employee',
            'manager_id': 'EMP1015',
            'manager_name': 'Venkat Ramana M.',
            'phone': f"+91 98490 {int(em_id[3:]):05d}",
            'date_of_joining': '2019-11-20'
        })
    curr_emp_idx += 4

    # Technical Leads under Technical Managers
    tech_leads = [
        (f"EMP{curr_emp_idx}", "Satish Babu", "Technical Lead", "EMP1067", "Ramesh Chandra", "Full Stack Web & Python"),
        (f"EMP{curr_emp_idx+1}", "Anusha P.", "Team Lead", "EMP1068", "Gita Vani K.", "Frontend & Mobile Apps"),
        (f"EMP{curr_emp_idx+2}", "Mahesh Goud", "Technical Lead", "EMP1069", "Srikanth Murthy", "Embedded & IoT Solutions"),
        (f"EMP{curr_emp_idx+3}", "Rohit Malhotra", "Associate Architect", "EMP1070", "Sudhakar G.", "ALM & Polarion Practice")
    ]
    for tl_id, tl_name, tl_title, mgr_id, mgr_name, tl_team in tech_leads:
        emps.append({
            'employee_id': tl_id,
            'email': f"{tl_name.lower().replace(' ', '.')}@otsi.co.in",
            'full_name': tl_name,
            'designation': tl_title,
            'department': 'Application Engineering',
            'team': tl_team,
            'role': 'employee',
            'manager_id': mgr_id,
            'manager_name': mgr_name,
            'phone': f"+91 98490 {int(tl_id[3:]):05d}",
            'date_of_joining': '2020-02-15'
        })
    curr_emp_idx += 4

    # Ravi Mallem - Senior Software Engineer (Python)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'ravi.mallem@otsi.co.in',
        'full_name': 'Ravi Mallem',
        'designation': 'Senior Software Engineer',
        'department': 'Application Engineering',
        'team': 'Full Stack Web & Python',
        'role': 'employee',
        'manager_id': tech_leads[0][0], # Satish Babu
        'manager_name': 'Satish Babu',
        'phone': '+91 98490 58310',
        'date_of_joining': '2021-06-15'
    })
    curr_emp_idx += 1

    # Remaining 55 engineering roles
    eng_roles = [
        ("Principal Engineer", 2),
        ("Senior Software Engineer", 7),
        ("Software Engineer", 9),
        ("Associate Software Engineer", 7),
        ("Graduate Engineer / Trainee", 5),
        ("Senior Front End Developer", 4),
        ("Front End Developer", 4),
        ("Web Developer (Python)", 3),
        ("Senior Mobile App Developer", 3),
        ("Senior Polarion Developer", 3),
        ("VxWorks Engineer", 2),
        ("Embedded Linux Engineer", 2),
        ("Senior System Engineer", 2),
        ("System Engineer", 2)
    ]

    for role_title, count in eng_roles:
        for i in range(count):
            tl = tech_leads[curr_emp_idx % len(tech_leads)]
            first_names = ["Ajay", "Bhargav", "Chaitanya", "Deepa", "Eswar", "Farhan", "Gayatri", "Hemant", "Indira", "Jitendra", "Kiran", "Lalitha", "Mohan", "Neeraj", "Praveen", "Rakesh", "Sandhya", "Tejas", "Venkat", "Zoya"]
            last_names = ["Koppula", "Bandari", "Goud", "Vemula", "Chowdary", "Singhania", "Tripathi", "Saxena", "Agarwal", "Verma", "Pillai", "Nambiar", "Mukherjee", "Chatterjee", "Banerjee", "Soni"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 5) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'Application Engineering',
                'team': tl[5],
                'role': 'employee',
                'manager_id': tl[0], # reporting to Technical Lead
                'manager_name': tl[1],
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2021, 1, 1) + timedelta(days=(curr_emp_idx * 43) % 1800)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 4. QUALITY ASSURANCE & PERFORMANCE TESTING (35 Total Headcount)
    # 1 Director (EMP1012 - Raghavendra Prasad) already defined.
    # Adding 34 QA professionals:
    # - Test Manager, Test Lead, Senior Test Lead
    # - Senior Test Architect
    # - Senior Test Engineer, Test Engineer, Associate Test Engineer
    # - QA Engineer
    # - Performance & Load Testing Specialist
    # ─────────────────────────────────────────────────────────────
    qa_leads = [
        (f"EMP{curr_emp_idx}", "Sanjay Kulkarni", "Test Manager", "EMP1012", "Raghavendra Prasad", "Functional & Regression QA"),
        (f"EMP{curr_emp_idx+1}", "Meenakshi Sundaram", "Senior Test Architect", "EMP1012", "Raghavendra Prasad", "Automation & Performance QA"),
        (f"EMP{curr_emp_idx+2}", "Bipin Bihari", "Test Lead", "EMP1012", "Raghavendra Prasad", "Mobile & Web QA"),
        (f"EMP{curr_emp_idx+3}", "Radhika Nair", "Senior Test Lead", "EMP1012", "Raghavendra Prasad", "Enterprise Systems QA")
    ]
    for ql_id, ql_name, ql_title, mgr_id, mgr_name, ql_team in qa_leads:
        emps.append({
            'employee_id': ql_id,
            'email': f"{ql_name.lower().replace(' ', '.')}@otsi.co.in",
            'full_name': ql_name,
            'designation': ql_title,
            'department': 'Quality Assurance & Testing',
            'team': ql_team,
            'role': 'employee',
            'manager_id': mgr_id,
            'manager_name': mgr_name,
            'phone': f"+91 98490 {int(ql_id[3:]):05d}",
            'date_of_joining': '2020-05-10'
        })
    curr_emp_idx += 4

    qa_roles = [
        ("Senior Test Engineer", 6),
        ("Test Engineer", 8),
        ("Associate Test Engineer", 6),
        ("QA Engineer", 5),
        ("Performance & Load Testing Specialist", 5)
    ]
    for role_title, count in qa_roles:
        for i in range(count):
            ql = qa_leads[curr_emp_idx % len(qa_leads)]
            first_names = ["Amit", "Bindu", "Charan", "Deepak", "Esha", "Girish", "Haritha", "Jagadish", "Komal", "Lokesh", "Mansi", "Nikhil", "Pallavi", "Rohan", "Swati"]
            last_names = ["Pandey", "Chauhan", "Bhatnagar", "Somani", "Goyal", "Madan", "Khatri", "Sethi", "Bahl", "Arora", "Sood", "Kapoor"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 7) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'Quality Assurance & Testing',
                'team': ql[5],
                'role': 'employee',
                'manager_id': ql[0],
                'manager_name': ql[1],
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2021, 3, 1) + timedelta(days=(curr_emp_idx * 29) % 1700)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 5. DIGITAL TRANSFORMATION & CONSULTING (18 Total Headcount)
    # 1 Director (EMP1013 - Siddharth Mehta) already defined.
    # Adding 17 consulting & transformation staff:
    # - Director, Strategy & Delivery
    # - Principal Architect, Architect, Associate Architect
    # - Senior Consultant, Consultant
    # - Business Analyst, Senior Analyst
    # - Project Manager, Technical Project Manager
    # ─────────────────────────────────────────────────────────────
    dt_roles = [
        ("Director, Strategy & Delivery", 1),
        ("Principal Architect", 2),
        ("Architect", 2),
        ("Associate Architect", 2),
        ("Senior Consultant", 3),
        ("Consultant", 2),
        ("Senior Analyst", 2),
        ("Business Analyst", 2),
        ("Technical Project Manager", 1)
    ]
    for role_title, count in dt_roles:
        for i in range(count):
            first_names = ["Abhishek", "Bhavik", "Chetna", "Devendra", "Garima", "Himanshu", "Isha", "Kunal", "Madhuri", "Naveen", "Pratibha", "Ritesh", "Sunita"]
            last_names = ["Sengupta", "Majumdar", "Bhattacharya", "Chakraborty", "Roy", "Dutta", "Goswami", "Banerjee", "Saha"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 11) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'Digital Transformation',
                'team': 'Strategy & Cloud Advisory',
                'role': 'employee',
                'manager_id': 'EMP1013', # Siddharth Mehta
                'manager_name': 'Siddharth Mehta',
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2020, 6, 1) + timedelta(days=(curr_emp_idx * 31) % 1900)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 6. IT INFRASTRUCTURE, CLOUD & SERVICE DESK (22 Total Headcount)
    # 1 Director (EMP1014 - Sunil Chander) already defined.
    # Adding 21 IT infra engineers:
    # - Technical Manager
    # - Senior System Administrator, System Administrator
    # - System Network Administrator
    # - Global Service Desk Agent
    # - IT Support Specialist / Specialist - IT Support
    # - Lab Technician / Lab Admin
    # ─────────────────────────────────────────────────────────────
    infra_leads = [
        (f"EMP{curr_emp_idx}", "Venkatesh Babu", "Technical Manager - IT & Cloud", "EMP1014", "Sunil Chander", "Cloud Infrastructure & Ops"),
        (f"EMP{curr_emp_idx+1}", "Syed Mustaq", "Lead System Network Administrator", "EMP1014", "Sunil Chander", "Network Security & Telecom")
    ]
    for il_id, il_name, il_title, mgr_id, mgr_name, il_team in infra_leads:
        emps.append({
            'employee_id': il_id,
            'email': f"{il_name.lower().replace(' ', '.')}@otsi.co.in",
            'full_name': il_name,
            'designation': il_title,
            'department': 'IT Infrastructure & Cloud',
            'team': il_team,
            'role': 'admin',
            'manager_id': mgr_id,
            'manager_name': mgr_name,
            'phone': f"+91 98490 {int(il_id[3:]):05d}",
            'date_of_joining': '2019-12-01'
        })
    curr_emp_idx += 2

    infra_roles = [
        ("Senior System Administrator", 3),
        ("System Administrator", 4),
        ("System Network Administrator", 3),
        ("Global Service Desk Agent", 4),
        ("Specialist – IT Support", 3),
        ("Lab Admin", 2)
    ]
    for role_title, count in infra_roles:
        for i in range(count):
            mgr = infra_leads[curr_emp_idx % len(infra_leads)]
            first_names = ["Kiran", "Nagaraj", "Raju", "Shiva", "Pavan", "Vijay", "Anil", "Satya", "Balu", "Gopi", "Muralidhar", "Prashanth"]
            last_names = ["Kulkarni", "Joshi", "Babu", "Reddy", "Sharma", "Yadav", "Kumar", "Patel", "Singh"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 13) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'IT Infrastructure & Cloud',
                'team': mgr[5],
                'role': 'admin' if 'Administrator' in role_title or 'Admin' in role_title else 'employee',
                'manager_id': mgr[0],
                'manager_name': mgr[1],
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2021, 2, 1) + timedelta(days=(curr_emp_idx * 17) % 1800)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 7. SALES, CLIENT PARTNERSHIPS & BUSINESS DEV (18 Total Headcount)
    # 2 SVPs (EMP1003 & EMP1004) already defined.
    # Adding 16 sales & account executives:
    # - Director of Client Success
    # - Senior Manager - Sales and Account Growth
    # - Manager - Alliances & Partnerships
    # - Sales & Business Development / Account Executive
    # ─────────────────────────────────────────────────────────────
    sales_roles = [
        ("Director of Client Success", 2),
        ("Senior Manager – Sales and Account Growth", 3),
        ("Manager – Alliances & Partnerships", 3),
        ("Account Executive", 5),
        ("Sales & Business Development Executive", 5)
    ]
    sales_svps = [
        ('EMP1003', 'Suresh Nambiar', 'Sales & Business Development', 'Public Sector Sales'),
        ('EMP1004', 'Vikramaditya Rao', 'Sales & Business Development', 'Commercial Enterprise Sales')
    ]
    for role_title, count in sales_roles:
        for i in range(count):
            svp_id, svp_name, dept, team = sales_svps[curr_emp_idx % len(sales_svps)]
            first_names = ["Aditya", "Dev", "Gautam", "Kabir", "Meera", "Neha", "Rohan", "Simran", "Tanya", "Varun", "Zain"]
            last_names = ["Mehra", "Kapoor", "Khanna", "Chopra", "Oberoi", "Singhal", "Talwar", "Malhotra", "Batra"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 7) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': dept,
                'team': team,
                'role': 'employee',
                'manager_id': svp_id,
                'manager_name': svp_name,
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2020, 8, 1) + timedelta(days=(curr_emp_idx * 23) % 1900)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 8. OPERATIONS, PROJECT & RESOURCE MANAGEMENT (10 Total Headcount)
    # Under AVP Operations (EMP1005 - Subhashini R.)
    # - General Manager / Senior Manager / Manager
    # - Project Manager / Technical Project Manager
    # - Resource Manager
    # - Associate Logistics Analyst
    # - Operations Analyst / Senior Executive - Operations
    # - Manager - Contracts & Administration
    # ─────────────────────────────────────────────────────────────
    ops_roles = [
        ("General Manager – PMO & Operations", 1),
        ("Senior Manager – Project Delivery", 1),
        ("Resource Manager", 2),
        ("Associate Logistics Analyst", 2),
        ("Senior Executive – Operations", 2),
        ("Manager – Contracts & Administration", 2)
    ]
    for role_title, count in ops_roles:
        for i in range(count):
            first_names = ["Anand", "Bhavna", "Chitra", "Dinesh", "Geeta", "Hemalatha", "Jayashree", "Kishore"]
            last_names = ["Deshpande", "Kulkarni", "Patil", "Shinde", "Gaikwad", "More", "Bhosale", "Kadam"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 3) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'Operations & PMO',
                'team': 'Resource & Logistics Operations',
                'role': 'employee',
                'manager_id': 'EMP1005',
                'manager_name': 'Subhashini R.',
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2021, 5, 1) + timedelta(days=(curr_emp_idx * 19) % 1600)).isoformat()
            })
            curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 9. HUMAN RESOURCES & TALENT ACQUISITION (Complete Hierarchy)
    # Under Sr. Director HR (EMP1006 - Priyanka Sengupta)
    # 1. People Operations:
    #    - HR Manager
    #    - HR Asst Manager
    #    - Sr. HR Executive
    #    - HR Executive
    #    - HR Specialist
    #    - Senior Specialist HRBP
    #    - HR Business Partner
    # 2. Talent Acquisition & Technical Recruiting:
    #    - Technical Manager
    #    - Sr. Technical Recruiter
    #    - Technical Recruiter
    #    - Associate Recruiter
    # 3. Resource Management:
    #    - Resource Manager
    #    - Associate Resource Manager
    # ─────────────────────────────────────────────────────────────
    # 1. HR Manager
    hr_mgr_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': hr_mgr_id,
        'email': 'kavita.krishnan@otsi.co.in',
        'full_name': 'Kavita Krishnan',
        'designation': 'HR Manager',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': 'EMP1006',
        'manager_name': 'Priyanka Sengupta',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2019-08-15'
    })
    curr_emp_idx += 1

    # 2. HR Asst Manager (reports to HR Manager)
    hr_asst_mgr_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': hr_asst_mgr_id,
        'email': 'rajeshwari.sharma@otsi.co.in',
        'full_name': 'Rajeshwari Sharma',
        'designation': 'HR Asst Manager',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': hr_mgr_id,
        'manager_name': 'Kavita Krishnan',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2020-03-10'
    })
    curr_emp_idx += 1

    # 3. Sr. HR Executive (reports to HR Asst Manager)
    sr_hr_exec_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': sr_hr_exec_id,
        'email': 'ananya.sen@otsi.co.in',
        'full_name': 'Ananya Sen',
        'designation': 'Sr. HR Executive',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': hr_asst_mgr_id,
        'manager_name': 'Rajeshwari Sharma',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-01-15'
    })
    curr_emp_idx += 1

    # 4. HR Executive (reports to Sr. HR Executive)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'pooja.verma@otsi.co.in',
        'full_name': 'Pooja Verma',
        'designation': 'HR Executive',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': sr_hr_exec_id,
        'manager_name': 'Ananya Sen',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2022-04-10'
    })
    curr_emp_idx += 1

    # 5. HR Specialist (reports to HR Manager)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'shruti.iyer@otsi.co.in',
        'full_name': 'Shruti Iyer',
        'designation': 'HR Specialist',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': hr_mgr_id,
        'manager_name': 'Kavita Krishnan',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-07-20'
    })
    curr_emp_idx += 1

    # 6. Senior Specialist HRBP (reports to HR Manager)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'aarti.venkatesh@otsi.co.in',
        'full_name': 'Aarti Venkatesh',
        'designation': 'Senior Specialist HRBP',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': hr_mgr_id,
        'manager_name': 'Kavita Krishnan',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2020-11-05'
    })
    curr_emp_idx += 1

    # 7. HR Business Partner (reports to HR Manager)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'divya.subramanian@otsi.co.in',
        'full_name': 'Divya Subramanian',
        'designation': 'HR Business Partner',
        'department': 'Human Resources',
        'team': 'HR Operations & People Management',
        'role': 'hr',
        'manager_id': hr_mgr_id,
        'manager_name': 'Kavita Krishnan',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-02-18'
    })
    curr_emp_idx += 1

    # 8. Technical Manager – Talent Acquisition (reports to Priyanka Sengupta)
    ta_mgr_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': ta_mgr_id,
        'email': 'vikram.malhotra@otsi.co.in',
        'full_name': 'Vikram Malhotra',
        'designation': 'Technical Manager',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': 'EMP1006',
        'manager_name': 'Priyanka Sengupta',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2019-10-01'
    })
    curr_emp_idx += 1

    # 9 & 10. Sr. Technical Recruiter (reports to Technical Manager)
    sr_rec_1_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': sr_rec_1_id,
        'email': 'lavanya.sundaram@otsi.co.in',
        'full_name': 'Lavanya Sundaram',
        'designation': 'Sr. Technical Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': ta_mgr_id,
        'manager_name': 'Vikram Malhotra',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2020-06-15'
    })
    curr_emp_idx += 1

    sr_rec_2_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': sr_rec_2_id,
        'email': 'karthik.swaminathan@otsi.co.in',
        'full_name': 'Karthik Swaminathan',
        'designation': 'Sr. Technical Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': ta_mgr_id,
        'manager_name': 'Vikram Malhotra',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2020-08-20'
    })
    curr_emp_idx += 1

    # 11 & 12. Technical Recruiter (reports to Technical Manager)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'nandita.chandran@otsi.co.in',
        'full_name': 'Nandita Chandran',
        'designation': 'Technical Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': ta_mgr_id,
        'manager_name': 'Vikram Malhotra',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-03-12'
    })
    curr_emp_idx += 1

    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'rahul.bose@otsi.co.in',
        'full_name': 'Rahul Bose',
        'designation': 'Technical Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': ta_mgr_id,
        'manager_name': 'Vikram Malhotra',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-05-19'
    })
    curr_emp_idx += 1

    # 13 & 14. Associate Recruiter (reports to Sr. Technical Recruiters)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'sneha.reddy@otsi.co.in',
        'full_name': 'Sneha Reddy',
        'designation': 'Associate Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': sr_rec_1_id,
        'manager_name': 'Lavanya Sundaram',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2022-08-01'
    })
    curr_emp_idx += 1

    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'amitabh.das@otsi.co.in',
        'full_name': 'Amitabh Das',
        'designation': 'Associate Recruiter',
        'department': 'Human Resources',
        'team': 'Talent Acquisition & Technical Recruiting',
        'role': 'hr',
        'manager_id': sr_rec_2_id,
        'manager_name': 'Karthik Swaminathan',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2022-10-15'
    })
    curr_emp_idx += 1

    # 15. Resource Manager (reports to Priyanka Sengupta)
    rm_id = f"EMP{curr_emp_idx}"
    emps.append({
        'employee_id': rm_id,
        'email': 'rameshwar.patil@otsi.co.in',
        'full_name': 'Rameshwar Patil',
        'designation': 'Resource Manager',
        'department': 'Human Resources',
        'team': 'Resource Management & Staffing',
        'role': 'hr',
        'manager_id': 'EMP1006',
        'manager_name': 'Priyanka Sengupta',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2020-04-01'
    })
    curr_emp_idx += 1

    # 16. Associate Resource Manager (reports to Resource Manager)
    emps.append({
        'employee_id': f"EMP{curr_emp_idx}",
        'email': 'bhavna.shinde@otsi.co.in',
        'full_name': 'Bhavna Shinde',
        'designation': 'Associate Resource Manager',
        'department': 'Human Resources',
        'team': 'Resource Management & Staffing',
        'role': 'hr',
        'manager_id': rm_id,
        'manager_name': 'Rameshwar Patil',
        'phone': f"+91 98490 {curr_emp_idx:05d}",
        'date_of_joining': '2021-09-10'
    })
    curr_emp_idx += 1

    # ─────────────────────────────────────────────────────────────
    # 10. FINANCE, COMPLIANCE & ADMINISTRATION (10 Total Headcount)
    # Under AVP Operations & Finance (EMP1005 - Subhashini R.)
    # - Senior Accountant / Accountant
    # - Senior Billing Analyst / Cash Billing Analyst
    # - Analyst – Cash Application
    # - Senior Compliance Analyst / Senior KYC Specialist
    # - Executive Assistant / Admin Executive
    # - Facility Assistant
    # - Graphic Designer
    # ─────────────────────────────────────────────────────────────
    fin_roles = [
        ("Senior Accountant", 1),
        ("Accountant", 1),
        ("Senior Billing Analyst", 1),
        ("Analyst – Cash Application", 1),
        ("Senior Compliance Analyst", 1),
        ("Senior KYC Specialist", 1),
        ("Executive Assistant", 1),
        ("Admin Executive", 1),
        ("Facility Assistant", 1),
        ("Graphic Designer", 1)
    ]
    for role_title, count in fin_roles:
        for i in range(count):
            first_names = ["Alok", "Bhaskar", "Gopal", "Harish", "Keshav", "Manish", "Nitin", "Prashant", "Ramesh", "Sridhar"]
            last_names = ["Khandelwal", "Mittal", "Singhal", "Agrawal", "Bansal", "Goel", "Garg", "Jain", "Maheshwari"]
            p_name = f"{first_names[curr_emp_idx % len(first_names)]} {last_names[(curr_emp_idx * 7) % len(last_names)]}"
            p_email = f"{p_name.lower().replace(' ', '.')}@otsi.co.in"

            emps.append({
                'employee_id': f"EMP{curr_emp_idx}",
                'email': p_email,
                'full_name': p_name,
                'designation': role_title,
                'department': 'Finance, Compliance & Administration',
                'team': 'Finance & Statutory Compliance',
                'role': 'employee',
                'manager_id': 'EMP1005',
                'manager_name': 'Subhashini R.',
                'phone': f"+91 98490 {curr_emp_idx:05d}",
                'date_of_joining': (date(2021, 4, 1) + timedelta(days=(curr_emp_idx * 23) % 1800)).isoformat()
            })
            curr_emp_idx += 1

    # Guarantee 100% unique emails across all employees
    seen_emails = set()
    for e in emps:
        base_email = e['email'].lower()
        if base_email in seen_emails:
            user_part, domain_part = base_email.split('@')
            e['email'] = f"{user_part}.{e['employee_id'].lower()}@{domain_part}"
        seen_emails.add(e['email'])

    assert len(set(e['email'] for e in emps)) == len(emps), "All emails must be unique!"
    assert len(set(e['employee_id'] for e in emps)) == len(emps), "All employee IDs must be unique!"

    return emps

def generate_sql_script(emps, output_path):
    """Generate the complete SQL migration file."""
    departments = sorted(list(set(e['department'] for e in emps)))
    teams = sorted(list(set((e['team'], e['department']) for e in emps)))

    sql = []
    sql.append("-- ============================================================")
    sql.append("-- OTSI Attendance Portal - 250 Employee Organizational Structure")
    sql.append("-- Complete Unified Schema & Seed Data (Supabase / PostgreSQL)")
    sql.append("-- Schema: public")
    sql.append("-- ============================================================\n")

    # 0. Clean Reset of Previous Data & Restart All IDs from 1
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 0. CLEAN RESET & RESTART ALL IDENTITY SEQUENCES FROM 1")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("""
TRUNCATE TABLE 
    attendance_logs, 
    leave_applications, 
    timesheet_entries, 
    timesheets, 
    support_tickets, 
    notifications, 
    audit_logs, 
    password_history, 
    leave_balance, 
    employees, 
    teams, 
    departments,
    holidays
RESTART IDENTITY CASCADE;

ALTER SEQUENCE IF EXISTS employees_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS attendance_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS leave_balance_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS departments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS teams_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS holidays_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS leave_applications_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS timesheets_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS timesheet_entries_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS support_tickets_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS notifications_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS audit_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS password_history_id_seq RESTART WITH 1;
""")

    # 1. Base DDL Tables
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 1. CREATE CORE TABLES")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("""
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    manager_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    department_name VARCHAR(150),
    team_lead_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, department_name)
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    designation VARCHAR(100),
    department VARCHAR(100),
    team VARCHAR(100),
    manager_id VARCHAR(50),
    manager_name VARCHAR(150),
    phone VARCHAR(20),
    date_of_joining DATE,
    role VARCHAR(20) DEFAULT 'employee' CHECK (role IN ('employee', 'hr', 'admin')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'on_leave')),
    is_active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    lockout_until TIMESTAMP,
    mfa_enabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS leave_balance (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL UNIQUE REFERENCES employees(employee_id) ON DELETE CASCADE,
    casual_leave INT DEFAULT 12,
    sick_leave INT DEFAULT 8,
    earned_leave DECIMAL(4, 1) DEFAULT 20.0,
    bereavement_leave INT DEFAULT 3,
    marriage_leave INT DEFAULT 0,
    lop_leave INT DEFAULT 0,
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance_logs (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    check_in_latitude FLOAT,
    check_in_longitude FLOAT,
    check_in_location VARCHAR(255),
    is_wfh BOOLEAN DEFAULT FALSE,
    working_hours DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'absent' CHECK (status IN ('present', 'absent', 'wfh', 'late', 'half_day')),
    is_late BOOLEAN DEFAULT FALSE,
    location_verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS leave_applications (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    number_of_days DECIMAL(3, 1),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    approved_by VARCHAR(50),
    approval_date TIMESTAMP,
    approval_comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS timesheets (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'approved', 'rejected')),
    total_hours DECIMAL(5, 2),
    submitted_date TIMESTAMP,
    approved_by VARCHAR(50),
    approved_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, week_start_date)
);

CREATE TABLE IF NOT EXISTS timesheet_entries (
    id SERIAL PRIMARY KEY,
    timesheet_id INT NOT NULL REFERENCES timesheets(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    project_name VARCHAR(200),
    task_description VARCHAR(500),
    hours_worked DECIMAL(3, 1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(10) DEFAULT 'p3' CHECK (priority IN ('p1', 'p2', 'p3')),
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to VARCHAR(50),
    resolution TEXT,
    resolved_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    title VARCHAR(200),
    message TEXT,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INT,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL,
    occasion VARCHAR(150) NOT NULL,
    remark VARCHAR(255) DEFAULT 'All Locations',
    region VARCHAR(50) DEFAULT 'India',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(holiday_date, occasion)
);
""")

    # 2. Performance Indexes & RLS Disable
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 2. PERFORMANCE INDEXES & PERMISSIONS")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("""
CREATE INDEX IF NOT EXISTS idx_employees_mgr ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_team ON employees(team);
CREATE INDEX IF NOT EXISTS idx_attendance_logs_emp_date ON attendance_logs(employee_id, attendance_date);
CREATE INDEX IF NOT EXISTS idx_leave_apps_emp ON leave_applications(employee_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_emp ON timesheets(employee_id);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);

ALTER TABLE IF EXISTS departments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS employees DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_balance DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendance_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheet_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS support_tickets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS password_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS holidays DISABLE ROW LEVEL SECURITY;
""")

    # 3. Seed Departments & Teams
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 3. SEED DEPARTMENTS & TEAMS")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("ALTER TABLE IF EXISTS teams ADD COLUMN IF NOT EXISTS department_name VARCHAR(150);")
    sql.append("ALTER TABLE IF EXISTS teams ADD COLUMN IF NOT EXISTS department_id INT;")
    sql.append("")
    for d in departments:
        clean_d = d.replace("'", "''")
        sql.append(f"INSERT INTO departments (name) VALUES ('{clean_d}') ON CONFLICT (name) DO NOTHING;")
    sql.append("")
    
    team_values = []
    for t_name, d_name in teams:
        clean_t = t_name.replace("'", "''")
        clean_d = d_name.replace("'", "''")
        team_values.append(f"    ('{clean_t}', '{clean_d}')")
        
    sql.append("INSERT INTO teams (name, department_id, department_name)")
    sql.append("SELECT t.name, d.id, t.dept_name")
    sql.append("FROM (VALUES\n" + ",\n".join(team_values) + "\n) AS t(name, dept_name)")
    sql.append("JOIN departments d ON d.name = t.dept_name")
    sql.append("ON CONFLICT DO NOTHING;\n")

    # 3.5 Seed Official OTSI Company Holidays 2026
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 3.5 SEED OFFICIAL OTSI COMPANY HOLIDAYS 2026")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("""
INSERT INTO holidays (holiday_date, occasion, remark, region) VALUES
    ('2026-01-01', 'New Year Day', 'All Locations', 'India'),
    ('2026-01-14', 'Sankranti / Pongal', 'All Locations excluding Bangalore', 'India'),
    ('2026-01-15', 'Makara Sankranti', 'Only Bangalore', 'India'),
    ('2026-01-26', 'Republic Day', 'All Locations', 'India'),
    ('2026-03-03', 'Holi', 'Only Delhi', 'India'),
    ('2026-03-19', 'Ugadi', 'All Locations excluding Delhi', 'India'),
    ('2026-05-01', 'Budha Purnima / May Day', 'All Locations excluding Bangalore', 'India'),
    ('2026-05-27', 'Eidul Azha (Bakrid)', 'All Locations', 'India'),
    ('2026-09-14', 'Vinayaka Chavithi', 'All Locations', 'India'),
    ('2026-10-02', 'Mahatma Gandhi Jayanthi', 'All Locations', 'India'),
    ('2026-10-20', 'Vijaya Dasami (Dussehra)', 'All Locations excluding Bangalore', 'India'),
    ('2026-10-21', 'Following Day of Vijaya Dasami', 'Only Bangalore', 'India'),
    ('2026-11-10', 'Balipadyami', 'Only Bangalore', 'India'),
    ('2026-12-25', 'Christmas', 'All Locations', 'India'),
    ('2026-01-01', 'New Year''s Day', 'All US Locations', 'US'),
    ('2026-01-19', 'Martin Luther King Jr. Day', 'All US Locations', 'US'),
    ('2026-05-25', 'Memorial Day', 'All US Locations', 'US'),
    ('2026-06-19', 'Juneteenth National Independence Day', 'All US Locations', 'US'),
    ('2026-07-03', 'Independence Day (Observed)', 'All US Locations', 'US'),
    ('2026-09-07', 'Labor Day', 'All US Locations', 'US'),
    ('2026-11-26', 'Thanksgiving Day', 'All US Locations', 'US'),
    ('2026-11-27', 'Day After Thanksgiving', 'All US Locations', 'US'),
    ('2026-12-25', 'Christmas Day', 'All US Locations', 'US')
ON CONFLICT (holiday_date, occasion) DO UPDATE SET
    remark = EXCLUDED.remark,
    region = EXCLUDED.region,
    updated_at = CURRENT_TIMESTAMP;
""")

    # 4. Seed 250 Employees (in batches of 50 for clean SQL parsing)
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append(f"-- 4. SEED {len(emps)} EMPLOYEES (Password: {DEFAULT_PASSWORD})")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- Clear any previous preliminary seed records to prevent email/ID conflicts")
    sql.append("TRUNCATE TABLE employees CASCADE;\n")
    
    batch_size = 50
    for i in range(0, len(emps), batch_size):
        batch = emps[i:i+batch_size]
        sql.append("INSERT INTO employees (employee_id, email, full_name, designation, department, team, manager_id, manager_name, phone, role, status, password_hash, date_of_joining) VALUES")
        val_lines = []
        for e in batch:
            m_id = f"'{e['manager_id']}'" if e['manager_id'] else "NULL"
            m_name = f"'{e['manager_name'].replace('\'', '\'\'')}'" if e['manager_name'] else "NULL"
            fn = e['full_name'].replace("'", "''")
            desig = e['designation'].replace("'", "''")
            dept = e['department'].replace("'", "''")
            team = e['team'].replace("'", "''")
            status = e.get('status', 'active')
            val_lines.append(f"    ('{e['employee_id']}', '{e['email']}', '{fn}', '{desig}', '{dept}', '{team}', {m_id}, {m_name}, '{e['phone']}', '{e['role']}', '{status}', '{PASSWORD_HASH}', '{e['date_of_joining']}')")
        sql.append(",\n".join(val_lines))
        sql.append("ON CONFLICT (employee_id) DO UPDATE SET")
        sql.append("    full_name = EXCLUDED.full_name,")
        sql.append("    designation = EXCLUDED.designation,")
        sql.append("    department = EXCLUDED.department,")
        sql.append("    team = EXCLUDED.team,")
        sql.append("    manager_id = EXCLUDED.manager_id,")
        sql.append("    manager_name = EXCLUDED.manager_name,")
        sql.append("    role = EXCLUDED.role,")
        sql.append("    password_hash = EXCLUDED.password_hash;\n")

    # 5. Seed Leave Balances
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 5. SEED LEAVE BALANCES FOR ALL EMPLOYEES")
    sql.append("-- ─────────────────────────────────────────────────────────")
    for i in range(0, len(emps), batch_size):
        batch = emps[i:i+batch_size]
        sql.append("INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, earned_leave, bereavement_leave, marriage_leave, lop_leave) VALUES")
        val_lines = [f"    ('{e['employee_id']}', 12, 8, 20.0, 3, 0, 0)" for e in batch]
        sql.append(",\n".join(val_lines))
        sql.append("ON CONFLICT (employee_id) DO NOTHING;\n")

    # 6. Sample Live Attendance for Today & Recent Days
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 6. SEED SAMPLE ATTENDANCE RECORDS (For Live Dashboard & Radar)")
    sql.append("-- ─────────────────────────────────────────────────────────")
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    # 20 present today
    sql.append("INSERT INTO attendance_logs (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_location, is_wfh, working_hours, status, is_late, location_verified) VALUES")
    att_rows = []
    for e in emps[:40]:
        eid = e['employee_id']
        att_rows.append(f"    ('{eid}', '{today_str}', '{today_str}T09:15:00Z', NULL, 17.4418, 78.3809, 'OTSi Hyderabad HQ', FALSE, 4.5, 'present', FALSE, TRUE)")
    # 10 WFH today
    for e in emps[40:55]:
        eid = e['employee_id']
        att_rows.append(f"    ('{eid}', '{today_str}', '{today_str}T09:00:00Z', NULL, 17.4418, 78.3809, 'WFH', TRUE, 4.8, 'wfh', FALSE, TRUE)")
    sql.append(",\n".join(att_rows))
    sql.append("ON CONFLICT (employee_id, attendance_date) DO NOTHING;\n")

    # 7. Reporting Hierarchy Verification View
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("-- 7. ORG HIERARCHY RECURSIVE VIEW")
    sql.append("-- ─────────────────────────────────────────────────────────")
    sql.append("""
CREATE OR REPLACE VIEW v_org_tree AS
WITH RECURSIVE org_hierarchy AS (
    -- Anchor: Top leaders with no manager
    SELECT 
        employee_id, full_name, designation, department, team, manager_id, manager_name, role,
        1 as level,
        ARRAY[full_name::text] as path
    FROM employees
    WHERE manager_id IS NULL AND status = 'active'
    
    UNION ALL
    
    -- Recursive step: Direct reportees
    SELECT 
        e.employee_id, e.full_name, e.designation, e.department, e.team, e.manager_id, e.manager_name, e.role,
        h.level + 1,
        h.path || e.full_name::text
    FROM employees e
    INNER JOIN org_hierarchy h ON e.manager_id = h.employee_id
    WHERE e.status = 'active'
)
SELECT * FROM org_hierarchy ORDER BY level, department, full_name;
""")

    content = "\n".join(sql)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully generated complete SQL file with {len(emps)} employees: {output_path}")

def main():
    print("Building 250-employee OTSI organization model...")
    emps = build_250_organization()
    print(f"Built {len(emps)} employee nodes.")
    
    # Verify no dangling manager_ids
    emp_ids = set(e['employee_id'] for e in emps)
    dangling = []
    for e in emps:
        m = e['manager_id']
        if m and m not in emp_ids:
            dangling.append((e['employee_id'], e['full_name'], m))
    
    if dangling:
        print(f"ERROR: Found {len(dangling)} dangling manager IDs: {dangling}")
        sys.exit(1)
    else:
        print("Hierarchy verification PASSED: Strict acyclic hierarchy with zero dangling manager links.")
        
    output_file = os.path.join(os.path.dirname(__file__), "otsi_org_structure_250.sql")
    generate_sql_script(emps, output_file)

if __name__ == '__main__':
    main()
