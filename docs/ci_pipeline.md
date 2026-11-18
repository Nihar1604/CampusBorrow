Here is your updated `ci_pipeline.md` presented as a Markdown document ready to copy and paste:

---

````md
# CI Pipeline (GitHub Actions)

## Objective

Automate the build, test, and deployment preparation for the backend service.  
This workflow runs on pull requests and pushes to the `main` branch.

## Workflow File: `.github/workflows/ci.yml`

### Key Stages

1. **Checkout code**
2. **Run tests using Pytest**
3. **Set lowercase repo owner (for GHCR compatibility)**
4. **Log in to GitHub Container Registry**
5. **Build Docker image**
6. **Push Docker image to GHCR**

### Dependencies

- `pytest` for backend tests.
- `responses` for mocking HTTP requests during CI.

## Example Workflow

```yaml
name: Build, Test and Push Backend Image

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-build-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set lowercase repo owner
        id: vars
        run: echo "owner_lower=$(echo ${{ github.repository_owner }} | tr '[:upper:]' '[:lower:]')" >> $GITHUB_OUTPUT

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install responses

      - name: Run tests
        run: pytest backend/tests

      - name: Log in to GitHub Container Registry
        run: echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u ${{ steps.vars.outputs.owner_lower }} --password-stdin

      - name: Build Docker image
        run: docker build -t ghcr.io/${{ steps.vars.outputs.owner_lower }}/meeting-backend:latest ./backend

      - name: Push Docker image
        run: docker push ghcr.io/${{ steps.vars.outputs.owner_lower }}/meeting-backend:latest
````

## Secrets

* `GHCR_TOKEN`: GitHub Personal Access Token with `write:packages` and `read:packages` scope.