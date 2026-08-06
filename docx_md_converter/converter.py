import os
import glob
from typing import List, Dict, Any
from .parser import parse_docx_file
from .writer import write_markdown_file
from .history import ConversionHistory

def convert_single_docx(docx_path: str, output_root: str = "output_md") -> tuple[str, dict]:
    """
    Converte um único arquivo .docx para .md.
    Retorna uma tupla (caminho_gerado, dados_parseados).
    """
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {docx_path}")
        
    parsed = parse_docx_file(docx_path)
    output_path = write_markdown_file(parsed, output_root=output_root)
    return output_path, parsed


def convert_batch(
    docx_paths: List[str],
    output_root: str = "output_md",
    history_file: str = "conversion_history.csv",
    force: bool = False
) -> Dict[str, Any]:
    """
    Converte uma lista ou diretório de arquivos .docx em lote.
    Utiliza histórico em CSV para pular arquivos já processados previamente.
    """
    history = ConversionHistory(history_file)
    
    files_to_process = []
    
    for path in docx_paths:
        if os.path.isdir(path):
            pattern = os.path.join(path, "**", "*.docx")
            found_files = glob.glob(pattern, recursive=True)
            for f in found_files:
                if not os.path.basename(f).startswith("~$"):
                    files_to_process.append(f)
        elif os.path.isfile(path):
            if path.endswith(".docx") and not os.path.basename(path).startswith("~$"):
                files_to_process.append(path)
                
    converted_files = []
    skipped_files = []
    failed_files = []
    
    for f in files_to_process:
        if not force and history.is_processed(f):
            skipped_files.append(f)
            continue
            
        try:
            out_path, parsed = convert_single_docx(f, output_root=output_root)
            history.record(
                docx_path=f,
                output_path=out_path,
                metadata=parsed.get("metadata", {}),
                status="SUCCESS"
            )
            converted_files.append(out_path)
        except Exception as e:
            history.record(
                docx_path=f,
                output_path="",
                metadata={},
                status="ERROR",
                error_message=str(e)
            )
            failed_files.append((f, str(e)))
            
    history.save()
    
    return {
        "converted": converted_files,
        "skipped": skipped_files,
        "failed": failed_files,
        "history_file": history_file
    }
