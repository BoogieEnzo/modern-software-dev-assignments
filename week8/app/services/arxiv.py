"""ArXiv service for searching and downloading papers."""

import arxiv
import os
import shutil
from typing import List
from datetime import datetime


class ArxivService:
    def __init__(self, papers_dir: str = "./papers"):
        self.papers_dir = papers_dir
        os.makedirs(papers_dir, exist_ok=True)

    def search(self, query: str, max_results: int = 10) -> List[dict]:
        """Search ArXiv for papers."""
        client = arxiv.Client()
        search = arxiv.Search(
            query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
        )

        results = []
        for result in client.results(search):
            results.append(
                {
                    "arxiv_id": result.entry_id.split("/")[-1],
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    "abstract": result.summary,
                    "published": result.published.isoformat() if result.published else None,
                    "pdf_url": result.pdf_url,
                }
            )
        return results

    def download(self, arxiv_id: str) -> dict:
        """Download a paper from ArXiv."""
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        result = list(client.results(search))[0]

        # Download PDF
        filename = f"{arxiv_id}.pdf"
        filepath = os.path.join(self.papers_dir, filename)
        result.download_pdf(dirpath=self.papers_dir, filename=filename)

        return {
            "arxiv_id": arxiv_id,
            "title": result.title,
            "authors": ", ".join([a.name for a in result.authors]),
            "abstract": result.summary,
            "pdf_path": filepath,
            "year": result.published.year if result.published else None,
        }
