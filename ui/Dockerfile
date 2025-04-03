# ui/Dockerfile

# 1. Build Stage
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the application code
COPY . .

# Set NEXT_PUBLIC_API_URL - this can be overridden at runtime by docker-compose
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN echo "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}" >> .env.production

# Build the Next.js application
RUN npm run build

# 2. Production Stage
FROM node:20-alpine AS runner
WORKDIR /app

# Set environment to production
ENV NODE_ENV production
# Optionally, uncomment the following line to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED 1

# Create a non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from the builder stage
# This assumes `output: 'standalone'` in next.config.ts
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set the user to the non-root user
USER nextjs

# Expose the port the app runs on
EXPOSE 3000

# Set the host and port Next.js should bind to
ENV HOSTNAME "0.0.0.0"
ENV PORT 3000

# Command to run the Node.js server created by the standalone output
CMD ["node", "server.js"] 