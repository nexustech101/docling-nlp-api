# 🚀 Deployment Guide

This guide covers different deployment options for the Docling NLP API with Firebase authentication, API tokens, and rate limiting.

## 📋 Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (for development mode)
- Firebase project (for authentication)
- Redis instance (for rate limiting)

## 🏃‍♂️ Quick Start

### Option 1: One-Command Deploy (Recommended)

**Windows PowerShell:**
```powershell
# Development
.\quick-deploy.ps1

# Production
.\quick-deploy.ps1 production
```

**Linux/macOS Bash:**
```bash
# Development  
./quick-deploy.sh

# Production
./quick-deploy.sh production
```

### Option 2: Manual Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Configuration

### 1. Environment Setup

Copy and customize the environment file:

**Development:**
```bash
cp app/.env.example .env
```

**Production:**
```bash
cp .env.prod.example .env.prod
```

### 2. Firebase Setup (Optional but Recommended)

1. **Create Firebase Project:**
   - Go to https://console.firebase.google.com
   - Create new project
   - Enable Authentication

2. **Generate Service Account Key:**
   - Project Settings → Service Accounts
   - Generate new private key
   - Download the JSON file

3. **Configure Environment:**
   ```bash
   # Option A: File path
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json
   
   # Option B: JSON string (recommended for containers)
   FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
   ```

### 3. Security Configuration

```bash
# Generate secure keys
JWT_SECRET_KEY=$(openssl rand -base64 64)
REDIS_PASSWORD=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 16)
```

## 🐳 Docker Deployment

### Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/docling-nlp-api.git
cd docling-nlp-api

# Quick deploy
./quick-deploy.sh
```

**Services included:**
- API Server (http://localhost:8000)
- Redis (localhost:6379)
- Nginx (http://localhost:80)
- Grafana (http://localhost:3000)
- Prometheus (http://localhost:9090)

### Production Environment

```bash
# Prepare environment
cp .env.prod.example .env.prod
# Edit .env.prod with your production values

# Deploy
./quick-deploy.sh production
```

**Additional production features:**
- SSL/TLS termination
- Enhanced security headers
- Resource limits
- Health checks
- Backup automation

## 🛠 Advanced Deployment

### Using the Python Deploy Script

```bash
# Install dependencies
pip install requests

# Deploy
python deploy/deploy.py deploy --environment production

# Other commands
python deploy/deploy.py status
python deploy/deploy.py logs --service docling-api --follow
python deploy/deploy.py backup
python deploy/deploy.py cleanup
```

### Manual Step-by-Step

1. **Build Images:**
   ```bash
   docker-compose build --no-cache
   ```

2. **Start Core Services:**
   ```bash
   # Start Redis first
   docker-compose up -d redis
   
   # Wait for Redis to be ready
   docker-compose up -d docling-api
   
   # Start remaining services
   docker-compose up -d
   ```

3. **Verify Deployment:**
   ```bash
   # Check service status
   docker-compose ps
   
   # Test API
   curl http://localhost:8000/health/
   ```

## 🌐 Production Considerations

### SSL/HTTPS Setup

1. **Obtain SSL Certificate:**
   ```bash
   # Using Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   
   # Copy certificates
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem config/nginx/ssl/cert.pem
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem config/nginx/ssl/key.pem
   ```

2. **Update Nginx Configuration:**
   - Uncomment HTTPS server block in `config/nginx/nginx.conf`
   - Update `server_name` with your domain

### Scaling

**Horizontal Scaling:**
```bash
# Scale API instances
docker-compose up -d --scale docling-api=3
```

**Resource Limits:**
```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

### Monitoring Setup

**Grafana Dashboard:**
1. Access: http://localhost:3000
2. Login: admin/admin (change immediately)
3. Import provided dashboard: `config/monitoring/grafana/`

**Prometheus Metrics:**
- API metrics: http://localhost:9090
- Custom alerts: `config/monitoring/rules/`

## 🔒 Security Checklist

### Pre-Production

- [ ] Change all default passwords
- [ ] Configure Firebase authentication
- [ ] Set up SSL certificates
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring alerts
- [ ] Configure automated backups

### Environment Variables

```bash
# Required for production
DEBUG=false
JWT_SECRET_KEY=<64-character-random-key>
FIREBASE_PROJECT_ID=<your-project-id>
FIREBASE_SERVICE_ACCOUNT_KEY=<service-account-json>
REDIS_PASSWORD=<secure-redis-password>
GRAFANA_PASSWORD=<secure-grafana-password>
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# API Health
curl http://localhost:8000/health/

# Service Status
docker-compose ps

# Logs
docker-compose logs -f docling-api
```

### Backup Strategy

**Automated Backups:**
```bash
# Create backup
python deploy/deploy.py backup

# Schedule with cron
0 2 * * * /path/to/deploy/deploy.py backup
```

**Manual Backup:**
```bash
# Configuration
tar -czf backup-config-$(date +%Y%m%d).tar.gz .env* config/

# Data volumes
docker run --rm -v docling_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-$(date +%Y%m%d).tar.gz -C /data .
```

### Updates & Rollbacks

**Update Application:**
```bash
# Pull latest code
git pull origin main

# Rebuild and deploy
python deploy/deploy.py deploy --no-cache

# Verify
python deploy/deploy.py status
```

**Rollback:**
```bash
python deploy/deploy.py rollback
```

## 🔧 Troubleshooting

### Common Issues

**1. Firebase Connection Issues:**
```bash
# Check credentials
docker-compose logs docling-api | grep -i firebase

# Verify project ID
echo $FIREBASE_PROJECT_ID
```

**2. Rate Limiting Not Working:**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Verify rate limiting is enabled
curl -v http://localhost:8000/health/
```

**3. SSL Certificate Issues:**
```bash
# Verify certificates
openssl x509 -in config/nginx/ssl/cert.pem -text -noout

# Check Nginx configuration
docker-compose exec nginx nginx -t
```

### Debug Mode

```bash
# Enable debug logging
docker-compose exec docling-api env DEBUG=true LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f docling-api
```

## 📞 Support

### Getting Help

1. **Documentation:** Check README.md and AUTHENTICATION.md
2. **Logs:** Always include relevant logs when reporting issues
3. **Configuration:** Verify environment variables are set correctly
4. **Health Checks:** Use built-in health endpoints to diagnose issues

### Performance Tuning

**Database Performance:**
- Monitor query performance
- Optimize indexes
- Use connection pooling

**API Performance:**
- Enable Redis caching
- Implement proper rate limiting
- Use CDN for static assets

**Resource Optimization:**
- Monitor CPU/memory usage
- Adjust worker processes
- Configure garbage collection

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Environment file configured
- [ ] Firebase project set up
- [ ] SSL certificates obtained
- [ ] DNS records configured
- [ ] Monitoring configured

### Deployment

- [ ] Services deployed successfully
- [ ] Health checks passing
- [ ] SSL/HTTPS working
- [ ] Authentication functional
- [ ] Rate limiting active

### Post-Deployment

- [ ] Performance monitoring active
- [ ] Backup system configured
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team trained on operations

---

**Need help?** Check the troubleshooting section or create an issue in the repository.
