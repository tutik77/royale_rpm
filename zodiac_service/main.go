package main

import (
	"encoding/json"
	"log"
	"net/http"
)

type Card struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	ImageURL    string `json:"image_url"`
}

type ZodiacResponse struct {
	Sign string `json:"sign"`
	Card Card   `json:"card"`
}

var zodiacCards = map[string]Card{
	"aries":       {ID: 26000000, Name: "Рыцарь", Description: "Ты прирождённый боец и лидер. Всегда первый в атаке!", ImageURL: "https://api-assets.clashroyale.com/cards/300/jAj1Q5rclXxU9kVImGqSJxa4wEMfEhvwNQ_4jiGUuqg.png"},
	"taurus":      {ID: 26000001, Name: "Лучницы", Description: "Ты надёжный и упоротый. Методично разносишь любую угрозу!", ImageURL: "https://api-assets.clashroyale.com/cards/300/W4Hmp8MTSdXANN8KdblbtHwtsbt0o749BbxNqmJYfA8.png"},
	"gemini":      {ID: 28000000, Name: "Стрелы", Description: "Ты быстрый и многогранный. Накрываешь всё и сразу!", ImageURL: "https://api-assets.clashroyale.com/cards/300/Flsoci-Y6y8ZFVi5uRFTmgkPnCmMyMVrU7YmmuPvSBo.png"},
	"cancer":      {ID: 26000003, Name: "Гигант", Description: "Ты защитник своих близких. Огромный запас терпения и стойкости!", ImageURL: "https://api-assets.clashroyale.com/cards/300/Axr4ox5_b7edmLsoHxBX3vmgijAIibuF6RImTbqLlXE.png"},
	"leo":         {ID: 26000010, Name: "Принц", Description: "Ты королевская особа. Харизма и мощь — твоё всё!", ImageURL: "https://api-assets.clashroyale.com/cards/300/3JntJV62aY0G1Qh6LIs-ek-0ayeYFY3VItpG7cb9I60.png"},
	"virgo":       {ID: 26000005, Name: "Мушкетёр", Description: "Ты точный и аналитический. Каждый выстрел попадает в цель!", ImageURL: "https://api-assets.clashroyale.com/cards/300/Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds.png"},
	"libra":       {ID: 26000011, Name: "Бэби-дракон", Description: "Ты гармоничный и сбалансированный. Огонь и грация в одном!", ImageURL: "https://api-assets.clashroyale.com/cards/300/cjC9n4AvEZJ3urkVh-rwBkJ-aRSsydIMqSAV48hAih0.png"},
	"scorpio":     {ID: 26000026, Name: "Мега-рыцарь", Description: "Ты мощный и загадочный. Один удар — и все разлетаются!", ImageURL: "https://api-assets.clashroyale.com/cards/300/O2NycChSNhn_UK9nqBXUhhC_lILkiANzPuJjtjoz0CE.png"},
	"sagittarius": {ID: 26000006, Name: "Мини P.E.K.K.A", Description: "Ты свободолюбивый авантюрист. Бьёшь сильно и наверняка!", ImageURL: "https://api-assets.clashroyale.com/cards/300/Fmltc4j3Ve9vO_xhHHPEO3PRP3SmU2oKp2zkZQHRZT4.png"},
	"capricorn":   {ID: 28000001, Name: "Огненный шар", Description: "Ты целеустремлённый и серьёзный. Сносишь любые преграды!", ImageURL: "https://api-assets.clashroyale.com/cards/300/lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc.png"},
	"aquarius":    {ID: 26000014, Name: "Ведьма", Description: "Ты нестандартный и креативный. Магия — твоя стихия!", ImageURL: "https://api-assets.clashroyale.com/cards/300/cfwk1vzehVyHC-uloEIH6NOI0hOdofCutR5PyhIgO6w.png"},
	"pisces":      {ID: 28000006, Name: "Заморозка", Description: "Ты интуитивный и загадочный. Замораживаешь врагов одним взглядом!", ImageURL: "https://api-assets.clashroyale.com/cards/300/I1M20_Zs_p_BS1NaNIVQjuMJkYI_1-ePtwYZahn0JXQ.png"},
}

var signs = []string{
	"aries", "taurus", "gemini", "cancer", "leo", "virgo",
	"libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}

func enableCORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		next(w, r)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func signsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(signs)
}

func zodiacHandler(w http.ResponseWriter, r *http.Request) {
	sign := r.URL.Query().Get("sign")
	if sign == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "parameter 'sign' is required"})
		return
	}

	card, ok := zodiacCards[sign]
	if !ok {
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(map[string]string{"error": "unknown zodiac sign"})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ZodiacResponse{Sign: sign, Card: card})
}

func main() {
	http.HandleFunc("/health", enableCORS(healthHandler))
	http.HandleFunc("/api/v1/zodiac", enableCORS(zodiacHandler))
	http.HandleFunc("/api/v1/signs", enableCORS(signsHandler))

	log.Println("zodiac_service starting on :8003")
	log.Fatal(http.ListenAndServe(":8003", nil))
}
