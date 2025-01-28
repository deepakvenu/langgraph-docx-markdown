I need you to help me come up with a project to do the following:

Given a prompt, identify the docx file to be analysed. 
There shall be two versions of the docx file: one with the original text and one with changes. Lets call them original and updated versions.
Once the dox file is identified, the program should perform the following:
1. Convert each docx file to pdf file , create a folder called pdf_files inside the folder where the   docx file is located, further inside the pdf_files folder create a subfolder with the 
  name of the docx file & save the pdf files in the this folder as <doc_file_name>_original.pdf and <doc_file_name>_updated.pdf respectively.
  For example, Input docx file identified as "C:/test/req_original.docx" (original version) and "C:/test/req_updated.docx" (updated version), Step 1 will create a folder called "C:/test/pdf_files" and inside this folder create a subfolder called "req" and save the pdf files in the this folder as "req_original.pdf" and "req_updated.pdf" respectively.
2. Convert each pdf file in the pdf_files folder to png file (Each page of the png file should be saved separately) -> the quality of the png file should be configurable (default 300 dpi)
   For this step create a separate folder called png_files inside the folder where the docx file is located and further a folder called <doc_file_name> inside the png_files folder, futher inside this create two folders called "original" and "updated" and save the png files in the respective folders with the suffix <doc_file_name>_original_page_<page_number>.png and <doc_file_name>_updated_page_<page_number>.png. For the example considered in step 1, Step 2 will create a folder called "C:/test/png_files" and inside this folder create a subfolder called "req" and further inside this folder create two sub folders one "original" and the other "updated" and save the png files in the original folder as "req_original_page_<page_number>.png" and updated files in the updated folder as "req_updated_page_<page_number>.png" respectively. One file for each page in the corresponding pdf file.
3. For the contents in the original and updated png files, extract the text in the form of markdown and save it in a file called <doc_file_name>_original.md and <doc_file_name>_updated.md respectively. In the original docx file folder, create a folder called markdown_files and save the markdown files in this folder. For this step, you can use an LLM to extract the text in the form of markdown. Please make a prompt such that the LLM extracts the text in the form of markdown from the png files and makes sure that the LaTex version of the Mathematical formuale or equations are extracted correctly so that the markdown file can be rendered in a markdown viewer clearly. Make sure the LLM does not create any new content other than what is present in the png files. Combine all the contents of the png files into a single markdown, one markdown for original and one for updated. Make sure you have a good python structure for this step. You can use pydantic to define the structure of the output from the LLM. You can also use the 64 bit representation of the png file to make the LLM call, use any python library to do this as you may see fit. While performing the LLM calls, make sure you handle the calls one png file at a time. You can follow these steps: Iterate over the png files in the png folder, for each file convert it to 64 bit representation and make the llm call with a good prompt and get the markdown output, write the output to the markdown file.
4. Once the markdown files are created, identify the differences between the original and updated markdown files, increase the context of the differences to include the entire sentences or paragraphs that contain the differences. Once the differences are identified, create a new markdown file called <doc_file_name>_diff.md and save it in the same folder as the original docx file.
5. Now use the <doc_file_name>_diff.md file and make an llm call for each of the difference in the document and ask llm to explain the difference in detail.
6. Once the llm call is made, save the output in a file called <doc_file_name>_diff_explanation.md and save it in the same folder as the original docx file.

For implementing steps 1 and 2 you may consider using the following python code:
'''
Sample code for testing:

import os
from typing import List

from docx2pdf import convert as docx2pdf_convert
from pdf2image import convert_from_path


def doc2pdf_convert(docx_path: str) -> str:
    """
    Converts a .docx file to .pdf using docx2pdf.
    The output PDF is created in the same folder with the same base name as the .docx.

    :param docx_path: Path to the input .docx file.
    :return: Path to the newly created .pdf file.
    """
    if not docx_path.lower().endswith(".docx"):
        raise ValueError("The input file must have a .docx extension.")

    base, _ = os.path.splitext(docx_path)
    pdf_path = base + ".pdf"

    # Perform the DOCX->PDF conversion
    docx2pdf_convert(docx_path, pdf_path)

    return pdf_path


def pdf2png_convert(pdf_path: str, output_dir: str = None, dpi: int = 300) -> List[str]:
    """
    Converts a PDF file to multiple PNG images (one per page).
    The output PNGs are saved in the specified output directory (defaults to the same
    directory as the PDF), each named as page_X.png.

    :param pdf_path: Path to the input .pdf file.
    :param output_dir: Directory to store the PNG images.
                      If None, uses the same directory as the PDF.
    :param dpi: Resolution (dots per inch) for the output images.
    :return: List of paths to the PNG images created.
    """
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError("The input file must have a .pdf extension.")

    # Default output directory is the same as the PDF file
    if output_dir is None:
        output_dir = os.path.dirname(pdf_path)
        if not output_dir:
            output_dir = os.getcwd()  # in case pdf_path was just a filename in the current dir

    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=dpi)

    output_paths = []
    for i, page in enumerate(pages):
        png_name = f"page_{i + 1}.png"
        png_path = os.path.join(output_dir, png_name)
        page.save(png_path, "PNG")
        output_paths.append(png_path)

    return output_paths


'''

I want the steps 1, 2, and 3 to be implemented in parallel for the original version of the docx file and the updated version of the docx file.


Code organization:
I also want you to use Langgraph to implement these steps.
The code can be split into main.py and chains.py. In main.py you can define the nodes, edges and connections of the graph. In chains.py you can define the nodes and the logic for each node. 

In main.py you can define the nodes: request, original_docx_to_pdf, updated_docx_to_pdf, original_pdf_to_png, updated_pdf_to_png, png_to_markdown_original, png_to_markdown_updated, diff_markdown, diff_explanation.
In chains.py you can define the nodes and the logic for each node. request_parser, original_docx_to_pdf_converter, updated_docx_to_pdf_converter, original_pdf_to_png_converter, updated_pdf_to_png_converter, png_to_markdown_original_converter, png_to_markdown_updated_converter, diff_markdown_converter, diff_explanation_converter.

The flow of the graph should be as follows:
start->request
request -> original_docx_to_pdf
request -> updated_docx_to_pdf
original_docx_to_pdf -> original_pdf_to_png
updated_docx_to_pdf -> updated_pdf_to_png
original_pdf_to_png -> png_to_markdown_original
updated_pdf_to_png -> png_to_markdown_updated
png_to_markdown_original -> diff_markdown
png_to_markdown_updated -> diff_markdown
diff_markdown -> diff_explanation
diff_explanation -> end

A sample code for main.py to add nodes and edges is given below. You may use this as a reference to add the nodes and edges.
'''
from typing import List
from dotenv import load_dotenv
import asyncio
load_dotenv()

from langchain_core.messages import BaseMessage
from langgraph.graph import END, MessageGraph
from chains import first_responder, revisor, request_parser, note_processor

MAX_ITERATIONS = 2

# Build the graph
builder = MessageGraph()

# Add nodes
builder.add_node("request", request_parser)
builder.add_node("notes", note_processor)
builder.add_node("draft", first_responder)
builder.add_node("revise", revisor)

# Add edges
builder.add_edge("request", "notes")
builder.add_edge("notes", "draft")
builder.add_edge("draft", "revise")

def should_continue(state: List[BaseMessage]) -> str:
    num_iterations = len(state) - 2
    if num_iterations >= MAX_ITERATIONS:
        return END
    return "revise"

# Add conditional edge from revise
builder.add_conditional_edges("revise", should_continue)
builder.set_entry_point("request")

# Compile the graph
graph = builder.compile()
'''

Sample code for chains.py is given below. You may use this as a reference to add the nodes and the logic for each node.

'''
from typing import Optional, List, Dict
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

@dataclass
class CRNotes:
    cr_id: str
    notes: List[str]
    status: str = "pending"  # pending, completed, failed

class CRNotesCollection:
    def __init__(self):
        self.cr_notes: List[CRNotes] = []

    def add_cr(self, cr_id: str, notes: List[str], status: str = "completed"):
        self.cr_notes.append(CRNotes(cr_id=cr_id, notes=notes, status=status))

    def to_dict(self) -> Dict:
        return {
            "cr_data": [
                {"cr_id": cr.cr_id, "notes": cr.notes, "status": cr.status}
                for cr in self.cr_notes
            ]
        }

class CRSummary(BaseModel):
    cr_id: str = Field(description="The MOLY ID of the CR being summarized")
    summary: str = Field(description="Detailed analysis of the CR notes")

class CRAnalysisResponse(BaseModel):
    summaries: List[CRSummary] = Field(description="List of CR summaries")    

async def fetch_notes_async(cr_id: str) -> Optional[CRNotes]:
    """Async version of fetch_notes"""
    try:
        with open('input_json/Updated_CR_data.json', 'r') as f:
            cr_data = json.load(f)
            
        for cr in cr_data:
            if cr['CR_ID'] == cr_id:
                return CRNotes(cr_id=cr_id, notes=cr['notes'], status="completed")
        return CRNotes(cr_id=cr_id, notes=[], status="failed")
    except Exception as e:
        print(f"Error reading CR data for {cr_id}: {e}")
        return CRNotes(cr_id=cr_id, notes=[], status="failed")

def request_parser(state: List[BaseMessage]) -> List[BaseMessage]:
    """Parse the initial request and identify CR IDs"""
    # Get the input text
    input_text = state[0].content
    
    # Find all MOLY IDs
    moly_ids = re.findall(r'MOLY\d+', input_text)
    
    # Create a structured message with the findings
    result_message = f"""
Original Request: {input_text}
Found CR IDs: {', '.join(moly_ids) if moly_ids else 'No CR IDs found'}
"""
    
    return state + [HumanMessage(content=result_message)]

async def note_processor(state: List[BaseMessage]) -> List[BaseMessage]:
    """Process multiple CR IDs in parallel and fetch their notes"""
    # Get the last message which should contain the CR IDs
    last_message = state[-1].content
    
    # Extract MOLY IDs using regex, but only from the "Found CR IDs:" line
    cr_line = re.search(r'Found CR IDs: (.*)', last_message)
    if cr_line:
        moly_ids = re.findall(r'MOLY\d+', cr_line.group(1))
    else:
        moly_ids = []
    
    # Create tasks for parallel execution
    tasks = [fetch_notes_async(moly_id) for moly_id in moly_ids]
    
    # Wait for all tasks to complete
    cr_results = await asyncio.gather(*tasks)
    
    # Collect results
    collection = CRNotesCollection()
    for result in cr_results:
        if result:
            collection.add_cr(result.cr_id, result.notes, result.status)
    
    # Convert to structured message
    return state + [HumanMessage(content=str(collection.to_dict()))]

def first_responder(state: List[BaseMessage]) -> List[BaseMessage]:
    """Generate initial response based on CR notes using structured output"""
    system_prompt = """You are an expert wireless systems researcher. 
    Analyze the CR data and provide summaries in a structured format.
    Your response MUST be valid JSON that matches the following Pydantic structure:

    {
        "summaries": [
            {
                "cr_id": "MOLY ID",
                "summary": "Detailed analysis"
            },
            ...
        ]
    }
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please analyze the following CR data and provide structured summaries: {state[-1].content}")
    ]
    
    # Use JSON mode to ensure structured output
    response = ChatOpenAI(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"}
    ).invoke(messages)
    
    try:
        # Parse the response into our Pydantic model
        analysis = CRAnalysisResponse.model_validate_json(response.content)
        
        # Format the response in the desired text format
        formatted_response = "\n\n".join([
            f"CR_ID: {summary.cr_id}\nSummary: {summary.summary}"
            for summary in analysis.summaries
        ])
        
        return state + [HumanMessage(content=formatted_response)]
    except Exception as e:
        print(f"Error parsing response: {e}")
        return state + [HumanMessage(content="Error: Failed to generate structured response")]

def revisor(state: List[BaseMessage]) -> List[BaseMessage]:
    """Revise and improve the previous response"""
    messages = [
        SystemMessage(content="You are an expert wireless systems researcher. Review and improve the previous analysis."),
        HumanMessage(content=f"Previous analysis: {state[-1].content}\nPlease provide an improved version.")
    ]
    
    response = ChatOpenAI(model="gpt-3.5-turbo-1106").invoke(messages)
    return state + [response]

# Create the tool
fetch_notes_tool = StructuredTool.from_function(
    func=fetch_notes_async,
    name="fetch_notes",
    description="Fetch notes for a given CR ID"
)

'''

