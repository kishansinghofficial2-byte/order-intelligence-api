from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import io
import uuid

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home route
@app.get("/")
def home():
    return {"message": "API is running 🚀"}


# GLOBAL STORAGE (temporary)
processed_data_store = {}


# 🔥 ANALYZE CSV
@app.post("/analyze/")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))

    # 🔍 Auto detect phone column
    phone_col = None
    for col in df.columns:
        if "phone" in col.lower() or "mobile" in col.lower():
            phone_col = col
            break

    if not phone_col:
        return {"error": "No phone column found"}

    # 📞 Clean numbers
    df[phone_col] = df[phone_col].astype(str).str.replace(r"\D", "", regex=True)

    # ❌ Invalid numbers
    invalid = df[~df[phone_col].str.match(r"^[6-9]\d{9}$")]

    # 🔁 Duplicates
    duplicates = df[df.duplicated(subset=[phone_col], keep=False)]

    # ✅ Clean unique
    clean_df = df.drop_duplicates(subset=[phone_col])
    clean_df = clean_df[clean_df[phone_col].str.match(r"^[6-9]\d{9}$")]

    # 📊 Insights
    insights = {
        "total_rows": len(df),
        "valid_numbers": len(clean_df),
        "invalid_numbers": len(invalid),
        "duplicate_numbers": len(duplicates)
    }

    # 🆔 Store result
    file_id = str(uuid.uuid4())
    processed_data_store[file_id] = clean_df

    # 🔍 Preview (top 5 rows)
    preview = clean_df.head().to_dict(orient="records")

    return {
        "file_id": file_id,
        "insights": insights,
        "preview": preview
    }


# 📥 DOWNLOAD CLEAN DATA
@app.get("/download/{file_id}")
def download(file_id: str):
    if file_id not in processed_data_store:
        return {"error": "Invalid file_id"}

    df = processed_data_store[file_id]

    file_path = f"cleaned_{file_id}.csv"
    df.to_csv(file_path, index=False)

    return FileResponse(file_path, filename="cleaned_data.csv")