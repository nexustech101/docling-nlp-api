#!/bin/bash

# Quick Deploy Script for Docling NLP API
# Usage: ./quick-deploy.sh [development|production]

set -e

ENVIRONMENT=${1:-development}
PROJECT_ROOT=$(dirname "$0")

echo "🚀 Quick Deploy - Docling NLP API"
echo "=================================="
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

cd "$PROJECT_ROOT"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads logs data/redis data/prometheus data/grafana backups
chmod 755 uploads logs

# Copy environment file if it doesn't exist
if [ "$ENVIRONMENT" = "production" ]; then
    if [ ! -f ".env.prod" ]; then
        if [ -f ".env.prod.example" ]; then
            cp .env.prod.example .env.prod
            echo "⚠️  Created .env.prod from template. Please update it with your values!"
        else
            echo "❌ .env.prod.example not found. Please create production environment file."
            exit 1
        fi
    fi
    ENV_FILE=".env.prod"
    COMPOSE_FILE="docker-compose.prod.yml"
else
    if [ ! -f ".env" ]; then
        if [ -f "app/.env.example" ]; then
            cp app/.env.example .env
            echo "✅ Created .env from template."
        else
            echo "⚠️  No .env file found. Using default values."
        fi
    fi
    ENV_FILE=".env"
    COMPOSE_FILE="docker-compose.yml"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true

# Build images
echo "🏗️  Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Performing health check..."
MAX_ATTEMPTS=12
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        break
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "❌ Health check failed after $MAX_ATTEMPTS attempts."
        echo "📋 Service status:"
        docker-compose -f "$COMPOSE_FILE" ps
        echo "📋 API logs:"
        docker-compose -f "$COMPOSE_FILE" logs docling-api
        exit 1
    fi
    
    echo "⏳ Attempt $ATTEMPT/$MAX_ATTEMPTS failed, waiting 5 seconds..."
    sleep 5
    ATTEMPT=$((ATTEMPT + 1))
done

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Available Services:"
echo "   🔗 API Documentation: http://localhost:8000/docs"
echo "   🔗 Health Check: http://localhost:8000/health/"
echo "   🔗 Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "   🔗 Prometheus: http://localhost:9090"
echo ""
echo "📋 Useful Commands:"
echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f [service_name]"
echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
echo "   Restart service: docker-compose -f $COMPOSE_FILE restart [service_name]"
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔒 Production Security Checklist:"
    echo "   ✓ Update all default passwords in .env.prod"
    echo "   ✓ Configure SSL certificates in config/nginx/ssl/"
    echo "   ✓ Set up proper firewall rules"
    echo "   ✓ Configure monitoring alerts"
    echo "   ✓ Set up automated backups"
    echo ""
fi

echo "🚀 Ready to process documents!"
