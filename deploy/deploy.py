#!/usr/bin/env python3
"""
Automated deployment script for Docling NLP API
Supports multiple deployment targets: local, docker, cloud
"""

import argparse
import subprocess
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional


class DeploymentManager:
    """Manages deployment of the Docling NLP API."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load deployment configuration."""
        config_path = self.project_root / "deploy" / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return {
            "environments": {
                "development": {
                    "compose_file": "docker-compose.yml",
                    "env_file": ".env.dev"
                },
                "production": {
                    "compose_file": "docker-compose.prod.yml",
                    "env_file": ".env.prod"
                }
            },
            "services": ["docling-api", "redis", "nginx", "prometheus", "grafana"],
            "health_check_url": "http://localhost:8000/health/",
            "timeout": 120
        }
    
    def run_command(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a shell command."""
        print(f"🔄 Running: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root
            )
            print(f"✅ Success: {command}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {command}")
            print(f"Error: {e.stderr}")
            raise
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        print("🔍 Checking prerequisites...")
        
        prerequisites = ["docker", "docker-compose"]
        missing = []
        
        for tool in prerequisites:
            try:
                self.run_command(f"{tool} --version")
            except subprocess.CalledProcessError:
                missing.append(tool)
        
        if missing:
            print(f"❌ Missing prerequisites: {', '.join(missing)}")
            return False
        
        print("✅ All prerequisites available")
        return True
    
    def build_images(self, no_cache: bool = False) -> None:
        """Build Docker images."""
        print("🏗️ Building Docker images...")
        
        cache_flag = "--no-cache" if no_cache else ""
        self.run_command(f"docker-compose build {cache_flag}")
    
    def deploy_local(self, environment: str = "development") -> None:
        """Deploy locally using Docker Compose."""
        print(f"🚀 Deploying locally ({environment})...")
        
        env_config = self.config["environments"].get(environment, {})
        compose_file = env_config.get("compose_file", "docker-compose.yml")
        env_file = env_config.get("env_file", ".env")
        
        # Check if environment file exists
        if not (self.project_root / env_file).exists():
            print(f"⚠️ Environment file {env_file} not found, using default values")
        
        # Stop existing containers
        self.run_command(f"docker-compose -f {compose_file} down")
        
        # Deploy services
        self.run_command(f"docker-compose -f {compose_file} up -d")
        
        # Wait for services to be ready
        self.wait_for_health_check()
    
    def deploy_production(self) -> None:
        """Deploy to production environment."""
        print("🚀 Deploying to production...")
        
        # Build production images
        self.build_images(no_cache=True)
        
        # Deploy with production configuration
        self.deploy_local("production")
        
        # Additional production checks
        self.verify_security_settings()
    
    def wait_for_health_check(self, timeout: int = None) -> None:
        """Wait for the health check endpoint to respond."""
        timeout = timeout or self.config["timeout"]
        health_url = self.config["health_check_url"]
        
        print(f"🏥 Waiting for health check at {health_url}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                import requests
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    print("✅ Health check passed!")
                    return
            except Exception as e:
                pass
            
            time.sleep(5)
        
        raise Exception(f"Health check failed after {timeout} seconds")
    
    def verify_security_settings(self) -> None:
        """Verify security settings for production."""
        print("🔒 Verifying security settings...")
        
        # Check environment variables
        required_env_vars = [
            "JWT_SECRET_KEY",
            "FIREBASE_SERVICE_ACCOUNT_KEY",
            "REDIS_PASSWORD"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                print(f"⚠️ Warning: {var} not set")
        
        # Check SSL certificates (if using HTTPS)
        ssl_cert_path = self.project_root / "config" / "nginx" / "ssl"
        if not ssl_cert_path.exists():
            print("⚠️ Warning: SSL certificates not found")
        
        print("✅ Security check completed")
    
    def rollback(self) -> None:
        """Rollback to previous deployment."""
        print("↩️ Rolling back deployment...")
        
        # Stop current containers
        self.run_command("docker-compose down")
        
        # Restore from backup (if available)
        backup_path = self.project_root / "backups" / "latest"
        if backup_path.exists():
            print("📁 Restoring from backup...")
            # Implementation depends on backup strategy
        else:
            print("⚠️ No backup found, manual intervention required")
    
    def backup(self) -> None:
        """Create backup of current deployment."""
        print("💾 Creating backup...")
        
        backup_dir = self.project_root / "backups" / f"backup_{int(time.time())}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration
        config_files = [".env", "docker-compose.yml", "config/"]
        for config_file in config_files:
            source = self.project_root / config_file
            if source.exists():
                if source.is_dir():
                    self.run_command(f"cp -r {source} {backup_dir}/")
                else:
                    self.run_command(f"cp {source} {backup_dir}/")
        
        # Backup data volumes
        self.run_command("docker run --rm -v docling_redis_data:/data -v $(pwd)/backups:/backup busybox tar czf /backup/redis_data.tar.gz -C /data .")
        
        print(f"✅ Backup created at {backup_dir}")
    
    def logs(self, service: str = None, follow: bool = False) -> None:
        """Show logs for services."""
        service_arg = service if service else ""
        follow_arg = "-f" if follow else ""
        
        self.run_command(f"docker-compose logs {follow_arg} {service_arg}")
    
    def status(self) -> None:
        """Show status of all services."""
        print("📊 Service Status:")
        self.run_command("docker-compose ps")
        
        print("\n🔍 Health Check:")
        try:
            import requests
            response = requests.get(self.config["health_check_url"], timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Status: {health_data.get('status', 'unknown')}")
                print(f"📈 Uptime: {health_data.get('uptime', 'unknown')} seconds")
            else:
                print(f"❌ API Status: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ API Status: {e}")
    
    def cleanup(self) -> None:
        """Clean up unused Docker resources."""
        print("🧹 Cleaning up...")
        
        # Remove unused images
        self.run_command("docker image prune -f")
        
        # Remove unused volumes
        self.run_command("docker volume prune -f")
        
        # Remove unused networks
        self.run_command("docker network prune -f")
        
        print("✅ Cleanup completed")


def main():
    """Main deployment script."""
    parser = argparse.ArgumentParser(description="Deploy Docling NLP API")
    
    parser.add_argument("action", choices=[
        "deploy", "build", "status", "logs", "backup", "rollback", "cleanup"
    ], help="Action to perform")
    
    parser.add_argument("--environment", "-e", choices=["development", "production"],
                       default="development", help="Deployment environment")
    
    parser.add_argument("--service", "-s", help="Specific service for logs")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")
    parser.add_argument("--no-cache", action="store_true", help="Build without cache")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Initialize deployment manager
    deployer = DeploymentManager(project_root)
    
    # Check prerequisites
    if not deployer.check_prerequisites():
        sys.exit(1)
    
    try:
        if args.action == "deploy":
            if args.environment == "production":
                deployer.deploy_production()
            else:
                deployer.deploy_local(args.environment)
        
        elif args.action == "build":
            deployer.build_images(args.no_cache)
        
        elif args.action == "status":
            deployer.status()
        
        elif args.action == "logs":
            deployer.logs(args.service, args.follow)
        
        elif args.action == "backup":
            deployer.backup()
        
        elif args.action == "rollback":
            deployer.rollback()
        
        elif args.action == "cleanup":
            deployer.cleanup()
        
        print(f"🎉 {args.action.title()} completed successfully!")
    
    except Exception as e:
        print(f"❌ {args.action.title()} failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
