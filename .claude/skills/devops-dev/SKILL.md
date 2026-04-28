---
name: devops-dev
description: DevOps and infrastructure specialization — Docker multi-stage builds, CI/CD pipelines, GitHub Actions, health checks, monitoring, deployment. For application code use language-specific skills. Routed by PM or invoked directly for infrastructure tasks.
context: fork
agent: developer
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---
# DevOps/Infrastructure Development Mode

You are now in **DevOps specialization mode**. Before writing any code:

## 1. Load Project Conventions
```bash
Read /.claude/memory/standards/conventions.md
```

## 2. Query Context7 for Latest Docs
Based on the task, query relevant tool documentation:
- **Docker/Docker Compose**: For container configuration
- **GitHub Actions/GitLab CI**: For pipeline configuration
- **Terraform/Pulumi**: For infrastructure as code
- **Nginx/Caddy**: For reverse proxy and load balancing

## 3. Container Standards
- Multi-stage builds to minimize image size
- Non-root user in production containers
- `.dockerignore` to exclude dev files and secrets
- Health checks in Dockerfile and compose
- Pin base image versions (no `latest` tag)
- Environment variables for configuration (12-factor)

## 4. CI/CD Standards
- Fast feedback: lint → unit tests → build → integration → deploy
- Cache dependencies between runs
- Separate build and deploy stages
- Environment-specific configs (dev/staging/prod)
- Rollback strategy documented

## 5. Security
- No secrets in Dockerfiles or CI configs (use secrets managers)
- Scan images for vulnerabilities (Trivy, Snyk)
- Least-privilege IAM roles
- Network segmentation between services
- TLS everywhere (internal and external)

## Task
$ARGUMENTS
