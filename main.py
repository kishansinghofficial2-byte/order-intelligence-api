from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import re
import csv
from io import StringIO
from collections import Counter

app = FastAPI()

# ✅ CORS FIX (buttons issue solve)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔥 Clean phone
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


# 🔥 Detect phone column
def detect_phone_column(fieldnames):
    for field in fieldnames:
        if "phone" in field.lower() or "mobile" in field.lower():
            return field
    return None


# 🔥 Risk + Reason
def get_risk_and_reason(number, count):
    if number == "INVALID":
        return "HIGH", "Invalid number"
    elif count > 3:
        return "HIGH", "Repeated many times"
    elif count > 1:
        return "MEDIUM", "Duplicate number"
    else:
        return "LOW", "Normal"


@app.get("/")
def home():
    return {"message": "Business Data Intelligence API 🚀"}


# 🔥 ANALYZE
@app.post("/analyze/")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    csv_data = StringIO(content.decode("utf-8"))

    reader = csv.DictReader(csv_data)
    phone_column = detect_phone_column(reader.fieldnames)

    if not phone_column:
        return {"error": "No phone column found"}

    rows = list(reader)

    cleaned_numbers = []
    for row in rows:
        cleaned = clean_phone(row.get(phone_column, ""))
        cleaned_numbers.append(cleaned)

    counts = Counter(cleaned_numbers)

    preview = []
    total = 0
    high = 0
    medium = 0
    low = 0
    invalid = 0

    for row in rows:
        cleaned = clean_phone(row.get(phone_column, ""))
        risk, reason = get_risk_and_reason(cleaned, counts[cleaned])

        if cleaned == "INVALID":
            invalid += 1

        if risk == "HIGH":
            high += 1
        elif risk == "MEDIUM":
            medium += 1
        else:
            low += 1

        row["cleaned_phone"] = cleaned
        row["risk"] = risk
        row["risk_reason"] = reason

        if total < 5:
            preview.append(row)

        total += 1

    duplicate_count = sum(1 for c in counts.values() if c > 1)
    high_percent = round((high / total) * 100, 2) if total > 0 else 0

    if high_percent > 30:
        insight = "⚠️ High fraud risk detected"
    elif high_percent > 10:
        insight = "⚠️ Moderate risk detected"
    else:
        insight = "✅ Data looks clean"

    return {
        "summary": {
            "total_rows": total,
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
            "invalid_numbers": invalid,
            "duplicate_entries": duplicate_count,
            "high_risk_percent": high_percent
        },
        "insight": insight,
        "preview": preview
    }


# 🔥 DOWNLOAD
@app.post("/download-result/")
async def download_result(file: UploadFile = File(...)):
    content = await file.read()
    csv_data = StringIO(content.decode("utf-8"))

    reader = csv.DictReader(csv_data)
    phone_column = detect_phone_column(reader.fieldnames)

    rows = list(reader)

    cleaned_numbers = []
    for row in rows:
        cleaned = clean_phone(row.get(phone_column, ""))
        cleaned_numbers.append(cleaned)

    counts = Counter(cleaned_numbers)

    output = StringIO()
    fieldnames = reader.fieldnames + ["cleaned_phone", "risk", "risk_reason"]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        cleaned = clean_phone(row.get(phone_column, ""))
        risk, reason = get_risk_and_reason(cleaned, counts[cleaned])

        row["cleaned_phone"] = cleaned
        row["risk"] = risk
        row["risk_reason"] = reason

        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analyzed_data.csv"}
    )