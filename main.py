from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import re
import csv
from io import StringIO

app = FastAPI()


# Home route
@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# 🔥 Phone Cleaner
def clean_phone(phone: str):
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("0"):
        digits = digits[1:]

    if len(digits) == 10:
        return "+91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    else:
        return "INVALID"


# 🔥 API 1: Clean Phone
@app.get("/clean-phone/")
def clean_phone_api(phone: str):
    return {
        "input": phone,
        "output": clean_phone(phone)
    }


# 🔥 API 2: Duplicate Detection
@app.post("/check-duplicates/")
def check_duplicates(phones: list[str]):
    cleaned_numbers = []
    duplicates = []

    for phone in phones:
        cleaned = clean_phone(phone)

        if cleaned in cleaned_numbers:
            duplicates.append(cleaned)
        else:
            cleaned_numbers.append(cleaned)

    return {
        "total_input": len(phones),
        "unique_numbers": list(set(cleaned_numbers)),
        "duplicates": duplicates
    }


# 🔥 API 3: CSV Upload + Download Cleaned File
@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    csv_data = StringIO(content.decode("utf-8"))

    reader = csv.DictReader(csv_data)

    output = StringIO()
    fieldnames = reader.fieldnames + ["cleaned_phone"]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        phone = row.get("phone", "")
        cleaned = clean_phone(phone)

        row["cleaned_phone"] = cleaned
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cleaned_data.csv"}
    )