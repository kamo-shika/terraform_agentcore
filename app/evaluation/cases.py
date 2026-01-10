"""
評価用テストケースの定義。

各ワークフローステップの評価に使用するテストケースを提供する。
（新ユースケース向けに実装予定）
"""

from strands_evals import Case


def create_step1_cases() -> list[Case[dict, str]]:
    """
    Step 1（ライフイベント検出）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    # 新ユースケース向けに実装予定
    return []


def create_step2_cases() -> list[Case[dict, str]]:
    """
    Step 2（履歴照合・パターン分析）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    # 新ユースケース向けに実装予定
    return []


def create_step3_cases() -> list[Case[dict, str]]:
    """
    Step 3（レコメンド生成）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    # 新ユースケース向けに実装予定
    return []
