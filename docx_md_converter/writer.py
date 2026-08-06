import os
from typing import Dict, Any

def get_metadata_val(metadata: Dict[str, str], *keys: str) -> str:
    """Retorna o valor da primeira chave encontrada no dicionário de metadados."""
    for k in keys:
        if k in metadata and metadata[k]:
            return metadata[k]
    return ""


def get_metadata_parts(metadata: Dict[str, str]) -> list:
    """Retorna os valores dos metadados na ordem especificada para compor o título e nome do arquivo."""
    bu = get_metadata_val(metadata, 'bu')
    familia = get_metadata_val(metadata, 'familia-de-produto', 'familia-produto', 'familia')
    produto = get_metadata_val(metadata, 'produto')
    subproduto = get_metadata_val(metadata, 'subproduto')
    modulo = get_metadata_val(metadata, 'modulo')
    segmento = get_metadata_val(metadata, 'segmento')
    return [p for p in [bu, familia, produto, subproduto, modulo, segmento] if p]


def build_filename(metadata: Dict[str, str], fallback_name: str = "documento") -> str:
    """
    Combina os metadados na ordem:
    BU, Familia de produto, produto, subproduto, Módulo e Segmento (se houver),
    separados por hífen (-).
    """
    parts = get_metadata_parts(metadata)
    if not parts:
        return f"{fallback_name}.md"
        
    filename_base = "-".join(parts)
    return f"{filename_base}.md"


def build_frontmatter_title(metadata: Dict[str, str], fallback_title: str = "") -> str:
    """
    Combina os metadados na mesma ordem do arquivo, mas separados por ' | '.
    """
    parts = get_metadata_parts(metadata)
    if not parts:
        return fallback_title
    return " | ".join(parts)


def write_markdown_file(parsed_data: Dict[str, Any], output_root: str = "output_md") -> str:
    """
    Gera o arquivo .md com Front Matter e salva dentro de output_md/<familia-de-produto>/<nome-do-arquivo>.md.
    Retorna o caminho do arquivo gerado.
    """
    original_title = parsed_data.get("title", "")
    metadata = parsed_data.get("metadata", {})
    content_md = parsed_data.get("content_md", "")
    
    fm_title = build_frontmatter_title(metadata, fallback_title=original_title)
    
    # Prepara o Front Matter
    front_matter_lines = ["---"]
    if fm_title:
        front_matter_lines.append(f'title: "{fm_title}"')
        
    for key, value in metadata.items():
        front_matter_lines.append(f"{key}: {value}")
        
    front_matter_lines.append("---")
    front_matter = "\n".join(front_matter_lines)
    
    full_md_content = f"{front_matter}\n\n{content_md}".strip() + "\n"
    
    # Identifica a família de produto para criar a subpasta
    familia_slug = get_metadata_val(metadata, 'familia-de-produto', 'familia-produto', 'familia')
    if not familia_slug:
        familia_slug = "sem-familia"
        
    target_dir = os.path.join(output_root, familia_slug)
    os.makedirs(target_dir, exist_ok=True)
    
    filename = build_filename(metadata)
    target_filepath = os.path.join(target_dir, filename)
    
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(full_md_content)
        
    return target_filepath
