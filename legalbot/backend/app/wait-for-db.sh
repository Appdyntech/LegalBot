#!/bin/bash
set -e

host="$1"
port="$2"
shift 2
cmd="$@"

echo "⏳ Waiting for Postgres at $host:$port..."
until nc -z "$host" "$port"; do
  sleep 2
done

echo "✅ Postgres is up - starting backend"
exec $cmd
