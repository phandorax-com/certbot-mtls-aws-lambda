#!/bin/bash

# Usuarios MAC M1
# export DOCKER_DEFAULT_PLATFORM=linux/amd64   

# Nombre del paquete zip y del directorio descomprimido
ZIP_NAME="function-mtls-manager.zip"
UNPACKED_DIR="unpacked"

# Descomprime el paquete ZIP
if [ -d "$UNPACKED_DIR" ]; then
    echo "Eliminando directorio anterior..."
    rm -rf $UNPACKED_DIR
fi

echo "Descomprimiendo $ZIP_NAME..."
mkdir $UNPACKED_DIR && unzip $ZIP_NAME -d $UNPACKED_DIR/

# Ejecuta la función Lambda localmente usando Docker
echo "Ejecutando función Lambda con Docker..."
cd $UNPACKED_DIR

docker run -v "$PWD":/var/task -e DOMAIN_NAME_APIG="<DOMAIN_HERE>" -e SECRET_NAME="<SECRET_NAME_HERE>" -e S3_BUCKET_NAME=""<BUCKET_NAME_HERE>"" lambci/lambda:python3.8 lambda_function.lambda_handler

# Limpia el directorio descomprimido (opcional)
cd ..
rm -rf $UNPACKED_DIR
