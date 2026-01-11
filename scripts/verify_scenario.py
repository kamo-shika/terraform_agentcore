#!/usr/bin/env python
"""
検証シナリオ実行スクリプト。

Issue #155で定義された検証シナリオを実行し、結果をレポートする。

使用方法:
    # シナリオ1: 単一ライフイベント検出
    uv run python scripts/verify_scenario.py --scenario 1

    # シナリオ2: 履歴蓄積パターン
    uv run python scripts/verify_scenario.py --scenario 2

    # シナリオ3: 複数イベント同時検出
    uv run python scripts/verify_scenario.py --scenario 3

    # 全シナリオ実行
    uv run python scripts/verify_scenario.py --all

環境変数:
    MEMORY_ID: AgentCore MemoryのID（必須）
    TEST_S3_BUCKET: テスト用S3バケット名（シナリオ1, 3で必要）
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(title: str) -> None:
    """セクションヘッダーを出力"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_result(success: bool, message: str) -> None:
    """結果を出力"""
    status = "✓" if success else "✗"
    print(f"  {status} {message}")


def verify_environment() -> dict:
    """
    環境設定を検証する。

    Returns:
        環境設定の辞書
    """
    print_header("環境検証")

    config = {
        "memory_id": os.environ.get("MEMORY_ID"),
        "test_bucket": os.environ.get("TEST_S3_BUCKET"),
        "region": os.environ.get("AWS_REGION", "ap-northeast-1"),
    }

    # MEMORY_IDは必須
    if config["memory_id"]:
        print_result(True, f"MEMORY_ID: {config['memory_id']}")
    else:
        print_result(False, "MEMORY_ID が設定されていません")
        print("  → `export MEMORY_ID=<your-memory-id>` を実行してください")

    # TEST_S3_BUCKETはオプション
    if config["test_bucket"]:
        print_result(True, f"TEST_S3_BUCKET: {config['test_bucket']}")
    else:
        print_result(False, "TEST_S3_BUCKET が設定されていません（シナリオ1, 3で必要）")

    # AWS認証の確認
    try:
        import boto3
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print_result(True, f"AWS認証: {identity['Arn']}")
        config["aws_authenticated"] = True
    except Exception as e:
        print_result(False, f"AWS認証エラー: {e}")
        config["aws_authenticated"] = False

    return config


def run_scenario_1(config: dict) -> bool:
    """
    シナリオ1: 単一ライフイベント検出。

    引っ越しの話題を含む通話ログからイベントを検出する。
    """
    print_header("シナリオ1: 単一ライフイベント検出")
    print("  入力: 引っ越しの話題を含む通話ログ")
    print("  期待: 引っ越しイベント検出（confidence: high）")

    try:
        from app.evaluation.cases import create_step1_cases

        # テストケースを取得
        cases = create_step1_cases()
        moving_case = next((c for c in cases if c.name == "moving-explicit"), None)

        if not moving_case:
            print_result(False, "moving-explicitケースが見つかりません")
            return False

        # ケースの内容を表示
        print("\n  テストケース内容:")
        print(f"    名前: {moving_case.name}")
        print(f"    メタデータ: {moving_case.metadata}")

        # 期待出力を確認
        expected = json.loads(moving_case.expected_output)
        print(f"\n  期待される出力:")
        print(f"    event_type: {expected.get('event_type')}")
        print(f"    confidence: {expected.get('confidence')}")
        print(f"    timing: {expected.get('timing')}")

        # 検証
        success = (
            expected.get("event_type") == "引っ越し"
            and expected.get("confidence") == "high"
        )
        print_result(success, "テストケース検証完了")

        return success

    except Exception as e:
        print_result(False, f"エラー: {e}")
        return False


def run_scenario_2(config: dict) -> bool:
    """
    シナリオ2: 履歴蓄積パターン。

    結婚→引っ越しのパターンを検出する。
    """
    print_header("シナリオ2: 履歴蓄積パターン")
    print("  入力: 結婚後の引っ越しイベント")
    print("  期待: 「結婚→引っ越し」のパターン検出")

    try:
        from app.evaluation.cases import create_step2_cases

        # テストケースを取得
        cases = create_step2_cases()
        related_case = next(
            (c for c in cases if c.name == "related-event-follow-up"), None
        )

        if not related_case:
            print_result(False, "related-event-follow-upケースが見つかりません")
            return False

        # ケースの内容を表示
        print("\n  テストケース内容:")
        print(f"    名前: {related_case.name}")
        print(f"    入力イベント: {related_case.input.get('current_event', {}).get('event_type')}")
        print(f"    過去イベント: {related_case.input.get('past_events')}")

        # 期待出力を確認
        expected = json.loads(related_case.expected_output)
        print(f"\n  期待される出力:")
        print(f"    is_new_event: {expected.get('is_new_event')}")
        print(f"    related_to_previous: {expected.get('related_to_previous')}")
        print(f"    pattern_analysis: {expected.get('pattern_analysis')}")
        print(f"    life_stage: {expected.get('life_stage')}")

        # 検証
        success = (
            expected.get("is_new_event") is True
            and expected.get("related_to_previous") is True
            and "結婚" in expected.get("pattern_analysis", "")
        )
        print_result(success, "テストケース検証完了")

        return success

    except Exception as e:
        print_result(False, f"エラー: {e}")
        return False


def run_scenario_3(config: dict) -> bool:
    """
    シナリオ3: 複数イベント同時検出。

    転職と引っ越しの両方を同時に検出する。
    """
    print_header("シナリオ3: 複数イベント同時検出")
    print("  入力: 転職と引っ越しを含む通話ログ")
    print("  期待: 両方のイベントが検出される")

    try:
        from app.evaluation.cases import create_step1_cases

        # テストケースを取得
        cases = create_step1_cases()
        multiple_case = next((c for c in cases if c.name == "multiple-events"), None)

        if not multiple_case:
            print_result(False, "multiple-eventsケースが見つかりません")
            return False

        # ケースの内容を表示
        print("\n  テストケース内容:")
        print(f"    名前: {multiple_case.name}")
        print(f"    メタデータ: {multiple_case.metadata}")

        # 期待出力を確認
        expected = json.loads(multiple_case.expected_output)
        print(f"\n  期待される出力:")
        print(f"    event_types: {expected.get('event_types')}")
        print(f"    confidence: {expected.get('confidence')}")
        print(f"    multiple_events: {expected.get('multiple_events')}")

        # 検証
        event_types = expected.get("event_types", [])
        success = (
            "就職・転職" in event_types
            and "引っ越し" in event_types
            and expected.get("multiple_events") is True
        )
        print_result(success, "テストケース検証完了")

        return success

    except Exception as e:
        print_result(False, f"エラー: {e}")
        return False


def run_all_scenarios(config: dict) -> dict:
    """
    全シナリオを実行する。

    Returns:
        各シナリオの結果
    """
    results = {
        "scenario_1": run_scenario_1(config),
        "scenario_2": run_scenario_2(config),
        "scenario_3": run_scenario_3(config),
    }

    # サマリーを出力
    print_header("検証結果サマリー")
    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"  合計: {total} シナリオ")
    print(f"  成功: {passed} シナリオ")
    print(f"  失敗: {total - passed} シナリオ")

    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name}: {status}")

    return results


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="検証シナリオ実行スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3],
        help="実行するシナリオ番号（1, 2, 3）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="全シナリオを実行",
    )

    args = parser.parse_args()

    # タイトル
    print("\n" + "=" * 60)
    print(" CS通話ログ分析システム - 検証シナリオ実行")
    print(f" 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 環境検証
    config = verify_environment()

    # シナリオ実行
    if args.all:
        results = run_all_scenarios(config)
        success = all(results.values())
    elif args.scenario == 1:
        success = run_scenario_1(config)
    elif args.scenario == 2:
        success = run_scenario_2(config)
    elif args.scenario == 3:
        success = run_scenario_3(config)
    else:
        print("\n使用方法: --scenario N または --all を指定してください")
        parser.print_help()
        sys.exit(1)

    # 終了
    print("\n" + "=" * 60)
    if success:
        print(" 検証完了: すべて成功")
    else:
        print(" 検証完了: 一部失敗")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
