FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]


