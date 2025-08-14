# Quick Deploy Script for Docling NLP API (Windows PowerShell)
# Usage: .\quick-deploy.ps1 [development|production]

param(
    [string]$Environment = "development"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Quick Deploy - Docling NLP API" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Project Root: $PWD" -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Blue
$directories = @("uploads", "logs", "data\redis", "data\prometheus", "data\grafana", "backups")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Gray
    }
}

# Determine environment files
if ($Environment -eq "production") {
    $envFile = ".env.prod"
    $composeFile = "docker-compose.prod.yml"
    
    if (-not (Test-Path $envFile)) {
        if (Test-Path ".env.prod.example") {
            Copy-Item ".env.prod.example" $envFile
            Write-Host "⚠️  Created $envFile from template. Please update it with your values!" -ForegroundColor Yellow
        } else {
            Write-Host "❌ .env.prod.example not found. Please create production environment file." -ForegroundColor Red
            exit 1
        }
    }
} else {
    $envFile = ".env"
    $composeFile = "docker-compose.yml"
    
    if (-not (Test-Path $envFile)) {
        if (Test-Path "app\.env.example") {
            Copy-Item "app\.env.example" $envFile
            Write-Host "✅ Created $envFile from template." -ForegroundColor Green
        } else {
            Write-Host "⚠️  No $envFile file found. Using default values." -ForegroundColor Yellow
        }
    }
}

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Blue
try {
    docker-compose -f $composeFile down --remove-orphans 2>$null
} catch {
    Write-Host "   No existing containers to stop" -ForegroundColor Gray
}

# Build images
Write-Host "🏗️  Building Docker images..." -ForegroundColor Blue
docker-compose -f $composeFile build --no-cache

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Blue
docker-compose -f $composeFile up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Blue
Start-Sleep -Seconds 10

# Health check
Write-Host "🏥 Performing health check..." -ForegroundColor Blue
$maxAttempts = 12
$attempt = 1
$healthCheckPassed = $false

while ($attempt -le $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health/" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Health check passed!" -ForegroundColor Green
            $healthCheckPassed = $true
            break
        }
    } catch {
        # Continue trying
    }
    
    if ($attempt -eq $maxAttempts) {
        Write-Host "❌ Health check failed after $maxAttempts attempts." -ForegroundColor Red
        Write-Host "📋 Service status:" -ForegroundColor Blue
        docker-compose -f $composeFile ps
        Write-Host "📋 API logs:" -ForegroundColor Blue
        docker-compose -f $composeFile logs docling-api
        exit 1
    }
    
    Write-Host "⏳ Attempt $attempt/$maxAttempts failed, waiting 5 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    $attempt++
}

# Show service status
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Blue
docker-compose -f $composeFile ps

Write-Host ""
Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Available Services:" -ForegroundColor Blue
Write-Host "   🔗 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   🔗 Health Check: http://localhost:8000/health/" -ForegroundColor Cyan
Write-Host "   🔗 Grafana Dashboard: http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
Write-Host "   🔗 Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Useful Commands:" -ForegroundColor Blue
Write-Host "   View logs: docker-compose -f $composeFile logs -f [service_name]" -ForegroundColor Gray
Write-Host "   Stop services: docker-compose -f $composeFile down" -ForegroundColor Gray
Write-Host "   Restart service: docker-compose -f $composeFile restart [service_name]" -ForegroundColor Gray
Write-Host ""

if ($Environment -eq "production") {
    Write-Host "🔒 Production Security Checklist:" -ForegroundColor Red
    Write-Host "   ✓ Update all default passwords in .env.prod" -ForegroundColor Yellow
    Write-Host "   ✓ Configure SSL certificates in config/nginx/ssl/" -ForegroundColor Yellow
    Write-Host "   ✓ Set up proper firewall rules" -ForegroundColor Yellow
    Write-Host "   ✓ Configure monitoring alerts" -ForegroundColor Yellow
    Write-Host "   ✓ Set up automated backups" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "🚀 Ready to process documents!" -ForegroundColor Green

# Open browser to documentation (optional)
$openBrowser = Read-Host "Would you like to open the API documentation in your browser? (y/N)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:8000/docs"
}
