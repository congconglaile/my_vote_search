FROM python:3.9
ADD my_config.py /code/
ADD main.py /code/
ADD requirements.txt /code/
ADD vector_store/ /code/vector_store/
ADD resource/ /code/resource/
ADD model/ /code/model/
WORKDIR /code
RUN pip install -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --default-timeout=60 --no-cache-dir -r requirements.txt
CMD ["python","-u","main.py"]
