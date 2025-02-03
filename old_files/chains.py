from typing import Dict, List
from dataclasses import dataclass
import os
from pathlib import Path
import base64
from concurrent.futures import ThreadPoolExecutor
import difflib

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from docx2pdf import convert as docx2pdf_convert
from pdf2image import convert_from_path

@dataclass
class DocumentPaths:
    original_docx: str
    updated_docx: str
    base_dir: str = ""
    doc_name: str = ""

class DocxToPdfResult(BaseModel):
    pdf_path: str
    success: bool
    error: str = ""

class PdfToPngResult(BaseModel):
    png_paths: List[str]
    success: bool
    error: str = ""

class MarkdownResult(BaseModel):
    markdown_path: str
    success: bool
    error: str = ""

class DiffResult(BaseModel):
    diff_content: str
    success: bool
    error: str = ""

def request_parser(state: List[BaseMessage]) -> List[BaseMessage]:
    """Parse the initial request to identify document paths and verify file existence"""
    try:
        input_text = state[0].content.strip()
        
        # Extract the base path
        if not input_text.endswith('.docx'):
            return state + [HumanMessage(content="Error: Input must be a path to a .docx file")]
        
        # Form the paths for original and updated files
        base_path = input_text[:-5]  # Remove .docx extension
        original_path = f"{base_path}_original.docx"
        updated_path = f"{base_path}_updated.docx"
        
        # Check if both files exist
        if not os.path.exists(original_path):
            return state + [HumanMessage(content=f"Error: Original file not found at {original_path}")]
        if not os.path.exists(updated_path):
            return state + [HumanMessage(content=f"Error: Updated file not found at {updated_path}")]
        
        # Get base directory and document name
        base_dir = os.path.dirname(original_path)
        doc_name = os.path.splitext(os.path.basename(original_path))[0]
        
        paths = DocumentPaths(
            original_docx=original_path,
            updated_docx=updated_path,
            base_dir=base_dir,
            doc_name=doc_name
        )
        
        return state + [HumanMessage(content=str(paths.__dict__))]
    except Exception as e:
        return state + [HumanMessage(content=f"Error parsing request: {str(e)}")]

def docx_to_pdf_converter(docx_path: str, output_dir: str) -> DocxToPdfResult:
    """Convert DOCX to PDF"""
    try:
        pdf_dir = os.path.join(output_dir, "pdf_files")
        os.makedirs(pdf_dir, exist_ok=True)
        
        doc_name = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(pdf_dir, f"{doc_name}.pdf")
        
        docx2pdf_convert(docx_path, pdf_path)
        return DocxToPdfResult(pdf_path=pdf_path, success=True)
    except Exception as e:
        return DocxToPdfResult(pdf_path="", success=False, error=str(e))

def pdf_to_png_converter(pdf_path: str, output_dir: str, dpi: int = 300) -> PdfToPngResult:
    """Convert PDF to PNG files"""
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

def png_to_markdown_converter(png_paths: List[str], output_dir: str) -> MarkdownResult:
    """Convert PNG files to Markdown"""
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

# Node functions for the graph
def original_docx_to_pdf(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert original DOCX to PDF"""
    paths = eval(state[-1].content)  # Parse the DocumentPaths dict
    result = docx_to_pdf_converter(paths["original_docx"], paths["base_dir"])
    return state + [HumanMessage(content=f"original:{str(result.dict())}")] 

def updated_docx_to_pdf(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert updated DOCX to PDF"""
    paths = eval(state[-1].content)
    result = docx_to_pdf_converter(paths["updated_docx"], paths["base_dir"])
    return state + [HumanMessage(content=f"updated:{str(result.dict())}")] 

def original_pdf_to_png(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert original PDF to PNG"""
    last_result = eval(state[-1].content.split(":", 1)[1])
    paths = eval(state[-2].content)
    result = pdf_to_png_converter(last_result["pdf_path"], paths["base_dir"])
    return state + [HumanMessage(content=f"original:{str(result.dict())}")] 

def updated_pdf_to_png(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert updated PDF to PNG"""
    last_result = eval(state[-1].content.split(":", 1)[1])
    paths = eval(state[-2].content)
    result = pdf_to_png_converter(last_result["pdf_path"], paths["base_dir"])
    return state + [HumanMessage(content=f"updated:{str(result.dict())}")] 

def original_png_to_markdown(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert original PNGs to Markdown"""
    last_result = eval(state[-1].content.split(":", 1)[1])
    paths = eval(state[-3].content)
    result = png_to_markdown_converter(last_result["png_paths"], paths["base_dir"])
    return state + [HumanMessage(content=f"original:{str(result.dict())}")] 

def updated_png_to_markdown(state: List[BaseMessage]) -> List[BaseMessage]:
    """Convert updated PNGs to Markdown"""
    last_result = eval(state[-1].content.split(":", 1)[1])
    paths = eval(state[-3].content)
    result = png_to_markdown_converter(last_result["png_paths"], paths["base_dir"])
    return state + [HumanMessage(content=f"updated:{str(result.dict())}")] 

def generate_diff(state: List[BaseMessage]) -> List[BaseMessage]:
    """Generate diff between original and updated markdown"""
    try:
        # Find the markdown results in the state
        original_result = None
        updated_result = None
        for message in reversed(state):
            if message.content.startswith("original:") and "markdown_path" in message.content:
                original_result = eval(message.content.split(":", 1)[1])
            elif message.content.startswith("updated:") and "markdown_path" in message.content:
                updated_result = eval(message.content.split(":", 1)[1])
            
            if original_result and updated_result:
                break
        
        with open(original_result["markdown_path"], 'r') as f:
            original_text = f.readlines()
        with open(updated_result["markdown_path"], 'r') as f:
            updated_text = f.readlines()
        
        diff = list(difflib.unified_diff(original_text, updated_text))
        diff_content = ''.join(diff)
        
        result = DiffResult(diff_content=diff_content, success=True)
        return state + [HumanMessage(content=str(result.dict()))]
    except Exception as e:
        result = DiffResult(diff_content="", success=False, error=str(e))
        return state + [HumanMessage(content=str(result.dict()))]

def explain_diff(state: List[BaseMessage]) -> List[BaseMessage]:
    """Explain the differences using LLM"""
    try:
        diff_result = eval(state[-1].content)
        if not diff_result["success"]:
            return state + [HumanMessage(content="Error: Failed to generate diff explanation")]
        
        llm = ChatOpenAI(model="gpt-4")
        explanation = llm.invoke([
            HumanMessage(content=f"""
            Analyze the following unified diff and provide a clear, concise explanation of the changes:
            {diff_result['diff_content']}
            
            Focus on:
            1. What content was added or removed
            2. Any significant formatting changes
            3. The overall impact of these changes
            """)
        ])
        
        return state + [HumanMessage(content=f"diff_explanation:{explanation.content}")]
    except Exception as e:
        return state + [HumanMessage(content=f"Error explaining diff: {str(e)}")] 