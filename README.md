# Innholdsoversikt

[![Code style: 
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Dette er vår cronjob-app på NAIS for å skaffe oversikt over innholdet vårt på nav.no og oppdatere [vårt 
dashboard](https://metabase.intern.nav.no/dashboard/11-innholdsoversikt-pa-nav-no) 
der vi følger med på innholdsmengde over tid.

[main](/src/innholdsoversikt/main.py) trekker ut innholdet vårt fra CMSet Enonic XP og lager 
aggregert statistikk på metadata som mengden publisert og avpublisert 
innhold, innholdsmengde, alder og fordeling på områdene på `nav.no`.

Dashboardet oppdateres en gang i måneden via en cronjob i kubernetes. 
[Logger i 
Kibana](https://logs.adeo.no/goto/6eac7c60-4a6a-11ed-8607-d590fd125f80).

**Jobb lokalt**

Bruk venv for å starte det virtuelle miljøet, og pip for avhengigheter. Installér avhengigheter med `make install`.

```
cd innholdsoversikt
source venv/bin/activate # starter virtuelt  miljø
make update-deps # oppdater avhengigheter
```

[Enonic data api](/src/innholdsoversikt/enonic_data_api.py) eksporterer innhold fra Enonic XP 
via [dataquery APIet](https://github.com/navikt/nav-enonicxp-dataquery).

**Se pods i kubernetes**

```
kubectl config use-context dev-gcp
kubectl config use-context prod-gcp
kubectl -npersonbruker get pods
```

**Se naisjobs i kubernetes**

```
kubectl get naisjob -npersonbruker # viser naisjob i namespace
kubectl describe naisjob innholdsoversikt-dashboard -npersonbruker # beskriver naisjob metadata
```


**Start og slutt naisjob manuelt**

```
kubectl create job innholdsdashboard 
--from=cronjob/innholdsoversikt-dashboard -npersonbruker
kubectl delete naisjob innholdsoversikt-dashboard -npersonbruker
```

**Secrets**

```
kubectl config use-context dev-gcp
kubectl config use-context prod-gcp
kubectl -npersonbruker create secret generic innholdsmengde-dashboard-secrets --from-file=secrets.json
kubectl -npersonbruker get secret 
kubectl -npersonbruker describe secrets/innholdsmengde-dashboard-secrets
kubectl -npersonbruker delete secret innholdsmengde-dashboard-secrets
```

**Bygg og Inspiser app lokalt**

```
colima start

docker build -f Dockerfile.local -t innholdsmengde_local .

docker run --rm -it innholdsmengde_local /bin/bash
```
