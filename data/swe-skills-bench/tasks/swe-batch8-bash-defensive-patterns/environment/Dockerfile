FROM zhangyiiiiii/swe-skills-bench-python
USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN if ! command -v git >/dev/null 2>&1 || ! command -v python >/dev/null 2>&1; then \
      apt-get update && apt-get install -y git ca-certificates python3 python3-pip && \
      rm -rf /var/lib/apt/lists/*; \
    fi
RUN if ! command -v python >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then \
      ln -s /usr/bin/python3 /usr/local/bin/python; \
    fi
RUN mkdir -p /workspace /logs/verifier /tmp/benchmark_tests

RUN set -eux; \
    repo_dir='/workspace/shellcheck'; \
    if [ ! -d "$repo_dir/.git" ]; then rm -rf "$repo_dir" && git clone 'https://github.com/koalaman/shellcheck' "$repo_dir"; fi; \
    cd "$repo_dir"; \
    git checkout 'cd41f794383b6159757575c9debbf198426b21aa'

WORKDIR /workspace/shellcheck

CMD ["/bin/bash"]
