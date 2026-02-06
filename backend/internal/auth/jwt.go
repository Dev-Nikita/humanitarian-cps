package auth

import (
	"errors"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Manager struct {
	Secret []byte
	Issuer string
	TTL    time.Duration
}

func NewFromEnv() Manager {
	sec := os.Getenv("JWT_SECRET")
	if sec == "" {
		sec = "dev_secret_change_me"
	}
	issuer := os.Getenv("JWT_ISSUER")
	if issuer == "" {
		issuer = "humanitarian-cps"
	}
	ttl := 24 * time.Hour
	return Manager{Secret: []byte(sec), Issuer: issuer, TTL: ttl}
}

func (m Manager) NewToken(subject string) (string, error) {
	now := time.Now()
	claims := jwt.RegisteredClaims{
		Issuer:    m.Issuer,
		Subject:   subject,
		IssuedAt:  jwt.NewNumericDate(now),
		ExpiresAt: jwt.NewNumericDate(now.Add(m.TTL)),
	}
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return t.SignedString(m.Secret)
}

func (m Manager) ParseFromAuthHeader(h string) (*jwt.RegisteredClaims, error) {
	if h == "" {
		return nil, errors.New("missing Authorization header")
	}
	parts := strings.SplitN(h, " ", 2)
	if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
		return nil, errors.New("invalid Authorization header")
	}
	tokenStr := parts[1]
	parsed, err := jwt.ParseWithClaims(tokenStr, &jwt.RegisteredClaims{}, func(t *jwt.Token) (any, error) {
		return m.Secret, nil
	})
	if err != nil {
		return nil, err
	}
	claims, ok := parsed.Claims.(*jwt.RegisteredClaims)
	if !ok || !parsed.Valid {
		return nil, errors.New("invalid token")
	}
	return claims, nil
}
