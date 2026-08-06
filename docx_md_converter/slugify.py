import re
import unicodedata

def normalize_slug(text: str) -> str:
    """
    Normaliza texto removendo acentos, convertendo para minúsculo
    e substituindo espaços e caracteres especiais por hífen.
    Exemplo: "Família de Produto" -> "familia-de-produto"
             "Conta Corrente" -> "conta-corrente"
    """
    if not text:
        return ""
    # Normalização Unicode NFKD para separar caracteres de diacríticos
    nfkd_form = unicodedata.normalize('NFKD', str(text))
    # Remove marcas diacríticas (acentos)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Converte para minúsculo
    lowercased = only_ascii.lower()
    # Substitui sequências de caracteres não alfanuméricos por hífen
    slug = re.sub(r'[^a-z0-9]+', '-', lowercased)
    # Remove hífens duplicados ou nas extremidades
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug
