package ingest

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"humanitarian-cps/backend/internal/events"
)

type EventIn struct {
	TS         float64                `json:"ts"`
	EventType  string                 `json:"event_type"`
	Confidence float64                `json:"confidence"`
	Sources    []string               `json:"sources"`
	Payload    map[string]any         `json:"payload"`
}

type Handler struct {
	Repo events.Repo
}

func NewHandler(repo events.Repo) Handler { return Handler{Repo: repo} }

func newUUID() (string, error) {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	// UUID v4-ish
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		b[0:4], b[4:6], b[6:8], b[8:10], b[10:16],
	), nil
}

func (h Handler) PostEvent(w http.ResponseWriter, r *http.Request) {
	var in EventIn
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}
	if in.EventType == "" {
		http.Error(w, "event_type required", http.StatusBadRequest)
		return
	}
	ts := time.Unix(0, int64(in.TS*1e9))
	if in.TS == 0 {
		ts = time.Now().UTC()
	}
	id, err := newUUID()
	if err != nil {
		http.Error(w, "uuid error", http.StatusInternalServerError)
		return
	}
	payloadBytes, _ := json.Marshal(in.Payload)

	ev := events.Event{
		ID:         id,
		TS:         ts,
		EventType:  in.EventType,
		Confidence: in.Confidence,
		Sources:    in.Sources,
		Payload:    payloadBytes,
	}
	if err := h.Repo.Create(context.Background(), ev); err != nil {
		http.Error(w, "db insert error: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(map[string]any{"id": id})
}
