FROM node:22-slim

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
COPY ui-design-system /app/ui-design-system

CMD ["npm", "exec", "vite", "--", "--host", "0.0.0.0"]
