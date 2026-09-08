# Source this to point the engine at the local Gitea (no secrets stored here;
# the token lives in ~/.gitea-engine-token, chmod 600).
export ENGINE_GITEA=1
export ENGINE_GITEA_BASE="${ENGINE_GITEA_BASE:-http://192.168.1.162:3300}"
export ENGINE_GIT_ROOT="${ENGINE_GIT_ROOT:-http://192.168.1.162:3300}"
export GITEA_TOKEN="$(cat ~/.gitea-engine-token 2>/dev/null)"
