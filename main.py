from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from datetime import datetime
import math

app = FastAPI()

# CORS 설정 (React 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용할 도시 리스트
city_list = ["boryeong", "buyeo", "cheonan", "geumsan", "seosan"]

# 데이터 로드 함수
def load_city_data(city_eng: str):
    folder_path = f"./data/{city_eng}"
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"도시 폴더가 없습니다: {folder_path}")
    
    file_name = f"{city_eng}_20222025.csv"
    full_path = os.path.join(folder_path, file_name)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"CSV 파일이 없습니다: {full_path}")

    df = pd.read_csv(full_path, encoding="euc-kr")  # 또는 'utf-8'
    return df

# 날짜 기반 예측 함수 (NaN 방지 포함)
def seasonal_predict(df, column: str):
    today = datetime.now().strftime("%m-%d")  # 예: "04-18"

    if "일시" not in df.columns:
        raise ValueError("CSV에 '일시' 컬럼이 없습니다.")

    df["날짜키"] = df["일시"].astype(str).str[5:]  # "YYYY-MM-DD" → "MM-DD"
    day_data = df[df["날짜키"] == today]

    if day_data.empty or column not in df.columns:
        return None

    value = day_data[column].mean()
    if pd.isna(value) or math.isnan(value):
        return None

    return round(value, 2)

# 예측 API
@app.get("/predict")
def predict(region: str = Query(..., description="영문 도시명 (예: boryeong)")):
    if region not in city_list:
        return {"error": f"{region}은 지원하지 않는 도시입니다."}

    try:
        df = load_city_data(region)

        return {
            "region": region,
            "predict_date": datetime.now().strftime("%m월 %d일 예측"),
            "temperature": seasonal_predict(df, "평균기온(°C)") or "데이터 없음",
            "precipitation": seasonal_predict(df, "1시간 최다강수량(mm)") or "데이터 없음",
            "windspeed": seasonal_predict(df, "최대 순간 풍속(m/s)") or "데이터 없음"
        }

    except Exception as e:
        return {"error": str(e)}
