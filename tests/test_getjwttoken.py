import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import parse_qs


SCRIPT = Path(__file__).resolve().parents[1] / "getjwttoken"
MOCK_COMMAND = r'''
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote_plus

root = Path(os.environ["MOCK_DIR"])
settings = json.loads(os.environ["MOCK_SETTINGS"])
command = Path(sys.argv[0]).name
args = sys.argv[1:]
record = {"command": command, "args": args}
if command == "curl":
    fields = []
    for index, arg in enumerate(args[:-1]):
        if arg == "--data-urlencode":
            name, value = args[index + 1].split("=", 1)
            fields.append(name + "=" + quote_plus(value))
        elif arg in ("-d", "--data"):
            fields.append(args[index + 1])
    record["body"] = "&".join(fields)
with (root / "calls.jsonl").open("a") as log:
    log.write(json.dumps(record) + "\n")

if command == "security":
    account = args[args.index("-a") + 1]
    field = account.removeprefix("getjwttoken_")
    if args[0] == "find-generic-password":
        sys.stdout.write(settings.get(field, "mock-" + field))
        sys.exit(settings.get("read_" + field + "_exit", 0))
    sys.exit(settings.get("save_" + field + "_exit", 0))
elif command == "curl":
    sys.stdout.write(settings.get("response", "mock-token"))
    if "--write-out" in args:
        template = args[args.index("--write-out") + 1]
        sys.stdout.write(template.replace("%{http_code}", settings.get("http_status", "200")))
    sys.exit(settings.get("curl_exit", 0))
elif command == "pbcopy":
    data = sys.stdin.buffer.read()
    if settings.get("pbcopy_exit", 0):
        sys.exit(settings["pbcopy_exit"])
    (root / "clipboard").write_bytes(data)
'''


class GetJwtTokenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="getjwttoken-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clipboard = self.root / "clipboard"
        self.clipboard.write_bytes(b"previous clipboard")
        for name in ("security", "curl", "pbcopy"):
            command = self.root / name
            command.write_text("#!" + sys.executable + "\n" + MOCK_COMMAND)
            command.chmod(0o700)

    def mock_environment(self, settings=None):
        return dict(
            os.environ,
            PATH=str(self.root) + os.pathsep + os.defpath,
            MOCK_DIR=str(self.root),
            MOCK_SETTINGS=json.dumps(settings or {}),
        )

    def run_script(self, settings=None, config_input=None, args=(), script=SCRIPT, env_extra=None):
        (self.root / "calls.jsonl").write_text("")
        self.clipboard.write_bytes(b"previous clipboard")
        command = ["/bin/bash", str(script), *args]
        if config_input is not None:
            command.append("--config")
        return subprocess.run(
            command,
            input=config_input or "",
            text=True,
            capture_output=True,
            env=dict(self.mock_environment(settings), **(env_extra or {})),
            timeout=10,
        )

    def calls(self, command):
        return [
            call
            for line in (self.root / "calls.jsonl").read_text().splitlines()
            if (call := json.loads(line))["command"] == command
        ]

    def assert_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)
        self.assertNotIn("successfully", result.stdout)
        self.assertNotIn("has been copied", result.stdout)

    def assert_no_copy(self):
        self.assertEqual(self.calls("pbcopy"), [])
        self.assertEqual(self.clipboard.read_bytes(), b"previous clipboard")

    def test_config_preserves_literal_credentials(self):
        username = "  mock\\user+name@example.com  "
        password = "  mock\\pass&word+%21  "
        result = self.run_script(config_input=username + "\n" + password + "\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        writes = self.calls("security")
        self.assertEqual(len(writes), 2)
        saved = [call["args"][call["args"].index("-w") + 1] for call in writes]
        self.assertEqual(saved, [username, password])

    def test_config_rejects_empty_or_interrupted_input(self):
        for value in ("", "mock-user\n", "\nmock-pass\n", "mock-user\n\n"):
            with self.subTest(input=value):
                self.assert_failure(self.run_script(config_input=value))
                self.assertEqual(self.calls("security"), [])

    def test_config_reports_each_keychain_write_failure(self):
        for field, expected_writes in (("username", 1), ("password", 2)):
            with self.subTest(field=field):
                result = self.run_script(
                    {"save_" + field + "_exit": 1}, config_input="mock-user\nmock-pass\n"
                )
                self.assert_failure(result)
                self.assertEqual(len(self.calls("security")), expected_writes)

    def test_credentials_are_form_encoded(self):
        credentials = {"username": "mock+user@example.com", "password": " \\&+=%!?é "}
        result = self.run_script(credentials)
        self.assertEqual(result.returncode, 0, result.stderr)
        submitted = parse_qs(self.calls("curl")[0]["body"])
        self.assertEqual(submitted, {**{k: [v] for k, v in credentials.items()}, "token": ["true"]})

    def test_keychain_read_errors_stop_request(self):
        for field in ("username", "password"):
            for settings in ({"read_" + field + "_exit": 1}, {field: ""}):
                with self.subTest(settings=settings):
                    self.assert_failure(self.run_script(settings))
                    self.assertEqual(self.calls("curl"), [])
                    self.assert_no_copy()

    def test_transport_errors_preserve_clipboard(self):
        for code in (7, 28, 60):
            with self.subTest(code=code):
                self.assert_failure(self.run_script({"curl_exit": code, "response": "partial response"}))
                self.assert_no_copy()

    def test_http_errors_preserve_clipboard(self):
        for status in ("000", "302", "400", "401", "403", "500", "503"):
            with self.subTest(status=status):
                result = self.run_script({"http_status": status, "response": "error body"})
                self.assert_failure(result)
                self.assertIn(status, result.stderr)
                self.assert_no_copy()

    def test_empty_response_preserves_clipboard(self):
        for response in ("", "\n"):
            with self.subTest(response=response):
                self.assert_failure(self.run_script({"response": response}))
                self.assert_no_copy()

    def test_clipboard_failure_is_reported(self):
        self.assert_failure(self.run_script({"pbcopy_exit": 1}))

    def test_success_copies_literal_response_without_trailing_newline(self):
        for response in ("mock.jwt.token", "mock.jwt.token\n", r"-n\\mock%token"):
            with self.subTest(response=response):
                result = self.run_script({"response": response, "http_status": "201"})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("has been copied", result.stdout)
                self.assertEqual(self.clipboard.read_bytes(), response.rstrip("\n").encode())

    def test_print_outputs_only_token_without_copying(self):
        for option in ("-p", "--print"):
            with self.subTest(option=option):
                result = self.run_script({"response": "mock.jwt.token\n"}, args=(option,))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "mock.jwt.token\n")
                self.assertEqual(result.stderr, "")
                self.assert_no_copy()

    def test_print_errors_have_no_stdout(self):
        for settings in ({"curl_exit": 28}, {"http_status": "401"}, {"response": ""}, {"read_password_exit": 1}):
            with self.subTest(settings=settings):
                result = self.run_script(settings, args=("--print",))
                self.assert_failure(result)
                self.assertEqual(result.stdout, "")
                self.assert_no_copy()

    def test_explicit_copy_mode(self):
        result = self.run_script(args=("--copy",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.clipboard.read_bytes(), b"mock-token")

    def test_help_does_not_fetch_token(self):
        for option in ("-h", "--help"):
            with self.subTest(option=option):
                result = self.run_script(args=(option,))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--install-profile", result.stdout)
                self.assertIn("--print", result.stdout)
                self.assertEqual(self.calls("security"), [])
                self.assertEqual(self.calls("curl"), [])
                self.assert_no_copy()

    def test_invalid_options_do_not_fetch_token(self):
        for args in (("--unknown",), ("--print", "--copy"), ("--config", "extra"), ("--install-profile", "A", "B", "C")):
            with self.subTest(args=args):
                result = self.run_script(args=args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.calls("security"), [])
                self.assertEqual(self.calls("curl"), [])
                self.assert_no_copy()

    def test_profile_install_preserves_content_and_is_idempotent(self):
        profile = self.root / ".zshrc"
        original = "# existing config\nexport EXISTING_SETTING=kept"
        profile.write_text(original)
        args = ("--install-profile", "MY_TOKEN", str(profile))
        result = self.run_script(args=args)
        self.assertEqual(result.returncode, 0, result.stderr)
        installed = profile.read_text()
        self.assertTrue(installed.startswith(original + "\n"))
        self.assertIn("export MY_TOKEN", installed)
        self.assertNotIn("mock-token", installed)
        self.assertEqual(self.calls("security"), [])
        self.assertEqual(self.calls("curl"), [])
        self.assertEqual(self.run_script(args=args).returncode, 0)
        self.assertEqual(profile.read_text(), installed)

    def test_profile_defaults_use_zdotdir_and_my_token(self):
        result = self.run_script(args=("--install-profile",), env_extra={"ZDOTDIR": str(self.root)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("export MY_TOKEN", (self.root / ".zshrc").read_text())

    def test_profile_rejects_invalid_and_reserved_variable_names(self):
        profile = self.root / ".zshrc"
        for variable in ("", "MY-TOKEN", "1TOKEN", "TOKEN;touch injected", "PATH", "HOME", "home", "CODEX_HOME"):
            with self.subTest(variable=variable):
                self.assert_failure(self.run_script(args=("--install-profile", variable, str(profile))))
                self.assertFalse(profile.exists())

    def test_profile_rejects_incomplete_managed_block(self):
        profile = self.root / ".zshrc"
        original = "# >>> getjwttoken: MY_TOKEN >>>\n"
        profile.write_text(original)
        self.assert_failure(self.run_script(args=("--install-profile", "MY_TOKEN", str(profile))))
        self.assertEqual(profile.read_text(), original)

    def test_profile_reports_invalid_destination(self):
        for profile in (self.root, self.root / "missing-parent" / ".zshrc"):
            with self.subTest(profile=profile):
                self.assert_failure(self.run_script(args=("--install-profile", "MY_TOKEN", str(profile))))

    @unittest.skipUnless(shutil.which("zsh"), "zsh is required to verify profile loading")
    def test_profile_exports_token_to_child_process_and_unsets_on_failure(self):
        # Exercise quoting with shell metacharacters in the command's actual path.
        tool_dir = self.root / "tool's $(not-a-command)"
        tool_dir.mkdir()
        script = tool_dir / "getjwttoken"
        shutil.copy2(SCRIPT, script)
        profile = self.root / "profile with spaces"
        result = self.run_script(args=("--install-profile", "MY_TOKEN", str(profile)), script=script)
        self.assertEqual(result.returncode, 0, result.stderr)
        for settings, expected in (({}, "mock-token"), ({"http_status": "401"}, "<unset>"), ({"curl_exit": 28}, "<unset>")):
            with self.subTest(settings=settings):
                result = subprocess.run(
                    [
                        shutil.which("zsh"), "-f", "-c",
                        'source "$1"; "$2" -c \'import os, sys; sys.stdout.write(os.environ.get("MY_TOKEN", "<unset>"))\'',
                        "--", str(profile), sys.executable,
                    ],
                    text=True,
                    capture_output=True,
                    env=dict(self.mock_environment(settings), MY_TOKEN="stale-token"),
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assert_no_copy()


if __name__ == "__main__":
    unittest.main()
