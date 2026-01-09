"""
評価実行ロジック。

CLIエントリーポイントとして `python -m app.evaluation.runner` で実行可能。
"""

import argparse
import json

from strands import Agent
from strands_evals import Case, Experiment

from ..config import MODEL_ID
from .cases import create_step1_cases
from .evaluators import create_step1_evaluators


def _load_summarize_prompt() -> str:
    """評価用のsummarize.mdからシステムプロンプトを読み込む"""
    from pathlib import Path

    # 評価用プロンプトを優先して使用（S3ツール取得指示なし）
    prompt_path = Path(__file__).parent.parent / "prompts" / "evaluation" / "summarize.md"
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
            case: テストケース（入力にs3_infoとfile_contentを含む）

        Returns:
            要約結果の文字列
        """
        # エージェントを作成（ツールなしで直接要約）
        agent = Agent(
            model=MODEL_ID,
            system_prompt=system_prompt,
            tools=[],  # 評価時はツールなしで直接ファイル内容を渡す
            callback_handler=None,  # コールバックを無効化
        )

        # ファイル内容を含むプロンプトを構築
        file_content = case.input.get("file_content", "")
        s3_info = case.input.get("s3_info", {})
        prompt = f"""以下のファイル内容を要約してください。

ファイル情報:
- バケット: {s3_info.get('bucket', 'N/A')}
- キー: {s3_info.get('key', 'N/A')}

ファイル内容:
{file_content}
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


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge評価を実行")
    parser.add_argument("--step1", action="store_true", help="Step 1（要約）の評価を実行")
    parser.add_argument("--all", action="store_true", help="全ステップの評価を実行")
    parser.add_argument("--output", type=str, help="結果をJSONファイルに出力")
    parser.add_argument("--quiet", action="store_true", help="詳細出力を抑制")

    args = parser.parse_args()

    if args.step1 or args.all or (not args.step1 and not args.all):
        # デフォルトはStep 1を実行
        reports = run_step1_evaluation(verbose=not args.quiet)

        if args.output:
            # 結果をJSONに出力
            results = []
            cases = create_step1_cases()
            for i, report in enumerate(reports):
                results.append(
                    {
                        "case_name": cases[i].name,
                        "overall_score": report.overall_score,
                        "test_passes": report.test_passes,
                    }
                )
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"結果を {args.output} に出力しました")


if __name__ == "__main__":
    main()
