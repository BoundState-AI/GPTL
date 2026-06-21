from __future__ import annotations

import hashlib
import shutil
import socket
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg import sql


def _postgres_binary(name: str) -> str:
    pg_config = shutil.which("pg_config")
    if pg_config is None:
        raise RuntimeError("pg_config is required for PostgreSQL acceptance tests")
    bindir = subprocess.run(
        [pg_config, "--bindir"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    binary = Path(bindir, name)
    if not binary.is_file():
        raise RuntimeError(f"PostgreSQL test binary is unavailable: {binary}")
    return str(binary)


def _unused_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.fixture(scope="session")
def postgres_cluster_url() -> Iterator[str]:
    root = Path(tempfile.mkdtemp(prefix="gptl-postgres-", dir="/tmp"))
    data_directory = root / "data"
    socket_directory = root / "socket"
    socket_directory.mkdir()
    log_path = root / "postgres.log"
    port = _unused_tcp_port()
    database_user = "gptl_test"
    initdb = _postgres_binary("initdb")
    pg_ctl = _postgres_binary("pg_ctl")

    started = False
    try:
        subprocess.run(
            [
                initdb,
                "--pgdata",
                str(data_directory),
                "--username",
                database_user,
                "--auth",
                "trust",
                "--no-locale",
                "--encoding",
                "UTF8",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        server_options = f"-F -h 127.0.0.1 -p {port} -k {socket_directory} -c log_statement=none"
        subprocess.run(
            [
                pg_ctl,
                "--pgdata",
                str(data_directory),
                "--log",
                str(log_path),
                "--options",
                server_options,
                "--wait",
                "start",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        started = True
        yield f"postgresql://{database_user}@127.0.0.1:{port}/postgres"
    finally:
        try:
            if started:
                subprocess.run(
                    [pg_ctl, "--pgdata", str(data_directory), "--wait", "stop"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
        finally:
            shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def postgres_url(postgres_cluster_url: str, request: pytest.FixtureRequest) -> str:
    node_hash = hashlib.sha256(request.node.nodeid.encode("utf-8")).hexdigest()
    database_name = f"gptl_{node_hash[:24]}"
    with psycopg.connect(postgres_cluster_url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
    return postgres_cluster_url.rsplit("/", 1)[0] + "/" + database_name
