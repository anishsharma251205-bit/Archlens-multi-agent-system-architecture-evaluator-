from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ArchLens")


@mcp.tool()
def evaluate_architecture(architecture: str):
    """
    Evaluate a software architecture using ArchLens.
    """
    # call your existing ArchLens pipeline here
    return result


@mcp.tool()
def get_evaluation_history(limit: int = 10):
    # read existing SQLite history
    return history


@mcp.tool()
def get_best_practices(query: str):
    # call your existing RAG retriever
    return results


if __name__ == "__main__":
    mcp.run()