# build docker image for running training, copied from "riseml/imagebuilder:v1.2.3"

import json
import traceback
import tempfile
import os
import glob
import shutil
import requests
import zipfile
import sys
import rollbar
import pika
import stat
from envparse import env
from docker import APIClient
from docker.errors import DockerException

import gcr

DEBUG = env('DEBUG', cast=bool, default=False)
RUN_SCRIPT = 'riseml_run.sh'
DOWNLOAD_SUBDIR = 'code'
RISEML_YML = 'riseml.yml'
BUILD_PATH = os.environ.get('BUILD_PATH', '/build')
LOGFILE = os.environ.get('LOGFILE', '/logs/job')
REGISTRY_USER = os.environ.get('REGISTRY_USER', '')
REGISTRY_PASSWORD = os.environ.get('REGISTRY_PASSWORD', '')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://backend.riseml.com')
ROLLBAR_ENDPOINT = BACKEND_URL + '/errors/imagebuilder/'
CLUSTER_ID = os.environ.get('CLUSTER_ID')


def log(message):
    #with open(LOGFILE, 'a') as f:
    #    f.write(message)
    sys.stdout.write(message)
    sys.stdout.flush()


class BuildException(DockerException):
    pass


def download_file(url, download_path):
    try:
        r = requests.get(url, stream=True)
        #d = r.headers['content-disposition']
        #filename = re.findall("filename=(.+)", d)[0]
        filename = 'code.zip'
        if (r.status_code != 200):
            msg = "Failed to download code from %s: %s" % (url, r.status_code)
            log("%s\n" % msg)
            if ENVIRONMENT not in ['development', 'test']:
                rollbar.report_exc_info()
            raise(BuildException(msg))
    except requests.exceptions.RequestException as e:
        log(str(e) + '\n')
        if ENVIRONMENT not in ['development', 'test']:
            rollbar.report_exc_info()
        raise(BuildException("Failed to download code from %s" % url))
    with open(os.path.join(download_path, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        return filename


def generage_runscript(run_commands):
    runscript = """#!/bin/bash\n\n"""
    runscript += 'set -o pipefail\n'
    for cmd in run_commands:
        runscript += "%s 2>&1 | tee -a $LOGFILE\n" % cmd
        # runscript += "stdbuf -o0 %s 2>&1 | tee -a $LOGFILE\n" % cmd
        return runscript


def generate_buildsteps(from_image, install_commands, code_path,
                        code_subdir, work_dir='/code',
                        run_script='riseml_run.sh'):
    copy_first = ['requirements*.txt']
    buildsteps = ""
    buildsteps += "FROM %s\n" % from_image
    buildsteps += "WORKDIR %s\n" % work_dir
    for cf in copy_first:
        if glob.glob(os.path.join(code_path, cf)):
            buildsteps += "COPY %s %s/\n" % (os.path.join(code_subdir, cf),
                                            work_dir)
    if install_commands:
        for cmd in install_commands:
            buildsteps += "RUN %s\n" % cmd
    buildsteps += "COPY %s /%s\n" % (run_script, run_script)
    buildsteps += "COPY %s %s\n" % (code_subdir, work_dir)
    buildsteps += "CMD /%s" % run_script
    return buildsteps


def output_stream(stream):
    for chunk in stream:
        if isinstance(chunk, bytes):
            #print(chunk)
            continue
        if 'stream' in chunk:
            log(chunk['stream'])
        elif 'status' in chunk:
            if chunk['status'].startswith('Pulling from'):
                log(chunk['status'] + '\n')
        elif 'error' in chunk:
            raise BuildException("Error: %s" % chunk['error'])
        if DEBUG:
            log(str(chunk) + '\n')


def set_execute(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)


def docker_build(client, image_name, build_path, stream_fun):
    stream = client.build(tag=image_name,
                          stream=True,
                          decode=True,
                          nocache=False,
                          rm=True,
                          pull=True,
                          path=build_path)
    stream_fun(stream)


def push(client, repo, image_tag, stream_fun):
    stream = client.push(repo, tag=image_tag, stream=True)
    stream_fun(stream)


def write_to_file(content, filename):
    with open(filename, 'w') as dockerfile:
        dockerfile.write(content)


def get_image_size(api_client, repo, image_tag):
    return api_client.inspect_image("%s:%s" % (repo, image_tag))['Size']


def get_num_image_layers(api_client, repo, image_tag):
    image_info = api_client.inspect_image("%s:%s" % (repo, image_tag))
    return len(image_info['RootFS']['Layers'])


def download_code(download_path, download_url):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    log("Downloading your code\n")
    repo_file = download_file(download_url, download_path)
    target_file = os.path.join(download_path, repo_file)
    zipfile.ZipFile(target_file).extractall(download_path)
    os.remove(target_file)


def output_push_stream(stream, num_layers):
    layers = {}
    total_push_size = 0
    last_prog = 0
    def output_progress(prog, last_prog, n_dots=10):
        prog = int(prog / n_dots)
        if (prog > n_dots):
            return prog
        output = '.' * (prog - last_prog)
        if output:
            log('...stored %d%%\n' % (prog * n_dots))
            #log(output)
        return prog
    for chunk in stream:
        if isinstance(chunk, bytes):
            chunk = eval(chunk)
        if 'status' in chunk:
            if chunk['status'] in ('Layer already exists', 'Pushed'):
                layer = chunk['id']
                if layer not in layers:
                    layers[layer] = 0
            elif chunk['status'] == 'Pushing' and \
                   'progressDetail' in chunk and \
                   'total' in chunk['progressDetail']:
                layer = chunk['id']
                if layer not in layers:
                    layers[layer] = 0
                    total_push_size += chunk['progressDetail']['total']
                layers[layer] = chunk['progressDetail']['current']
                total_pushed = sum(layers.values())
                if len(layers) == num_layers:
                    last_prog = output_progress(total_pushed / total_push_size * 100,
                                                last_prog)
        elif 'error' in chunk:
            raise BuildException("Error: %s" % chunk['error'])
        if DEBUG:
            log(chunk + '\n')
    output_progress(100.0, last_prog)


def parse_image(image):
    parts = image.split('/')
    image_tag = 'latest'
    if ':' in parts[-1]:
        parts[-1], image_tag = parts[-1].split(':')
    registry_host = parts[0]
    registry_repo = '/'.join(parts[1:])
    return registry_host, registry_repo, image_tag


def build(from_image, install_commands,
          target_image, download_url,
          build_path=BUILD_PATH,
          registry_user=REGISTRY_USER,
          registry_password=REGISTRY_PASSWORD,
          download_subdir=DOWNLOAD_SUBDIR,
          run_script=RUN_SCRIPT):
    download_path = os.path.join(build_path, download_subdir)
    download_code(download_path, download_url)

    buildsteps = generate_buildsteps(from_image,
                                     install_commands,
                                     download_path,
                                     download_subdir,
                                     run_script=run_script)
    #run_script = generage_runscript(config_section.run)

    write_to_file(buildsteps, os.path.join(build_path, 'Dockerfile'))
    shutil.copyfile(run_script, os.path.join(build_path, run_script))
    #write_to_file(run_script, os.path.join(build_path, run_script))
    set_execute(os.path.join(build_path, run_script))

    client = APIClient(version='auto')
    log('Running install commands...\n')

    # possibly login to source registry
    from_registry, _, _ = parse_image(from_image)
    if gcr.is_gcr(from_registry) and gcr.gcr_scopes_enabled():
        token = gcr.get_gcr_token()
        # token could still be empty
        if token is not None:
            login_to_registry(client, from_registry, '_token', token)

    # login to target registry
    host, repo, tag = parse_image(target_image)
    #login_to_registry(client, host, registry_user, registry_password)

    repo = "%s/%s" % (host, repo)

    docker_build(client, "%s:%s" % (repo, tag), build_path, output_stream)
    num_layers = get_num_image_layers(client, repo, tag)
    log('Image size: %.2f MB in %d layers\n' %
           (get_image_size(client, repo, tag)/(1000*1000),
            num_layers))
    if DEBUG:
        log("Build done. Pushing to registry %s with tag %s.\n" % (repo, tag))
    log('Storing your image...\n')
    push(client, repo, tag, lambda x: output_push_stream(x, num_layers))
    log("Build process finished.\n")


def login_to_registry(client, registry, user, password):
    try:
        client.login(username=user,
                     password=password,
                     registry=registry,
                     reauth=True)
    except DockerException as de:
        if ENVIRONMENT not in ['development', 'test']:
            rollbar.report_exc_info()
        raise BuildException("Failed to connect to registry %s, %s" % (registry, str(de)))


def main():
    target_image = os.environ.get('TARGET_IMAGE')
    download_url = os.environ.get('DOWNLOAD_URL')
    from_image = os.environ.get('FROM_IMAGE')
    client = APIClient(version='auto')
    install_commands = json.loads(os.environ.get('INSTALL_COMMANDS'))
    log("Preparing image for your experiment\n")
    try:
        build(from_image, install_commands, target_image, download_url)
    except DockerException as e:
        log(str(e) + '\n')
        sys.exit(1)


if __name__ == '__main__':
    if ENVIRONMENT not in ['development', 'test']:
        rollbar.init(
            CLUSTER_ID, # Use cluster id as access token
            ENVIRONMENT,
            endpoint=ROLLBAR_ENDPOINT,
            root=os.path.dirname(os.path.realpath(__file__)))
    try:
        main()
    except Exception as e:
        if ENVIRONMENT not in ['development', 'test']:
            rollbar.report_exc_info()
        log(traceback.format_exc() + '\n')
        sys.exit(1)
