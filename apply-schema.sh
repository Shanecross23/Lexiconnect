# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

apply_schema() {
    local max_attempts=30
    local wait_time=2

    # Get the Neo4j container ID
    CONTAINER_ID=$(docker ps -qf "name=lexiconnect-neo4j")

    if [ -z "$CONTAINER_ID" ]; then
        echo "Neo4j container is not running"
        return 1
    fi

    # Check if schema file exists
    SCHEMA_FILE="$SCRIPT_DIR/backend/app/migrations/neo4j/schema.cypher"
    if [ ! -f "$SCHEMA_FILE" ]; then
        echo "Schema file not found at: $SCHEMA_FILE"
        return 1
    fi

    echo "Waiting for Neo4j to be ready..."
    
    # Wait for Neo4j to be ready
    for ((i=1; i<=$max_attempts; i++)); do
        if docker exec $CONTAINER_ID cypher-shell -u neo4j -p password "RETURN 1;" &>/dev/null; then
            echo "Neo4j is ready"
            break
        fi
        
        if [ $i -eq $max_attempts ]; then
            echo "Neo4j did not become ready in time"
            return 1
        fi
        
        echo "Attempt $i/$max_attempts - Waiting for Neo4j to be ready..."
        sleep $wait_time
    done

    echo "Applying schema to Neo4j database..."
    echo "Using schema file: $SCHEMA_FILE"

    # Apply schema
    if cat "$SCHEMA_FILE" | docker exec -i $CONTAINER_ID cypher-shell -u neo4j -p password; then
        echo "Schema applied successfully!"
        return 0
    else
        echo "Failed to apply schema"
        return 1
    fi
}

# If script is run directly, execute apply_schema
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    apply_schema
fi