# homebrew-tools

## Install
```shell
brew tap jplonghi/tools
brew trust --formula jplonghi/tools/getjwttoken
brew install getjwttoken
```
## Configure
```shell
getjwttoken --config
```
## Usage

Copy a token to the clipboard (the default):

```shell
getjwttoken
# Or: getjwttoken --copy
```

Print only the token, without changing the clipboard:

```shell
getjwttoken --print
# Short form: getjwttoken -p
```

Use it in the current shell and scripts launched from that shell:

```shell
MY_TOKEN="$(getjwttoken --print)" && export MY_TOKEN
```

The assignment is checked before exporting so a failed request is reported.
Errors go to stderr, and failed requests produce no token on stdout.
Use `MY_TOKEN`, with an underscore: shell variable names cannot contain hyphens.

## Automatic shell export

Add an export to your zsh profile:

```shell
getjwttoken --install-profile MY_TOKEN
```

This defaults to `${ZDOTDIR:-$HOME}/.zshrc` and to the variable `MY_TOKEN` if
you omit its name. You can specify another variable and profile file:

```shell
getjwttoken --install-profile API_TOKEN "$HOME/.zshrc"
```

Setup appends a marked block while preserving existing content. Running it
again for the same variable does not add another block. It stores the absolute
path to the command used for setup, so install the tool in its permanent location
first. If you move it, remove the marked block and run setup again.

Open a new terminal after setup. The profile fetches and exports a fresh token
at each interactive shell startup, and unsets the variable if the fetch fails.
The profile stores the command, never the token or your credentials. Each request
has a 5-second connection timeout and a 15-second total timeout.

Child scripts inherit the exported variable:

```shell
printf '%s\n' "$MY_TOKEN"
```

Tokens can expire while a shell stays open. Fetch and export again when needed:

```shell
if MY_TOKEN="$(getjwttoken --print)"; then
    export MY_TOKEN
else
    unset MY_TOKEN
fi
```

An executable cannot change its parent shell's environment directly; the profile
or command substitution performs the export in your shell. Independently launched
jobs, such as cron jobs, must fetch their own token because they do not read `.zshrc`.
Remove the marked `getjwttoken` block from your profile to disable automatic fetching.

Run `getjwttoken --help` for all options.

## Development

Run the regression tests with Python 3.9 or newer:

```shell
python3 -m unittest discover -s tests -v
```

The tests mock Keychain, HTTP requests, and clipboard access. With zsh installed,
they also verify profile loading and inheritance by child processes.

To try changes from this checkout before a new release, use `./getjwttoken`
instead of `getjwttoken` in the commands above.

## Releasing version 1.1.0

The formula downloads `getjwttoken` directly from the `v1.1.0` Git tag. Its
SHA-256 checksum covers only that script, so changes to the formula or README
do not affect it. If you edit the script before releasing, recalculate its
checksum and update `sha256` in `getjwttoken.rb`:

```shell
shasum -a 256 getjwttoken
```

After reviewing and testing the changes, commit them and publish the branch
and tag together:

```shell
git add getjwttoken getjwttoken.rb README.md tests/test_getjwttoken.py
git commit -m "Release getjwttoken 1.1.0"
git tag v1.1.0
git push --atomic origin main v1.1.0
```

The tag must point to the commit containing the script that matches the formula's
checksum. Publishing only the branch leaves the new download URL unavailable.
Keep published version tags unchanged; use a new version for later releases.

Once the release is published, validate the download and installation:

```shell
brew update
brew audit --strict jplonghi/tools/getjwttoken
brew fetch --force jplonghi/tools/getjwttoken
brew upgrade jplonghi/tools/getjwttoken
brew test jplonghi/tools/getjwttoken
```

Use `brew install jplonghi/tools/getjwttoken` instead of `brew upgrade` for a
first installation. The formula's test exercises profile setup in a temporary
file without accessing credentials or requesting a token.
