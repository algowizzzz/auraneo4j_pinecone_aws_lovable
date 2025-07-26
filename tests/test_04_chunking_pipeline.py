import pytest
import os
import json
from data_pipeline.create_graph_v5_integrated import IntegratedFinancialGraphBuilder

@pytest.fixture(scope="module")
def graph_builder():
    """Fixture to initialize the graph builder and clean up after tests."""
    URI = os.getenv("NEO4J_URI")
    USER = os.getenv("NEO4J_USERNAME")
    PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    if not all([URI, USER, PASSWORD]):
        pytest.skip("Missing Neo4j credentials in environment variables.")

    builder = IntegratedFinancialGraphBuilder(URI, USER, PASSWORD, use_pinecone=False)
    yield builder
    builder.close()

def find_large_test_file(data_dir="zion_10k_md&a_chunked", min_size_kb=50):
    """Find a file in the data directory that is larger than a certain size."""
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(data_dir, filename)
            if os.path.getsize(file_path) > min_size_kb * 1024:
                return file_path
    return None

@pytest.mark.end_to_end
def test_chunking_pipeline_end_to_end(graph_builder):
    """
    End-to-end test for the chunking pipeline.
    1. Clears the database.
    2. Finds a large file to ensure chunking is triggered.
    3. Runs the full graph build process on that single file.
    4. Validates the created graph structure in Neo4j.
    """
    # Step 1: Clear the database
    graph_builder.clear_database()
    graph_builder.create_full_schema()

    # Step 2: Find a large test file
    data_dir = "zion_10k_md&a_chunked"
    test_file = find_large_test_file(data_dir)
    
    if not test_file:
        pytest.skip(f"No file larger than 50KB found in {data_dir} for chunking test.")

    # Step 3: Run the graph build process
    # We create a temporary directory with just this one file to process
    temp_dir = "temp_test_data"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, os.path.basename(test_file))
    with open(test_file, 'r') as f_in, open(temp_file_path, 'w') as f_out:
        f_out.write(f_in.read())
        
    try:
        graph_builder.validate_and_build_graph(temp_dir, "*.json")
    finally:
        # Clean up the temporary file and directory
        os.remove(temp_file_path)
        os.rmdir(temp_dir)

    # Step 4: Validate the results in Neo4j
    with graph_builder.driver.session() as session:
        # Check that a SourceSection was created
        source_section_result = session.run(
            "MATCH (s:SourceSection {filename: $filename}) RETURN s",
            filename=os.path.basename(test_file)
        )
        source_node = source_section_result.single()
        assert source_node is not None, "SourceSection node was not created."

        # Check that Chunk nodes were created and are linked to the SourceSection
        chunk_result = session.run(
            "MATCH (s:SourceSection {filename: $filename})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) as chunk_count",
            filename=os.path.basename(test_file)
        )
        chunk_count = chunk_result.single()["chunk_count"]
        
        # Based on the chunking logic, a file > 50KB should definitely be chunked.
        assert chunk_count > 1, f"Expected multiple chunks, but found {chunk_count}."

        # Verify properties on a sample chunk
        sample_chunk_result = session.run(
            "MATCH (s:SourceSection {filename: $filename})-[:HAS_CHUNK]->(c:Chunk) "
            "WHERE c.chunk_id ENDS WITH '_chunk_0' "
            "RETURN c.text as text, c.embedding as embedding, c.word_count as word_count",
            filename=os.path.basename(test_file)
        )
        sample_chunk = sample_chunk_result.single()
        assert sample_chunk is not None
        assert sample_chunk["text"] is not None and len(sample_chunk["text"]) > 0
        assert sample_chunk["embedding"] is not None and len(sample_chunk["embedding"]) > 0
        assert sample_chunk["word_count"] > 0 