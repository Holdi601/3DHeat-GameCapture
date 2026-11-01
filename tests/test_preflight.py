"""
Tests for the dependency check.

The behaviour that matters is consent: nothing may be installed without a yes,
silence must not be read as one, and a refusal must be reported rather than
worked around. Installation itself is stubbed — a test that actually ran pip
would be testing pip.
"""

from __future__ import annotations

import pytest

from heat3d_capture.runtime import preflight
from heat3d_capture.runtime.preflight import (
    MODEL_EXPORT,
    SCANNER,
    Requirement,
    describe,
    missing,
)

PRESENT = Requirement("numpy", "numpy", "arithmetic", 20)
ABSENT = Requirement("nonexistent-pkg", "definitely_not_a_real_module_xyz", "nothing", 7)
OPTIONAL = Requirement("opt-pkg", "also_not_real_xyz", "optional thing", 3, essential=False)


class TestDetection:
    def test_finds_what_is_missing(self):
        assert missing([PRESENT, ABSENT]) == [ABSENT]

    def test_an_installed_package_is_not_reported(self):
        assert missing([PRESENT]) == []

    def test_optional_things_can_be_excluded(self):
        assert missing([ABSENT, OPTIONAL], essential_only=True) == [ABSENT]
        assert set(missing([ABSENT, OPTIONAL])) == {ABSENT, OPTIONAL}

    def test_a_package_whose_import_name_differs_is_looked_up_correctly(self):
        # The trap: `pip install opencv-python` gives you `import cv2`. Checking
        # for a module called "opencv-python" would report it missing forever and
        # reinstall it on every launch.
        opencv = next(r for r in SCANNER if r.package == "opencv-python")
        assert opencv.module == "cv2"
        onnx = next(r for r in SCANNER if r.package.startswith("onnxruntime"))
        assert onnx.module == "onnxruntime"

    def test_a_broken_spec_counts_as_absent(self, monkeypatch):
        # A half-removed package can leave a spec that raises on lookup.
        def explode(name):
            raise ValueError("broken install")

        monkeypatch.setattr(preflight.importlib.util, "find_spec", explode)
        assert PRESENT.present() is False


class TestDescription:
    def test_says_nothing_is_needed_when_nothing_is(self):
        assert "already installed" in describe([])

    def test_names_every_missing_thing_and_the_total_size(self):
        text = describe([ABSENT, OPTIONAL])
        assert "nonexistent-pkg" in text and "opt-pkg" in text
        assert "10 MB" in text  # 7 + 3

    def test_explains_purpose_rather_than_package_names_alone(self):
        # "opencv-python" means nothing to someone who just wants to scan a level.
        text = describe(missing(SCANNER) or [ABSENT])
        assert "—" in text

    def test_says_where_it_will_install(self):
        # Someone is about to let a program install software. They should know
        # it is not going into their system Python.
        assert "system Python" in describe([ABSENT])

    def test_singular_and_plural_read_correctly(self):
        assert "1 thing still needed" in describe([ABSENT])
        assert "2 things still needed" in describe([ABSENT, OPTIONAL])


class TestConsent:
    @pytest.fixture
    def never_installs(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            preflight, "install", lambda absent, **kw: (calls.append(absent), (True, "ok"))[1]
        )
        return calls

    def test_nothing_missing_installs_nothing_and_asks_nothing(self, never_installs, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("must not ask"))
        assert preflight.ensure_console([PRESENT]) is True
        assert never_installs == []

    def test_a_no_installs_nothing(self, never_installs, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: "n")
        assert preflight.ensure_console([ABSENT]) is False
        assert never_installs == []

    def test_a_bare_return_is_a_yes(self, never_installs, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: "")
        assert preflight.ensure_console([ABSENT]) is True
        assert never_installs == [[ABSENT]]

    @pytest.mark.parametrize("answer", ["y", "Y", "yes", "j", "ja"])
    def test_accepts_the_obvious_yeses(self, never_installs, monkeypatch, answer):
        monkeypatch.setattr("builtins.input", lambda *_: answer)
        assert preflight.ensure_console([ABSENT]) is True

    def test_no_terminal_is_not_consent(self, never_installs, monkeypatch):
        # A double-clicked shortcut has no stdin. Silence must not be read as a
        # yes to installing software.
        def no_stdin(*_):
            raise EOFError

        monkeypatch.setattr("builtins.input", no_stdin)
        assert preflight.ensure_console([ABSENT]) is False
        assert never_installs == []

    def test_assume_yes_skips_the_question(self, never_installs, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("must not ask"))
        assert preflight.ensure_console([ABSENT], assume_yes=True) is True
        assert never_installs == [[ABSENT]]

    def test_a_failed_install_is_reported_as_failure(self, monkeypatch):
        monkeypatch.setattr(preflight, "install", lambda absent, **kw: (False, "network died"))
        monkeypatch.setattr("builtins.input", lambda *_: "y")
        assert preflight.ensure_console([ABSENT]) is False


class TestInstall:
    def test_nothing_to_do_is_a_success(self):
        assert preflight.install([]) == (True, "nothing to install")

    def test_reports_a_pip_that_will_not_start(self, monkeypatch):
        def explode(*_a, **_k):
            raise OSError("no such file")

        monkeypatch.setattr(preflight.subprocess, "Popen", explode)
        ok, message = preflight.install([ABSENT])
        assert ok is False
        assert "could not start pip" in message


class TestManifests:
    def test_the_scanner_does_not_require_torch(self):
        # The whole portability argument. Torch is a one-off conversion tool and
        # an NVIDIA-only runtime; if it ever appears here, the app has stopped
        # running on AMD.
        assert "torch" not in {r.package for r in SCANNER}

    def test_torch_is_in_the_conversion_manifest_instead(self):
        assert "torch" in {r.package for r in MODEL_EXPORT}

    def test_live_capture_is_optional(self):
        # Scanning a recorded video must work without it, including off Windows.
        capture = next(r for r in SCANNER if r.package == "windows-capture")
        assert capture.essential is False

    def test_every_requirement_explains_itself_and_has_a_size(self):
        for requirement in SCANNER + MODEL_EXPORT:
            assert requirement.purpose and not requirement.purpose[0].isupper()
            assert requirement.megabytes > 0


class TestThePlatformsBuild:
    def test_the_runtime_matches_what_requirements_txt_installs(self, monkeypatch):
        # requirements.txt installs onnxruntime-directml on Windows only; the
        # check offered it everywhere, where pip has no such package.
        import importlib
        import sys

        for platform, expected in (("win32", "onnxruntime-directml"), ("linux", "onnxruntime")):
            monkeypatch.setattr(sys, "platform", platform)
            reloaded = importlib.reload(preflight)
            assert reloaded.ONNXRUNTIME == expected
            assert expected in {r.package for r in reloaded.SCANNER}
        monkeypatch.undo()
        importlib.reload(preflight)


class TestTheOfflinePath:
    def test_it_names_what_reconstruct_imports(self):
        from heat3d_capture.runtime.preflight import OFFLINE

        modules = {r.module for r in OFFLINE}
        assert {"torch", "transformers", "vggt"} <= modules
        for requirement in OFFLINE:
            assert requirement.purpose and not requirement.purpose[0].isupper()
            assert requirement.megabytes > 0

    def test_vggt_comes_without_its_numpy_pin(self, monkeypatch):
        from heat3d_capture.runtime.preflight import OFFLINE

        commands = []

        class Done:
            stdout = iter(())

            def wait(self):
                return 0

        def record(command, **_):
            commands.append(command)
            return Done()

        monkeypatch.setattr(preflight.subprocess, "Popen", record)
        ok, _ = preflight.install(OFFLINE)
        assert ok
        assert len(commands) == 2
        assert "--no-deps" not in commands[0]
        assert commands[1][-2:] == [f"vggt @ {preflight.VGGT_SOURCE}", "--no-deps"]

    def test_the_offline_requirements_file_lists_the_same(self):
        from pathlib import Path

        from heat3d_capture.runtime.preflight import OFFLINE

        text = (Path(__file__).resolve().parents[1] / "requirements-offline.txt").read_text(encoding="utf-8")
        for requirement in OFFLINE:
            if requirement.package != "torch" and not requirement.no_deps:
                assert requirement.package in text, requirement.package
        assert "facebookresearch/vggt" in text and "--no-deps" in text
