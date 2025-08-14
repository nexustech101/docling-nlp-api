# Docling NLP API

A production-ready FastAPI application for document processing using Docling, featuring document upload, URL processing, and multiple output formats with comprehensive error handling and monitoring.

## 🚀 Features

### Core Functionality
- **Document Upload Processing**: Upload and process PDF, DOCX, DOC, HTML, TXT, and Markdown files
- **URL Document Processing**: Process documents directly from URLs
- **Multiple Output Formats**: Convert to Markdown, HTML, Text, JSON, and DocTags
- **OCR Support**: Optional OCR processing for scanned documents
- **Metadata Extraction**: Automatic extraction of document metadata (page count, word count, etc.)

### Production Features
- **Async Processing**: Full asynchronous processing for better performance
- **Comprehensive Error Handling**: Structured exception handling with detailed error responses
- **Health Monitoring**: Health check endpoints with service status
- **Structured Logging**: Configurable logging with detailed context
- **File Validation**: Size limits, type validation, and security checks
- **Configuration Management**: Environment-based configuration
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Contributing](#contributing)

## 💻 Installation

### Prerequisites
- Python 3.12.10
- pip or poetry for dependency management

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/nexustech101/docling-nlp-api.git
cd docling-nlp-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Development Installation

```bash
# Install with development dependencies
pip install -r requirements.txt -r requirements-test.txt

# Or using poetry
poetry install --with dev
```

### Docker Installation

```bash
# Build Docker image
docker build -t docling-nlp-api .

# Run with Docker
docker run -p 8000:8000 docling-nlp-api
```

## 🚀 Quick Start

### 1. Quick Deploy (Recommended)

**Windows (PowerShell):**
```powershell
.\quick-deploy.ps1
```

**Linux/macOS (Bash):**
```bash
./quick-deploy.sh
```

**Manual Docker Compose:**
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Python Development Mode

```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt

# Run the application
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health/
- **Authentication**: http://localhost:8000/auth/
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
APP_NAME=Docling NLP API
VERSION=1.0.0
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000

# File Handling
UPLOAD_DIR=uploads
MAX_FILE_SIZE=52428800        # 50MB in bytes
MAX_URL_FILE_SIZE=104857600   # 100MB in bytes
ALLOWED_EXTENSIONS=.pdf,.docx,.doc,.html,.txt,.md

# Docling Configuration
DOCLING_CACHE_SIZE=1
ENABLE_OCR=true

# URL Processing
URL_TIMEOUT=30

# Logging
LOG_LEVEL=INFO

# CORS (for production, specify allowed origins)
ALLOWED_ORIGINS=*
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `UPLOAD_DIR` | `uploads` | Directory for temporary file uploads |
| `MAX_FILE_SIZE` | `52428800` | Maximum upload file size (bytes) |
| `MAX_URL_FILE_SIZE` | `104857600` | Maximum URL file size (bytes) |
| `URL_TIMEOUT` | `30` | Timeout for URL downloads (seconds) |
| `ENABLE_OCR` | `true` | Enable OCR processing |
| `DOCLING_CACHE_SIZE` | `1` | Number of cached Docling instances |

## 📚 API Documentation

### Core Endpoints

#### 1. Document Upload
```http
POST /documents/upload
Content-Type: multipart/form-data

Parameters:
- file: Document file (PDF, DOCX, DOC, HTML, TXT, MD)
- dest_format: Output format (markdown, html, text, json, doctags)
- use_ocr: Enable OCR (optional, default: false)
```

#### 2. URL Processing
```http
POST /documents/process-url
Content-Type: application/json

{
  "url": "https://example.com/document.pdf",
  "dest_format": "markdown",
  "use_ocr": false
}
```

#### 3. Health Check
```http
GET /health/

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 123.45,
  "docling_available": true
}
```

### Response Formats

#### Success Response
```json
{
  "status": "completed",
  "content": "# Document Title\n\nDocument content...",
  "metadata": {
    "page_count": 5,
    "word_count": 1250,
    "has_images": true,
    "has_tables": false,
    "source_url": "https://example.com/doc.pdf"  // for URL processing
  },
  "processing_time": 2.5,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Error Response
```json
{
  "error": "DocumentProcessingError",
  "detail": "Failed to process document: Invalid file format",
  "timestamp": 1642781234.567
}
```

### Supported Input Formats
- PDF (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- HTML (`.html`)
- Plain Text (`.txt`)
- Markdown (`.md`)

### Supported Output Formats
- **Markdown** (`markdown`): Clean, structured markdown
- **HTML** (`html`): Formatted HTML with styling
- **Text** (`text`): Plain text content
- **JSON** (`json`): Structured document data
- **DocTags** (`doctags`): XML-like structured format

## 💡 Usage Examples

### Python Client

```python
import requests
import json

# Upload document
def upload_document(file_path, dest_format="markdown", use_ocr=False):
    url = "http://localhost:8000/documents/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'dest_format': dest_format,
            'use_ocr': use_ocr
        }
        
        response = requests.post(url, files=files, data=data)
        return response.text if response.status_code == 200 else response.json()

# Process URL
def process_url(document_url, dest_format="markdown", use_ocr=False):
    url = "http://localhost:8000/documents/process-url"
    
    payload = {
        "url": document_url,
        "dest_format": dest_format,
        "use_ocr": use_ocr
    }
    
    response = requests.post(url, json=payload)
    return response.text if response.status_code == 200 else response.json()

# Examples
markdown_result = upload_document("./document.pdf", "markdown")
html_result = process_url("https://example.com/report.pdf", "html")
```

### cURL Examples

```bash
# Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf" \
  -F "dest_format=markdown" \
  -F "use_ocr=false"

# Process URL
curl -X POST "http://localhost:8000/documents/process-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/document.pdf",
    "dest_format": "html",
    "use_ocr": false
  }'

# Health check
curl -X GET "http://localhost:8000/health/"
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// Upload document
async function uploadDocument(filePath, destFormat = 'markdown', useOcr = false) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('dest_format', destFormat);
  form.append('use_ocr', useOcr);

  try {
    const response = await axios.post('http://localhost:8000/documents/upload', form, {
      headers: form.getHeaders()
    });
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error.response.data);
  }
}

// Process URL
async function processUrl(documentUrl, destFormat = 'markdown', useOcr = false) {
  try {
    const response = await axios.post('http://localhost:8000/documents/process-url', {
      url: documentUrl,
      dest_format: destFormat,
      use_ocr: useOcr
    });
    return response.data;
  } catch (error) {
    console.error('URL processing failed:', error.response.data);
  }
}
```

## 🔧 Development

### Project Structure

```
docling_nlp_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── dependencies.py     # Dependency injection
│   │   └── routes/
│   │       ├── documents.py    # Document processing routes
│   │       └── health.py       # Health check routes
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   └── exceptions.py       # Custom exceptions
│   ├── models/
│   │   ├── enums.py           # Enumerations
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── docling_service.py # Document processing logic
│   │   └── url_service.py     # URL processing logic
│   └── utils/
│       ├── file_utils.py      # File handling utilities
│       └── logger.py          # Logging configuration
├── tests/                      # Test suite
├── requirements.txt           # Production dependencies
├── requirements-test.txt      # Test dependencies
├── .env                       # Environment configuration
└── README.md                  # This file
```

### Code Style

This project follows:
- **PEP 8** for Python code style
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black app tests
isort app tests

# Lint code
flake8 app tests
mypy app
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "not integration"  # Skip integration tests
pytest tests/test_api_routes.py  # Specific test file

# Run with verbose output
pytest -v -s
```

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions (marked with `@pytest.mark.integration`)
- **API Tests**: Test HTTP endpoints and responses

### Test Structure

```
tests/
├── conftest.py                 # Test fixtures and configuration
├── test_config.py             # Configuration tests
├── test_models.py             # Model validation tests
├── test_exceptions.py         # Exception handling tests
├── test_file_utils.py         # File utility tests
├── test_docling_service.py    # Docling service tests
├── test_url_service.py        # URL service tests
├── test_api_routes.py         # API endpoint tests
└── test_integration.py        # Integration tests
```

### Writing Tests

```python
import pytest
from app.services.docling_service import DoclingService

class TestDoclingService:
    @pytest.fixture
    def docling_service(self):
        return DoclingService()
    
    @pytest.mark.asyncio
    async def test_process_document(self, docling_service, temp_file):
        result = await docling_service.process_document(
            temp_file, OutputFormat.MARKDOWN
        )
        assert result.status == ProcessingStatus.COMPLETED
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t docling-nlp-api .
docker run -p 8000:8000 -e LOG_LEVEL=INFO docling-nlp-api
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - MAX_FILE_SIZE=52428800
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

### Production Considerations

#### 1. Environment Configuration
```bash
# Production environment variables
export DEBUG=false
export LOG_LEVEL=WARNING
export ALLOWED_ORIGINS=https://yourdomain.com
export MAX_FILE_SIZE=104857600  # 100MB
```

#### 2. Security Headers
```python
# Add security middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 3. Load Balancing
```nginx
upstream api_servers {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://api_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 4. Monitoring Setup
```python
# Add Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

## 📊 Monitoring

### Health Checks

The API provides comprehensive health checking:

```http
GET /health/
```

Response includes:
- Service status
- Uptime information
- Docling service availability
- Version information

### Logging

Structured logging with configurable levels:

```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_LEVEL=INFO
```

Log format includes:
- Timestamp
- Log level
- Module name
- Function name and line number
- Message

### Metrics Collection

For production monitoring, consider integrating:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Sentry**: Error tracking
- **ELK Stack**: Log aggregation

### Performance Monitoring

Key metrics to monitor:
- Request latency
- Document processing time
- Error rates
- Memory usage
- File upload sizes
- Active connections

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes with tests**
   ```bash
   # Add your changes
   # Write tests for new functionality
   pytest  # Ensure all tests pass
   ```

4. **Format and lint**
   ```bash
   black app tests
   isort app tests
   flake8 app tests
   ```

5. **Submit pull request**

### Code Standards

- Follow PEP 8 style guide
- Write comprehensive docstrings
- Add type hints for all functions
- Include unit tests for new features
- Update documentation as needed

### Issue Reporting

When reporting issues, include:
- Python version
- Docling version
- Full error traceback
- Steps to reproduce
- Expected vs actual behavior

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Docling Team**: For the excellent document processing library
- **FastAPI Team**: For the fantastic web framework
- **Contributors**: All contributors to this project

## 🚀 Support

- **Documentation**: Check this README and API docs at `/docs`
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Use GitHub discussions for questions


---

## 🔧 Additional Configuration Files

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create uploads directory
RUN mkdir -p uploads

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  docling-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - MAX_FILE_SIZE=52428800
      - MAX_URL_FILE_SIZE=104857600
      - URL_TIMEOUT=30
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - docling-api
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  grafana-storage:
```

#### .dockerignore
```
.git
.gitignore
README.md
Dockerfile
.dockerignore
.env
.env.*
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.coverage
.pytest_cache
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.DS_Store
.vscode
.idea
uploads/
tests/
docs/
```

### GitHub Workflows

#### .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt -r requirements-test.txt
    
    - name: Lint with flake8
      run: |
        flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 app tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Format check with black
      run: |
        black --check app tests
    
    - name: Import sorting check with isort
      run: |
        isort --check-only app tests
    
    - name: Type check with mypy
      run: |
        mypy app
    
    - name: Test with pytest
      run: |
        pytest --cov=app --cov-report=xml --cov-report=html -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  docker:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t docling-nlp-api .
    
    - name: Test Docker image
      run: |
        docker run -d --name test-api -p 8000:8000 docling-nlp-api
        sleep 10
        curl -f http://localhost:8000/health/ || exit 1
        docker stop test-api
```

### Pre-commit Configuration

#### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Monitoring Configuration

#### monitoring/prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'docling-api'
    static_configs:
      - targets: ['docling-api:8000']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### monitoring/grafana/dashboards/api-dashboard.json
```json
{
  "dashboard": {
    "id": null,
    "title": "Docling API Dashboard",
    "tags": ["docling", "api"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      }
    ]
  }
}
```

### Nginx Configuration

#### nginx/nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream docling_api {
        server docling-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    # File upload limits
    client_max_body_size 100M;
    client_body_timeout 120s;
    client_header_timeout 120s;

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://docling_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }

        # Health check (no rate limiting)
        location /health/ {
            proxy_pass http://docling_api;
            proxy_set_header Host $host;
            access_log off;
        }
    }
}
```

### Development Tools

#### pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?
        
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["app"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "docling.*",
    "aiohttp.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow tests",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--cov=app",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "pass",
]
```

### Performance Testing

#### performance/locustfile.py
```python
from locust import HttpUser, task, between
import json

class DoclingAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when user starts"""
        # Check if API is healthy
        response = self.client.get("/health/")
        if response.status_code != 200:
            print("API is not healthy!")
    
    @task(3)
    def health_check(self):
        """Regular health check"""
        self.client.get("/health/")
    
    @task(1)
    def upload_small_document(self):
        """Upload a small test document"""
        files = {
            'file': ('test.txt', 'This is a test document content.', 'text/plain')
        }
        data = {
            'dest_format': 'markdown',
            'use_ocr': 'false'
        }
        
        with self.client.post(
            "/documents/upload", 
            files=files, 
            data=data, 
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")
    
    @task(1)
    def process_url(self):
        """Process document from URL"""
        payload = {
            "url": "https://httpbin.org/robots.txt",
            "dest_format": "text",
            "use_ocr": False
        }
        
        with self.client.post(
            "/documents/process-url",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"URL processing failed: {response.status_code}")
```

#### Run performance tests:
```bash
# Install locust
pip install locust

# Run performance test
locust -f performance/locustfile.py --host=http://localhost:8000
```

### Security Configuration

#### security/rate_limits.py
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

def setup_rate_limiting(app: FastAPI):
    """Setup rate limiting for the application"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return app

# Usage in routes:
# @limiter.limit("5/minute")
# async def upload_document(request: Request, ...):
#     ...
```

### Database Integration (Optional)

#### database/models.py
```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class ProcessingJob(Base):
    """Model for tracking document processing jobs"""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True)  # UUID
    filename = Column(String(255))
    source_url = Column(String(1000), nullable=True)
    dest_format = Column(String(20))
    use_ocr = Column(Boolean, default=False)
    status = Column(String(20), default="pending")
    content = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Deployment Scripts

#### scripts/deploy.sh
```bash
#!/bin/bash
set -e

echo "🚀 Deploying Docling NLP API..."

# Build and tag Docker image
docker build -t docling-nlp-api:latest .
docker tag docling-nlp-api:latest docling-nlp-api:$(git rev-parse --short HEAD)

# Run tests
echo "🧪 Running tests..."
docker run --rm docling-nlp-api:latest python -m pytest

# Deploy with docker-compose
echo "📦 Deploying services..."
docker-compose down
docker-compose up -d

# Health check
echo "🏥 Performing health check..."
sleep 10
if curl -f http://localhost:8000/health/; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed - health check failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
```

#### scripts/backup.sh
```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "📁 Creating backup in $BACKUP_DIR..."

# Backup configuration
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# Backup logs
docker-compose logs > $BACKUP_DIR/application.log

# Backup database (if using one)
# docker exec postgres pg_dump -U user dbname > $BACKUP_DIR/database.sql

echo "✅ Backup completed!"
```

---

**Made with ❤️ for the document processing community**

## 📈 Roadmap

### Version 2.0 (Planned Features)
- [ ] Batch document processing
- [ ] WebSocket support for real-time processing updates
- [ ] Document caching system
- [ ] Advanced OCR configuration options
- [ ] Document comparison features
- [ ] Multi-language support

### Version 2.5 (Future Features)
- [ ] Machine learning-based document classification
- [ ] Custom document processing pipelines
- [ ] Integration with cloud storage (AWS S3, Google Cloud Storage)
- [ ] Advanced analytics and reporting
- [ ] Document version control

## 🔧 Troubleshooting

### Common Issues

#### 1. Docling Import Error
```bash
Error: No module named 'docling'
Solution: pip install docling
```

#### 2. Large File Processing Timeout
```bash
Error: Request timeout
Solution: Increase timeout settings in .env:
URL_TIMEOUT=120
```

#### 3. Memory Issues with Large Documents
```bash
Error: Out of memory
Solution: 
- Increase Docker memory limits
- Process documents in smaller chunks
- Enable swap if needed
```

#### 4. Permission Denied on Upload Directory
```bash
Error: Permission denied
Solution: 
chmod 755 uploads/
# Or in Docker:
chown -R appuser:appuser /app/uploads
```

### Performance Optimization

1. **Enable Caching**: Use Redis for response caching
2. **Async Processing**: Implement background job queue
3. **Load Balancing**: Use multiple API instances
4. **CDN**: Serve static content via CDN
5. **Database Indexing**: Index frequently queried fields

### Debug Mode

Enable debug mode for development:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python -m app.main
```

This will provide:
- Detailed error messages
- Request/response logging
- Performance timing information
- Stack traces for debugging