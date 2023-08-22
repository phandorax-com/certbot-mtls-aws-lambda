# Automatización de la Gestión de Certificados mTLS con Lambda y Certbot


## Introducción

Este proyecto está diseñado para facilitar la gestión y renovación de certificados SSL/TLS para el uso en comunicaciones mTLS (Mutual TLS). El mTLS es una extensión del protocolo TLS que asegura una comunicación bidireccional cifrada entre dos partes, donde ambas, cliente y servidor, presentan certificados al otro.

### Función Lambda

Nuestra función Lambda automatiza varios pasos clave:

1. **Obtención y Renovación de Certificado**: Utilizando Certbot, renueva o adquiere certificados para el dominio especificado en `DOMAIN_NAME_APIG`.
2. **Lectura y Concatenación del Certificado**: Lee el certificado y la clave del directorio temporal, y concatena el certificado raíz de Let's Encrypt para formar un `truststore.pem`.
3. **Almacenamiento Seguro en AWS**: El `truststore.pem` se sube a un bucket S3 y los detalles del certificado se guardan en AWS Secret Manager.

### Contenerización

Mediante Docker, aseguramos un proceso consistente y reproducible:

1. **Consistencia de Entorno**: Docker garantiza que las dependencias y el entorno son los mismos en todas partes.
2. **Manejo de Dependencias**: Usando un entorno virtual Python, todas las dependencias se instalan y gestionan dentro del contenedor.
3. **Empaquetado y Despliegue**: Los binarios y códigos necesarios se empaquetan juntos, listos para desplegarse como función Lambda.

El uso de contenerización, combinado con la función Lambda, ofrece una solución robusta y automatizada para la gestión de certificados en comunicaciones mTLS.

## Paso a Paso:

1. **Construir la Imagen Docker**:
   Este paso construye una imagen Docker que contiene todas las dependencias necesarias para `certbot`.

   ```bash
   docker build -t lambda_packager .
   ```

2. **Ejecutar el Contenedor**:
   Una vez que la imagen se ha construido, puedes ejecutarla. Esto creará un contenedor llamado `lambda_container` que compila y paqueta la función Lambda.

   ```bash
   docker run --name lambda_container lambda_packager
   ```

3. **Extraer el Paquete ZIP**:
   Luego, extrae el archivo `.zip` del contenedor. Este archivo contiene la función Lambda junto con todas las bibliotecas necesarias.

   ```bash
   docker cp lambda_container:/app/certbot/function-mtls-manager.zip .
   ```

4. **Limpiar**: 
   Después de extraer el paquete, es una buena práctica eliminar el contenedor para evitar conflictos futuros y liberar recursos.

   ```bash
   docker rm lambda_container
   ```

5. **Probar la Función Lambda Localmente**:
   Finalmente, puedes probar la función Lambda en tu máquina local usando el siguiente comando:

   ```bash
   ./test_lambda.sh
   ```

### Ejemplo Integrado:

Si prefieres un comando único que realice todas las acciones anteriores de forma secuencial, aquí lo tienes:

```bash
docker build -t lambda_packager . \
&& docker run --name lambda_container lambda_packager \
&& docker cp lambda_container:/app/certbot/function-mtls-manager.zip . \
&& docker rm lambda_container 

./test_lambda.sh
```


### Ejemplo Policy:


```json
{
    "Statement": [
        {
            "Action": "apigateway:GET",
            "Effect": "Allow",
            "Resource": "arn:aws:apigateway:us-east-1::/domainnames",
            "Sid": "APIGatewayDOMAIN"
        },
        {
            "Action": [
                "apigateway:UpdateClientCertificate",
                "apigateway:GetDomainName"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:apigateway:us-east-1::/restapis/<REPLACE_VALUE>",
            "Sid": "APIGatewayREST"
        },
        {
            "Action": "cloudwatch:PutMetricData",
            "Effect": "Allow",
            "Resource": "*",
            "Sid": "CloudWatch"
        },
        {
            "Action": [
                "logs:PutLogEvents",
                "logs:CreateLogStream",
                "logs:CreateLogGroup"
            ],
            "Effect": "Allow",
            "Resource": "*",
            "Sid": "Logs"
        },
        {
            "Action": [
                "route53:ListHostedZones",
                "route53:GetChange",
                "route53:ChangeResourceRecordSets"
            ],
            "Effect": "Allow",
            "Resource": "*",
            "Sid": "Route53"
        },
        {
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:s3:::<YOUR_BUCKET_NAME_HERE>/*",
            "Sid": "S3"
        },
        {
            "Action": [
                "secretsmanager:UpdateSecret",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
                "secretsmanager:CreateSecret"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:secretsmanager:us-east-1:<ACCOUNT>:secret:<SECRET_NAME>*",
            "Sid": "SecretsManager"
        }
    ],
    "Version": "2012-10-17"
}
```