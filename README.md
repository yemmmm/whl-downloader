# Offline Package Downloader

This repository provides GitHub Actions workflows for preparing offline install
artifacts:

- Python wheels: `.github/workflows/download-whl.yml`
- Docker images: `.github/workflows/download-docker-image.yml`

## Download a Docker Image for an Offline Server

Use the `Download Docker Image` workflow from the GitHub Actions tab.

Inputs:

- `image`: Docker image reference, for example `nginx:1.27` or
  `redis:7-alpine`
- `platform`: target platform for the offline server, usually `linux/amd64`
  for x86_64 servers or `linux/arm64` for ARM servers
- `artifact-name`: optional artifact name

After the workflow finishes, download the generated artifact from the workflow
run page. It contains a `.tar.gz` file created with `docker save`.

Copy the archive to the offline server, then load it:

```bash
docker load -i nginx-1.27.tar.gz
```

Start the container normally:

```bash
docker run --rm -p 8080:80 nginx:1.27
```

For Docker Compose, export every image used by `image:` entries, upload all
archives to the offline server, and run `docker load -i <archive>.tar.gz` for
each archive before `docker compose up`.

If the image is private, add a login step or configure registry credentials in
GitHub Actions secrets before running `docker pull`.

## Download Python Wheels

Use the `Download WHL Packages` workflow from the GitHub Actions tab. It
downloads Python wheel files and dependencies, packages them as a zip artifact,
and prints offline install commands in the workflow log.
