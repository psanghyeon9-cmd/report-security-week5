"""교육용 샘플 데이터와 모의 응답으로 월간 매출 리포트를 만든다."""

import os
import sqlite3
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


def load_settings():
    load_dotenv(
        Path(__file__).resolve().parent / ".env",
        override=False,
        encoding="utf-8-sig",
        interpolate=False,
    )
    names = ("API_KEY", "DB_URL", "MODEL", "REPORT_MONTH")
    settings = {name: os.getenv(name, "") for name in names}
    missing = [name for name, value in settings.items() if not value.strip()]
    if missing:
        raise ValueError("필수 설정 누락: " + ", ".join(missing))

    month = settings["REPORT_MONTH"]
    try:
        if len(month) != 7:
            raise ValueError
        date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("REPORT_MONTH는 YYYY-MM 형식의 유효한 월이어야 합니다.") from None
    return settings


def connect_db(db_url):
    if not isinstance(db_url, str) or not db_url.strip():
        raise ValueError("DB_URL 설정이 필요합니다.")
    print("[INFO] DB 설정 확인 완료 (접속 정보 비공개)")
    print("[데모] 실제 DB 대신 내장 샘플 데이터를 사용합니다.")

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sales (sold_on TEXT, category TEXT, amount INTEGER)")
    sample = [
        ("2026-09-01", "음료", 4500), ("2026-09-01", "음료", 5000),
        ("2026-09-02", "디저트", 6500), ("2026-09-03", "음료", 4500),
        ("2026-09-05", "원두", 18000), ("2026-09-07", "디저트", 5500),
        ("2026-09-10", "음료", 5500), ("2026-09-12", "원두", 22000),
        ("2026-09-15", "음료", 4500), ("2026-09-18", "디저트", 7000),
        ("2026-09-21", "음료", 5000), ("2026-09-25", "원두", 18000),
        ("2026-08-30", "음료", 4500),
    ]
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?)", sample)
    return conn


def monthly_summary(conn, month):
    rows = conn.execute(
        """SELECT category, COUNT(*), SUM(amount)
           FROM sales
           WHERE substr(sold_on, 1, 7) = ?
           GROUP BY category
           ORDER BY SUM(amount) DESC""",
        (month,),
    ).fetchall()
    return [{"category": c, "count": n, "total": t} for c, n, t in rows]


def request_llm_comment(summary, api_key, model):
    if not api_key or not model:
        raise ValueError("API_KEY와 MODEL 설정이 필요합니다.")
    if not isinstance(summary, list):
        raise ValueError("집계 결과는 목록이어야 합니다.")
    for row in summary:
        if not isinstance(row, dict):
            raise ValueError("집계 항목은 딕셔너리여야 합니다.")
        if (
            not isinstance(row.get("category"), str)
            or not row["category"].strip()
            or type(row.get("count")) is not int
            or row["count"] <= 0
            or type(row.get("total")) is not int
            or row["total"] < 0
        ):
            raise ValueError("집계 항목의 형식 또는 값이 올바르지 않습니다.")

    top = summary[0]["category"] if summary else "없음"
    print("[데모] 외부 API 호출 없이 모의 응답을 사용합니다.")
    comment = (
        f"[MOCK] 이번 달 매출 1위 카테고리는 '{top}'입니다. "
        "상위 품목 재고를 점검하세요."
    )
    if not comment.startswith("[MOCK] ") or len(comment) > 500:
        raise ValueError("모의 응답의 형식 또는 길이가 올바르지 않습니다.")
    return comment


def print_report(month, summary, comment):
    total = sum(r["total"] for r in summary)
    print("\n" + "=" * 46)
    print(f"  서강카페 월간 매출 리포트 ({month})")
    print("=" * 46)
    for r in summary:
        share = r["total"] / total * 100 if total else 0
        print(f"  {r['category']:<6} {r['count']:>3}건  {r['total']:>8,}원  ({share:4.1f}%)")
    print("-" * 46)
    print(f"  합계            {total:>8,}원")
    print(f"\n  AI 코멘트: {comment}")
    print("=" * 46)


def main():
    settings = load_settings()
    conn = connect_db(settings["DB_URL"])
    try:
        summary = monthly_summary(conn, settings["REPORT_MONTH"])
        comment = request_llm_comment(summary, settings["API_KEY"], settings["MODEL"])
        print_report(settings["REPORT_MONTH"], summary, comment)
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(f"설정 또는 입력 오류: {error}")
