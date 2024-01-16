import boto3
import certbot.main
import os
import requests
import json
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def load_certificates_from_pem(pem_data):
    """Divide y carga múltiples certificados desde un archivo PEM."""
    pem_certs = pem_data.split("-----END CERTIFICATE-----")
    certificates = []

    for pem in pem_certs:
        if "-----BEGIN CERTIFICATE-----" in pem:
            cert_data = (pem + "-----END CERTIFICATE-----").strip()
            cert = x509.load_pem_x509_certificate(cert_data.encode(), default_backend())
            certificates.append(cert)

    return certificates

def lambda_handler(event, context):

    try:
        # Obtener las variables de entorno
        DOMAIN_NAME_APIG = os.environ['DOMAIN_NAME_APIG']
        DOMAIN_NAME_MTLS = os.environ['DOMAIN_NAME_MTLS']
        SECRET_NAME = os.environ['SECRET_NAME']
        S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
        CERT_PATH = '/tmp/config-dir/live/' + DOMAIN_NAME_MTLS

        # 1. Obtener y renovar el certificado usando Certbot
        certbot.main.main([
            'certonly', '--dns-route53', '-d', DOMAIN_NAME_MTLS, '--agree-tos',
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

        # 3. Leer y filtrar el chain.pem seleccionando solo el primer certificado usando cryptography
        with open(CERT_PATH + "/chain.pem", 'r') as file:
            certs_data = file.read()

        certs = load_certificates_from_pem(certs_data)

        first_cert = certs[0].public_bytes(serialization.Encoding.PEM).decode('utf-8')

        # 4. Crear truststore.pem
        truststore = first_cert
        if not first_cert.endswith("\n"):
            truststore += "\n"
        truststore += root_cert

        truststore_path = "/tmp/truststore.pem"

        with open(truststore_path, 'w') as file:
            file.write(truststore)

        # 5. Subir truststore.pem a S3
        s3_client = boto3.client('s3')
        with open(truststore_path, 'rb') as file:
            upload_response = s3_client.put_object(Bucket=S3_BUCKET_NAME, Key='truststore.pem', Body=file)
        version_id = upload_response.get('VersionId')
         
        # 6. Actualizar AWS Secret Manager
        client = boto3.client('secretsmanager')
        secret_data = {
            "cert": CERT,
            "key": KEY
        }
        client.update_secret(SecretId=SECRET_NAME, SecretString=json.dumps(secret_data))

        # 7. Actualizar la configuración de API Gateway usando Boto3
        apigateway_client = boto3.client('apigateway')
        update_response = apigateway_client.update_domain_name(
            domainName=DOMAIN_NAME_APIG,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/mutualTlsAuthentication/truststoreVersion',
                    'value': version_id
                }
            ]
        )
        
        # Mensaje de finalización
        return "Operación completada exitosamente. Version ID: " + version_id

    except Exception as e:
        print(f"Error: {e}")
        return f"Se produjo un error durante la ejecución: {e}"
