FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY odoo_agent odoo_agent
COPY knowledge knowledge
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "odoo_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
