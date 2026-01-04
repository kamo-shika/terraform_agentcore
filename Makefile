PROJECT_NAME = agentcore
REGION = ap-northeast-1
REPO_NAME = $(PROJECT_NAME)-repo
TF_DIR = terraform

# AWS Account ID and ECR URL retrieval
ACCOUNT_ID = $(shell aws sts get-caller-identity --query Account --output text)
ECR_URL = $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com

# Git commit hash for image tagging
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_COMMIT_FULL = $(shell git rev-parse HEAD)

# Image URIs with version tags
IMAGE_URI_LATEST = $(ECR_URL)/$(REPO_NAME):latest
IMAGE_URI_VERSIONED = $(ECR_URL)/$(REPO_NAME):$(GIT_COMMIT)

.PHONY: init plan apply destroy login build push deploy deploy-init setup test test-cov ci-test update-endpoint get-runtime-info list-versions list-endpoints rollback lint format validate-tf clean help

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

# --- Terraform ---
init:
	cd $(TF_DIR) && terraform init

plan:
	cd $(TF_DIR) && terraform plan -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)" -var="image_tag=$(GIT_COMMIT)"

apply:
	cd $(TF_DIR) && terraform apply -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)" -var="image_tag=$(GIT_COMMIT)"

destroy:
	cd $(TF_DIR) && terraform destroy -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)" -var="image_tag=$(GIT_COMMIT)"

validate-tf:
	cd $(TF_DIR) && terraform validate

# --- Docker / ECR ---
login:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ECR_URL)

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
	cd $(TF_DIR) && terraform apply -target=aws_ecr_repository.main -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)" -var="image_tag=$(GIT_COMMIT)"
	$(MAKE) push
	$(MAKE) apply

# --- AgentCore Endpoint Management ---
# AgentCore Runtime IDを取得
RUNTIME_ID = $(shell cd $(TF_DIR) && terraform output -raw runtime_id 2>/dev/null)

# AgentCore Memory IDを取得（Dockerビルド時に注入）
MEMORY_ID = $(shell cd $(TF_DIR) && terraform output -raw memory_id 2>/dev/null)

# DEFAULTエンドポイントを最新バージョンに更新
update-endpoint:
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
	@echo "Updating AgentCore Runtime endpoint to latest version..."
	aws bedrock-agentcore-control update-agent-runtime-endpoint \
		--agent-runtime-id $(RUNTIME_ID) \
		--endpoint-name DEFAULT \
		--region $(REGION)
	@echo "Endpoint update initiated. Use 'make get-runtime-info' to check status."

# Runtime情報を表示
get-runtime-info:
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
	@echo "=== AgentCore Runtime Info ==="
	aws bedrock-agentcore-control get-agent-runtime \
		--agent-runtime-id $(RUNTIME_ID) \
		--region $(REGION)
	@echo ""
	@echo "=== AgentCore Runtime Endpoints ==="
	aws bedrock-agentcore-control list-agent-runtime-endpoints \
		--agent-runtime-id $(RUNTIME_ID) \
		--region $(REGION)

# Runtimeの全バージョン一覧を表示
list-versions:
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
	@echo "=== AgentCore Runtime Versions ==="
	aws bedrock-agentcore-control list-agent-runtime-versions \
		--agent-runtime-id $(RUNTIME_ID) \
		--region $(REGION)

# 全エンドポイント一覧を表示
list-endpoints:
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
	@echo "=== AgentCore Runtime Endpoints ==="
	aws bedrock-agentcore-control list-agent-runtime-endpoints \
		--agent-runtime-id $(RUNTIME_ID) \
		--region $(REGION)

# PRODエンドポイントを指定バージョンにロールバック
# 使用法: make rollback VERSION=V1
rollback:
	@if [ -z "$(RUNTIME_ID)" ]; then \
		echo "Error: Could not get Runtime ID. Run 'make apply' first."; \
		exit 1; \
	fi
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION is required. Usage: make rollback VERSION=V1"; \
		exit 1; \
	fi
	@echo "Rolling back PROD endpoint to version $(VERSION)..."
	aws bedrock-agentcore-control update-agent-runtime-endpoint \
		--agent-runtime-id $(RUNTIME_ID) \
		--endpoint-name PROD \
		--agent-runtime-version $(VERSION) \
		--region $(REGION)
	@echo "Rollback initiated. Use 'make list-endpoints' to check status."
