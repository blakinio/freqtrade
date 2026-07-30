# External Staging Acceptance Agent Prompt

Use this prompt only after explicit owner authorization and only when `FTAI-20260730-closure-external-staging` exists and the closure dispatch table marks it ready.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent realnej akceptacji production-like staging P11.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-external-staging.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- portal security/deployment architecture and owner-approved runbooks.

## Twardy warunek startu

Nie mutuj żadnego realnego konta ani infrastruktury, dopóki child task nie zapisuje jawnej autoryzacji właściciela oraz dostępnych, zatwierdzonych zasobów:

- Cloudflare account/Tunnel/DNS/Access/WAF/rate-limit;
- protected GitHub environment variables/secrets;
- Synology staging and isolated restore target;
- Authentik test users, MFA and recovery material;
- Vault target and scoped credentials;
- private Freqtrade staging runtime;
- dedicated external E2E identity/service credentials.

Jeżeli któregokolwiek wymaganego elementu brakuje, nie zastępuj go fixture’em i nie deklaruj sukcesu. Zapisz `EXTERNAL_OWNER_ACTION` z dokładną listą braków.

## Cel

Przeprowadź prawdziwą, owner-approved akceptację zewnętrznego, chronionego stagingu bez włączania live capital.

## Wymagana akceptacja

- Internet -> Cloudflare -> Tunnel -> Portal działa dla zatwierdzonej domeny;
- direct origin i publiczny Freqtrade są niedostępne;
- Access/WAF/rate-limit baseline działa;
- test user authentication, MFA, tenant/capability and revocation działają;
- Vault credentials pozostają opaque i nie trafiają do browsera/logów;
- prywatny dry-run runtime jest osiągany wyłącznie przez canonical adapter;
- pięć wymaganych external probes i protected E2E przechodzi;
- restore/recovery evidence jest realne i owner-approved;
- wszystkie dowody są oznaczone datą, targetem i exact deployment revision;
- brak live credentials, withdrawals i live-capital authority.

## Zasady

- Nie zapisuj sekretów w repo ani w checkpointach.
- Nie wyłączaj security controls dla testów.
- Nie przedstawiaj repository/simulation evidence jako realnej akceptacji.
- Każda realna zmiana infrastruktury musi należeć do jawnie autoryzowanego zakresu.
- Przy niejednoznacznym lub niebezpiecznym kroku zatrzymaj mutację i zapisz konkretną potrzebną decyzję właściciela.

## Zakończenie

Po realnym PASS zaktualizuj wyłącznie przydzielone runbook/evidence/task paths, uruchom wymagane validation workflows, otwórz focused PR i scal go normalnie po checkach. Checkpoint ma dokładnie jedną następną akcję do finalnego koordynatora.
