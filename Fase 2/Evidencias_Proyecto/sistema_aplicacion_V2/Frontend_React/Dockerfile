# Dockerfile para Frontend React con Vite

# Etapa 1: Build
FROM node:20-alpine as build

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del proyecto
COPY . .

# Argumento de build para la URL del API
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build de producción
RUN npm run build

# Etapa 2: Servidor Nginx
FROM nginx:alpine

# Copiar archivos build
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
