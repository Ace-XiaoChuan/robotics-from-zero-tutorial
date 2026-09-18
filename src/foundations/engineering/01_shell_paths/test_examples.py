"""验证本课最重要的可观察行为：启动目录、输入路径和环境继承。"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


UNIT_DIR = Path(__file__).resolve().parent
SAMPLE = UNIT_DIR / "data" / "joint_states.csv"


class ShellPathsTests(unittest.TestCase):
    def run_python(self, script, cwd, *args):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        )

    def test_context_reports_caller_directory_and_script_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_python(UNIT_DIR / "inspect_context.py", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"当前工作目录 cwd: {Path(tmp).resolve()}", result.stdout)
            self.assertIn(f"脚本目录: {UNIT_DIR}", result.stdout)

    def test_relative_example_succeeds_in_unit_directory(self):
        result = self.run_python(UNIT_DIR / "read_relative.py", UNIT_DIR)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(SAMPLE.read_text(), result.stdout)

    def test_relative_example_fails_in_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_python(UNIT_DIR / "read_relative.py", tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn(str(Path(tmp) / "data" / "joint_states.csv"), result.stdout)
            self.assertIn("读取失败", result.stderr)

    def test_bundled_sample_is_independent_of_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            for cwd in (UNIT_DIR, Path(tmp)):
                with self.subTest(cwd=cwd):
                    result = self.run_python(UNIT_DIR / "read_file.py", cwd)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(SAMPLE.read_text(), result.stdout)

    def test_explicit_relative_path_uses_caller_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "用户数据 sample.txt"
            custom.write_text("caller-selected-data\n", encoding="utf-8")
            result = self.run_python(UNIT_DIR / "read_file.py", tmp, "--input", custom.name)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("caller-selected-data", result.stdout)
            self.assertNotIn("time_s,joint_name", result.stdout)

    def test_absolute_input_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_python(UNIT_DIR / "read_file.py", tmp, "--input", SAMPLE)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(SAMPLE.read_text(), result.stdout)

    def test_invalid_explicit_input_fails_without_falling_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            invalid_utf8 = Path(tmp) / "binary.dat"
            invalid_utf8.write_bytes(b"\xff\xfe")
            cases = [(Path(tmp) / "missing.csv", "文件不存在"),
                     (Path(tmp), "输入是目录"),
                     (invalid_utf8, "UTF-8")]
            for path, message in cases:
                with self.subTest(path=path):
                    result = self.run_python(UNIT_DIR / "read_file.py", tmp, "--input", path)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("time_s,joint_name", result.stdout)

    def test_script_and_resources_can_move_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            moved = Path(tmp) / "课程副本 with spaces"
            (moved / "data").mkdir(parents=True)
            shutil.copy2(UNIT_DIR / "read_file.py", moved)
            shutil.copy2(SAMPLE, moved / "data")
            result = self.run_python(moved / "read_file.py", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(moved / "data" / "joint_states.csv"), result.stdout)
            self.assertIn(SAMPLE.read_text(), result.stdout)

    def test_unknown_argument_returns_usage_error(self):
        result = self.run_python(UNIT_DIR / "read_file.py", UNIT_DIR, "--unknown")
        self.assertEqual(result.returncode, 2)

    def test_export_and_source_have_the_documented_scope(self):
        env = os.environ.copy()
        env.pop("S0_LESSON_LABEL", None)
        shell_code = '''
S0_LESSON_LABEL=local-only
"$1" -c 'import os; assert "S0_LESSON_LABEL" not in os.environ'
export S0_LESSON_LABEL
"$1" -c 'import os; assert os.environ["S0_LESSON_LABEL"] == "local-only"'
bash "$2"
test "$S0_LESSON_LABEL" = local-only
source "$2"
test "$S0_LESSON_LABEL" = loaded-from-script
"$1" -c 'import os; assert os.environ["S0_LESSON_LABEL"] == "loaded-from-script"'
'''
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-e", "-c", shell_code,
             "s0-scope-test", sys.executable, str(UNIT_DIR / "set_lesson_env.sh")],
            env=env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
