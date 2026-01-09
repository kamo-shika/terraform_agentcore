# コーディング規約

このルールは、すべてのコード変更時に適用されます。

## コメントとドキュメント

- **すべてのコメントとdocstringは日本語で記載すること**
- Shellスクリプトのコメントも日本語で記載
- Terraformのコメント（`#`）も日本語で記載

### Python docstring形式

```python
def function_name(arg1: str, arg2: int) -> str:
    """
    関数の簡潔な説明。

    Args:
        arg1: 引数1の説明
        arg2: 引数2の説明

    Returns:
        戻り値の説明

    Raises:
        ErrorType: エラー発生条件の説明
    """
```

### インラインコメント

```python
# S3バケットとオブジェクト情報を抽出
bucket = event.get("bucket")
```

## 命名規則

- 変数名や関数名は**英語**で記載（Pythonの命名規則に従う）
- クラス名: `PascalCase`
- 関数名・変数名: `snake_case`
- 定数: `UPPER_SNAKE_CASE`

## その他

- ログメッセージは英語でも日本語でも可
- エラーメッセージは状況に応じて適切な言語を選択
