# サンプルデータ

このディレクトリには、CS通話ログ分析システムのテスト・評価用サンプルデータが含まれています。

## ディレクトリ構成

```
samples/
├── README.md                    # このファイル
├── call-logs/                   # 入力: 通話ログサンプル
│   ├── 01_moving_explicit.json      # 引っ越し（明示的）
│   ├── 01_moving_implicit.json      # 引っ越し（暗示的）
│   ├── 02_marriage_explicit.json    # 結婚（明示的）
│   ├── 02_marriage_implicit.json    # 結婚（暗示的）
│   ├── 03_childbirth_explicit.json  # 出産・子育て（明示的）
│   ├── 03_childbirth_implicit.json  # 出産・子育て（暗示的）
│   ├── 04_job_change_explicit.json  # 就職・転職（明示的）
│   ├── 04_job_change_implicit.json  # 就職・転職（暗示的）
│   ├── 05_education_explicit.json   # 進学（明示的）
│   ├── 05_education_implicit.json   # 進学（暗示的）
│   ├── 06_retirement_explicit.json  # 退職・定年（明示的）
│   ├── 06_retirement_implicit.json  # 退職・定年（暗示的）
│   ├── 07_independence_explicit.json # 独立（明示的）
│   ├── 07_independence_implicit.json # 独立（暗示的）
│   ├── 08_multiple_events.json      # 複数イベント同時検出
│   └── 09_no_event.json             # ライフイベントなし
└── expected-outputs/            # 出力: 期待される検出結果
    ├── 01_moving_explicit_output.json
    ├── 02_marriage_explicit_output.json
    ├── 03_childbirth_implicit_output.json
    ├── 08_multiple_events_output.json
    └── 09_no_event_output.json
```

## サンプルの分類

### ライフイベント別

| # | イベント | 明示的 | 暗示的 | 難易度 |
|---|----------|--------|--------|--------|
| 1 | 引っ越し | `01_moving_explicit.json` | `01_moving_implicit.json` | easy / medium |
| 2 | 結婚 | `02_marriage_explicit.json` | `02_marriage_implicit.json` | easy / medium |
| 3 | 出産・子育て | `03_childbirth_explicit.json` | `03_childbirth_implicit.json` | easy / medium |
| 4 | 就職・転職 | `04_job_change_explicit.json` | `04_job_change_implicit.json` | easy / medium |
| 5 | 進学（子供） | `05_education_explicit.json` | `05_education_implicit.json` | easy / hard |
| 6 | 退職・定年 | `06_retirement_explicit.json` | `06_retirement_implicit.json` | easy / medium |
| 7 | 独立（子供） | `07_independence_explicit.json` | `07_independence_implicit.json` | easy / medium |

### 特殊ケース

| ファイル | 説明 | 用途 |
|----------|------|------|
| `08_multiple_events.json` | 転職＋引っ越しの複合ケース | 複数イベント同時検出のテスト |
| `09_no_event.json` | ライフイベントなし（料金確認のみ） | ノイズ除去・False Positive抑制のテスト |

## 通話ログのフォーマット

```json
{
  "call_id": "CALL-YYYY-MM-DD-NNNNN",
  "customer_id": "C-NNNNN",
  "call_date": "YYYY-MM-DD",
  "call_time": "HH:MM:SS",
  "duration_seconds": 999,
  "call_reason": "問い合わせ理由",
  "transcript": [
    {"speaker": "operator", "text": "オペレーターの発言"},
    {"speaker": "customer", "text": "顧客の発言"}
  ],
  "metadata": {
    "event_type": "ライフイベント種別",
    "detection_type": "explicit / implicit",
    "difficulty": "easy / medium / hard"
  }
}
```

## 期待出力のフォーマット

```json
{
  "step1_output": {
    "call_id": "...",
    "customer_id": "...",
    "call_date": "...",
    "detected_events": [...],
    "no_event_detected": false
  },
  "step2_output": {
    "customer_id": "...",
    "current_event": {...},
    "historical_context": {...},
    "is_new_event": true,
    "related_to_previous": false
  },
  "step3_output": {
    "customer_id": "...",
    "call_date": "...",
    "recommendations": [...],
    "life_stage_summary": "..."
  }
}
```

## 利用方法

### 単体テスト

```python
import json

# 通話ログを読み込み
with open("docs/samples/call-logs/01_moving_explicit.json") as f:
    call_log = json.load(f)

# 期待出力を読み込み
with open("docs/samples/expected-outputs/01_moving_explicit_output.json") as f:
    expected = json.load(f)

# ワークフローを実行して比較
result = run_workflow(call_log)
assert result["step1_output"]["detected_events"][0]["event_type"] == "引っ越し"
```

### 評価テスト（strands-evals）

これらのサンプルは `app/evaluation/cases.py` のテストケース定義で使用されます。
```
