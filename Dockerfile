FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . .
# I dati stanno nel volume montato su /data (vedi README)
ENV DATA_DIR=/data
EXPOSE 3000
CMD ["node", "server.js"]
