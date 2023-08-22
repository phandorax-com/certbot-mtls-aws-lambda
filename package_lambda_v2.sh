#!/bin/bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64   

set -e

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CERTBOT_VERSION=2.6.0
readonly VENV="certbot/venv"
readonly PYTHON="python3.8"
readonly CERTBOT_ZIP_FILE="function-mtls-manager.zip"
readonly CERTBOT_SITE_PACKAGES=${VENV}/lib/${PYTHON}/site-packages

cd "${SCRIPT_DIR}"

${PYTHON} -m venv "${VENV}"
source "${VENV}/bin/activate"

pip3 install -r requirements.txt

# Copiar los binarios de certbot
mkdir -p package/bin
cp ${VENV}/bin/certbot package/bin/

pushd ${CERTBOT_SITE_PACKAGES}
    zip -r -q ${SCRIPT_DIR}/certbot/${CERTBOT_ZIP_FILE} . -x "/*__pycache__/*"
popd

zip -g "certbot/${CERTBOT_ZIP_FILE}" lambda_function.py

# Agregar el binario de certbot
zip -g "certbot/${CERTBOT_ZIP_FILE}" package/bin/certbot

#pip3 freeze | grep -v "pkg-resources" > requirements_updated.txt

echo "El paquete de despliegue function-mtls-manager.zip está listo. ${SCRIPT_DIR}/certbot/${CERTBOT_ZIP_FILE} "
