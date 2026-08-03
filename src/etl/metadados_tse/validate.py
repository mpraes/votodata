from __future__ import annotations

from models import DatasetRecord, DqInfo, ValidationResult

# Campos prioritários do plano (após API+HTML)
PRIORITY_FIELDS = (
    ("negocio", "contato"),
    ("negocio", "escopo_geopolitico"),
    ("negocio", "area_gestora"),
    ("operacional", "extracao_dados"),
    ("operacional", "frequencia_atualizacao"),
    ("operacional", "criado_em"),
)


def validate_dataset(record: DatasetRecord) -> ValidationResult:
    warnings: list[str] = []
    errors: list[str] = []

    # Críticos — sem isso não faz sentido persistir
    if not record.dataset.id:
        errors.append("dataset.id ausente")
    if not (record.dataset.name or "").strip():
        errors.append("dataset.name ausente")
    if not (record.dataset.titulo or "").strip():
        errors.append("dataset.titulo ausente")

    for rec in record.recursos:
        if not (rec.url or "").strip():
            errors.append(f"recurso {rec.id} sem url")

    # Avisos — persiste mesmo assim
    if not record.recursos or (record.dataset.num_resources or 0) == 0:
        warnings.append("dataset sem recursos")

    for secao, campo in PRIORITY_FIELDS:
        obj = getattr(record, secao)
        if getattr(obj, campo, None) in (None, ""):
            warnings.append(f"campo prioritario vazio: {secao}.{campo}")

    if record.negocio.extras_nao_mapeados:
        keys = ", ".join(sorted(record.negocio.extras_nao_mapeados.keys()))
        warnings.append(f"extras_nao_mapeados: {keys}")

    if errors:
        dq = DqInfo(status="error", warnings=warnings, errors=errors)
        return ValidationResult(ok_to_persist=False, dq=dq)

    status = "warn" if warnings else "ok"
    dq = DqInfo(status=status, warnings=warnings, errors=errors)
    return ValidationResult(ok_to_persist=True, dq=dq)


def apply_validation(record: DatasetRecord) -> ValidationResult:
    """Valida e anexa dq no record (in-place)."""
    result = validate_dataset(record)
    record.dq = result.dq
    return result