# Test Strategy

## Objective

Ensure the backend service is stable and functioning as expected by validating its health endpoint in a CI environment. All tests must pass before the image is built and pushed to the container registry.

---

## Test Type

| Type       | Description                                        |
|------------|----------------------------------------------------|
| Unit Test  | Validate functionality in isolation (e.g. endpoints) |
| Mock Test  | Simulate backend response without a running server |

---

## Tooling

- `pytest` — Python testing framework
- `responses` — HTTP mocking library for `requests`

Install locally via:

```bash
pip install pytest responses
````

---

## Test Scope

### ✅ Included

* Health endpoint test: `GET /api/health`

### Excluded (Future Work)

* Database connectivity
* Auth/session handling
* Full integration tests

---

## CI Pipeline Integration

Tests are run in a dedicated `test` stage before the image is built:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run tests
        run: pytest tests/
```

If tests fail, the pipeline exits immediately.

---

## Example Test

File: `tests/test_backend.py`

```python
import requests
import responses

BASE_URL = "http://localhost:5000"

@responses.activate
def test_health_check():
    responses.add(
        responses.GET,
        f"{BASE_URL}/api/health",
        json={"status": "OK"},
        status=200,
    )

    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    assert "OK" in response.json()["status"]
```

---

## Notes

* Use mocking to avoid external dependencies.
* Keep test coverage minimal but meaningful.
* Extend scope as system complexity grows.