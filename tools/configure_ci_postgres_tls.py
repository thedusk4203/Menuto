"""Enable verified TLS on the disposable GitHub CI PostgreSQL service, never production."""

import argparse
import os
import subprocess
import time
from pathlib import Path

import psycopg
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This provisioning helper is restricted to the disposable CI service")
    url = make_url(os.environ["MENUTO_TEST_POSTGRES_URL"])
    if url.host != "127.0.0.1" or url.database != "postgres":
        raise SystemExit("Expected the isolated loopback CI maintenance URL")
    directory = Path(os.environ["RUNNER_TEMP"]) / "menuto-ci-postgres-tls"
    directory.mkdir(exist_ok=True)
    cert, key = directory / "server.crt", directory / "server.key"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=IP:127.0.0.1,DNS:localhost",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for local, remote in ((cert, "menuto_ci.crt"), (key, "menuto_ci.key")):
        destination = "/var/lib/postgresql/" + remote
        subprocess.run(["docker", "cp", str(local), f"{args.container}:{destination}"], check=True)
        subprocess.run(
            [
                "docker",
                "exec",
                "--user",
                "0",
                args.container,
                "chown",
                "postgres:postgres",
                destination,
            ],
            check=True,
        )
        subprocess.run(
            ["docker", "exec", "--user", "0", args.container, "chmod", "600", destination],
            check=True,
        )
    kwargs = dict(
        host=url.host, port=url.port, user=url.username, password=url.password, dbname=url.database
    )
    with psycopg.connect(**kwargs, autocommit=True) as connection:
        connection.execute("ALTER SYSTEM SET ssl_cert_file='/var/lib/postgresql/menuto_ci.crt'")
        connection.execute("ALTER SYSTEM SET ssl_key_file='/var/lib/postgresql/menuto_ci.key'")
        connection.execute("ALTER SYSTEM SET ssl='on'")
        connection.execute("SELECT pg_reload_conf()")
    verified = dict(kwargs, sslmode="verify-full", sslrootcert=str(cert), connect_timeout=2)
    for attempt in range(50):
        try:
            with psycopg.connect(**verified) as connection:
                assert (
                    connection.execute(
                        "SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()"
                    ).fetchone()[0]
                    is True
                )
            break
        except psycopg.OperationalError:
            if attempt == 49:
                raise
            time.sleep(0.1)
    verified_url = url.update_query_dict({"sslmode": "verify-full", "sslrootcert": str(cert)})
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as output:
        output.write(
            "MENUTO_TEST_POSTGRES_URL=" + verified_url.render_as_string(hide_password=False) + "\n"
        )
    print("Disposable PostgreSQL CI service: TLS verified; production requirements unchanged.")


if __name__ == "__main__":
    main()
