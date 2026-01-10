PROJECT_NAME = agentcore
REGION = ap-northeast-1
REPO_NAME = $(PROJECT_NAME)-repo
TF_DIR = terraform

# AWS CLIのデフォルトリージョンを設定（--region指定を省略可能に）
export AWS_DEFAULT_REGION = $(REGION)

# AWS Account ID and ECR URL retrieval
ACCOUNT_ID = $(shell aws sts get-caller-identity --query Account --output text)
ECR_URL = $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com

# Git commit hash for image tagging
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_COMMIT_FULL = $(shell git rev-parse HEAD)

# Image URIs with version tags
IMAGE_URI_LATEST = $(ECR_URL)/$(REPO_NAME):latest
IMAGE_URI_VERSIONED = $(ECR_URL)/$(REPO_NAME):$(GIT_COMMIT)

# Terraform共通設定
TF_CMD = cd $(TF_DIR) && terraform
TF_VARS = -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)" -var="image_tag=$(GIT_COMMIT)"

# AgentCore Runtime ID/Memory IDを取得（Dockerビルド時に注入）
RUNTIME_ID = $(shell $(TF_CMD) output -raw runtime_id 2>/dev/null)
MEMORY_ID = $(shell $(TF_CMD) output -raw memory_id 2>/dev/null)

# RUNTIME_IDチェックマクロ
define check_runtime_id
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
endef

.PHONY: init plan apply destroy login build push deploy deploy-init setup test test-cov ci-test eval eval-step1 eval-step2 eval-step3 update-endpoint get-runtime-info list-versions list-endpoints rollback lint format validate-tf clean help

# --- Help ---
help:
	@echo "使用可能なターゲット:"
	@echo ""
	@echo "  ローカル開発:"
	@echo "    setup          - 依存関係をインストール (uv sync)"
	@echo "    lint           - ruffでコード検査"
	@echo "    format         - ruffでコードフォーマット"
	@echo "    clean          - ビルド成果物を削除"
	@echo ""
	@echo "  テスト:"
	@echo "    test           - テストを実行"
	@echo "    test-cov       - カバレッジ付きでテストを実行"
	@echo "    ci-test        - CI用テスト (XML レポート出力)"
	@echo ""
	@echo "  評価 (LLM-as-a-Judge):"
	@echo "    eval           - 全ステップの評価を実行"
	@echo "    eval-step1     - Step 1 (要約) の評価を実行"
	@echo "    eval-step2     - Step 2 (パターン分析) の評価を実行"
	@echo "    eval-step3     - Step 3 (プロファイル生成) の評価を実行"
	@echo ""
	@echo "  Terraform:"
	@echo "    init           - terraform init"
	@echo "    plan           - terraform plan"
	@echo "    apply          - terraform apply"
	@echo "    destroy        - terraform destroy"
	@echo "    validate-tf    - terraform validate"
	@echo ""
	@echo "  Docker / ECR:"
	@echo "    login          - ECRにログイン"
	@echo "    build          - Dockerイメージをビルド"
	@echo "    push           - ECRにイメージをプッシュ"
	@echo ""
	@echo "  デプロイ:"
	@echo "    deploy         - イメージをプッシュしてTerraformを適用"
	@echo "    deploy-init    - 初回デプロイ (ECR作成 → イメージプッシュ → Agent作成)"
	@echo ""
	@echo "  AgentCore:"
	@echo "    get-runtime-info - Runtime情報とエンドポイント状態を表示"
	@echo "    list-versions    - Runtime全バージョン一覧を表示"
	@echo "    list-endpoints   - 全エンドポイント一覧を表示"
	@echo "    update-endpoint  - DEFAULTエンドポイントを最新バージョンに更新"
	@echo "    rollback VERSION=V1 - PRODエンドポイントを指定バージョンにロールバック"

# --- Local Development ---
setup:
	uv sync

lint:
	uv run ruff check app/ tests/

format:
	uv run ruff format app/ tests/
	uv run ruff check --fix app/ tests/

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf lambda_build
	rm -f lambda_function_payload.zip
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# --- Testing ---
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ --cov=app --cov-report=term-missing

ci-test:
	uv run pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing

# --- Evaluation (LLM-as-a-Judge) ---
eval:
	@echo "Running full evaluation..."
	uv run python -m app.evaluation.runner

eval-step1:
	@echo "Running Step 1 (summarize) evaluation..."
	uv run python -m app.evaluation.runner --step1

eval-step2:
	@echo "Running Step 2 (pattern analysis) evaluation..."
	uv run python -m app.evaluation.runner --step2

eval-step3:
	@echo "Running Step 3 (profile generation) evaluation..."
	uv run python -m app.evaluation.runner --step3

# --- Terraform ---
init:
	$(TF_CMD) init

plan:
	$(TF_CMD) plan $(TF_VARS)

apply:
	$(TF_CMD) apply -auto-approve $(TF_VARS)

destroy:
	$(TF_CMD) destroy $(TF_VARS)

validate-tf:
	$(TF_CMD) validate

# --- Docker / ECR ---
login:
	aws ecr get-login-password | docker login --username AWS --password-stdin $(ECR_URL)

# Dockerイメージをビルド（Memory IDを環境変数として注入）
# 注意: MEMORY_IDが取得できない場合はビルドを中止する（壊れたイメージのデプロイを防止）
build:
	@if [ -z "$(MEMORY_ID)" ]; then \
		echo ""; \
		echo "Error: MEMORY_ID is required but not found."; \
		echo ""; \
		echo "Possible causes:"; \
		echo "  1. Terraform state is not initialized (run 'make init' first)"; \
		echo "  2. AgentCore Memory resource has not been created (run 'make apply' first)"; \
		echo "  3. Working from a worktree without terraform state"; \
		echo ""; \
		echo "Solutions:"; \
		echo "  - Run 'make init && make apply' to initialize terraform state"; \
		echo "  - Or deploy from the main worktree where terraform state is available"; \
		echo ""; \
		exit 1; \
	fi
	@echo "Building with AGENTCORE_MEMORY_ID=$(MEMORY_ID)"
	docker build --build-arg AGENTCORE_MEMORY_ID=$(MEMORY_ID) -t $(REPO_NAME) .

push: login build
	docker tag $(REPO_NAME):latest $(IMAGE_URI_LATEST)
	docker tag $(REPO_NAME):latest $(IMAGE_URI_VERSIONED)
	docker push $(IMAGE_URI_LATEST)
	docker push $(IMAGE_URI_VERSIONED)
	@echo "Pushed images with tags: latest, $(GIT_COMMIT)"

# --- Workflow ---
# Push new image AND apply Terraform changes
# 重要: イメージをpushしてからapplyすることで、data.aws_ecr_image.latestが
# 最新のダイジェストを取得し、AgentCore Runtimeが更新される
deploy: push apply

# Initial deployment: Create ECR -> Push Image -> Create Agent
deploy-init:
	$(TF_CMD) apply -target=aws_ecr_repository.main $(TF_VARS)
	$(MAKE) push
	$(MAKE) apply

# --- AgentCore Endpoint Management ---
# DEFAULTエンドポイントを最新バージョンに更新
update-endpoint:
	$(check_runtime_id)
	@echo "Updating AgentCore Runtime endpoint to latest version..."
	aws bedrock-agentcore-control update-agent-runtime-endpoint \
		--agent-runtime-id $(RUNTIME_ID) \
		--endpoint-name DEFAULT
	@echo "Endpoint update initiated. Use 'make get-runtime-info' to check status."

# Runtime情報を表示
get-runtime-info:
	$(check_runtime_id)
	@echo "=== AgentCore Runtime Info ==="
	aws bedrock-agentcore-control get-agent-runtime \
		--agent-runtime-id $(RUNTIME_ID)
	@echo ""
	@echo "=== AgentCore Runtime Endpoints ==="
	aws bedrock-agentcore-control list-agent-runtime-endpoints \
		--agent-runtime-id $(RUNTIME_ID)

# Runtimeの全バージョン一覧を表示
list-versions:
	$(check_runtime_id)
	@echo "=== AgentCore Runtime Versions ==="
	aws bedrock-agentcore-control list-agent-runtime-versions \
		--agent-runtime-id $(RUNTIME_ID)

# 全エンドポイント一覧を表示
list-endpoints:
	$(check_runtime_id)
	@echo "=== AgentCore Runtime Endpoints ==="
	aws bedrock-agentcore-control list-agent-runtime-endpoints \
		--agent-runtime-id $(RUNTIME_ID)

# PRODエンドポイントを指定バージョンにロールバック
# 使用法: make rollback VERSION=V1
rollback:
	$(check_runtime_id)
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make rollback VERSION=V1"; \
		exit 1; \
	fi
	@echo "Rolling back PROD endpoint to version $(VERSION)..."
	aws bedrock-agentcore-control update-agent-runtime-endpoint \
		--agent-runtime-id $(RUNTIME_ID) \
		--endpoint-name PROD \
		--agent-runtime-version $(VERSION)
	@echo "Rollback initiated. Use 'make list-endpoints' to check status."
