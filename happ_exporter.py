#!/usr/bin/env python3
"""Export locally stored Happ profiles to a portable JSON file."""

import argparse
import base64
import copy
import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Happ uses AES-128-GCM for encrypted subscription responses. The client-side
# compatibility keys below are needed solely to read profiles on this computer.
AES_KEYS = (
    "key01:3jk#R2d&Dd", "key02:+]%4ij#P\"/", "key03:?&YNg/\"L3}",
    "key04:+-4b\"-?S${", "key05:N5<a/(~jJ'", "key06:s5\\[\"=`uC/",
    "key07:(H+b'')_@5", "key08:W'=)[/~i9w", "key09:'2%`C~>)_d",
    "key10:)\\'h]*#7MP",
)
GCM_IV = b"k" * 12


def default_database() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is unavailable; pass --database explicitly.")
    return Path(local_app_data) / "Happ" / "subs.db"


def b64decode(value: str) -> bytes:
    value = value.strip()
    return base64.b64decode(value + "=" * (-len(value) % 4))


def decrypt_record(data: bytes | str, tag: str) -> tuple[bytes, int]:
    ciphertext_b64 = data.decode("ascii") if isinstance(data, bytes) else data
    encrypted = b64decode(ciphertext_b64) + b64decode(tag)
    for slot, key in enumerate(AES_KEYS, start=1):
        try:
            return AESGCM(key.encode("ascii")).decrypt(GCM_IV, encrypted, None), slot
        except Exception:
            continue
    raise RuntimeError("the record does not match a supported Happ encryption key")


def normalize_payload(value: bytes) -> str:
    """Decode UTF-8 payloads; Happ sometimes wraps them in Base64."""
    text = value.decode("utf-8-sig")
    for _ in range(2):
        try:
            decoded = b64decode(text).decode("utf-8-sig")
        except (UnicodeDecodeError, ValueError):
            break
        if not decoded:
            break
        text = decoded
    return text


def profile_from_server(subscription: dict, server: dict) -> dict | None:
    try:
        config = json.loads(server["config"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
    outbounds = config.get("outbounds", [])
    protocols = sorted({item.get("protocol", "unknown").lower() for item in outbounds if isinstance(item, dict)})
    return {
        "subscription": subscription.get("name", ""),
        "name": server.get("name", ""),
        "host": server.get("host", ""),
        "port": server.get("port"),
        "protocols": protocols,
        # Preserve the original Xray outbounds exactly, including credentials and
        # transport settings needed to import the profile elsewhere.
        "outbounds": outbounds,
    }


def extract_profiles(payload: str) -> list[dict]:
    try:
        root = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"decrypted payload is not JSON: {error.msg}") from error
    profiles = []
    for subscription in root.get("map", {}).values():
        if not isinstance(subscription, dict):
            continue
        for server in subscription.get("serverMap", {}).values():
            if isinstance(server, dict):
                profile = profile_from_server(subscription, server)
                if profile is not None:
                    profiles.append(profile)
    return profiles


def read_happ_database(database: Path) -> tuple[list[dict], int, list[int]]:
    if not database.is_file():
        raise RuntimeError(f"Happ database was not found: {database}")
    uri = f"file:{database.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT data, tag FROM subscriptions").fetchall()
    profiles, slots = [], []
    for data, tag in rows:
        decrypted, slot = decrypt_record(data, tag)
        slots.append(slot)
        profiles.extend(extract_profiles(normalize_payload(decrypted)))
    return profiles, len(rows), slots


def write_json_atomically(destination: Path, content: dict) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, delete=False) as temporary:
        json.dump(content, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(destination)


def xkeen_document(profiles: list[dict]) -> dict:
    """Build the standalone Xray config expected by XKeen's 04_outbounds.json."""
    outbounds = []
    counter = 0
    for profile in profiles:
        for outbound in profile["outbounds"]:
            if not isinstance(outbound, dict):
                continue
            protocol = outbound.get("protocol", "").lower()
            # Each Happ profile carries its own direct/block pair. XKeen needs
            # one shared pair, added below.
            if protocol in {"freedom", "blackhole", "dns", "loopback"}:
                continue
            counter += 1
            item = copy.deepcopy(outbound)
            # Happ commonly uses the same "proxy" tag for every server; Xray
            # requires tags to be unique when more than one outbound is loaded.
            item["tag"] = f"happ-{protocol or 'proxy'}-{counter:03d}"
            outbounds.append(item)
    if not outbounds:
        raise RuntimeError("no proxy outbounds suitable for XKeen were found")
    outbounds.extend((
        {"tag": "direct", "protocol": "freedom"},
        {"tag": "block", "protocol": "blackhole"},
    ))
    return {"outbounds": outbounds}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export all locally stored Happ profiles to JSON.")
    parser.add_argument("--database", type=Path, default=default_database(), help="path to Happ subs.db")
    parser.add_argument("--output", type=Path, default=Path("happ-profiles-export.json"), help="destination JSON file")
    parser.add_argument("--format", choices=("archive", "xkeen"), default="archive", help="archive: full profile export; xkeen: ready 04_outbounds.json")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    profiles, record_count, key_slots = read_happ_database(arguments.database)
    if not profiles:
        raise RuntimeError("no exportable profiles were found")
    protocol_counts = Counter(protocol for profile in profiles for protocol in profile["protocols"])
    if arguments.format == "xkeen":
        document = xkeen_document(profiles)
    else:
        document = {
            "format": "happ-profile-export/v1",
            "profile_count": len(profiles),
            "protocol_counts": dict(sorted(protocol_counts.items())),
            "profiles": profiles,
        }
    write_json_atomically(arguments.output, document)
    print(json.dumps({
        "output": str(arguments.output.resolve()),
        "format": arguments.format,
        "profiles": len(profiles),
        "xkeen_outbounds": len(document["outbounds"]) if arguments.format == "xkeen" else None,
        "encrypted_records": record_count,
        "protocol_counts": dict(sorted(protocol_counts.items())),
        "aes_key_slots": key_slots,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
