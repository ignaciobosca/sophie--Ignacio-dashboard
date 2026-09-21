# Amazon Ads — Sponsored Products creation API (reference)

All calls go through the Sophie Hub bridge tool:

```
mcp__Sophie_Hub__sophie_call_amazon_ads_mcp(
  profile_id = "<Amazon Ads profileId for the chosen store+marketplace>",
  tool_name  = "<campaign_management-...>",
  arguments  = { ... }   # the "arguments" object below
)
```

- **Writes are restricted to Sophie Society staff.** External callers get a clear error. Nacho (ignacio@sophiesociety.com) is staff, so writes are allowed.
- Every write body needs `accessRequestedAccount`. When calling through the bridge you already pass `profile_id`; also mirror it inside the body as `accessRequestedAccount: { profileId: "<same>" }` unless the bridge injects it (if a call is rejected for a missing account, add it).
- **Do NOT send the `skill` field.** It is only for registered skill definitions and will break the call if you invent values. Omit it entirely.
- `adProduct` is always `"SPONSORED_PRODUCTS"`. `costType` is `"CPC"`.
- Currencies/marketplaces: pass the marketplace code (e.g. `US`, `CA`, `MX`, `UK`→`GB`). Note Amazon uses `GB` for the UK marketplace.
- **After every create call, read the response and capture the returned entity id** (campaignId / adGroupId / adId / targetId). The next step needs it. Responses can also carry per-row errors even on a 200 — inspect them and treat a row-level error as a failure for that entity.

There are two creation paths. Use **singleshot for AUTO** campaigns and the **individual tools for MANUAL** campaigns (so every keyword/target gets its own bid).

---

## Path A — AUTO campaign: `campaign_management-create_singleshot_sp_campaign`

Creates campaign + ad group + product ad(s) + auto targeting in ONE atomic call. `oneshotCampaigns` accepts exactly 1 campaign per call.

```jsonc
arguments = {
  "body": {
    "accessRequestedAccount": { "profileId": "<profileId>" },
    "oneshotCampaigns": [{
      "marketplaces": ["US"],
      "campaignName": "SO | <Product> | <ASIN> | SPA | Auto",
      "startDateTime": "2026-08-21T00:00:00Z",          // activation date; default = tomorrow
      "budgets": {
        "budgetValue": {
          "marketplaceSettings": [
            { "marketplace": "US", "monetaryBudget": { "value": 20 } }   // daily budget
          ]
        }
      },
      "portfolioId": "<optional>",
      "adGroupName": "SO | <Product> | <ASIN> | SPA | Auto",
      "bid": {
        "marketplaceSettings": [
          { "marketplace": "US", "defaultBid": 0.75 }     // ad group default bid
        ]
      },
      "creative": {
        "productCreativeSettings": {
          "advertisedProduct": {
            "productIdType": "ASIN",
            "marketplaceSettings": [
              { "marketplace": "US", "productId": "B0XXXXXXXX" }   // one entry per ASIN
            ]
          }
        }
      },
      "autoCreateTargets": true      // AUTO campaign
    }]
  }
}
```

Notes:
- `startDateTime` is how we avoid spending today: set it to the chosen activation date at 00:00 in the marketplace's timezone (default = tomorrow). The campaign can be `ENABLED` and still not spend until that date.
- For a manual campaign in one shot you *can* set `autoCreateTargets:false` and add a single `target` object, but singleshot only takes ONE target — so prefer Path B for manual campaigns with multiple keywords.

---

## Path B — MANUAL campaign: individual tools (per-keyword bids)

Run in order, capturing ids as you go. Any step's response may contain the new id under a `campaignId` / `adGroupId` / `adId` field (exact envelope varies — read the whole response).

### B1. `campaign_management-create_campaign`

```jsonc
arguments = {
  "body": {
    "accessRequestedAccount": { "profileId": "<profileId>" },
    "campaigns": [{
      "adProduct": "SPONSORED_PRODUCTS",
      "name": "SO | <Product> | <ASIN> | SPM | <Theme> | Exact",
      "state": "ENABLED",                       // ENABLED + future startDateTime = no spend until then
      "costType": "CPC",
      "marketplaceScope": "SINGLE_MARKETPLACE",
      "marketplaces": ["US"],
      "startDateTime": "2026-08-21T00:00:00Z",  // activation date (default tomorrow)
      // "endDateTime": optional,
      "portfolioId": "<optional>",
      "budgets": [{
        "budgetType": "MONETARY",
        "recurrenceTimePeriod": "DAILY",
        "budgetValue": { "monetaryBudget": { "value": 20 } }   // daily budget
      }],
      "optimizations": {
        "bidSettings": {
          "bidStrategy": "SALES_DOWN_ONLY",     // see bid-strategy map below
          "bidAdjustments": {
            "placementBidAdjustments": [        // only include placements the user set > 0
              { "placement": "TOP_OF_SEARCH", "percentage": 30 },
              { "placement": "REST_OF_SEARCH", "percentage": 0 }
            ]
          }
        }
      }
    }]
  }
}
```

**Bid-strategy map** (what the user picks → enum):
- "Dynamic bids – down only" (Sophie default) → `SALES_DOWN_ONLY`
- "Dynamic bids – up and down" → `SALES_UP_AND_DOWN`
- "Fixed bids" → `MANUAL`

**Placement enum:** `TOP_OF_SEARCH`, `REST_OF_SEARCH`, `PRODUCT_PAGE`, `HOME_PAGE`. `percentage` is an integer (e.g. `30` = +30%).

> The schema also exposes `audienceBidAdjustments` and `shopperSegmentBidAdjustments`. These are **Sponsored Display / DSP** features — **not Sponsored Products**. Do NOT set them for SP campaigns. Audience modifiers like "high interest" belong to the future SB/SD extension.

### B2. `campaign_management-create_ad_group`

```jsonc
arguments = {
  "body": {
    "accessRequestedAccount": { "profileId": "<profileId>" },
    "adGroups": [{
      "adProduct": "SPONSORED_PRODUCTS",
      "campaignId": "<from B1>",
      "name": "SO | <Product> | <ASIN> | SPM | <Theme> | Exact",   // MUST equal the campaign name (B1) verbatim
      "state": "ENABLED",
      "bid": { "defaultBid": 0.75 }             // fallback bid for the ad group
    }]
  }
}
```

### B3. `campaign_management-create_ad` (product ad — one per advertised ASIN/SKU)

```jsonc
arguments = {
  "body": {
    "accessRequestedAccount": { "profileId": "<profileId>" },
    "ads": [{
      "adProduct": "SPONSORED_PRODUCTS",
      "adType": "PRODUCT_AD",
      "adGroupId": "<from B2>",
      "state": "ENABLED",
      "creative": {
        "productCreative": {
          "productCreativeSettings": {
            "advertisedProduct": {
              "productIdType": "SKU",           // SELLERS use SKU; vendors use ASIN
              "productId": "<SKU-or-ASIN>"
            }
          }
        }
      }
    }]
  }
}
```

- **Sellers must advertise by SKU.** Resolve each ASIN → SKU via `mcp__Sophie_Hub__get_product_catalog` (or `get_product_catalog_bulk`) for the store before this call. If a SKU can't be found, flag that ASIN and skip it (report at the end).
- **One ASIN can have several SKUs.** Prefer the active, in-stock, FBA offer; if two live offers remain, ask the user which SKU to advertise — never guess (see SKILL.md Step 4). Send one `create_ad` per SKU you actually advertise.

### B4. `campaign_management-create_target` (batch keywords/products WITH per-keyword bids)

`targets` is an array — send all positive targets in one call.

```jsonc
arguments = {
  "body": {
    "accessRequestedAccount": { "profileId": "<profileId>" },
    "targets": [
      {
        "adProduct": "SPONSORED_PRODUCTS",
        "adGroupId": "<from B2>",
        "campaignId": "<from B1>",
        "state": "ENABLED",
        "negative": false,
        "targetType": "KEYWORD",
        "bid": { "bid": 0.92 },                 // per-keyword bid (H10 CPC)
        "targetDetails": {
          "keywordTarget": { "keyword": "wool dryer balls", "matchType": "EXACT" }  // BROAD | PHRASE | EXACT
        }
      }
      // ...one object per keyword; all share the batch match type
    ]
  }
}
```

**Product/ASIN targeting** (manual product campaigns) uses `targetType: "PRODUCT"`:

```jsonc
{
  "adProduct": "SPONSORED_PRODUCTS",
  "adGroupId": "<from B2>", "campaignId": "<from B1>",
  "state": "ENABLED", "negative": false,
  "targetType": "PRODUCT",
  "bid": { "bid": 0.80 },
  "targetDetails": {
    "productTarget": {
      "productIdType": "ASIN",                  // competitor/own ASIN to target
      "matchType": "PRODUCT_EXACT",             // PRODUCT_EXACT | PRODUCT_SIMILAR
      "product": { "marketplaceSettings": [ { "marketplace": "US", "productId": "B0COMPETIT" } ] }
    }
  }
}
```

### B5. Negatives (optional) — same `create_target`, `negative: true`

Negative keywords have no bid. Match types for negatives: keyword → `EXACT` or `PHRASE` (Amazon has no negative broad for SP keywords); product → `productTarget` with `matchType: "PRODUCT_EXACT"`.

```jsonc
{
  "adProduct": "SPONSORED_PRODUCTS",
  "adGroupId": "<from B2>", "campaignId": "<from B1>",
  "state": "ENABLED", "negative": true,
  "targetType": "KEYWORD",
  "targetDetails": { "keywordTarget": { "keyword": "cheap", "matchType": "PHRASE" } }
}
```

---

## Portfolios (optional)

`campaign_management-create_portfolio` — create a portfolio, then pass its id as `portfolioId`. `campaign_management-query_portfolio` lists existing ones if the user wants to attach to an existing portfolio.

## Post-launch state control

`campaign_management-update_campaign_state` flips ENABLED/PAUSED/ARCHIVED if the user changes their mind after creation.
