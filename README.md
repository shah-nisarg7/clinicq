# clinic queue manager

built for a hack club project. It's a simple, zero cost queue management system for local clinics. Local clinics usually have messy waiting rooms, so this lets the receptionist track who is expected, who is waiting, and who is currently in the room.

Backend: google sheets api acting as a serverless database. it automatically creates a new sheet tab whenever a new clinic registers. The entire database is stored in a google spreadsheet, accessed by a service account of google cloud console.

whatsapp notifications: patients get a message when their appointment is booked, and again when they're a few people away from being seen. currently switching from green api to ultramsg since the free tier fits this project's usage better. (still in progress, not wired up yet)

# migrating off streamlit
streamlit isn't allowed for this program, so im rebuilding whole thing as a static frontend + vercel python serverless functions (flask). the google sheets logic in database.py is mostly unchanged from the streamlit version, just moved into api/ and wrapped with proper api routes instead of being wired directly into streamlit...


frontend is still the old placeholder, not built yet...

# testing / for reviewers
if you are reviewing this code and want to test the database logic, you can create a test clinic account. you'll need an admin invite code to make an account.

**a note on security:** in a real production environment, this code is securely managed via an environment variable to prevent random web scrapers from spamming the database. for this review, the fallback code is `HACKCLUB_2026` so you can easily bypass it and test the dynamic google sheets auth layer.

# how to run locally
1. clone the repo
2. install dependencies: `pip install -r requirements.txt`
3. you need your own google cloud service account key. save it as `service_account.json` in the root folder.
4. set up a `.env` file with your ultramsg instance id + token
5. run with `vercel dev`