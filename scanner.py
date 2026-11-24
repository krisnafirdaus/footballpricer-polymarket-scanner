#!/usr/bin/env python3
"""Zero-dependency FootballPricer Oracle & Polymarket EV Scanner.

Uses Python standard library only (`urllib`, `json`, `argparse`).
Set `FOOTBALLPRICER_API_KEY=fp_live_...` for authenticated modes (`edges`, `reprice`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    api_key: str | None = None,
    timeout: float = 20.0,
) -> tuple[dict[str, Any], dict[str, str]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "footballpricer-polymarket-scanner/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data: bytes | None = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return json.loads(raw), hdrs
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(body_text)
        except json.JSONDecodeError:
            err_json = {"error": body_text}
        raise RuntimeError(f"HTTP {exc.code} from {url}: {json.dumps(err_json)}") from exc


def print_credit_footer(headers: dict[str, str], body: dict[str, Any]) -> None:
    charged = headers.get("x-credits-charged", body.get("creditsCharged"))
    remaining = headers.get("x-credits-remaining", body.get("creditsRemaining"))
    cache = headers.get("x-cache-status", body.get("cacheStatus"))
    parts = []
    if charged is not None:
        parts.append(f"charged={charged}cr")
    if remaining is not None:
        parts.append(f"remaining={remaining}cr")
    if cache is not None:
        parts.append(f"cache={cache}")
    if parts:
        print(f"Credits: {' | '.join(parts)}")


def run_track_record(base_url: str, raw_json: bool) -> None:
    data, _ = request_json(f"{base_url}/api/v1/oracle/track-record")
    if raw_json:
        print(json.dumps(data, indent=2))
        return
    overall = data.get("overall") or {}
    graded = overall.get("graded", 0)
    picks = overall.get("picks", 0)
    wins = overall.get("wins", 0)
    losses = overall.get("losses", 0)
    pushes = overall.get("pushes", 0)
    brier_model = overall.get("brierModel")
    brier_market = overall.get("brierMarket")
    brier_samples = overall.get("brierSamples", 0)
    avg_clv = overall.get("avgClvPct")
    roi = overall.get("roiPct")
    kelly_roi = overall.get("kellyRoiPct")
    print("FootballPricer Public Calibration Track Record")
    print(f"  Graded / Actionable : {graded} graded / {picks} picks ({wins}W-{losses}L-{pushes}P)")
    print(f"  Model vs Market Brier ({brier_samples}): {brier_model} vs {brier_market}")
    print(f"  Avg CLV (%)         : {avg_clv}")
    print(f"  Flat / Kelly ROI (%): {roi} / {kelly_roi}")


def run_edges(base_url: str, args: argparse.Namespace, api_key: str | None) -> None:
    if not api_key:
        raise RuntimeError("--api-key or FOOTBALLPRICER_API_KEY is required for --mode edges")
    params: dict[str, str] = {"detail": args.detail, "limit": str(args.limit)}
    if args.league:
        params["league"] = args.league
    if args.min_ev is not None:
        params["minEvPct"] = str(args.min_ev)
    url = f"{base_url}/api/v1/oracle/edges?{urllib.parse.urlencode(params)}"
    data, headers = request_json(url, api_key=api_key)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    edges = data.get("edges") or []
    print(f"Upcoming Matches / Edges ({len(edges)} returned, detail={args.detail})")
    for idx, item in enumerate(edges, start=1):
        match_name = f"{item.get('homeTeam', '?')} vs {item.get('awayTeam', '?')}"
        league = item.get("league", "")
        slate_id = item.get("slateId", "")
        top = item.get("topValuePlay")
        if isinstance(top, dict):
            summary = (
                f"{top.get('label')} | EV={top.get('evPct')}% | "
                f"quarterKelly={top.get('quarterKellyPct')}%"
            )
        else:
            summary = (
                f"pass={item.get('pass')} | stability={item.get('stabilityTier')} | "
                f"actionable={item.get('hasActionableEdge')} | cacheCost={item.get('cacheHitCostCredits')}cr"
            )
        print(f"  {idx}. {match_name} [{league}] slateId={slate_id} ({summary})")
    print_credit_footer(headers, data)


def run_reprice(base_url: str, args: argparse.Namespace, api_key: str | None) -> None:
    if not api_key:
        raise RuntimeError("--api-key or FOOTBALLPRICER_API_KEY is required for --mode reprice")
    if args.price is None:
        raise RuntimeError("--price is required for --mode reprice (e.g. 0.48 for a 48c Polymarket share)")

    body: dict[str, Any] = {
        "mode": "quote_only",
        "quotes": [
            {
                "marketKey": args.market_key,
                "format": args.quote_format,
                "price": args.price,
                "slippageBps": args.slippage_bps,
                "commissionPct": args.commission_pct,
            }
        ],
    }
    if args.slate_id:
        body["slateId"] = args.slate_id
    else:
        if not args.home or not args.away:
            raise RuntimeError("Provide either --slate-id or both --home and --away")
        body["homeTeam"] = args.home
        body["awayTeam"] = args.away
        if args.league:
            body["league"] = args.league
        if args.match_date:
            body["matchDate"] = args.match_date

    data, headers = request_json(f"{base_url}/api/v1/oracle/reprice", method="POST", payload=body, api_key=api_key)
    if args.json:
        print(json.dumps(data, indent=2))
        return
    quotes = data.get("quotes") or []
    print(f"Reprice Result for {args.market_key} (mode=quote_only):")
    if quotes:
        for q in quotes:
            print(
                f"  market={q.get('marketKey')} | modelProb={q.get('blendedProbPct')}% "
                f"(fairShare={q.get('fairSharePrice')}) | effImplied={q.get('effectiveImpliedProbPct')}% | "
                f"edge={q.get('impliedEdgePct')}% | EV={q.get('evPct')}% | "
                f"quarterKelly={q.get('quarterKellyPct')}% | +EV={q.get('isPositiveEv')}"
            )
    else:
        print(json.dumps(data, indent=2))
    print_credit_footer(headers, data)


def run_mcp_tools(base_url: str, api_key: str | None, raw_json: bool) -> None:
    rpc_payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    data, _ = request_json(f"{base_url}/api/mcp", method="POST", payload=rpc_payload, api_key=api_key)
    if raw_json:
        print(json.dumps(data, indent=2))
        return
    tools = ((data.get("result") or {}).get("tools")) or []
    print(f"FootballPricer Remote MCP Tools ({len(tools)}):")
    for t in tools:
        print(f"  - {t.get('name')}: {t.get('description')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FootballPricer Calibrated Probability Oracle CLI")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("FOOTBALLPRICER_BASE_URL", "https://www.footballpricer.com"),
        help="Oracle base URL (default: https://www.footballpricer.com)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("FOOTBALLPRICER_API_KEY"),
        help="FootballPricer API key (fp_live_...); defaults to $FOOTBALLPRICER_API_KEY",
    )
    parser.add_argument(
        "--mode",
        choices=["track-record", "edges", "reprice", "mcp-tools"],
        default="track-record",
        help="Operation mode",
    )
    parser.add_argument("--detail", choices=["discovery", "full"], default="discovery", help="Edges detail tier")
    parser.add_argument("--league", default="", help="Optional league filter")
    parser.add_argument("--min-ev", type=float, default=None, help="Minimum EV%% filter for edges")
    parser.add_argument("--limit", type=int, default=15, help="Max edges to return")
    parser.add_argument("--slate-id", default="", help="Cached slateId target for reprice")
    parser.add_argument("--home", default="", help="Home team name for reprice")
    parser.add_argument("--away", default="", help="Away team name for reprice")
    parser.add_argument("--match-date", default="", help="YYYY-MM-DD for reprice")
    parser.add_argument("--market-key", default="1x2_home", help="Market key e.g. 1x2_home, goals_over_2.5, btts_yes")
    parser.add_argument(
        "--quote-format",
        choices=["probability_share", "decimal"],
        default="probability_share",
        help="Quote price format (default: probability_share for Polymarket 0.01..0.99)",
    )
    parser.add_argument("--price", type=float, default=None, help="Share price (0.01..0.99) or decimal odds (>1.01)")
    parser.add_argument("--slippage-bps", type=float, default=0.0, help="Slippage penalty in bps")
    parser.add_argument("--commission-pct", type=float, default=0.0, help="Exchange fee/commission percentage")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        if args.mode == "track-record":
            run_track_record(base_url, args.json)
        elif args.mode == "edges":
            run_edges(base_url, args, args.api_key)
        elif args.mode == "reprice":
            run_reprice(base_url, args, args.api_key)
        elif args.mode == "mcp-tools":
            run_mcp_tools(base_url, args.api_key, args.json)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
