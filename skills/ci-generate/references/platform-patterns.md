# CI/CD Platform Patterns

Detailed YAML structure and patterns for each supported CI/CD platform. Use these as reference templates, adapting commands and versions to match the actual project stack discovered in Phase 1.

## GitHub Actions

### Standard Node.js Pipeline

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".node-version"
          cache: "npm"  # or pnpm, yarn, bun
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check  # if tsconfig.json exists

  test:
    name: Test
    runs-on: ubuntu-latest
    timeout-minutes: 15
    # services: # Uncomment if tests need databases
    #   postgres:
    #     image: postgres:16
    #     env:
    #       POSTGRES_DB: test
    #       POSTGRES_USER: test
    #       POSTGRES_PASSWORD: test
    #     ports:
    #       - 5432:5432
    #     options: >-
    #       --health-cmd pg_isready
    #       --health-interval 10s
    #       --health-timeout 5s
    #       --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".node-version"
          cache: "npm"
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage/

  build:
    name: Build
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".node-version"
          cache: "npm"
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/  # or .next/, build/, out/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
      # Optional: Trivy for deeper scanning
      # - uses: aquasecurity/trivy-action@master
      #   with:
      #     scan-type: "fs"
      #     scan-ref: "."
```

### Standard Python Pipeline

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4  # for uv projects
        # OR: uses: actions/setup-python@v5
      - run: uv sync --extra dev
        # OR: pip install -r requirements-dev.txt
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pyright  # or mypy

  test:
    name: Test
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run pytest --cov --cov-report=xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage.xml

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run pip-audit  # or safety check
```

### Matrix Testing Pattern

```yaml
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest
```

### Docker Build & Push Pattern

```yaml
  docker:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: read
      packages: write
    outputs:
      # Downstream deploy jobs MUST consume this, not re-derive their own tag
      image: ${{ steps.meta.outputs.image }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        run: echo "image=ghcr.io/${{ github.repository }}:${{ github.sha }}" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.image }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Vercel Deployment Pattern

```yaml
  deploy:
    name: Deploy to Vercel
    runs-on: ubuntu-latest
    needs: [build]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: ".node-version"
      - run: npm i -g vercel
      - id: deploy
        run: |
          URL=$(vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }})
          echo "url=$URL" >> "$GITHUB_OUTPUT"
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

### AWS Deployment Pattern (ECS)

```yaml
  deploy:
    name: Deploy to AWS ECS
    runs-on: ubuntu-latest
    needs: [docker]
    if: github.ref == 'refs/heads/main'
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-arn: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecs-render-task-definition@v1
        id: render
        with:
          task-definition: task-definition.json
          container-name: app
          image: ${{ needs.docker.outputs.image }}
      - uses: aws-actions/amazon-ecs-deploy-task-definition@v2
        with:
          task-definition: ${{ steps.render.outputs.task-definition }}
          service: my-service
          cluster: my-cluster
          wait-for-service-stability: true
```

### Monorepo Path Filter Pattern

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            frontend:
              - 'frontend/**'
              - 'shared/**'
            backend:
              - 'backend/**'
              - 'shared/**'

  frontend:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... frontend-specific steps

  backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... backend-specific steps
```

---

## GitLab CI

### Standard Node.js Pipeline

```yaml
stages:
  - lint
  - test
  - build
  - security
  - deploy

default:
  image: node:22-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/

variables:
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

lint:
  stage: lint
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run lint
    - npm run type-check
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

test:
  stage: test
  script:
    - npm ci --cache .npm --prefer-offline
    - npm test -- --coverage
  coverage: '/All files\s*\|\s*[\d.]+/'
  artifacts:
    when: always
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

build:
  stage: build
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

security:
  stage: security
  script:
    - npm audit --audit-level=high
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Standard Python Pipeline

```yaml
stages:
  - lint
  - test
  - build
  - security

default:
  image: python:3.12-slim

variables:
  UV_CACHE_DIR: "$CI_PROJECT_DIR/.uv-cache"

lint:
  stage: lint
  before_script:
    - pip install uv
    - uv sync --extra dev
  script:
    - uv run ruff check .
    - uv run ruff format --check .
    - uv run pyright
  cache:
    key: uv-${CI_COMMIT_REF_SLUG}
    paths:
      - .uv-cache/

test:
  stage: test
  before_script:
    - pip install uv
    - uv sync --extra dev
  script:
    - uv run pytest --cov --cov-report=xml --junitxml=report.xml
  artifacts:
    when: always
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  cache:
    key: uv-${CI_COMMIT_REF_SLUG}
    paths:
      - .uv-cache/

security:
  stage: security
  before_script:
    - pip install uv
    - uv sync --extra dev
  script:
    - uv run pip-audit
  allow_failure: true
```

### GitLab Docker Build Pattern

```yaml
docker:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

---

## CircleCI

### Standard Node.js Pipeline

```yaml
version: 2.1

orbs:
  node: circleci/node@6.1

executors:
  default:
    docker:
      - image: cimg/node:22.0

jobs:
  lint:
    executor: default
    steps:
      - checkout
      - node/install-packages
      - run:
          name: Lint
          command: npm run lint
      - run:
          name: Type Check
          command: npm run type-check

  test:
    executor: default
    steps:
      - checkout
      - node/install-packages
      - run:
          name: Run Tests
          command: npm test -- --coverage
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: coverage

  build:
    executor: default
    steps:
      - checkout
      - node/install-packages
      - run:
          name: Build
          command: npm run build
      - persist_to_workspace:
          root: .
          paths:
            - dist/

  security:
    executor: default
    steps:
      - checkout
      - node/install-packages
      - run:
          name: Security Audit
          command: npm audit --audit-level=high

workflows:
  ci:
    jobs:
      - lint
      - test
      - security
      - build:
          requires:
            - lint
            - test
```

### Standard Python Pipeline

```yaml
version: 2.1

orbs:
  python: circleci/python@2.1

executors:
  default:
    docker:
      - image: cimg/python:3.12

jobs:
  lint:
    executor: default
    steps:
      - checkout
      - run:
          name: Install uv
          command: pip install uv
      - run:
          name: Install Dependencies
          command: uv sync --extra dev
      - run:
          name: Lint
          command: uv run ruff check .
      - run:
          name: Format Check
          command: uv run ruff format --check .
      - run:
          name: Type Check
          command: uv run pyright

  test:
    executor: default
    steps:
      - checkout
      - run:
          name: Install uv
          command: pip install uv
      - run:
          name: Install Dependencies
          command: uv sync --extra dev
      - run:
          name: Run Tests
          command: uv run pytest --cov --junitxml=test-results/results.xml
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: htmlcov

workflows:
  ci:
    jobs:
      - lint
      - test
```

---

## Jenkins

### Declarative Pipeline (Node.js)

```groovy
pipeline {
    agent {
        docker {
            image 'node:22-alpine'
        }
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        CI = 'true'
        HOME = '.'
    }

    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Quality') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'npm run lint'
                    }
                }
                stage('Type Check') {
                    steps {
                        sh 'npm run type-check'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                sh 'npm test -- --coverage'
            }
            post {
                always {
                    junit 'test-results/**/*.xml'
                    publishHTML(target: [
                        reportDir: 'coverage/lcov-report',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }

        stage('Security') {
            steps {
                sh 'npm audit --audit-level=high || true'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying...'
                // Add deployment steps
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            echo 'Pipeline failed!'
            // Add notification steps (Slack, email, etc.)
        }
    }
}
```

### Declarative Pipeline (Python)

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
        }
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Install') {
            steps {
                sh 'pip install uv'
                sh 'uv sync --extra dev'
            }
        }

        stage('Quality') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'uv run ruff check .'
                    }
                }
                stage('Format') {
                    steps {
                        sh 'uv run ruff format --check .'
                    }
                }
                stage('Type Check') {
                    steps {
                        sh 'uv run pyright'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                sh 'uv run pytest --cov --junitxml=test-results/results.xml'
            }
            post {
                always {
                    junit 'test-results/**/*.xml'
                }
            }
        }

        stage('Security') {
            steps {
                sh 'uv run pip-audit || true'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

---

## Common Patterns (Cross-Platform)

### Caching Strategies

| Package Manager | Cache Key | Cache Path |
|----------------|-----------|------------|
| npm | `package-lock.json` hash | `~/.npm` or `node_modules/` |
| pnpm | `pnpm-lock.yaml` hash | `~/.pnpm-store` |
| yarn | `yarn.lock` hash | `~/.yarn/cache` |
| bun | `bun.lockb` hash | `~/.bun/install/cache` |
| uv | `uv.lock` hash | `~/.cache/uv` |
| pip | `requirements*.txt` hash | `~/.cache/pip` |
| poetry | `poetry.lock` hash | `~/.cache/pypoetry` |
| cargo | `Cargo.lock` hash | `~/.cargo/registry` |
| go | `go.sum` hash | `~/go/pkg/mod` |

### Security Scanning Tools

| Language | Dependency Scan | SAST | Container Scan |
|----------|----------------|------|----------------|
| JavaScript | `npm audit`, Snyk | ESLint security plugin | Trivy |
| Python | `pip-audit`, Safety | Bandit, Semgrep | Trivy |
| Go | `govulncheck` | `staticcheck`, Semgrep | Trivy |
| Rust | `cargo audit` | `cargo clippy` | Trivy |
| Java | OWASP Dependency-Check | SpotBugs, Semgrep | Trivy |
| Ruby | `bundle-audit` | Brakeman | Trivy |

### Branch Protection Patterns

```
main/master branch:
  - Require PR reviews
  - Require status checks (lint, test, build)
  - Require up-to-date branches
  - No direct pushes

develop branch:
  - Require status checks
  - Allow direct pushes from maintainers

feature/* branches:
  - Run lint + test on PR
  - No deploy

release/* branches:
  - Full pipeline including deploy to staging
```

### Environment-Based Deployment

```
PR → lint + test + build (no deploy)
main → lint + test + build + deploy to staging
tag v*.*.* → lint + test + build + deploy to production
```
