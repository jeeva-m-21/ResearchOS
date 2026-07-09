"""Paper endpoints — CRUD for papers, citations, and references"""
import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from api.dependencies.events import get_event_producer
from domain.papers.events import (
    CitationAdded,
    CitationRemoved,
    PaperCreated,
    PaperDeleted,
    PaperEdited,
)
from infrastructure.auth.jwt import TokenData
from infrastructure.database import db
from infrastructure.events.producer import EventProducer

router = APIRouter()


# ─── Papers ────────────────────────────────────────────────────────────


@router.post("/")
async def create_paper(
    title: str,
    project_id: UUID,
    abstract: Optional[str] = None,
    authors: Optional[str] = None,
    latex_content: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Create a new paper"""
    # Verify project belongs to organization
    project = await db.fetch_one(
        """
        SELECT id FROM projects
        WHERE id = $1 AND organization_id = $2
        AND deleted_at IS NULL
        """,
        project_id,
        organization_id,
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied",
        )

    paper_id = uuid4()
    parsed_authors = json.loads(authors) if authors else []
    now = datetime.utcnow()

    await db.execute(
        """
        INSERT INTO papers (
            id, organization_id, project_id, title, abstract,
            status, version, authors, latex_content,
            created_by, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, 'draft', 1, $6::jsonb, $7, $8, $9, $10)
        """,
        paper_id,
        organization_id,
        project_id,
        title,
        abstract,
        json.dumps(parsed_authors),
        latex_content,
        user.user_id,
        now,
        now,
    )

    # Emit paper.created event
    event = PaperCreated(
        aggregate_id=paper_id,
        paper_id=paper_id,
        organization_id=organization_id,
        project_id=project_id,
        title=title,
        status="draft",
    )
    await event_producer.emit(event)

    return {
        "id": str(paper_id),
        "title": title,
        "status": "draft",
    }


@router.get("/")
async def list_papers(
    project_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List papers, optionally filtered by project and/or status"""
    conditions = ["organization_id = $1", "deleted_at IS NULL"]
    params: list[Any] = [organization_id]
    idx = 2

    if project_id:
        conditions.append(f"project_id = ${idx}")
        params.append(project_id)
        idx += 1

    if status_filter:
        conditions.append(f"status = ${idx}")
        params.append(status_filter)
        idx += 1

    params.extend([limit, offset])

    papers = await db.fetch_all(
        f"""
        SELECT
            id, project_id, title, abstract, status, version,
            authors, doi, arxiv_id, tags, latex_content,
            created_at, updated_at
        FROM papers
        WHERE {' AND '.join(conditions)}
        ORDER BY updated_at DESC
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params,
    )

    return [dict(p) for p in papers]


@router.get("/{paper_id}")
async def get_paper(
    paper_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Get paper by ID with citations"""
    paper = await db.fetch_one(
        """
        SELECT
            id, project_id, title, abstract, status, version,
            authors, doi, arxiv_id, tags, latex_content,
            created_by, created_at, updated_at
        FROM papers
        WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL
        """,
        paper_id,
        organization_id,
    )

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    result = dict(paper)

    # Fetch citations
    citations = await db.fetch_all(
        """
        SELECT id, citation_key, cited_paper_id, cited_doi,
               title, authors, year, venue, url, citation_text,
               created_at
        FROM citations
        WHERE paper_id = $1 AND organization_id = $2
        ORDER BY citation_key ASC
        """,
        paper_id,
        organization_id,
    )
    result["citations"] = [dict(c) for c in citations]

    return result


@router.patch("/{paper_id}")
async def update_paper(
    paper_id: UUID,
    title: Optional[str] = None,
    abstract: Optional[str] = None,
    status: Optional[str] = None,
    authors: Optional[str] = None,
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    tags: Optional[str] = None,
    latex_content: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Update paper fields"""
    # Verify paper exists
    existing = await db.fetch_one(
        "SELECT id, status, project_id FROM papers "
        "WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL",
        paper_id,
        organization_id,
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Build dynamic SET clause
    sets: list[str] = []
    params: list[Any] = [paper_id, organization_id]
    idx = 3
    changes: dict[str, Any] = {}

    if title is not None:
        sets.append(f"title = ${idx}")
        params.append(title)
        changes["title"] = title
        idx += 1

    if abstract is not None:
        sets.append(f"abstract = ${idx}")
        params.append(abstract)
        changes["abstract"] = abstract
        idx += 1

    if status is not None:
        valid_statuses = {"draft", "in_review", "published", "archived"}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid status. Must be one of: "
                    "draft, in_review, published, archived"
                ),
            )
        sets.append(f"status = ${idx}")
        params.append(status)
        changes["status"] = status
        idx += 1

    if authors is not None:
        parsed = json.loads(authors)
        sets.append(f"authors = ${idx}::jsonb")
        params.append(json.dumps(parsed))
        changes["authors"] = parsed
        idx += 1

    if doi is not None:
        sets.append(f"doi = ${idx}")
        params.append(doi)
        changes["doi"] = doi
        idx += 1

    if arxiv_id is not None:
        sets.append(f"arxiv_id = ${idx}")
        params.append(arxiv_id)
        changes["arxiv_id"] = arxiv_id
        idx += 1

    if tags is not None:
        parsed = json.loads(tags)
        sets.append(f"tags = ${idx}::jsonb")
        params.append(json.dumps(parsed))
        changes["tags"] = parsed
        idx += 1

    if latex_content is not None:
        sets.append(f"latex_content = ${idx}")
        params.append(latex_content)
        changes["latex_content"] = latex_content
        idx += 1

    if not sets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    sets.append("version = version + 1")
    sets.append("updated_at = NOW()")

    await db.execute(
        (
            "UPDATE papers SET " + ", ".join(sets)
            + " WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL"
        ),
        *params,
    )

    # Emit paper.edited event
    if changes:
        event = PaperEdited(
            aggregate_id=paper_id,
            paper_id=paper_id,
            organization_id=organization_id,
            project_id=existing["project_id"],
            changes=changes,
            created_by=user.user_id,
        )
        await event_producer.emit(event)

    # Return updated paper
    updated = await db.fetch_one(
        """
        SELECT id, project_id, title, abstract, status, version,
               authors, doi, arxiv_id, tags, latex_content,
               created_at, updated_at
        FROM papers WHERE id = $1 AND organization_id = $2
        """,
        paper_id,
        organization_id,
    )
    return dict(updated)


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(
    paper_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Soft-delete a paper"""
    result = await db.execute(
        "UPDATE papers SET deleted_at = NOW() "
        "WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL",
        paper_id,
        organization_id,
    )

    if result == "UPDATE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    event = PaperDeleted(
        aggregate_id=paper_id,
        paper_id=paper_id,
        organization_id=organization_id,
    )
    await event_producer.emit(event)


# ─── Citations ──────────────────────────────────────────────────────────


@router.post("/{paper_id}/citations")
async def add_citation(
    paper_id: UUID,
    citation_key: str,
    title: str,
    year: int,
    cited_doi: Optional[str] = None,
    cited_paper_id: Optional[UUID] = None,
    authors: Optional[str] = None,
    venue: Optional[str] = None,
    url: Optional[str] = None,
    citation_text: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Add a citation to a paper"""
    # Verify paper exists
    paper = await db.fetch_one(
        "SELECT id FROM papers "
        "WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL",
        paper_id,
        organization_id,
    )

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    citation_id = uuid4()
    parsed_authors = json.loads(authors) if authors else []

    await db.execute(
        """
        INSERT INTO citations (
            id, paper_id, organization_id, citation_key,
            cited_paper_id, cited_doi, title, authors,
            year, venue, url, citation_text
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb,
                  $9, $10, $11, $12)
        """,
        citation_id,
        paper_id,
        organization_id,
        citation_key,
        cited_paper_id,
        cited_doi,
        title,
        json.dumps(parsed_authors),
        year,
        venue,
        url,
        citation_text,
    )

    event = CitationAdded(
        aggregate_id=paper_id,
        paper_id=paper_id,
        organization_id=organization_id,
        citation_id=citation_id,
        citation_key=citation_key,
    )
    await event_producer.emit(event)

    return {
        "id": str(citation_id),
        "citation_key": citation_key,
        "title": title,
        "year": year,
    }


@router.get("/{paper_id}/citations")
async def list_citations(
    paper_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List citations for a paper"""
    citations = await db.fetch_all(
        """
        SELECT id, citation_key, cited_paper_id, cited_doi,
               title, authors, year, venue, url, citation_text,
               created_at
        FROM citations
        WHERE paper_id = $1 AND organization_id = $2
        ORDER BY citation_key ASC
        """,
        paper_id,
        organization_id,
    )
    return [dict(c) for c in citations]


@router.delete("/{paper_id}/citations/{citation_id}", status_code=204)
async def remove_citation(
    paper_id: UUID,
    citation_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
):
    """Remove a citation from a paper"""
    result = await db.execute(
        "DELETE FROM citations "
        "WHERE id = $1 AND paper_id = $2 AND organization_id = $3",
        citation_id,
        paper_id,
        organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation not found",
        )

    event = CitationRemoved(
        aggregate_id=paper_id,
        paper_id=paper_id,
        organization_id=organization_id,
        citation_id=citation_id,
    )
    await event_producer.emit(event)


# ─── References ──────────────────────────────────────────────────────────


@router.post("/{paper_id}/references")
async def add_reference(
    paper_id: UUID,
    citation_id: UUID,
    section_id: Optional[UUID] = None,
    context: Optional[str] = None,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Add an inline reference to a citation"""
    # Verify paper and citation exist
    paper = await db.fetch_one(
        "SELECT id FROM papers "
        "WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL",
        paper_id,
        organization_id,
    )
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    ref_id = uuid4()
    await db.execute(
        """
        INSERT INTO references (id, paper_id, citation_id, section_id, context)
        VALUES ($1, $2, $3, $4, $5)
        """,
        ref_id,
        paper_id,
        citation_id,
        section_id,
        context,
    )

    return {
        "id": str(ref_id),
        "citation_id": str(citation_id),
    }


# ─── LaTeX Compilation ──────────────────────────────────────────────────


@router.post("/{paper_id}/compile")
async def compile_paper(
    paper_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Compile LaTeX source to PDF preview.

    Requires 'pdflatex' to be installed in the container.
    If not available, returns instructions for setup.
    """
    paper = await db.fetch_one(
        """
        SELECT id, title, latex_content
        FROM papers
        WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL
        """,
        paper_id,
        organization_id,
    )
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    latex = paper["latex_content"]
    if not latex:
        return {
            "status": "error",
            "message": (
                "Paper has no LaTeX content. "
                "Write LaTeX source in the editor first."
            ),
        }

    # Check if pdflatex is available
    import os
    import subprocess
    import tempfile

    try:
        subprocess.run(
            ["which", "pdflatex"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "status": "unavailable",
            "message": (
                "LaTeX compiler (pdflatex) is not installed in this "
                "environment. To enable PDF compilation, install TeX Live: "
                "apt-get install texlive texlive-latex-extra"
            ),
            "latex_content": latex,
        }

    # Compile LaTeX to PDF
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "paper.tex")
            with open(tex_path, "w") as f:
                f.write(latex)

            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode",
                 "-output-directory", tmpdir, tex_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            pdf_path = os.path.join(tmpdir, "paper.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()

                # Store the compiled PDF as a temporary artifact
                # For now, return base64-encoded PDF
                import base64
                pdf_b64 = base64.b64encode(pdf_content).decode()

                return {
                    "status": "success",
                    "message": "PDF compiled successfully.",
                    "pdf_base64": pdf_b64,
                    "pdf_size_bytes": len(pdf_content),
                    "log": result.stdout[-2000:] if result.stdout else "",
                }
            else:
                errors = result.stdout[-3000:] if result.stdout else ""
                if result.stderr:
                    errors += "\n" + result.stderr[-2000:]
                return {
                    "status": "error",
                    "message": "LaTeX compilation failed.",
                    "errors": errors[:3000],
                    "log": result.stdout[-3000:] if result.stdout else "",
                }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "LaTeX compilation timed out after 60 seconds.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Compilation error: {exc}",
        }
