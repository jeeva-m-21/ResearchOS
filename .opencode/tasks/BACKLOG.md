# ResearchOS Backlog
Ordered, smallest-shippable tasks. The orchestrator works top-down and only starts a task whose deps are DONE.

Task format:
## T-XXX — <title>
- status: TODO | DOING | DONE | BLOCKED
- deps: none | T-YYY
- agents: @backend, @test
- acceptance: <the one test / command that must pass>
- notes: <one line of context>

## T-001 — Fix GET /auth/api-keys 404
- status: TODO
- deps: none
- agents: @backend, @test
- acceptance: test_auth_api_keys_post_creates_key passes; ruff + mypy clean
- notes: endpoint should be POST /auth/api-keys; remove/redirect the bad GET

## T-002 — logout requires refresh_token body
- status: TODO
- deps: none
- agents: @backend, @test
- acceptance: test_logout_with_refresh_token returns 200; missing body returns 422
- notes: validate refresh_token in the request model