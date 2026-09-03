from unittest.mock import MagicMock, patch
import pytest
from langchain_core.documents import Document
from app.services.document_parser import parse_pdf, parse_docx, parse_document

def test_parse_pdf_success():
    # Mock the PdfReader and extracted page text
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 Content."
    
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 Content."
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        docs = parse_pdf("path/to/test.pdf", "test.pdf")
        
        assert len(docs) == 2
        assert docs[0].page_content == "Page 1 Content."
        assert docs[0].metadata["source"] == "test.pdf"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["file_type"] == "pdf"
        assert docs[1].page_content == "Page 2 Content."
        assert docs[1].metadata["page"] == 2

def test_parse_docx_success():
    # Mock paragraphs structure
    mock_para_heading = MagicMock()
    mock_para_heading.text = "Chapter 1: The Beginning"
    mock_para_heading.style.name = "Heading 1"
    mock_para_heading.runs = []
    
    mock_para_text = MagicMock()
    mock_para_text.text = "This is paragraph text describing the start."
    mock_para_text.style.name = "Normal"
    mock_para_text.runs = []
    
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para_heading, mock_para_text]
    
    with patch("docx.Document", return_value=mock_doc):
        docs = parse_docx("path/to/test.docx", "test.docx")
        
        assert len(docs) == 1
        assert docs[0].page_content == "This is paragraph text describing the start."
        assert docs[0].metadata["source"] == "test.docx"
        assert docs[0].metadata["section"] == "Chapter 1: The Beginning"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["file_type"] == "docx"

def test_parse_document_routing():
    with patch("app.services.document_parser.parse_pdf", return_value=[]) as mock_pdf, \
         patch("app.services.document_parser.parse_docx", return_value=[]) as mock_docx:
         
        # Test routing for PDF
        parse_document("some_file.pdf", "some_file.pdf")
        mock_pdf.assert_called_once_with("some_file.pdf", "some_file.pdf")
        
        # Test routing for DOCX
        parse_document("some_file.docx", "some_file.docx")
        mock_docx.assert_called_once_with("some_file.docx", "some_file.docx")
        
        # Test unsupported extension raise
        with pytest.raises(ValueError) as excinfo:
            parse_document("some_file.txt", "some_file.txt")
        assert "Unsupported file extension" in str(excinfo.value)
