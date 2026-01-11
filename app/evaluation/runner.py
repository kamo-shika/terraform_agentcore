"""
評価実行ロジック。

CLIエントリーポイントとして `python -m app.evaluation.runner` で実行可能。
"""

import argparse
import json

from strands import Agent
from strands.models import BedrockModel
from strands_evals import Case, Experiment

from ..config import MODEL_ID, REGION

# Nova 2 Liteのmax_tokens設定（デフォルトでは小さいため明示的に設定）
EVAL_MAX_TOKENS = 4096
from .cases import create_step1_cases, create_step2_cases, create_step3_cases
from .evaluators import create_step1_evaluators, create_step2_evaluators, create_step3_evaluators


def _load_summarize_prompt() -> str:
    """workflow/step1.mdから要約用プロンプトを読み込む"""
    from pathlib import Path

    prompt_path = Path(__file__).parent.parent / "prompts" / "workflow" / "step1.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "あなたはファイル分析の専門家です。ファイル内容を要約してください。"


def _create_task_function():
    """
    Step 1のタスク関数を作成する。

    テストケースの入力を受け取り、エージェントを実行して出力を返す。
    """
    system_prompt = _load_summarize_prompt()

    def task_function(case: Case[dict, str]) -> str:
        """
        Step 1のタスクを実行する。

        Args:
            case: テストケース（入力にcall_log, customer_id, call_dateを含む）

        Returns:
            ライフイベント検出結果の文字列
        """
        # エージェントを作成（ツールなしで直接分析）
        # Nova 2 Liteはmax_tokensの明示的な設定が必要
        bedrock_model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            max_tokens=EVAL_MAX_TOKENS,
        )
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=[],  # 評価時はツールなしで直接通話ログを渡す
            callback_handler=None,  # コールバックを無効化
        )

        # CS通話ログ分析用のプロンプトを構築
        call_log = case.input.get("call_log", "")
        customer_id = case.input.get("customer_id", "")
        call_date = case.input.get("call_date", "")

        prompt = f"""以下の通話ログを分析し、顧客のライフイベントを検出してください。

**通話ログ:**
```
{call_log}
```

**通話メタデータ:**
- 顧客ID: {customer_id}
- 通話日: {call_date}
"""

        response = agent(prompt)
        return str(response)  # 文字列を返す（OutputEvaluatorの要件）

    return task_function


def run_step1_evaluation(
    cases: list[Case[dict, str]] | None = None,
    verbose: bool = True,
) -> list:
    """
    Step 1（S3ファイル要約）の評価を実行する。

    Args:
        cases: テストケース（Noneの場合はデフォルトケースを使用）
        verbose: 詳細な出力を表示するかどうか

    Returns:
        評価レポートのリスト
    """
    if cases is None:
        cases = create_step1_cases()

    evaluators = create_step1_evaluators()
    experiment = Experiment[dict, str](cases=cases, evaluators=evaluators)

    task_function = _create_task_function()

    if verbose:
        print(f"Step 1評価を開始します（{len(cases)}ケース）...")
        print(f"使用モデル: {MODEL_ID}")
        print("-" * 50)

    reports = experiment.run_evaluations(task_function)

    if verbose:
        print("-" * 50)
        print("評価完了")
        for i, report in enumerate(reports):
            print(f"\n[ケース {i + 1}] {cases[i].name}")
            report.run_display()

    return reports


def _load_analyze_prompt() -> str:
    """workflow/step2.mdからパターン分析用プロンプトを読み込む"""
    from pathlib import Path

    prompt_path = Path(__file__).parent.parent / "prompts" / "workflow" / "step2.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "あなたはパターン分析の専門家です。要約からパターンを分析してください。"


def _create_step2_task_function():
    """
    Step 2のタスク関数を作成する。

    テストケースの入力を受け取り、エージェントを実行して出力を返す。
    """
    system_prompt = _load_analyze_prompt()

    def task_function(case: Case[dict, str]) -> str:
        """
        Step 2のタスクを実行する。

        Args:
            case: テストケース（入力にcurrent_event, customer_id, past_eventsを含む）

        Returns:
            履歴照合・パターン分析結果の文字列
        """
        # エージェントを作成（ツールなしで直接分析）
        # Nova 2 Liteはmax_tokensの明示的な設定が必要
        bedrock_model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            max_tokens=EVAL_MAX_TOKENS,
        )
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=[],
            callback_handler=None,
        )

        # 履歴照合用プロンプトを構築
        current_event = case.input.get("current_event", {})
        customer_id = case.input.get("customer_id", "")
        past_events = case.input.get("past_events", [])

        # current_eventの情報をJSON形式でフォーマット
        import json

        step1_result = json.dumps(current_event, ensure_ascii=False, indent=2)

        # past_eventsの情報をフォーマット
        if past_events:
            past_summaries_text = json.dumps(past_events, ensure_ascii=False, indent=2)
        else:
            past_summaries_text = "なし（初回検出）"

        prompt = f"""Step 1で検出されたライフイベントを、過去の検出履歴と照合し、パターン分析を行ってください。

**顧客ID:** {customer_id}

**今回検出されたイベント（Step 1の結果）:**
```
{step1_result}
```

**過去の検出履歴:**
```
{past_summaries_text}
```
"""

        response = agent(prompt)
        return str(response)

    return task_function


def run_step2_evaluation(
    cases: list[Case[dict, str]] | None = None,
    verbose: bool = True,
) -> list:
    """
    Step 2（パターン分析）の評価を実行する。

    Args:
        cases: テストケース（Noneの場合はデフォルトケースを使用）
        verbose: 詳細な出力を表示するかどうか

    Returns:
        評価レポートのリスト
    """
    if cases is None:
        cases = create_step2_cases()

    evaluators = create_step2_evaluators()
    experiment = Experiment[dict, str](cases=cases, evaluators=evaluators)

    task_function = _create_step2_task_function()

    if verbose:
        print(f"Step 2評価を開始します（{len(cases)}ケース）...")
        print(f"使用モデル: {MODEL_ID}")
        print("-" * 50)

    reports = experiment.run_evaluations(task_function)

    if verbose:
        print("-" * 50)
        print("評価完了")
        for i, report in enumerate(reports):
            print(f"\n[ケース {i + 1}] {cases[i].name}")
            report.run_display()

    return reports


def _load_profile_prompt() -> str:
    """workflow/step3.mdからプロファイル生成用プロンプトを読み込む"""
    from pathlib import Path

    prompt_path = Path(__file__).parent.parent / "prompts" / "workflow" / "step3.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "あなたはユーザープロファイル生成の専門家です。分析結果からプロファイルを生成してください。"


def _create_step3_task_function():
    """
    Step 3のタスク関数を作成する。

    テストケースの入力を受け取り、エージェントを実行して出力を返す。
    """
    system_prompt = _load_profile_prompt()

    def task_function(case: Case[dict, str]) -> str:
        """
        Step 3のタスクを実行する。

        Args:
            case: テストケース（入力にevent_type, confidence, timing, customer_id,
                  life_stage, historical_contextを含む）

        Returns:
            レコメンド生成結果の文字列
        """
        # エージェントを作成（ツールなしで直接生成）
        # Nova 2 Liteはmax_tokensの明示的な設定が必要
        bedrock_model = BedrockModel(
            model_id=MODEL_ID,
            region_name=REGION,
            max_tokens=EVAL_MAX_TOKENS,
        )
        agent = Agent(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=[],
            callback_handler=None,
        )

        # レコメンド生成用プロンプトを構築
        import json

        # 入力から各フィールドを取得
        event_type = case.input.get("event_type", "")
        event_types = case.input.get("event_types", [])  # 複数イベントの場合
        confidence = case.input.get("confidence", "")
        timing = case.input.get("timing", "")
        customer_id = case.input.get("customer_id", "")
        life_stage = case.input.get("life_stage", "")
        historical_context = case.input.get("historical_context")

        # Step 2の結果をシミュレート
        step2_result = {
            "customer_id": customer_id,
            "current_event": {
                "event_type": event_type if event_type else event_types,
                "confidence": confidence,
                "timing": timing,
            },
            "life_stage": life_stage,
        }

        # historical_contextがある場合は追加
        if historical_context:
            step2_result["historical_context"] = historical_context

        step2_result_text = json.dumps(step2_result, ensure_ascii=False, indent=2)

        prompt = f"""Step 2のパターン分析結果に基づいて、顧客へのサービス提案（レコメンド）を生成してください。

**パターン分析結果（Step 2の結果）:**
```
{step2_result_text}
```

**顧客ID:** {customer_id}
"""

        response = agent(prompt)
        return str(response)

    return task_function


def run_step3_evaluation(
    cases: list[Case[dict, str]] | None = None,
    verbose: bool = True,
) -> list:
    """
    Step 3（プロファイル生成）の評価を実行する。

    Args:
        cases: テストケース（Noneの場合はデフォルトケースを使用）
        verbose: 詳細な出力を表示するかどうか

    Returns:
        評価レポートのリスト
    """
    if cases is None:
        cases = create_step3_cases()

    evaluators = create_step3_evaluators()
    experiment = Experiment[dict, str](cases=cases, evaluators=evaluators)

    task_function = _create_step3_task_function()

    if verbose:
        print(f"Step 3評価を開始します（{len(cases)}ケース）...")
        print(f"使用モデル: {MODEL_ID}")
        print("-" * 50)

    reports = experiment.run_evaluations(task_function)

    if verbose:
        print("-" * 50)
        print("評価完了")
        for i, report in enumerate(reports):
            print(f"\n[ケース {i + 1}] {cases[i].name}")
            report.run_display()

    return reports


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge評価を実行")
    parser.add_argument("--step1", action="store_true", help="Step 1（要約）の評価を実行")
    parser.add_argument("--step2", action="store_true", help="Step 2（パターン分析）の評価を実行")
    parser.add_argument("--step3", action="store_true", help="Step 3（プロファイル生成）の評価を実行")
    parser.add_argument("--all", action="store_true", help="全ステップの評価を実行")
    parser.add_argument("--output", type=str, help="結果をJSONファイルに出力")
    parser.add_argument("--quiet", action="store_true", help="詳細出力を抑制")

    args = parser.parse_args()

    # 実行するステップを決定
    run_steps = []
    if args.all:
        run_steps = ["step1", "step2", "step3"]
    else:
        if args.step1:
            run_steps.append("step1")
        if args.step2:
            run_steps.append("step2")
        if args.step3:
            run_steps.append("step3")
        # 何も指定がなければデフォルトでstep1を実行
        if not run_steps:
            run_steps = ["step1"]

    all_results = []

    for step in run_steps:
        if step == "step1":
            reports = run_step1_evaluation(verbose=not args.quiet)
            cases = create_step1_cases()
        elif step == "step2":
            reports = run_step2_evaluation(verbose=not args.quiet)
            cases = create_step2_cases()
        elif step == "step3":
            reports = run_step3_evaluation(verbose=not args.quiet)
            cases = create_step3_cases()

        if args.output:
            for i, report in enumerate(reports):
                all_results.append(
                    {
                        "step": step,
                        "case_name": cases[i].name,
                        "overall_score": report.overall_score,
                        "test_passes": report.test_passes,
                    }
                )

    if args.output and all_results:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"結果を {args.output} に出力しました")


if __name__ == "__main__":
    main()
