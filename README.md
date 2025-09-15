# Lexiconnect

**IGT-first, graph-native tool for endangered/minority language documentation and research**

Lexiconnect is a modern web application designed specifically for linguistic researchers working with endangered and minority languages. Built with FastAPI backend and Next.js frontend, it provides comprehensive tools for language documentation, analysis, and preservation.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with Neo4j graph database
- **Frontend**: Next.js (TypeScript) with Tailwind CSS
- **Deployment**: Docker containers on Google Cloud Platform
- **Frontend Hosting**: Vercel
- **Storage**: Google Cloud Storage for file uploads
- **Database**: Neo4j graph database

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Google Cloud Platform account
- Vercel account (for frontend deployment)

### Local Development Setup

#### 🆓 Option 1: Free Tier (No GCP Billing Required)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Lexiconnect
   ```

2. **Start everything with one command**

   ```bash
   ./start-free.sh
   ```

   This will start:

   - FastAPI backend on `http://localhost:8000`
   - Next.js frontend on `http://localhost:3000`
   - Neo4j database on `bolt://localhost:7687`
   - Neo4j Browser interface on `http://localhost:7474`

#### ☁️ Option 2: Full Setup (GCP Integration)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Lexiconnect
   ```

2. **Set up backend environment**

   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**

   ```bash
   # From project root
   docker-compose up -d
   ```

   This will start:

   - FastAPI backend on `http://localhost:8000`
   - Neo4j database on `bolt://localhost:7687`
   - Neo4j Browser interface on `http://localhost:7474`

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

### Environment Variables

#### Backend (.env)

```env
# Environment
ENVIRONMENT=development
DEBUG=True

# Neo4j Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# JWT
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Google Cloud Platform
GCP_PROJECT_ID=your-gcp-project-id
GCP_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json
GCS_BUCKET_NAME=your-bucket-name
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## ☁️ Google Cloud Platform Setup

### 1. Create GCP Project

```bash
# Install gcloud CLI
gcloud auth login
gcloud projects create lexiconnect-project --name="Lexiconnect"
gcloud config set project lexiconnect-project
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  compute.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com
```

### 3. Deploy with Terraform

```bash
cd gcp/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id = "lexiconnect-project"
region = "us-central1"
neo4j_password = "secure-neo4j-password"
jwt_secret_key = "your-jwt-secret-key"
EOF

# Plan and apply
terraform plan
terraform apply
```

### 4. Set up Service Account

```bash
# Create service account
gcloud iam service-accounts create lexiconnect-backend \
  --display-name="Lexiconnect Backend Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding lexiconnect-project \
  --member="serviceAccount:lexiconnect-backend@lexiconnect-project.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding lexiconnect-project \
  --member="serviceAccount:lexiconnect-backend@lexiconnect-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Download service account key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=lexiconnect-backend@lexiconnect-project.iam.gserviceaccount.com

# Move to credentials directory
mkdir -p gcp-credentials
mv service-account.json gcp-credentials/
```

### 5. Deploy Backend to Cloud Run

```bash
# Build and deploy using Cloud Build
gcloud builds submit --config=gcp/cloudbuild.yaml .
```

## 🌐 Vercel Deployment (Frontend)

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Deploy to Vercel

```bash
cd frontend
vercel

# Follow the prompts:
# - Link to existing project or create new
# - Set build command: npm run build
# - Set output directory: .next
```

### 3. Configure Environment Variables

In Vercel dashboard, add environment variables:

- `NEXT_PUBLIC_API_URL`: Your Cloud Run backend URL

### 4. Set up Custom Domain (Optional)

```bash
vercel domains add your-domain.com
vercel alias your-app.vercel.app your-domain.com
```

## 🐳 Docker Commands

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild backend
docker-compose up -d --build backend
```

### Production

```bash
# Build production image
docker build -t lexiconnect-backend ./backend

# Run production container
docker run -p 8000:8000 \
  -e NEO4J_URI=bolt://your-neo4j-host:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your-neo4j-password \
  -e SECRET_KEY=your-production-secret \
  lexiconnect-backend
```

## 📁 Project Structure

```
Lexiconnect/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── languages.py
│   │   │   └── documentation.py
│   │   └── database.py
│   └── env.example
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── vercel.json
│   ├── tailwind.config.js
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── globals.css
│       └── providers.tsx
└── gcp/
    ├── cloudbuild.yaml
    └── terraform/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## 🔧 Development Workflow

1. **Make changes** to backend or frontend code
2. **Test locally** using Docker Compose
3. **Commit changes** to your repository
4. **Deploy backend** using Cloud Build
5. **Deploy frontend** using Vercel (automatic on git push)

## 📊 Monitoring and Logs

### Backend Logs (Cloud Run)

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=lexiconnect-backend" --limit 50
```

### Local Development Logs

```bash
docker-compose logs -f backend
```

## 🔒 Security Considerations

- Use strong passwords for Neo4j and JWT secret
- Enable Neo4j SSL/TLS connections in production
- Use least-privilege IAM roles for service accounts
- Regularly rotate service account keys and Neo4j passwords
- Restrict Neo4j network access to authorized IPs only
- Enable Cloud Armor for DDoS protection
- Use HTTPS in production (handled by Cloud Run and Vercel)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Neo4j connection failed**

   - Check NEO4J_URI format (should be bolt://host:7687)
   - Ensure Neo4j is running
   - Verify credentials (NEO4J_USER/NEO4J_PASSWORD)
   - Check firewall rules for ports 7474 and 7687

2. **GCP permissions denied**

   - Check service account permissions
   - Verify API enablement
   - Ensure correct project ID

3. **Frontend API calls failing**
   - Check NEXT_PUBLIC_API_URL configuration
   - Verify CORS settings in backend
   - Check network connectivity

### Getting Help

- Check the GitHub issues
- Review Docker and container logs
- Verify environment variable configuration
- Test API endpoints directly
