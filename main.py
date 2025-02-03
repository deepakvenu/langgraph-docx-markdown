from typing import List
from dotenv import load_dotenv
import asyncio
import json
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph
from coordinator import coordinator
from tools import local_tool_call

def should_continue(state: List[BaseMessage]) -> str:
    """
    Determine the next node based on the last message in the state.
    Returns "local_tool" if a tool call is detected, "end" otherwise.
    """
    try:
        # Get the last message
        last_message = state[-1].content
        
        # Parse the result dictionary
        result_dict = eval(last_message)
        
        # Check for tool calls in additional_kwargs
        if (result_dict.get("additional_kwargs") and 
            "tool_calls" in result_dict["additional_kwargs"] and 
            result_dict["additional_kwargs"]["tool_calls"]):
            
            # Extract tool call information
            tool_call = result_dict["additional_kwargs"]["tool_calls"][0]
            
            # Prepare tool info for local_tool_call
            if "function" in tool_call:
                tool_info = {
                    "tool_name": tool_call["function"]["name"],
                    "tool_args": json.loads(tool_call["function"]["arguments"])
                }
                # Update the last message with the formatted tool info
                state[-1] = HumanMessage(content=json.dumps(tool_info))
                return "local_tool"
    except:
        pass
    
    # If no tool call is detected or there's an error parsing,
    # extract just the content for the final message
    try:
        result_dict = eval(last_message)
        state[-1] = HumanMessage(content=str(result_dict.get("content", last_message)))
    except:
        pass
    
    return "end"

# Build the graph
builder = MessageGraph()

# Add nodes
builder.add_node("coordinator", coordinator)
builder.add_node("local_tool", local_tool_call)

# Add conditional edge from coordinator
builder.add_conditional_edges(
    "coordinator",
    should_continue
)

# Add edge from local_tool back to coordinator
builder.add_edge("local_tool", "coordinator")

# Set entry point
builder.set_entry_point("coordinator")

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