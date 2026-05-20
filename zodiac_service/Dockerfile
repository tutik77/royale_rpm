FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o zodiac_service .

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/zodiac_service .
EXPOSE 8003
CMD ["./zodiac_service"]
