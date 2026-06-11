from app.services.chunking_service import ChunkingService

def test_split_text_small():
    text = "Short text."
    chunks = ChunkingService.split_text(text, chunk_size=500, overlap=10)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_split_text_boundaries():
    # Write a sentence that will split at whitespace
    # Length of "This is a long sentence that should split at a space boundary." is 63.
    # If chunk_size is 35, "This is a long sentence that should" (35 chars) or nearest space
    text = "This is a sentence that should split at a boundary. Let's see if it works."
    chunks = ChunkingService.split_text(text, chunk_size=40, overlap=10)
    
    # Assert that chunks were created
    assert len(chunks) > 1
    # Check that no words are cut in the middle (e.g. check for words split across chunks)
    for c in chunks:
        # Check that chunk does not end in alphabetical chars if next char is alphabetical,
        # but our splitter looks for " " space boundary backward so it will split at space.
        assert not c.startswith("ntence")  # should not cut "sentence" into c.g. "se" and "ntence"

def test_chunk_document_pdf():
    # Mock extracted pages
    pages = [
        {"page_number": 1, "text": "Page one text contents " * 20},  # ~440 chars
        {"page_number": 2, "text": "Page two text contents " * 30}   # ~660 chars
    ]
    
    # Run chunker with chunk_size 300, overlap 50
    chunks = ChunkingService.chunk_document(pages, chunk_size=300, overlap=50)
    
    # Assertions
    assert len(chunks) >= 4
    # Ensure page numbers are correct
    page_1_chunks = [c for c in chunks if c["page_number"] == 1]
    page_2_chunks = [c for c in chunks if c["page_number"] == 2]
    
    assert len(page_1_chunks) >= 2
    assert len(page_2_chunks) >= 2
    
    # Assert indices are incremental
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))
