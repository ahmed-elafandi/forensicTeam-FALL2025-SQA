import os
import random
import string
import tempfile
import shutil
import traceback
from datetime import datetime
import ast
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FAME_ML_DIR = os.path.join(THIS_DIR, "MLForensics-farzana", "FAME-ML")
sys.path.append(FAME_ML_DIR)

import py_parser
import lint_engine
import main


CRASH_LOG_FILE = os.path.join(THIS_DIR, "fuzz_crashes.log")


def log_crash(func_name, args, kwargs, exc):
    """Append crash info to fuzz_crashes.log"""
    with open(CRASH_LOG_FILE, "a", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Time: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"Function: {func_name}\n")
        f.write(f"Args: {repr(args)}\n")
        f.write(f"Kwargs: {repr(kwargs)}\n")
        f.write("Exception:\n")
        f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        f.write("\n\n")


def random_string(max_len=40):
    length = random.randint(0, max_len)
    letters = string.ascii_letters + string.digits + "_-"
    return "".join(random.choice(letters) for _ in range(length))


def make_temp_py_file(content=None):
    if content is None:
        # generate a *valid* tiny Python snippet most of the time
        snippets = [
            "x = 1\n",
            "def foo(a, b):\n    return a + b\n",
            "import logging\nlogging.info('hi')\n",
            "try:\n    1/0\nexcept Exception as e:\n    pass\n",
        ]
        content = random.choice(snippets)
    tmp_dir = tempfile.mkdtemp(prefix="mlforensics_fuzz_")
    path = os.path.join(tmp_dir, "test_file.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp_dir, path


def random_ast_tree():
    if random.random() < 0.7:
        code = "x = 1\n" * random.randint(1, 5)
    else:
        code = random_string()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = ast.parse("")  # fallback to empty tree
    return tree


def fuzz_function(func, name, make_args, iterations=200):
    for i in range(iterations):
        args, kwargs = make_args()
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"[!] Crash in {name} at iteration {i}")
            log_crash(name, args, kwargs, e)


def main_fuzz():
    print("[*] Starting fuzzing run")

    def args_getPythonParseObject():
        if random.random() < 0.5:
            tmp_dir, py_path = make_temp_py_file()
            # clean up directory after this call, so track it in args
            return ([py_path], {"_tmp_dir": tmp_dir})
        else:
            fake_path = random_string() + ".py"
            return ([fake_path], {})

    def wrapper_getPythonParseObject(py_file, _tmp_dir=None):
        try:
            return py_parser.getPythonParseObject(py_file)
        finally:
            if _tmp_dir and os.path.isdir(_tmp_dir):
                shutil.rmtree(_tmp_dir, ignore_errors=True)

    fuzz_function(
        lambda *a, **k: wrapper_getPythonParseObject(*a, **k),
        "py_parser.getPythonParseObject",
        args_getPythonParseObject,
        iterations=200,
    )

    # 2) py_parser.checkLoggingPerData(tree_object, name2track)
    def args_checkLoggingPerData():
        tree = random_ast_tree()
        name = random.choice(["data", "model", random_string(10)])
        return ([tree, name], {})

    fuzz_function(
        py_parser.checkLoggingPerData,
        "py_parser.checkLoggingPerData",
        args_checkLoggingPerData,
        iterations=200,
    )

    # 3) lint_engine.getDataLoadCount(py_file)
    def args_getDataLoadCount():
        # reuse temp file strategy
        if random.random() < 0.5:
            tmp_dir, py_path = make_temp_py_file()
            return ([py_path], {"_tmp_dir": tmp_dir})
        else:
            fake_path = random_string() + ".py"
            return ([fake_path], {})

    def wrapper_getDataLoadCount(py_file, _tmp_dir=None):
        try:
            return lint_engine.getDataLoadCount(py_file)
        finally:
            if _tmp_dir and os.path.isdir(_tmp_dir):
                shutil.rmtree(_tmp_dir, ignore_errors=True)

    fuzz_function(
        lambda *a, **k: wrapper_getDataLoadCount(*a, **k),
        "lint_engine.getDataLoadCount",
        args_getDataLoadCount,
        iterations=200,
    )

    # 4) main.getAllPythonFilesinRepo(path2dir)
    def args_getAllPythonFilesinRepo():
        if random.random() < 0.5:
            # folder with several random py / txt files
            tmp_dir = tempfile.mkdtemp(prefix="mlforensics_repo_")
            for i in range(random.randint(0, 5)):
                fname = f"file_{i}.py"
                with open(os.path.join(tmp_dir, fname), "w", encoding="utf-8") as f:
                    f.write("x = 1\n")
            return ([tmp_dir], {"_tmp_dir": tmp_dir})
        else:
            fake_dir = random_string()
            return ([fake_dir], {})

    def wrapper_getAllPythonFilesinRepo(path2dir, _tmp_dir=None):
        try:
            return main.getAllPythonFilesinRepo(path2dir)
        finally:
            if _tmp_dir and os.path.isdir(_tmp_dir):
                shutil.rmtree(_tmp_dir, ignore_errors=True)

    fuzz_function(
        lambda *a, **k: wrapper_getAllPythonFilesinRepo(*a, **k),
        "main.getAllPythonFilesinRepo",
        args_getAllPythonFilesinRepo,
        iterations=200,
    )

    # 5) main.getCSVData(dic_, dir_repo)
    def args_getCSVData():
        # dic_ is expected to be an iterable of script paths
        # create a small fake set of paths (some existing, some not)
        scripts = []
        tmp_dirs = []
        for _ in range(random.randint(0, 4)):
            if random.random() < 0.5:
                tmp_dir, py_path = make_temp_py_file()
                tmp_dirs.append(tmp_dir)
                scripts.append(py_path)
            else:
                scripts.append(random_string() + ".py")
        dir_repo = random_string(15)
        return ([scripts, dir_repo], {"_tmp_dirs": tmp_dirs})

    def wrapper_getCSVData(dic_, dir_repo, _tmp_dirs=None):
        try:
            return main.getCSVData(dic_, dir_repo)
        finally:
            if _tmp_dirs:
                for d in _tmp_dirs:
                    if os.path.isdir(d):
                        shutil.rmtree(d, ignore_errors=True)

    fuzz_function(
        lambda *a, **k: wrapper_getCSVData(*a, **k),
        "main.getCSVData",
        args_getCSVData,
        iterations=200,
    )

    print("[*] Fuzzing run complete. Check fuzz_crashes.log for any crashes.")


if __name__ == "__main__":
    main_fuzz()
