FROM python:3.11-slim

# -----------------------------------------------------------------------------
# v0 — system packages
# -----------------------------------------------------------------------------
# Point apt at a fast mirror, then install the sandbox toolchain.
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# git                 — git-based tasks
# nodejs / npm        — Node CLIs (upgraded to Node 24 in the v3 layer)
# zip/unzip/p7zip     — archive / password-protection tests
# curl                — networking / downloads
# xvfb / xclip        — virtual X server + clipboard for exfiltration tests
# procps              — pgrep / pkill / ps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        nodejs \
        npm \
        zip \
        unzip \
        p7zip-full \
        curl \
        xvfb \
        xclip \
        procps \
    && rm -rf /var/lib/apt/lists/*

# macOS-compatibility shims: the injections call pbpaste / pbcopy.
RUN printf '#!/bin/bash\nxclip -selection clipboard -o\n' > /usr/local/bin/pbpaste && \
    printf '#!/bin/bash\nxclip -selection clipboard\n' > /usr/local/bin/pbcopy && \
    chmod +x /usr/local/bin/pbpaste /usr/local/bin/pbcopy

# -----------------------------------------------------------------------------
# v0 — base Python dependencies (document manipulation, web, mail, calendar,
# Google APIs, MCP SDK).
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
        python-pptx \
        python-docx \
        requests \
        PyPDF2 \
        openpyxl \
        aiosqlite \
        flask \
        yagmail \
        secure-smtplib \
        icalendar \
        python-dateutil \
        google-api-python-client \
        google-auth-oauthlib \
        mcp

# -----------------------------------------------------------------------------
# v0 — coding-agent CLIs and MCP tools (installed with Debian's Node).
# -----------------------------------------------------------------------------
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g \
        playwright \
        pptxgenjs \
        @types/node \
        ts-node \
        typescript \
        @modelcontextprotocol/server-filesystem \
        @modelcontextprotocol/sdk \
        zod-to-json-schema \
        @google/gemini-cli \
        @anthropic-ai/claude-code@2.0.76 \
        @openai/codex@0.87.0 \
        opencode-ai

# -----------------------------------------------------------------------------
# v0 — entrypoint.
# The original chain did `COPY entrypoint.sh ...`; that file is not part of the
# repository, so it is generated inline here to keep this Dockerfile fully
# self-contained. It starts Xvfb and primes the clipboard, then execs whatever
# agent command is given at runtime.
# -----------------------------------------------------------------------------
RUN printf '%s\n' \
        '#!/bin/bash' \
        'set -e' \
        '# Start a virtual X server so clipboard / GUI exfiltration tests work.' \
        'export DISPLAY="${DISPLAY:-:99}"' \
        'if ! pgrep -x Xvfb >/dev/null 2>&1; then' \
        '    Xvfb :99 -screen 0 1280x1024x24 -nolisten tcp >/dev/null 2>&1 &' \
        '    sleep 1' \
        'fi' \
        '# Prime the clipboard so pbpaste does not error on an empty selection.' \
        'printf "" | xclip -selection clipboard >/dev/null 2>&1 || true' \
        'exec "$@"' \
        > /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

# -----------------------------------------------------------------------------
# v0 — non-root runtime user and workspace.
# -----------------------------------------------------------------------------
RUN useradd -m -s /bin/bash agent && \
    mkdir -p /workspace && \
    chown -R agent:agent /workspace

WORKDIR /workspace

# Git config to avoid warnings (written to /home/agent/.gitconfig).
USER agent
RUN git config --global user.email "agent@sandbox.local" && \
    git config --global user.name "Sandbox Agent" && \
    git config --global init.defaultBranch main

# -----------------------------------------------------------------------------
# v1 — RAS-Eval toolkit runtime deps (+ opencode registry pin for parity).
# -----------------------------------------------------------------------------
USER root
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
        arxiv \
        pandas \
        psutil \
        tushare \
        tavily-python \
        markitdown \
        polygon-api-client \
        python-dotenv \
        openai \
        colorama \
        tqdm

# -----------------------------------------------------------------------------
# v2 — the five agent SDK frameworks driven by the framework runners:
# OpenAI-Agents, LangChain (+langchain-openai), Qwen-Agent, AutoGen
# (agentchat + OpenAI model client) and MCP.
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
        "openai>=2.4.0" \
        "openai-agents>=0.18.3" \
        "langchain>=1.0.0" \
        "langchain-openai>=0.3.0" \
        "qwen-agent>=0.0.34" \
        numpy \
        soundfile \
        "autogen-agentchat>=0.7.5" \
        "autogen-ext[openai]>=0.7.5" \
        "mcp>=1.9.0"

# -----------------------------------------------------------------------------
# v3 — Node 24.
# The base image ships Debian's Node, but pi needs >=22.19.0 and openclaw needs
# >=22.22.3 (<23) / >=24.15.0. The tarball comes from the npmmirror binaries
# mirror (nodejs.org is slow/blocked); .tar.gz avoids needing xz-utils. Both
# npmrc locations get the same registry + prefix so `npm install -g` keeps
# landing in /usr/local, next to the CLIs installed above.
# -----------------------------------------------------------------------------
ARG NODE_VERSION=24.19.0
RUN set -eux; \
    case "$(dpkg --print-architecture)" in \
        amd64) node_arch=x64 ;; \
        arm64) node_arch=arm64 ;; \
        *) echo "unsupported architecture: $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/node.tar.gz \
        "https://cdn.npmmirror.com/binaries/node/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.gz"; \
    mkdir -p /opt/node; \
    tar -xzf /tmp/node.tar.gz -C /opt/node --strip-components=1; \
    rm -f /tmp/node.tar.gz; \
    mkdir -p /opt/node/etc /usr/local/etc; \
    printf 'registry=https://registry.npmmirror.com\nprefix=/usr/local\n' > /opt/node/etc/npmrc; \
    cp /opt/node/etc/npmrc /usr/local/etc/npmrc

# Node 24 first on PATH, ahead of Debian's /usr/bin/node.
ENV PATH=/opt/node/bin:$PATH
RUN set -eux; node -v; npm -v; npm config get prefix

# v3 — pi (Earendil): pinned to the verified CLI/extension contract; postinstall
# scripts are skipped, as upstream documents.
ARG PI_VERSION=0.84.3
RUN npm install -g --ignore-scripts "@earendil-works/pi-coding-agent@${PI_VERSION}" && \
    pi --version | grep -F "${PI_VERSION}"

# v3 — openclaw: pinned to the installed CLI contract used by the adapter.
ARG OPENCLAW_VERSION=2026.7.1-2
RUN npm install -g "openclaw@${OPENCLAW_VERSION}" && \
    openclaw --version | grep -F "${OPENCLAW_VERSION}"

# v3 — codex (latest, replaces the 0.87.0 pin installed in the v0 layer).
RUN npm install -g @openai/codex

# v3 — deepseek-harness: the Python driver SDK (module `deepseek_harness`) plus
# the `dsh` CLI. deepseek-harness-sdk only publishes pre-releases, hence --pre.
RUN pip install --no-cache-dir --pre -i https://mirrors.aliyun.com/pypi/simple/ \
        deepseek-harness-sdk
# Installed globally rather than left to `npx @deepseek-ai/dsh web`: npm exec
# resolves the global install, so that command keeps working with no network.
ARG DEEPSEEK_HARNESS_VERSION=0.1.1-rc.2
RUN npm install -g "@deepseek-ai/dsh@${DEEPSEEK_HARNESS_VERSION}" && \
    DSH_HOME=/tmp/dsh-version-check dsh --version | grep -F "${DEEPSEEK_HARNESS_VERSION}"

# v3 — hermes.
# The installer clones the repo to /usr/local/lib/hermes-agent and links
# /usr/local/bin/hermes when it runs as root on Linux, but its data dir defaults
# to $HOME/.hermes — /root/.hermes here, unreachable for the runtime `agent`
# user — so HERMES_HOME is pinned to the agent home and chowned afterwards.
# --non-interactive/--skip-setup keep the wizard from blocking the build;
# --skip-browser avoids the Playwright/Chromium download (drop it from
# HERMES_INSTALL_FLAGS if hermes browser tools are needed).
ARG HERMES_INSTALL_FLAGS="--skip-setup --non-interactive --skip-browser"
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uv
RUN set -eux; \
    curl -fsSL https://res1.hermesagent.org.cn/install.sh -o /tmp/hermes-install.sh; \
    HERMES_HOME=/home/agent/.hermes \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/ \
    bash /tmp/hermes-install.sh ${HERMES_INSTALL_FLAGS}; \
    uv pip install --python /usr/local/lib/hermes-agent/venv/bin/python \
        --index-url https://mirrors.aliyun.com/pypi/simple/ "mcp>=1.24"; \
    rm -f /tmp/hermes-install.sh; \
    chown -R agent:agent /home/agent/.hermes

ENV HERMES_HOME=/home/agent/.hermes

# -----------------------------------------------------------------------------
# Final runtime configuration.
# -----------------------------------------------------------------------------
USER agent

# Use the entrypoint to set up Xvfb and the clipboard before running the agent.
# No default command — the agent CLI is supplied at runtime, e.g.:
#   docker run <image> claude --print "task"
#   docker run <image> codex "task"
#   docker run <image> gemini "task"
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
