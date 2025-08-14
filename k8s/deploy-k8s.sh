#!/bin/bash

# Kubernetes Deployment Script for Docling NLP API
# This script deploys the Docling NLP API to a Kubernetes cluster

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="docling-nlp"
IMAGE_NAME="docling-nlp-api"
IMAGE_TAG="latest"
KUBECTL_CONTEXT=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_success "kubectl found"
}

# Function to check if cluster is accessible
check_cluster() {
    print_status "Checking cluster connection..."
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_status "Please ensure you are connected to the correct cluster"
        exit 1
    fi
    print_success "Connected to Kubernetes cluster"
    kubectl cluster-info
}

# Function to create namespace
create_namespace() {
    print_status "Creating namespace: $NAMESPACE"
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f namespace.yaml
        print_success "Namespace $NAMESPACE created"
    fi
}

# Function to generate random base64 encoded secrets
generate_secret() {
    local length=$1
    openssl rand -base64 "$length" | tr -d '\n' | base64 | tr -d '\n'
}

# Function to setup secrets
setup_secrets() {
    print_status "Setting up secrets..."
    
    # Check if secrets already exist
    if kubectl get secret api-secrets -n "$NAMESPACE" &> /dev/null; then
        print_warning "Secret api-secrets already exists, skipping generation"
    else
        print_status "Generating JWT secret..."
        JWT_SECRET=$(generate_secret 64)
        
        # Update config.yaml with generated secrets
        sed -i.bak "s|jwt-secret: \"\"|jwt-secret: \"$JWT_SECRET\"|g" config.yaml
        print_success "JWT secret generated"
    fi
    
    if kubectl get secret redis-secret -n "$NAMESPACE" &> /dev/null; then
        print_warning "Secret redis-secret already exists, skipping generation"
    else
        print_status "Generating Redis password..."
        REDIS_PASSWORD=$(generate_secret 32)
        
        # Update config.yaml with generated secrets
        sed -i.bak "s|password: \"\"|password: \"$REDIS_PASSWORD\"|g" config.yaml
        print_success "Redis password generated"
    fi
    
    if kubectl get secret grafana-secret -n "$NAMESPACE" &> /dev/null; then
        print_warning "Secret grafana-secret already exists, skipping generation"
    else
        print_status "Generating Grafana admin password..."
        GRAFANA_PASSWORD=$(generate_secret 16)
        
        # Update monitoring.yaml with generated password
        sed -i.bak "s|admin-password: \"\"|admin-password: \"$GRAFANA_PASSWORD\"|g" monitoring.yaml
        print_success "Grafana password generated"
    fi
    
    # Check for Firebase service account
    if [ -z "$FIREBASE_SERVICE_ACCOUNT_KEY" ]; then
        print_warning "FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set"
        print_status "Please set Firebase service account key:"
        print_status "export FIREBASE_SERVICE_ACCOUNT_KEY=\$(cat path/to/serviceAccountKey.json | base64 | tr -d '\\n')"
    else
        print_status "Updating Firebase service account key..."
        sed -i.bak "s|service-account-key: \"\"|service-account-key: \"$FIREBASE_SERVICE_ACCOUNT_KEY\"|g" config.yaml
        print_success "Firebase service account key updated"
    fi
}

# Function to update configuration
update_config() {
    print_status "Updating configuration..."
    
    # Check for Firebase project ID
    if [ -z "$FIREBASE_PROJECT_ID" ]; then
        print_warning "FIREBASE_PROJECT_ID environment variable not set"
        print_status "Using default project ID. Update config.yaml manually if needed."
    else
        sed -i.bak "s|your-firebase-project-id|$FIREBASE_PROJECT_ID|g" config.yaml
        print_success "Firebase project ID updated"
    fi
    
    # Check for domain name
    if [ -n "$DOMAIN_NAME" ]; then
        print_status "Updating domain name to: $DOMAIN_NAME"
        sed -i.bak "s|api.your-domain.com|$DOMAIN_NAME|g" ingress.yaml
        print_success "Domain name updated"
    else
        print_warning "DOMAIN_NAME environment variable not set"
        print_status "Using default domain. Update ingress.yaml manually for production."
    fi
}

# Function to build and push Docker image
build_image() {
    local build_image=${1:-true}
    
    if [ "$build_image" = "true" ]; then
        print_status "Building Docker image..."
        
        # Go back to project root
        cd ..
        
        if [ ! -f "Dockerfile" ]; then
            print_error "Dockerfile not found in project root"
            exit 1
        fi
        
        # Build image
        docker build -t "$IMAGE_NAME:$IMAGE_TAG" .
        print_success "Docker image built successfully"
        
        # If using a registry, push the image
        if [ -n "$DOCKER_REGISTRY" ]; then
            print_status "Tagging image for registry: $DOCKER_REGISTRY"
            docker tag "$IMAGE_NAME:$IMAGE_TAG" "$DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
            
            print_status "Pushing image to registry..."
            docker push "$DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
            print_success "Image pushed to registry"
            
            # Update deployment to use registry image
            cd k8s
            sed -i.bak "s|image: docling-nlp-api:latest|image: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG|g" api-deployment.yaml
        fi
        
        cd k8s
    else
        print_status "Skipping Docker image build"
    fi
}

# Function to deploy to Kubernetes
deploy_k8s() {
    print_status "Deploying to Kubernetes..."
    
    # Apply configurations in order
    print_status "Creating namespace..."
    kubectl apply -f namespace.yaml
    
    print_status "Creating config maps and secrets..."
    kubectl apply -f config.yaml
    
    print_status "Deploying Redis..."
    kubectl apply -f redis-deployment.yaml
    
    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n "$NAMESPACE"
    print_success "Redis is ready"
    
    print_status "Deploying API..."
    kubectl apply -f api-deployment.yaml
    
    # Wait for API to be ready
    print_status "Waiting for API to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/docling-api -n "$NAMESPACE"
    print_success "API is ready"
    
    print_status "Setting up monitoring..."
    kubectl apply -f monitoring.yaml
    
    print_status "Setting up ingress..."
    kubectl apply -f ingress.yaml
    
    print_success "Deployment completed successfully!"
}

# Function to check deployment status
check_status() {
    print_status "Checking deployment status..."
    echo
    print_status "Pods:"
    kubectl get pods -n "$NAMESPACE"
    echo
    print_status "Services:"
    kubectl get services -n "$NAMESPACE"
    echo
    print_status "Ingress:"
    kubectl get ingress -n "$NAMESPACE"
    echo
}

# Function to get service URLs
get_urls() {
    print_status "Service URLs:"
    
    # Get ingress IP/hostname
    INGRESS_IP=$(kubectl get ingress docling-api-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    INGRESS_HOST=$(kubectl get ingress docling-api-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    
    if [ -n "$INGRESS_IP" ]; then
        print_success "API URL: https://$INGRESS_IP"
    elif [ -n "$INGRESS_HOST" ]; then
        print_success "API URL: https://$INGRESS_HOST"
    else
        print_warning "Ingress IP/hostname not available yet"
        DOMAIN=$(kubectl get ingress docling-api-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
        print_status "Configured domain: $DOMAIN"
    fi
    
    # Port forward commands for local access
    print_status "Local access (using port-forward):"
    echo "  API:        kubectl port-forward -n $NAMESPACE service/docling-api-service 8000:80"
    echo "  Grafana:    kubectl port-forward -n $NAMESPACE service/grafana-service 3000:3000"
    echo "  Prometheus: kubectl port-forward -n $NAMESPACE service/prometheus-service 9090:9090"
}

# Function to show logs
show_logs() {
    local service=${1:-docling-api}
    print_status "Showing logs for $service..."
    kubectl logs -n "$NAMESPACE" -l app="$service" --tail=100 -f
}

# Function to cleanup deployment
cleanup() {
    print_warning "This will delete the entire deployment. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up deployment..."
        kubectl delete namespace "$NAMESPACE" --ignore-not-found=true
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to scale deployment
scale() {
    local replicas=${1:-3}
    print_status "Scaling API to $replicas replicas..."
    kubectl scale deployment docling-api --replicas="$replicas" -n "$NAMESPACE"
    print_success "Scaling completed"
}

# Function to show help
show_help() {
    echo "Docling NLP API Kubernetes Deployment Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  deploy [--no-build]    Deploy the application to Kubernetes"
    echo "  status                 Check deployment status"
    echo "  logs [SERVICE]         Show logs (default: docling-api)"
    echo "  urls                   Show service URLs"
    echo "  scale [REPLICAS]       Scale the API deployment"
    echo "  cleanup               Remove the entire deployment"
    echo "  help                  Show this help message"
    echo
    echo "Environment Variables:"
    echo "  FIREBASE_PROJECT_ID              Firebase project ID"
    echo "  FIREBASE_SERVICE_ACCOUNT_KEY     Base64 encoded Firebase service account JSON"
    echo "  DOMAIN_NAME                      Domain name for ingress"
    echo "  DOCKER_REGISTRY                  Docker registry URL (optional)"
    echo "  KUBECTL_CONTEXT                  Kubectl context to use (optional)"
    echo
    echo "Examples:"
    echo "  $0 deploy                        Deploy with Docker build"
    echo "  $0 deploy --no-build             Deploy without building Docker image"
    echo "  $0 logs docling-api              Show API logs"
    echo "  $0 scale 5                       Scale to 5 replicas"
    echo
}

# Main execution
main() {
    local command=${1:-help}
    local option=$2
    
    # Set kubectl context if provided
    if [ -n "$KUBECTL_CONTEXT" ]; then
        kubectl config use-context "$KUBECTL_CONTEXT"
    fi
    
    case $command in
        "deploy")
            check_kubectl
            check_cluster
            create_namespace
            setup_secrets
            update_config
            
            if [ "$option" = "--no-build" ]; then
                build_image false
            else
                build_image true
            fi
            
            deploy_k8s
            echo
            check_status
            echo
            get_urls
            ;;
        "status")
            check_kubectl
            check_status
            ;;
        "logs")
            check_kubectl
            show_logs "$option"
            ;;
        "urls")
            check_kubectl
            get_urls
            ;;
        "scale")
            check_kubectl
            scale "$option"
            ;;
        "cleanup")
            check_kubectl
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
