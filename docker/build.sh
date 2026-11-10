set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PLATFORM="${PLATFORM:-linux/amd64}"

case "${PLATFORM}" in
    linux/amd64) DEFAULT_TAG="ras-eval-amd:latest" ;;
    linux/arm64) DEFAULT_TAG="ras-eval-arm:latest" ;;
    *)           DEFAULT_TAG="ras-eval:latest" ;;
esac

IMAGE_TAG="${IMAGE_TAG:-${DEFAULT_TAG}}"
DOCKERFILE="${DOCKERFILE:-${SCRIPT_DIR}/Dockerfile}"
CONTEXT="${CONTEXT:-${REPO_ROOT}}"

echo "==> Building ${IMAGE_TAG} for ${PLATFORM} from ${DOCKERFILE}"
docker buildx build \
    --platform "${PLATFORM}" \
    -t "${IMAGE_TAG}" \
    --load \
    --file "${DOCKERFILE}" \
    "${CONTEXT}"

if [[ "${EXPORT_TAR:-0}" == "1" ]]; then
    TAR_PATH="${TAR_PATH:-${SCRIPT_DIR}/$(echo "${IMAGE_TAG}" | tr ':/' '--').tar}"
    echo "==> Saving image to ${TAR_PATH}"
    docker save -o "${TAR_PATH}" "${IMAGE_TAG}"

    APPTAINER_BIN="${APPTAINER_BIN:-apptainer}"
    SIF_PATH="${SIF_PATH:-${TAR_PATH%.tar}.sif}"
    echo "==> Building apptainer image ${SIF_PATH}"
    "${APPTAINER_BIN}" build "${SIF_PATH}" "docker-archive://${TAR_PATH}"
fi

echo "==> Done: ${IMAGE_TAG}"
