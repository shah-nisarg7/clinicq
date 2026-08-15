# clinic queue manager

built for a hack club project. It's a simple, zero cost queue management system for local clinics. Local clinics usually have messy waiting rooms, so this lets the receptionist track who is expected, who is waiting, and who is currently in the room.

Backend: google sheets api acting as a serverless database. it automatically creates a new sheet tab whenever a new clinic registers. The entire database is stored in a google spreadsheet, accessed by a service account of google cloud console.

whatsapp notifications: Couldnt implement real whatsapp API firing messages.. as it requires an established business (under government/ linking GST etc etc)after using multiple wayaround APIs i decided that  for this demo project ill keep  a log panel on the dashboard instead (just simulating what would be sent to patient and on what triggers)
# queue logic
Once the doctor starts the queue, each expected patient gets a live ETA calculated from how many people are ahead of them (in consult + waiting + still expected) times an average consult time, plus any doctor delay (before doctor arrives) the front desk enters manually which gets added to each patient's ETA

# How to run 
 Direct link : https://clinicq-three.vercel.app/
To register for a new account the secret code/admin code is set to "HACKCLUB_2026" (this was added in earlier version to prevent spamming whatsapp api through normal people testing it/using a bot..)



# RUNNING LOCALLY 
(its somewhat lengthhy)
 1) clone the repo 
 2) pip install -r requirements.txt
 3) Create a free Google Cloud project at console.cloud.google.com
 4) Enable the "Google Sheets" and "Google Drive" API for that project
 5) Create a service account (IAM and Admin Tab -> Service account -> create ) then generate a JSON Key for it and save it as "service_account.json" in the project root.
 6) Create a new Google Sheet named "Clinic_Queue_MVP" and share it (Editor access) with the service account's email 
(looks like `xxx@xxx.iam.gserviceaccount.com`) found in the json key file
7) run "vercel dev" , click on the link shown (or just open localhost:3000), login with "REVIEWER_CLINIC" and pass is already shared in the reviewer's note. 
(or just register a new account using the "HACKCLUB_2026" code already mentioned above.
everything is free under google's free tier.. 

  
# Important points
Google sheets has limitations of approx 200 sheets, meaning 200 -3 (management tabs) ~ 197 clinics can register after which
google sheets cant handle it.
There is no rate limit currently, adding it would be a big task for login, register and adding a patient. 
Project Images
Login Page:
<img width="506" height="393" alt="image" src="https://github.com/user-attachments/assets/0f4aa289-cba4-48c4-a9b6-eb2684dffe39" />
Dashboard: 
<img width="1912" height="698" alt="image" src="https://github.com/user-attachments/assets/9714c5b7-7525-43bd-bbf5-b0464f6fc9ad" />
Notification panel : 
<img width="1887" height="641" alt="image" src="https://github.com/user-attachments/assets/075ad1e5-05c6-4f25-b1c1-7ac6f7e353e5" />
backend : 
<img width="1480" height="559" alt="image" src="https://github.com/user-attachments/assets/69737f87-ba25-438f-933e-9d08da4af39a" />
(database for all patient data, Clinic settings/data) 
<img width="540" height="436" alt="image" src="https://github.com/user-attachments/assets/d2a60daf-1330-4676-b4fa-3609a4932333" />
<img width="1357" height="643" alt="image" src="https://github.com/user-attachments/assets/1949ad06-04ef-4a76-9fa2-9ddc74609295" />






