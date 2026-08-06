import sys
import os
import argparse
from docx_md_converter import convert_batch

def main():
    parser = argparse.ArgumentParser(
        description="Conversor em lote incremental de arquivos .docx para .md com controle via CSV."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Caminhos de arquivos .docx ou diretórios para conversão. Se omitido, busca na pasta 'input_docx'."
    )
    parser.add_argument(
        "-o", "--output",
        default="output_md",
        help="Diretório raiz de saída para salvar os arquivos .md (Padrão: output_md)."
    )
    parser.add_argument(
        "-hist", "--history",
        default="conversion_history.csv",
        help="Caminho do arquivo CSV para controle de histórico (Padrão: conversion_history.csv)."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Força o reprocessamento de todos os arquivos, ignorando o histórico."
    )

    args = parser.parse_args()

    inputs = args.inputs
    if not inputs:
        default_dir = "input_docx"
        if os.path.exists(default_dir):
            inputs = [default_dir]
            print(f"Nenhum caminho especifico informado. Buscando arquivos na pasta '{default_dir}'...")
        else:
            os.makedirs(default_dir, exist_ok=True)
            print(f"Nenhum arquivo especificado. A pasta '{default_dir}' foi criada.")
            print(f"Coloque seus arquivos .docx dentro de '{default_dir}' e execute novamente:")
            print("  python convert.py")
            sys.exit(0)

    print(f"Iniciando conversao incremental para a pasta de saida '{args.output}'...")
    if args.force:
        print("Modo '--force' ativo: Todos os arquivos serao reprocessados.")

    results = convert_batch(
        inputs,
        output_root=args.output,
        history_file=args.history,
        force=args.force
    )
    
    converted = results["converted"]
    skipped = results["skipped"]
    failed = results["failed"]
    
    print("\n--- RESUMO DA EXECUCAO ---")
    print(f" Novos convertidos: {len(converted)}")
    print(f" Pulados (ja convertidos): {len(skipped)}")
    if failed:
        print(f" Falhas: {len(failed)}")
    print(f" Historico atualizado em: {args.history}\n")
    
    if converted:
        print("Arquivos gerados nesta rodada:")
        for path in converted:
            print(f"  [CONVERTIDO] -> {path}")

    if failed:
        print("\nArquivos com erro:")
        for f, err in failed:
            print(f"  [ERRO] {f}: {err}")

if __name__ == "__main__":
    main()
