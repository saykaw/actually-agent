from .pubmed_server import PUBMED_TOOLS
from .semantic_scholar_server import SEMANTIC_TOOLS

ALL_MCP_TOOLS = PUBMED_TOOLS + SEMANTIC_TOOLS

__all__ = ["PUBMED_TOOLS", "SEMANTIC_TOOLS", "ALL_MCP_TOOLS"]