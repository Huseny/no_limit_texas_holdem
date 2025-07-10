# frontend/Dockerfile
FROM node:20

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm

COPY ./package.json ./pnpm-lock.yaml ./
RUN pnpm install

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]
