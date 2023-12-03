FROM python:3.8
COPY . /usr/app/
WORKDIR /usr/app/
RUN pip install -r requirements.txt \
    &&  apt-get update && apt-get install libsm6 libxrender1      libfontconfig1 libice6 ffmpeg libxext6 -y
EXPOSE 8501
CMD streamlit run app.py
