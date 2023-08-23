import boto3
import certbot.main
import os
import requests
import json


def lambda_handler(event, context):

    try:
        # Obtener las variables de entorno
        DOMAIN_NAME_APIG = os.environ['DOMAIN_NAME_APIG']
        SECRET_NAME = os.environ['SECRET_NAME']
        S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
        CERT_PATH = '/tmp/config-dir/live/' + DOMAIN_NAME_APIG

        # 1. Obtener y renovar el certificado usando Certbot
        certbot.main.main([
            'certonly', '--dns-route53', '-d', DOMAIN_NAME_APIG, '--agree-tos',
            '--no-eff-email', '--email', 'support@hocknas.us', '--config-dir',
            '/tmp/config-dir/', '--work-dir', '/tmp/work-dir/', '--logs-dir',
            '/tmp/logs-dir/'
        ])

        # 2. Leer el certificado y la clave
        with open(CERT_PATH + "/fullchain.pem", 'r') as file:
            CERT = file.read()

        with open(CERT_PATH + "/privkey.pem", 'r') as file:
            KEY = file.read()

        response = requests.get(
            "https://letsencrypt.org/certs/isrgrootx1.pem.txt")
        root_cert = response.text
        if not root_cert.endswith("\n"):
            root_cert += "\n"

        with open("/tmp/isrgrootx1.pem", 'w') as file:
            file.write(root_cert)

        # 3. Leer y filtrar el chain.pem
        with open(CERT_PATH + "/chain.pem", 'r') as file:
            certs = file.read().split("-----END CERTIFICATE-----")

        if len(certs) < 2:
            raise Exception("No se encontraron suficientes certificados en chain.pem")

        filtered_certs = certs[:-1]
        chain_cert = "-----END CERTIFICATE-----".join(filtered_certs)

        # 4. Crear truststore.pem 
        truststore = chain_cert
        if not chain_cert.endswith("\n"):
            truststore += "\n"
        truststore += root_cert

        truststore_path = "/tmp/truststore.pem"

        with open(truststore_path, 'w') as file:
            file.write(truststore)

        # 5. Subir truststore.pem a S3
        s3_client = boto3.client('s3')
        s3_client.upload_file(truststore_path, S3_BUCKET_NAME, 'truststore.pem')

        # 6. Actualizar AWS Secret Manager
        client = boto3.client('secretsmanager')
        secret_data = {
            "cert": CERT,
            "key": KEY
        }
        client.update_secret(SecretId=SECRET_NAME, SecretString=json.dumps(secret_data))

        # Mensaje de finalización
        return "Operación completada exitosamente."

    except Exception as e:
        print(f"Error: {e}")
        return f"Se produjo un error durante la ejecución: {e}"
