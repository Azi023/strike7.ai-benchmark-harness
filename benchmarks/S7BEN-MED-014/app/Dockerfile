FROM python:3.11-slim
WORKDIR /app
RUN pip install flask==3.0.0
COPY app.py .
EXPOSE 8100
CMD ["python", "app.py"]
