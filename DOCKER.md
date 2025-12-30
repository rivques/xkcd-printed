Usage and notes for Dockerizing this project

- Persistent status file: a bind mount is provided at `./data` and the service
  sets `STATUS_FILE=/data/xkcd_last_printed.txt` so the last-printed file is
  stored on the host.

- Bluetooth access: the compose file runs the container with `network_mode: host`
  and `privileged: true`, and mounts `/var/run/dbus` and `/sys/class/bluetooth`.
  This allows the container to access the host BlueZ stack on Linux hosts.

- Important: Docker Desktop on Windows does not expose host Bluetooth to Linux
  containers. For Bluetooth access run this on a Linux host (or a full Linux VM
  with Docker). If you're on Windows and can't run on Linux, Bluetooth
  functionality will not work from inside the container.

Quick start (Linux host)

1. Create the data folder for persistent storage:

```bash
mkdir -p data
```

2. Copy your environment variables into `.env` (or use the provided `.env.example`).

3. Build and run with docker-compose:

```bash
docker compose up --build -d
```

4. To view logs:

```bash
docker compose logs -f
```

If you prefer `docker run`, run with:

```bash
docker build -t catprinter .
docker run --rm -it --network=host --privileged \
  -v "$(pwd)/data:/data" \
  -v /var/run/dbus:/var/run/dbus:ro \
  -v /sys/class/bluetooth:/sys/class/bluetooth:ro \
  --env-file .env \
  catprinter
```
