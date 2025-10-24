# Windows Setup Guide (WordPress + MariaDB + Neo4j via WSL 2)

These steps keep the local stack lightweight while running WordPress, MariaDB, and Neo4j side-by-side. Anything that requires elevated permissions or a manual download is called out explicitly.

## 1. Install WSL 2 with Ubuntu

1. Open **Windows PowerShell** **as Administrator**.
2. Enable WSL and the Virtual Machine Platform:
   ```powershell
   wsl --install
   ```
   - If prompted to reboot, do so before continuing.
3. After reboot, Windows will open a console to finish installing Ubuntu. If it does not, launch it manually:
   ```powershell
   wsl --install -d Ubuntu
   ```
4. When the Ubuntu terminal appears, choose a UNIX username and password (they can differ from your Windows credentials).

> Already have WSL installed? Make sure `wsl -l -v` shows version 2 for your distro. If not, run `wsl --set-version <distroName> 2`.

## 2. Install Docker Engine inside WSL

We avoid Docker Desktop to reduce footprint.

1. In the Ubuntu shell, update packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Install Docker Engine dependencies:
   ```bash
   sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
   ```
3. Add Docker’s official GPG key:
   ```bash
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
   ```
4. Add the Docker repository:
   ```bash
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```
5. Install Docker Engine, CLI, and Compose plugin:
   ```bash
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
6. Allow your Linux user to run Docker without `sudo`:
   ```bash
   sudo usermod -aG docker $USER
   ```
   Log out of WSL (`exit`) and reopen Ubuntu so group membership takes effect.
7. Verify the installation:
   ```bash
   docker version
   docker compose version
   ```
8. Optional: enable Docker to start automatically with WSL sessions:
   ```bash
   sudo systemctl enable --now docker
   ```

## 3. Prepare the project inside WSL

1. In Ubuntu, navigate to the Windows project path (WSL mounts drives under `/mnt`):
   ```bash
   cd /mnt/c/Users/micha/Documents/FlavorPairing/infra/docker
   ```
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` to set secure passwords:
   ```bash
   nano .env
   ```
   - `MYSQL_ROOT_PASSWORD` should be unique.
   - `WORDPRESS_DB_PASSWORD` should be unique.
   - Adjust `NEO4J_AUTH` (`username/password`) if you want something other than `neo4j/test`.
4. (Optional) If the WordPress plugin directory is elsewhere, update the bind mount in `docker-compose.yml`:
   ```yaml
   - ../../flavor-pairing:/var/www/html/wp-content/plugins/flavor-pairing
   ```

## 4. Start the containers

1. From `infra/docker/` run:
   ```bash
   docker compose up -d
   ```
2. Check container health:
   ```bash
   docker compose ps
   ```
3. Tail logs if needed:
   ```bash
   docker compose logs -f web
   docker compose logs -f neo4j
   ```

## 5. Finish application setup

- WordPress: visit [http://localhost/](http://localhost/) in your browser and follow the installer. Use the database values from `.env`.
- Neo4j Browser: visit [http://localhost:7474/](http://localhost:7474/) and log in with the credentials from `.env` (`neo4j/test` by default). The first login will ask you to change the password if you kept the default.

## 6. Managing the stack

| Action | Command (from `infra/docker/`) |
| ------ | ------------------------------ |
| Stop containers | `docker compose down` |
| Stop and remove volumes | `docker compose down -v` |
| Restart | `docker compose down && docker compose up -d` |
| Update images | `docker compose pull` |

## 7. Optional: Lightweight alternative without WSL

If you prefer a native Windows approach:

1. Install [Laragon Portable](https://laragon.org/download/) (bundles Apache/nginx, PHP, and MySQL).
2. Download the [Neo4j Community ZIP](https://neo4j.com/download-center/#community) and unzip to `C:\neo4j`.
3. Launch Neo4j with:
   ```powershell
   .\neo4j\bin\neo4j.bat console
   ```
   Configure WordPress inside Laragon as usual, then point your PHP integration at `bolt://localhost:7687` with the credentials you set via `neo4j-admin`.

The Docker-in-WSL flow is slimmer and easier to automate, but both routes work. Let me know which path you take so we can tailor integration scripts accordingly.
