# clinic queue manager

built for a hack club project. It's a simple, zero cost queue management system for local clinics. Local clinics usually have messy waiting rooms, so this lets the receptionist track who is expected, who is waiting, and who is currently in the room. 


Backend : google sheets api acting as a serverless database. it automatically creates a new sheet tab whenever a new clinic registers. The entire database is stored in a google spreadsheet, accessed by a service account of google cloud console.

# upcoming features
whatsapp notifications :currently integrating green api to automatically fire messages to patients when their turn is approaching
and inform them if any delay is there helping them leave on time and reduce queue waiting time. 


#  testing / for reviewers
if you are reviewing this code and want to test the database logic, you can create a test clinic account in the sidebar. 
go to the REGISTER tab. you'll need an admin invite code to make an account. 

**a note on security:** in a real production environment, this code is securely managed via an environment variable to prevent random web scrapers from spamming the database. for this review, i set the fallback code to `HACKCLUB_2026` so you can easily bypass it and test the dynamic google sheets auth layer.

# how to run locally
if you want to fork this and run it on your own machine:
1. clone the repo
2. install dependencies: `pip install -r requirements.txt`
3. you need your own google cloud service account key. save it as `service_account.json` in the root folder.
4. run `streamlit run app.py`