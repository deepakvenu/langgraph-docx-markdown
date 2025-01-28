from typing import List
from dotenv import load_dotenv
import asyncio
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph
from chains import (
    request_parser,
    original_docx_to_pdf,
    updated_docx_to_pdf,
    original_pdf_to_png,
    updated_pdf_to_png,
    original_png_to_markdown,
    updated_png_to_markdown,
    generate_diff,
    explain_diff
)

def should_end(state: List[BaseMessage]) -> bool:
    """Check if the workflow should end"""
    last_message = state[-1].content
    return "error" in last_message.lower() or "diff_explanation" in last_message

def route_to_png_conversion(state: List[BaseMessage]) -> str:
    """Route to appropriate PNG conversion node based on success of PDF conversion"""
    last_message = state[-1].content
    result_dict = eval(last_message)
    
    if not result_dict.get("success", False):
        return END
    
    if "original" in state[-2].content:
        return "original_pdf_to_png"
    return "updated_pdf_to_png"

def route_to_markdown_conversion(state: List[BaseMessage]) -> str:
    """Route to appropriate markdown conversion node based on success of PNG conversion"""
    last_message = state[-1].content
    result_dict = eval(last_message)
    
    if not result_dict.get("success", False):
        return END
    
    if "original" in state[-2].content:
        return "original_png_to_markdown"
    return "updated_png_to_markdown"

# Build the graph
builder = MessageGraph()

# Add nodes
builder.add_node("request", request_parser)
builder.add_node("original_docx_to_pdf", original_docx_to_pdf)
builder.add_node("updated_docx_to_pdf", updated_docx_to_pdf)
builder.add_node("original_pdf_to_png", original_pdf_to_png)
builder.add_node("updated_pdf_to_png", updated_pdf_to_png)
builder.add_node("original_png_to_markdown", original_png_to_markdown)
builder.add_node("updated_png_to_markdown", updated_png_to_markdown)
builder.add_node("generate_diff", generate_diff)
builder.add_node("explain_diff", explain_diff)

# Add edges with conditional routing
builder.add_conditional_edges(
    "original_docx_to_pdf",
    route_to_png_conversion
)

builder.add_conditional_edges(
    "updated_docx_to_pdf",
    route_to_png_conversion
)

builder.add_conditional_edges(
    "original_pdf_to_png",
    route_to_markdown_conversion
)

builder.add_conditional_edges(
    "updated_pdf_to_png",
    route_to_markdown_conversion
)

# Add direct edges
builder.add_edge("request", "original_docx_to_pdf")
builder.add_edge("request", "updated_docx_to_pdf")
builder.add_edge("original_png_to_markdown", "generate_diff")
builder.add_edge("updated_png_to_markdown", "generate_diff")
builder.add_edge("generate_diff", "explain_diff")

# Set entry point
builder.set_entry_point("request")

# Add end condition
builder.set_finish_criterion(should_end)

# Compile the graph
graph = builder.compile()

async def main():
    """Main function to run the document processing workflow"""
    try:
        input_message = "Process documents at path/to/original.docx and path/to/updated.docx"
        result = await graph.ainvoke([HumanMessage(content=input_message)])
        
        # Extract the final diff explanation from the result
        final_message = result[-1].content
        if "error" in final_message.lower():
            print("Error occurred during processing:", final_message)
        else:
            print("Document Comparison Results:")
            print(final_message)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 