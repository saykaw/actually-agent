from .pubmed_server import PUBMED_TOOLS
from .openalex_server import OPENALEX_TOOLS
 
# Semantic Scholar is kept in the repo for reference / fallback, but is no
# longer wired into ALL_MCP_TOOLS — its free-tier rate limit was the
# bottleneck (see semantic_scholar_server.py RATE_SLEEP = 3.0s per call).
# Uncomment below to reinstate it alongside OpenAlex if you want both.
# from .semantic_scholar_server import SEMANTIC_TOOLS
 
ALL_MCP_TOOLS = PUBMED_TOOLS + OPENALEX_TOOLS
 
__all__ = ["PUBMED_TOOLS", "OPENALEX_TOOLS", "ALL_MCP_TOOLS"]
 