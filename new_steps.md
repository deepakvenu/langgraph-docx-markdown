Node : Coordinator: Coordinates with the other nodes to perform the task. Description of what the coordinator does:
- Runs a prompt to identify the next actions to take. The prompt can be of this format:
'''
You are an expert at document processing and can convert documents from .docx format to .Markdown format using the tools at your disposal.

 You are expected to convert the document to supplied to you to .Markdown format using the tools at your disposal. For Markdown documents, please use LaTex formatting for math equations. The markdown document is expected to be previewed in a markdown viewer.
'''
In addition to the above prompt, give it the tools as follows:
'''
{tools}
'''
The tools are as follows:
1. GeneratePdfFromDocx: This takes in one parameter, the path to the .docx and and it creates a folder pdf inside the same directory as the .docx file. It then creates a pdf file inside the pdf folder. You can  use the following code to generate the pdf:

'''
class DocxToPdfResult(BaseModel):
    pdf_path: str
    success: bool
    error: str = ""
#First identify the docx file and the get the directory of the docx file. Then call the follwing #function:
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
'''

Once the above function is run, the result is returned to the coordinator. The coordinator then uses the result to determine the next action to take.

2. GeneratePngFromPdf: This takes in one parameter, the path to the .pdf and and it creates a folder png inside the same directory as the .pdf file. This also takes another optional parameter to determine how many dpi the png file should be, by default it is 300 dpi. It then creates a png files inside the png folder. The files are suffixed with the page number of the page in the pdf file. For example if the pdf file has 5 pages, the png files will be named as <doc_file_name>_page_1.png, <doc_file_name>_page_2.png, <doc_file_name>_page_3.png, <doc_file_name>_page_4.png, <doc_file_name>_page_5.png. You can  use the following code to generate the png:
'''
class PdfToPngResult(BaseModel):
    png_paths: List[str]
    success: bool
    error: str = ""
#First identify the pdf file and the get the directory of the pdf file. Then call the follwing function:
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
'''
Once the above function is run, the result is returned to the coordinator. The coordinator then uses the result to determine the next action to take.

3. GenerateMdFromPng: This takes in one parameter, the path to the png files directory and and it creates a folder markdown inside the same directory as the png directory. It then creates a single markdown files inside the markdown folder. The markdown file is formed with the combination of all the png files in the png folder. The png to markdown conversion is done using an LLM. The conversion is done page by page by starting at the first page (indicated by the page number in the png file name) and ending at the last page. The ouput should be a single markdown file. You can  use the following code to generate the markdown:
'''
class PngToMdResult(BaseModel):
    md_paths: List[str]
    success: bool
    error: str = ""
#First identify the png file and the get the directory of the png file. Then call the follwing function:
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
'''
Once the above function is run, the result is returned to the coordinator. The coordinator then uses the result to determine the next action to take.

Organize this code into different files based on what you see fit.

