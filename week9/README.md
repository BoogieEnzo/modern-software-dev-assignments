# Week9 Repo Trends Explorer

每日简报页面：展示 GitHub Top 3 趋势仓库（按 7 天累计增星）。

## Run

```bash
pip install -r requirements.txt
make run
```

Open: http://localhost:8002

## Remote Development (SSH + Browser)

This project runs on a remote Linux server. You access it via SSH from your Mac and test through Chrome.

### Workflow

1. **Start the server on the remote machine:**
   ```bash
   make run
   ```

2. **Access from your Mac's Chrome:**
   - The server binds to `0.0.0.0:8002`
   - Open: `http://<server-ip>:8002`
   - Example: `http://192.168.1.100:8002`

3. **Check server IP:**
   ```bash
   hostname -I | awk '{print $1}'
   ```

### Port Notes

- Default port: **8002** (avoid conflict with 8000)
- If port is in use:
  ```bash
  lsof -ti:8002 | xargs kill -9
  ```

```bash
pip install -r requirements.txt
make run
```

Open: http://localhost:8000

## Test

```bash
pip install -r requirements.txt
make test
```

## Env

- `GITHUB_TOKEN` (optional, recommended to avoid low API rate limits)
