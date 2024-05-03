import logging
import os
import shutil
import time
import json
from tempfile import NamedTemporaryFile
from minio import Minio
from minio.error import S3Error
import parsl
from parsl import bash_app
from config import transcode_config_local
from parsl.data_provider.files import File
from parsl.config import Config
from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.channels import LocalChannel

def get_secret(key):
    with open("/var/openfaas/secrets/{}".format(key)) as f:
        return f.read().strip()
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = get_secret("minio-access-key")
MINIO_SECRET_KEY = get_secret("minio-secret-key")
BUCKET_NAME = os.getenv('BUCKET_NAME')

@bash_app
def run_ffmpeg(inputs=(), outputs=()) -> str:
    args = inputs[1]
    resolution = args.get('resolution', '1280x720')
    acodec = args.get('acodec', 'copy')
    vcodec = args.get('vcodec', '')
    if resolution != 'no':
        resolution_cmd = f'-s {resolution}'
    else:
        resolution_cmd = ''
    codec = ''
    if acodec != '':
        codec += ' -acodec ' + acodec
    if vcodec != '':
        codec += ' -vcodec ' + vcodec
    cmd = f'ffmpeg -hide_banner -loglevel warning -y -i {inputs[0].filepath} {resolution_cmd} {codec} {outputs[0].filepath}'
    print(cmd)
    return cmd

def upload_video(object_path, local_path):
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    try:
        minio_client.fput_object(BUCKET_NAME, object_path, local_path)
    except S3Error as e:
        logging.error(f"MinIO Error: {e}")
        return f"Error uploading file: {e}"
    return "Success"
        # return {"statusCode": 500, "body": f"Error uploading file: {e}"}

def handle(event, context):
    if event.method != "POST":
      return {
        "statusCode": 405,
        "body": "Method not allowed"
      }
    
    transcode_config_local = Config(
    executors=[
        HighThroughputExecutor(
            label="htex_Local",
            worker_debug=True,
            # cores_per_worker=1,
            # storage_access=[HTTPInTaskStaging()],
            provider=LocalProvider(
                channel=LocalChannel(),
                init_blocks=1,
                max_blocks=10,
            ),
        )
    ],
    strategy=None,
)

    with parsl.load(transcode_config_local):
        body = json.loads(event.body.decode('utf-8'))
        
        path = body.get('path')
        obj_name = body.get('object')
        args = body.get('args', {})
        video_format = args.get('format', 'mp4')
        current_time = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
        remote_video = File(os.path.join("http://" + MINIO_ENDPOINT, BUCKET_NAME, path, obj_name))
        # remote_video = File('https://github.com/Parsl/parsl/blob/master/README.rst')
        tmp_path = path + "-" + current_time
        os.mkdir(tmp_path)
        output_local_path = os.path.join(tmp_path, "output." + video_format)
        transcoding_future = run_ffmpeg(inputs=[remote_video, args], 
                                        outputs=[File(output_local_path)])
        print(transcoding_future.result())
        if transcoding_future.result() == 0:
            res_upload = upload_video(os.path.join(path, "output." + video_format), output_local_path)
            if "Error" in res_upload:
                shutil.rmtree(tmp_path)
                return {"statusCode": 500, "body": res_upload}
        else:
            shutil.rmtree(tmp_path)
            return {"statusCode": 500, "body": f"Transcoding function exit with err code: {transcoding_future.result()}"}
        shutil.rmtree(tmp_path)
        return {"statusCode": 200, "body": "success"}
