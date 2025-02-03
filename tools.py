from typing import List
import os
import base64
from pydantic import BaseModel, Field
from docx2pdf import convert as docx2pdf_convert
from pdf2image import convert_from_path
from langchain_openai import ChatOpenAI
from langchain.tools import tool

class DocxToPdfResult(BaseModel):
    pdf_path: str = Field(description="Path to the generated PDF file")
    success: bool = Field(description="Whether the conversion was successful")
    error: str = Field(default="", description="Error message if conversion failed")

class PdfToPngResult(BaseModel):
    png_paths: List[str] = Field(description="List of paths to the generated PNG files")
    success: bool = Field(description="Whether the conversion was successful")
    error: str = Field(default="", description="Error message if conversion failed")

class MarkdownResult(BaseModel):
    markdown_path: str = Field(description="Path to the generated Markdown file")
    success: bool = Field(description="Whether the conversion was successful")
    error: str = Field(default="", description="Error message if conversion failed")

@tool
def docx_to_pdf_converter(docx_path: str, output_dir: str) -> DocxToPdfResult:
    """
    Convert a DOCX file to PDF format. This function requires both a DOCX file path and an output directory.

    Parameters:
        docx_path (str): The path to the DOCX file to be converted. (Required)
        output_dir (str): The directory where the output PDF will be saved. (Required)

    Returns:
        DocxToPdfResult: The result of the conversion, including the path to the PDF and a success flag.
    """
    try:
        pdf_dir = os.path.join(output_dir, "pdf_files")
        os.makedirs(pdf_dir, exist_ok=True)
        
        doc_name = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(pdf_dir, f"{doc_name}.pdf")
        
        docx2pdf_convert(docx_path, pdf_path)
        return DocxToPdfResult(pdf_path=pdf_path, success=True)
    except Exception as e:
        return DocxToPdfResult(pdf_path="", success=False, error=str(e))

@tool
def pdf_to_png_converter(pdf_path: str, output_dir: str, dpi: int = 300) -> PdfToPngResult:
    """Convert a PDF file to PNG images. Takes pdf_path, output_dir, and optional dpi as parameters."""
    try:
        png_dir = os.path.join(output_dir, "png_files")
        os.makedirs(png_dir, exist_ok=True)
        
        pages = convert_from_path(pdf_path, dpi=dpi)
        png_paths = []
        
        for i, page in enumerate(pages):
            png_path = os.path.join(png_dir, f"page_{i+1}.png")
            page.save(png_path, "PNG")
            png_paths.append(png_path)
            
        return PdfToPngResult(png_paths=png_paths, success=True)
    except Exception as e:
        return PdfToPngResult(png_paths=[], success=False, error=str(e))

@tool
def png_to_markdown_converter(png_paths: List[str], output_dir: str) -> MarkdownResult:
    """Convert PNG files to Markdown format. Takes a list of png_paths and output_dir as parameters."""
    try:
        markdown_dir = os.path.join(output_dir, "markdown_files")
        os.makedirs(markdown_dir, exist_ok=True)
        
        llm = ChatOpenAI(model="gpt-4-vision-preview")
        markdown_content = []
        
        for png_path in png_paths:
            with open(png_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            response = llm.invoke([
                {"type": "text", "text": "Convert this image to markdown. Extract any mathematical formulas as LaTeX."},
                {"type": "image_url", "image_url": f"data:image/png;base64,{img_base64}"}
            ])
            
            markdown_content.append(response.content)
        
        markdown_path = os.path.join(markdown_dir, "output.md")
        with open(markdown_path, "w") as f:
            f.write("\n\n".join(markdown_content))
            
        return MarkdownResult(markdown_path=markdown_path, success=True)
    except Exception as e:
        return MarkdownResult(markdown_path="", success=False, error=str(e)) 