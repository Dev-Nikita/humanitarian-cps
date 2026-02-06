package events

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Event struct {
	ID         string          `json:"id"`
	TS         time.Time       `json:"ts"`
	EventType  string          `json:"event_type"`
	Confidence float64         `json:"confidence"`
	Sources    []string        `json:"sources"`
	Payload    json.RawMessage `json:"payload"`
	CreatedAt  time.Time       `json:"created_at"`
}

type Repo struct{ DB *pgxpool.Pool }

func (r Repo) Create(ctx context.Context, e Event) error {
	if r.DB == nil {
		return errors.New("db is nil")
	}
	_, err := r.DB.Exec(ctx, `
		insert into events (id, ts, event_type, confidence, sources, payload)
		values ($1,$2,$3,$4,$5,$6)
	`, e.ID, e.TS, e.EventType, e.Confidence, e.Sources, e.Payload)
	return err
}

func (r Repo) List(ctx context.Context, limit int) ([]Event, error) {
	if limit <= 0 || limit > 500 {
		limit = 50
	}
	rows, err := r.DB.Query(ctx, `
		select id, ts, event_type, confidence, sources, payload, created_at
		from events
		order by ts desc
		limit $1
	`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Event
	for rows.Next() {
		var e Event
		if err := rows.Scan(&e.ID, &e.TS, &e.EventType, &e.Confidence, &e.Sources, &e.Payload, &e.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}
