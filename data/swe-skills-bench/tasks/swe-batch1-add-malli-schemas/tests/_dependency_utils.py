import os
import subprocess


_PREPARED = set()


def _run_once(key, command, cwd, timeout=1200):
    if key in _PREPARED:
        return
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed in {cwd}: {' '.join(command)}\n"
            f"stdout={result.stdout[-4000:]}\n"
            f"stderr={result.stderr[-4000:]}"
        )
    _PREPARED.add(key)


def ensure_npm_dependencies(repo_dir):
    package_json = os.path.join(repo_dir, "package.json")
    if not os.path.isfile(package_json):
        return
    if os.path.isfile(os.path.join(repo_dir, "package-lock.json")):
        command = ["npm", "ci", "--legacy-peer-deps"]
    else:
        command = ["npm", "install", "--legacy-peer-deps"]
    _run_once(("npm", repo_dir), command, repo_dir, timeout=1800)


def ensure_go_dependencies(repo_dir):
    go_mod = os.path.join(repo_dir, "go.mod")
    if not os.path.isfile(go_mod):
        return
    _run_once(("go", repo_dir), ["go", "mod", "download"], repo_dir, timeout=1800)


def ensure_dotnet_dependencies(repo_dir):
    solution_exists = (
        any(name.endswith((".sln", ".csproj")) for name in os.listdir(repo_dir))
        if os.path.isdir(repo_dir)
        else False
    )
    if not solution_exists:
        for root, _, files in os.walk(repo_dir):
            if any(name.endswith((".sln", ".csproj")) for name in files):
                solution_exists = True
                break
    if not solution_exists:
        return
    _run_once(("dotnet", repo_dir), ["dotnet", "restore"], repo_dir, timeout=1800)


def ensure_python_dependencies(repo_dir):
    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt",
        os.path.join("requirements", "base.txt"),
        os.path.join("requirements", "dev.txt"),
        os.path.join("requirements", "development.txt"),
    ]
    installed = False
    for relpath in requirements_files:
        fpath = os.path.join(repo_dir, relpath)
        if os.path.isfile(fpath):
            _run_once(
                ("pip-req", repo_dir, relpath),
                ["python", "-m", "pip", "install", "-r", fpath],
                repo_dir,
                timeout=1800,
            )
            installed = True
    if installed:
        return
    project_markers = ["pyproject.toml", "setup.py", "setup.cfg"]
    if any(
        os.path.isfile(os.path.join(repo_dir, marker)) for marker in project_markers
    ):
        _run_once(
            ("pip-editable", repo_dir),
            ["python", "-m", "pip", "install", "-e", "."],
            repo_dir,
            timeout=1800,
        )
