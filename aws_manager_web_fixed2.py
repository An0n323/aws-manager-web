#!/usr/bin/env python3
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import Flask, request, redirect, url_for, render_template_string, flash

# Configuration Flask
app = Flask(__name__)
app.secret_key = "aws_manager_secret_key"

# Lecture des variables AWS depuis l'environnement
region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN")

# Création de la session boto3
if aws_access_key and aws_secret_key:
    session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        aws_session_token=aws_session_token,
        region_name=region
    )
else:
    session = boto3.Session(region_name=region)

# Clients AWS
try:
    ec2_client = session.client("ec2")
    s3_client = session.client("s3")
    s3_resource = session.resource("s3")
    identity = session.client("sts").get_caller_identity()
    print(f"✅ Identité AWS détectée : {identity['Arn']}")
except NoCredentialsError:
    ec2_client = None
    s3_client = None
    s3_resource = None
    print("⚠️ Aucun rôle IAM détecté ou credentials manquants !")
    print("L'application ne pourra pas accéder à EC2 ou S3 sans rôle IAM attaché.")

# HTML Template minimal
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AWS Manager Web</title>
</head>
<body>
    <h1>AWS Manager Web</h1>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}

    <h2>Instances EC2</h2>
    <ul>
    {% for instance in instances %}
        <li>{{ instance['InstanceId'] }} - {{ instance.get('State', {}).get('Name') }}</li>
    {% endfor %}
    </ul>

    <h2>Buckets S3</h2>
    <ul>
    {% for bucket in buckets %}
        <li>{{ bucket }}</li>
    {% endfor %}
    </ul>

    <h2>Créer un Bucket</h2>
    <form method="post" action="/create_bucket">
        Nom du bucket: <input type="text" name="bucket_name">
        <input type="submit" value="Créer">
    </form>

    <h2>Uploader un fichier</h2>
    <form method="post" action="/upload_file" enctype="multipart/form-data">
        Bucket: <input type="text" name="bucket_name">
        Fichier: <input type="file" name="file">
        <input type="submit" value="Uploader">
    </form>

    <h2>Supprimer un Bucket</h2>
    <form method="post" action="/delete_bucket">
        Nom du bucket: <input type="text" name="bucket_name">
        <input type="submit" value="Supprimer">
    </form>
</body>
</html>
"""

# Routes Flask
@app.route("/")
def index():
    instances = []
    buckets = []
    if ec2_client:
        try:
            response = ec2_client.describe_instances()
            for r in response.get('Reservations', []):
                for i in r.get('Instances', []):
                    instances.append(i)
        except ClientError as e:
            flash(f"Erreur EC2: {str(e)}")
    if s3_client:
        try:
            response = s3_client.list_buckets()
            buckets = [b['Name'] for b in response.get('Buckets', [])]
        except ClientError as e:
            flash(f"Erreur S3: {str(e)}")
    return render_template_string(HTML_TEMPLATE, instances=instances, buckets=buckets)

@app.route("/create_bucket", methods=["POST"])
def create_bucket():
    bucket_name = request.form.get("bucket_name")
    if s3_client and bucket_name:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
            flash(f"Bucket '{bucket_name}' créé avec succès !")
        except ClientError as e:
            flash(f"Erreur création bucket: {str(e)}")
    else:
        flash("Credentials AWS manquants ou nom de bucket invalide.")
    return redirect(url_for("index"))

@app.route("/delete_bucket", methods=["POST"])
def delete_bucket():
    bucket_name = request.form.get("bucket_name")
    if s3_client and bucket_name:
        try:
            bucket = s3_resource.Bucket(bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
            flash(f"Bucket '{bucket_name}' supprimé avec succès !")
        except ClientError as e:
            flash(f"Erreur suppression bucket: {str(e)}")
    else:
        flash("Credentials AWS manquants ou nom de bucket invalide.")
    return redirect(url_for("index"))

@app.route("/upload_file", methods=["POST"])
def upload_file():
    bucket_name = request.form.get("bucket_name")
    file = request.files.get("file")
    if s3_client and bucket_name and file:
        try:
            s3_client.upload_fileobj(file, bucket_name, file.filename)
            flash(f"Fichier '{file.filename}' uploadé dans '{bucket_name}' !")
        except ClientError as e:
            flash(f"Erreur upload: {str(e)}")
    else:
        flash("Credentials AWS manquants, nom de bucket ou fichier invalide.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    print(f"Lancement AWS Manager Web sur 0.0.0.0:8080, région AWS : {region}")
    app.run(host="0.0.0.0", port=8080)
