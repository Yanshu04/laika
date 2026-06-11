from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from app.services.parser_service import PDFParser, DOCXParser, TextExtractionService

@patch("app.services.parser_service.PdfReader")
def test_pdf_parser(mock_pdf_reader):
    # Setup mock pages
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "  This is page 1 content.  "
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "This is page 2 content."
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page_1, mock_page_2]
    mock_pdf_reader.return_value = mock_reader
    
    # Run parser
    pages = PDFParser.parse(Path("mock_file.pdf"))
    
    # Assertions
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[0]["text"] == "This is page 1 content."
    assert pages[1]["page_number"] == 2
    assert pages[1]["text"] == "This is page 2 content."

@patch("app.services.parser_service.docx.Document")
def test_docx_parser(mock_docx_document):
    # Setup mock paragraphs
    mock_p1 = MagicMock()
    mock_p1.text = "Hello from DOCX paragraph 1."
    mock_p2 = MagicMock()
    mock_p2.text = "Hello from paragraph 2."
    
    # Setup mock tables
    mock_cell_1 = MagicMock()
    mock_cell_1.text = "Cell A"
    mock_cell_2 = MagicMock()
    mock_cell_2.text = "Cell B"
    
    mock_row = MagicMock()
    mock_row.cells = [mock_cell_1, mock_cell_2]
    
    mock_table = MagicMock()
    mock_table.rows = [mock_row]
    
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_p1, mock_p2]
    mock_doc.tables = [mock_table]
    mock_docx_document.return_value = mock_doc
    
    # Run parser
    res = DOCXParser.parse(Path("mock_file.docx"))
    
    # Assertions
    assert len(res) == 1
    assert res[0]["page_number"] is None
    assert "Hello from DOCX paragraph 1." in res[0]["text"]
    assert "Hello from paragraph 2." in res[0]["text"]
    assert "Cell A | Cell B" in res[0]["text"]

def test_text_extraction_service_unsupported():
    with pytest.raises(ValueError, match="Unsupported file extension"):
        TextExtractionService.extract_text(Path("mock_file.jpg"))

def test_text_parser(tmp_path):
    # Create a temp txt file
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello text content!", encoding="utf-8")
    
    res = TextExtractionService.extract_text(file_path)
    assert len(res) == 1
    assert res[0]["page_number"] is None
    assert res[0]["text"] == "Hello text content!"
