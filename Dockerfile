# پایه: Python 3.9
FROM python:3.9-slim

# جلوگیری از تولید pyc و بافر stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# مسیر کاری داخل کانتینر
WORKDIR /code

# نصب وابستگی‌های سیستمی لازم برای mysqlclient
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       pkg-config \
    && rm -rf /var/lib/apt/lists/*

# نصب پکیج‌های پایتون
COPY requirements.txt /code/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# کپی کل پروژه
COPY . /code/

# پورت جنگو
EXPOSE 8000

# اجرای سرور توسعه جنگو
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
