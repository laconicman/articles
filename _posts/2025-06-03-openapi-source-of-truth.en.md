---
layout: post
title: "Wiki Lies, Prod is Silent — Why OpenAPI Should Be the Single Source of Truth for Your API"
date: 2025-06-03 18:00:00 +0000
tags: [OpenAPI]
lang: en
permalink: /2025/06/03/openapi-source-of-truth/
---

*<a {% static_href %}href="{{ site.baseurl }}/2025/06/03/openapi-source-of-truth/"{% endstatic_href %}>Читать оригинал на русском →</a>*

---

# Wiki lies, prod is silent: why OpenAPI should be the single source of truth for your API

> **In short.** Some teams still keep the "truth" about their API in three incompatible places: in a
> backend developer's head, on a Confluence page that went stale last spring, and in the actual JSON
> that arrives from production. Those three sources drift apart constantly, and everyone pays for it —
> client developers most of all. OpenAPI is a way to reduce the truth to a single contract file that
> humans and machines read alike. This article covers why that is worth doing, why code generation is
> far from the main reason, what adoption actually costs the backend, and where the approach is
> genuinely weak.

## Where the pain comes from

I am a mobile developer. Working with data structures, I sometimes look at an endpoint, go to the wiki,
find the page describing it — and do not believe it. Because experience says the page describes the API
as it was intended six months ago, not as it is now. Then the familiar ritual begins: I message a
backend developer, they answer "check Swagger", Swagger is generated from annotations and shows an
approximate picture, and the real response differs from it because the serialisation rule lives in one
place and the description-generating rule in another. In the end I do what most client developers do: I
call the endpoint for real, look at the actual JSON, and believe only that.

This is the source-of-truth problem. We do not have one source, we have several, and they compete. The
wiki is intent. The backend code is implementation. Real traffic is fact. And when they diverge — which
they always do — the cost of the mistake lands first on the API's consumers: on the frontend, on iOS, on
Android, on desktop, on external integrators.

Plenty of people have described this pain. Alexey, a Java developer at YooMoney, puts it bluntly in his
article on improving server-to-server interaction: Swagger UI generated automatically from class
metadata shows only a rough description of what the API really returns, so frontend and mobile
developers cannot start work without calling the endpoint live. This is not somebody's personal
sloppiness — it is a structural flaw in a process where the truth is not centralised.

## What OpenAPI is (for those who have not run into it)

OpenAPI is an open standard for describing HTTP APIs — primarily REST-style ones — in a machine-readable
form. It is worth drawing the boundary immediately: OpenAPI is not the only contract language and does
not cover every protocol. For strictly typed inter-service communication there is gRPC with Protobuf;
for APIs with flexible queries, GraphQL with its own type system; for event-driven and broker
architectures (Kafka, message queues), the related AsyncAPI standard. OpenAPI occupies the REST/HTTP
niche — and there, where most client-server APIs of mobile products live, it has become the de facto
standard. It used to be called Swagger; in the mid-2010s the specification was handed to the OpenAPI
Initiative (a body under the Linux Foundation, founded by companies including Google, IBM, Microsoft,
PayPal and SmartBear), and today Swagger is a set of tools around the standard (Swagger UI, Swagger
Editor and so on) while the format itself is called the OpenAPI Specification.

Technically it is a single file — usually YAML, occasionally JSON — describing everything you need to
know about a REST API: which paths exist, which methods they have, which parameters and request bodies
they accept, which response codes and data schemas they return, and how authentication works. The format
is not the point; the idea is: one document that humans and tools read the same way.

Here is what describing a single simple endpoint looks like — a service returning a task by its
identifier:

```yaml
openapi: 3.1.0
info:
  title: TODO Service
  version: 1.0.0
paths:
  /tasks/{taskId}:
    get:
      operationId: getTask
      summary: Get a task by its identifier
      parameters:
        - name: taskId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Task found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
        '404':
          description: Task not found
components:
  schemas:
    Task:
      type: object
      required: [id, title, done]
      properties:
        id:
          type: string
        title:
          type: string
        done:
          type: boolean
```

This reads with almost no preparation: there is a path `/tasks/{taskId}`, it takes an identifier in the
path, and it returns either `200` with a `Task` object or `404`. And — this is the key point — the very
same text is read by a human and by a machine: what you just parsed by eye without preparation, a tool
parses programmatically. One file, one truth, for people and for code alike.

### Reuse instead of copy-paste: DRY in an API description

Before going further, it is worth showing a property that is nearly unattainable in hand-written
documentation and comes free with OpenAPI: reuse. To my mind this is one of the most underrated
arguments, so I will dwell on it.

**Data schemas are described once.** In wiki documentation the same structure — say a user object or a
standard error envelope — spreads across dozens of endpoints, and each description lives its own life.
Somebody fixes a field in one place and forgets five others, and now the documentation contradicts
itself. In OpenAPI the structure is described once in `components/schemas` and referenced everywhere
else through `$ref`. Fix it in one place and it changes everywhere. Inconsistency inside the contract
becomes structurally impossible.

**Different response variants are described briefly and share common parts.** An endpoint rarely returns
a single kind of response: there is `200`, there is `400`, `404`, `409`, and errors usually share a
structure. In a hand-written description that turns into a wall of text where the error structure is
rewritten for every code. In OpenAPI all error responses reference one schema, and there is `default`
for "everything else". Plus schema inheritance through `allOf`: the shared part of several related types
is described once and the special cases inherit it — DRY at the level of data. An important caveat for
later: `allOf` is inheritance, not polymorphism, and it is the calm, predictable case — elegant to
describe and mapped into code by generators without surprises. Polymorphic union types (`oneOf`/`anyOf`)
are a different story, but they belong in the section on drawbacks.

Look how compact this is in practice:

```yaml
paths:
  /tasks/{taskId}:
    get:
      operationId: getTask
      parameters:
        - $ref: '#/components/parameters/TaskId'   # the parameter is described once
      responses:
        '200':
          description: Task found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
              examples:
                sample:
                  $ref: '#/components/examples/TaskSample'  # the example is reused
        '404':
          $ref: '#/components/responses/NotFound'   # a shared error response
        default:
          $ref: '#/components/responses/Error'      # everything else, in one line

components:
  parameters:
    TaskId:
      name: taskId
      in: path
      required: true
      schema:
        type: string
  responses:
    NotFound:
      description: Not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'   # the same error schema
    Error:
      description: Error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
  schemas:
    Error:                       # the error structure is described exactly once
      type: object
      required: [code, message]
      properties:
        code:
          type: integer
        message:
          type: string
    Task:
      allOf:                     # inheritance: the shared part is described once
        - $ref: '#/components/schemas/Entity'
        - type: object
          required: [title, done]
          properties:
            title:
              type: string
            done:
              type: boolean
    Entity:                      # base fields shared by many entities
      type: object
      required: [id]
      properties:
        id:
          type: string
  examples:
    TaskSample:
      value:
        id: "42"
        title: "Buy milk"
        done: false
```

Not a single fragment here is described twice: the parameter, the error schema, the response structure,
the entity's base fields and the example each exist in exactly one copy, and the endpoints reference
them. In hand-written documentation these are precisely the things that get copied again and again, and
it is in that copying that the drift accumulates.

And one more thing, against a common prejudice that "REST is old-fashioned request-response and
everything modern is elsewhere". It is not so. Modern versions of OpenAPI can describe streaming
responses too — the ones where the answer arrives progressively rather than in one piece. The most
recognisable example today is talking to AI chatbots, where text is "typed" onto the screen as tokens
arrive (usually over Server-Sent Events). OpenAPI describes such interfaces alongside ordinary ones, and
tools support them: the official swift-openapi-generator can hand you a streaming response body as an
`AsyncSequence` — that is, the generated client produces a stream that Swift handles with a native
`for try await`. So a contract-first approach does not lock you into the paradigm of the previous
decade: it covers what you are writing right now, while integrating yet another LLM.

---
## The single-source-of-truth idea

The whole point of the approach fits in one sentence: the specification stops being documentation and
becomes a contract. A contract is handled as strictly as code: it lives in version control, it gets pull
requests, it is reviewed, it is versioned with SemVer. Any change to the API starts with a change to the
specification, not with a code edit and a subsequent "don't forget to update the wiki".

Russian-language case studies name it variously — Contract-First, Design-First, Specification-First,
Manifest-First — but the essence is the same: contract first, code second. And one misunderstanding is
worth clearing up immediately. The opposite approach exists too: generating the specification from code,
through annotations (code-first). It looks cheaper, but it reproduces exactly the problem we started
with: the specification stays a secondary, by-product artefact that lags behind reality. Matvey Likhota
of MTS Web Services puts it this way in his write-up: documentation written by hand separately from the
code goes stale at the very next commit — which is precisely why his team inverted the process and made
the specification primary.

When the contract is primary, it acquires a property that neither the wiki nor a backend developer's
head has: it is simultaneously human-readable documentation and input data for a whole zoo of tools. And
this is where it gets interesting.

## Code generation: useful, but not the point

The first thing people think of at the word OpenAPI is code generation: client and server code can be
generated from the specification. For a client developer that means not writing data models, parsing and
a networking layer by hand — all of it comes from the contract and always matches it.

Since I write for Apple platforms, the Swift story is closest to me. Apple has an official
swift-openapi-generator — a package-manager plugin that generates code at build time. That detail
matters: the generated code does not need to be committed, it is always rebuilt from the current
specification, and therefore physically cannot drift from the contract. Calling the generated client
looks roughly like this:

```swift
let client = Client(
    serverURL: URL(string: "https://api.example.com")!,
    transport: URLSessionTransport()
)

let response = try await client.getTask(path: .init(taskId: "42"))

switch response {
case .ok(let ok):
    let task = try ok.body.json
    print(task.title)
case .notFound:
    print("Task not found")
}
```

Note that neither the `getTask` method nor the `.ok` / `.notFound` breakdown of the response is
something I wrote by hand — it is generated from that same YAML specification above. The compiler is now
on my side: if the backend changes the contract, my code simply stops compiling in the right place
instead of "crashing at runtime for some of the users".

Besides the official generator, the Swift ecosystem has third-party tools — for instance projects
optimised for a lightweight networking client. Kotlin/Android and desktop have their own generators,
Microsoft has the cross-language client generator Kiota, and there are .NET-focused tools (NSwag). So
from one contract a team can generate clients for every platform at once — which is exactly what the
YooMoney case studies describe, where one specification yields code for both iOS and Android.

But here is what I want to emphasise, and to my mind it is the main idea of this article: code
generation is a pleasant bonus, not a reason to adopt OpenAPI. Generated code has its own cost (more on
that below), and if everything came down to it, the approach would be much harder to argue for. The real
value of a contract is that it switches on an entire ecosystem of tools that work even if you never
generate a single line of code.

## The main argument: benefits that have nothing to do with code generation

This, I think, is where the real answer to "why do we need this" lies. In order:

**Linting and a consistent API style.** A contract can be checked automatically by a linter — the
best-known tool being Spectral, with alternatives such as Redocly CLI and Vacuum. The linter makes sure
all endpoints follow one style, that operations have descriptions and identifiers, that internal
conventions and security rules are respected. It turns an abstract "API style guide" into an executable
rule that fires in CI rather than living on a forgotten wiki page.

**A mock server out of the box.** A specification can back a mock server — through Prism, for example.
That means a client developer can start work before the backend has written a single line of
implementation: the mock returns responses conforming to the contract. Frontend and backend work in
parallel rather than in sequence. For me as a mobile developer this is possibly the most underrated
item: I stop being at the end of the queue.

**Contract testing.** The same Prism can run as a proxy: it passes real traffic through itself and
checks both requests and responses against the contract, reporting any divergence. That is the
protection against drift: if the real server has started returning something other than what the
specification promises, you learn it from tests rather than from angry users. For deeper testing there
are tools that generate test cases straight from the contract (Schemathesis, for instance).

**Documentation that does not lie.** The specification generates good interactive documentation — via
Redoc/Redocly or Swagger UI. Unlike a wiki, that documentation cannot go stale: it is produced from the
same contract that is the source of truth. Divergence between documentation and "the truth" becomes
structurally impossible.

**Breaking-change detection.** This is a separate and, for a consumer, very important point. The oasdiff
tool compares two versions of a specification and tells you which changes break backward compatibility
and which are safe. It can be wired into CI to block a pull request that quietly breaks clients. For
mobile development, where old versions of an app live on users' devices for months, this is critical: a
breaking change in an API is not an abstraction, it is a crashed app belonging to somebody who did not
update.

**Reverse-engineering existing APIs.** What if there is no specification and the API already works? Not
a dead end either. There are tools that build a draft OpenAPI document from observed traffic — browser
extensions that listen to network requests (openapi-devtools) and utilities converting captured traffic
or Postman collections into a specification (mitmproxy2swagger, postman2openapi). That lets you catch up
to design-first even on legacy.

**Overlays — careful modification without touching the original.** A separate OpenAPI Overlays standard
lets you apply changes on top of a specification without editing the source: add descriptions, hide
internal endpoints before publishing externally, substitute different server URLs for different
environments. Useful when the source contract is generated or maintained by another team.

**AI and MCP.** A fresh layer: a specification can automatically back an MCP (Model Context Protocol)
server — through a tool such as emcee — after which an AI agent can use your API as a set of tools. The
contract works once again as a universal adapter: what is described once gets reused by people, by
machines and by language models.

**Editors and design tools.** Working with a contract locally has become convenient. The main tool here
is the OpenAPI (Swagger) Editor plugin from 42Crunch for VS Code: it gives you practically what the
online Swagger Editor does, but locally — rendered documentation preview (through Swagger UI or ReDoc),
autocompletion (IntelliSense), navigation through references, go-to-definition and built-in linting. The
basic editor is free and requires no registration; there are heavier security-audit capabilities, some
of which do. Alongside it, several other tools are worth naming: the Redocly OpenAPI extension for VS
Code (validation, `$ref` navigation and documentation preview — though preview needs a Redocly key);
Stoplight Studio, a visual specification editor with a built-in Prism mock server; Insomnia by Kong, a
client with a native OpenAPI editor and live preview, local storage and linting through the Inso CLI;
and Apidog, an integrated platform combining design, debugging, mocking and testing in one place. It is
worth separating local from cloud here honestly: the 42Crunch and Redocly VS Code plugins and Stoplight
Studio work locally; Insomnia can store data entirely locally (Local Vault); Apidog is fundamentally a
cloud platform, which teams with data-residency requirements need to take into account.

Note that not one of these items requires code generation. Even if your team writes every line of the
networking layer by hand, you still get linting, mocks, contract tests, honest documentation and
protection from breaking changes. That is why I consider the "generate code or not" argument secondary
to the decision "have a contract or not".

## Honestly about the drawbacks

I promised an apologia in the classical sense — a defence that does not hide the inconvenient facts.
Here they are.

**Polymorphism and discriminators hurt (but less often than you would think).** First, the scale. The
overwhelming majority of types in a real specification are simple flat structures reused through `$ref`;
for them, code generation and the rest of the tooling work flawlessly. Inheritance through `allOf`,
which we just praised for DRY, is usually digested by generators without surprises too. And both `allOf`
and — even more so — polymorphism with a discriminator appear in live contracts noticeably less often
than simple subtypes. The pain begins precisely with polymorphic "either-or" types, where an object can
be *one of* several variants (`oneOf`/`anyOf` with a discriminator): here generators behave differently
and often emit clumsy code. Habr has a detailed analysis of exactly this pain in a Java/Spring context
(the article on generating OpenAPI contracts and `oneOf`, `anyOf`, `allOf`): the discriminator is
described there as the thing that lets you control code generation when using polymorphism, and it turns
into specific Java annotations, `@JsonSubTypes`. The conclusion is honest: discriminators work, but they
require care and an understanding of how exactly your generator maps polymorphism into code. On the
client the story is similar. This is a genuine limitation — but, as I said, more of a rare corner than a
daily obstacle: for most endpoints you will simply not meet it.

**The ergonomics of generated code.** Generated code is almost always bulkier and less "native" than
hand-written code. Names in the specification turn directly into names in the code — crooked naming in
the spec means crooked naming in the code. Some generators stumble over anonymous objects and
non-standard constructs. The official swift-openapi-generator has already had a sceptical review on
Habr from Ozon's iOS team: Andrey, a developer on the "Ozon Pickup Point" app, complains in his article
"Is Swift OpenAPI Generator ready for production code?" about the inability to influence the generation
process and about very long dependency builds — an empty project took him around 105 seconds on a
MacBook Pro M1. The tool has matured noticeably since, but the fact itself is telling: choose a
generator soberly and check the result against your real contract rather than against a textbook example
with kittens.

**The discipline to maintain it.** A contract works exactly as well as the team is disciplined. If the
process allows changing code around the specification, you get the worst of both worlds: a contract and
a reality, both lying. Russian-language case studies describe this bluntly: an analyst draws a schema, a
developer changes it "in the code" along the way, testers file fifty defects against the analyst's
schema — and it turns out there is no single source of truth after all. Formally adopting a contract
without discipline does not solve the problem, it masks it.

**The approach requires roles and time.** The same MTS team notes honestly: spec-first works well where
there are analysts and architects responsible for specifications, or where developers have time
allocated for writing them. This is not free. And that brings us to the main objection.

## "That's extra work for the backend" — an honest look

The most frequent objection I hear: "It's fine for you, a client developer — but now we, the backend
team, have to write YAML specifications by hand as well. That's extra work."

Let us take the objection seriously rather than wave it away. It has two parts, and distinguishing them
matters.

**The first part is real.** Yes, spec-first has a genuine up-front cost. Somebody has to sit down and
write the contract before coding starts. For a new service that is hours, sometimes days, of work for a
couple of people. For a team without dedicated analysts it means the load falls on developers. That is
an honest price, and pretending it does not exist would be dishonest. What is more, under code-first the
specification is formally "free" (generated from annotations), and for prototypes, MVPs and APIs whose
only consumer is you, code-first may genuinely be the more sensible choice. I am not claiming spec-first
is for everyone always.

**The second part is resistance to novelty, disguised as an argument about effort.** And here it pays to
be careful. "Extra work" in that objection often means not "more work in total" but "work that is new to
me, that I have not done before and do not fancy learning". That is a normal human reaction — habit is a
strong thing, as one Habr case study neatly puts it. But it is not an argument about effort, it is an
argument about comfort zones, and it deserves to be called by its name.

Because if you count the full cost honestly, the picture changes. The work that "disappears" under
code-first does not actually disappear — it is smeared out and shifted onto other people and onto later.
Matvey Likhota of MTS gives a concrete figure: keeping Swagger documentation current across a dozen
microservices consumed up to 20% of the team's time, and after moving to Documentation-Driven
Development roughly 20% of developer time was freed up. That is not "extra work for the backend" — that
is a loss already being incurred, merely invisible, because it is spread across integration bugs, chat
threads, "just call the endpoint live", and clients broken for users after an unannounced breaking
change.

Move the cost to the front — write the contract once and strictly — and everyone gains afterwards:
mistakes are caught in a YAML review in minutes rather than the day before release; client teams start
in parallel against mocks; breaking changes are caught automatically; documentation stops lying. So the
honest answer to the objection is: **yes, there is a real up-front cost for the backend and it must be
planned for honestly; but a significant part of this "new work" is not additional effort — it is the
effort the team already spends, moved to the front and made visible, instead of being spent later, more
expensively, and by somebody else.**

And one more detail that takes the tension out: the contract does not have to be written by a backend
developer alone. Analysts and testers write excellent drafts, and client developers finally get to
influence the API at design time — bringing not a JSON file saying "I want it like this" but a pull
request against the specification. That inverts the usual dynamic where the backend can change the API
at any moment and the client is obliged to adapt, moving it toward a jointly agreed contract.

## How to adopt without risk: a staged plan

Switching the whole company to full Contract-First at once is a bad idea. The approach requires
discipline, and discipline is not introduced by decree. It is far safer to move in small steps, each of
which pays off even if you stop there.

1. **Start with one service, or even one domain.** Make it the reference. Do not try to describe
   everything at once — that is the road to burnout and an abandoned initiative.
2. **If the API already exists, do not write the contract from scratch.** Generate a draft from real
   traffic or from existing Postman collections, then finish it by hand.
3. **Agree on conventions and turn on a linter.** Before scaling, describe what "good" looks like for
   your APIs and fix it as Spectral rules in CI. Otherwise every service will have its own style.
4. **Wire up mocks and contract tests before code generation.** These are the fastest wins with the
   least risk: client teams start working in parallel and drift is caught automatically. Code generation
   can wait.
5. **Put a breaking-change check in CI.** oasdiff on a pull request against the specification is cheap
   to adopt and expensive to underestimate.
6. **And only then code generation**, where it is justified, and always verified against your real
   contract rather than a textbook example.

What should stop you and make you revisit the plan: if the specification starts being edited around the
process — the code has diverged from the contract and nobody is bothered — then there is no discipline,
and the process needs fixing before more tools are added. A contract without discipline is just one more
lying source of truth.

## Conclusion

OpenAPI is not about "not writing code by hand". It is about a team having one source of truth about how
the API is built, and about that source being machine-readable — and therefore checkable, testable, and
incapable of silently diverging from reality. Code generation is a pleasant bonus with its own cost; the
real benefit is in linting, mocks, contract tests, honest documentation and automatic detection of
breaking changes.

The approach has an honest price and real weak spots: polymorphism is awkward, generated code is not
always pretty, and the whole thing rests on team discipline. The objection "this is extra work for the
backend" is half fair — the up-front cost is real and must be budgeted for; but the other half of that
"work" is not new effort, it is old effort moved to the front and made visible.

To my mind, for a team whose API has more than one consumer — and mobile products always have at least
two, iOS and Android — this trade is almost always worth making. The wiki lies, prod is silent, and a
contract, if taken seriously, tells the truth. It is worth giving it the chance.
