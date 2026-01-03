PROJECT_NAME = agentcore
REGION = ap-northeast-1
REPO_NAME = $(PROJECT_NAME)-repo
TF_DIR = terraform

# AWS Account ID and ECR URL retrieval
ACCOUNT_ID = $(shell aws sts get-caller-identity --query Account --output text)
ECR_URL = $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
IMAGE_URI = $(ECR_URL)/$(REPO_NAME):latest

.PHONY: init plan apply destroy login build push deploy deploy-init setup test test-cov ci-test update-endpoint get-runtime-info

# --- Local Development ---
setup:
	uv sync

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
	cd $(TF_DIR) && terraform plan -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)"

apply:
	cd $(TF_DIR) && terraform apply -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)"

destroy:
	cd $(TF_DIR) && terraform destroy -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)"

# --- Docker / ECR ---
login:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ECR_URL)

build:
	docker build -t $(REPO_NAME) .

push: login build
	docker tag $(REPO_NAME):latest $(IMAGE_URI)
	docker push $(IMAGE_URI)

# --- Workflow ---
# Push new image AND apply Terraform changes
# 重要: イメージをpushしてからapplyすることで、data.aws_ecr_image.latestが
# 最新のダイジェストを取得し、AgentCore Runtimeが更新される
deploy: push apply

# Initial deployment: Create ECR -> Push Image -> Create Agent
deploy-init:
	cd $(TF_DIR) && terraform apply -target=aws_ecr_repository.main -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)"
	$(MAKE) push
	$(MAKE) apply

# --- AgentCore Endpoint Management ---
# AgentCore Runtime IDを取得
RUNTIME_ID = $(shell cd $(TF_DIR) && terraform output -raw runtime_id 2>/dev/null)

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
