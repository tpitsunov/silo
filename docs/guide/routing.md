# Deep Dive: Dynamic Routing (BM25)

In SILO V2, an Agent doesn't have to know specific tool names upfront. Instead, it uses **Semantic Discovery** to find the right tool for the job.

## 1. How Search Works

When you call `silo_search(query="get market data")`, SILO performs a hybrid search across all installed skills in the hub:

1.  **Exact Match**: Tools or namespaces that exactly match the query (or are substrings) are ranked highest.
2.  **BM25 Fallback**: If no exact matches are found, SILO uses the **BM25Okapi** algorithm (Best Matching 25) to rank tool descriptions and instructions semantically.
3.  **Cross-Namespace**: Search is not limited to a single skill; it scans the entire hub.

## 2. Optimizing for Agents

To make your tools easily discoverable, follow these best practices in your `skill.py`:

- **Descriptive Names**: Use `get_stock_price` instead of `fetch_data`.
- **Rich Docstrings**: The text in your function's docstring is indexed by the search engine.
    - *Good*: `"""Fetches the current trading price for a stock ticker symbols like AAPL."""`
    - *Bad*: `"""Gets price."""`
- **Skill Instructions**: Use `@skill.instructions()` to describe the overall capability of the skill (e.g., "This skill is the source of truth for all financial data").

## 3. The `silo_search` Tool

The MCP server exposes `silo_search`. Here is how an Agent typically interacts with it:

> **Agent**: "I need to check the company's annual revenue. Let me search for an appropriate tool."
>
> *(Agent calls `silo_search(query="annual revenue")`)*
>
> **SILO**: Returns `fin-ops:get_financials` with its description and schema.

---

**Next:** See how SILO handles [Interactive Approvals](interactive.md).
