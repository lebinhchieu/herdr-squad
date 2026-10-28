`usage.csv` (40 rows) has one row per session (session, role, input_tokens, cache_read_tokens, output_tokens); `prices.txt` has the price per 1M tokens. Compute each row's cost = sum of tokens x price per token, sum per role, and the grand total. Read both files; do the arithmetic yourself (no code execution is available).
Reply with ONLY one JSON object, no prose, no code fence:
{"top_role": "<role with the highest total cost>", "top_role_cost_usd": <number, 2 decimals>, "total_cost_usd": <number, 2 decimals>}
