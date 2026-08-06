import re
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table
from .slugify import normalize_slug

def parse_docx_file(file_path: str) -> dict:
    """
    Lê um arquivo .docx e extrai:
    - title: Título original do documento (primeira linha não vazia)
    - metadata: Dicionário de metadados com chaves e valores normalizados (slug)
    - raw_metadata: Dicionário de metadados preservando o formato original caso necessário
    - content_md: Conteúdo do corpo em formato Markdown
    """
    doc = docx.Document(file_path)
    
    paragraphs_and_tables = []
    
    # Coleta blocos em ordem (parágrafos e tabelas)
    for element in doc.element.body:
        if element.tag.endswith('p'):
            paragraphs_and_tables.append(Paragraph(element, doc))
        elif element.tag.endswith('tbl'):
            paragraphs_and_tables.append(Table(element, doc))
            
    title = ""
    metadata = {}
    raw_metadata = {}
    content_blocks = []
    
    in_metadata_section = True
    title_found = False
    
    # Expressão regular para capturar "- Chave: Valor", "• Chave: Valor" ou "Chave: Valor"
    kv_pattern = re.compile(r'^(?:[\-\*•]\s*)?([^:]+):\s*(.*)$')
    
    for item in paragraphs_and_tables:
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                continue
                
            # Se ainda estamos buscando o título
            if not title_found:
                title = text
                title_found = True
                continue
                
            # Se estamos na seção de metadados
            if in_metadata_section:
                # Condição de saída 1: Parágrafo inicia com # (início de conteúdo markdown)
                if text.startswith('#'):
                    in_metadata_section = False
                    content_blocks.append(item)
                    continue
                    
                # Condição de saída 2: Estilo de parágrafo é um Heading (Título)
                if item.style and item.style.name.startswith('Heading'):
                    in_metadata_section = False
                    content_blocks.append(item)
                    continue
                    
                # Tenta casar com o padrão de chave: valor
                match = kv_pattern.match(text)
                if match:
                    raw_key = match.group(1).strip()
                    raw_val = match.group(2).strip()
                    
                    norm_key = normalize_slug(raw_key)
                    norm_val = normalize_slug(raw_val)
                    
                    metadata[norm_key] = norm_val
                    raw_metadata[raw_key] = raw_val
                    
                    # Condição de saída 3: se for a chave 'palavras-chave' / 'palavras chave'
                    if norm_key in ('palavras-chave', 'palavras-chave-'):
                        in_metadata_section = False
                else:
                    # Não casou com chave-valor e não é o título -> Início do conteúdo
                    in_metadata_section = False
                    content_blocks.append(item)
            else:
                content_blocks.append(item)
        elif isinstance(item, Table):
            # Tabelas sempre fazem parte do conteúdo
            in_metadata_section = False
            content_blocks.append(item)
            
    # Converte os blocos de conteúdo para Markdown
    markdown_lines = []
    for item in content_blocks:
        if isinstance(item, Paragraph):
            md_line = paragraph_to_markdown(item)
            if md_line:
                markdown_lines.append(md_line)
        elif isinstance(item, Table):
            md_table = table_to_markdown(item)
            if md_table:
                markdown_lines.append(md_table)
                
    content_md = "\n\n".join(markdown_lines)
    
    return {
        "title": title,
        "metadata": metadata,
        "raw_metadata": raw_metadata,
        "content_md": content_md
    }


def paragraph_to_markdown(paragraph: Paragraph) -> str:
    text = paragraph.text.strip()
    if not text:
        return ""
        
    style_name = paragraph.style.name if paragraph.style else ""
    
    # Se a própria linha já começar com marcas de título (#)
    if text.startswith('#'):
        return text
        
    # Estilos nativos de cabeçalho do docx
    if style_name.startswith('Heading 1'):
        return f"# {text}"
    elif style_name.startswith('Heading 2'):
        return f"## {text}"
    elif style_name.startswith('Heading 3'):
        return f"### {text}"
    elif style_name.startswith('Heading 4'):
        return f"#### {text}"
    elif style_name.startswith('Heading 5'):
        return f"##### {text}"
    elif style_name.startswith('Heading 6'):
        return f"###### {text}"
        
    # Listas marcadas (bullets)
    if style_name.startswith('List Bullet') or text.startswith(('• ', '- ', '* ')):
        clean_text = re.sub(r'^[•\-\*]\s*', '', text)
        return f"- {clean_text}"
        
    # Listas numeradas
    if style_name.startswith('List Number') or re.match(r'^\d+\.\s', text):
        clean_text = re.sub(r'^\d+\.\s*', '', text)
        return f"1. {clean_text}"
        
    return format_runs(paragraph, text)



def format_runs(paragraph: Paragraph, default_text: str = None) -> str:
    """
    Aplica formatações inline (negrito, itálico) baseadas nos runs do parágrafo.
    """
    if not paragraph.runs:
        return default_text or paragraph.text
        
    result = []
    for run in paragraph.runs:
        r_text = run.text
        if not r_text:
            continue
        if run.bold and run.italic:
            r_text = f"***{r_text.strip()}***"
        elif run.bold:
            r_text = f"**{r_text.strip()}**"
        elif run.italic:
            r_text = f"*{r_text.strip()}*"
        result.append(r_text)
        
    formatted = "".join(result).strip()
    return formatted if formatted else (default_text or paragraph.text)


def table_to_markdown(table: Table) -> str:
    """
    Converte uma tabela docx em tabela Markdown.
    """
    if not table.rows:
        return ""
        
    rows_data = []
    for row in table.rows:
        row_cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
        rows_data.append(row_cells)
        
    if not rows_data:
        return ""
        
    header = rows_data[0]
    separator = ["---"] * len(header)
    
    md_lines = []
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("| " + " | ".join(separator) + " |")
    
    for row in rows_data[1:]:
        md_lines.append("| " + " | ".join(row) + " |")
        
    return "\n".join(md_lines)
