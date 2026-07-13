FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
# Don't fail if package.json is empty or missing scripts during initial build
RUN npm install || true
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
