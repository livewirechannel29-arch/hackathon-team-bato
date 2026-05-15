# Team bato
 
## Participants

rolando.d.de.guzman

jyrus.d.carrasco

kenneth.abad

jake.r.necio

## Scenario

Scenario 1: Code Modernization
 
## What We Built

Northwind Logistics
 
## Challenges Attempted

#	Challenge	Role	Description

1	The Stories	PM	Write user stories for the three most important business capabilities. Acceptance criteria that a tester could actually execute.

2	The Patient	Architect	Generate the legacy monolith. 4–6 modules, shared database, at least two circular dependencies, one God class. Make it realistic.

3	The Map	Architect	Produce a decomposition plan. Strangler fig, branch-by-abstraction, your call. Name the seams. Rank the services by extraction risk.

4	The Pin	Tester	Write characterization tests against the monolith before anyone touches it. You're not testing correctness — you're pinning behavior.

5	The Cut	Dev	Extract your first service. Clean API contract. The monolith still works. Prove both.

6	The Fence	Dev	Build an anti-corruption layer between old and new. The monolith's data model should not leak into your new service.

7	The Contract	Tester	Contract tests between the monolith and the new service. Both sides. If one changes, the other screams.

8	The Pipeline	Infra	CI/CD that builds and deploys both monolith and service. Independently. One failing doesn't block the other.

9	The Second Cut	Stretch	Extract a second service. This one talks to the first via events, not HTTP. Handle the dual-write problem.

10	The Weekend	Stretch	Write the cutover runbook. Steps, rollback triggers, the 3am decision tree. The one ops will actually follow.
 
## Key Decisions

Biggest calls you made and why. Link into /decisions for the full ADRs.
 
## How to Run It

Exact commands. Assume the reader has Docker and nothing else.
 
## If We Had Another Day

What you'd tackle next, in priority order.

Be honest about what's held together with tape.
 
## How We Used Claude Code

What worked. What surprised you. Where it saved the most time.
 # hackathon-team-bato
