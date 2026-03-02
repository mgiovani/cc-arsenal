# Competitive Analysis Guide

A structured approach to researching and analyzing competitors when building a SaaS product.

---

## Purpose

Competitive analysis helps you:
- Understand what users already have access to
- Identify gaps that your product can exploit
- Define clear differentiation
- Set appropriate pricing and positioning
- Avoid building features users can already get elsewhere for free

---

## Step 1: Discover Competitors

### Search Strategies

**Direct search terms** (replace `[problem]` and `[user]` with specifics):
- `[problem] software`
- `[problem] tool for [user type]`
- `best [problem] solutions`
- `[problem] alternatives`
- `[problem] SaaS`

**Review site searches**:
- **G2.com**: Search by category; look at "top rated" and "trending"
- **Capterra**: Excellent for B2B software categories
- **ProductHunt**: Good for newer indie products and recent launches
- **AlternativeTo.net**: Finds products users switch between

**Community searches** (search on these platforms):
- Reddit: `r/[industry]`, `r/entrepreneur`, `r/smallbusiness`
- Hacker News: `site:news.ycombinator.com [problem]`
- LinkedIn: Search for "[category] software" in jobs and company posts

**VC / investor signals**:
- Crunchbase: Search by category to find funded competitors
- AngelList: Lists startups in your space
- CB Insights: Industry reports often name category leaders

### Categorize What You Find

Organize competitors into three tiers:

**Tier 1 — Direct Competitors**: Same user, same problem, similar approach
- The first thing users will compare you to
- Must understand deeply

**Tier 2 — Indirect Competitors**: Same user or same problem, different approach
- Users may use these as substitutes (e.g., spreadsheets instead of dedicated software)
- Important for understanding switching costs

**Tier 3 — Adjacent Players**: Different user or problem, but overlap exists
- May expand into your space; may be acquisition threats
- Less urgent but worth monitoring

---

## Step 2: Profile Each Competitor

For each Tier 1 competitor, gather:

### Basic Facts

| Field | What to Find |
|-------|-------------|
| Company name | Official name |
| Website | Primary URL |
| Founded | Year founded (from Crunchbase or LinkedIn) |
| Funding | Total raised, last round, investors |
| Team size | Approximate headcount (from LinkedIn) |
| Headquarters | Country / city |

### Product Profile

| Field | What to Find |
|-------|-------------|
| Value proposition | Their headline / tagline (from homepage) |
| Core features | What do they prominently advertise? (from features page) |
| Target user | Who are they selling to? (from homepage messaging) |
| Use cases | What problems do they claim to solve? |
| Integrations | What tools do they connect to? |
| Platform | Web? Mobile? Desktop? API? |

### Business Model

| Field | What to Find |
|-------|-------------|
| Pricing model | Freemium? Subscription? Usage-based? |
| Pricing tiers | Starter/Pro/Enterprise price points (from pricing page) |
| Free trial | Do they offer one? For how long? |
| Contract | Monthly or annual? Any lock-in? |
| Enterprise sales | Do they have a sales team? Contact-only pricing? |

---

## Step 3: Feature Comparison Matrix

List the 10–15 most important features in your space, then check whether each competitor has them.

Example template:

| Feature | Your Product | Competitor A | Competitor B | Competitor C |
|---------|-------------|-------------|-------------|-------------|
| Core feature 1 | ✅ | ✅ | ✅ | ❌ |
| Core feature 2 | ✅ | ❌ | ✅ | ✅ |
| Integration: Slack | ✅ | ✅ | ❌ | ❌ |
| Mobile app | ❌ | ✅ | ❌ | ❌ |
| API access | ✅ | ✅ | ✅ | ❌ |
| SSO / Enterprise auth | ✅ | ✅ | ❌ | ❌ |
| Audit logs | ✅ | ✅ | ❌ | ❌ |
| White label | ❌ | ❌ | ✅ | ❌ |
| Offline mode | ❌ | ❌ | ❌ | ❌ |

**Legend**: ✅ = Has it | ❌ = Doesn't have it | 🟡 = Partial/limited

---

## Step 4: Review Analysis

Go beyond features — understand what users actually experience.

### Where to Find Reviews

- **G2.com**: Filter by "most recent" and read 1-star and 5-star reviews
- **Capterra**: Similar to G2, strong for SMB tools
- **App Store / Google Play**: For mobile products
- **Reddit**: Search `[competitor name] review` or `[competitor name] alternative`
- **Twitter/X**: Search competitor name + words like "frustrating", "love", "switched from"

### What to Extract

For each competitor, extract:

**What users love** (from 5-star reviews):
- Specific features they praise
- Moments of delight or surprise
- Comparisons to what they used before

**What users hate** (from 1-2 star reviews):
- Support complaints
- Features that are broken or missing
- Pricing frustrations
- Reliability issues
- Onboarding confusion

**Common switching reasons** (from "why I switched" posts):
- What broke the relationship?
- What did they switch TO?

### Review Analysis Template

```
Competitor: [Name]
Total reviews analyzed: [N]
Average rating: [X/5]

Users Love:
- [Specific strength with frequency: "mentioned in 40% of positive reviews"]
- [Specific strength]

Users Hate:
- [Specific weakness with frequency: "top complaint in 60% of negative reviews"]
- [Specific weakness]

Common Switch Triggers:
- [Reason users leave]
- [Reason users leave]

Opportunity This Reveals:
- [What gap can we fill based on these complaints?]
```

---

## Step 5: Positioning Analysis

Understand how each competitor positions itself:

### Positioning Dimensions

**Price positioning**: Budget | Mid-market | Premium | Enterprise

**Feature depth**: Broad/shallow (many features, none deep) vs. Narrow/deep (fewer features, excellent execution)

**User sophistication**: Self-serve / simple vs. Requires training / complex

**Market focus**: Horizontal (all industries) vs. Vertical (specific industry)

**Delivery model**: SaaS / cloud vs. On-premise vs. Hybrid

### Positioning Map

Draw a simple 2x2 grid with the most important dimensions for your market:

```
            SIMPLE / SELF-SERVE
                    |
                    |
CHEAP ______________|______________ EXPENSIVE
                    |
                    |
            COMPLEX / ENTERPRISE
```

Place each competitor on the map. Find the empty quadrant where you can win.

---

## Step 6: Gap Analysis

After completing competitor profiles, identify gaps:

### Gap Types to Look For

**Feature gaps**: Important capabilities that no or few competitors have
- Look at frequent feature requests on competitor review sites
- Look at what users do as workarounds

**User gaps**: Segments of users underserved by current products
- Small businesses vs. enterprise (often a gap)
- Specific verticals (e.g., "invoicing for freelancers" vs. "invoicing for agencies")
- Geographic gaps (product not localized for certain markets)

**Experience gaps**: Poor UX, slow onboarding, bad support
- High support ticket volume = poor UX
- Long onboarding = complex product
- "Had to watch 10 tutorials" = bad documentation

**Price gaps**: Segments priced out of the market
- Enterprise tools with no SMB option
- Products with no free tier in a freemium-heavy market
- Usage-based pricing that becomes expensive at scale

**Integration gaps**: Missing connections to popular tools
- If 80% of target users use Salesforce but no competitor integrates, that's a gap

---

## Output: Competitive Landscape Section

Use this structure in `docs/project-brief.md`:

```markdown
## Competitive Landscape

### Market Overview
[1 paragraph: how crowded is this market? Where is investment flowing? What trends are shaping it?]

### Direct Competitors

| Competitor | Value Prop | Target User | Price | Key Strength | Key Weakness |
|------------|------------|-------------|-------|-------------|-------------|
| [Name] | [Tagline] | [User type] | [From $X/mo] | [Strength] | [Weakness] |

### Indirect Competitors / Substitutes
- **Spreadsheets / Manual Process**: [% of users still doing this; why they haven't switched]
- **[General tool]**: [How users use it as a workaround]

### Our Differentiation
[How does this product fill the gap identified above? Be specific about what you do that competitors don't.]

### Why We Win
[Articulate the unfair advantage — speed, price, integrations, UX, vertical focus, or unique insight]
```

---

## Quick Competitive Analysis Checklist

- [ ] Found at least 3 direct competitors
- [ ] Found at least 2 indirect competitors / substitutes
- [ ] Checked review sites for sentiment on top 2 competitors
- [ ] Identified the primary complaint users have with existing solutions
- [ ] Completed feature comparison matrix
- [ ] Mapped competitor positioning
- [ ] Identified at least 1 clear gap or differentiation opportunity
- [ ] Documented pricing models for all direct competitors
- [ ] Captured the differentiation statement ("We win because...")
