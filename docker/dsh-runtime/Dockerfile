# syntax=docker/dockerfile:1

# ==========================================
# 1. Base Image
# ==========================================
ARG NODE_IMAGE=node:24.22.2-bookworm-slim
FROM ${NODE_IMAGE}

# ==========================================
# 2. Version Configuration
# ==========================================
ARG DSH_VERSION=0.2.2-rc.1
ARG NPM_VERSION=11.19.1
ARG PNPM_VERSION=12.18.0

# ==========================================
# 3. Runtime Environment
# ==========================================
ENV DSH_HOME=/root/.dsh \
    npm_config_update_notifier=false \
    npm_config_fund=false

WORKDIR /app

# ==========================================
# 4. System Dependencies
# ==========================================
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        python3 \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# 5. Upgrade npm
# ==========================================
RUN npm install --global \
        --no-audit \
        --no-fund \
        "npm@${NPM_VERSION}" \
    && test "$(npm --version)" = "${NPM_VERSION}"

# ==========================================
# 6. Install DSH and pnpm
# ==========================================
RUN npm_config_engine_strict=true npm install --global \
        --no-audit \
        --no-fund \
        --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs \
        "@deepseek-ai/dsh@${DSH_VERSION}" \
        "pnpm@${PNPM_VERSION}" \
    && test "$(dsh --version)" = "${DSH_VERSION}" \
    && test "$(pnpm --version)" = "${PNPM_VERSION}"

# ==========================================
# 7. Initialize Directories
# ==========================================
RUN mkdir -p /app "${DSH_HOME}" \
    && chmod 700 "${DSH_HOME}"

# ==========================================
# 8. Default Container Behavior
# ==========================================
CMD ["sleep", "infinity"]
