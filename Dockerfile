FROM lambci/lambda:build-python3.8

WORKDIR /app

COPY requirements.txt /app/
COPY package_lambda_v2.sh /app/
COPY lambda_function.py /app/

CMD ["./package_lambda_v2.sh"]
