#!/usr/bin/env python3
"""
Firebase Setup Guide Script
This script helps you collect Firebase configuration and set up environment variables.
"""

import json
import os
from pathlib import Path

def main():
    print("🔥 Firebase Setup Guide for Docling NLP API")
    print("=" * 50)
    
    print("\n📋 STEP 1: Get Web App Configuration")
    print("1. Go to Firebase Console → Project Settings → General")
    print("2. Scroll to 'Your apps' section")
    print("3. Click 'Add app' → Web app (</>) icon")
    print("4. App nickname: 'Docling NLP API'")
    print("5. Check 'Also set up Firebase Hosting' (optional)")
    print("6. Click 'Register app'")
    print("7. Copy the firebaseConfig object")
    
    print("\n📋 STEP 2: Get Service Account Key")
    print("1. Go to Firebase Console → Project Settings → Service accounts")
    print("2. Click 'Generate new private key'")
    print("3. Download the JSON file")
    print("4. Save it as 'firebase-service-account.json' in your project root")
    
    print("\n📋 STEP 3: Enter Configuration")
    print("Please provide the following information:")
    
    # Collect Firebase config
    config = {}
    
    print("\nFrom your Firebase Web App Config:")
    config['project_id'] = input("Project ID: ").strip()
    config['api_key'] = input("API Key: ").strip()
    config['auth_domain'] = input("Auth Domain: ").strip()
    config['database_url'] = input("Database URL (optional): ").strip() or None
    config['storage_bucket'] = input("Storage Bucket: ").strip()
    config['messaging_sender_id'] = input("Messaging Sender ID: ").strip()
    config['app_id'] = input("App ID: ").strip()
    
    print("\nFrom your Service Account JSON file:")
    service_account_path = input("Path to service account JSON file: ").strip()
    
    # Process service account
    if service_account_path and os.path.exists(service_account_path):
        try:
            with open(service_account_path, 'r') as f:
                service_account = json.load(f)
            
            config['service_account'] = {
                'private_key_id': service_account.get('private_key_id'),
                'private_key': service_account.get('private_key'),
                'client_email': service_account.get('client_email'),
                'client_id': service_account.get('client_id'),
                'token_uri': service_account.get('token_uri'),
            }
            print("✅ Service account loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading service account: {e}")
            return
    else:
        print("❌ Service account file not found!")
        return
    
    # Generate .env file
    env_content = f"""# Firebase Configuration
FIREBASE_PROJECT_ID={config['project_id']}
FIREBASE_API_KEY={config['api_key']}
FIREBASE_AUTH_DOMAIN={config['auth_domain']}
FIREBASE_DATABASE_URL={config['database_url'] or ''}
FIREBASE_STORAGE_BUCKET={config['storage_bucket']}
FIREBASE_MESSAGING_SENDER_ID={config['messaging_sender_id']}
FIREBASE_APP_ID={config['app_id']}

# Service Account Configuration
FIREBASE_PRIVATE_KEY_ID={config['service_account']['private_key_id']}
FIREBASE_PRIVATE_KEY="{config['service_account']['private_key']}"
FIREBASE_CLIENT_EMAIL={config['service_account']['client_email']}
FIREBASE_CLIENT_ID={config['service_account']['client_id']}
FIREBASE_TOKEN_URI={config['service_account']['token_uri']}

# API Configuration
ENABLE_ANALYTICS=true
ENABLE_RATE_LIMITING=true
LOG_LEVEL=INFO
"""
    
    # Write .env file
    env_path = Path('.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Environment file created: {env_path.absolute()}")
    
    # Generate client config for frontend
    client_config = {
        "apiKey": config['api_key'],
        "authDomain": config['auth_domain'],
        "databaseURL": config['database_url'],
        "projectId": config['project_id'],
        "storageBucket": config['storage_bucket'],
        "messagingSenderId": config['messaging_sender_id'],
        "appId": config['app_id']
    }
    
    client_config_path = Path('firebase-config.json')
    with open(client_config_path, 'w') as f:
        json.dump(client_config, f, indent=2)
    
    print(f"✅ Client config created: {client_config_path.absolute()}")
    
    print("\n🔧 Next Steps:")
    print("1. Set up Firestore Security Rules")
    print("2. Configure Authentication settings")
    print("3. Test the API with Firebase integration")
    print("4. Deploy to production")
    
    print("\n📝 Important Notes:")
    print("- Keep your .env file secure and never commit it to version control")
    print("- Add .env to your .gitignore file")
    print("- Use environment variables in production deployment")

if __name__ == "__main__":
    main()
