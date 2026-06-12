# Ireland’s Flora, Fauna and Birds

**Subtitle:** The Majestic Beauty of the Irish Countryside

A mobile-friendly Streamlit field guide for Irish flora, fauna, resident birds and migratory birds.

## Features

- Colourful mobile-first layout
- Browse Irish flora, fauna and birds
- Search by name, habitat, season, edibility, warning or notes
- Filter by group/category/edibility/spotted status
- Mark items as spotted
- Save personal notes
- Upload photos from mobile gallery
- Supabase support for persistent notes, spotted records and photos
- Local fallback mode for testing
- CSV-based species data so the guide can be expanded over time

## Files

```text
app.py
requirements.txt
supabase_schema.sql
data/species_seed.csv
.streamlit/config.toml
.streamlit/secrets.toml.example
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Create a GitHub repository.
2. Upload all files and folders in this project.
3. Go to Streamlit Cloud.
4. Create a new app from your GitHub repo.
5. Set the main file path to:

```text
app.py
```

6. Deploy.

## Supabase setup

1. Create a Supabase project.
2. Open **SQL Editor**.
3. Paste and run the contents of `supabase_schema.sql`.
4. In Supabase, go to **Project Settings > API**.
5. Copy:
   - Project URL
   - Service role key
6. In Streamlit Cloud, go to your app settings > **Secrets**.
7. Add:

```toml
APP_PASSWORD = "your-family-password"
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"
```

8. Open the app.
9. Go to **Data setup**.
10. Press **Sync starter species data to Supabase**.

## Expanding the species guide

Edit `data/species_seed.csv` or use the app’s **Data setup** page to import a larger CSV into Supabase.

Required columns:

```text
id, common_name, scientific_name, kingdom_group, category, subcategory, season, habitat, description, edibility, medicinal_uses, warning, conservation_status, image_search, image_url
```

## Safety note

This app is educational. It is not medical, veterinary, foraging, ecological survey, or legal advice. Never eat wild plants, fungi, berries, or seaweeds unless identified by a competent local expert and verified with a reliable field guide.


## Version 2 updates

- Richer home screen with Irish habitat photo panels for woodlands, waterways, lakes and mountains.
- More colourful mobile navigation tiles.
- Habitat, season, edibility, medicinal/traditional uses, warnings and conservation status are now visible by default on each record.
- Expanded starter database from 95 records to 270 records.
- Added many more trees, shrubs, wildflowers, seaweeds, fungi, mammals, marine species, insects, invertebrates and resident/migratory birds.
