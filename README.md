# 🚀 DevOps Researcher

**Automatyczny system do znajdowania i kontrybuowania do projektów niemieckich firm DevOps/Cloud**

## 🎯 Cel projektu

Projekt automatyzuje proces:
1. **Znajdowania** niemieckich firm z publicznymi repozytoriami
2. **Analizowania** ich projektów pod kątem możliwych ulepszeń
3. **Generowania** konkretnych kontrybuji (README, Makefile, testy)
4. **Przygotowywania** materiałów do kontaktu z firmami

## 🛠️ Funkcjonalności

### ✅ Analiza firm i repozytoriów
- Automatyczne wyszukiwanie firm DevOps/Cloud w Niemczech
- Analiza jakości dokumentacji (README.md)
- Sprawdzanie obecności Makefile i struktury testów
- Identyfikacja issues z tagami "help wanted", "good first issue"

### ✅ Generowanie kontrybuji
- Automatyczne poprawki README.md
- Generowanie standardowych Makefile
- Dodawanie brakujących testów i CI/CD
- Tworzenie Docker configurations

### ✅ Komunikacja z firmami
- Szablony email/LinkedIn messages
- Automatyczne generowanie spersonalizowanych wiadomości
- Tracking wysłanych wiadomości

### ✅ Raportowanie
- Raporty CSV z analizą firm
- HTML dashboardy z wynikami
- Metryki sukcesu kontrybuji

## 🚀 Szybki start

### 1. Instalacja
```bash
git clone https://github.com/coboarding/researcher
cd researcher
pip install -r requirements.txt
```

### 2. Konfiguracja
```bash
cp .env.example .env
# Edytuj .env i dodaj swój GitHub token
```

### 3. Uruchomienie
```bash
# Pełna analiza
python scripts/main.py

# Tylko analiza firm
python scripts/analyze_companies.py

# Generowanie kontrybuji
python scripts/generate_contributions.py

# Wysyłanie wiadomości
python scripts/send_outreach.py
```

## 📋 Wymagania

- Python 3.8+
- GitHub Token (dla wyższych limitów API)
- Git (do klonowania repozytoriów)

## 🔧 Konfiguracja

### GitHub Token
1. Idź do [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Utwórz nowy token z scope: `public_repo`
3. Dodaj do `.env`: `GITHUB_TOKEN=your_token_here`

### Lista firm
Edytuj `config/companies.json` aby dodać/usunąć firmy do analizy.

## 📊 Przykładowe wyniki

Po uruchomieniu otrzymasz:
- `output/reports/companies_analysis.csv` - analiza firm
- `output/contributions/` - wygenerowane poprawki
- `output/logs/` - logi wykonania

## 🤝 Kontrybuowanie

Projekt jest open source! Jeśli chcesz dodać funkcjonalność:
1. Fork repository
2. Utwórz feature branch
3. Commituj zmiany
4. Utwórz Pull Request

## 📄 Licencja

MIT License - zobacz [LICENSE](LICENSE) dla szczegółów.

## 🆘 Pomoc

- **Dokumentacja**: [docs/](docs/)
- **Issues**: Zgłaszaj problemy przez GitHub Issues
- **Kontakt**: [Twój email]

---

**Autor**: [Twoje Imię]  
**GitHub**: [@twoj-github](https://github.com/tom-sapletta-com)  
**LinkedIn**: [Twój LinkedIn](https://linkedin.com/in/tom-sapletta-com)