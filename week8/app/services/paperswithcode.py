"""Papers with Code service for GitHub repository links."""

from paperswithcode import PapersWithCodeClient
from typing import Optional, List


class PapersWithCodeService:
    def __init__(self):
        self.client = PapersWithCodeClient()

    def get_repo(self, paper_title: str) -> Optional[str]:
        """Get GitHub repository for a paper."""
        try:
            # Search for the paper
            results = self.client.search_papers(paper_title)
            if results and results.items:
                paper = results.items[0]
                # Get methods/repositories for this paper
                methods = self.client.get_paper_methods(paper.id)
                if methods and methods.items:
                    for method in methods.items[:3]:
                        if method.repository:
                            return method.repository.url
            return None
        except Exception as e:
            print(f"Error getting repo for {paper_title}: {e}")
            return None

    def search_code(self, query: str) -> List[dict]:
        """Search for code repositories."""
        try:
            results = self.client.search_papers(query)
            code_results = []
            for paper in results.items[:5]:
                code_results.append(
                    {
                        "title": paper.title,
                        "url": paper.url,
                    }
                )
                # Try to get repo
                methods = self.client.get_paper_methods(paper.id)
                if methods and methods.items:
                    for method in methods.items[:2]:
                        if method.repository:
                            code_results[-1]["repo_url"] = method.repository.url
                            break
            return code_results
        except Exception as e:
            print(f"Error searching code: {e}")
            return []
