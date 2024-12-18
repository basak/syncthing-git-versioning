# Copyright 2024 Robie Basak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Dependencies: pytest, git, git-annex

import itertools
import os
import pathlib
import shutil
import subprocess
import tempfile
import types

import pytest


GIT_ENV = dict(os.environ)
GIT_ENV.update(
    GIT_AUTHOR_NAME="test",
    GIT_AUTHOR_EMAIL="test@example.com",
    GIT_COMMITTER_NAME="test",
    GIT_COMMITTER_EMAIL="test@example.com",
)


@pytest.fixture
def test_paths(tmp_path):
    elements = ["git", "other", "sync", "bin"]
    paths = types.SimpleNamespace(**{x: (tmp_path / x) for x in elements})
    for e in elements:
        os.mkdir(getattr(paths, e))
    subprocess.check_call(["git", "init"], cwd=paths.git)
    return paths


def call_target(test_paths, file_path, env=None):
    subprocess.check_call(
        [
            os.path.join(
                os.path.dirname(__file__), "syncthing-git-versioning"
            ),
            test_paths.git,
            test_paths.sync,
            file_path,
        ],
        cwd=test_paths.other,
        env=env,
    )


@pytest.mark.parametrize(["annex"], [(False,), (True,)])
def test_single_file(annex, test_paths):
    if annex:
        subprocess.check_call(["git", "annex", "init"], cwd=test_paths.git)
    (test_paths.sync / "target").write_text("content")
    call_target(test_paths, "target")
    subprocess.check_call(["git", "reset", "--hard"], cwd=test_paths.git)
    subprocess.check_call(["git", "clean", "-ffxd"], cwd=test_paths.git)
    assert (test_paths.git / "target").read_text() == "content"
    assert (test_paths.git / "target").is_symlink() == annex


@pytest.mark.parametrize(["annex"], [(False,), (True,)])
def test_no_change(annex, test_paths):
    if annex:
        subprocess.check_call(["git", "annex", "init"], cwd=test_paths.git)
    (test_paths.sync / "target").write_text("content")
    call_target(test_paths, "target")
    (test_paths.sync / "target").write_text("content")
    call_target(test_paths, "target")
    subprocess.check_call(["git", "reset", "--hard"], cwd=test_paths.git)
    subprocess.check_call(["git", "clean", "-ffxd"], cwd=test_paths.git)
    assert (test_paths.git / "target").read_text() == "content"
    assert (test_paths.git / "target").is_symlink() == annex


DIR_VARIETIES = [".", "foo", "foo/foo"]
FILE_VARIETIES = [None, "foo"]
INITIAL_VARIATIONS = [(d, f) for d in DIR_VARIETIES for f in FILE_VARIETIES]
# FINAL_VARIATIONS doesn't include the None file variety since the hook would
# never get called unless there is a file to call it against.
FINAL_VARIATIONS = [(d, "foo") for d in DIR_VARIETIES]
PERMUTATIONS = [(i, f) for i in INITIAL_VARIATIONS for f in FINAL_VARIATIONS]


def inject_variation(top_dir, variation, content, git_commit=False):
    dir_path, file_path = variation
    os.makedirs(top_dir / dir_path, exist_ok=True)
    if file_path is not None:
        (top_dir / dir_path / file_path).write_text(content)
        if git_commit:
            subprocess.check_call(["git", "add", "-A"], cwd=top_dir)
            subprocess.check_call(
                ["git", "commit", "-mtest"], cwd=top_dir, env=GIT_ENV
            )


@pytest.mark.parametrize(["initial", "final"], PERMUTATIONS)
def test_permutation(initial, final, test_paths):
    inject_variation(test_paths.git, initial, "content1", git_commit=True)
    inject_variation(test_paths.sync, final, "content2")
    call_target(test_paths, pathlib.Path(final[0]) / final[1])
    subprocess.check_call(["git", "reset", "--hard"], cwd=test_paths.git)
    subprocess.check_call(["git", "clean", "-ffxd"], cwd=test_paths.git)
    assert (test_paths.git / final[0] / final[1]).read_text() == "content2"


def test_git_commit_failure(test_paths):
    """When git commit fails, original file should continue to exist

    If there is an unexpected problem, we need to relay that through Syncthing
    back to the user. If we fail to commit, we do exit non-zero. But Syncthing
    seems to ignore this and continue anyway. To get Syncthing to fail, we also
    need to ensure that the original file still exists.
    """
    wrap_env = dict(os.environ)
    wrap_env["ORIG_GIT_PATH"] = shutil.which("git")

    git_wrapper_path = test_paths.bin / "git"
    git_wrapper_path.write_text(
        """#!/bin/sh
echo "Wrapper called" >&2
if [ "$1" = "commit" ]; then
    echo "Wrapper detected commit subcommand; failing deliberately for test" >&2
    exit 1
fi
echo "Wrapper execing the real git at $ORIG_GIT_PATH" >&2
exec "$ORIG_GIT_PATH" "$@"
"""
    )
    git_wrapper_path.chmod(0o755)
    wrap_env["PATH"] = f"{test_paths.bin}:{wrap_env['PATH']}"

    (test_paths.sync / "target").write_text("content")
    with pytest.raises(subprocess.CalledProcessError):
        call_target(test_paths, "target", env=wrap_env)
    assert (test_paths.sync / "target").exists()


def test_cross_filesystem(test_paths):
    """Test basic functionality if Syncthing folder and git repository are on
    different filesystems.

    This is relevant since we try to use hardlinks in
    our implementation, and hardlinks across filesystems are not permitted.
    """
    if "XDG_RUNTIME_DIR" not in os.environ:
        pytest.skip("XDG_RUNTIME_DIR unset")
    runtime_dir = pathlib.Path(os.environ["XDG_RUNTIME_DIR"])
    if test_paths.sync.stat().st_dev == runtime_dir.stat().st_dev:
        pytest.skip("$XDG_RUNTIME_DIR is not on a separate filesystem")
    with tempfile.TemporaryDirectory(dir=runtime_dir) as tmpdir:
        test_paths.sync = pathlib.Path(tmpdir)
        (test_paths.sync / "target").write_text("content")
        call_target(test_paths, "target")
        subprocess.check_call(["git", "reset", "--hard"], cwd=test_paths.git)
        subprocess.check_call(["git", "clean", "-ffxd"], cwd=test_paths.git)
        assert (test_paths.git / "target").read_text() == "content"
