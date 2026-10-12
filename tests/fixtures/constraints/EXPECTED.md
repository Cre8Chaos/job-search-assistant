| Fixture | Constraints Gate | Grade capped at F? |
|---|---|---|
| 01-travel-30 | CONFLICT (travel), quotes "Travel up to 30%" | yes |
| 02-relocation | CONFLICT (relocation), quotes "Relocation to Chicago" | yes |
| 03-onsite-outside-radius | CONFLICT (onsite outside radius), quotes "3 days a week from our Chicago" | yes |
| 04-travel-vague | CHECK | no |
| 05-remote-10 | PASS | no |
| 06-domain-and-travel | CONFLICT (travel), quotes "Travel up to 40%" | yes (F, not D) |
