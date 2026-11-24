# FootballPricer Polymarket & MCP Probability Oracle Quickstart

[![FootballPricer Probability Oracle MCP connector – tool definition quality and endpoint health on Glama](https://glama.ai/mcp/connectors/com.footballpricer/football-pricer-probability-oracle/badges/score.svg)](https://glama.ai/mcp/connectors/com.footballpricer/football-pricer-probability-oracle)

Zero-dependency Python 3 client and Remote MCP configuration kit for the **FootballPricer Calibrated Probability Oracle** (<https://www.footballpricer.com>).

Evaluate live Polymarket / prediction-market probability shares or sportsbook decimal odds in **<10ms** against calibrated Dixon-Coles match probabilities, Fair Odds, EV%, and Fractional Kelly sizing, or connect Claude, Cursor, and autonomous agent frameworks directly via Streamable HTTP MCP.

---

## What You Get

- **Zero-dependency Python CLI (`scanner.py`)**: standard library only (`urllib`, `json`, `argparse`) — no `pip install` needed.
- **Public Track Record Audit (`0` credits, no API key)**: inspect live settled Brier Score vs sharp closing market, CLV%, and ROI% before running a single bot cycle.
- **Sub-10ms Polymarket / Exchange Re-Pricer (`1` credit = `$0.01`)**: compare live probability shares (`0.01..0.99`) with slippage and commission adjustments.
- **Confirmed XI Pass-2 SSE Feed**: stream real-time pre-match vs confirmed-lineup probability swings on `GET /api/v1/oracle/stream`.
- **30 Free Sandbox Credits (`$0.30` value — 30 live reprices or 6 cached forecasts, no card required)**: mint scoped `fp_live_...` API keys at <https://www.footballpricer.com/#/app?tab=api-keys>.
- **Production Bot Plans**: **Agent Starter** (`$49/mo · 5,000 cr`, auto-refill) and **Agent Pro Bot** (`$199/mo · 25,000 cr`), plus one-time prepaid packs (`$25 / $100 / $500`).

---

## Quickstart (Python CLI)

### 1. Public smoke checks (`0` credits, no auth needed)

```bash
python3 scanner.py --mode track-record
python3 scanner.py --mode mcp-tools
```

### 2. Discover pre-warmed upcoming fixtures (`0` credits in `discovery` mode)

```bash
export FOOTBALLPRICER_API_KEY="fp_live_..."
python3 scanner.py --mode edges --detail discovery --limit 10
```

### 3. Reprice a live Polymarket share (`1` credit = `$0.01`, `<10ms`)

```bash
python3 scanner.py \
  --mode reprice \
  --slate-id <SLATE_ID> \
  --market-key 1x2_home \
  --quote-format probability_share \
  --price 0.51 \
  --slippage-bps 40 \
  --commission-pct 0
```

Add `--json` to any command to output raw JSON for downstream trading or research pipelines.

---

## Connect Any MCP Client (Remote Streamable HTTP)

**Official MCP Registry:** `com.footballpricer.www/oracle`

```json
{
  "mcpServers": {
    "footballpricer-oracle": {
      "type": "streamable-http",
      "url": "https://www.footballpricer.com/api/mcp",
      "headers": {
        "Authorization": "Bearer fp_live_YOUR_API_KEY"
      }
    }
  }
}
```

### Machine Discovery Endpoints

- Agent Instructions: <https://www.footballpricer.com/llms.txt>
- MCP Server Card: <https://www.footballpricer.com/.well-known/mcp/server-card.json>
- Agent Card: <https://www.footballpricer.com/.well-known/agent-card.json>
- Public Track Record API: <https://www.footballpricer.com/api/v1/oracle/track-record>
- Pass-2 Confirmed XI SSE Stream: `GET https://www.footballpricer.com/api/v1/oracle/stream` (`Authorization: Bearer fp_live_...` with `oracle:read` scope)

---

## Credit Pricing (`1 credit = $0.01 USD`)

| Tool / Endpoint | Credits | Notes |
| --- | --- | --- |
| `get_track_record` | `0` | Public settled Brier, CLV%, and ROI% verification |
| `list_upcoming_edges` (`detail=discovery`) | `0` | Upcoming fixture schedule, Pass 1/2 status, stability tier |
| `list_upcoming_edges` (`detail=full`) | `1` | Pre-computed EV%, Fair Odds, and offered odds |
| `reprice_live_odds` (`quote_only` / `reanchor_market`) | `1` | Deterministic `<10ms` live Polymarket / sportsbook repricing |
| `get_match_pricing` (cache hit) | `5` | Full 1X2, Asian Handicap, O/U, BTTS, Kelly ladder |
| `get_match_pricing` (`allowFreshRun=true`) | `50` | On-demand async deep forecast (auto-refunded on failure) |

---

## License & Disclaimer

MIT License — see [LICENSE](./LICENSE).

Informational quantitative analytics only. Not financial advice, and not a gambling operator or automated order-execution bot. Never commit API keys to source control.
