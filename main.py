from typing import List
from dotenv import load_dotenv
import asyncio
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph
from coordinator import coordinator

# Build the graph
builder = MessageGraph()

# Add coordinator node
builder.add_node("coordinator", coordinator)

# Set entry point
builder.set_entry_point("coordinator")

# Set finish point
builder.set_finish_point("coordinator")

# Compile the graph
graph = builder.compile()

async def main():
    """Main function to run the document processing workflow"""
    try:
        input_message = "./test_files/test_updated.docx"
        result = await graph.ainvoke([HumanMessage(content=input_message)])
        
        # Extract the final message
        final_message = result[-1].content
        print(final_message)
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 