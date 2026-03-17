import json
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from ..core.hub import HubManager

class SearchEngine:
    """
    Implements a hybrid search across installed SILO skills.
    Exact/Fuzzy match on names first, then BM25 on descriptions.
    """
    def __init__(self, hub: Optional[HubManager] = None):
        self.hub = hub or HubManager()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant tools across all installed skills."""
        corpus = self._collect_metadata()
        if not corpus:
            return []

        query_lower = query.lower()
        # 2. Exact/Fuzzy Match (Highest Priority)
        results = [t for t in corpus if query_lower in t["full_id"].lower() or query_lower in t["tool_name"].lower()]

        if len(results) >= limit:
            return results[:limit]

        # 3. BM25 Fallback (Lower Priority)
        return self._rank_by_bm25(query_lower, corpus, results, limit)

    def _collect_metadata(self) -> List[Dict[str, Any]]:
        corpus = []
        for ns in self.hub.list_skills():
            skill_path = self.hub.get_skill_path(ns)
            meta_path = skill_path / ".silo_meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        for tool_name, info in meta.get("tools", {}).items():
                            corpus.append({
                                "namespace": ns,
                                "tool_name": tool_name,
                                "description": info.get("description", ""),
                                "instructions": meta.get("instructions", ""),
                                "full_id": f"{ns}:{tool_name}"
                            })
                except (json.JSONDecodeError, IOError):
                    continue
        return corpus

    def _rank_by_bm25(self, query: str, corpus: List[Dict], results: List[Dict], limit: int) -> List[Dict]:
        tokenized_corpus = [doc["description"].lower().split() for doc in corpus]
        if not tokenized_corpus:
            return results

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(query.split())
        seen_ids = {t["full_id"] for t in results}

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        for idx in ranked_indices:
            if len(results) >= limit:
                break
            tool = corpus[idx]
            if scores[idx] > 0 and tool["full_id"] not in seen_ids:
                results.append(tool)
        return results
