# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Bedrock AgentCore deployment project that packages and deploys AI agents to AWS using containerized runtimes. The project uses:
- **Strands Agents framework** for agent implementation
- **Bedrock AgentCore** for managed agent hosting on AWS
- **Terraform** for infrastructure provisioning
- **Docker + ECR** for containerized agent deployment
- **uv** for Python dependency management

## Architecture

### Application Structure
- `app/main.py` - Entry point with `handler()` function for AgentCore Runtime invocation
- `app/agent.py` - Agent configuration using Strands framework (Claude Sonnet 4.5 model)
- `app/memory.py` - AgentCore Memory integration setup (currently not wired into main handler)

### Infrastructure (Terraform)
- `terraform/agentcore.tf` - AgentCore Runtime and Memory resources
- `terraform/ecr.tf` - ECR repository for Docker images
- `terraform/iam.tf` - IAM roles and policies for Bedrock AgentCore service
- `terraform/backend.tf` - Terraform state backend configuration
- `terraform/variables.tf` - Project configuration (defaults to `ap-northeast-1`)

### Key Architecture Notes
- AgentCore Runtime pulls container images from ECR
- The container must expose a handler function compatible with AgentCore's invocation model
- Memory integration exists in `memory.py` but is not currently used in the main handler
- Network mode is PUBLIC (configured in agentcore.tf:13)

## Development Commands

### Local Development
```bash
# Setup dependencies
make setup                    # Installs dependencies with uv sync

# Run agent locally
make run-local               # Runs app/main.py directly for testing
```

### Docker Build and Push
```bash
# Build Docker image
make build                   # Builds image tagged as agentcore-repo:latest

# Login to ECR
make login                   # Authenticates Docker with ECR

# Build and push to ECR
make push                    # Runs login + build + tag + push
```

### Terraform Deployment
```bash
# Initialize Terraform
make init                    # cd terraform && terraform init

# Plan infrastructure changes
make plan                    # Preview changes with default variables

# Apply infrastructure
make apply                   # Deploy/update all resources

# Destroy infrastructure
make destroy                 # Tear down all resources
```

### Deployment Workflows

**Initial deployment** (creates ECR, then image, then agent):
```bash
make deploy-init             # 1. Create ECR repo
                            # 2. Build & push image
                            # 3. Create AgentCore runtime & memory
```

**Regular deployment** (update both infrastructure and code):
```bash
make deploy                  # Apply terraform + push new image
```

## Configuration

### Default Settings (Makefile)
- PROJECT_NAME: `agentcore`
- REGION: `ap-northeast-1`
- Model: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` (Japan region endpoint)

### Modifying Configuration
Override Makefile variables or edit `terraform/variables.tf` defaults. Terraform commands accept `-var` flags for runtime customization.

## Agent Development

### Adding Tools to Agent
Edit `app/agent.py` and add tools to the `tools=[]` parameter. Available via `strands-agents-tools` package.

### Memory Integration
The `create_memory()` function in `app/memory.py` is ready but not integrated. To enable:
1. Import in `main.py`
2. Extract memory_id, session_id, actor_id from event
3. Pass session_manager to agent configuration

### Event Structure
AgentCore invokes with event format:
```python
{
  "input": {
    "text": "user input here"
  }
}
```
