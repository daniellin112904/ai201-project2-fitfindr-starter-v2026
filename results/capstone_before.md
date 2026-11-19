# Capstone run log (before)

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Rewrite finds an allowed listing | 7 of 10 | 5/10 | 6/10 | 7/10 | MISSED |
| 2. At most one rewrite; none when search has results | 20 of 20 | 20/20 | 20/20 | 20/20 | MET |
| 3. Impossible query stops with a clear message | 10 of 10 | 10/10 | 10/10 | 10/10 | MET |
| 4. Model down: stopped, not crashed, and logged | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Every run has a complete log record | 10 of 10 | 10/10 | 10/10 | 10/10 | MET |

## Criterion 1, every attempt

| Trial | Query | Rewritten to | Selected | Pass |
|---|---|---|---|---|
| 1 | comfy sweater | cozy knitwear | lst_008 | yes |
| 1 | comfy sweater | None | None | no |
| 1 | purse | bag | lst_039 | yes |
| 1 | purse | bag | lst_039 | yes |
| 1 | running shoes | athletic sneakers | None | no |
| 1 | running shoes | athletic shoes | None | no |
| 1 | button up shirt | button down shirt | None | no |
| 1 | button up shirt | button down shirt | None | no |
| 1 | ankle booties | boots | lst_028 | yes |
| 1 | ankle booties | boots | lst_028 | yes |
| 2 | comfy sweater | cardigan | lst_008 | yes |
| 2 | comfy sweater | cozy cardigan | lst_008 | yes |
| 2 | purse | bag | lst_039 | yes |
| 2 | purse | bag | lst_039 | yes |
| 2 | running shoes | athletic shoes | None | no |
| 2 | running shoes | athletic shoes | None | no |
| 2 | button up shirt | button down shirt | None | no |
| 2 | button up shirt | button down shirt | None | no |
| 2 | ankle booties | boots | lst_028 | yes |
| 2 | ankle booties | boots | lst_028 | yes |
| 3 | comfy sweater | cozy knitwear | lst_008 | yes |
| 3 | comfy sweater | cozy cardigan | lst_008 | yes |
| 3 | purse | bag | lst_039 | yes |
| 3 | purse | bag | lst_039 | yes |
| 3 | running shoes | athletic sneakers | None | no |
| 3 | running shoes | sneakers | lst_019 | yes |
| 3 | button up shirt | button down shirt | None | no |
| 3 | button up shirt | button down shirt | None | no |
| 3 | ankle booties | boots | lst_028 | yes |
| 3 | ankle booties | boots | lst_028 | yes |
