# Worktree運用ルール

このルールは、コード変更を伴う作業時に**必ず**適用されます。

## 必須ルール

### mainブランチでの直接作業禁止

mainブランチで直接コードを変更することは**禁止**です。

以下の手順で作業すること：

1. **別ワークツリーの作成**
   ```bash
   git worktree add -b feature/issue-XX-description ../terraform_agentcore-issue-XX
   cd ../terraform_agentcore-issue-XX
   ```

2. **作業実施** - コードの実装・修正・テスト

3. **コミット**
   ```bash
   git add .
   git commit -m "[Issue #XX] 変更内容の要約"
   ```

4. **プルリクエスト作成**
   ```bash
   git push -u origin feature/issue-XX-description
   gh pr create --title "Issue #XX対応: タイトル" --body "変更内容の説明"
   ```

## チェックポイント

作業開始時に現在のブランチを確認すること：

```bash
git branch --show-current
```

- **mainブランチの場合**: 作業を中止し、ワークツリーを作成
- **featureブランチの場合**: 作業を続行

## 禁止事項

- mainブランチで直接`git commit`すること
- mainブランチで直接ファイルを編集すること
- PRなしでmainにマージすること

## 例外

以下の場合はmainブランチでの作業を許可：
- `git pull`でのリモート同期
- `git worktree`コマンドの実行
- ファイルの読み取りのみ（変更なし）

## ワークツリー管理

### 一覧確認
```bash
git worktree list
```

### クリーンアップ（マージ後）
```bash
cd ../terraform_agentcore
git worktree remove ../terraform_agentcore-issue-XX
git branch -d feature/issue-XX-description
git pull origin main
```
