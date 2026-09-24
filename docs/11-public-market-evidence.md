# Public commercial reference — verified 20 September 2026

LastBuy now includes a real-part market evidence screen at `?view=market`, available without exposing any enterprise case data. Manufacturer: **onsemi**. Orderable part: **AP0202AT2L00XPGA0-DR**, a 100-VFBGA image signal processor. This is a new public reference, not an assertion that it replaces the fictional ASIC in historical tested plans.

**24 September recheck:** A web retrieval of the [DigiKey US listing](https://www.digikey.com/en/products/detail/onsemi/AP0202AT2L00XPGA0-DR/7221063), reported as crawled that day, still displayed 2,201 in stock, Last Time Buy, the 7 October date and the five USD tiers below. The [India listing](https://www.digikey.in/en/products/detail/onsemi/AP0202AT2L00XPGA0-DR/7221063) presented a security-verification page in a fresh browser session, and an independent page fetch timed out. Its INR tiers were **not** reverified on 24 September. The combined 20 September snapshot and its timestamp remain unchanged; the application's 24-hour guard therefore refuses to present either currency as a current purchase estimate until both sources are verified again. No challenge was bypassed and no substitute INR conversion was invented.

## Directly observed catalogue prices

Both distributor pages were opened in the browser during this session. USD and INR are separate catalogue observations; no exchange-rate conversion was used.

| Quantity | USD / unit | USD line total | INR / unit | INR line total |
|---:|---:|---:|---:|---:|
| 1 | 12.46000 | 12.46 | 1190.55000 | 1190.55 |
| 10 | 9.78400 | 97.84 | 934.86100 | 9348.61 |
| 25 | 9.11520 | 227.88 | 870.95720 | 21773.93 |
| 100 | 8.37970 | 837.97 | 800.68030 | 80068.03 |
| 250 | 8.37760 | 2094.40 | 800.47968 | 200119.92 |

Sources: [DigiKey US listing](https://www.digikey.com/en/products/detail/onsemi/AP0202AT2L00XPGA0-DR/7221063), [DigiKey India listing](https://www.digikey.in/en/products/detail/onsemi/AP0202AT2L00XPGA0-DR/7221063). Observed stock: 2,201; backorders unavailable. The 2,600-unit manufacturer package is not assumed to be the order minimum. Taxes, freight, tariffs, duties and customer discounts are outside these catalogue subtotals.

An older search-index result reported INR 779.49 and Active lifecycle. The current browser page instead showed INR 1190.55 and Last Time Buy. The stale indexed result was rejected; this is why source observation time is recorded separately from discovery time.

## Manufacturer discontinuance evidence

[onsemi notice PD27281ZA, supplied through DigiKey](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8865/PD27281ZA.pdf), issued 7 January 2026:

- Last-time-buy date: **7 October 2026**; last shipment: **7 April 2027**.
- Orders become non-cancelable/non-returnable; acceptance is conditional on availability and commercial terms. Minimum quantities or values may be imposed.
- The affected-parts table lists **AP0202AT2L00XPGA0-TR** as the replacement. This does not establish customer board, firmware or assembly-process qualification.
- No deadline time zone or exact hour is supplied, so none is invented.

PDF SHA-256: `1168330165aaf040ce65a112718a0b2f214f45b7e319b6b27dcf64c329897cdf`. The PDF was downloaded and pages 1–3 text-inspected. It is a manufacturer-authored notice mirrored by its distributor, not a customer purchase agreement.

## Pricing and authority controls

Unit prices remain exact decimal strings. The server multiplies with Decimal, then rounds the line once, half up. For 250 units the INR result is **200119.92**; rounding the unit price to two decimals first would incorrectly produce **200120.00**.

A requested 10,000 units exceeds 2,201 observed units by **7,799**. The response is `QUOTE_REQUIRED`, with no fabricated unit price or subtotal. Replacement inventory is not pooled into original-part stock. Above the last published tier but within observed inventory, the calculator applies the last published tier as a catalogue estimate, subject to supplier reconfirmation.

The 24-hour freshness threshold is our conservative application policy, not a supplier price guarantee. After that threshold, or on/after the stated last-buy date, current estimates stop pending re-verification. Historical tables retain their original observation date. No purchase, reservation, real supplier RFQ, customer inventory read, or paid model call is performed by this feature.

The earlier ASIC-SYN-017 results and their audit hashes remain intact. Editing those verified historical prices would invalidate the source-bound approvals and make past model evidence misleading. Public real prices are shown in the new reference; example enterprise data remains identified once at workspace level and in source records.

## Refresh procedure

1. Open the exact supplier URLs and verify currency, SKU, packaging, availability, tiers and lifecycle in the current rendered page.
2. Recheck the manufacturer notice for superseding revisions. Never infer a time zone from a date-only notice.
3. Update `lastbuy/market_prices.json` with exact price strings and the actual observation timestamp. Retain the previous version in Git and a digest of any newly retrieved notice.
4. Run the market/API tests, inspect currency switching and an over-stock request in the browser, package and deploy. Do not treat reference refresh as authority to amend enterprise source snapshots or approvals.

Verification this change: **161 automated tests passed**, including exact USD/INR totals, tier/stock boundaries, stale observation denial, cutoff uncertainty, input validation and public-reference/private-case access separation. Browser interaction confirmed INR 250-unit subtotal, USD switching and the 10,000-unit quote-required path.
