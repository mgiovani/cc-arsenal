# Install

Check first:

```bash
stopslop --version
```

If missing, install from crates.io (the only published method):

```bash
cargo install stopslop
```

Latest unreleased main:

```bash
cargo install --git https://github.com/mgiovani/stopslop
```

Without `cargo`, print the rustup install line from https://rustup.rs and stop. Do not try other installers.

Update only when the user asks: `cargo install stopslop --force`.

stopslop prints a daily update notice. Set `STOPSLOP_NO_UPDATE_CHECK=1` on every run so it does not pollute the output.
