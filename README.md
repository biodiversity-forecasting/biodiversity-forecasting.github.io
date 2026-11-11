# Nettsida til Senter for naturprognosar (CBF)

Tospråkleg nettside (nynorsk og engelsk) for Senter for naturprognosar / Centre for Biodiversity Forecasting.
Sida er statisk: tekstane ligg som Markdown-filer, og GitHub byggjer og publiserer sida automatisk.


## Slik endrar de innhald

Alt kan gjerast i nettlesaren på github.com: opna fila, trykk på blyanten, skriv, og trykk *Commit changes*. Sida vert oppdatert automatisk.

| Kva | Kvar |
|---|---|
| Tekst på sidene | `content/nn/…` (nynorsk) og `content/en/…` (engelsk) |
| Framsida | `content/nn/index.md` og `content/en/index.md` (tekstane står øvst i fila) |
| Folk i leiinga | `data/people.yaml` + bilete i `static/img/people/` |
| Partnarar og logoar | `data/partners.yaml` + logoar i `static/img/partners/` |
| Forskingsområda | korttekstar i `data/research.yaml`, lange tekstar i `content/nn/forsking/` og `content/en/research/` |
| Tabellen klima/natur | `data/gap.yaml` |
| Meny, knappetekstar, kontaktadresse, LinkedIn | `site.yaml` |
| Farger og utsjånad | `static/css/style.css` |

### Skrive ein nyheit

Lag ei ny fil i `content/nn/aktuelt/`, til dømes `ny-stipendiat.md`:

```markdown
---
key: ny-stipendiat
layout: post
parent_label: Aktuelt
title: Ny stipendiat i CBF
date: 2027-02-01
lead: Ei kort ingress som vert vist øvst.
description: Ei setning som vert vist i lista over nyheiter.
image: photos/feltarbeid.jpg
image_alt: Kort skildring av biletet.
---

Sjølve teksten skriv de her, med vanleg Markdown: **feit**, *kursiv*, [lenkje](https://ntnu.no), lister med - osv.
```

Den engelske versjonen legg de i `content/en/news/` med **same `key`**. Då lenkjar språkknappen mellom dei.
Nyheiter utan engelsk versjon fungerer òg; då vert språkknappen berre borte på den sida.

Lenkjer og bilete inne i tekstane skriv de med stiar som byrjar med `/`, til dømes `/nn/bli-med/` eller `/img/photos/smalom.jpg`.

### Skjula ei side mellombels

Skriv `draft: true` øvst i fila (mellom dei to `---`-linjene). Då vert sida ikkje publisert, og ho forsvinn frå menyen og frå lenkjer på framsida. Fjern linja for å visa sida igjen.
Casar-sidene (`content/nn/casar.md` og `content/en/cases.md`) er skjulte på denne måten no.

### Mørkt band

Vil de ha ein del av ei tekstside på djupblå bakgrunn over heile breidda (som Organisering på Om senteret), set de `<!-- mørkt band -->` på eiga linje før delen og `<!-- /mørkt band -->` etter.

### Bilete

Legg bilete i `static/img/photos/`. Bruk JPG, helst under 1600 pikslar breie og under 400 kB. Skriv alltid ein alt-tekst (`image_alt`) som skildrar biletet, av omsyn til universell utforming.

## Publikasjonar frå NVA

Publikasjonslista vert henta automatisk frå Nasjonalt vitenarkiv (NVA) kvar gong sida vert bygd, og i tillegg kvar måndag morgon.
Det som trengst, er ID-en til CBF-prosjektet i NVA. Skriv han inn i `site.yaml`:

```yaml
nva:
  projects: [1234567]   # talet frå adressa nva.sikt.no/projects/1234567
```

Prosjektet kan registrerast i NVA utan NFR-prosjektnummer; nummeret kan leggjast til seinare. Publikasjonar kjem med på lista når dei er knytte til prosjektet i NVA.
Så lenge `projects` er tom, er sida «Publikasjonar» og blokka «Siste publikasjonar» på framsida skjulte.

## LinkedIn

I `site.yaml` under `linkedin` fyller de inn adressa til LinkedIn-sida. Då kjem knappen «Følg oss på LinkedIn» på framsida og under Aktuelt.

Vil de visa utvalde innlegg, legg de dei inn under `posts`. Opna innlegget på LinkedIn, vel «…» → *Bygg inn dette innlegget*, og kopier koden `urn:li:share:…`.
Innlegga vert fyrst henta frå LinkedIn når den besøkjande klikkar på «Vis innlegget». Slik slepp sida å lasta inn sporing frå LinkedIn utan samtykke, og sida treng ikkje eit eige samtykkebanner.

## Når domenet er klart

1. Skriv domenet i `site.yaml`: `domain: naturprognosar.no` og `base_url: https://naturprognosar.no` (døme).
2. Set opp DNS hos domeneleverandøren (eller NTNU IT om det er eit ntnu.no-domene):
   - for eit underdomene (t.d. `www.naturprognosar.no`): ein `CNAME`-post som peikar på `cbf-ntnu.github.io`
   - for eit rotdomene: `A`-postar til `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
3. Under **Settings → Pages** skriv de inn domenet og hakar av for **Enforce HTTPS**.

Med `base_url` sett lagar sida òg `sitemap.xml` og `robots.txt` for søkjemotorar.

## Teste lokalt (valfritt)

```bash
pip install -r requirements.txt
python build.py --serve
```

Opna http://localhost:8000. Utan skriftfilene i `static/fonts/` brukar sida ei reserveskrift. Med `--fonts google` vert Open Sans henta frå Google Fonts i staden (berre til testing).

## Personvern og universell utforming

- Sida set ingen informasjonskapslar og hentar ingenting frå tredjepartar (skrifta er sjølvhosta).
- Farger er valde med kontrast etter WCAG 2.1 AA. Sida fungerer med tastatur og har «hopp til innhaldet»-lenkje.
- Offentlege verksemder må ha ei **tilgjengelegheitserklæring** (via uustatus.no). Avklar med NTNU om CBF-sida skal ha ei eiga.

## Teknisk

- `build.py`: lite byggjeskript (Python, Markdown og Jinja2) som gjer innhaldet om til HTML i `_site/`
- `templates/`: HTML-malar
- `.github/workflows/deploy.yml`: byggjer og publiserer sida på GitHub Pages
- Alle lenkjer er relative, så sida fungerer både på `github.io` og på eige domene utan endringar.
