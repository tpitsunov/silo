import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from .hub import HubManager

class SearchEngine:
    """
    Implements a hybrid search across installed SILO skills.
    Exact/Fuzzy match on names first, then BM25 on descriptions.
    """
    def __init__(self, hub: Optional[HubManager] = None):
        self.hub = hub or HubManager()

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant tools across all installed skills.
        """
        skills = self.hub.list_skills()
        corpus_tools = []
        
        # 1. Collect all tool metadata from installed skills
        # This requires running 'silo execute <ns> --silo-metadata' for each skill
        # (Though in a real production environment, we should cache this metadata)
        for ns in skills:
            skill_path = self.hub.get_skill_path(ns)
            entrypoint = skill_path / "skill.py"
            if not entrypoint.exists():
                continue
            
            # For brevity in this implementation, we read the metadata if it were cached.
            # In a real scenario, we'd use the Runner to call --silo-metadata.
            try:
                # Mocking metadata retrieval for now
                # In next steps, we'll integrate this with the Runner's ability to get metadata.
                metadata_path = skill_path / ".silo_meta.json"
                if metadata_path.exists():
                    with open(metadata_path, "r") as f:
                        meta = json.load(f)
                        # Expand tools into search corpus
                        for tool_name, tool_info in meta.get("tools", {}).items():
                            corpus_tools.append({
                                "namespace": ns,
                                "tool_name": tool_name,
                                "description": tool_info.get("description", ""),
                                "instructions": meta.get("instructions", ""),
                                "full_id": f"{ns}:{tool_name}"
                            })
            except Exception:
                continue

        if not corpus_tools:
            return []

        # 2. Exact/Fuzzy Match (Highest Priority)
        query_lower = query.lower()
        results = []
        
        for tool in corpus_tools:
            if query_lower in tool["full_id"].lower() or query_lower in tool["tool_name"].lower():
                results.append(tool)
        
        if len(results) >= limit:
            return results[:limit]

        # 3. BM25 Fallback (Lower Priority)
        tokenized_corpus = [doc["description"].lower().split() for doc in corpus_tools]
        if not tokenized_corpus:
            return results

        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query_lower.split()
        scores = bm25.get_scores(tokenized_query)
        
        # Sort tools by BM25 score and add to results if not already present
        # (Very simple ranking)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        seen_ids = {t["full_id"] for t in results}
        for idx in ranked_indices:
            if scores[idx] > 0: # Only include if there's some match
                tool = corpus_tools[idx]
                if tool["full_id"] not in seen_ids:
                    results.append(tool)
                    seen_ids.add(tool["full_id"])
            
            if len(results) >= limit:
                break
                
        return results
