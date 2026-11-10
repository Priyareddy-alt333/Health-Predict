"""Attempt the exact assessment records. Invalid entries are reported, not changed.
Duplicate valid rows are intentionally allowed because the task does not require
duplicate prevention. Run: python seed_test_records.py
"""
from app import init_db, validate_patient, save_patient

records = [
    {"full_name":"Robyn Pears","dob":"28.01.1960","email":"robyn@gmail.com","glucose":"232","haemoglobin":"13.5","cholesterol":"180"},
    {"full_name":"John Hunter","dob":"10.12.1990","email":"hunter@gmail","glucose":"94","haemoglobin":"15","cholesterol":"200"},
    {"full_name":"Darryl Tim","dob":"12.11.1993","email":"timd@smh.com.au","glucose":"240","haemoglobin":"18.6","cholesterol":"326"},
    {"full_name":"Peter Larry","dob":"31.11.2001","email":"Larry@hotmail.com","glucose":"88","haemoglobin":"11.5","cholesterol":"165"},
    {"full_name":"Sam Kerr","dob":"09.12.2006","email":"sam@news.com.au","glucose":"198","haemoglobin":"8.9","cholesterol":"192"},
    {"full_name":"Robyn Pears","dob":"28.01.1960","email":"robyn@gmail.com","glucose":"232","haemoglobin":"13.5","cholesterol":"180"},
    {"full_name":"Madison XI","dob":"12.09.1998","email":"madison@hotmail.com","glucose":"85","haemoglobin":"7.6","cholesterol":"163"},
    {"full_name":"Kris Wu","dob":"19.10.2030","email":"Kris.wu.gmail.com","glucose":"79","haemoglobin":"16.5","cholesterol":"197"},
    {"full_name":"Tenille Singh","dob":"30.11.1991","email":"Tenille@yahoo.com","glucose":"101","haemoglobin":"15","cholesterol":"310"},
    {"full_name":"Prem Kumar","dob":"28.04.1990","email":"prem@telstra.com","glucose":"155","haemoglobin":"12.5","cholesterol":"265"},
]

init_db()
created = 0
print("HealthPredict assessment data import")
print("-----------------------------------")
for number, record in enumerate(records, 1):
    clean, errors = validate_patient(record)
    if errors:
        print(f"Test {number}: REJECTED")
        for error in errors:
            print(f"  - {error}")
    else:
        save_patient(clean)
        created += 1
        print(f"Test {number}: CREATED - {record['full_name']}")
print("-----------------------------------")
print(f"Created {created} records; rejected {len(records)-created} records.")
print("Note: each successful creation requests AI remarks. If no API key is set,")
print("the record is still saved with a clear AI-unavailable message.")
