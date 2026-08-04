from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tse import queries

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/tse", tags=["tse"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def tse_hub(request: Request) -> HTMLResponse:
    summary = queries.get_summary()
    return templates.TemplateResponse(
        request,
        "tse/hub.html",
        {"summary": summary, "section": "tse"},
    )


@router.get("/groups", response_class=HTMLResponse)
def groups_index(request: Request) -> HTMLResponse:
    groups = queries.list_groups()
    return templates.TemplateResponse(
        request,
        "tse/groups/index.html",
        {"groups": groups, "section": "tse"},
    )


@router.get("/groups/{slug}", response_class=HTMLResponse)
def groups_detail(
    request: Request,
    slug: str,
    q: str | None = Query(default=None),
    frequency: str | None = Query(default=None),
) -> HTMLResponse:
    datasets = queries.list_datasets(group=slug, q=q, frequency=frequency)
    frequencies = queries.list_frequencies()
    return templates.TemplateResponse(
        request,
        "tse/groups/detail.html",
        {
            "slug": slug,
            "datasets": datasets,
            "q": q or "",
            "frequency": frequency or "",
            "frequencies": frequencies,
            "section": "tse",
        },
    )


@router.get("/datasets/{name}", response_class=HTMLResponse)
def dataset_detail(request: Request, name: str) -> HTMLResponse:
    dataset = queries.get_dataset(name)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")
    resources = queries.list_resources(name)
    return templates.TemplateResponse(
        request,
        "tse/datasets/detail.html",
        {"dataset": dataset, "resources": resources, "section": "tse"},
    )


@router.get("/datasets/{name}/resources/{resource_id}", response_class=HTMLResponse)
def resource_detail(request: Request, name: str, resource_id: str) -> HTMLResponse:
    resource = queries.get_resource(resource_id)
    if not resource or resource["dataset_name"] != name:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    columns = queries.list_columns(resource_id)
    return templates.TemplateResponse(
        request,
        "tse/resources/detail.html",
        {"resource": resource, "columns": columns, "section": "tse"},
    )


@router.get("/health", response_class=HTMLResponse)
def health(request: Request) -> HTMLResponse:
    health_data = queries.get_health()
    return templates.TemplateResponse(
        request,
        "tse/health.html",
        {"health": health_data, "section": "health"},
    )


@router.get("/about", response_class=HTMLResponse)
def about(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tse/about.html",
        {"section": "about"},
    )
