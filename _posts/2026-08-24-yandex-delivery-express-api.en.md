---
layout: post
title: "The Spec Exists Now, and You Still Can't Download It — A Close Read of Yandex Delivery's Express API"
date: 2026-08-24 09:00:00 +0000
tags: [OpenAPI, API design, Yandex]
lang: en
---

*[Читать по-русски →]({{ '/2026/08/24/yandex-delivery-express-api.ru/' | relative_url }})*

---

# The spec exists now, and you still can't download it

> **In short.** To build a typed client for Yandex Delivery's Express API I had to write the vendor's
> OpenAPI document myself — 2,028 lines of YAML transcribed from HTML pages. Yandex now publishes a
> reference that is clearly rendered *from* an OpenAPI document, which is a real improvement; the
> document itself is still not downloadable, so you cannot generate, lint, mock or diff against it.
> Below is what a year of reading that documentation and calling the real API taught me, defect by
> defect, each one paired with what I would have done instead. Some of the defects are mine.

## Where this comes from

I write client software for Apple platforms. In 2025 I needed to call Yandex Delivery's Express API —
the B2B Cargo integration behind same-city courier delivery — from a Swift app, and I wanted a typed
client generated from a contract rather than a hand-rolled networking layer. That is the approach I
argued for at length in [an earlier article]({{ '/2025/06/03/openapi-source-of-truth.en/' | relative_url }}):
one machine-readable document, and everything else derived from it.

Searching Habr I found exactly one article about the Swift generator itself — [a sceptical review from
Ozon Tech's iOS team](https://habr.com/ru/companies/ozontech/articles/769624/) — and, across a dozen
phrasings, none at all about integrating with Yandex Delivery's Express API. The closest thing is [a tariff-optimisation case study from
GRI](https://habr.com/ru/companies/gri/articles/924986/), which is about economics rather than the
contract.

There was no document to derive anything from. So I wrote one: 2,028 lines of OpenAPI covering the six
operations of the ordering lifecycle — `offers/calculate`, `claims/create`, `claims/info`,
`claims/accept`, `claims/cancel-info`, `claims/cancel` — transcribed by hand from Yandex's HTML help
pages and cross-checked against a Postman collection of requests that were known to work.

Writing a specification for an API you do not own is a strange exercise. Every schema is a hypothesis.
Nothing validates it except a real request, so the client's live test suite became the only thing
standing between a hypothesis and a wrong belief. One afternoon of live calls against a **test account**
in August 2026 found an undocumented status code, five undocumented response fields, a misspelled
field name, a route point the API invents on its own, and two mutually inconsistent vocabularies of
error codes in a single field.

Two honest caveats before the substance, because they bound everything that follows.

**Everything on the wire here was observed on a test account, and it is dated.** Production may differ.
For most APIs I would treat that as pedantry; for this one it is not, and by the end of this article
you will see why I do not assume two environments of the same product agree.

**Everything about the documentation was verified on 24 August 2026.** That date matters more than it
usually would, because — as the next section but one explains — the documentation carries no
"last updated" stamp and its changelog stopped three years ago. If you read this later and something
does not match, that is the point rather than an error in the text.

## What changed: the reference is now generated from a spec

Sometime between July 2025 and today, Yandex's developer documentation grew a set of pages under
`/api/express/openapi/` — one per method, rendered by [Diplodoc](https://habr.com/ru/companies/yandex/articles/765768/),
Yandex's own open-source documentation toolkit. They are unmistakably generated from an OpenAPI
document: they show typed properties, `Pattern` assertions, `Enum` value lists, request and response
bodies, per-operation status codes and named entity definitions with anchors.

This is a genuine improvement, and I want to say so plainly before I start listing what is wrong with
it. The HTML pages I transcribed in 2025 had none of that structure. Today's reference documents the
route point the API adds by itself, gives money fields their regular expression, and enumerates claim
statuses. Somebody did real work here.

What it does not do is hand you the document. There is no download link on any of those pages — I
checked programmatically, collecting every `<a href>` on the `claims/create` page and filtering for
anything matching `.json`, `.yaml`, `download` or `spec`. Nothing. No "specification" or "download"
wording anywhere in the page text either. The pages do not even return a `Last-Modified` header;
they are served `cache-control: no-store`.

So the contract exists inside Yandex — you can see its shadow on every page — and what is published is
the shadow.

**What I would have done.** Publish the file. It already exists; serving it is a link, not a project.
The moment it is downloadable, everything I had to hand-build becomes free for every integrator:
a generated client in any language, a [Spectral](https://stoplight.io/open-source/spectral) lint run,
a [Prism](https://stoplight.io/open-source/prism) mock server so client teams can start before
credentials arrive, contract tests that catch drift, and an `oasdiff` job that tells *you*, the vendor,
when a change you are about to ship breaks somebody. A rendered reference helps a human read. A
document helps everyone else's machines, and machines are most of the audience.

## The changelog stopped in 2023

The "История изменений" (release notes) page is a table with three rows. All three are dated
**17 July 2023**: the addition of `offers/calculate`, the `offer_payload` parameter it forced into
`claims/create`, and an `expected_visit_interval` field in the `claims/info` response.

Meanwhile the documentation index lists methods that appear nowhere in that table: editing a claim
before and after confirmation, skipping a route point, claim search, a change journal, a confirmation
code, proof of delivery, marking a point ready — and three methods for handing a parcel over **to a
robot**. The API has visibly grown for three years and the changelog has not noticed.

Combine that with the missing `Last-Modified` and you get the practical consequence: there is no way to
answer the question every integrator eventually asks, which is *"did this change, or did I always read
it wrong?"* When I found an undocumented `409` in August 2026 and patched my own document to match, the
reference now documents that same `409`. Did Yandex add it before or after I hit it? Unanswerable.

This is not an isolated habit at the vendor: [a dated audit of Yandex 360's audit log](https://habr.com/ru/articles/1072594/),
published on Habr three days ago, is the same exercise against a different product, with the same
finding — the documentation does not contain the thing an integrator needs.

**What I would have done.** Version the document and let the changelog be generated from diffs between
versions rather than written by hand — a hand-maintained changelog is exactly the kind of documentation
that goes stale first, which is [the argument the MTS team makes](https://habr.com/ru/companies/ru_mts/articles/1003562/)
about hand-written API docs generally. Failing that, stamp each page with the date it was generated.
It costs one template change and it converts an unanswerable question into a lookup.

## `droppof_point`: a typo that shipped, and had to stay

Every cargo item in a claim response carries two fields with the same meaning:

```json
"dropoff_point":  26389626087876,
"droppof_point":  26389626087876
```

The second one is a misspelling of the first. It reached production, integrators wrote code against it,
and from that moment removing it would have broken them — so it is sent forever. Today's reference
documents it, and the entire description of the field reads:

> deprecated, use dropoff_point

I want to be careful here, because this is the *most sympathetic* defect in this article. Every API of
any age has one. The interesting part is not that somebody mistyped a word; it is what the
documentation does with it afterwards, and there the handling is worse than the typo:

- The deprecation lives in prose. OpenAPI has a `deprecated: true` flag that generators, linters and
  diff tools understand, and the renderer plainly supports it: every page ships an abbreviation
  definition for a `Deprecated` badge ("No longer supported, please use an alternative and newer
  version"). Across the six operation pages I checked, **nothing carries that badge** — the only
  deprecation in the whole reference is this lowercase sentence inside a description. A machine
  reading this document cannot tell the field is deprecated, and a machine is what reads documents.
- There is no date and no policy. Deprecated since when? Removed when? "Deprecated forever" is a
  legitimate answer — it is probably the true one — but it should be written down.
- The field is still in the **request** examples. In the `claims/create` sample body, which appears four
  times on the page, you will find:

  ```json
  "pickup_point": 1,
  "dropoff_point": 2,
  "droppof_point": 0,
  ```

  Two fields that mean the same thing, in an example a newcomer will copy, carrying **different
  values**. The example teaches the mistake it is documenting.

**What I would have done.** Keep the field — that part is right, and breaking integrators to fix a
spelling would be vanity. Then set `deprecated: true` in the document so tooling can see it, put the
date and the intent in the description ("kept for backward compatibility, will not be removed, always
mirrors `dropoff_point`"), and delete it from every example.

## Two error vocabularies, and they disagree with each other

Every error in this API comes back in the same envelope:

```json
{"code": "...", "message": "..."}
```

That is a good decision. What goes into `code` is not one vocabulary but three.

**First**, symbolic domain codes: `not_found`, `state_mismatch`, `estimating.too_many_loaders`. These are
stable and worth branching on.

**Second**, the HTTP status as a string, with a message that leaks the parser's internal state. Both of
these came back from real calls:

```json
{"code":"400","message":"Parse error at pos 763, path 'route_points': incorrect size, must be 2 (limit) <= 1 (value)"}
{"code":"400","message":"Value of query 'claim_id': incorrect size, must be 32 (limit) <= 3 (value)"}
```

`"code": "400"` tells a caller nothing the HTTP status line did not already say, and `pos 763` is an
offset into a buffer the caller cannot see.

**Third — and this is the one that surprised me — the documentation contains two different names for
the same failure.** The error reference lists:

| Status | Code |
|---|---|
| 400 | `too_many_loaders` — "the maximum number of loaders is 2" |

The `offers/calculate` page, in the same documentation set, on the same day, documents a `409` whose
`code` is a closed list of 23 values, including:

```
estimating.too_many_loaders
```

So: same refusal, two codes, two status codes, two pages. The wire settles it — on 12 August 2026 I got
`409 {"code":"estimating.too_many_loaders", "message":"В выбранном кузове не получится заказать столько
грузчиков"}` — but a reader has no way to know which page to believe, and the one that is wrong is the
one titled "Error reference".

That reference, incidentally, is eleven rows long for an API of thirty-odd methods, and it mixes
registers within its own table: `unauthorized` and `inappropriate_status` are machine codes,
`Internal server error` and `Parse error` are English sentences, all four typeset identically as code.

**What I would have done.** One vocabulary, and it is the symbolic one. Never put the HTTP status in
the body — it is already in the status line. Keep `message` human and unstable, add a structured
`details` object for the machine-readable specifics (which field, which limit) instead of formatting
them into prose, and never let a parser offset out of the building. Then declare the codes per operation
in the document, as the `offers/calculate` page already does, and delete the free-floating error page —
if it disagrees with the operations, it is not a reference, it is a second source of truth. This is the
same argument [Konstantin Moseenko makes for informative API errors](https://habr.com/ru/companies/otus/articles/1018008/):
an error is a value your caller programs against, not a log line.

## Is it three days or five?

The error reference says:

> `delay_too_long` — the maximum number of days for the `due` field is 3

The `Due` entity on the `claims/create` page says the arrival time can be deferred

> by 30–240 minutes for the `express` tariff; **by five days** for the `cargo` tariff

Both pages are current as of 24 August 2026. I have not tested which one the server enforces, and
that is deliberate: the point is not which number is right, it is that a careful reader who checks two
pages ends up less certain than one who checks one.

## Which statuses can an operation return? Depends who you ask

Here is my hand-written document against Yandex's reference, operation by operation:

| Operation | My document | Yandex's reference |
|---|---|---|
| `offers/calculate` | 200 400 401 409 429 500 | 200 400 409 429 |
| `claims/create` | 200 400 401 429 500 | 200 400 **403** 429 |
| `claims/info` | 200 400 401 404 429 500 | 200 400 404 429 |
| `claims/accept` | 200 400 401 409 429 500 | 200 404 409 429 |
| `claims/cancel-info` | 200 400 401 404 409 429 500 | 200 400 404 |
| `claims/cancel` | 200 400 401 409 429 500 | 200 400 404 409 |

Two things stand out, and one of them is my fault.

**`401` is not declared on a single operation.** Every one of them is authenticated; the error reference
documents `401 unauthorized`; and the very first live call I ever made against this API returned
`401 {"code":"unauthorized","message":"Access denied"}` because the token had expired. A generated client
built strictly from the published reference treats the most common failure in any integration as an
undocumented response. The same is true of `500`.

**`403` on `claims/create` is in their document and missing from mine.** That is a hole in my
specification, found by writing this article, and it is exactly the failure mode of owning a document
nobody else validates.

**What I would have done.** Declare the shared failures once in `components/responses` and `$ref` them
from every operation — three lines each, and then a generated client has a case for the thing that
happens most often. My own document does this; it is not a hard pattern, it is just one nobody
remembers to apply to authentication because authentication feels like infrastructure rather than API.

## Timestamps: valid, and not consistent

The document declares timestamp fields as `string<date-time>`, which means RFC 3339. The examples in
the documentation itself come in two shapes: `2020-01-01T07:00:00+00:00` and
`2023-07-17T08:02:26.607358+00:00`.

The wire is more varied than that. One `offers/calculate` response, captured on 12 August 2026, carried
**21 timestamps with six-digit fractional seconds and 4 with none** — including a single interval object
whose `from` had a fraction and whose `to` did not:

```json
"pickup_interval": {
  "from": "2026-08-12T17:12:40.051944+00:00",
  "to":   "2026-08-12T18:15:00+00:00"
}
```

Same object, same field type, same response, same second of wall-clock time.

Here I have to be fair, because the obvious accusation is wrong: **both forms are valid RFC 3339.**
Fractional seconds are optional in the standard, and a server that emits them sometimes is not
violating anything. The cost is not standards compliance, it is that the variance is invisible in the
schema. A code generator installs one date decoder for every `date-time` field in the API; that decoder
must now be liberal enough for both shapes, and nothing in the document tells you so. You find out from
a failed decode, in production, on a field you were not thinking about.

And there is a sharper version of the problem on the way out. Reading, you can afford to accept
anything. Writing, you have to pick one shape, and the document gives you no basis for picking. I kept
whatever shape the client that had been talking to the live API already sent, and wrote down the
question rather than "fixing" it toward symmetry — because the feedback for guessing wrong here is not
a failed test, it is a delivery that does not happen.

**What I would have done.** Pick one representation, state it in the field description with an example,
and emit it everywhere. If the backend genuinely cannot promise that — different services, different
serializers, a legacy path — then say *that* in the description. "Fractional seconds may or may not be
present" is a poor guarantee and an excellent piece of documentation.

## Money: strings, and a pattern that permits nonsense

Prices cross the wire as decimal strings, and the reference pins them with a regular expression:

```
^-?[0-9]{1,14}(\.[0-9]{0,4})?$
```

Two observations. Money in this API is charged in roubles and kopecks — two decimal places — but the
pattern allows four. And because the fractional group is `{0,4}` rather than `{1,4}`, the pattern
accepts a bare trailing dot: `"1449."` is a valid amount according to the vendor's own document.

On the wire, in one response object, I saw `"total_price":"1449"` alongside
`"total_price_with_vat":"1767.78"`. A reader that assumed two decimal places would have been wrong about
the first.

Strings for money are, to be clear, the right call — floating point in JSON is how you get a price of
`807.6000000000001`. The problem is a pattern loose enough to describe values the system cannot mean.

**What I would have done.** Either integer minor units (`144900` kopecks, no ambiguity, no parser) or a
decimal string with a fixed scale — `^-?\d{1,14}\.\d{2}$` — and the scale stated in words. If four
decimals are genuinely possible somewhere, say where. A pattern is a promise; a loose one promises
things you will have to support later.

## The server invents a route point

Create a claim with two route points — a pickup and a destination — and the response contains three.
Yandex appends a `return` point of its own:

```
point id=26389626087875 type=source      visit=pending
point id=26389626087876 type=destination visit=pending
point id=26389626087877 type=return      visit=pending
```

Credit where it is due: **today's reference documents this**, and the description is good — the return
point "is added automatically and by default coincides with the pickup point". In the pages I
transcribed in 2025 it was not there, and finding three points where I sent two is how I learned about
it.

The related behaviour is still worth stating because it catches people. The point identifiers a caller
sends are not echoed back. I numbered my points `1` and `2`; the response numbered them
`26389626087875` and `26389626087876`, and every field that references a point — `items[].pickup_point`,
`items[].dropoff_point` — was renumbered with them. Any client-side logic that derives a new point id as
"the highest one I have seen, plus one" is building on numbers that live exactly as long as the request.

**What I would have done.** Model the request point and the response point as two schemas rather than
one. They genuinely are different types: one carries an identifier the client chose and the server will
discard, the other carries an identifier the server assigned and the client must not invent. Reusing one
schema for both saves a few lines in the document and moves the confusion into every consumer.

## Advice that does not bind

There is an endpoint whose whole purpose is to tell you what cancelling would cost:
`claims/cancel-info`. On a fresh claim it answered `{"cancel_state":"free"}`. Cancelling a moment later
returned:

```json
409 {"code":"state_mismatch","message":"Недопустимое действие над заявкой"}
```

The same claim cancelled successfully a few minutes later. Nothing was wrong with the request; the
claim had been mid-estimation, and the refusal was about a transient state that `cancel-info` had not
mentioned, because `cancel-info` reports price, not permission.

Two practical consequences. A cancellation that fails is not necessarily one that will keep failing, so
cleanup code should re-read the status and retry rather than give up. And an advisory endpoint whose
advice can be contradicted one call later needs to say so.

**What I would have done.** Either give the advisory answer a stated validity — the conditions under
which it holds, the states in which cancellation is refused regardless of price — or make it a dry run
of the real operation, returning exactly what the real call would return minus the effect. The failure
here is not the 409; it is that two endpoints describe the same act and only one of them knows the
answer.

## Constraints that exist only on the server

Ask for a `cargo_loaders` count on the `express` tariff and the API refuses with
`409 estimating.too_many_loaders`. Ask for the same loaders on `cargo` with a body type and it is
accepted. Nothing in the document expresses that dependency, and nothing offline can catch it: a stub
transport accepts whatever you hand it, so a request fixture can be wrong from the day it is written
and every offline test will still pass. Mine was.

This one is only half a criticism. Cross-field constraints are genuinely hard to express in JSON Schema,
and the ones that depend on tariff, region and account state are not expressible at all.

**What I would have done.** Write them down in prose, in the description of the field they constrain —
"not available with `taxi_class: express`" is one sentence and it would have saved me an afternoon. For
the constraints that vary by account, an endpoint that reports what *this* account can order beats any
amount of documentation, and this API is one step away from having it: `offers/calculate` already knows.

## The webhook builds its URL by concatenation

This one is documented, so I am quoting rather than reporting. On status changes, Yandex calls back to
a URL you register, appending the claim id and a timestamp. From the `claims/create` page:

> Important: the parameters are appended to `callback_url` by concatenation, that is, a url of the form
> `https://example.com` will turn into the invalid `https://example.comupdated_ts=...&claim_id=...`

So the documented behaviour is that the vendor will build a malformed URL unless your callback happens
to end in `?` or `&`. Writing it down is better than not writing it down. It is not better than parsing
the URL and merging the query, which is a library call in every language this service is written in.

**What I would have done.** Merge the query properly — or, better, put the payload in the body of the
POST request, where a status notification belongs, rather than in a query string that ends up in access
logs. Then delete the paragraph.

## Access, tokens, and the sandbox that is not one

To start, you get a login and password "from your Yandex Delivery manager", sign into the dashboard and
press a button to obtain a token. The quickstart says, twice, that in case of problems you should
contact your manager.

The token, per the same page, "is valid for an unlimited time". There is one host in the entire
documentation — production. There is no sandbox. There is a test *cabinet*, which you can infer only
from an entry in the error reference: `required_tariffs_disabled_for_user` — "the test cabinet has
expired". So the test environment is a time-limited account on the production system, and when it
lapses you find out through an error code.

The page titled "Technical integration details" is, in full, one sentence about using TLS 1.2 and PCI
DSS v4 cipher suites.

I am not going to pretend this is unusual for a Russian B2B logistics API — it is not — but it has a
cost, and Vladimir Sinyavsky's ["all tests green, payments stuck"](https://habr.com/ru/articles/1050584/)
piece names it precisely: without a sandbox that behaves like production, your test suite measures your
own assumptions. Everything I know about this API's behaviour is scoped to one test account, and I say
so every time I say anything about it, which is not a rhetorical tic — it is the actual epistemic
situation.

**What I would have done.** Self-service credentials, tokens with a lifetime and a rotation story
(an unlimited bearer token is a credential with no answer to "it leaked"), and a sandbox with a written
statement of how it differs from production. The statement matters more than the sandbox: "identical
except that no courier is dispatched and no money moves" is a sentence that tells an integrator exactly
how far to trust their green tests.

## Now my own mistakes, because the document was mine

It would be cheap to write all of this as though the client had been correct throughout. It was not,
and the most instructive failure of the whole project was mine.

**I modelled an advisory field as a closed enum, and lost entire responses.** Claim responses carry a
`warnings` array, each with a `source`. I enumerated the values I had seen. On 17 August 2026 a live
`claims/info` returned `"source": "taxi_requirements"` — a value not in my enum — and decoding threw.
Not the warning: **the whole claim response**. A piece of advisory text took the payload down with it.

It was worse than a failed request, because a polling loop read `status` through that same call. Claims
that had in fact progressed to `ready_for_approval` looked frozen at `new` for an hour, and I spent that
hour convinced the API was not estimating.

Two things make this squarely my fault. Yandex's own document types that field as **`Type: string`** —
an open string, with two known values listed in prose. I made it stricter than the vendor claimed it
was. And the third value is named after a section of the request body (`taxi_requirements` is a field in
`claims/create`), which means the vocabulary grows with the request schema and was never closeable in
the first place.

The rule I took away, and it is the one I would give anyone generating a client from a document they
wrote themselves: **a closed enum is a decode-time assertion that takes the whole payload with it when
it fails.** Model one where a caller must branch exhaustively and a new value is a real decision —
tariff class, cancellation type. Anywhere the field is advisory, descriptive or diagnostic, use a
string. Be liberal in what you accept.

Two smaller ones, in the same spirit. My `ClaimStatus` enum has 27 values against the reference's 26;
the extra is `pay_waiting`, which I cannot now source. My `TaxiClass` carries `sdd_long` with a comment
next to it saying it should not be there. And an early draft of the specification — written fast, from
the HTML pages — declared a second server, `https://b2b.taxi.tst.yandex.net`, labelled `Sandbox`. No
such host appears in the documentation or in the collection of requests that actually worked. When you
write a document for an API you do not own, invention is not a hypothetical risk.

## What this API gets right

**Idempotency works exactly as documented.** Re-posting `claims/create` with the same `request_id`
returns the same claim, in whatever state it has reached, rather than creating a second one. That is the
recovery mechanism the whole mutating test suite relies on, and it is the one promise in the reference
that held without qualification. It is also, pleasingly, the subject of the best Russian-language
article on the topic, ["Intern Vasya and his stories about API idempotency"](https://habr.com/ru/companies/yandex/articles/442762/) —
published on Yandex's own blog. The institutional knowledge is in the building.

**The reference is real progress.** Compared with what I transcribed in 2025, today's pages carry
patterns, enums, entity definitions and per-operation status codes. The `return` point is documented.
Somebody made this better.

**The engineering behind the service is strong**, and Yandex writes about it well — their piece on
[how couriers are matched and assigned for same-day delivery](https://habr.com/ru/companies/yandex/articles/887484/)
is a good read. That is precisely why the contract at the edge is worth complaining about: the hard part
is done, and the part that is left is a YAML file and a changelog.

## How I would have designed it

None of this is original — the list overlaps with [designing quality APIs](https://habr.com/ru/companies/ruvds/articles/942916/)
and with [ten API mistakes](https://habr.com/ru/articles/1013924/). Which is the uncomfortable part:
nearly every item is violated by a live API from a major company.

Nothing in this list is specific to delivery. It is what I would want from any vendor API I have to
integrate against, ordered by what it costs the vendor to do.

1. **Publish the machine-readable document.** You have it. A link is not a project, and it converts every
   integrator's private transcription effort into zero.
2. **Date everything.** A generation stamp on each page, a version on the document, a changelog produced
   from diffs. "Did this change?" should be a lookup, not an archaeology project.
3. **One error vocabulary.** Symbolic codes, declared per operation, machine-readable specifics in a
   structured field, no HTTP status inside the body, no parser offsets in the message.
4. **One representation per concept.** One timestamp shape, one money scale, and if you cannot promise
   it, document the variance instead of leaving it to be discovered.
5. **Patterns that describe what you mean.** `{0,4}` fractional digits admits `"1449."`; you did not mean
   that.
6. **Deprecate in the document, not in prose.** Set the flag, add the date, state the policy, and take
   the field out of the examples.
7. **Separate request and response types** wherever the server assigns identifiers or adds entities.
8. **Say what an advisory endpoint does not guarantee.** Preconditions and validity, or make it a dry run.
9. **Write down cross-field constraints in prose**, since the schema cannot hold them.
10. **Give integrators a sandbox with a stated difference from production** — and self-service,
    rotatable credentials.

## Bottom line

I built the client, it works, and the six operations of the ordering lifecycle have all been exercised
against the real API. None of what is above stopped the project; all of it made it slower, and most of
it was discovered in the one way that costs the most, which is by calling the thing and reading the
bytes.

The thread running through every item is the same one from my previous article: a contract is only worth
what it is machine-checkable. Yandex has the document — every rendered page proves it. Publishing it
would cost a link and would retire, at a stroke, a whole category of work that every one of their
integrators is currently doing separately, by hand, and getting slightly wrong in slightly different
ways. I have the 2,028 lines to prove it.

---

*Documentation claims verified 24 August 2026. Wire observations were made against a Yandex Delivery
**test** account in August 2026 and are dated where they appear; production behaviour may differ.*
