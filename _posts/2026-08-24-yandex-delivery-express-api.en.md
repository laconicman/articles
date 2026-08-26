---
layout: post
title: "The Ghost of a Specification — A Close Read of Yandex Delivery's Express API, and How I'd Have Designed It"
date: 2026-08-24 09:00:00 +0000
tags: [OpenAPI, API design, Yandex]
lang: en
permalink: /2026/08/24/yandex-delivery-express-api/
---

*[Читать по-русски →]({{ '/2026/08/24/yandex-delivery-express-api/' | relative_url }})*

---

# The ghost of a specification

> **In short.** Yandex Delivery's Express API looks as though it has an OpenAPI document: the
> reference on the site looks exactly like documentation rendered from one. You cannot download it,
> and when my company asked officially, the answer was that no specification exists. So I wrote it
> myself — 2,028 lines of YAML transcribed from HTML pages. Below is what that work and a day of live
> calls turned up: two incompatible vocabularies of error codes, two timestamp formats in a single
> response, a misspelled field name, and a reference that contradicts itself. Each item comes with
> what I would have done instead. Some of the failures are mine.

## Where this comes from

I write client software for Apple platforms. In 2025 I needed to call Yandex Delivery's Express API —
the B2B Cargo service which, once you strip away everything that sounds like a pitch deck, means "a
courier picks up your box and takes it to an address."

Let me be clear about one thing up front: nobody forced me to generate a client from a contract. I
could have handed the documentation to a language model and got a pile of `URLSession` or Alamofire
code out of it, and it would have worked. I wanted to do it properly — no hand-rolled wheels, types
that catch mistakes at compile time, and no networking layer to maintain by hand afterwards. That is
the approach I argued for at length in [an earlier article]({{ '/en/2025/06/03/openapi-source-of-truth/' | relative_url }}).

And this is where the story starts. The reference on the site looks **exactly like documentation
built from an OpenAPI document**: typed properties, regular expressions, enumerations, per-operation
status codes. Which means the work is already done, the file exists, and the only thing missing is a
link to it. There is no link. My company sent an official enquiry and got an official answer: **there
is no specification.** That ended the search — where you would normally spend a week wondering whether
you simply failed to find it, one support reply settles the matter.

So I wrote the document myself: 2,028 lines of OpenAPI covering the six operations of the ordering
lifecycle — `offers/calculate`, `claims/create`, `claims/info`, `claims/accept`, `claims/cancel-info`,
`claims/cancel` — transcribed by hand from the help pages and cross-checked against a Postman
collection of requests known to work.

Writing a specification for an API you do not own is a peculiar exercise: every schema in it is a
hypothesis, and only a real request can confirm one. A single day of live calls against a **test
account** in August 2026 produced an undocumented status code, five undocumented response fields, a
misspelled field name, a route point the server adds by itself, and two incompatible vocabularies of
error codes in one field.

Everything below about the documentation was verified on **24 August 2026**; everything about real
responses was observed on a test account and is dated where it appears. The dates are not pedantry:
the pages carry no modification stamp and the changelog stopped three years ago, so "verified on such
a date" is the only available form of precision.

## There is a reference; there is no document

The pages under `/api/express/openapi/` — one per method — are built with
[Diplodoc](https://habr.com/ru/companies/yandex/articles/765768/), Yandex's own open-source
documentation toolkit. They carry typed properties, `Pattern` assertions, `Enum` lists, request and
response bodies, per-operation status codes and named entity definitions with anchors.

This is a real improvement, and I want to say so before I start listing complaints: the pages I
transcribed in 2025 had none of that. Today's reference documents the route point the API adds by
itself, gives money fields their regular expression, and enumerates claim statuses.

What it does not do is hand you the document. There is no download link on any page — I collected
every `<a href>` on the `claims/create` page and filtered for `.json`, `.yaml`, `download` and `spec`:
nothing. No "specification" or "download" wording in the page text either. The pages do not even
return a `Last-Modified` header.

**What I would have done.** Publish the file. It exists — there would be nothing to render these pages
from otherwise — and serving it is a link, not a project. The moment it is downloadable, everything I
had to build by hand becomes free for every integrator: a client in any language, a
[Spectral](https://stoplight.io/open-source/spectral) run as an executable style guide, a
[Prism](https://stoplight.io/open-source/prism) mock server so client teams can start before
credentials arrive, contract tests against drift, and an `oasdiff` job that tells the vendor what it
is about to break. A rendered reference helps a human read. The document helps everyone else's
machines, and machines are most of the audience.

## The changelog stopped in 2023

The release-notes page is a table with three rows, all dated **17 July 2023**.

Meanwhile the documentation index lists methods that appear nowhere in that table: editing a claim
before and after confirmation, skipping a route point, claim search, a change journal, a confirmation
code, proof of delivery, marking a point ready — and three methods for handing a parcel over **to a
robot**. The API has grown visibly for three years; the changelog has not noticed.

The practical consequence is that you cannot answer the question every integrator eventually asks:
*"did this change, or did I always read it wrong?"* When I found an undocumented `409` in August 2026
and patched my own document, it turned out that today's reference documents the same `409`. Whether it
appeared there before or after I hit it is unknowable.

This is not an isolated habit at the vendor: [a dated audit of Yandex 360's audit
log](https://habr.com/ru/articles/1072594/) is the same exercise against a different product, with the
same finding.

**What I would have done.** Version the document and generate the changelog from diffs between
versions — a hand-written one goes stale first, which is [exactly the argument the MTS team
makes](https://habr.com/ru/companies/ru_mts/articles/1003562/). Failing that, stamp each page with its
build date.

## `droppof_point`: a typo that shipped

Every cargo item in a response carries two fields with the same meaning:

```json
"dropoff_point":  26389626087876,
"droppof_point":  26389626087876
```

The second is a misspelling of the first. It reached production, integrators wrote code against it,
and removing it became impossible. There is no per-endpoint versioning here either: the new version
was merged into the old one, there is no `v3` and not even a compatibility flag — so there is no place
where the typo could have been dropped.

Every API older than a couple of years has one of these, and on its own this is the most sympathetic
item in the article. What is worse than the typo is what the documentation does with it:

- **The deprecation lives in prose.** The entire description of the field reads "deprecated, use
  dropoff_point". OpenAPI has a `deprecated: true` flag that generators, linters and diff tools
  understand. The renderer supports it — every page defines a `Deprecated` badge — yet across the six
  method pages no field carries one.
- **The field is still in the request examples**, with a different value from the correct one:

  ```json
  "pickup_point": 1,
  "dropoff_point": 2,
  "droppof_point": 0,
  ```

  The example teaches the mistake it documents.

**What I would have done.** Keep the field — breaking integrators over spelling would be vanity. Set
`deprecated: true`, write in the description that it will not be removed and always mirrors
`dropoff_point`, and take it out of the examples.

## Two error vocabularies, and they disagree with each other

Every error arrives in the same structure: `{"code": "...", "message": "..."}`. That is a good
decision. What is not good is that `code` holds three vocabularies rather than one.

**First**, symbolic domain codes: `not_found`, `state_mismatch`, `estimating.too_many_loaders`. Stable,
and worth branching on.

**Second**, the HTTP status as a string, with a message that leaks the parser's internals:

```json
{"code":"400","message":"Parse error at pos 763, path 'route_points': incorrect size, must be 2 (limit) <= 1 (value)"}
{"code":"400","message":"Value of query 'claim_id': incorrect size, must be 32 (limit) <= 3 (value)"}
```

`"code": "400"` says nothing the status line did not, and `pos 763` is an offset into a buffer the
caller cannot see.

**Third: the documentation gives the same error two different names.** The error reference says "too
many loaders" is `too_many_loaders` with status **400**. The `offers/calculate` page, in the same
documentation set on the same day, documents a **409** whose `code` is a closed list of 23 values,
among them `estimating.too_many_loaders`. The real response settles it: on 12 August 2026 I got
`409 {"code":"estimating.too_many_loaders", ...}`.

A reader has no way to know which page to believe, and the one that is wrong is the one titled "Error
reference". That reference is eleven rows long for an API of thirty-odd methods, and it mixes registers
inside its own table: `unauthorized` and `inappropriate_status` are machine codes, `Internal server
error` and `Parse error` are English sentences, all typeset identically.

**What I would have done.** One vocabulary, the symbolic one. No HTTP status inside the body.
`message` stays human and unstable; the machine-readable specifics — which field, which limit — move
into a structured `details` object, and parser offsets never leave the building. Codes get declared per
operation in the document, as the `offers/calculate` page already does, and the standalone error page
goes away: if it disagrees with the operations, it is not a reference, it is a second source of truth.
This is the same argument [Konstantin Moseenko makes for informative API
errors](https://habr.com/ru/companies/otus/articles/1018008/) — an error is a value your caller
programs against, not a log line.

## Is it three days or five?

The error reference: "`delay_too_long` — the maximum number of days for the `due` field is 3." The
`Due` entity on the `claims/create` page: "by 30–240 minutes for the `express` tariff; **by five days**
for the `cargo` tariff." Both pages are current as of 24 August 2026.

I did not test which number the server enforces, deliberately: the point is not which is right, but
that a careful reader who checks two pages ends up less certain than one who checks a single page.

## Which statuses can an operation return? Depends who you ask

My hand-written document against Yandex's reference:

| Operation | My document | Yandex's reference |
|---|---|---|
| `offers/calculate` | 200 400 401 409 429 500 | 200 400 409 429 |
| `claims/create` | 200 400 401 429 500 | 200 400 **403** 429 |
| `claims/info` | 200 400 401 404 429 500 | 200 400 404 429 |
| `claims/accept` | 200 400 401 409 429 500 | 200 404 409 429 |
| `claims/cancel-info` | 200 400 401 404 409 429 500 | 200 400 404 |
| `claims/cancel` | 200 400 401 409 429 500 | 200 400 404 409 |

**`401` is not declared on a single operation.** All of them require authentication, the error
reference knows about `401`, and the very first live call I made returned
`401 {"code":"unauthorized","message":"Access denied"}` because the token had expired. A client
generated strictly from the published reference meets the most common failure in any integration as an
undocumented response. The same goes for `500`.

**`403` on `claims/create` is in their document and missing from mine.** Either a hole in my
specification or drift in their documentation — whether the code appeared after I transcribed the page
or I simply missed it, there is no way to tell, for exactly the reason in the previous section.

**What I would have done.** Declare the shared failures once in `components/responses` and `$ref` them
from every operation — three lines each, and a generated client gains a case for the thing that happens
most often.

## Timestamps: formally valid, practically unbearable

Timestamp fields are declared `string<date-time>`. The examples in the documentation itself come in two
shapes: `2020-01-01T07:00:00+00:00` and `2023-07-17T08:02:26.607358+00:00`.

Real responses show the same spread. One `offers/calculate` response captured on 12 August 2026 carried
**21 timestamps with six-digit fractional seconds and 4 with none** — including an interval whose
`from` had a fraction and whose `to` did not:

```json
"pickup_interval": {
  "from": "2026-08-12T17:12:40.051944+00:00",
  "to":   "2026-08-12T18:15:00+00:00"
}
```

One object, one field by meaning, one response.

Formally both forms are allowed: RFC 3339 permits a fractional part and does not require it. But
"allowed" and "works" are different things, and here is what Foundation's standard decoders do with
these exact strings (Swift 6.3.3, macOS 26.5):

| Input | `JSONDecoder.iso8601` | `ISO8601DateFormatter` | `…+.withFractionalSeconds` |
|---|---|---|---|
| `…T17:12:40.051944+00:00` | ok | **FAIL** | ok |
| `…T18:15:00+00:00` | ok | ok | **FAIL** |

`ISO8601DateFormatter` — the platform's own tool — **cannot be configured to accept both**: turn
fractional seconds on and it fails on the value without them, turn them off and it fails on the value
with them. Both values arrive in the same object. You are left writing your own transcoder that tries
each shape in turn, or catching the failure and retrying with the other format.

One more detail that explains why this trips up more than just Apple: six digits are microseconds, and
the canonical text representation in ISO 8601 stops at milliseconds. Formally there is nothing to
object to; practically you have stepped outside what other people's libraries are obliged to
understand.

Writing is sharper still: reading, you can accept anything; writing, you must pick one shape, and the
document gives you no basis for picking. I kept the shape the previously working client already sent
and wrote the question down rather than "correcting" it toward symmetry — the feedback for guessing
wrong here is not a failed test but a delivery that does not happen.

**What I would have done.** One format, pinned in the field description with an example, identical in
both directions. If the backend honestly cannot promise that, document *that*: "the fractional part may
or may not be present" is a poor guarantee and excellent documentation.

## Money as strings

Prices travel as decimal strings, and the reference pins them with a regular expression:

```
^-?[0-9]{1,14}(\.[0-9]{0,4})?$
```

Strings for money are an acceptable, explicable choice: JSON has no decimal type. Plenty of APIs use
`double` in this role and the industry has long since learned not to trip over rounding, so this is a
"debatable but fine" decision.

The argument is not about strings, it is about the pattern. Money here is roubles and kopecks — two
digits — and the pattern allows four. And because the fractional group is `{0,4}` rather than `{1,4}`,
it accepts a bare trailing dot: `"1449."` is a valid amount according to the vendor's own document. In
a real response, one object carried `"total_price":"1449"` next to `"total_price_with_vat":"1767.78"`.

**What I would have done.** Either integer minor units (`144900` kopecks — no ambiguity and no parser)
or a decimal string with a fixed scale, `^-?\d{1,14}\.\d{2}$`, with the scale stated in words. A
pattern is a promise, and a loose one promises what you will have to support later.

## The server invents a route point

Create a claim with two points — pickup and destination — and the response has three: Yandex adds its
own `return` point. This is in the reference now, and the description is good: the return point "is
added automatically and by default coincides with the pickup point". The pages I transcribed in 2025
did not mention it, and I learned about the third point from a response.

The adjacent behaviour is worth stating because people trip on it. The point identifiers the client
sends are not echoed back: I numbered my points `1` and `2`, the response numbered them
`26389626087875` and `26389626087876`, and every referencing field was renumbered with them —
`items[].pickup_point`, `items[].dropoff_point`.

So why send them at all? Because inside the request they are the join key: an item says "collect me at
point 1, deliver me to point 2", and there is no other way to express that — `point_id` is documented
as required. What is awkward is that in the response the same field means something else: the
identifier the server assigned. One name, two things, and a client that misses the difference builds
logic on numbers that live until the end of the request.

**What I would have done.** Describe the request point and the response point as two schemas. They
really are different types: in one the identifier was chosen by the client and will be discarded, in
the other it was assigned by the server and must not be invented. One schema for both saves a few lines
in the document and moves the confusion into every consumer.

## Advice that does not bind

There is a method whose whole job is to say what cancelling would cost: `claims/cancel-info`. On a
fresh claim it answered `{"cancel_state":"free"}`. Cancelling a minute later returned
`409 {"code":"state_mismatch"}`. The same claim cancelled without complaint a few minutes after that:
it had been mid-estimation, and the refusal was about a transient state `cancel-info` said nothing
about, because it reports price, not permission.

Two consequences. A cancellation that fails is not necessarily one that will keep failing, so cleanup
code should re-read the status and retry. And a method whose advice can be contradicted one call later
needs to say so.

**What I would have done.** Either give the advice conditions and a validity window — which states
refuse cancellation regardless of price — or make it a dry run of the real operation: return exactly
what the real call would return, minus the effect.

## Constraints that exist only on the server

Ask for `cargo_loaders` on the `express` tariff and you get `409 estimating.too_many_loaders`. Ask for
the same loaders on `cargo` with a body type and the claim is accepted. No schema expresses that
dependency and no offline test catches it: a stub transport accepts whatever you hand it, so a request
fixture can be wrong from the day it is written while every offline test stays green. Mine was.

I cannot push this one very hard: cross-field constraints are poorly expressed in JSON Schema, and the
ones that depend on tariff, region and account state cannot be expressed at all.

**What I would have done.** Write them in prose, in the description of the field they constrain: "not
available with `taxi_class: express`" is one sentence that would have saved me half a day. For
account-dependent constraints, an endpoint reporting what *this* account can order beats any amount of
documentation — and it is one step away: `offers/calculate` already knows.

## The webhook builds its URL by concatenation

A quote from the `claims/create` page is enough here:

> Important: the parameters are appended to `callback_url` by concatenation, that is, a url of the form
> `https://example.com` will turn into the invalid `https://example.comupdated_ts=...&claim_id=...`

The documented behaviour is that the vendor will build a malformed URL unless your address happens to
end in `?` or `&`. Writing it down beats not writing it down; it does not beat parsing the URL and
merging the query, which is a library call in any language.

**What I would have done.** Merge the query properly — better still, put the payload in the body of the
POST request, where a status notification belongs, rather than in a query string that ends up in access
logs.

## Access, tokens, and the sandbox that is not one

Credentials come through the dashboard: a manager issues a login and password, then there is a button
that produces a token, and anything the dashboard cannot do goes through support. That part works.

What does not work is the token, which per the same page "is valid for an unlimited time". An unlimited
bearer token is a credential with no answer to "what if it leaks?": no lifetime, no rotation, no
scopes.

And there is no sandbox: the documentation has exactly one host, production. A test *cabinet* exists,
but as far as I can tell you can only learn about it from a line in the error reference —
`required_tariffs_disabled_for_user`, "the test cabinet has expired". So the test environment is a
time-limited account on the production system, and you discover its expiry through an error code.

The page titled "Technical integration details" consists, in full, of one sentence about TLS 1.2 and
PCI DSS v4 cipher suites.

For a Russian B2B logistics API this is ordinary, but it has a cost, and Vladimir Sinyavsky names it
precisely in ["all tests green, payments stuck"](https://habr.com/ru/articles/1050584/): without a
sandbox that behaves like production, your test suite measures your own assumptions.

**What I would have done.** Tokens with a lifetime and a rotation story. And a sandbox whose
differences from production are, first, written down and, second, minimal: "identical to production
except that no courier is dispatched and no money moves" tells an integrator exactly how far to trust
their green tests.

## Now my own failure, which is about the same thing

It would be cheap to write all of this as though my client had been right throughout. It was not.

Claim responses carry a `warnings` array, each warning with a `source`. In my specification I
enumerated the values I had seen — I made the enumeration closed. On 17 August 2026 a live
`claims/info` returned `"source": "taxi_requirements"` and decoding threw. Not the warning: **the whole
claim response.** A piece of advisory text took the payload down with it.

It was worse than a failed request, because a polling loop read `status` through the same call, so
claims that had reached `ready_for_approval` looked stuck at `new`, and I spent an hour certain the API
was not estimating.

This is not about typing — an untyped client with a closed set of expected values would have had just
as bad a time, only failing somewhere else. It is that **the specification was wrong.** Yandex's
document types the field as `Type: string` — an open string with two known values listed in prose; the
third is named after a section of the request body (`taxi_requirements` is a field in `claims/create`),
so the vocabulary grows with the request schema and was never closeable. I made it stricter than the
vendor claimed — though the documentation also leaves room for interpretation here, and I interpreted
badly.

The rule I took away: **a closed enumeration is an assertion checked at decode time, and when it fails
it takes the whole response with it.** Enumerate where the caller must handle every case and a new
value is a real decision — tariff class, cancellation type. Where the field is advisory or diagnostic,
use a string.

And this is not a rule about home-made documents. YooKassa publishes a specification — and it is wrong
too. An official document tells you about its provenance, not about its truthfulness.

## What this API gets right

**Idempotency works exactly as documented.** Re-posting `claims/create` with the same `request_id`
returns the same claim in whatever state it has reached rather than creating a second one. The whole
mutating test suite depends on it, and it is the one promise in the reference that held without
qualification. The best Russian-language article on the subject — ["Intern Vasya and his stories about
API idempotency"](https://habr.com/ru/companies/yandex/articles/442762/) — is published on Yandex's own
blog. The knowledge is in the building.

**The reference is real progress.** Today's pages carry patterns, enumerations, entity definitions and
per-operation status codes; the automatically added return point, which you previously could only learn
about from a response, is now described.

**The engineering behind the service is strong**, and Yandex writes about it well: [their piece on how
couriers are found and assigned](https://habr.com/ru/companies/yandex/articles/887484/) is a good read.
Which is exactly why the contract at the edge is worth talking about: the hard part is done, and what
is left is a YAML file and a changelog.

## Four questions I have no answer to

These are not defects — they are decisions whose motivation I do not understand. Each may well have a
story; the documentation does not show it.

**1. Why are coordinates an array?** The type is `number[]`, exactly two elements, and the description
has to explain the order: "longitude, latitude — in exactly that order". What was the third coordinate
going to be? The price of this decision sits nearby, in the error codes of the calculation method:
`estimating.swapped_coordinates`. An object with two named fields would make that code unnecessary —
you cannot confuse `latitude` with `longitude`, but you can certainly confuse `[0]` with `[1]`.

**2. Why that pattern for money?** The string is explicable. Four decimal places for roubles and
kopecks, and an accepted `"1449."`, are not a decision — they are a pattern nobody re-read.

**3. Why `int64` for an identifier that lives until the end of the request?** `point_id` is documented
as "integer point identifier (int64), unique within one claim creation", and in the examples it is `1`
and `2`. Nineteen significant digits for a quantity that in practice does not exceed one hand. *(For
the record: `cargo_loaders` is a plain `integer` in both documents, not an `int64` — I checked, because
I was about to complain about that too.)*

**4. Why two timestamp formats in one response?** If microseconds matter for the start of an interval,
why do they not matter for its end? And if they do not matter, why are they there? One format would
remove the guesswork with formatters; canonical ISO 8601 — with or without a fractional part — would
also remove the questions that standard libraries keep tripping over.

## How I would have designed it

Nothing here is original — the list overlaps with [designing quality
APIs](https://habr.com/ru/companies/ruvds/articles/942916/) and with [ten API
mistakes](https://habr.com/ru/articles/1013924/). Which is the uncomfortable part: nearly every item is
violated by a live API from a major company.

1. **Publish the machine-readable document.** It exists. A link is not a project, and it turns every
   integrator's transcription effort into zero.
2. **Date everything.** A build stamp on the page, a version on the document, a changelog from diffs.
3. **One error vocabulary.** Symbolic codes per operation, machine-readable specifics in a structured
   field, no HTTP status inside the body, no parser offsets in the message.
4. **One representation per concept.** One timestamp format, one money scale; and if you cannot promise
   it, document the variance.
5. **Patterns that describe what you mean.** `{0,4}` fractional digits admits `"1449."`; you did not
   mean that.
6. **Deprecate in the document, not in prose.** The flag, the date, the policy — and out of the
   examples.
7. **Separate request and response types** wherever the server assigns identifiers or adds entities.
8. **Say what an advisory method does not guarantee** — conditions and validity, or make it a dry run.
9. **Write cross-field constraints in prose**, since the schema cannot hold them.
10. **Provide a sandbox** whose differences from production are documented and minimal, and tokens that
    rotate.

## Bottom line

The client is built, it works, and all six operations have been exercised against the real API. None of
the above stopped the project; all of it slowed the project down, and most of it was discovered the
most expensive way there is — by calling the thing and reading the response.

The thread running through every item is the one from my previous article: a contract is worth exactly
as much as it is machine-checkable. Yandex has the document — every rendered page proves it. Publishing
it costs a link, and it would retire at a stroke a whole category of work that every one of their
integrators is currently doing separately, by hand, and getting slightly wrong in slightly different
ways. I have 2,028 lines to prove it.

---

*Documentation claims verified 24 August 2026. Observations of real responses were made against a
Yandex Delivery **test** account in August 2026 and are dated where they appear; production behaviour
may differ.*
