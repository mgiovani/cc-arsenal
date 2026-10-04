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

Without `cargo`, print this line and stop:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Then re-run `cargo install stopslop`. Do not try other installers.

Update only when the user asks: `cargo install stopslop --force`.

stopslop prints a daily update notice. Set `STOPSLOP_NO_UPDATE_CHECK=1` on every run so it does not pollute the output.
