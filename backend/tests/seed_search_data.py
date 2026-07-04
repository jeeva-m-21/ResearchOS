"""Seed search test data: insert nodes with embeddings for hybrid search testing.

Usage:
    docker exec researchos-backend-1 python tests/seed_search_data.py
"""
import sys

# PYTHONPATH is set to /app/src but importing "src" requires the parent /app
# to be in sys.path so Python can find /app/src/__init__.py.
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

import asyncio

import asyncpg

from src.infrastructure.adapters.embeddings.local import LocalEmbeddingAdapter

DATABASE_URL = "postgresql://researchos:researchos@postgres:5432/researchos"
TEST_ORG_ID = "02b5991b-d971-41fc-b257-4ded07d94aac"
TEST_USER_ID = "53b11894-63f8-45a5-8095-8581c9b01163"

SEED_NODES = [
    (
        "transformer",
        "A transformer neural network for NLP tasks, including BERT and GPT",
    ),
    (
        "reinforcement learning",
        "Training agents through reward-based learning in environments",
    ),
    (
        "convolutional neural networks",
        "CNN architecture for image processing and computer vision tasks",
    ),
    (
        "attention mechanism",
        "Allows models to focus on relevant parts of the input",
    ),
    (
        "gradient descent optimization",
        "Minimizes loss by iteratively updating parameters",
    ),
    (
        "natural language processing",
        "NLP techniques for text analysis, translation, and generation",
    ),
    (
        "computer vision",
        "Image recognition, object detection, and segmentation with deep learning",
    ),
    (
        "graph neural networks",
        "GNN architecture for processing graph-structured data",
    ),
    (
        "transfer learning",
        "Leveraging pre-trained models for new tasks with limited data",
    ),
    (
        "data augmentation",
        "Techniques to increase dataset diversity through transformations",
    ),
]

# Use only types that exist in the ENUM (see migration 4ad09203efc6)
NODE_TYPES = [
    "idea", "hypothesis", "experiment", "paper", "dataset",
    "model", "notebook", "block", "citation", "person",
]


async def seed():
    adapter = LocalEmbeddingAdapter()
    conn = await asyncpg.connect(DATABASE_URL)

    # Check existing count
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM nodes WHERE organization_id = $1", TEST_ORG_ID
    )
    print(f"Existing nodes for org: {count}")

    if count and count > 0:
        print("Nodes already seeded — skipping.")
        await conn.close()
        return

    texts = [title for title, desc in SEED_NODES]
    embeddings = await adapter.embed(texts)

    for i, ((title, desc), embedding, ntype) in enumerate(
        zip(SEED_NODES, embeddings, NODE_TYPES)
    ):
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
        await conn.execute(
            """INSERT INTO nodes
               (id, organization_id, node_type, title, description,
                embedding, search_vector, created_by, created_at, updated_at)
               VALUES (gen_random_uuid(), $1::uuid, $2::node_type,
                       $3::varchar(500), $4::text, $5::vector,
                       setweight(to_tsvector('english', coalesce($3, '')), 'A')
                       || setweight(to_tsvector('english', coalesce($4, '')), 'B'),
                       $6::uuid, NOW(), NOW())""",
            TEST_ORG_ID,
            ntype,
            title,
            desc,
            vec_str,
            TEST_USER_ID,
        )
        print(f"  [{i+1}/{len(SEED_NODES)}] Inserted '{title}' ({ntype})")

    final_count = await conn.fetchval(
        "SELECT COUNT(*) FROM nodes WHERE organization_id = $1", TEST_ORG_ID
    )
    print(f"\n✅ Seeded {final_count} nodes for organization {TEST_ORG_ID}")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
