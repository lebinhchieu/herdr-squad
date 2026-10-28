#!/usr/bin/env bash
# usage: probe26.sh <runtime-root> <role> <rule> <outdir>  -- stub squad-usage prints <rule>; hook copied beside it
root=$1; role=$2; rule=$3; out=$4; rm -rf $out; mkdir -p $out/sq $out/stub
printf '#!/bin/sh\necho %s\n' "$rule" > $out/stub/squad-usage; chmod +x $out/stub/squad-usage
cp $root/bin/squad-usage-hook $out/stub/squad-usage-hook
for n in 1 2; do
  echo '{"session_id":"s1"}' | env -u SCOPE_DIR -u GOAL_DIR SQUAD_NAME=dev-1 SQUAD_DIR=$out/sq SQUAD_ROLE=$role $out/stub/squad-usage-hook 2>$out/stderr$n; echo "exit ${PIPESTATUS[1]}" > $out/rc$n
done
