FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/c2-api ./cmd/c2-api

FROM alpine:3.20
WORKDIR /app
COPY --from=build /out/c2-api /app/c2-api
COPY migrations /app/migrations
EXPOSE 8080
CMD ["/app/c2-api"]
