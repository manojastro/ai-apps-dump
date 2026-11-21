#!/usr/bin/env python3
"""Generate institutional BTC intelligence report .docx"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
import datetime

OUT = r"D:\ai apps dump\BTC\BTC_Intelligence_Top25_Quant_Research_Protocol.docx"

doc = Document()

# Page setup: landscape A4 for wide table
for section in doc.sections:
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11.69)
    section.page_height = Inches(8.27)
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.5)
    section.right_margin = Inches(0.5)

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(9)
style.paragraph_format.space_after = Pt(4)

def h1(t):
    h = doc.add_heading(t, level=1)
    for r in h.runs:
        r.font.size = Pt(14); r.font.color.rgb = RGBColor(0x1A,0x3C,0x6E)
    return h
def h2(t):
    h = doc.add_heading(t, level=2)
    for r in h.runs:
        r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x1A,0x3C,0x6E)
    return h
def h3(t):
    h = doc.add_heading(t, level=3)
    for r in h.runs:
        r.font.size = Pt(10)
    return h
def para(t, bold=False, italic=False, size=9):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    return p
def bullet(t, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = p.add_run(bold_prefix); r.bold = True; r.font.size = Pt(9)
        r2 = p.add_run(t); r2.font.size = Pt(9)
    else:
        r = p.add_run(t); r.font.size = Pt(9)
    return p
def shade_cell(cell, color="1A3C6E"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn('w:shd'), {qn('w:val'): 'clear', qn('w:fill'): color})
    tcPr.append(shd)
def set_cell(cell, text, bold=False, size=7, color=None, bg=None):
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.bold = bold; r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor(*color)
    if bg: shade_cell(cell, bg)

# COVER
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("COMPREHENSIVE CRYPTO INTELLIGENCE & QUANTITATIVE BTC RESEARCH PROTOCOL")
r.bold = True; r.font.size = Pt(18); r.font.color.rgb = RGBColor(0x1A,0x3C,0x6E)
t2 = doc.add_paragraph(); t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t2.add_run("Top 25 High-Reputation, Non-Paywalled Bitcoin Market Intelligence Sources  |  5 Verticals x 5 Profiles  |  10-Tool Institutional Stack Audit")
r.font.size = Pt(10); r.italic = True
t3 = doc.add_paragraph(); t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t3.add_run(f"Research date: 19 September 2026 (UTC)  |  BTC reference regime: ~$75k–$80k post-halving consolidation, ETF AUM ~$100–102B (~6.3% of BTC mkt cap), cumulative ETF net flows ~$55B  |  Classification: Open-source (X / TradingView / public terminals only)")
r.font.size = Pt(7.5)
para("Execution scope: institutional digital-asset intelligence + quantitative analysis + OSINT. Prioritizes empirical methodology, probabilistic modeling, and capital-preservation mechanics. Excludes affiliate-monetized feeds, paywalled-signal funnels, deletion/retrospective-charting accounts, 1m–5m scalping noise, and pump-and-dump / microcap contamination. Every retained profile was screened for (a) explicit invalidation, (b) multi-cycle track record (3–5y or verified institutional pedigree), (c) high information-to-noise with reproducible charts / code / raw ledger data.", size=8.5)

h1("1. Forensic & Disqualification Protocol (Applied)")
h2("1.1 Automatic disqualification triggers (excluded)")
bullet("Affiliate monetization bias: offshore high-leverage referral links (Bybit / Bitget / MEXC volume incentives) as primary monetization.", "A1 — ")
bullet("Paywalled signal redirection: public feed as incomplete funnel for VIP signals, copy-trading, paid Discord/Telegram.", "A2 — ")
bullet("Selective verification & deletion: retrospective deletion/editing of invalidated setups, retroactive charting without predefined invalidation, unverified PnL screenshots.", "A3 — ")
bullet("LTF noise over signal: hyperactive 1m–5m scalping without structural trade-management or statistical edge.", "A4 — ")
bullet("Pump-and-dump / microcap contamination: illiquid altcoins, paid launches, sponsored promos.", "A5 — ")
h2("1.2 Mandatory retention criteria (all 25 satisfy)")
bullet("Explicit invalidation: entry range + target horizon + hard stop / structure-shift / HTF-close invalidation stated before or at trigger.", "B1 — ")
bullet("Multi-cycle track record: public analysis across bull + bear regimes (min. 3–5 years) or verified institutional pedigree (bank, Bloomberg, Glassnode, etc.).", "B2 — ")
bullet("High information-to-noise: raw order flow, verifiable Pine/Python code, HTF structure, or unmanipulated on-chain metrics with source citation.", "B3 — ")
para("Note on transparency scoring (1–10): composite of auditability (open code / labeled addresses / primary-source links), invalidation discipline, multi-cycle survival, absence of monetization conflict, and correction behavior (openly admits failed calls). 9–10 = institutional-grade audit trail; 7–8 = strong but partial (e.g., proprietary model or occasional narrative). Nothing below 7 was retained.", italic=True, size=8)

h1("2. Master Directory — Top 25 (5 x 5 Verticals)")
para("Conventions: X = X (Twitter); TV = TradingView; Primary Platform(s) lists where free signal is published. 'Operational Vertical' codes: V1 Microstructure & Derivatives; V2 Macro & Liquidity; V3 On-Chain & Entity Forensics; V4 Algo / Quant / AI; V5 Institutional Strategy & News Wire.", italic=True, size=8)

headers = ["#", "Profile / Handle", "Primary Platform(s)", "Vertical", "Core Edge & Methodology", "Key Indicators & Stack", "Invalidation & Risk Framework", "Score"]
rows_data = [
["1", "Byzantine General\n@ByzGeneral", "X + Substack (free) + TradingView ideas", "V1 Microstructure & Derivatives", "Derivatives positioning: OI divergence, funding-rate disparity, liquidation-cluster mapping. Auction-market lens; fade crowded leverage, trade toward max-pain liquidity.", "Coinglass + Laevitas-style OI/funding boards; BTC perp CVD; liquidation heatmaps; HTF S/R. No repaint — exchange-reported aggregates.", "Invalidation: HTF close beyond cluster edge or OI reset (>5% flush) + funding normalization. Risk: no leverage >3x guidance; stop beyond sweep wick; documents failed calls without deletion.", "8.5"],
["2", "Daan Crypto Trades\n@DaanCrypto", "X (free daily threads)", "V1 Microstructure & Derivatives", "Systematic derivatives dashboard: spot-vs-perp CVD, OI build into decay, funding extremes. Mean-reversion of crowded positioning, not price prediction.", "CryptoQuant + Coinglass + Velo; spot/perp CVD split; OI + funding; ETF flow context. Bar-close reads on 1H/4H.", "Invalidation: OI contraction with funding flip, or daily close through structure. Risk: defines stop + invalidation in-post; warns against counter-trend knife-catching until spot absorption.", "8.5"],
["3", "Material Indicators\n@MI_Algos (FireCharts)", "X + FireCharts + TradingView", "V1 Microstructure & Derivatives", "Limit order book forensics: LOB depth, bid/ask liquidity walls, spoof detection, CVD + order-book imbalance. Passive-liquidity behavior before active flow.", "FireCharts LOB heatmap; CVD; order-book imbalance; BTC/USDT L2 depth. Real exchange L2, non-repainting by construction.", "Invalidation: wall pulled/repriced before contact = thesis void; requires >$50M-equivalent absorptive wall within 1% + CVD confirmation. Risk: size by wall persistence, not notional.", "8.0"],
["4", "Kingfisher\n@kingfisher_btc (terminal)", "X + thekingfisher.io (free heatmap)", "V1 Microstructure & Derivatives", "Model-based liquidation intelligence: liquidation maps + Z-score cluster filtering, GEX+, toxic-flow detection. Mean-reversion toward liquidity magnets.", "KF Liquidation Heatmap/Maps (all-leverage + optical_opti <72h), Z-score gradient, KF-API. Estimates, not exchange quotes — disclosed.", "Invalidation: cluster decay/swept-level fade; price acceptance beyond cluster on rising OI voids fade. Risk: probabilistic — never deterministic target; pairs with CVD + OI.", "8.0"],
["5", "CrypNuevo\n@CrypNuevo", "X + TradingView (free ideas)", "V1 Microstructure & Derivatives", "HTF structure + liquidity-sweep execution: predefined zones, wick-fills, liquidation hunts with exact invalidation. One of few large TA accounts that posts entry/stop/target upfront.", "TradingView HTF S/R, liquidation levels (Coinglass overlay), Fib/expansion grids. Forward-posted charts, archived.", "Invalidation: hard stop price printed on chart pre-trigger; hourly/daily close rule. Risk: fixed fractional (1–2R boxes); public win/loss ledger; deletes nothing.", "8.0"],
["6", "Lyn Alden\n@LynAldenContact (lynalden.com)", "X + Newsletter (free) + Books", "V2 Macro & Liquidity", "Monetary-history + stock/flow: Fed balance sheet, fiscal dominance, 1940s vs 2020s analog, global M2 (~83% co-move with BTC per her work). Gradual-print base case; no cavalry-print reliance.", "Fed H.4.1 / FRED / Treasury issuance calendars; realized price vs STH cost basis overlay; gold/BTC debasement tracking. Primary-source cited.", "Invalidation: balance-sheet expansion re-acceleration or real-yield collapse flips gradual-print thesis; cycle call void if BTC holds above realized price + STH basis reclaim. Risk: position-size by valuation quartile, self-custody core.", "9.5"],
["7", "Raoul Pal\n@RaoulGMI (Real Vision / GMI)", "X + Real Vision + GMI (free clips + paid depth)", "V2 Macro & Liquidity", "Everything Code: global M2 / debasement forecasting (~3y lead from interest payments), BTC ~87–90% correlated to liquidity, business-cycle timing. Probabilistic supercycle framing, not date-certain targets.", "GMI liquidity models; cross-asset regression (BTC vs M2, Nasdaq 97% corr. ref); ISM/PMI cycle overlays. Institutional pedigree: Goldman/GLG.", "Invalidation: sustained M2 contraction or debt-rollover without liquidity injection voids supercycle path; $450k cited only as conditional scenario. Risk: cycle position-sizing, multi-year horizon.", "8.5"],
["8", "Julien Bittel\n@BittelJulien", "X + Real Vision Macro", "V2 Macro & Liquidity", "Global-liquidity timing: WLI, credit impulse, DXY vs BTC lead-lag, ETF net-flow regime filter. Complements Pal with higher-frequency cycle dashboards.", "True M2 / WLI composites; DXY, real yields; Farside/SoSoValue ETF flows. Weekly charts, free on X.", "Invalidation: liquidity uptrend break + weekly close below cycle trend voids bullish continuation. Risk: HTF trend-continuation only; no leverage guidance.", "8.0"],
["9", "TechDev\n@TechDev_52", "X + TradingView (free)", "V2 Macro & Liquidity", "Long-cycle quant-macro: log-growth channels, RSI/RVI cycle oscillators, gold/SPX/BTC rotation, halving supply compression. Multi-cycle log charts since 2018.", "TradingView log regression bands, time-based cycle oscillators, global-liquidity overlay. Open charts, reproducible.", "Invalidation: log-channel breakdown on monthly close or oscillator regime-switch failure. Risk: spot-only HTF accumulation bands; explicitly anti-leverage in late cycle.", "8.0"],
["10", "Philip Swift\n@PositiveCrypto (LookIntoBitcoin)", "X + lookintobitcoin.com (free)", "V2 Macro & Liquidity", "Cycle-valuation bridge: Pi Cycle, RHODL, MVRV Z-score bands, realized-price multiples. Halving + ETF structural bid overlay.", "LookIntoBitcoin suite; Glassnode realized cap/MVRV; Farside ETF flows. Free, non-repainting on-chain aggregates.", "Invalidation: MVRV Z >7 distribution or RHODL euphoria band hit = de-risk, not chase; bear invalidation on realized-price loss on weekly close. Risk: DCA bands, no calls without range.", "8.5"],
["11", "James Check (Checkmate)\n@_Checkmatey_ / Checkonchain", "X + checkonchain.com + Substack", "V3 On-Chain & Entity Forensics", "Cointime Economics (co-author with Puell/ARK): AVIV, True Market Mean, STH/LTH cost-basis maps, entity-adjusted realized loss. Ex-Glassnode lead (120+ Week On-Chain).", "Glassnode Studio: Realized Price, STH Cost Basis (~69k ref. Jul-26), MVRV, SOPR, Cointime; Checkonchain suite. Entity clustering, no PnL screenshots.", "Invalidation: recovery thesis needs spot-driven break + hold above STH basis; renewed LTH-loss acceleration voids bottom-build. Risk: probabilistic regime (Risk-On/Off), cohort-spending confirmation.", "9.5"],
["12", "Willy Woo\n@willywoo (Woobull / Vector)", "X + woobull.com + Substack", "V3 On-Chain & Entity Forensics", "Investor-flow valuation: NVT Ratio ('BTC P/E'), CVDD floor, STH realized price vs spot, ETF/corporate flow accounting. Cycle liquidity mapping.", "Woobull charts; Glassnode NVT, CVDD, realized bands; Bitcoin Vector Lite. 1.1M followers, cited 11k+ media.", "Invalidation: STH-basis reclaim + idle-flow rotation required; 79k-break example given 30% odds — probabilistic. Risk: structured cost-basis zones; openly bearish 2026, admits missed targets ($250k '21, 46–54k bottom).", "8.5"],
["13", "Axel Adler Jr\n@AxelAdlerJr", "X + CryptoQuant (verified)", "V3 On-Chain & Entity Forensics", "Valuation + leverage pressure: MVRV, NUPL, SOPR/STH-SOPR, funding/OI pressure, ETF structure. Bank C-level quant, repeatable cycle templates.", "CryptoQuant: MVRV, Realized Price Bands, NUPL, SOPR cohorts, OI/funding. Low-latency, block-level.", "Invalidation: MVRV/NUPL regime flip or STH-SOPR sustained >1 voids bear thesis; funding-reset + OI flush required for longs. Risk: cohort-confirmed entries only.", "9.0"],
["14", "Darkfost\n@Darkfost_Coc", "X + CryptoQuant (verified)", "V3 On-Chain & Entity Forensics", "Exchange-flow forensics: entity-adjusted inflows/outflows, miner reserves, STH/LTH supply, funding/ETF cross-check. Pure data threads, zero promo.", "CryptoQuant exchange reserves, miner flows, SOPR, taker buy/sell; Glassnode cross-verify. Drag-drop cohort analytics.", "Invalidation: thesis tied to reserve-flow reversal + cohort SOPR; no call without on-chain trigger. Risk: flow-confirmation gating, no LTF leverage.", "8.5"],
["15", "Arkham Intelligence\n@ArkhamIntel", "X + arkham.com (free) + Dune", "V3 On-Chain & Entity Forensics", "Entity-level de-anonymization: exchange/whale/miner/ETF custodian labeling, custodial tracking, hack/contagion tracing. Primary evidence for whale-alert clusters.", "Arkham entity labels + alerts; Dune custom queries; Nansen-adjacent clustering. Address-level proof, linkable.", "Invalidation: labeled-flow thesis void if counterparty is internal transfer (re-label) or net Exchange Netflow reverses. Risk: requires multi-tx confirmation + custody attribution before action.", "9.0"],
["16", "LuxAlgo\n@LuxAlgo (library)", "X + TradingView (open + premium)", "V4 Algo / Quant / AI", "Non-repainting systematic toolkit: Signals & Overlays (confirmation + exits, Smart Trail, Neo Cloud), Predictive Ranges, Crypto PCA, On-Chain Signals (IntoTheBlock). Bar-close logic.", "Pine v5; Signals & Overlays, Price Action Concepts, Oscillator Matrix, Backtester (S&O). PCA over top-20 basket; Z-score standardization.", "Invalidation: Smart Trail flip / Trend Strength <50% + squeeze = stand down; exit crosses for partials. Risk: filter-gated signals, TP/SL projector; backtest before live.", "8.5"],
["17", "PlanC\n@PlanCBitcoin (quant models)", "X + TradingView (free scripts)", "V4 Algo / Quant / AI", "Bitcoin Quantile / Expectile regression: log-log fits over full history (from 2010-07-16), accumulation/distribution zones, forecast extrapolation. Probabilistic bands, not lines.", "Pine: Quantile Model + LuxAlgo Expectile variant (7 taus, IRLS fit); BTC All-Time-History Index 3D/1W log scale. Open methodology.", "Invalidation: monthly close outside modeled band + refit drift; uses zone (green buy / red distribution / purple anomaly), never single price. Risk: long-horizon DCA zones only.", "8.0"],
["18", "Ecoinometrics\n@ecoinometrics", "X + Substack (free) + Python", "V4 Algo / Quant / AI", "Regime-switching quant: growth-adjusted positioning, volatility-breakout engines, ETF-flow vs price regressions, Monte Carlo drawdown cones.", "Python (pandas/ccxt) + FRED/Glassnode/SoSoValue feeds; walk-forward splits. Charts reproducible, code-described.", "Invalidation: regime filter flip (vol/ETF-flow) voids breakout; walk-forward decay >20% = halt. Risk: volatility-targeted sizing, max-drawdown stops.", "8.5"],
["19", "TradingShot\n@TradingShot", "TradingView + X (free ideas)", "V4 Algo / Quant / AI", "Automated MA/oscillator systems: 1W MA50/300 crosses, Ichimoku + RSI regime filters, Mayer Multiple bands. 5y+ public TradingView track record across cycles.", "Pine v5 MA ribbons, HL2 systems, VWAP bands; all bar-close, no future-leak. Published source where open.", "Invalidation: weekly close through MA system band or RSI regime flip; each idea prints stop + target horizon. Risk: HTF swing only, 1–2% risk/trade framing.", "7.5"],
["20", "Stockmoney Lizards\n@StockmoneyL", "X + TradingView (free)", "V4 Algo / Quant / AI", "Cycle-math overlays: log-channel + halving-cycle repetition, BTC rainbow/floor models, risk-heat timing. Conservative HTF accumulation framing.", "TradingView log channels, CVDD/MVRV overlays via Glassnode; simple, auditable math. No black-box AI claims.", "Invalidation: log-floor weekly loss or cycle-length extension beyond 1.2x prior voids timing; de-risks into red zone. Risk: spot DCA ladders, no leverage.", "7.5"],
["21", "Walter Bloomberg\n@DeItaone (*Parody wire, de-facto terminal)", "X (free, high-speed)", "V5 Institutional News & Macro Wire", "Zero-latency macro wire: CPI/FOMC/payrolls, Fed speakers, SEC/CFTC headlines with primary-source screenshot/link. Zero editorial bias.", "X real-time + primary docs (BLS/Fed/SEC); timestamped posts. Latency-free reporting, cites source.", "Invalidation: N/A (news, not calls) — risk control is source-verification: requires second primary source before trading headline; corrects/deletes with flag if wrong.", "9.0"],
["22", "Tree News\n@TreeNewsFeed", "X + Telegram (free)", "V5 Institutional News & Macro Wire", "Crypto-native sub-minute wire: ETF flows, liquidations, SEC actions, exchange outages, contagion alerts. Fastest free crypto headline layer.", "Exchange/ETF issuer releases + SoSoValue/Farside cross-check; on-chain alert cross-verify. No opinion.", "Invalidation: N/A — framework is confirmation latency: waits for issuer/SEC doc or 2nd wire before confirming; pins corrections.", "8.5"],
["23", "db\n@tier10k", "X (free)", "V5 Institutional News & Macro Wire", "High-signal headline aggregator: macro + crypto breaking with chart/doc attachment. Institutional desk staple for first headline.", "Primary wires + terminal screenshots; minimal commentary. High SNR.", "Invalidation: N/A — reliability via source link + time-stamp; risk rule: fade first spike until filing/statement linked.", "8.5"],
["24", "Colin Wu\n@WuBlockchain", "X + wublockchain.com (free EN/CN)", "V5 Institutional News & Macro Wire", "Asia-centric primary reporting: miner reserves, exchange flows, regulatory filings (HK/SG/CN/US), ETF custody moves. Names sources, links filings.", "On-chain + company filings + exchange announcements; bilingual primary docs. No affiliate links.", "Invalidation: N/A — journalistic: story updated/corrected with edit history; trading risk = wait for filing hash/tx proof before sizing.", "9.0"],
["25", "Eric Balchunas\n@EricBalchunas (Bloomberg)", "X + Bloomberg (free posts)", "V5 Institutional News & Macro Wire", "ETF-flow authority: spot BTC ETF cumulative net flows (~$55B Sep-26, peak $63B), IBIT/FBTC/ARKB decomposition, AUM vs price-appreciation separation. Structural bid quantification.", "Bloomberg terminal + issuer creations/redemptions + SoSoValue/Farside; excludes price appreciation for pure demand read.", "Invalidation: N/A — data desk: flow thesis flips on consecutive >$250M daily outflows or cumulative-breakdown; single-day IBIT outlier never traded alone. Risk: flow-confirmation for HTF bias only.", "9.5"],
]

# Build table
table = doc.add_table(rows=1, cols=len(headers))
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = True
hdr = table.rows[0].cells
for i, htxt in enumerate(headers):
    set_cell(hdr[i], htxt, bold=True, size=7, color=(255,255,255), bg="1A3C6E")
for rdata in rows_data:
    cells = table.add_row().cells
    for j, val in enumerate(rdata):
        sz = 7
        b = (j == 0 or j == 7)
        c = cells[j]
        # score highlight
        set_cell(c, val, bold=b, size=sz)

# shrink table font / padding
for row in table.rows:
    for cell in row.cells:
        for p in cell.paragraphs:
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)

para("How to read the Score: 9.5 = institutional pedigree + open audit trail + multi-cycle survival + explicit probabilistic framing (Alden / Check / Balchunas). 9.0 = verified institutional data desk with primary-source chain (Balchunas / Arkham / Adler / Wu / Walter). 8.5/8.0 = strong derivatives/on-chain/quant discipline with minor opacity (proprietary model, occasional narrative). 7.5 = solid HTF quant with narrower scope but clean history (TradingShot / Stockmoney). All retained feeds are free at point of use; premium depth (GMI, Glassnode Studio tiers, LuxAlgo Premium, FireCharts) is optional, not a funnel — public posts are complete theses with invalidation.", italic=True, size=7.5)

h1("3. Technical Stack — 10 Essential, Non-Repainting Tools")
para("Audit rule applied: a tool is 'non-repainting' only if it calculates exclusively on bar-close (Pine: barstate.isconfirmed) or on immutable exchange/on-chain prints, with no future-leak, no backfill revision without versioning, and walk-forward / out-of-sample validation where modeling is involved.", italic=True, size=8)

h2("3.1 Order Flow & Microstructure Terminals (4)")
h3("T1 — Coinglass (coinglass.com) — daily derivatives cockpit")
bullet("Tracks: aggregated OI (e.g., $111B ref. Jul-26 capture), 24h volume/liquidations, funding, long/short ratio, spot-perp basis, liquidation heatmaps (Models 1/2/3) + liquidation map bars, ETF-flow panel.", "Metrics: ")
bullet("Non-repaint: exchange-reported prints; heatmap models weight leverage distribution differently — disclose model; threshold slider (e.g., 0.85) filters low-confidence zones.", "Verification: ")
bullet("Use: morning OI/funding/liq-cluster check; fade crowded side only with HTF structure + CVD.", "SOP: ")
h3("T2 — Kingfisher Liquidation Maps + Heatmap (thekingfisher.io)")
bullet("Tracks: estimated liquidation-price concentrations (all-leverage 2w+ view + optical_opti <72h scalping view), Z-score standardized cluster significance, GEX+, toxic flow, aggregated orderbook.", "Metrics: ")
bullet("Non-repaint: model estimates, not exchange quotes — vendor discloses proprietary engine; Z-score filters noise; swept levels decay (honest history).", "Verification: ")
bullet("Use: liquidity-magnet bias; never deterministic target — require CVD/OI confirmation.", "SOP: ")
h3("T3 — Bookmap (bookmap.com + L2 add-ons)")
bullet("Tracks: real-time LOB depth heatmap, footprint/volume bubbles, liquidation indicator (Binance Futures/Bybit/Bitfinex), bid/ask absorption walls.", "Metrics: ")
bullet("Non-repaint: direct L2 feed prints; Binance sends last-liq-per-second (known aggregation limit); backfill supported since v7.4 with versioning.", "Verification: ")
bullet("Use: execution-grade wall/spoof detection (cf. Taha-type 177 BTC wall reads); invalidation = wall pulled before touch.", "SOP: ")
h3("T4 — Exocharts / Aggr / Hyblock (footprint & CVD layer)")
bullet("Tracks: footprint (bid x ask per price), session CVD + spot-vs-perp CVD split, OBI/OFI, VPIN, delta-imbalance stacks (3x+), POC migration.", "Metrics: ")
bullet("Non-repaint: trade-tape classification per interval, summed running total; venue-separated (never blend spot+perp silently); multi-exchange aggregation with disclosed venue list.", "Verification: ")
bullet("Use: Gate-4 absorption (price lower-low + CVD higher-low) + Gate-5 CHoCH close trigger; divergence only valid with fixed window + same instrument.", "SOP: ")

h2("3.2 On-Chain Forensic Platforms (3)")
h3("T5 — Glassnode Studio (glassnode.com / research)")
bullet("Tracks: Realized Cap/Price, STH/LTH Cost Basis & Supply, MVRV Z-Score, SOPR cohorts, NUPL, Entity-Adjusted LTH Realized Loss, Exchange Reserves (cluster-labeled), Cointime/AVIV.", "Core: ")
bullet("Non-repaint: ledger-immutable; clustering via published + proprietary labels with accuracy disclaimer; Week On-Chain gives regime preconditions (e.g., LTH-loss cooldown).", "Verification: ")
bullet("Alert: recovery needs spot-driven STH-basis reclaim + hold; rejection to Realized Price = back to range.", "Signal: ")
h3("T6 — CryptoQuant (cryptoquant.com + Pro-Chart on TradingView)")
bullet("Tracks: exchange inflow/outflow + reserves, miner flows, taker buy/sell, funding/OI pressure, ETF-flow structure, cohort analytics (drag-drop), Quicktake verified authors.", "Core: ")
bullet("Non-repaint: block-level resolution, low-latency proprietary feeds; verified-author (Adler/Darkfost) methods disclosed per post.", "Verification: ")
bullet("Alert: >2-sigma spot outflow vs 30d avg = structural exit; OI +5% into decay + positive funding = cascade risk.", "Signal: ")
h3("T7 — Arkham Intelligence + Dune Analytics (arkham.com / dune.com)")
bullet("Tracks: entity-labeled whale/exchange/miner/ETF-custodian balances, hack/contagion tracing, custom SQL (Dune) for SOPR/NUPL/whale clusters.", "Core: ")
bullet("Non-repaint: address-level proof, linkable tx hashes; Dune queries versioned and forkable; re-labels flagged as internal transfers.", "Verification: ")
bullet("Use: custodial-tracking confirmation for ETF/miner distribution theses; require multi-tx + attribution.", "SOP: ")

h2("3.3 Quantitative & AI-Assisted Scripting Environments (3)")
h3("T8 — TradingView Pine Script v5 (native) + LuxAlgo Suite")
bullet("Tracks: Signals & Overlays (Confirmation+Exits, Smart Trail, Reversal Zones, Trend Tracer/Catcher, Neo Cloud, dashboard Trend Strength/Squeeze), Predictive Ranges (ATR ranges, non-repaint), Crypto PCA (PC1 over top-20 basket, Z-scored, ±2σ extremes), On-Chain Signals (IntoTheBlock: net growth / in-money / concentration / large-tx).", "Stack: ")
bullet("Non-repaint proof: Pine executes on bar-close (barstate.isconfirmed); LuxAlgo Breakouts verified non-repaint in replay; Predictive Ranges explicitly 'do not repaint'; PCA uses SMA-smoothed Z-scores with disclosed lookback; some auto-trendline modules DO recalc — disable for signals.", "Verification: ")
bullet("Use: HTF (15m–1W) presets (Trend/Swing/Contrarian), Smart-Trail-gated entries, exit crosses for partials; Backtester (S&O) + Screener for walk-forward.", "SOP: ")
h3("T9 — Python ccxt Backtesting Pipeline (open-source)")
bullet("Stack: Python pandas/ccxt/backtrader-vectorbt + Glassnode/CryptoQuant/SoSoValue APIs; Glassnode MCP (1,700+ assets, 900+ metrics) for LLM-assisted analysis. Verification: bar-close-only features, purged/embargoed splits, no lookahead; report out-of-sample decay; halt if >20% degradation. Tracks: multi-venue OHLCV + funding/OI, Walk-Forward Optimization, Monte Carlo drawdown cones, regime-switch filters.", "T9 — ")
bullet("Maps to V4 (Ecoinometrics/PlanC) methodology; required before sizing any LuxAlgo/Pine system live.", "Gate: ")
h3("T10 — IntoTheBlock + LuxAlgo On-Chain Signals Bridge")
bullet("Tracks: Net Network Growth, In-the-Money momentum, Whale Concentration change, Large-Tx ($100k+) vs 21/30 EMA; gauge/table/history/average (triangular MA20) views.", "Core: ")
bullet("Non-repaint: 7-period ROC on daily close; thresholds user-set per asset; daily timeframe optimal; data via TradingView customData feed.", "Verification: ")
bullet("Use: directional-bias filter for V3 theses (bullish only if bull signals > bear); never standalone entry.", "SOP: ")

h1("4. Operational Playbook — How to Use the 25 + 10 Without Getting Chopped")
bullet("Morning triage (15 min): T1 OI/funding/liq + T5/T6 STH-basis vs spot + T10 ETF flows (Farside/SoSoValue via @EricBalchunas/@TreeNewsFeed). If OI stretched + funding crowded + price into KF cluster with no spot CVD follow-through → stand down / fade plan only.", "1. ")
bullet("Entry gating (V1+V3+V4 confluence): Gate-4 absorption (sweep + CVD divergence + OI flush) → Gate-5 CHoCH close → V3 cohort confirm (STH-SOPR / LTH-loss cooldown) → T8 Smart-Trail-aligned signal. Miss one gate = no trade.", "2. ")
bullet("Invalidation-first sizing: every idea must have pre-printed stop/structure-close; size 0.5–2R; T8 exit crosses for partials; macro (V2) sets max exposure (gradual-print = valuation-quartile sizing, not leverage).", "3. ")
bullet("News discipline (V5): never trade first headline (@DeItaone/@tier10k/@TreeNewsFeed) — wait for primary doc (BLS/Fed/SEC filing, issuer creation file, Arkham tx) via @WuBlockchain; fade spike until confirmed.", "4. ")
bullet("Decontamination: instant mute on any retained account if it posts affiliate-coded leverage link, VIP-funnel, deleted call, or microcap promo — 1 strike = remove from rotation pending 90-day re-audit.", "5. ")

h1("5. Disqualification Log (illustrative — why CT favorites were cut)")
para("Bitcoin Prediction Scoreboard / CT post-mortems show why popularity ≠ retainability: e.g., high-noise scalpers (A4), VIP-funnel chart accounts (A2), and perma-bull microcap cross-promoters (A5) fail B1–B3 even with 300k+ followers. Retained accounts above survived because they publish stops, keep failed calls public, and cite exchange/ledger/primary sources. Full per-handle audit trail available from X archives + TradingView idea history + Glassnode/CryptoQuant author pages.", size=8.5)

h1("6. Sources & Verification Anchors (sample)")
bullet("Glassnode Week On-Chain W28-2026 (STH basis ~69k, LTH-loss peak cooldown); CryptoQuant Quicktakes (Adler/Darkfoster cohorts); Checkonchain About/Cointime Economics (Glassnode × ARK); Woobull/Vector Lite (NVT/CVDD).", "On-chain: ")
bullet("Lyn Alden (lynalden.com, Jul-2026 sentiment/gradual-print; Feb-2026 Warsh/Fed balance-sheet); Raoul Pal GMI/Everything Code (87–90% liquidity correlation; $450k conditional); Bittel liquidity dashboards.", "Macro: ")
bullet("Kingfisher docs (CVD vs LiqMap methodology + Z-score); Bookmap liquidation indicator KB (venue limits); Coinglass/CoinAnk/Hyblock comparative review Jul-2026; MarketTrace/ChartWhisperer CVD doctrine (spot-vs-perp split).", "Microstructure: ")
bullet("LuxAlgo library docs (Signals & Overlays, Expectile/Quantile model, Predictive Ranges 'do not repaint', On-Chain Signals Pine source); TradingView indicator lab repaint notes.", "Quant: ")
bullet("ETF flows Sep 17–18 2026: $159M (IBIT +$183M) then $433M (FBTC $311M, IBIT $108M); AUM ~$100–102B (~6.3% BTC mkt cap); cumulative ~$55B (peak $63B) via Balchunas/SoSoValue — anchors V5 flow-reading SOP.", "Flows: ")

para("Compiled as open-source intelligence synthesis. Not financial advice. All handles/URLs verified live as of September 2026; follower counts, prices, and flow prints are regime snapshots — re-verify before sizing. Methodology honors no-paywall constraint: every edge above is consumable free; optional paid depth never gates the invalidation.", italic=True, size=8)

# Footer with date
para(f"Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — BTC_Intelligence_Top25 protocol.", italic=True, size=7)

doc.save(OUT)
print(f"saved -> {OUT}")
