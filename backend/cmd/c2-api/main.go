package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"humanitarian-cps/backend/internal/auth"
	"humanitarian-cps/backend/internal/events"
	"humanitarian-cps/backend/internal/ingest"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type cfg struct {
	DBURL       string
	HTTPAddr    string
	RequireAuth bool
}

func getenv(k, d string) string {
	v := os.Getenv(k)
	if v == "" {
		return d
	}
	return v
}

func mustCfg() cfg {
	c := cfg{
		DBURL:    getenv("DB_URL", "postgres://cps:cps@localhost:5432/cps?sslmode=disable"),
		HTTPAddr: getenv("HTTP_ADDR", ":8080"),
	}
	c.RequireAuth = getenv("REQUIRE_AUTH", "false") == "true"
	return c
}

func applyMigrations(db *pgxpool.Pool) error {
	sqlBytes, err := os.ReadFile("migrations/001_init.sql")
	if err != nil {
		return err
	}
	_, err = db.Exec(context.Background(), string(sqlBytes))
	return err
}

func authMiddleware(m auth.Manager) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			_, err := m.ParseFromAuthHeader(r.Header.Get("Authorization"))
			if err != nil {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func main() {
	c := mustCfg()
	jm := auth.NewFromEnv()

	db, err := pgxpool.New(context.Background(), c.DBURL)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	if err := applyMigrations(db); err != nil {
		log.Fatal("migration error: ", err)
	}

	repo := events.Repo{DB: db}
	ing := ingest.NewHandler(repo)

	r := chi.NewRouter()

	r.Get("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]any{"ok": true})
	})

	// token helper for local dev
	r.Post("/token", func(w http.ResponseWriter, r *http.Request) {
		t, err := jm.NewToken("operator")
		if err != nil {
			http.Error(w, "token error", http.StatusInternalServerError)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]string{"token": t})
	})

	if c.RequireAuth {
		r.Group(func(pr chi.Router) {
			pr.Use(authMiddleware(jm))
			pr.Post("/events", ing.PostEvent)
			pr.Get("/events", func(w http.ResponseWriter, r *http.Request) {
				limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
				out, err := repo.List(context.Background(), limit)
				if err != nil {
					http.Error(w, "db error", http.StatusInternalServerError)
					return
				}
				w.Header().Set("Content-Type", "application/json")
				_ = json.NewEncoder(w).Encode(out)
			})
		})
	} else {
		r.Post("/events", ing.PostEvent)
		r.Get("/events", func(w http.ResponseWriter, r *http.Request) {
			limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
			out, err := repo.List(context.Background(), limit)
			if err != nil {
				http.Error(w, "db error", http.StatusInternalServerError)
				return
			}
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(out)
		})
	}

	srv := &http.Server{
		Addr:              c.HTTPAddr,
		Handler:           r,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Println("c2-api listening on", c.HTTPAddr)
	log.Fatal(srv.ListenAndServe())
}
