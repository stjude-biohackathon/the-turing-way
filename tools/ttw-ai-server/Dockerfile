# =================================================================================
# Base image
# =================================================================================
#
# python:3.11-slim is a Docker Hub "official image" — a curated, verified image
# maintained by the Docker community. Using official images reduces the risk of
# inheriting malicious code or unpatched vulnerabilities from an unknown source.
# TTW: "only download and run something on your machine if it comes from a trusted
# source. Docker Hub has 'official image' badges for commonly used, verified images."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-whatdocker
#
# The version is pinned to 3.11 rather than "python:latest" so this Dockerfile
# continues to build identically after future Python releases that may remove or
# rename behaviour this server depends on.
# TTW: "Specifying a version for the image is optional. However, it is best practice
# as it ensures that our Dockerfile remains valid after new releases."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles
#
# The -slim variant ships only the runtime essentials, omitting compilers, headers,
# and documentation that are not needed to run a pure-Python server.
# TTW: "containers only contain the individual components they need in order to
# operate the project they contain. This gives a significant performance boost and
# reduces the size of the application."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-what
FROM python:3.11-slim

# =================================================================================
# Working directory
# =================================================================================
#
# WORKDIR creates /app if it does not exist and makes it the active directory for
# every subsequent instruction. Using WORKDIR instead of "RUN cd /app" avoids a
# subtle build error: each RUN instruction starts a new shell from the image root,
# so a bare "RUN cd" has no lasting effect on the layers that follow.
# TTW: "WORKDIR should be used when changing directories is necessary while building
# an image...using 'RUN cd directory_name' can lead to errors."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles-workdir
WORKDIR /app

# =================================================================================
# Dependency installation
# =================================================================================
#
# pyproject.toml is copied before the source tree so Docker can reuse the cached
# install layer on rebuilds where only application code has changed. Separating the
# manifest copy from the source copy is a deliberate use of Docker's layer cache to
# avoid re-downloading packages unnecessarily.
# TTW: "It is good practice to group related commands into a single RUN block to
# reduce the final size of your image by avoiding the creation of unnecessary layers."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles
COPY pyproject.toml .

# --no-cache-dir tells pip not to write its download cache into the image layer.
# That cache is never used at runtime, so keeping it only inflates the image size.
# TTW: "follow best-practice by...cleaning up the apt-cache...further reduce the
# size of Debian or Ubuntu images."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles
RUN pip install --no-cache-dir -e .

# =================================================================================
# Application source
# =================================================================================
#
# COPY is used rather than ADD because it is explicit: it only copies local files
# and never silently fetches remote URLs or unpacks archives. ADD's extra behaviour
# makes a Dockerfile harder to reason about, so COPY is preferred unless ADD is
# specifically required.
# TTW: "It is good practice to use COPY, except where ADD is specifically required,
# as the term COPY is more explicit about what is being done."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles
#
# Source is copied after the install step so that editing application code does not
# invalidate the cached dependency layer above.
COPY src/ src/

# =================================================================================
# Runtime configuration
# =================================================================================
#
# EXPOSE documents the port the HTTP server binds to. Docker does not publish this
# port automatically; it serves as machine-readable metadata for orchestration tools
# (such as docker-compose and Kubernetes) so they can wire up networking without
# parsing the application source.
# TTW: "EXPOSE: This includes ports that should be exposed. It is more relevant to
# people using Docker to share web apps."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles-commands
EXPOSE 8000

# CMD sets the default command run when a container starts from this image, making
# the intended use clear without hardcoding it. Unlike RUN (which executes at build
# time), CMD executes at runtime and can be overridden without modifying the
# Dockerfile — for example, pass "ttw-server mcp" to run as a Claude Desktop MCP
# server on stdio instead.
# TTW: "It is good practice to use CMD for any commands that need to be run before
# someone starts working in the container instead of forcing users to run them
# themselves (and trusting that they will even know that they need to)."
# See: https://book.the-turing-way.org/reproducible-research/renv/renv-containers#rr-renv-containers-dockerfiles-commands
CMD ["ttw-server", "http"]
