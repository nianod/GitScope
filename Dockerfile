FROM python:3.12-slim AS runtime

ARG SCC_VERSION=3.7.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/analyzer/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl git \
    && curl --fail --location --silent --show-error \
        "https://github.com/boyter/scc/releases/download/v${SCC_VERSION}/scc_Linux_x86_64.tar.gz" \
        --output /tmp/scc.tar.gz \
    && tar -xzf /tmp/scc.tar.gz -C /usr/local/bin scc \
    && chmod 0755 /usr/local/bin/scc \
    && rm -rf /var/lib/apt/lists/* /tmp/scc.tar.gz

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin analyzer

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY tools ./tools

RUN mkdir -p /work/outputs /work/cloned_repos \
    && chown -R analyzer:analyzer /app /work

USER analyzer

ENTRYPOINT ["python", "/app/tools/Repo_analysis_tool.py"]
CMD ["--help"]
