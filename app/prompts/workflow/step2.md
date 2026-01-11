# Step 2: 履歴照合・パターン分析

## タスク

Step 1で検出されたライフイベントを、過去の検出履歴と照合し、パターン分析を行ってください。

## 入力

**今回検出されたイベント（Step 1の結果）:**
```
{step1_result}
```

**過去の検出履歴:**
```
{past_summaries}
```

## 分析ルール

### 1. 新規イベント vs 既知イベントの判定

- **新規イベント**: 過去に同じイベントタイプが検出されていない
- **既知イベントの続報**: 過去に同じイベントタイプが検出されており、進捗や詳細が追加された
- **関連イベント**: 過去のイベントと論理的に関連がある（例: 結婚 → 引っ越し）

### 2. ライフステージパターン

よくあるライフイベントの連鎖パターン：

| パターン | 説明 |
|---------|------|
| 結婚 → 引っ越し | 新婚による新居への移転 |
| 結婚 → 出産・子育て | 家族形成期 |
| 出産 → 進学（子供） | 子供の成長段階 |
| 就職・転職 → 引っ越し | 仕事の都合による転居 |
| 退職・定年 → 引っ越し | シニアライフへの移行 |
| 進学（子供） → 独立（子供） | 子供の巣立ち |

### 3. 時間的整合性

- 過去のイベントからの経過時間を考慮
- 論理的に矛盾するパターンは除外（例: 出産直後の退職・定年は関連性なし）

## 出力形式

以下のJSON形式で出力してください。**JSONのみを出力し、他の説明は含めないでください。**

```json
{{
  "customer_id": "顧客ID",
  "current_event": {{
    "event_type": "今回検出されたイベント",
    "confidence": "確度"
  }},
  "historical_context": {{
    "previous_events": [
      {{
        "date": "過去の検出日",
        "event_type": "過去のイベント種別",
        "confidence": "確度"
      }}
    ],
    "pattern_analysis": "パターン分析の結果（1〜2文）"
  }},
  "is_new_event": true,
  "related_to_previous": false
}}
```

### 出力例

**過去の履歴があり、関連パターンが検出された場合:**
```json
{{
  "customer_id": "C-98765",
  "current_event": {{
    "event_type": "引っ越し",
    "confidence": "high"
  }},
  "historical_context": {{
    "previous_events": [
      {{"date": "2024-06-15", "event_type": "結婚", "confidence": "high"}}
    ],
    "pattern_analysis": "結婚後約7ヶ月での引っ越し。新婚による新居への移転と推測される。"
  }},
  "is_new_event": true,
  "related_to_previous": true
}}
```

**過去の履歴がない場合:**
```json
{{
  "customer_id": "C-10001",
  "current_event": {{
    "event_type": "引っ越し",
    "confidence": "high"
  }},
  "historical_context": {{
    "previous_events": [],
    "pattern_analysis": "初回検出のため、過去のパターンは不明。新規イベントとして記録。"
  }},
  "is_new_event": true,
  "related_to_previous": false
}}
```

**複数イベントが同時検出された場合:**
```json
{{
  "customer_id": "C-10015",
  "current_event": {{
    "event_types": ["就職・転職", "引っ越し"],
    "confidence": "high"
  }},
  "historical_context": {{
    "previous_events": [],
    "pattern_analysis": "転職に伴う引っ越し。キャリアの転換期と生活環境の変化が同時発生。"
  }},
  "is_new_event": true,
  "related_to_previous": false,
  "event_correlation": "転職が引っ越しのトリガー。両イベントは強く関連している。"
}}
```

## 注意事項

1. **過去の履歴がない場合**も、適切に処理する
2. **パターン分析は簡潔に**（1〜2文で要約）
3. **時間的整合性**を考慮し、不自然な関連付けは避ける
4. **複数イベント同時検出**の場合は、イベント間の関連性も分析する
