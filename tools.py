from typing import List
import os
import json
import base64
from pydantic import BaseModel, Field
from docx2pdf import convert as docx2pdf_convert
from pdf2image import convert_from_path
from langchain_openai import ChatOpenAI
from langchain.tools import tool, Tool
from langchain_core.messages import BaseMessage, HumanMessage

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
def docx_to_pdf_converter(docx_path: str) -> DocxToPdfResult:
    """
    Convert a DOCX file to PDF format. This function requires both a DOCX file path and an output directory.

    Parameters:
        docx_path (str): The path to the DOCX file to be converted. (Required)

    Returns:
        DocxToPdfResult: The result of the conversion, including the path to the PDF and a success flag.
    """
    try:
                
        # Get output directory
        output_dir = os.path.dirname(docx_path)

        pdf_dir = os.path.join(output_dir, "pdf_files")
        os.makedirs(pdf_dir, exist_ok=True)
        
        doc_name = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(pdf_dir, f"{doc_name}.pdf")
        
        docx2pdf_convert(docx_path, pdf_path)
        return DocxToPdfResult(pdf_path=pdf_path, success=True)
    except Exception as e:
        return DocxToPdfResult(pdf_path="", success=False, error=str(e))

@tool
def pdf_to_png_converter(pdf_path: str, dpi: int = 300) -> PdfToPngResult:
    """Convert a PDF file to PNG images. Takes pdf_path and optional dpi as parameters."""
    try:
        # Get output directory
        output_dir = os.path.dirname(pdf_path)
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

def local_tool_call(state: List[BaseMessage]) -> List[BaseMessage]:
    """Execute the tool call identified by the coordinator."""
    try:
        # Get the tool call information from the last message
        result_dict = eval(state[-1].content)  # Use eval instead of json.loads for the outer structure
        
        # Extract tool call information
        tool_calls = result_dict.get('additional_kwargs', {}).get('tool_calls', [])
        if not tool_calls:
            return state + [HumanMessage(content="Error: No tool calls found")]
        
        tool_call = tool_calls[0]
        tool_name = tool_call['function']['name']
        tool_args = json.loads(tool_call['function']['arguments'])  # Parse the arguments JSON
        
        # Initialize tools
        tools = [
            Tool(
                func=docx_to_pdf_converter,
                name="docx_to_pdf_converter",
                description=docx_to_pdf_converter.__doc__
            ),
            Tool(
                func=pdf_to_png_converter,
                name="pdf_to_png_converter",
                description=pdf_to_png_converter.__doc__
            ),
            Tool(
                func=png_to_markdown_converter,
                name="png_to_markdown_converter",
                description=png_to_markdown_converter.__doc__
            )
        ]
        
        # Find and execute the tool
        for tool in tools:
            if tool.name == tool_name:
                tool_result = tool.invoke(tool_args)
                return state + [HumanMessage(content=str(tool_result.model_dump()))]
        
        return state + [HumanMessage(content="Error: Tool not found")]
        
    except Exception as e:
        return state + [HumanMessage(content=f"Error in tool execution: {str(e)}")] 