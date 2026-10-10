#!/bin/sh
# During a Cloudflare build: copy the relay codes from the build settings into the helper's runtime secrets.
# (They're never stored in this repo; if they aren't set, this does nothing.)
if [ -n "$TURN_KEY_ID" ] && [ -n "$TURN_KEY_API_TOKEN" ]; then
  printf '%s' "$TURN_KEY_ID" | npx wrangler secret put TURN_KEY_ID --name just-trees-online >/dev/null 2>&1 && echo "relay key id copied" || echo "relay key id: copy failed"
  printf '%s' "$TURN_KEY_API_TOKEN" | npx wrangler secret put TURN_KEY_API_TOKEN --name just-trees-online >/dev/null 2>&1 && echo "relay token copied" || echo "relay token: copy failed"
else
  echo "relay codes not in build settings; skipping"
fi
exit 0
