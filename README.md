# AIS Backend Developer assignment

You are given this repository from the data science team. It contains a Python script that generates a model, stores it in a file and then uses it to generate a house price prediction based on the property parameters.

## Task
Create a back-end with REST API that uses the model for predictions. Include token based authentication and rate limiting. The solution needs to be production ready with a configured Dockerfile, CI/CD pipeline and some tests. 

## Submitting your solution
The preferred form of submission is to place the whole solution in a public GitHub repository and send us a link. Both the dataset and model are distributed under the public license. If you don't wish to display your solution publicly, you can send a zip archive with the code to the telekom email address (your contact person).

## Notes
* You should not generate any new model. Use the model provided in the `model.joblib` file.
* If you use a database, it should be part of your solution as a file.
* If something is unclear or you run into any technical diffilcuties, feel free to contact us.
* Python 3.9.13 was tested with the solution, thus this version is safe to use. But upgrading the solution to the latest stable python version woudln't hurt eiter.

### Files
* `main.py` - sample script that generates and uses the model
* `model.joblib` - the computed model you should use
* `housing.csv` - data files used to generate the model
* `requirements.txt` - pip dependencies

## Sample outputs
You can validate you predictions on these sample inputs and expected outputs.

Input 1:
```
longitude: -122.64
latitude: 38.01
housing_median_age: 36.0
total_rooms: 1336.0
total_bedrooms: 258.0
population: 678.0
households: 249.0
median_income: 5.5789
ocean_proximity: 'NEAR OCEAN'
```

Output 1: `320201.58554044`

-----------------------------------

Input 2:
```
longitude: -115.73
latitude: 33.35
housing_median_age: 23.0
total_rooms: 1586.0
total_bedrooms: 448.0
population: 338.0
households: 182.0
median_income: 1.2132
ocean_proximity: 'INLAND'
```
Output 2: `58815.45033765`

-----------------------------------

Input 3:
```
longitude: -117.96
latitude: 33.89
housing_median_age: 24.0
total_rooms: 1332.0
total_bedrooms: 252.0
population: 625.0
households: 230.0
median_income: 4.4375
ocean_proximity: '<1H OCEAN'
```
Output 3: `192575.77355635`

## What’s Been Implemented
- API
  - `GET /health` – quick liveness check (`{"status":"ok"}`).
  - `POST /predict` – returns a price prediction; requires Bearer JWT.
  - `POST /users` – sign up with email and password.
  - `POST /login` – authenticate and receive a short‑lived JWT.
  - `GET /predictions` – fetch your own prediction history.
- Authentication & Rate Limiting
  - JWT bearer auth (sign up → login → use token in `Authorization: Bearer <token>`).
  - Fixed‑window rate limit per token; configurable via `RATE_LIMIT_MAX` and `RATE_LIMIT_WINDOW` (defaults: 10 req / 60 s).
- Model & Features
  - Uses the provided `model.joblib` (no retraining).
  - Aligns request payloads to the training feature space derived from `housing.csv` (one‑hot encodes `ocean_proximity`).
- Persistence
  - PostgreSQL database via `DATABASE_URL` (see `docker-compose.yml` for a local Postgres service).
  - Stores users and each prediction with original payload and timestamp.
- Tooling & Run
  - Dockerfile and `docker-compose.yml` for local development (API on `:8000`, optional frontend dev server on `:3000`).
  - Pytest covers health, auth requirement, and the first sample prediction value.
  - Minimal React frontend (register, login, dashboard) is served from `/app` when a production build exists.

Quick start (compose):
```
docker-compose up --build
# API: http://localhost:8000  |  Web (dev): http://localhost:3000
```
