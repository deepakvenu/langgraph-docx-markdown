import os
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from tools import (
    docx_to_pdf_converter,
    pdf_to_png_converter,
    png_to_markdown_converter
)

SYSTEM_PROMPT = """
You are an expert at document processing and can convert documents from .docx format to .Markdown format using the tools at your disposal.

You are expected to convert the document supplied to you to .Markdown format using the tools at your disposal. For Markdown documents, please use LaTex formatting for math equations. The markdown document is expected to be previewed in a markdown viewer.

Follow these steps:
1. Convert the DOCX file to PDF using docx_to_pdf_converter
2. Convert the PDF to PNG files using pdf_to_png_converter
3. Convert the PNG files to Markdown using png_to_markdown_converter

Check the success status of each conversion before proceeding to the next step.

Current Progress:
{scratch_pad}
"""

def coordinator(state: List[BaseMessage], scratch_pad: Dict[str, Any] = None) -> List[BaseMessage]:
    """
    Coordinate the document processing workflow using LLM.
    Uses scratch_pad to track progress and previous results.
    Returns the state with the LLM's complete response appended.
    """
    try:
        # Initialize scratch_pad if None
        if scratch_pad is None:
            scratch_pad = {
                "completed_steps": [],
                "current_step": "start",
                "last_result": None
            }
        
        # Initialize tools with descriptions from their docstrings
        tools = [
            Tool(
                func=docx_to_pdf_converter,
                name="docx_to_pdf_converter",
                description=(docx_to_pdf_converter.__doc__ or "Convert DOCX file to PDF format").strip()
            ),
            Tool(
                func=pdf_to_png_converter,
                name="pdf_to_png_converter",
                description=(pdf_to_png_converter.__doc__ or "Convert PDF file to PNG images").strip()
            ),
            Tool(
                func=png_to_markdown_converter,
                name="png_to_markdown_converter",
                description=(png_to_markdown_converter.__doc__ or "Convert PNG files to Markdown format").strip()
            )
        ]

        # Initialize LLM with bound tools
        llm_with_tools = ChatOpenAI(model="gpt-4").bind_tools(tools)
        
        # Get input path and validate if this is the first message
        if len(state) == 1:
            input_path = state[0].content.strip()
            if not input_path.endswith('.docx'):
                return state + [HumanMessage(content="Error: Input must be a path to a .docx file")]
            output_dir = os.path.dirname(input_path)
        else:
            # For subsequent messages, get the paths from the first message
            input_path = state[0].content.strip()
            output_dir = os.path.dirname(input_path)
        
        # Update scratch_pad based on the last message if it contains a tool result
        if len(state) > 1:
            try:
                last_result = eval(state[-1].content)
                if isinstance(last_result, dict) and "success" in last_result:
                    scratch_pad["last_result"] = last_result
                    if last_result["success"]:
                        # Determine which step was completed based on the result type
                        if "pdf_path" in last_result:
                            scratch_pad["completed_steps"].append("docx_to_pdf")
                            scratch_pad["current_step"] = "pdf_to_png"
                        elif "png_paths" in last_result:
                            scratch_pad["completed_steps"].append("pdf_to_png")
                            scratch_pad["current_step"] = "png_to_markdown"
                        elif "markdown_path" in last_result:
                            scratch_pad["completed_steps"].append("png_to_markdown")
                            scratch_pad["current_step"] = "complete"
            except:
                pass  # If we can't parse the last message as a result, continue without updating scratch_pad
        
        # Format scratch pad for prompt
        scratch_pad_text = "\n".join([
            f"- Completed Steps: {', '.join(scratch_pad['completed_steps']) if scratch_pad['completed_steps'] else 'None'}",
            f"- Current Step: {scratch_pad['current_step']}",
            f"- Last Result: {scratch_pad['last_result']}"
        ])
        
        # Execute LLM with system prompt (including scratch pad) and conversation history
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(scratch_pad=scratch_pad_text)),
            HumanMessage(content=f"Process the document at {input_path} with output directory {output_dir}")
        ]
        
        # Add any additional context from previous messages
        if len(state) > 1:
            messages.extend(state[1:])
        
        result = llm_with_tools.invoke(messages)
        
        # Return the complete result including any tool calls
        # Package the entire result (including tool_calls if present) as a JSON string
        result_dict = {
            "content": result.content,
            "additional_kwargs": result.additional_kwargs
        }
        
        return state + [HumanMessage(content=str(result_dict))]
        
    except Exception as e:
        return state + [HumanMessage(content=f"Error in coordination: {str(e)}")] 