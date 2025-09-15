#!/bin/bash

echo "🚀 Starting Lexiconnect in FREE mode..."
echo "This uses only local Docker containers - no GCP billing required!"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Start services
echo "📦 Starting all services..."
docker-compose -f docker-compose.free.yml up -d --build

echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose -f docker-compose.free.yml ps

echo ""
echo "✅ Lexiconnect is running!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo "📊 Neo4j Browser: http://localhost:7474"
echo "🔗 Neo4j Bolt: bolt://localhost:7687"
echo ""
echo "Neo4j Login: neo4j / password"
echo ""
echo "To stop: docker-compose -f docker-compose.free.yml down"
echo "To view logs: docker-compose -f docker-compose.free.yml logs -f"
