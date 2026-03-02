# Elicitation Guide for SaaS Products

A structured set of questions for gathering requirements from founders, product owners, and stakeholders before building a SaaS product.

---

## How to Use This Guide

1. Work through sections sequentially — earlier sections inform later ones
2. Take notes in the user's own words — avoid paraphrasing too early
3. Probe vague answers with follow-up questions
4. After each section, summarize what you heard and ask for confirmation
5. Flag conflicting answers and resolve them before moving on

---

## Section 1: The Core Problem

**Goal**: Understand the specific, concrete problem this product solves.

### Opening Questions

1. Describe the problem you're solving in one or two sentences. Pretend you're explaining it to someone outside your industry.

2. How do you currently solve this problem? Walk me through the exact steps.

3. What do you do when the current solution fails or falls short?

4. How long have you lived with this problem? When did it first become painful?

### Probing Questions (use when answers are vague)

- "Can you give me a specific example of when this problem cost you time or money?"
- "What was the last time you were frustrated by this? What happened?"
- "What would you have done differently if the problem didn't exist?"

### Red Flags to Watch For

- Problem is described as a solution ("I need a dashboard") — redirect: "What decision does the dashboard help you make?"
- Problem is too broad ("communication is broken") — narrow: "Which specific part of communication? Between whom?"
- Problem is hypothetical ("users probably struggle with X") — validate: "Have you seen this happen? With whom?"

---

## Section 2: Target Users

**Goal**: Define the specific person experiencing the problem — not a demographic, but a context.

### Primary User Questions

1. Who is the main person experiencing this problem day-to-day?
   - What is their job title and role?
   - What does their day look like?
   - What tools do they use most?

2. What are they responsible for achieving? What does success look like in their job?

3. What do they find most frustrating about their current tools or workflow?

4. How technically sophisticated are they?
   - Do they use spreadsheets heavily? Write formulas?
   - Are they comfortable with new software?
   - Have they used similar products before?

### Buyer vs. User Questions

5. Is the user the same person who would approve buying the product?
   - If not: who decides to purchase? What does that person care about?
   - What would make a buyer reluctant to purchase?

6. Who else interacts with the output of this product? (Stakeholders, downstream teams)

### Ideal Customer Profile (ICP)

7. Describe your ideal first customer in detail:
   - Industry or vertical
   - Company size (number of employees or revenue)
   - Geography (country, region, language)
   - Stage (startup, growth, enterprise)

8. Are there user types you explicitly do NOT want to serve? (Helps clarify ICP boundaries)

---

## Section 3: Current Alternatives

**Goal**: Understand what users do today so you know what you must improve on.

### Current Workflow Questions

1. Walk me through exactly how you solve this problem today, step by step.
   - What triggers the process?
   - What tools do you touch?
   - Where does it end?

2. How much time does this take per week? Per month?

3. Who is involved in this workflow besides yourself?

4. Where does the current process break down most often?

### Existing Tool Questions

5. Have you tried any software products to solve this problem?
   - What did you try?
   - Why did it not work?
   - What did you like about it?

6. Are there general-purpose tools you use (spreadsheets, email, Slack, Notion) to fill the gap?
   - What do they do well?
   - What do they fail to do?

7. Why haven't you built an internal tool or hired someone to handle this?

---

## Section 4: The Proposed Solution

**Goal**: Define the solution at a high level without over-specifying.

### Core Concept Questions

1. Describe the product you want to build in one sentence. Pretend you're writing a tagline.

2. What is the core action the product helps users accomplish?
   - Framing: "With this product, users can [do X] in [Y minutes] instead of [current approach]."

3. What are the 3–5 things the product must do to deliver value? (Focus on capabilities, not features)

4. If you had to launch in 4 weeks, what would you cut and still have something worth using?

### MVP Boundary Questions

5. What features are nice-to-have but not essential for v1?

6. What are you explicitly choosing NOT to build in the first version?

7. What could you build manually or with existing tools temporarily while you validate the core value?

---

## Section 5: Value & Economics

**Goal**: Understand the economic case for the product.

### Value Quantification

1. How much does the current problem cost?
   - In hours per week (multiply by hourly rate)
   - In direct costs (tools, contractors, errors, rework)
   - In opportunity cost (what can't you do because of this problem)

2. What would users be willing to pay per month to make this problem disappear?

3. Are there comparable products in the market? What do they charge?

### Business Model

4. How do you plan to monetize this product?
   - Per seat / per user?
   - Usage-based (per API call, per document, per hour)?
   - Flat monthly subscription?
   - Freemium?
   - One-time purchase?

5. What is the minimum price that would make this product financially viable for you to build?

---

## Section 6: Constraints & Non-Negotiables

**Goal**: Surface requirements and constraints that constrain design decisions.

### Technical Constraints

1. Are there systems this product must integrate with? (CRMs, ERPs, databases, APIs)

2. Does the product need to run on specific platforms? (Web, mobile, desktop, specific OS)

3. Are there data residency or storage requirements? (Must data stay in EU, on-premise, etc.)

4. Are there performance requirements? (Must respond in <2 seconds, must handle 10,000 concurrent users)

### Compliance & Regulatory

5. Does the product touch sensitive data?
   - Personal data → GDPR, CCPA considerations
   - Health data → HIPAA
   - Financial data → PCI-DSS, SOX
   - Payment processing → PCI-DSS

6. Are there industry-specific compliance requirements in your target market?

7. Will you need certifications to sell to enterprise customers? (SOC2, ISO 27001)

### Team & Resource Constraints

8. What is the current team composition? (Technical? Design? Product?)

9. Are there technologies the team is already proficient in that should be preferred?

10. Are there hard deadlines (launch events, funding milestones, contractual commitments)?

---

## Section 7: Success & Failure

**Goal**: Define what "working" looks like before you start building.

### Success Criteria

1. What does success look like 6 months after launch?
   - Revenue or number of customers
   - Daily active users
   - Key engagement metric (sessions per week, features used, time in product)

2. What would make you feel confident that this product is working?
   - User testimonials ("I can't imagine going back")
   - Churn rate
   - Net Promoter Score

3. What metric would you check every morning to know if the product is healthy?

### Failure Signals

4. What would cause you to reconsider this product direction?
   - No one signs up after launch
   - Users sign up but don't return
   - Users use it once and cancel

5. At what point would you pivot? What would you pivot to?

---

## Synthesis: Common Elicitation Traps

**Trap 1: Solutionitis** — User describes features, not problems.
> Redirect: "Help me understand what problem that feature solves. What goes wrong without it?"

**Trap 2: The All-Inclusive List** — User wants everything in v1.
> Redirect: "If you could only launch with ONE of these capabilities, which one would still make it worth using?"

**Trap 3: Hypothetical Users** — User describes users they haven't talked to.
> Redirect: "Have you spoken to any of these users? What did they tell you?"

**Trap 4: Assumed Market Size** — User claims a large market without data.
> Redirect: "Where does that number come from? How many of those would actually pay for this?"

**Trap 5: Vague Differentiation** — "We're better, faster, cheaper."
> Redirect: "Faster than what specifically? By how much? What makes the speed possible for you but hard for competitors?"
