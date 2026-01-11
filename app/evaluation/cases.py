"""
評価用テストケースの定義。

CS通話ログ分析ワークフローの各ステップを評価するためのテストケースを提供する。
- Step 1: ライフイベント検出
- Step 2: 履歴照合・パターン分析
- Step 3: レコメンド生成
"""

import json
from pathlib import Path

from strands_evals import Case

# サンプルデータのパス
SAMPLES_DIR = Path(__file__).parent.parent.parent / "docs" / "samples"
CALL_LOGS_DIR = SAMPLES_DIR / "call-logs"
EXPECTED_OUTPUTS_DIR = SAMPLES_DIR / "expected-outputs"


def _load_call_log(filename: str) -> dict:
    """通話ログのサンプルファイルを読み込む"""
    file_path = CALL_LOGS_DIR / filename
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"サンプルファイルが見つかりません: {file_path}")


def _load_expected_output(filename: str) -> dict | None:
    """期待出力のサンプルファイルを読み込む（存在しない場合はNone）"""
    file_path = EXPECTED_OUTPUTS_DIR / filename
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))
    return None


def _format_transcript(transcript: list[dict]) -> str:
    """会話記録を文字列形式に変換する"""
    lines = []
    for entry in transcript:
        speaker = "オペレーター" if entry["speaker"] == "operator" else "顧客"
        lines.append(f"{speaker}: {entry['text']}")
    return "\n".join(lines)


def create_step1_cases() -> list[Case[dict, str]]:
    """
    Step 1（ライフイベント検出）のテストケースを作成する。

    各ライフイベント（明示的・暗示的）およびエッジケースのテストケースを含む。

    Returns:
        テストケースのリスト
    """
    cases = []

    # ===== 引っ越し =====
    # 明示的
    call_log = _load_call_log("01_moving_explicit.json")
    cases.append(
        Case[dict, str](
            name="moving-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "引っ越し",
                    "confidence": "high",
                    "timing": "1ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "引っ越し",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("01_moving_implicit.json")
    cases.append(
        Case[dict, str](
            name="moving-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "引っ越し",
                    "confidence": "medium",
                    "timing": "1週間以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "引っ越し",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== 結婚 =====
    # 明示的
    call_log = _load_call_log("02_marriage_explicit.json")
    cases.append(
        Case[dict, str](
            name="marriage-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "結婚",
                    "confidence": "high",
                    "timing": "1ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "結婚",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("02_marriage_implicit.json")
    cases.append(
        Case[dict, str](
            name="marriage-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "結婚",
                    "confidence": "high",
                    "timing": "完了済み",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "結婚",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== 出産・子育て =====
    # 明示的
    call_log = _load_call_log("03_childbirth_explicit.json")
    cases.append(
        Case[dict, str](
            name="childbirth-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "出産・子育て",
                    "confidence": "high",
                    "timing": "完了済み",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "出産・子育て",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("03_childbirth_implicit.json")
    cases.append(
        Case[dict, str](
            name="childbirth-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "出産・子育て",
                    "confidence": "medium",
                    "timing": "進行中",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "出産・子育て",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== 就職・転職 =====
    # 明示的
    call_log = _load_call_log("04_job_change_explicit.json")
    cases.append(
        Case[dict, str](
            name="job-change-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "就職・転職",
                    "confidence": "high",
                    "timing": "3ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "就職・転職",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("04_job_change_implicit.json")
    cases.append(
        Case[dict, str](
            name="job-change-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "就職・転職",
                    "confidence": "medium",
                    "timing": "1ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "就職・転職",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== 進学（子供） =====
    # 明示的
    call_log = _load_call_log("05_education_explicit.json")
    cases.append(
        Case[dict, str](
            name="education-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "進学（子供）",
                    "confidence": "high",
                    "timing": "3ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "進学（子供）",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的（難易度: hard）
    call_log = _load_call_log("05_education_implicit.json")
    cases.append(
        Case[dict, str](
            name="education-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "進学（子供）",
                    "confidence": "low",
                    "timing": "1年以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "進学（子供）",
                "detection_type": "implicit",
                "difficulty": "hard",
            },
        )
    )

    # ===== 退職・定年 =====
    # 明示的
    call_log = _load_call_log("06_retirement_explicit.json")
    cases.append(
        Case[dict, str](
            name="retirement-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "退職・定年",
                    "confidence": "high",
                    "timing": "3ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "退職・定年",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("06_retirement_implicit.json")
    cases.append(
        Case[dict, str](
            name="retirement-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "退職・定年",
                    "confidence": "medium",
                    "timing": "完了済み",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "退職・定年",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== 独立（子供） =====
    # 明示的
    call_log = _load_call_log("07_independence_explicit.json")
    cases.append(
        Case[dict, str](
            name="independence-explicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "独立（子供）",
                    "confidence": "high",
                    "timing": "1ヶ月以内",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "独立（子供）",
                "detection_type": "explicit",
                "difficulty": "easy",
            },
        )
    )

    # 暗示的
    call_log = _load_call_log("07_independence_implicit.json")
    cases.append(
        Case[dict, str](
            name="independence-implicit",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_type": "独立（子供）",
                    "confidence": "medium",
                    "timing": "近日中",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "独立（子供）",
                "detection_type": "implicit",
                "difficulty": "medium",
            },
        )
    )

    # ===== エッジケース =====
    # 複数イベント同時検出
    call_log = _load_call_log("08_multiple_events.json")
    cases.append(
        Case[dict, str](
            name="multiple-events",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "event_types": ["就職・転職", "引っ越し"],
                    "confidence": "high",
                    "multiple_events": True,
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "multiple",
                "detection_type": "explicit",
                "difficulty": "medium",
                "note": "転職と引っ越しの複合ケース",
            },
        )
    )

    # ライフイベントなし（ノイズ除去）
    call_log = _load_call_log("09_no_event.json")
    cases.append(
        Case[dict, str](
            name="no-event",
            input={
                "call_log": _format_transcript(call_log["transcript"]),
                "customer_id": call_log["customer_id"],
                "call_date": call_log["call_date"],
            },
            expected_output=json.dumps(
                {
                    "no_event_detected": True,
                    "detected_events": [],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": None,
                "detection_type": "none",
                "difficulty": "easy",
                "note": "ライフイベントなし（料金確認のみ）",
            },
        )
    )

    return cases


def create_step2_cases() -> list[Case[dict, str]]:
    """
    Step 2（履歴照合・パターン分析）のテストケースを作成する。

    過去のライフイベント履歴との照合、パターン分析のテストケースを含む。

    Returns:
        テストケースのリスト
    """
    cases = []

    # ===== 新規イベント（履歴なし） =====
    cases.append(
        Case[dict, str](
            name="new-event-no-history",
            input={
                "current_event": {
                    "event_type": "引っ越し",
                    "timing": "1ヶ月以内",
                    "confidence": "high",
                    "evidence": "来月引っ越すことになったので、インターネットの手続きについて確認したい",
                },
                "customer_id": "C-10001",
                "past_events": [],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": True,
                    "related_to_previous": False,
                    "pattern_analysis": "初回検出",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "新規顧客の初回イベント検出",
                "difficulty": "easy",
            },
        )
    )

    # ===== 既知イベントの続報（関連あり） =====
    cases.append(
        Case[dict, str](
            name="related-event-follow-up",
            input={
                "current_event": {
                    "event_type": "引っ越し",
                    "timing": "1ヶ月以内",
                    "confidence": "high",
                    "evidence": "来月引っ越すことになったので、インターネットの手続きについて確認したい",
                },
                "customer_id": "C-10001",
                "past_events": [
                    {
                        "date": "2024-06-15",
                        "event_type": "結婚",
                        "confidence": "high",
                    }
                ],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": True,
                    "related_to_previous": True,
                    "pattern_analysis": "結婚→引っ越し",
                    "life_stage": "新婚期",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "結婚後の新居への引っ越し",
                "difficulty": "medium",
            },
        )
    )

    # ===== 同一イベントの再報告（重複除去） =====
    cases.append(
        Case[dict, str](
            name="duplicate-event",
            input={
                "current_event": {
                    "event_type": "引っ越し",
                    "timing": "1ヶ月以内",
                    "confidence": "high",
                    "evidence": "新居への引っ越しの件でまた電話しました",
                },
                "customer_id": "C-10001",
                "past_events": [
                    {
                        "date": "2025-01-05",
                        "event_type": "引っ越し",
                        "confidence": "high",
                    }
                ],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": False,
                    "related_to_previous": True,
                    "pattern_analysis": "同一イベントの続報",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "同一引っ越しに関する再問い合わせ",
                "difficulty": "medium",
            },
        )
    )

    # ===== ライフステージの連続パターン =====
    cases.append(
        Case[dict, str](
            name="life-stage-pattern",
            input={
                "current_event": {
                    "event_type": "進学（子供）",
                    "timing": "3ヶ月以内",
                    "confidence": "high",
                    "evidence": "子供が4月から中学校に入学するので、スマホを持たせようと思っています",
                },
                "customer_id": "C-10009",
                "past_events": [
                    {
                        "date": "2013-03-01",
                        "event_type": "出産・子育て",
                        "confidence": "high",
                    }
                ],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": True,
                    "related_to_previous": True,
                    "pattern_analysis": "出産・子育て→進学（子供）",
                    "life_stage": "子育て期（学齢期）",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "子供の成長に伴うライフステージ変遷",
                "difficulty": "medium",
            },
        )
    )

    # ===== 複数イベントの履歴照合 =====
    cases.append(
        Case[dict, str](
            name="multiple-events-history",
            input={
                "current_event": {
                    "event_types": ["就職・転職", "引っ越し"],
                    "confidence": "high",
                },
                "customer_id": "C-10015",
                "past_events": [],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": True,
                    "related_to_previous": False,
                    "pattern_analysis": "転職に伴う引っ越し（同時発生）",
                    "life_stage": "キャリア転換期",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "転職と引っ越しの同時検出",
                "difficulty": "medium",
            },
        )
    )

    # ===== 退職後の一連のパターン =====
    cases.append(
        Case[dict, str](
            name="retirement-pattern",
            input={
                "current_event": {
                    "event_type": "独立（子供）",
                    "timing": "1ヶ月以内",
                    "confidence": "high",
                    "evidence": "息子が来月から一人暮らしを始めるので、契約を分けたい",
                },
                "customer_id": "C-10013",
                "past_events": [
                    {
                        "date": "2024-03-01",
                        "event_type": "退職・定年",
                        "confidence": "high",
                    }
                ],
            },
            expected_output=json.dumps(
                {
                    "is_new_event": True,
                    "related_to_previous": False,
                    "pattern_analysis": "子供の独立（退職とは別イベント）",
                    "life_stage": "シニア期・子供独立",
                },
                ensure_ascii=False,
            ),
            metadata={
                "scenario": "退職後に子供が独立",
                "difficulty": "medium",
            },
        )
    )

    return cases


def create_step3_cases() -> list[Case[dict, str]]:
    """
    Step 3（レコメンド生成）のテストケースを作成する。

    ライフイベントに基づくアクションレコメンドのテストケースを含む。

    Returns:
        テストケースのリスト
    """
    cases = []

    # ===== 引っ越し =====
    cases.append(
        Case[dict, str](
            name="recommend-moving",
            input={
                "event_type": "引っ越し",
                "confidence": "high",
                "timing": "1ヶ月以内",
                "customer_id": "C-10001",
                "life_stage": "転居準備期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "光回線移転手続きの案内", "priority": "high"},
                        {"action": "でんき・ガスセット割の提案", "priority": "medium"},
                        {"action": "引越し特典キャンペーンの案内", "priority": "low"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "引っ越し",
                "difficulty": "easy",
            },
        )
    )

    # ===== 結婚 =====
    cases.append(
        Case[dict, str](
            name="recommend-marriage",
            input={
                "event_type": "結婚",
                "confidence": "high",
                "timing": "1ヶ月以内",
                "customer_id": "C-10003",
                "life_stage": "新婚期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "家族割の提案", "priority": "high"},
                        {"action": "回線追加の案内", "priority": "medium"},
                        {"action": "新生活応援キャンペーンの案内", "priority": "low"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "結婚",
                "difficulty": "easy",
            },
        )
    )

    # ===== 出産・子育て =====
    cases.append(
        Case[dict, str](
            name="recommend-childbirth",
            input={
                "event_type": "出産・子育て",
                "confidence": "high",
                "timing": "完了済み",
                "customer_id": "C-10005",
                "life_stage": "子育て期（乳幼児）",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "見守りサービスの案内", "priority": "medium"},
                        {"action": "キッズ向けコンテンツの案内", "priority": "low"},
                        {"action": "将来のキッズスマホの案内", "priority": "low"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "出産・子育て",
                "difficulty": "easy",
            },
        )
    )

    # ===== 就職・転職 =====
    cases.append(
        Case[dict, str](
            name="recommend-job-change",
            input={
                "event_type": "就職・転職",
                "confidence": "high",
                "timing": "3ヶ月以内",
                "customer_id": "C-10007",
                "life_stage": "キャリア転換期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "プラン見直しの提案", "priority": "high"},
                        {"action": "リモートワーク向け高速プランの案内", "priority": "high"},
                        {"action": "モバイルWi-Fiの案内", "priority": "medium"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "就職・転職",
                "difficulty": "easy",
            },
        )
    )

    # ===== 進学（子供） =====
    cases.append(
        Case[dict, str](
            name="recommend-education",
            input={
                "event_type": "進学（子供）",
                "confidence": "high",
                "timing": "3ヶ月以内",
                "customer_id": "C-10009",
                "life_stage": "子育て期（学齢期）",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "学割の提案", "priority": "high"},
                        {"action": "子供用スマホの案内", "priority": "high"},
                        {"action": "家族割の確認・拡大", "priority": "medium"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "進学（子供）",
                "difficulty": "easy",
            },
        )
    )

    # ===== 退職・定年 =====
    cases.append(
        Case[dict, str](
            name="recommend-retirement",
            input={
                "event_type": "退職・定年",
                "confidence": "high",
                "timing": "3ヶ月以内",
                "customer_id": "C-10011",
                "life_stage": "シニア期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "シニア割引の提案", "priority": "high"},
                        {"action": "ライトプランへの変更案内", "priority": "high"},
                        {"action": "らくらくスマホの案内", "priority": "medium"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "退職・定年",
                "difficulty": "easy",
            },
        )
    )

    # ===== 独立（子供） =====
    cases.append(
        Case[dict, str](
            name="recommend-independence",
            input={
                "event_type": "独立（子供）",
                "confidence": "high",
                "timing": "1ヶ月以内",
                "customer_id": "C-10013",
                "life_stage": "子供独立期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "子供の新規契約サポート", "priority": "high"},
                        {"action": "家族割の再構成案内", "priority": "medium"},
                        {"action": "親御様向けプラン見直し", "priority": "low"},
                    ],
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "独立（子供）",
                "difficulty": "easy",
            },
        )
    )

    # ===== 複数イベント（転職+引っ越し） =====
    cases.append(
        Case[dict, str](
            name="recommend-multiple-events",
            input={
                "event_types": ["就職・転職", "引っ越し"],
                "confidence": "high",
                "customer_id": "C-10015",
                "life_stage": "キャリア転換期",
                "historical_context": None,
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "転居先での光回線新規契約", "priority": "high"},
                        {"action": "リモートワーク向け高速プランの案内", "priority": "high"},
                        {"action": "でんき・ガスセット割の提案", "priority": "medium"},
                    ],
                    "note": "転職と引っ越しの複合提案",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "multiple",
                "difficulty": "medium",
            },
        )
    )

    # ===== 結婚後の引っ越し（履歴考慮） =====
    cases.append(
        Case[dict, str](
            name="recommend-with-history",
            input={
                "event_type": "引っ越し",
                "confidence": "high",
                "timing": "1ヶ月以内",
                "customer_id": "C-20001",
                "life_stage": "新婚期・新生活開始",
                "historical_context": {
                    "previous_events": [
                        {"date": "2024-06-15", "event_type": "結婚"}
                    ],
                    "pattern": "結婚→引っ越し",
                },
            },
            expected_output=json.dumps(
                {
                    "recommendations": [
                        {"action": "新婚向け住宅セットプランの提案", "priority": "high"},
                        {"action": "でんき・ガスセット割の提案", "priority": "high"},
                        {"action": "家族割の継続確認", "priority": "medium"},
                    ],
                    "life_stage_summary": "新婚期・新生活開始",
                },
                ensure_ascii=False,
            ),
            metadata={
                "event_type": "引っ越し",
                "difficulty": "medium",
                "note": "結婚後の新居引っ越し（履歴を考慮した提案）",
            },
        )
    )

    return cases
