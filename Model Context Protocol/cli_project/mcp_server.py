from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc_content",
    description="Reads the content of a document given its name.")
def read_documemt(doc_id:str = Field(description="The name of the document to read")):
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found.")
    return docs[doc_id]

@mcp.tool(
    name="edit_doc_content",
    description="Edits the content of a document given new content.")
def edit_document(
    doc_id:str = Field(description="The name of the document to edit"), 
    old_string:str = Field(description="The content to be replaced in the document"),
    new_content:str = Field(description="The new content for the document")
    ):
    if doc_id not in docs:
        raise ValueError(f"Document '{doc_id}' not found.")
    docs[doc_id] = docs[doc_id].replace(old_string, new_content)
    return f"Document '{doc_id}' updated successfully."

# TODO: Write a resource to return all doc id's
# TODO: Write a resource to return the contents of a particular doc
# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
