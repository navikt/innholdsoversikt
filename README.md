# Innholdsoversikt

[![Code style: 
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Dette er vår cronjob-app på NAIS for å skaffe oversikt over innholdet vårt på nav.no og oppdatere [vårt 
dashboard](https://metabase.ansatt.nav.no/dashboard/11-innholdsoversikt-pa-nav-no) 
der vi følger med på innholdsmengde over tid.

[main](/src/innholdsoversikt/main.py) trekker ut innholdet vårt fra CMSet Enonic XP og lager 
aggregert statistikk på metadata som mengden publisert og avpublisert 
innhold, innholdsmengde, alder og fordeling på områdene på `nav.no`.

Dashboardet oppdateres en gang i måneden via en cronjob i kubernetes. 
[Logger i 
Kibana](https://logs.adeo.no/goto/6eac7c60-4a6a-11ed-8607-d590fd125f80).

**Jobb lokalt**

Bruk venv for å lage og starte det virtuelle miljøet, og pip for avhengigheter. Installér avhengigheter med `make install`.

```
cd innholdsoversikt
source venv/bin/activate # starter virtuelt  miljø
make install # installerer avhengigheter
make update-deps # oppdater avhengigheter
make format # formaterer python-kode med black
```

[Enonic data api](/src/innholdsoversikt/enonic_data_api.py) eksporterer innhold fra Enonic XP 
via [dataquery APIet](https://github.com/navikt/nav-enonicxp-dataquery).

**Se pods i kubernetes**

```
kubectl config use-context dev-gcp
kubectl config use-context prod-gcp
kubectl -n navno get pods
```

**Se naisjobs i kubernetes**

```
kubectl get naisjob -n navno # viser naisjob i namespace
kubectl describe naisjob innholdsoversikt-dashboard -n navno # beskriver naisjob metadata
```


**Start og slutt naisjob manuelt**

```
kubectl create job innholdsdashboard 
--from=cronjob/innholdsoversikt-dashboard -n navno
kubectl delete naisjob innholdsoversikt-dashboard -n navno
```

**Secrets**

```
kubectl config use-context dev-gcp
kubectl config use-context prod-gcp
kubectl -n navno create secret generic innholdsmengde-dashboard-secrets --from-file=secrets.json
kubectl -n navno get secret 
kubectl -n navno describe secrets/innholdsmengde-dashboard-secrets
kubectl -n navno delete secret innholdsmengde-dashboard-secrets
```

**Bygg og Inspiser app lokalt**

```
colima start

docker build -f Dockerfile.local -t innholdsmengde_local .

docker run --rm -it innholdsmengde_local /bin/bash
```

**Spørringer i databasen**

Bigquery har [sin egen syntaks](https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax) for SQL spørringer. Bruk kopitabellen for å teste spørringer.

Det går an å [kjøre spørringer regelmessig](https://cloud.google.com/bigquery/docs/scheduling-queries#setting_up_a_scheduled_query), f.eks ukentlig.

Velg rader for en gitt dato, med et utvalg på 1000

```SQL
SELECT * FROM `project-id.dataset.table` WHERE dato = '2024-07-05' LIMIT 1000
```

Velg samme data uten begrenset utvalg

```SQL
SELECT * FROM `project-id.dataset.table` WHERE dato = '2023-08-21'
```

Slett rader for en gitt dato

```SQL
DELETE FROM `project-id.dataset.table` WHERE dato = '2023-08-21'
```