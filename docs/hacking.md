# Hacking loop

The installed plugin is a real git clone (`omarchy plugin add file://...`),
so never `cp` repo files over it — that dirties the clone and blocks
`omarchy plugin update`. Iterate like this:

```bash
./tests/test.sh
git add -A && git commit -m "..."
omarchy plugin update cogitator-rite --yes
omarchy restart shell   # mandatory: rescanPlugins does NOT reload services,
                        # a stale service keeps serving its old IPC surface
```

Theme iteration is still file-based until enable:

```bash
python3 palettes/render.py green --check  # must pass
```

`cogitator enable`/`disable` remain the only commands that switch themes;
both queue a detached `cogitator-v2-transition` unit because `omarchy theme
set` restarts the invoking terminal. Poll with `cogitator status`, read the
unit journal on failure:

```bash
journalctl --user -u cogitator-v2-transition.service --no-pager -o cat | tail -n 20
```
