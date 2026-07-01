# apps/api rules
- Routers stay thin: parse -> call a domain service -> serialize.
- Business logic in domain/services. Domain imports no framework/DB.
- Reach DB/LLM/storage only through ports/. Implement in adapters/.
- Every endpoint gets a pytest. Ingest must be idempotent.
- Migrations via alembic; never edit the DB by hand.
