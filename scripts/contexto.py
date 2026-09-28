"""Consultas compactas locais; sem shell, API, hooks ou dependencias externas."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def local_path(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("O caminho precisa permanecer dentro do projeto.")
    return path


def compact(text: str, limit: int = 6000, lines: int = 80) -> str:
    return "".join(text.splitlines(keepends=True)[:lines])[:limit]


def run_read(command: list[str], root: Path) -> tuple[str, int]:
    result = subprocess.run(
        command, cwd=root, capture_output=True, encoding="utf-8",
        errors="replace", shell=False,
    )
    output = result.stdout
    if result.stderr:
        output += "\n[stderr]\n" + result.stderr
    return output, result.returncode


def render(output: str, code: int, label: str, root: Path) -> str:
    # Falhas permanecem completas; o resumo sempre aponta para o original.
    shortened = compact(output) if code == 0 else output
    record_id = uuid.uuid4().hex
    notice = f"\n[Saida parcial. Completa: python scripts/contexto.py original {record_id}]\n"
    shown = shortened + notice if len(shortened) < len(output) else output
    if len(shown) >= len(output):
        shown = output
    try:
        folder = local_path(root, "data/contexto")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{record_id}.txt").write_text(output, encoding="utf-8")
        record = {
            "id": record_id, "data": datetime.now(timezone.utc).isoformat(),
            "consulta": label, "codigo": code,
            "caracteres_originais": len(output), "caracteres_exibidos": len(shown),
        }
        with (folder / "historico.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        return output  # Sem arquivo completo confiavel, nao cortar a resposta.
    return shown


def measure(root: Path) -> dict:
    previous = (root / "docs/system/referencia-agente-completa.md").read_text(encoding="utf-8")
    current = (root / "AGENTS.md").read_text(encoding="utf-8")
    shared = sum(len((root / item).read_text(encoding="utf-8")) for item in (
        "memory/MEMORY.md", "marketing/memory/README.md",
    ))
    before, after = len(previous) + shared, len(current) + shared
    return {
        "escopo": "AGENTS.md + dois indices obrigatorios; sem skills, conversa ou ferramentas",
        "agente_antes_caracteres": len(previous), "agente_depois_caracteres": len(current),
        "inicio_antes_caracteres": before, "inicio_depois_caracteres": after,
        "reducao_contexto_inicial_percentual": round(100 * (before - after) / before, 1),
        "tokens_antes_estimativa": round(before / 4),
        "tokens_depois_estimativa": round(after / 4),
        "metodo": "caracteres/4 e aproximacao, nao tokenizacao nem economia faturada",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subs = result.add_subparsers(dest="action", required=True)
    subs.add_parser("status", help="Git status curto, incluindo branch")
    diff = subs.add_parser("diff", help="Resumo do diff; --completo mostra conteudo")
    diff.add_argument("path", nargs="?")
    diff.add_argument("--completo", action="store_true")
    diff.add_argument("--staged", action="store_true")
    subs.add_parser("log", help="Ultimos dez commits, uma linha por commit")
    search = subs.add_parser("buscar", help="Busca literal com ripgrep, limitada ao caminho")
    search.add_argument("term")
    search.add_argument("path")
    read = subs.add_parser("ler", help="Trecho numerado; usar --inicio e --linhas para continuar")
    read.add_argument("path")
    read.add_argument("--inicio", type=int, default=1)
    read.add_argument("--linhas", type=int, default=60)
    original = subs.add_parser("original", help="Saida integral de uma consulta pelo ID")
    original.add_argument("id")
    subs.add_parser("estatisticas", help="Caracteres realmente omitidos nas consultas locais")
    subs.add_parser("medir", help="Comparacao do contexto inicial, nao da fatura")
    return result


def execute(args: argparse.Namespace, root: Path) -> tuple[str, int]:
    action = args.action
    if action == "status":
        return run_read(["git", "--no-optional-locks", "status", "--short", "--branch"], root)
    if action == "log":
        return run_read(["git", "--no-pager", "log", "-10", "--oneline"], root)
    if action == "diff":
        command = ["git", "--no-pager", "diff", "--no-ext-diff", "--no-textconv"]
        if args.staged:
            command.append("--cached")
        command.append("--unified=3" if args.completo else "--stat")
        if args.path:
            command.extend(["--", str(local_path(root, args.path))])
        return run_read(command, root)
    if action == "buscar":
        return run_read(["rg", "-n", "-F", "--", args.term, str(local_path(root, args.path))], root)
    if action == "ler":
        if args.inicio < 1 or not 1 <= args.linhas <= 200:
            raise ValueError("Inicio >= 1; linhas entre 1 e 200.")
        path = local_path(root, args.path)
        rows = path.read_text(encoding="utf-8-sig").splitlines()
        start = args.inicio - 1
        end = min(start + args.linhas, len(rows))
        header = f"{args.path}: trecho solicitado; total {len(rows)} linhas\n"
        return header + "".join(f"{i + 1}: {rows[i]}\n" for i in range(start, end)), 0
    raise ValueError("Consulta desconhecida.")


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    args = parser().parse_args(argv)
    try:
        if args.action == "medir":
            print(json.dumps(measure(root), ensure_ascii=False, indent=2))
            return 0
        if args.action == "original":
            if len(args.id) != 32 or any(c not in "0123456789abcdef" for c in args.id):
                raise ValueError("ID de consulta invalido.")
            path = local_path(root, f"data/contexto/{args.id}.txt")
            print(path.read_text(encoding="utf-8"), end="")
            return 0
        if args.action == "estatisticas":
            path = local_path(root, "data/contexto/historico.jsonl")
            records = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
            before = sum(row["caracteres_originais"] for row in records)
            after = sum(row["caracteres_exibidos"] for row in records)
            print(json.dumps({"consultas": len(records), "caracteres_originais": before,
                              "caracteres_exibidos": after, "caracteres_omitidos": before - after,
                              "nota": "Nao mede tokens cobrados, nem consultas nativas fora deste comando."},
                             ensure_ascii=False, indent=2))
            return 0
        output, code = execute(args, root)
        print(render(output, code, args.action, root), end="")
        return code
    except (OSError, ValueError) as exc:
        print(f"Erro: {exc}. Use o comando nativo se necessario.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
