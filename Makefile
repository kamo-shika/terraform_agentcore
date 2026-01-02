PROJECT_NAME = agentcore
REGION = ap-northeast-1
REPO_NAME = $(PROJECT_NAME)-repo
TF_DIR = terraform

# AWS Account ID and ECR URL retrieval
ACCOUNT_ID = $(shell aws sts get-caller-identity --query Account --output text)
ECR_URL = $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
IMAGE_URI = $(ECR_URL)/$(REPO_NAME):latest

.PHONY: init plan apply destroy login build push deploy deploy-init setup run-local

# --- Local Development ---
setup:
	uv sync

run-local:
	@if [ -f .env.local ]; then \
		echo "Loading environment variables from .env.local..."; \
		export $$(cat .env.local | grep -v '^#' | xargs) && uv run python app/main.py; \
	else \
		echo "No .env.local file found. Running without memory configuration..."; \
		uv run python app/main.py; \
	fi

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
# Apply Terraform changes AND push new image
deploy: apply push

# Initial deployment: Create ECR -> Push Image -> Create Agent
deploy-init:
	cd $(TF_DIR) && terraform apply -target=aws_ecr_repository.main -var="project_name=$(PROJECT_NAME)" -var="region=$(REGION)"
	$(MAKE) push
	$(MAKE) apply
