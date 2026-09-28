"""Testes sem dependencias para o leitor compacto de contexto."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import contexto


class ContextoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_short_output_is_unchanged(self):
        self.assertEqual(contexto.render("ok\n", 0, "status", self.root), "ok\n")

    def test_truncated_output_is_recoverable_and_counted(self):
        text = "linha de conteudo\n" * 1000
        shown = contexto.render(text, 0, "ler", self.root)
        self.assertLess(len(shown), len(text))
        folder = self.root / "data/contexto"
        record = json.loads((folder / "historico.jsonl").read_text(encoding="utf-8"))
        self.assertIn(record["id"], shown)
        self.assertEqual(record["caracteres_exibidos"], len(shown))
        result = io.StringIO()
        with contextlib.redirect_stdout(result):
            self.assertEqual(contexto.main(["original", record["id"]], self.root), 0)
        self.assertEqual(result.getvalue(), text)

    def test_errors_are_not_truncated(self):
        text = "erro\n" * 1000
        self.assertEqual(contexto.render(text, 3, "buscar", self.root), text)

    def test_failed_archive_returns_full_output(self):
        text = "conteudo\n" * 1000
        with patch.object(Path, "mkdir", side_effect=OSError("indisponivel")):
            self.assertEqual(contexto.render(text, 0, "ler", self.root), text)

    def test_rejects_path_outside_workspace(self):
        with self.assertRaises(ValueError):
            contexto.local_path(self.root, "../arquivo")

    def test_rejects_invalid_archive_id(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(contexto.main(["original", "../segredo"], self.root), 2)

    def test_literal_search_does_not_invoke_shell(self):
        parsed = contexto.parser().parse_args(["buscar", "$(echo teste); -h", "."])
        result = subprocess.CompletedProcess([], 1, "", "erro de busca")
        with patch.object(subprocess, "run", return_value=result) as call:
            output, code = contexto.execute(parsed, self.root)
        self.assertEqual(code, 1)
        self.assertIn("erro de busca", output)
        self.assertFalse(call.call_args.kwargs["shell"])
        self.assertEqual(call.call_args.args[0][3:5], ["--", "$(echo teste); -h"])

    def test_diff_preserves_staging_and_file_scope(self):
        parsed = contexto.parser().parse_args(["diff", "a b.txt", "--staged", "--completo"])
        with patch.object(contexto, "run_read", return_value=("", 0)) as call:
            contexto.execute(parsed, self.root)
        command = call.call_args.args[0]
        self.assertIn("--cached", command)
        self.assertIn("--no-ext-diff", command)
        self.assertEqual(command[-2:], ["--", str(self.root / "a b.txt")])

    def test_read_range_has_line_numbers_and_total(self):
        (self.root / "exemplo.md").write_text("primeira\nsegunda\nterceira\n", encoding="utf-8")
        args = contexto.parser().parse_args(["ler", "exemplo.md", "--inicio", "2", "--linhas", "1"])
        text, code = contexto.execute(args, self.root)
        self.assertEqual(code, 0)
        self.assertIn("total 3 linhas", text)
        self.assertTrue(text.endswith("2: segunda\n"))

    def test_native_error_code_survives_main(self):
        with patch.object(contexto, "execute", return_value=("falhou\n", 7)):
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(contexto.main(["status"], self.root), 7)
        self.assertEqual(stream.getvalue(), "falhou\n")

    def test_measure_is_characters_not_billed_tokens(self):
        for name, text in [("AGENTS.md", "novo"), ("docs/system/referencia-agente-completa.md", "x" * 100),
                           ("memory/MEMORY.md", "indice"), ("marketing/memory/README.md", "marca")]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        result = contexto.measure(self.root)
        self.assertEqual(result["inicio_depois_caracteres"], 15)
        self.assertIn("nao tokenizacao", result["metodo"])


if __name__ == "__main__":
    unittest.main()
