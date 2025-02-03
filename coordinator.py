import os
import json
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
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
"""

def coordinator(state: List[BaseMessage]) -> List[BaseMessage]:
    """Coordinate the document processing workflow using LLM and allow the LLM to trigger tool calls."""
    try:
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
        llm_with_tools = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
        
        # Get input path and validate
        input_path = state[0].content.strip()
        if not input_path.endswith('.docx'):
            return state + [HumanMessage(content="Error: Input must be a path to a .docx file")]
        
        # Get output directory
        output_dir = os.path.dirname(input_path)
        
        # Execute agent with both system prompt and user instruction
        result = llm_with_tools.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Process the document at {input_path} with output directory {output_dir}")
        ])
        
        # Safely extract tool call data (whether it's a list or dict)
        tool_call_data = result.additional_kwargs.get("tool_calls")
        if tool_call_data:
            # If tool_call_data is a list, get the first element; else assume it is dict
            tool_call = tool_call_data[0] if isinstance(tool_call_data, list) else tool_call_data
            
            # Support both formats: either within a "function" key or directly contained
            if "function" in tool_call:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
            else:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

            # Adjust parameters for docx_to_pdf_converter if necessary.
            if tool_name == "docx_to_pdf_converter":
                if "__arg1" in tool_args:
                    tool_args["docx_path"] = tool_args.pop("__arg1")
                if "output_dir" not in tool_args:
                    tool_args["output_dir"] = output_dir

            # Find and execute the corresponding tool using the invoke method
            for tool in tools:
                if tool.name == tool_name:
                    tool_result = tool.invoke(tool_args)
                    return state + [HumanMessage(content=str(tool_result.model_dump()))]
            
            return state + [HumanMessage(content="Error: Tool not found")]
        
        # If no tool call is present, return the final response
        return state + [HumanMessage(content=str(result.content))]
        
    except Exception as e:
        return state + [HumanMessage(content=f"Error in coordination: {str(e)}")] 