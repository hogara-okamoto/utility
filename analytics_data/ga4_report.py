import os
import csv
from datetime import datetime, timedelta  # 日付操作用にインポート追加
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, 
    Filter, FilterExpression, OrderBy, FilterExpressionList
)

# --- 設定パラメータ ---
PROPERTY_ID = "509200578"  # <--- あなたのGA4プロパティID
START_DATE = "2025-11-01"
END_DATE = "2025-11-30"

# 1. 取得したいイベント名
TARGET_EVENT_NAME = "" 

# 2. 内訳として表示したいディメンション
TARGET_DIMENSION_KEY = "customEvent:selected_language" 

# 3. 行の表示順序設定 (指定された順序)
ROW_ORDER = ["(not set)", "en", "ja", "ko", "zh-CN", "zh-TW"]

OUTPUT_FILENAME = "ga4_daily_report_pivot.csv"
# --------------------

KEY_FILE_NAME = "your-service-account-key.json" 

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(__file__), KEY_FILE_NAME
)

def get_date_range_list(start_str, end_str):
    """開始日から終了日までの日付リスト(yyyyMMdd形式)を生成する"""
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    
    date_list = []
    current = start
    while current <= end:
        # GA4 APIのレスポンスに合わせて yyyyMMdd 形式にする
        date_list.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return date_list

def run_analytics_report():
    """GA4データを取得し、指定されたピボット形式(横軸:日付、縦軸:指標/内訳)でCSV出力する"""
    try:
        client = BetaAnalyticsDataClient()
        
        # ★修正: APIの結果に頼らず、指定期間の全日付リストを先に生成する
        # これによりデータが0の日も欠落せずに列が作られます
        sorted_dates = get_date_range_list(START_DATE, END_DATE)

        # ==========================================
        # 1. 全体のアクティブユーザー数を取得 (行1用)
        # ==========================================
        print(f"1/2: 全体のアクティブユーザー数を取得中...")
        req_dau = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            date_ranges=[DateRange(start_date=START_DATE, end_date=END_DATE)],
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers")]
        )
        res_dau = client.run_report(req_dau)
        
        # { "20251101": 100, ... } の形式で保存
        dau_data = {}
        for row in res_dau.rows:
            date = row.dimension_values[0].value
            val = row.metric_values[0].value
            dau_data[date] = val

        # ==========================================
        # 2. 言語ごとのイベント数を取得 (行3以降用)
        # ==========================================
        print(f"2/2: 内訳ごとのイベント数を取得中... ({TARGET_DIMENSION_KEY})")
        
        # フィルタ作成 (イベント名指定がある場合のみ)
        filter_expr = None
        if TARGET_EVENT_NAME:
            filter_expr = FilterExpression(
                filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(
                        value=TARGET_EVENT_NAME,
                        match_type=Filter.StringFilter.MatchType.EXACT
                    )
                )
            )

        req_breakdown = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            date_ranges=[DateRange(start_date=START_DATE, end_date=END_DATE)],
            dimensions=[
                Dimension(name="date"),
                Dimension(name=TARGET_DIMENSION_KEY)
            ],
            metrics=[Metric(name="eventCount")],
            dimension_filter=filter_expr
        )
        res_breakdown = client.run_report(req_breakdown)

        # { "20251101": { "ja": 10, "en": 5 }, ... } の形式で保存
        event_breakdown_data = {}
        
        # データに含まれるすべての内訳キーを収集 (指定外のものがあった場合のため)
        found_keys = set()

        for row in res_breakdown.rows:
            date = row.dimension_values[0].value
            key = row.dimension_values[1].value # 言語 (en, ja など)
            val = row.metric_values[0].value    # イベント数
            
            if date not in event_breakdown_data:
                event_breakdown_data[date] = {}
            
            event_breakdown_data[date][key] = val
            found_keys.add(key)

        # ==========================================
        # 3. CSV出力 (ピボット変換)
        # ==========================================
        
        # sorted_dates は既に全期間分あるので、これを使って出力
        
        with open(OUTPUT_FILENAME, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)

            # --- ヘッダー行 (横軸: 日付) ---
            # 例: [項目, 20251101, 20251102, ...]
            header = ["項目"] + sorted_dates
            writer.writerow(header)

            # --- 1行目: アクティブユーザー数 ---
            row_dau = ["アクティブユーザー数"]
            for d in sorted_dates:
                # データがない日は "0" を入れる
                row_dau.append(dau_data.get(d, "0"))
            writer.writerow(row_dau)

            # --- 2行目: 空データ ---
            row_empty = [""] + [""] * len(sorted_dates)
            writer.writerow(row_empty)

            # --- 3行目以降: 言語ごとのイベント数 ---
            # 指定された順序で出力
            
            # まず指定されたキーを出力
            for key in ROW_ORDER:
                row = [key]
                for d in sorted_dates:
                    # その日のデータ辞書を取得 -> その言語の値を取得 (なければ0)
                    day_data = event_breakdown_data.get(d, {})
                    val = day_data.get(key, "0")
                    row.append(val)
                writer.writerow(row)
                
                # 出力済みとして記録
                if key in found_keys:
                    found_keys.remove(key)

            # (オプション) ROW_ORDER に含まれていないが、データには存在したキーがあれば末尾に追加
            if found_keys:
                sorted_remain = sorted(list(found_keys))
                for key in sorted_remain:
                    row = [key]
                    for d in sorted_dates:
                        day_data = event_breakdown_data.get(d, {})
                        val = day_data.get(key, "0")
                        row.append(val)
                    writer.writerow(row)

        print(f"\n完了: ピボットテーブル形式で '{OUTPUT_FILENAME}' に保存しました。")
        print(f"カラム数(日付): {len(sorted_dates)} (データ有無に関わらず全日程を出力)")
        print(f"出力行: アクティブユーザー数 + 空行 + {len(ROW_ORDER)}種類の指定言語 + その他({len(found_keys)}種)")

    except Exception as e:
        print(f"\nエラーが発生しました:\n{e}")
        if "Invalid dimension" in str(e):
             print(f"\nヒント: ディメンション名 '{TARGET_DIMENSION_KEY}' が無効です。")

if __name__ == "__main__":
    run_analytics_report()