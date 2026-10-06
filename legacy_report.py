"""
legacy_report.py — 서강카페 월간 매출 리포트 생성 스크립트 (레거시 버전)

[AI 오케스트레이션 스튜디오 · 5주차 과제 1 — 리팩터링 대상 파일]

이 스크립트는 '동작은 하지만 보안상 위험한' 레거시 코드의 전형이다.
과제: 비밀 값을 .env 로 분리하고, .gitignore / .env.example 을 작성하여
      python-dotenv 로 읽어 오도록 리팩터링한다. (강의노트 3.4절)

※ 아래 API 키·DB 비밀번호는 실제 권한이 전혀 없는 교육용 더미 값이다.
※ 표준 라이브러리만 사용하며, 실제 DB·외부 API에는 접속하지 않는다.
   (DB는 메모리 내 샘플 데이터로, LLM 호출은 모의 응답으로 대체)

실행:  python legacy_report.py
"""

import sqlite3
from urllib.parse import urlparse

# =====================================================================
# 설정 — 레거시: 모든 값을 코드에 직접 적어 두었다
# =====================================================================
API_KEY = "sk-demo-week05-legacy-0000-NOT-A-REAL-KEY"
# 예전 키 (혹시 몰라서 남겨둠): sk-demo-week05-old-1111-NOT-A-REAL-KEY
DB_URL = "postgresql://report_admin:Sogang!2026@10.20.30.40:5432/sales_prod"
MODEL = "claude-sonnet-4-5"
REPORT_MONTH = "2026-09"


# =====================================================================
# 1) DB 연결 — 데모용: 실제 서버 대신 메모리 DB에 샘플 매출을 적재한다
# =====================================================================
def connect_db(db_url):
    print(f"[DEBUG] DB 접속 시도: {db_url}")          # 로그에 비밀번호까지 그대로 출력
    info = urlparse(db_url)
    print(f"[INFO] 호스트 {info.hostname}:{info.port} / DB {info.path.lstrip('/')}")
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
        ("2026-08-30", "음료", 4500),   # 지난달 데이터 (집계에서 제외되어야 함)
    ]
    conn.executemany("INSERT INTO sales VALUES (?, ?, ?)", sample)
    return conn


# =====================================================================
# 2) 월간 집계 — 카테고리별 건수·매출 합계
# =====================================================================
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


# =====================================================================
# 3) LLM 코멘트 요청 — 데모용: 실제 호출 없이 모의 응답을 돌려준다
# =====================================================================
def request_llm_comment(summary, api_key):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    print(f"[DEBUG] 요청 헤더: {headers}")              # 키 전체가 콘솔·로그에 남는다
    top = summary[0]["category"] if summary else "없음"
    print(f"[데모] {MODEL} 호출을 생략하고 모의 응답을 사용합니다.")
    return f"[MOCK] 이번 달 매출 1위 카테고리는 '{top}'입니다. 상위 품목 재고를 점검하세요."


# =====================================================================
# 4) 리포트 출력
# =====================================================================
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
    conn = connect_db(DB_URL)
    summary = monthly_summary(conn, REPORT_MONTH)
    comment = request_llm_comment(summary, API_KEY)
    print_report(REPORT_MONTH, summary, comment)
    conn.close()


if __name__ == "__main__":
    main()
